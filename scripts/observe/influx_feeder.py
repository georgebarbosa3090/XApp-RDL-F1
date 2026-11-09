#!/usr/bin/env python3
"""
Alimentador do InfluxDB para acompanhar as simulações no Grafana (bucket "simulacoes", org "rdl").

Fontes (o mesmo que as abas de observabilidade mostram, docs/11):

- execução NORI corrente: raw/slice_series.csv do pod do NORI (contadores acumulados do FlowMonitor por UE a cada
  0,5 s simulado) -> measurement ``nori_slice`` (vazão e atraso por fatia, com o tempo simulado);
- eventos da xApp kpm-probe (/data/logs/kpm_probe_events.jsonl) -> ``xapp_kpm_node``, ``xapp_kpm_ue``,
  ``xapp_indication``, ``xapp_control``, ``xapp_control_outcome``, ``xapp_decision``;
- evidência no repositório: vereditos de efeito de cada execução NORI (slice_effect.json e slice_effect_v6.json)
  -> ``campanha_execucao``, e os gates do certificado mais recente -> ``certificado``.

Uso (Ubuntu do WSL; normalmente via scripts/observe/influx_live.sh, que abre o port-forward e lê o token):
    INFLUX_URL=http://127.0.0.1:18086 INFLUX_TOKEN=... python3 scripts/observe/influx_feeder.py
    ... --once           # uma passada (campanhas e certificado) e sai
    ... --no-campaign    # só o ao vivo (NORI e xApp)

O alimentador só lê: nada é escrito no repositório nem no cluster (o estado fica em ~/.cache/xapp-rdl/).
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
RUN_RE = re.compile(r"^nori_(S[0-8])_(B[0-3])((?:_[a-z0-9]+)*)_seed(\d+)$")
VERDICT_CODE = {"CONSISTENT": 1, "NOT_TESTABLE": 0, "INCONSISTENT": -1, "INVALID": -2}
SST_SLICE = {1: "eMBB", 2: "URLLC"}
GATE_CODE = {"CERTIFIED": 3, "LOCAL_ONLY": 2, "NOT_CERTIFIED": 1, "BLOCKED": 0}


# ---------------------------------------------------------------------------
# Line protocol
# ---------------------------------------------------------------------------

def _esc_key(s: str) -> str:
    return str(s).replace("\\", "\\\\").replace(",", "\\,").replace("=", "\\=").replace(" ", "\\ ")


def _field(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return f"{v}i"
    if isinstance(v, float):
        return repr(v) if v == v else None   # NaN fora
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def line(measurement: str, tags: Dict[str, Any], fields: Dict[str, Any], ts_ns: int) -> Optional[str]:
    """Uma linha do line protocol do InfluxDB; None se não houver campo."""
    fs = [f"{_esc_key(k)}={_field(v)}" for k, v in fields.items() if _field(v) is not None]
    if not fs:
        return None
    ts = "".join(f",{_esc_key(k)}={_esc_key(v)}" for k, v in sorted(tags.items()) if v not in (None, ""))
    return f"{_esc_key(measurement)}{ts} {','.join(fs)} {int(ts_ns)}"


def to_ns(t_utc: str) -> int:
    """'2026-11-09T12:00:00.123Z' -> ns desde a época."""
    t = t_utc.rstrip("Z")
    fmt = "%Y-%m-%dT%H:%M:%S.%f" if "." in t else "%Y-%m-%dT%H:%M:%S"
    return int(datetime.strptime(t, fmt).replace(tzinfo=timezone.utc).timestamp() * 1e9)


def run_tags(run_id: str) -> Dict[str, Any]:
    m = RUN_RE.match(run_id)
    if not m:
        return {"run": run_id}
    return {"run": run_id, "scenario": m.group(1), "baseline": m.group(2),
            "condition": m.group(3).lstrip("_") or "padrao", "seed": m.group(4)}


# ---------------------------------------------------------------------------
# NORI: série por fatia
# ---------------------------------------------------------------------------

def slice_points(run_id: str, csv_text: str, sent: Dict[Tuple[str, int], float]) -> List[str]:
    """Vazão (Mb/s) e atraso médio (ms) por UE/fatia entre amostras consecutivas do slice_series.csv.
    ``sent`` guarda o último tempo simulado enviado por (run, ue), para não repetir pontos."""
    rows: Dict[int, List[Tuple[float, float, int, int, int, float]]] = {}
    for raw in csv_text.splitlines():
        parts = raw.strip().split(",")
        if len(parts) < 8 or not parts[0][:1].isdigit():
            continue
        try:
            t, wall, ue, sst = float(parts[0]), float(parts[1]), int(parts[2]), int(parts[3])
            rxp, rxb, dsum = int(parts[5]), int(parts[6]), float(parts[7])
        except ValueError:
            continue
        rows.setdefault(ue, []).append((t, wall, sst, rxp, rxb, dsum))
    out = []
    tags_base = run_tags(run_id)
    for ue, rs in rows.items():
        rs.sort()
        for (t0, _w0, _s0, p0, b0, d0), (t1, w1, sst, p1, b1, d1) in zip(rs, rs[1:]):
            if t1 <= t0 or sent.get((run_id, ue), -1.0) >= t1:
                continue
            mbps = (b1 - b0) * 8.0 / (t1 - t0) / 1e6
            delay_ms = (d1 - d0) / (p1 - p0) * 1000 if p1 > p0 else None
            ln = line("nori_slice", {**tags_base, "ue": ue, "sst": sst, "slice": SST_SLICE.get(sst, str(sst))},
                      {"throughput_mbps": round(mbps, 4), "delay_ms": round(delay_ms, 4) if delay_ms is not None else None,
                       "sim_time_s": t1}, int(w1 * 1e9))
            if ln:
                out.append(ln)
            sent[(run_id, ue)] = t1
    return out


# ---------------------------------------------------------------------------
# xApp: eventos
# ---------------------------------------------------------------------------

def event_points(ev: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
    """Eventos da kpm-probe -> pontos. ``context`` leva o run/cenário/baseline correntes (da execução NORI)."""
    kind, t = ev.get("event"), ev.get("t_utc")
    if not kind or not t:
        return []
    ts = to_ns(t)
    tags = {k: v for k, v in context.items() if k in ("run", "scenario", "baseline", "condition")}
    out: List[Optional[str]] = []
    if kind == "kpm" and ev.get("format") == 1:
        n = ev.get("node") or {}
        out.append(line("xapp_kpm_node", tags, {"prb_used_dl": n.get("RRU.PrbUsedDl"), "prb_avail_dl": n.get("RRU.PrbAvailDl"),
                                                "active_ue_dl": n.get("DRB.MeanActiveUeDl"), "rrc_conn": n.get("RRC.ConnMean")}, ts))
    elif kind == "kpm" and ev.get("format") == 3:
        for u in ev.get("ues") or []:
            sst = u.get("DRB.NetworkSlicing.SST")
            out.append(line("xapp_kpm_ue", {**tags, "ue": u.get("ue_id"), "sst": sst,
                                            "slice": SST_SLICE.get(sst, str(sst)) if sst is not None else None},
                            {"prb_used_dl": u.get("RRU.PrbUsedDl"), "ue_thp_dl": u.get("DRB.UEThpDl"),
                             "tb_dl": u.get("TB.TotNbrDl.1")}, ts))
    elif kind == "rmr_message" and ev.get("mtype") == 12050:
        out.append(line("xapp_indication", tags, {"count": 1, "length": ev.get("length")}, ts))
    elif kind == "control_request":
        q = {int(x["sst"]): x["max_prb_ratio"] for x in ev.get("quotas") or []}
        d = ev.get("decision") or {}
        out.append(line("xapp_control", {**tags, "source": ev.get("decision_source"), "rmr_ok": ev.get("rmr_ok")},
                        {"embb_cap_pct": q.get(1), "urllc_cap_pct": q.get(2), "ric_instance": ev.get("ric_instance_id"),
                         "order": ev.get("control_order") or 1, "pair_gap_ms": d.get("kpm_pair_gap_ms"),
                         "decision_ms": d.get("decision_wall_ms"), "trigger_seq": ev.get("trigger_kpm_seq")}, ts))
    elif kind == "control_outcome":
        out.append(line("xapp_control_outcome", {**tags, "outcome": ev.get("outcome")},
                        {"latency_ms": ev.get("latency_ms"), "correlated": 1 if ev.get("correlated_with_request") else 0}, ts))
    elif kind == "control_decision":
        d = ev.get("decision") or {}
        out.append(line("xapp_decision", {**tags, "source": ev.get("decision_source")},
                        {"sent": 0, "reason": d.get("reason"), "not_actuated": len(d.get("not_actuated") or [])}, ts))
    return [x for x in out if x]


# ---------------------------------------------------------------------------
# Repositório: campanhas e certificado
# ---------------------------------------------------------------------------

def _load(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def campaign_points(root: Path, done: set) -> List[str]:
    """Um ponto por (execução, regra de efeito) ainda não enviado; tempo = início da execução (manifesto)."""
    out = []
    for f in sorted(glob.glob(str(root / "experiments" / "e2_dissection" / "nori_*" / "slice_effect*.json"))):
        p = Path(f)
        run_id = p.parent.name
        key = f"{run_id}/{p.name}"
        if key in done or not RUN_RE.match(run_id):
            continue
        eff = _load(p)
        man = _load(root / "experiments" / "runs" / run_id / "execution_manifest.json")
        diss = _load(p.parent / "e2_messages.json") or {}
        if not eff or not man or not man.get("started_at_utc"):
            continue
        x = (diss.get("xapp_crosscheck") or {}).get("decision") or {}
        s = eff.get("slices") or {}
        e, u = s.get("1") or {}, s.get("2") or {}
        verdict = eff.get("verdict", "NOT_TESTABLE")
        ln = line("campanha_execucao", {**run_tags(run_id), "rule": eff.get("rule"), "verdict": verdict,
                                        "source": x.get("source")},
                  {"verdict_code": VERDICT_CODE.get(verdict, 0), "embb_before_mbps": e.get("throughput_before_mbps"),
                   "embb_after_mbps": e.get("throughput_after_mbps"), "urllc_before_mbps": u.get("throughput_before_mbps"),
                   "urllc_after_mbps": u.get("throughput_after_mbps"), "urllc_predicted_mbps": u.get("predicted_after_mbps"),
                   "embb_cap_pct": e.get("cap_max_prb_pct"), "urllc_cap_pct": u.get("cap_max_prb_pct"),
                   "trigger_is_kpm_t0": 1 if x.get("trigger_is_kpm_t0") else 0,
                   "e2_messages": diss.get("message_count")}, to_ns(man["started_at_utc"]))
        if ln:
            out.append(ln)
        done.add(key)
    return out


def certificate_points(root: Path) -> List[str]:
    files = sorted(glob.glob(str(root / "reports" / "certification" / "certificate_*.json")))
    if not files:
        return []
    cert = _load(Path(files[-1])) or {}
    stamp = re.search(r"certificate_(\d{8}T\d{6}Z)", files[-1])
    ts = int(datetime.strptime(stamp.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).timestamp() * 1e9) if stamp else int(time.time() * 1e9)
    out = []
    for gate, g in (cert.get("gates") or {}).items():
        v = g.get("verdict")
        ln = line("certificado", {"gate": gate, "verdict": v, "certificate": Path(files[-1]).stem},
                  {"certified": 1 if v == "CERTIFIED" else 0, "verdict_code": GATE_CODE.get(v, -1), "reason": g.get("reason")}, ts)
        if ln:
            out.append(ln)
    return out


# ---------------------------------------------------------------------------
# Escrita e laço
# ---------------------------------------------------------------------------

class Influx:
    def __init__(self, url: str, token: str, org: str = "rdl", bucket: str = "simulacoes"):
        self.endpoint = f"{url.rstrip('/')}/api/v2/write?org={org}&bucket={bucket}&precision=ns"
        self.token = token

    def write(self, lines: Iterable[str]) -> int:
        batch = [x for x in lines if x]
        for i in range(0, len(batch), 5000):
            body = "\n".join(batch[i:i + 5000]).encode("utf-8")
            req = urllib.request.Request(self.endpoint, data=body, method="POST",
                                         headers={"Authorization": f"Token {self.token}",
                                                  "Content-Type": "text/plain; charset=utf-8"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status not in (200, 204):
                    raise RuntimeError(f"InfluxDB respondeu {resp.status}")
        return len(batch)


def kubectl(*args: str, timeout: int = 20) -> str:
    proc = subprocess.run(["kubectl", *args], capture_output=True, text=True, timeout=timeout)
    return proc.stdout if proc.returncode == 0 else ""


NORI_CMD = ('R=$(ls -td /workspace/runs/*/ 2>/dev/null | head -1); [ -n "$R" ] || exit 0; '
            'basename "$R"; [ -f "$R/hashes.sha256" ] && echo FIM || echo ANDAMENTO; cat "$R/raw/slice_series.csv" 2>/dev/null')
XAPP_FILE = "/data/logs/kpm_probe_events.jsonl"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--once", action="store_true", help="envia campanhas e certificado uma vez e sai")
    ap.add_argument("--no-campaign", action="store_true")
    ap.add_argument("--interval", type=float, default=2.0)
    args = ap.parse_args(argv)
    url, token = os.environ.get("INFLUX_URL", "http://127.0.0.1:18086"), os.environ.get("INFLUX_TOKEN", "")
    if not token:
        print("INFLUX_TOKEN ausente (use scripts/observe/influx_live.sh)", file=sys.stderr)
        return 2
    db = Influx(url, token)
    state_path = Path(os.path.expanduser("~/.cache/xapp-rdl/influx_feeder_state.json"))
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = _load(state_path) or {}
    done = set(state.get("campaign_done", []))
    sent: Dict[Tuple[str, int], float] = {}
    xapp_offset: Optional[int] = None
    context: Dict[str, Any] = {}
    last_campaign = 0.0

    def save():
        state_path.write_text(json.dumps({"campaign_done": sorted(done)}), encoding="utf-8")

    while True:
        n = 0
        try:
            if not args.no_campaign and time.time() - last_campaign > 30:
                n += db.write(campaign_points(ROOT, done) + certificate_points(ROOT))
                save()
                last_campaign = time.time()
            if args.once:
                print(f"enviados {n} pontos (campanhas e certificado)")
                return 0
            out = kubectl("-n", "ricsim", "exec", "deploy/nori-ns3", "--", "sh", "-c", NORI_CMD)
            if out:
                head, _, csv_text = out.partition("\n")
                status, _, csv_text = csv_text.partition("\n")
                run_id = head.strip()
                context = run_tags(run_id)
                n += db.write(slice_points(run_id, csv_text, sent))
            total = kubectl("-n", "ricxapp", "exec", "deploy/kpm-probe", "--", "sh", "-c", f"wc -l < {XAPP_FILE}").strip()
            if total.isdigit():
                total_i = int(total)
                if xapp_offset is None or total_i < xapp_offset:
                    xapp_offset = total_i            # começa no fim (só o ao vivo); recomeça se o arquivo girar
                elif total_i > xapp_offset:
                    chunk = kubectl("-n", "ricxapp", "exec", "deploy/kpm-probe", "--", "sh", "-c",
                                    f"tail -n +{xapp_offset + 1} {XAPP_FILE} | head -n {total_i - xapp_offset}")
                    pts = []
                    for raw in chunk.splitlines():
                        try:
                            pts += event_points(json.loads(raw), context)
                        except ValueError:
                            continue
                    n += db.write(pts)
                    xapp_offset = total_i
            if n:
                print(f"[{datetime.now():%H:%M:%S}] {n} pontos | execução {context.get('run', '-')}", flush=True)
        except (urllib.error.URLError, RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
            print(f"[{datetime.now():%H:%M:%S}] falha ao enviar ({type(exc).__name__}: {exc}); tentando de novo", flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("alimentador encerrado")
        sys.exit(0)
