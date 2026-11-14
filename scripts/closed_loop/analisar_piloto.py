#!/usr/bin/env python3
# Autor: George Barbosa
"""
Resumo das execuções de malha fechada (piloto E7 do docs/16): por execução, propostas por xApp e parâmetro,
janelas com conflito (duas ou mais propostas para o mesmo gNB e recurso), decisões, ações por status,
reversões de PRB_QUOTA (oscilação), políticas A1 e KPIs agregados das células.

Uso: python scripts/closed_loop/analisar_piloto.py [--seed 16901] [--prefix cl_piloto_] [--out reports/avaliacao/...]
Gera resumo_execucoes.csv, propostas_por_xapp.csv e resumo.md no diretório de saída.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# recursos disputados: parâmetros que agem sobre a mesma grandeza do gNB
RESOURCE = {"TX_POWER": "potencia", "CELL_STATE": "estado_celula", "PRB_QUOTA": "prb", "HANDOVER": "associacao_ue",
            "BEAM": "feixe", "MCS": "mcs"}


def _reversals(series):
    """Número de inversões de sentido numa série de valores aplicados (sobe-desce-sobe conta 2)."""
    signs = [1 if b > a else -1 for a, b in zip(series, series[1:]) if b != a]
    return sum(1 for a, b in zip(signs, signs[1:]) if a != b)


def analyze_run(run: Path, horizon_s: float = 5.0):
    man = json.loads((run / "execution_manifest.json").read_text(encoding="utf-8"))
    header, windows = None, []
    for line in (run / "raw" / "closed_loop_log.jsonl").read_text(encoding="utf-8").splitlines():
        w = json.loads(line)
        if w.get("type") == "header":
            header = w
        elif w.get("type") == "window":
            windows.append(w)
    by_xapp = Counter()
    conflict_windows, conflict_pairs = 0, Counter()
    selected = 0
    a1_events = 0
    timeline = defaultdict(list)          # (gnb, recurso) -> [(t, xapp)] das propostas
    for w in windows:
        props = w.get("proposals") or []
        a1_events += 1 if w.get("a1") else 0
        selected += len((w.get("decision") or {}).get("selected") or [])
        groups = defaultdict(set)
        for p in props:
            by_xapp[(p["xapp_id"], p["parameter"])] += 1
            key = (p["gnb"], RESOURCE.get(p["parameter"], p["parameter"]))
            groups[key].add(p["xapp_id"])
            timeline[key].append((float(p["t"]), p["xapp_id"]))
        hit = [xs for xs in groups.values() if len(xs) > 1]
        if hit:
            conflict_windows += 1
            for xs in hit:
                conflict_pairs[" x ".join(sorted(xs))] += 1
    # conflito em sequência: xApp diferente propõe no mesmo gNB e recurso até horizon_s depois de outra
    seq_conflicts, seq_pairs = 0, Counter()
    for key, ev in timeline.items():
        ev.sort()
        for i, (t, x) in enumerate(ev):
            others = {x2 for t2, x2 in ev[i + 1:] if t2 - t <= horizon_s and x2 != x}
            for x2 in others:
                seq_conflicts += 1
                seq_pairs[" x ".join(sorted((x, x2))) + f" [{key[1]}]"] += 1
    status, applied = Counter(), defaultdict(list)
    with open(run / "raw" / "rdl_actuation_log.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            status[r["status"]] += 1
            if r["status"] == "APPLIED":
                applied[(r["gnb"], r["parameter"])].append(float(r["value"]))
    prb_rev = sum(_reversals(v) for (g, p), v in applied.items() if p == "PRB_QUOTA")
    thp_t, delays = defaultdict(float), []
    with open(run / "raw" / "rdl_kpi_timeseries.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if float(r["t_end_s"]) < 1.0:
                continue
            thp_t[r["t_end_s"]] += float(r["throughput_mbps"] or 0.0)
            if r["mean_delay_ms"] not in ("", "nan", None):
                delays.append(float(r["mean_delay_ms"]))
    return {
        "execucao": run.name, "cenario": (header or {}).get("scenario", man.get("scenario")), "baseline": man.get("baseline"),
        "commit": man.get("repo_git_sha"), "drivers": " ".join((header or {}).get("drivers", [])),
        "janelas": len(windows), "eventos_a1": a1_events, "propostas": sum(by_xapp.values()),
        "janelas_com_conflito": conflict_windows, f"conflitos_em_{horizon_s:g}s": seq_conflicts,
        "selecionadas": selected, "nao_selecionadas": sum(by_xapp.values()) - selected,
        "aplicadas": status.get("APPLIED", 0), "recusadas": sum(v for k, v in status.items() if k != "APPLIED"),
        "status": " ".join(f"{k}={v}" for k, v in sorted(status.items())),
        "reversoes_prb_quota": prb_rev,
        "vazao_media_mbps": round(statistics.fmean(thp_t.values()), 3) if thp_t else None,
        "atraso_medio_ms": round(statistics.fmean(delays), 3) if delays else None,
        "pares_em_conflito": "; ".join(f"{k}={v}" for k, v in conflict_pairs.most_common()),
        "pares_em_sequencia": "; ".join(f"{k}={v}" for k, v in seq_pairs.most_common()),
    }, by_xapp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", default="16901")
    ap.add_argument("--prefix", default="cl_piloto_")
    ap.add_argument("--out", default=None)
    ap.add_argument("--horizon", type=float, default=5.0, help="horizonte do conflito em sequência (s)")
    a = ap.parse_args()
    runs = sorted((ROOT / "experiments" / "runs").glob(f"{a.prefix}*_seed{a.seed}"))
    out = Path(a.out) if a.out else ROOT / "reports" / "avaliacao" / f"piloto_malha_fechada_seed{a.seed}"
    out.mkdir(parents=True, exist_ok=True)
    rows, xrows = [], []
    for run in runs:
        row, by_xapp = analyze_run(run, a.horizon)
        rows.append(row)
        for (x, p), n in sorted(by_xapp.items()):
            xrows.append({"execucao": run.name, "cenario": row["cenario"], "baseline": row["baseline"],
                          "xapp_id": x, "parametro": p, "propostas": n})
    with open(out / "resumo_execucoes.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(out / "propostas_por_xapp.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["execucao", "cenario", "baseline", "xapp_id", "parametro", "propostas"])
        w.writeheader()
        w.writerows(xrows)
    cols = ["cenario", "baseline", "commit", "propostas", "janelas_com_conflito", f"conflitos_em_{a.horizon:g}s",
            "nao_selecionadas", "aplicadas", "recusadas",
            "reversoes_prb_quota", "vazao_media_mbps", "atraso_medio_ms"]
    md = [f"# Piloto da malha fechada, semente {a.seed}", "",
          "Gerado por `scripts/closed_loop/analisar_piloto.py`. Exploratório (docs/16, E7): serve para fixar o "
          "pré-registro 11, não para conclusões.", "",
          "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    md += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    md += ["", "## Propostas por xApp", "", "| cenario | baseline | xapp_id | parametro | propostas |", "|---|---|---|---|---|"]
    md += [f"| {r['cenario']} | {r['baseline']} | {r['xapp_id']} | {r['parametro']} | {r['propostas']} |" for r in xrows]
    md += ["", "## Pares de xApps em conflito (janelas)", ""]
    md += [f"- {r['cenario']}/{r['baseline']}: mesma janela: {r['pares_em_conflito'] or 'nenhum'}; "
           f"em sequência ({a.horizon:g} s): {r['pares_em_sequencia'] or 'nenhum'}" for r in rows]
    (out / "resumo.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{len(rows)} execuções -> {out}")


if __name__ == "__main__":
    main()
