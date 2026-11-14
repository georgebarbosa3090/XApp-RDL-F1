#!/usr/bin/env python3
# Autor: George Barbosa
"""
Orquestrador da malha fechada (docs/16 §3): ns-3 (5G-LENA) ↔ xApps ↔ baseline, janela a janela.

Fluxo de uma execução:
  1. Abre um socket Unix e chama o executor certificado (scripts/certification/run_ns3_certified.sh)
     com RDL_CONTROL_SOCKET e RDL_DECISION_WINDOW; o cenário ns-3 conecta-se ao socket
     (RdlActuation, rdl-nr-common.h) e envia a topologia ("hello").
  2. A cada janela de decisão o ns-3 pausa e envia o KPM da janela. Os drivers de xApp
     (scripts/closed_loop/drivers.py) recebem o KPM e devolvem propostas.
  3. O baseline decide as propostas da janela (B0, B1, B2 ou o pipeline real da RDL-N1: B3, B3A, B3M)
     e as ações voltam ao ns-3, aplicadas no mesmo instante simulado.
  4. Cada janela (KPM, propostas, decisão, ações) é gravada em raw/closed_loop_log.jsonl da execução,
     antes de as ações voltarem ao ns-3: o arquivo está completo quando o executor calcula os hashes.

Diferença para a malha aberta: no B0, as propostas de uma janela são aplicadas no fechamento dela,
na ordem de chegada (no executor de cronograma, cada uma é aplicada no instante em que é emitida).

Uso (Ubuntu do WSL, com o venv do projeto):
  python scripts/closed_loop/orchestrator.py --scenario S8 --baseline B3 --seed 16001 --xapps replay
"""

from __future__ import annotations

import argparse
import json
import os
import select
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "scripts" / "certification"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import run_conflict_experiment as rce  # noqa: E402
from src.core import baselines as bl  # noqa: E402
from scripts.closed_loop.drivers import ReplayDriver, XAppDriver  # noqa: E402

RUNS = ROOT / "experiments" / "runs"
EEVS = {"B3": "additive", "B3A": "additive", "B3M": "mean"}


# --------------------------------------------------------------------------- baselines por janela
class WindowBaseline:
    """Decide as propostas de uma janela. B0/B1/B2 como no executor; B3* pelo pipeline real."""

    def __init__(self, baseline: str):
        self.baseline = baseline
        self.stream = None
        self._previous_eevs = os.environ.get("RDL_EEVS_AGGREGATION")
        if baseline in EEVS:
            os.environ["RDL_EEVS_AGGREGATION"] = EEVS[baseline]
            self.stream = rce.HrdlStream()

    def decide(self, group: List[Dict[str, Any]], t_close: float) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not group:
            return [], {"t_close": round(t_close, 6), "proposal_ids": [], "selected": [], "rule": "empty"}
        if self.stream is not None:
            ids, entry = self.stream.decide(group, t_close)
            by_id = {e["id"]: e for e in group}
            return [by_id[i] for i in ids if i in by_id], entry
        winners = bl.select(group, self.baseline, rce._target, rce._arrival, lambda e: e["priority"])
        rule = bl.B0_AT_WINDOW_CLOSE if self.baseline == "B0" else bl.RULES[self.baseline]
        return winners, {"t_close": round(t_close, 6), "proposal_ids": [e["id"] for e in group],
                         "selected": [w["id"] for w in winners], "rule": rule}

    def close(self) -> None:
        if self.stream is not None:
            self.stream.close()
        if self._previous_eevs is None:
            os.environ.pop("RDL_EEVS_AGGREGATION", None)
        else:
            os.environ["RDL_EEVS_AGGREGATION"] = self._previous_eevs


# --------------------------------------------------------------------------- socket com o ns-3
class Ns3Link:
    def __init__(self, conn: socket.socket):
        self.conn = conn
        self.buf = b""

    def read(self) -> Dict[str, Any] | None:
        while b"\n" not in self.buf:
            chunk = self.conn.recv(1 << 16)
            if not chunk:
                return None
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        return json.loads(line.decode("utf-8"))

    def send_actions(self, actions: List[Dict[str, Any]]) -> None:
        lines = [f"ACT {a['gnb']} {a['parameter']} {a['value']:g} {a['ue']} {a['xapp_id']} {a['id']}"
                 for a in actions]
        self.conn.sendall(("\n".join(lines + ["END"]) + "\n").encode("utf-8"))


SHIM_BUILD = os.environ.get("RDL_SHIM_BUILD", os.path.expanduser("~/xapps-originais/shim-build"))


def build_drivers(kind: str, spec: Dict[str, Any], window: float, run_id: str,
                  derivado: tuple = ()) -> List[XAppDriver]:
    if kind == "replay":
        return [ReplayDriver(rce.expand_proposals(spec), window)]
    if kind == "es-orange":
        # Gate E2: só o ES Orange original no laço (as demais xApps do cenário ficam de fora)
        from scripts.closed_loop.flexric_driver import FlexricXAppDriver
        work = os.path.join(tempfile.gettempdir(), f"rdl_xapp_es_{run_id}")
        return [FlexricXAppDriver("es-orange", "energy_saving", os.path.join(SHIM_BUILD, "xapp_es_with_cell_util_rdl"),
                                  "es", priority=60, workdir=work)]
    if kind == "completo":
        return build_full_drivers(spec, run_id, derivado)
    raise SystemExit(f"--xapps {kind}: desconhecido (replay | es-orange | completo)")


CLOSED_LOOP_CFG = ROOT / "simulations" / "ns3" / "conflicts" / "closed_loop.json"


class RAppStep:
    """
    rApp-ResourceOptimizer na malha fechada (Non-RT, A1): a cada ``period_s`` simulados planeja as três
    políticas (``rapps/greenran_resource_optimizer.plan``) com a intenção do cenário e o KPI da fatia de
    câmeras (SST 1) medido no KPM, e as entrega como chegariam pelo A1:
      - 20001 (RDL): ao gerenciador A1 da xApp RDL (B3*), que reaplica pesos e regras;
      - 21000 / 21001: às xApps RANSlicer-GreenRAN e EnergySaver-GreenRAN (mensagem 20010).
    """

    INSTANCES = {"20001": "greenran-rdl", "21000": "greenran-ranslicer", "21001": "greenran-energysaver"}

    def __init__(self, drivers: List[XAppDriver], baseline: "WindowBaseline", intent: Dict[str, Any], hour: int,
                 ue_sst: Dict[int, int], period_s: float = 10.0):
        import importlib.util
        spec = importlib.util.spec_from_file_location("greenran_resource_optimizer",
                                                      ROOT / "rapps" / "greenran_resource_optimizer.py")
        self.rapp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.rapp)
        self.apps = {getattr(d, "app", None).XAPP_ID: d.app for d in drivers if getattr(d, "app", None) is not None}
        self.baseline, self.intent, self.hour, self.ue_sst, self.period_s = baseline, intent, hour, ue_sst, period_s
        self.next_t = 0.0

    def _kpi(self, kpm: Dict[str, Any]) -> Dict[str, Any]:
        thp, delays = 0.0, []
        for u in kpm.get("ues", []):
            if u.get("connected") and self.ue_sst.get(int(u["ue"]), 1) == 1:
                thp += float(u.get("thp_mbps") or 0.0)
                if isinstance(u.get("delay_ms"), (int, float)):
                    delays.append(float(u["delay_ms"]))
        return {"camera_thp_mbps": thp, "camera_delay_ms": max(delays) if delays else None}

    def step(self, kpm: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        t = float(kpm["t"])
        if t + 1e-9 < self.next_t:
            return None
        self.next_t = t + self.period_s
        kpi = self._kpi(kpm)
        out = self.rapp.plan(self.intent, self.hour, kpi={"thp_mbps": kpi["camera_thp_mbps"],
                                                           "delay_ms": kpi["camera_delay_ms"]})
        delivered = []
        stream = getattr(self.baseline, "stream", None)
        for type_id, body in out["policies"].items():
            if type_id == "20001":
                if stream is not None:
                    stream.app.a1_policies.put_policy("20001", self.INSTANCES[type_id], body)
                    delivered.append("20001->RDL")
                continue
            target = {"21000": "ranslicer_greenran", "21001": "energysaver_greenran"}[type_id]
            app = self.apps.get(target)
            if app is not None:
                app.handle_a1(json.dumps({"operation": "CREATE", "policy_type_id": int(type_id),
                                          "policy_instance_id": self.INSTANCES[type_id], "payload": body}).encode())
                delivered.append(f"{type_id}->{target}")
        return {"t": t, "kpi": kpi, "policies": out["policies"], "reasons": out["reasons"], "delivered": delivered}


def ue_sst_map(spec: Dict[str, Any], groups_sst: List[int]) -> Dict[int, int]:
    """Índice do UE -> SST, pelos tamanhos dos grupos em --ueGroups (na ordem)."""
    arg = next((a for a in spec.get("args", []) if a.startswith("--ueGroups=")), "")
    sizes = [int(g.split(",")[0]) for g in arg.split("=", 1)[1].split(";")] if arg else []
    out, u = {}, 0
    for k, n in enumerate(sizes):
        for _ in range(n):
            out[u] = int(groups_sst[k]) if k < len(groups_sst) else 1
            u += 1
    return out


def ue_offered_mbps(spec: Dict[str, Any], default_packet_bytes: int = 1024) -> Dict[int, float]:
    """Índice do UE -> taxa oferecida pela aplicação (Mb/s): --packetSize × 8 ÷ intervalMs do grupo em --ueGroups.

    1024 B é o padrão de --packetSize no scenario_rdl_multicell.cc; os UEs seguem a ordem dos grupos.
    """
    args = spec.get("args", [])
    groups = next((a.split("=", 1)[1] for a in args if a.startswith("--ueGroups=")), "")
    size = next((int(a.split("=", 1)[1]) for a in args if a.startswith("--packetSize=")), default_packet_bytes)
    out, u = {}, 0
    for g in filter(None, groups.split(";")):
        f = g.split(",")
        for _ in range(int(f[0])):
            out[u] = size * 8 / (float(f[5]) * 1000.0)       # bytes/ms -> Mb/s
            u += 1
    return out


def build_full_drivers(spec: Dict[str, Any], run_id: str = "", derivado: tuple = ()) -> List[XAppDriver]:
    """Todas as xApps do cenário em malha fechada, pelo papel no catálogo e pelo closed_loop.json.

    ``derivado``: papéis que rodam com a derivada em Python no lugar do original (controle pareado, docs/16 §7).
    """
    import importlib
    from scripts.closed_loop.drivers import PythonXAppDriver
    from src.greenran.common import load_neighbors

    cfg = json.loads(CLOSED_LOOP_CFG.read_text(encoding="utf-8"))
    sc_cfg = {**cfg.get("defaults", {}), **cfg["scenarios"].get(spec.get("_id", ""), {})}
    ue_sst = ue_sst_map(spec, sc_cfg.get("ue_sst_groups", []))
    hour = int(sc_cfg.get("hour", 2))
    roles = sorted({p["xapp_id"] for p in spec["proposals"]})
    drivers: List[XAppDriver] = []
    made = set()
    for role in roles:
        rc = cfg["roles"].get(role)
        if rc is None:
            raise SystemExit(f"papel {role} sem xApp no closed_loop.json")
        if rc.get("same_as"):
            role, rc = rc["same_as"], cfg["roles"][rc["same_as"]]
        if role in made:
            continue
        made.add(role)
        if role in derivado:
            if "derivado" not in rc:
                raise SystemExit(f"--derivado {role}: o papel não tem derivada no closed_loop.json")
            rc = rc["derivado"]
        if rc.get("driver"):                      # original em processo próprio (docs/16 §4.3)
            cls = getattr(importlib.import_module(rc["driver"]), rc["class"])
            work = os.path.join(tempfile.gettempdir(), f"rdl_xapp_{role}_{run_id or os.getpid()}")
            kw = dict(rc.get("args", {}))
            if kw.get("anomaly_mode") == "oferta":
                kw["ue_offered_mbps"] = ue_offered_mbps(spec)
            drivers.append(cls(workdir=work, **kw))
            continue
        if rc.get("replay_catalog"):
            events = [e for e in rce.expand_proposals(spec) if e["xapp_id"] == role]
            drv = ReplayDriver(events, float(rce.load_catalog().get("decision_window_s", 0.2)))
            drv.name = f"replay:{role}"
            drivers.append(drv)
            continue
        cls = getattr(importlib.import_module(rc["module"]), rc["class"])
        from scripts.closed_loop.drivers import _NullTransport
        kwargs: Dict[str, Any] = {"transport": _NullTransport()}
        if rc["class"] in ("EnergySaver", "LoadBalancer"):
            kwargs["neighbors"] = load_neighbors()
        if rc["class"] == "EnergySaver":
            kwargs["hour_of"] = lambda t, h=hour: h
        app = cls(**kwargs)
        drivers.append(PythonXAppDriver(f"{rc['xapp_impl']}:{app.XAPP_ID}", app, ue_sst, rc["xapp_impl"]))
    return drivers


def run(args) -> int:
    catalog = rce.load_catalog()
    spec = dict(catalog["scenarios"][args.scenario], _id=args.scenario)
    window = float(catalog.get("decision_window_s", 0.2))
    run_id = args.run_id or f"cl_{args.scenario}_{args.baseline}_{args.xapps}_seed{args.seed}"
    run_dir = RUNS / run_id

    topo_file = None
    if spec.get("topology"):
        fd, topo_file = tempfile.mkstemp(suffix=".json", prefix="rdl_topology_")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(spec["topology"], fh)
        os.environ["RDL_TOPOLOGY_FILE"] = topo_file

    sock_path = os.path.join(tempfile.gettempdir(), f"rdl_ctl_{os.getpid()}.sock")
    if os.path.exists(sock_path):
        os.remove(sock_path)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(sock_path)
    server.listen(1)

    env = dict(os.environ, RDL_CONTROL_SOCKET=sock_path, RDL_DECISION_WINDOW=f"{window}")
    cmd = ["bash", str(rce.RUNNER), "--scenario", spec["ns3"], "--seed", str(args.seed),
           "--baseline", args.baseline, "--run-id", run_id]
    if args.baseline in EEVS:
        cmd += ["--extra-source", "HRDL_RUNTIME"]
    if args.no_build:
        cmd += ["--no-build"]
    cmd += ["--", *spec.get("args", []), *args.sim_arg]
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.Popen(cmd, env=env)

    baseline = WindowBaseline(args.baseline)
    drivers = build_drivers(args.xapps, spec, window, run_id, tuple(args.derivado))
    rapp = None
    if args.xapps == "completo":
        cfg = json.loads(CLOSED_LOOP_CFG.read_text(encoding="utf-8"))
        sc_cfg = {**cfg.get("defaults", {}), **cfg["scenarios"].get(args.scenario, {})}
        rapp = RAppStep(drivers, baseline, sc_cfg.get("intent", {}), int(sc_cfg.get("hour", 2)),
                        ue_sst_map(spec, sc_cfg.get("ue_sst_groups", [])))
    log_fh = chain_fh = chain = None
    use_chain = args.cadeia_e2 == "on" or (args.cadeia_e2 == "auto" and args.xapps == "completo")
    n_windows = n_props = n_actions = 0
    t = 0.0
    try:
        conn = None
        while conn is None:
            if proc.poll() is not None:
                print(f"[RDL-CTL] o executor terminou ({proc.returncode}) antes de conectar", flush=True)
                return proc.returncode or 1
            ready, _, _ = select.select([server], [], [], 1.0)
            if ready:
                conn, _ = server.accept()
        link = Ns3Link(conn)
        hello = link.read()
        if not hello or hello.get("type") != "hello":
            raise RuntimeError(f"esperava hello do ns-3, recebi {hello!r}")
        for d in drivers:
            d.on_hello(hello)
        run_dir.joinpath("raw").mkdir(parents=True, exist_ok=True)
        log_fh = open(run_dir / "raw" / "closed_loop_log.jsonl", "w", encoding="utf-8")
        log_fh.write(json.dumps({"type": "header", "scenario": args.scenario, "baseline": args.baseline,
                                 "xapps": args.xapps, "drivers": [d.name for d in drivers], "seed": args.seed,
                                 "window_s": window, "hello": hello}, ensure_ascii=False) + "\n")
        if use_chain:                             # ciclo NORI S8 (docs/16 §10.1): setup e subscrições
            from scripts.closed_loop.e2_chain import E2Chain
            chain_fh = open(run_dir / "raw" / "e2_chain.jsonl", "w", encoding="utf-8")
            chain = E2Chain(chain_fh, window)
            chain.setup(hello)
            chain.subscribe([d.name for d in drivers])
        while True:
            msg = link.read()
            if msg is None or msg.get("type") == "end":
                break
            t = float(msg["t"])
            if chain is not None:                 # KPM_t0 aos assinantes; ACK/Failure dos controles anteriores
                chain.indication(msg)
            a1_event = rapp.step(msg) if rapp is not None else None
            proposals: List[Dict[str, Any]] = []
            notes: List[Dict[str, Any]] = []
            for d in drivers:
                proposals += d.on_kpm(msg)
                dlog = getattr(d, "log", None)
                if dlog:
                    notes += [dict(n, driver=d.name) for n in dlog]
                    dlog.clear()
            proposals.sort(key=lambda e: (e["t"], e["id"]))
            actions, entry = baseline.decide(proposals, t)
            if chain is not None:                 # decisão gravada e uma RIC Control Request por ação
                actions = chain.dispatch(t, actions, entry)
            chosen = {a["id"] for a in actions}
            for d in drivers:
                d.on_decision(chosen)
            log_fh.write(json.dumps({"type": "window", "t": t, "kpm": msg, "a1": a1_event, "proposals": proposals,
                                     "xapp_controls": notes, "decision": entry, "actions": actions},
                                    ensure_ascii=False) + "\n")
            log_fh.flush()
            link.send_actions(actions)
            n_windows += 1
            n_props += len(proposals)
            n_actions += len(actions)
        if chain is not None:
            summary = chain.close(t)
            chain_fh.close()
            chain_fh = None
            print("[RDL-E2] cadeia: " + " ".join(f"{k}={v}" for k, v in summary.items()), flush=True)
        log_fh.close()
        log_fh = None
        print(f"[RDL-CTL] {n_windows} janelas, {n_props} propostas, {n_actions} ações", flush=True)
        return proc.wait()
    finally:
        if log_fh is not None:
            log_fh.close()
        if chain_fh is not None:
            chain_fh.close()
        baseline.close()
        for d in drivers:
            d.close()
            out = getattr(d, "stdout_log", None)   # log do processo da xApp original, guardado na execução
            if out is not None and Path(out).exists():
                run_dir.joinpath("logs").mkdir(parents=True, exist_ok=True)
                shutil.copyfile(out, run_dir / "logs" / f"xapp_{d.name.split(':')[-1]}.log")
        server.close()
        if os.path.exists(sock_path):
            os.remove(sock_path)
        if topo_file and os.path.exists(topo_file):
            os.remove(topo_file)
        if proc.poll() is None:
            time.sleep(0.5)
            if proc.poll() is None:
                proc.terminate()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--baseline", required=True, choices=["B0", "B1", "B2", "B3", "B3A", "B3M"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--xapps", default="replay", help="replay (gate E1) | originais (docs/16, E2–E4)")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--sim-arg", action="append", default=[])
    ap.add_argument("--cadeia-e2", choices=["auto", "on", "off"], default="auto",
                    help="ciclo NORI S8 (docs/16 §10.1): auto = ligado com --xapps completo")
    ap.add_argument("--derivado", action="append", default=[], metavar="PAPEL",
                    help="papel que roda com a derivada em Python (controle pareado), ex.: traffic_steering")
    args = ap.parse_args(argv)
    if os.name == "nt":
        raise SystemExit("rode no Ubuntu do WSL: o ns-3 e o socket Unix ficam no Linux")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
