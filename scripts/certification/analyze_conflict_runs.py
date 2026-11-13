#!/usr/bin/env python3
"""
Análise das execuções de conflito (experiments/runs/nr_<S>_<B>_seed<N>/).

Usa somente a evidência gravada pela execução:
  raw/rdl_kpi_timeseries.csv  vazão e atraso por célula e janela, medidos no ns-3;
  raw/rdl_actuation_log.csv   ações efetivamente aplicadas na RAN simulada;
  raw/decision_log.json       propostas e decisões do baseline;
  raw/rdl_cell_state.csv      ocupação de recursos, potência de TX e sono emulado de todas as células
                              por janela (RdlCellEnergySampler; só nas execuções com essa instrumentação).
Execuções que não passam no certificador (hashes, manifesto, origem) são ignoradas.

Métricas por execução:
  thp_pre / thp_conflict / thp_post  vazão agregada média (Mbps) antes, durante e
                                      depois da janela de conflito do catálogo;
  delay_conflict_ms                  atraso médio ponderado por pacote na janela;
  actions_applied, handovers         ações APPLIED na RAN;
  unsafe_applied                     ações aplicadas fora dos limites físicos
                                      (TX_POWER > 43 dBm ou < -10 dBm; PRB_QUOTA fora de 0-100);
  oscillations                       trocas de valor num mesmo alvo (gNB, parâmetro);
  energia (docs/17 §5)               energy_conflict_tr1/_tr2 (u.r.·s, 3GPP TR 38.864 Cat. 1/Cat. 2),
                                      energy_conflict_j (J, EARTH), energia por bit, ocupação de PRB,
                                      tempo de sono, vazamento em sono e parcela UL, estimados pelo modelo
                                      (scripts/certification/energy_model.py) a partir da ocupação medida
                                      no simulador. Sem raw/rdl_cell_state.csv, essas colunas ficam vazias
                                      ("—"); energy_proxy_commanded (nível 0, só com o log de atuação) é proxy.
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
import energy_model  # noqa: E402

# S0–S15 e G1–G2; B0–B3 e variantes do B3 (B3A: EEVS aditivo, pré-registro 09)
RUN_PATTERN = re.compile(r"^nr_([SG]\d+)_(B\d[A-Z]?)_seed(\d+)$")
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


def _arg(spec: Dict[str, Any], name: str, default: str) -> str:
    return next((a.split("=", 1)[1] for a in spec.get("args", []) if a.startswith(f"--{name}=")), default)


def _power_alloc_from_command(manifest: Dict[str, Any]) -> str:
    """Modo de potência pela linha de comando (execuções sem rdl_cell_state.csv; padrão do 5G-LENA: used)."""
    m = re.search(r"--powerAllocation=(\w+)", str(manifest.get("command", "")))
    return m.group(1) if m else "used"


def analyze_run(run_dir: Path, catalog: Dict[str, Any], models: Dict[str, Any] | None = None) -> Dict[str, Any]:
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
    cell_path = run_dir / "raw" / "rdl_cell_state.csv"
    models = models or energy_model.load_models()
    energy = energy_model.energy_metrics(
        read_csv(cell_path) if cell_path.exists() else None, kpi, actuation, models, c0, c1,
        bandwidth_hz=float(_arg(spec, "bandwidth", "100e6")), sim_end_s=sim_time,
        n_gnbs=len([g for g in _arg(spec, "gnbs", "0,0,25;200,0,25").split(";") if g]))
    if energy["power_alloc"] is None:
        energy["power_alloc"] = _power_alloc_from_command(manifest)
    return {
        "run_id": run_dir.name, "scenario": scenario, "baseline": baseline, "seed": seed,
        "run_status": manifest.get("run_status"),
        "thp_pre": thp_pre, "thp_conflict": thp_conflict, "thp_post": thp_post,
        "delay_conflict_ms": delay_conflict,
        "actions_applied": len(applied),
        "handovers": sum(1 for a in applied if a["parameter"] == "HANDOVER"),
        "unsafe_applied": unsafe, "oscillations": oscillations,
        **energy,
    }


METRICS = ["thp_pre", "thp_conflict", "thp_post", "delay_conflict_ms", "actions_applied", "handovers",
           "unsafe_applied", "oscillations", *energy_model.ENERGY_METRICS]
# Economia contra o B0, pareada por semente (a métrica do TR 38.864): 1 − E(Bx)/E(B0), em %.
SAVINGS = {"energy_conflict_tr1": "saving_vs_b0_tr1_pct", "energy_conflict_tr2": "saving_vs_b0_tr2_pct",
           "energy_conflict_j": "saving_vs_b0_j_pct"}


def add_paired_savings(rows: List[Dict[str, Any]]) -> None:
    """Acrescenta a cada execução a economia contra o B0 da mesma semente, cenário e modo de potência
    (o B0U de uma campanha com --run-suffix U é o B0 dela); None sem par."""
    b0 = {(r["scenario"], r["seed"], r.get("power_alloc")): r for r in rows if r["baseline"].startswith("B0")}
    for r in rows:
        ref = b0.get((r["scenario"], r["seed"], r.get("power_alloc")))
        for metric, key in SAVINGS.items():
            e, e0 = r.get(metric), (ref or {}).get(metric)
            r[key] = 100.0 * (1.0 - e / e0) if e is not None and e0 else None


def aggregate(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[tuple, List[Dict[str, Any]]] = {}
    for r in rows:
        groups.setdefault((r["scenario"], r["baseline"]), []).append(r)
    out = []
    for (scenario, baseline), rs in sorted(groups.items()):
        entry: Dict[str, Any] = {"scenario": scenario, "baseline": baseline, "n": len(rs),
                                 "seeds": sorted(r["seed"] for r in rs)}
        entry["power_alloc"] = sorted({str(r.get("power_alloc")) for r in rs})
        for metric in METRICS + list(SAVINGS.values()):
            values = [r[metric] for r in rs if r.get(metric) is not None]
            if not values:
                entry[metric] = None
                continue
            mean = statistics.fmean(values)
            sd = statistics.stdev(values) if len(values) > 1 else None
            ci = t_quantile(len(values) - 1) * sd / math.sqrt(len(values)) if sd is not None else None
            entry[metric] = {"mean": mean, "sd": sd, "ci95": ci}
        out.append(entry)
    return out


def fmt(cell, digits: int = 2, scale: float = 1.0) -> str:
    if cell is None:
        return "—"
    if cell["ci95"] is None:
        return f"{cell['mean'] * scale:.{digits}f}"
    return f"{cell['mean'] * scale:.{digits}f} ± {cell['ci95'] * scale:.{digits}f}"


def render_energy(agg, models_sha256: str) -> List[str]:
    """Tabela de energia por cenário × baseline e por modelo (só grupos com rdl_cell_state.csv)."""
    groups = [a for a in agg if a.get("energy_conflict_tr1") is not None]
    if not groups:
        return []
    return [
        "", "## Energia na janela de conflito (docs/17)", "",
        "Estimada pelos modelos 3GPP TR 38.864 V18.1.0 (Cat. 1 principal; Cat. 2 robustez) e EARTH (Auer et al., "
        "2011; um TRX de macro por célula) a partir da ocupação de recursos medida no simulador "
        "(`raw/rdl_cell_state.csv`); não é energia medida. Parâmetros: `simulations/ns3/energy/energy_models.json`, "
        f"sha256 `{models_sha256}`. Economia: 1 − E(Bx)/E(B0), pareada por semente.", "",
        "| Cenário | Baseline | n | Potência | TR Cat. 1 (u.r.·s) | TR Cat. 2 (u.r.·s) | EARTH (J) | "
        "Economia TR1 vs B0 (%) | Economia EARTH vs B0 (%) | µJ/bit (EARTH) | Ocupação de PRB | Sono (s) | "
        "Vazamento em sono (REG) | Parcela UL |",
        "| :-- | :-- | --: | :-- | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: |",
    ] + [
        f"| {a['scenario']} | {a['baseline']} | {a['n']} | {', '.join(a['power_alloc'])} | "
        f"{fmt(a['energy_conflict_tr1'], 1)} | {fmt(a['energy_conflict_tr2'], 1)} | {fmt(a['energy_conflict_j'], 1)} | "
        f"{fmt(a['saving_vs_b0_tr1_pct'], 1)} | {fmt(a['saving_vs_b0_j_pct'], 1)} | "
        f"{fmt(a['energy_per_bit_j'], 3, 1e6)} | {fmt(a['prb_occupancy_conflict'], 3)} | {fmt(a['sleep_time_s'], 2)} | "
        f"{fmt(a['sleep_leak_reg'], 0)} | {fmt(a['ul_share'], 4)} |"
        for a in groups
    ]


def render(agg, rows, skipped, generated_at, models_sha256: str = "") -> str:
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
    lines += render_energy(agg, models_sha256)
    lines += ["", "## Execuções", "",
              "| run_id | seed | vazão no conflito | atraso | ações | inseguras | oscilações | potência | "
              "TR Cat. 1 (u.r.·s) | EARTH (J) | proxy comandado |",
              "| :-- | --: | --: | --: | --: | --: | --: | :-- | --: | --: | --: |"]

    def num(v, d=2):
        return f"{v:.{d}f}" if v is not None else "—"

    for r in rows:
        lines.append(f"| `{r['run_id']}` | {r['seed']} | {num(r['thp_conflict'])} | {num(r['delay_conflict_ms'])} | "
                     f"{r['actions_applied']} | {r['unsafe_applied']} | {r['oscillations']} | "
                     f"{r.get('power_alloc') or '—'} | {num(r.get('energy_conflict_tr1'), 1)} | "
                     f"{num(r.get('energy_conflict_j'), 1)} | {num(r.get('energy_proxy_commanded'))} |")
    lines += ["", "O proxy comandado (nível 0) é a média no tempo de Σ gNBs ligada × cota de PRB aplicada, só com o "
              "log de atuação: não é energia e serve só às execuções sem `raw/rdl_cell_state.csv`."]
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
    models = energy_model.load_models()
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
        rows.append(analyze_run(run_dir, catalog, models))
    add_paired_savings(rows)
    agg = aggregate(rows)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_md = render(agg, rows, skipped, generated_at, models["sha256"])
    print(report_md)
    if not args.no_write and rows:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        stamp = generated_at.replace(":", "").replace("-", "")
        (out / f"conflict_analysis_{stamp}.md").write_text(report_md, encoding="utf-8")
        (out / f"conflict_analysis_{stamp}.json").write_text(
            json.dumps({"generated_at_utc": generated_at, "energy_models_sha256": models["sha256"],
                        "aggregate": agg, "runs": rows,
                        "skipped": skipped}, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Relatórios em {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
