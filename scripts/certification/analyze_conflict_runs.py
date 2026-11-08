#!/usr/bin/env python3
"""
Análise das execuções de conflito (experiments/runs/nr_<S>_<B>_seed<N>/).

Usa somente a evidência gravada pela execução:
  raw/rdl_kpi_timeseries.csv  vazão e atraso por célula e janela, medidos no ns-3;
  raw/rdl_actuation_log.csv   ações efetivamente aplicadas na RAN simulada;
  raw/decision_log.json       propostas e decisões do baseline.
Execuções que não passam no certificador (hashes, manifesto, origem) são ignoradas.

Métricas por execução:
  thp_pre / thp_conflict / thp_post  vazão agregada média (Mbps) antes, durante e
                                      depois da janela de conflito do catálogo;
  delay_conflict_ms                  atraso médio ponderado por pacote na janela;
  actions_applied, handovers         ações APPLIED na RAN;
  unsafe_applied                     ações aplicadas fora dos limites físicos
                                      (TX_POWER > 43 dBm ou < -10 dBm; PRB_QUOTA fora de 0-100);
  oscillations                       trocas de valor num mesmo alvo (gNB, parâmetro).
Agregado por cenário × baseline: média, desvio-padrão e IC 95% (t de Student) com n >= 2.

Uso: python scripts/certification/analyze_conflict_runs.py [--out reports/conflicts]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "certification"))
import certify_chain  # noqa: E402

RUN_PATTERN = re.compile(r"^nr_(S\d+)_(B\d)_seed(\d+)$")
TX_POWER_RANGE = (-10.0, 43.0)
T_975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262,
         10: 2.228, 14: 2.145, 19: 2.093, 29: 2.045}


def t_quantile(df: int) -> float:
    if df in T_975:
        return T_975[df]
    keys = sorted(T_975)
    return T_975[max(k for k in keys if k <= df)] if df < 30 else 1.96


def read_csv(path: Path) -> List[Dict[str, str]]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def window_stats(rows, t0, t1):
    by_t: Dict[float, List[Dict[str, str]]] = {}
    for r in rows:
        t = float(r["t_end_s"])
        if t0 < t <= t1:
            by_t.setdefault(t, []).append(r)
    if not by_t:
        return None, None
    thp = statistics.fmean(sum(float(r["throughput_mbps"]) for r in rs) for rs in by_t.values())
    packets = sum(int(r["rx_packets"]) for rs in by_t.values() for r in rs)
    delay = (sum(float(r["mean_delay_ms"]) * int(r["rx_packets"]) for rs in by_t.values() for r in rs) / packets
             if packets else None)
    return thp, delay


def analyze_run(run_dir: Path, catalog: Dict[str, Any]) -> Dict[str, Any]:
    m = RUN_PATTERN.match(run_dir.name)
    scenario, baseline, seed = m.group(1), m.group(2), int(m.group(3))
    spec = catalog["scenarios"][scenario]
    c0, c1 = spec["conflict_window_s"]
    manifest = json.loads((run_dir / "execution_manifest.json").read_text(encoding="utf-8"))
    sim_time = next((float(a.split("=")[1]) for a in spec.get("args", []) if a.startswith("--simTime=")), c1 + 5)
    kpi = read_csv(run_dir / "raw" / "rdl_kpi_timeseries.csv")
    actuation = read_csv(run_dir / "raw" / "rdl_actuation_log.csv") if (run_dir / "raw" / "rdl_actuation_log.csv").exists() else []
    thp_pre, _ = window_stats(kpi, max(1.5, c0 - 5), c0)
    thp_conflict, delay_conflict = window_stats(kpi, c0, c1)
    thp_post, _ = window_stats(kpi, c1, sim_time - 0.5)
    applied = [a for a in actuation if a["status"] == "APPLIED"]
    unsafe = 0
    last: Dict[tuple, float] = {}
    oscillations = 0
    for a in applied:
        value = float(a["value"])
        if a["parameter"] == "TX_POWER" and not TX_POWER_RANGE[0] <= value <= TX_POWER_RANGE[1]:
            unsafe += 1
        if a["parameter"] == "PRB_QUOTA" and not 0 <= value <= 100:
            unsafe += 1
        key = (a["gnb"], a["parameter"])
        if key in last and last[key] != value:
            oscillations += 1
        last[key] = value
    return {
        "run_id": run_dir.name, "scenario": scenario, "baseline": baseline, "seed": seed,
        "run_status": manifest.get("run_status"),
        "thp_pre": thp_pre, "thp_conflict": thp_conflict, "thp_post": thp_post,
        "delay_conflict_ms": delay_conflict,
        "actions_applied": len(applied),
        "handovers": sum(1 for a in applied if a["parameter"] == "HANDOVER"),
        "unsafe_applied": unsafe, "oscillations": oscillations,
    }


METRICS = ["thp_pre", "thp_conflict", "thp_post", "delay_conflict_ms", "actions_applied", "handovers",
           "unsafe_applied", "oscillations"]


def aggregate(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[tuple, List[Dict[str, Any]]] = {}
    for r in rows:
        groups.setdefault((r["scenario"], r["baseline"]), []).append(r)
    out = []
    for (scenario, baseline), rs in sorted(groups.items()):
        entry: Dict[str, Any] = {"scenario": scenario, "baseline": baseline, "n": len(rs),
                                 "seeds": sorted(r["seed"] for r in rs)}
        for metric in METRICS:
            values = [r[metric] for r in rs if r[metric] is not None]
            if not values:
                entry[metric] = None
                continue
            mean = statistics.fmean(values)
            sd = statistics.stdev(values) if len(values) > 1 else None
            ci = t_quantile(len(values) - 1) * sd / math.sqrt(len(values)) if sd is not None else None
            entry[metric] = {"mean": mean, "sd": sd, "ci95": ci}
        out.append(entry)
    return out


def fmt(cell) -> str:
    if cell is None:
        return "—"
    if cell["ci95"] is None:
        return f"{cell['mean']:.2f}"
    return f"{cell['mean']:.2f} ± {cell['ci95']:.2f}"


def render(agg, rows, skipped, generated_at) -> str:
    lines = [
        "# Análise dos experimentos de conflito (ns-3.48 + 5G-LENA v5.1)", "",
        f"Gerado em {generated_at} por `scripts/certification/analyze_conflict_runs.py` a partir de "
        f"{len(rows)} execução(ões) elegível(is) em `experiments/runs/nr_*`.", "",
        "Avaliação em malha aberta: as propostas das xApps são decididas pelo baseline e aplicadas na RAN "
        "simulada; não há E2 nem realimentação de KPM. Valores: média ± IC 95% (t de Student) quando n ≥ 2.", "",
        "| Cenário | Baseline | n | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | "
        "Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras aplicadas | Oscilações |",
        "| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | --: |",
    ]
    for a in agg:
        lines.append(f"| {a['scenario']} | {a['baseline']} | {a['n']} | {fmt(a['thp_pre'])} | {fmt(a['thp_conflict'])} | "
                     f"{fmt(a['thp_post'])} | {fmt(a['delay_conflict_ms'])} | {fmt(a['actions_applied'])} | "
                     f"{fmt(a['handovers'])} | {fmt(a['unsafe_applied'])} | {fmt(a['oscillations'])} |")
    lines += ["", "## Execuções", "", "| run_id | seed | vazão no conflito | atraso | ações | inseguras | oscilações |",
              "| :-- | --: | --: | --: | --: | --: | --: |"]
    for r in rows:
        tc = f"{r['thp_conflict']:.2f}" if r["thp_conflict"] is not None else "—"
        dc = f"{r['delay_conflict_ms']:.2f}" if r["delay_conflict_ms"] is not None else "—"
        lines.append(f"| `{r['run_id']}` | {r['seed']} | {tc} | {dc} | {r['actions_applied']} | "
                     f"{r['unsafe_applied']} | {r['oscillations']} |")
    if skipped:
        lines += ["", "## Execuções ignoradas (não elegíveis no certificador)", ""]
        lines += [f"- `{run_id}`: {reason}" for run_id, reason in skipped]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-dir", default=str(ROOT / "experiments" / "runs"))
    parser.add_argument("--out", default=str(ROOT / "reports" / "conflicts"))
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    catalog = json.loads((ROOT / "simulations" / "ns3" / "conflicts" / "catalog.json").read_text(encoding="utf-8"))
    policy, lock = certify_chain.load_policy(), certify_chain.load_versions_lock()
    patterns = certify_chain.synthetic_run_id_patterns()
    rows, skipped = [], []
    for run_dir in sorted(Path(args.runs_dir).iterdir()):
        if not run_dir.is_dir() or not RUN_PATTERN.match(run_dir.name):
            continue
        report = certify_chain.certify_run(run_dir, policy, lock, patterns)
        if not report.publication_eligible:
            skipped.append((run_dir.name, "; ".join(f"{c.rule}: {c.detail}" for c in report.failed()) or report.classification))
            continue
        if not (run_dir / "raw" / "rdl_kpi_timeseries.csv").exists():
            skipped.append((run_dir.name, "sem série temporal de KPIs"))
            continue
        rows.append(analyze_run(run_dir, catalog))
    agg = aggregate(rows)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_md = render(agg, rows, skipped, generated_at)
    print(report_md)
    if not args.no_write and rows:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        stamp = generated_at.replace(":", "").replace("-", "")
        (out / f"conflict_analysis_{stamp}.md").write_text(report_md, encoding="utf-8")
        (out / f"conflict_analysis_{stamp}.json").write_text(
            json.dumps({"generated_at_utc": generated_at, "aggregate": agg, "runs": rows,
                        "skipped": skipped}, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Relatórios em {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
