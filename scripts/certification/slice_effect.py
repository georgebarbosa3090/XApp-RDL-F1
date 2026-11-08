#!/usr/bin/env python3
"""
Efeito do RIC Control na RAN (fase 4): vazão por fatia antes e depois do Control.

O KPM do NORI não mede vazão por UE (``DRB.UEThpDl`` sai sempre 0) e calcula PRB por UE a partir
de símbolos. O efeito é medido na referência da simulação: ``raw/slice_series.csv``, gravado pela
variante ``nori-rc-slicing-flowmon`` a cada 0,5 s simulado com os contadores acumulados do
FlowMonitor por UE/fatia, o tempo simulado e o relógio de parede.

Procedimento (constantes fixadas antes das execuções):

1. O instante do RIC Control no PCAP (relógio de parede do pod, o mesmo do ns-3) é convertido em
   tempo simulado por interpolação na série (simulação em tempo real).
2. Vazão por fatia na janela ANTES = [t_c - W, t_c] e DEPOIS = [t_c + S, t_c + S + W].
3. As cotas são lidas dos bytes do Control no PCAP (decodificados com src/e2/v3/codec.py), não do
   registro da xApp.
4. Expectativa por fatia, a partir da parte que cada fatia usava antes (p_s = vazão_s / total):
   - teto < 100·p_s − MARGEM_PP: a vazão deve cair ao menos QUEDA_MIN;
   - caso contrário: a vazão não pode cair mais que QUEDA_MIN.
5. Veredito: CONSISTENT se há ao menos uma fatia com queda esperada e todas as expectativas se
   cumprem; INCONSISTENT se alguma falha; NOT_TESTABLE se nenhuma fatia tem teto abaixo da parte
   que usava ou se a série não cobre as janelas.

Saída: ``experiments/e2_dissection/<run>/slice_effect.json`` (hash do CSV de origem incluído).

Uso:
    python scripts/certification/slice_effect.py --run nori_hrdl_loop_seed1
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WINDOW_S = 4.0       # W
SETTLE_S = 2.0       # S
MARGIN_PP = 5.0      # pontos percentuais
MIN_DROP = 0.05      # 5 %
SCHEMA = "xapp-rdl/slice-effect/v1"


def load_series(path: Path) -> Dict[int, List[Tuple[float, float, float]]]:
    """sst -> [(sim_time_s, wall_epoch_s, rx_bytes acumulado)] somando os UEs de cada fatia."""
    per_sample: Dict[Tuple[float, int], List[float]] = {}
    walls: Dict[float, float] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t, sst = float(row["sim_time_s"]), int(row["sst"])
            walls[t] = float(row["wall_epoch_s"])
            per_sample.setdefault((t, sst), []).append(float(row["rx_bytes"]))
    series: Dict[int, List[Tuple[float, float, float]]] = {}
    for (t, sst), values in sorted(per_sample.items()):
        series.setdefault(sst, []).append((t, walls[t], sum(values)))
    return series


def wall_to_sim(series: Dict[int, List[Tuple[float, float, float]]], wall: float) -> Optional[float]:
    points = sorted({(w, t) for rows in series.values() for t, w, _ in rows})
    for (w0, t0), (w1, t1) in zip(points, points[1:]):
        if w0 <= wall <= w1:
            return t0 if w1 == w0 else t0 + (wall - w0) * (t1 - t0) / (w1 - w0)
    return None


def throughput_mbps(rows: List[Tuple[float, float, float]], start: float, end: float) -> Optional[float]:
    """Vazão média (Mb/s) entre as amostras mais próximas dentro de [start, end]."""
    inside = [r for r in rows if start - 1e-9 <= r[0] <= end + 1e-9]
    if len(inside) < 2 or inside[-1][0] - inside[0][0] < 0.5 * (end - start):
        return None
    (t0, _, b0), (t1, _, b1) = inside[0], inside[-1]
    return (b1 - b0) * 8.0 / (t1 - t0) / 1e6


def control_quotas(dissection: Dict[str, Any], ddir: Path) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    roles = dissection.get("chain_roles") or {}
    by_index = {m["index"]: m for m in dissection.get("messages", [])}
    ctrl = by_index.get(roles.get("control_request") or -1)
    if not ctrl or not ctrl.get("file"):
        return None, []
    from src.e2.v3 import codec
    pdu = codec.decode_e2ap_pdu((ddir / ctrl["file"]).read_bytes())
    quotas = codec.E2smCodec().rc_decode_slice_quotas(pdu["control_message"])
    return ctrl, [q.__dict__ for q in quotas]


def evaluate(series: Dict[int, List[Tuple[float, float, float]]], t_control: float,
             quotas: List[Dict[str, Any]]) -> Dict[str, Any]:
    before_w = (t_control - WINDOW_S, t_control)
    after_w = (t_control + SETTLE_S, t_control + SETTLE_S + WINDOW_S)
    caps = {int(q["sst"]): float(q["max_prb_ratio"]) for q in quotas}
    stats: Dict[str, Dict[str, Any]] = {}
    before = {sst: throughput_mbps(rows, *before_w) for sst, rows in series.items()}
    after = {sst: throughput_mbps(rows, *after_w) for sst, rows in series.items()}
    if any(v is None for v in list(before.values()) + list(after.values())) or not caps:
        return {"verdict": "NOT_TESTABLE", "reason": "série não cobre as janelas ou Control sem cotas",
                "window_before": before_w, "window_after": after_w}
    total = sum(before.values())
    decrease_expected = False
    all_ok = True
    for sst in sorted(series):
        share = 100.0 * before[sst] / total if total > 0 else 0.0
        cap = caps.get(sst, 100.0)
        expect = "decrease" if cap < share - MARGIN_PP else "no_decrease"
        change = (after[sst] - before[sst]) / before[sst] if before[sst] > 0 else 0.0
        ok = change <= -MIN_DROP if expect == "decrease" else change >= -MIN_DROP
        decrease_expected |= expect == "decrease"
        all_ok &= ok
        stats[str(sst)] = {"cap_max_prb_pct": cap, "share_before_pct": round(share, 2),
                           "throughput_before_mbps": round(before[sst], 3), "throughput_after_mbps": round(after[sst], 3),
                           "relative_change": round(change, 4), "expectation": expect, "met": ok}
    verdict = "NOT_TESTABLE" if not decrease_expected else ("CONSISTENT" if all_ok else "INCONSISTENT")
    return {"verdict": verdict, "window_before": before_w, "window_after": after_w, "slices": stats}


def analyze(run_id: str, runs_dir: Path = ROOT / "experiments" / "runs",
            dissection_root: Path = ROOT / "experiments" / "e2_dissection") -> Dict[str, Any]:
    run_dir, ddir = runs_dir / run_id, dissection_root / run_id
    csv_path = run_dir / "raw" / "slice_series.csv"
    dissection = json.loads((ddir / "e2_messages.json").read_text(encoding="utf-8"))
    out: Dict[str, Any] = {
        "schema": SCHEMA, "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scripts/certification/slice_effect.py",
        "constants": {"window_s": WINDOW_S, "settle_s": SETTLE_S, "margin_pp": MARGIN_PP, "min_drop": MIN_DROP},
        "source_csv": f"raw/slice_series.csv",
        "source_csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest() if csv_path.exists() else None,
        "source_dissection_sha256": hashlib.sha256((ddir / "e2_messages.json").read_bytes()).hexdigest(),
    }
    if not csv_path.exists():
        out.update(verdict="NOT_TESTABLE", reason="execução sem raw/slice_series.csv")
    else:
        ctrl, quotas = control_quotas(dissection, ddir)
        series = load_series(csv_path)
        if not ctrl:
            out.update(verdict="NOT_TESTABLE", reason="nenhum RIC Control na cadeia do PCAP")
        else:
            t_c = wall_to_sim(series, float(ctrl["time_epoch"]))
            out.update(control_frame=ctrl["frame"], control_wall_epoch=ctrl["time_epoch"], control_sim_time_s=t_c,
                       quotas_from_pcap=quotas)
            if t_c is None:
                out.update(verdict="NOT_TESTABLE", reason="instante do Control fora da série (relógio de parede)")
            else:
                out.update(evaluate(series, t_c, quotas))
    (ddir / "slice_effect.json").write_bytes((json.dumps(out, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return out


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True)
    args = parser.parse_args(argv)
    r = analyze(args.run)
    print(f"Efeito do Control ({args.run}): {r['verdict']}" + (f" — {r['reason']}" if r.get("reason") else ""))
    if r.get("control_sim_time_s") is not None:
        print(f"  Control no quadro {r['control_frame']}, t_sim = {r['control_sim_time_s']:.2f} s; cotas do PCAP: {r['quotas_from_pcap']}")
    for sst, s in (r.get("slices") or {}).items():
        print(f"  SST {sst}: teto {s['cap_max_prb_pct']:.0f} %, parte antes {s['share_before_pct']:.1f} %; "
              f"{s['throughput_before_mbps']:.2f} -> {s['throughput_after_mbps']:.2f} Mb/s "
              f"({100 * s['relative_change']:+.1f} %); esperado {s['expectation']}: {'cumprido' if s['met'] else 'NÃO cumprido'}")
    return 0 if r["verdict"] == "CONSISTENT" else 1


if __name__ == "__main__":
    sys.exit(main())
