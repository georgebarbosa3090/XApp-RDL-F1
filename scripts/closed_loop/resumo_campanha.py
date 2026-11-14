#!/usr/bin/env python3
# Autor: George Barbosa
"""
Painel de fim de campanha da malha fechada (para relato e workshop): o que aconteceu na cadeia inteira.

Lê só os artefatos de cada execução (``closed_loop_log.jsonl``, ``e2_chain.jsonl``, ``rdl_actuation_log.csv``,
``logs/xapp_*.log`` e manifesto) e mostra, por campanha:

1. execuções (cenário × baseline × semente, status, duração, commit);
2. rede: gNBs, UEs, UEs registrados (conectados), handovers, ping-pong, células dormindo, ajustes de potência;
3. mensagens: Indications KPM, propostas das xApps (RMR 30000), políticas A1 por tipo e destino (Non-RT RIC ->
   A1 -> RDL / xApps), RIC Control Request, ACK, Failure e timeout, recusas devolvidas às xApps;
4. conflitos (mesma janela e em sequência), pares e recursos, resoluções por regra (TVS/EEVS), oscilações;
5. controle da RAN: ações por parâmetro e status, ajustes por gNB;
6. regras e políticas: regra de decisão do baseline, estratégias de resolução, consultas ao grafo de conhecimento;
7. xApps originais em processo (TS: AD, QP, HandOff) e KPIs.

Campo que a execução não registra aparece como "não registrado" (nunca como zero).

Uso: python scripts/closed_loop/resumo_campanha.py --prefix cl_piloto_ --seed 16902 [--out reports/avaliacao/<dir>]
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
RESOURCE = {"TX_POWER": "potência", "CELL_STATE": "estado da célula", "PRB_QUOTA": "PRB", "HANDOVER": "associação de UE"}
A1_TARGET = {"20001": "RDL (pesos e limites)", "21000": "RANSlicer-GreenRAN (intenção de fatia)",
             "21001": "EnergySaver-GreenRAN (limiares de energia)", "20008": "Traffic Steering (limiar)"}
NR = "não registrado"


def _iso(s: Optional[str]) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
    except ValueError:
        return None


def _reversals(series: List[float]) -> int:
    signs = [1 if b > a else -1 for a, b in zip(series, series[1:]) if b != a]
    return sum(1 for a, b in zip(signs, signs[1:]) if a != b)


def analyze(run: Path, horizon_s: float = 5.0) -> Dict[str, Any]:
    man = json.loads((run / "execution_manifest.json").read_text(encoding="utf-8")) \
        if (run / "execution_manifest.json").exists() else {}
    header, windows = {}, []
    log = run / "raw" / "closed_loop_log.jsonl"
    for line in log.read_text(encoding="utf-8").splitlines() if log.exists() else []:
        w = json.loads(line)
        if w.get("type") == "header":
            header = w
        elif w.get("type") == "window":
            windows.append(w)
    hello = header.get("hello") or {}
    r: Dict[str, Any] = {"execucao": run.name, "cenario": header.get("scenario"), "baseline": header.get("baseline"),
                         "semente": header.get("seed"), "status": man.get("run_status", "sem manifesto"),
                         "commit": man.get("repo_git_sha"), "drivers": header.get("drivers", []),
                         "gnbs": len(hello.get("gnbs", [])), "ues": hello.get("n_ues"), "janelas": len(windows)}
    t0, t1 = _iso(man.get("started_at_utc")), _iso(man.get("finished_at_utc"))
    r["duracao_s"] = round((t1 - t0).total_seconds()) if t0 and t1 else None

    # ---------------- rede: registro de UEs, handovers, ping-pong, estado das células
    serving: Dict[int, List[tuple]] = defaultdict(list)
    connected_max, sleeping_windows, tx_changes = 0, 0, 0
    last_tx: Dict[int, float] = {}
    for w in windows:
        k = w.get("kpm") or {}
        ues = k.get("ues", [])
        connected_max = max(connected_max, sum(1 for u in ues if u.get("connected")))
        for u in ues:
            if u.get("connected"):
                hist = serving[u["ue"]]
                if not hist or hist[-1][1] != u["cell_id"]:
                    hist.append((float(w["t"]), u["cell_id"]))
        for c in k.get("cells", []):
            sleeping_windows += 1 if c.get("sleeping") else 0
            tx = c.get("tx_power_dbm")
            if tx is not None:
                if c["gnb"] in last_tx and last_tx[c["gnb"]] != tx:
                    tx_changes += 1
                last_tx[c["gnb"]] = tx
    handovers = sum(len(h) - 1 for h in serving.values())
    pingpong = sum(1 for h in serving.values() for a, b, c in zip(h, h[1:], h[2:]) if a[1] == c[1] and c[0] - a[0] <= horizon_s)
    r.update(ues_registrados=connected_max, handovers_observados=handovers, ping_pong=pingpong,
             janelas_celula_dormindo=sleeping_windows, mudancas_potencia=tx_changes)

    # ---------------- mensagens, propostas, decisões, conflitos
    props_by = Counter()
    a1 = Counter()
    rules, strategies, conflict_types = Counter(), Counter(), Counter()
    same_window, timeline = 0, defaultdict(list)
    pairs = Counter()
    selected = proposals = 0
    kg_q = kg_w = None
    for w in windows:
        ev = w.get("a1")
        if ev:
            for type_id in (ev.get("policies") or {}):
                a1[str(type_id)] += 1
        ps = w.get("proposals") or []
        proposals += len(ps)
        groups = defaultdict(set)
        for p in ps:
            props_by[(p["xapp_id"], p["parameter"])] += 1
            key = (p["gnb"], RESOURCE.get(p["parameter"], p["parameter"]))
            groups[key].add(p["xapp_id"])
            timeline[key].append((float(p["t"]), p["xapp_id"]))
        if any(len(x) > 1 for x in groups.values()):
            same_window += 1
        d = w.get("decision") or {}
        selected += len(d.get("selected") or [])
        if ps:
            rules[d.get("rule", "?")] += 1
        for res in d.get("resolutions") or []:
            strategies[res.get("strategy", "?")] += 1
            conflict_types[res.get("conflict_type", "?")] += 1
        if "kg_queries" in d:
            kg_q = (kg_q or 0) + int(d["kg_queries"])
            kg_w = (kg_w or 0) + int(d.get("kg_writes", 0))
    sequential = 0
    for key, ev in timeline.items():
        ev.sort()
        for i, (t, x) in enumerate(ev):
            for x2 in {x2 for t2, x2 in ev[i + 1:] if t2 - t <= horizon_s and x2 != x}:
                sequential += 1
                pairs[f"{' × '.join(sorted((x, x2)))} [{key[1]}]"] += 1
    r.update(indicacoes_kpm=len(windows) * max(1, r["gnbs"]), propostas_rmr_30000=proposals,
             propostas_por_xapp={f"{x}/{p}": n for (x, p), n in sorted(props_by.items())},
             recusas_devolvidas=proposals - selected, politicas_a1=dict(sorted(a1.items())),
             conflitos_mesma_janela=same_window, conflitos_em_sequencia=sequential, pares_em_conflito=dict(pairs.most_common()),
             regras_de_decisao=dict(rules), resolucoes_por_estrategia=dict(strategies), tipos_de_conflito=dict(conflict_types),
             consultas_grafo=kg_q if kg_q is not None else NR, escritas_grafo=kg_w if kg_w is not None else NR)

    # ---------------- controle da RAN (log de atuação do ns-3)
    status, by_param, per_gnb, applied = Counter(), Counter(), defaultdict(Counter), defaultdict(list)
    act = run / "raw" / "rdl_actuation_log.csv"
    if act.exists():
        with open(act, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                status[row["status"]] += 1
                by_param[f"{row['parameter']}:{row['status']}"] += 1
                per_gnb[f"gnb_{row['gnb']}"][row["parameter"]] += 1
                if row["status"] == "APPLIED" and row["parameter"] in ("TX_POWER", "PRB_QUOTA"):
                    applied[(row["gnb"], row["parameter"])].append(float(row["value"]))
    r.update(acoes_ran_por_status=dict(status), acoes_ran_por_parametro=dict(sorted(by_param.items())),
             ajustes_por_gnb={g: dict(c) for g, c in sorted(per_gnb.items())},
             oscilacoes=sum(_reversals(v) for v in applied.values()))

    # ---------------- cadeia E2 (docs/16 §10.1)
    chain = run / "raw" / "e2_chain.jsonl"
    if chain.exists():
        roles = Counter(json.loads(line)["role"] for line in chain.read_text(encoding="utf-8").splitlines() if line.strip())
        r["cadeia_e2"] = {k: roles.get(k, 0) for k in ("e2_setup", "subscription", "kpm_t0", "decision", "control_request",
                                                      "control_ack", "control_failure", "control_timeout", "kpm_t1")}
        from scripts.closed_loop.verificar_cadeia import verify
        r["cadeia_veredito"] = verify(run)["verdict"]
    else:
        r["cadeia_e2"], r["cadeia_veredito"] = NR, NR

    # ---------------- xApps originais em processo
    ts = run / "logs" / "xapp_traffic_steering.log"
    if ts.exists():
        txt = ts.read_text(errors="replace")
        r["ts_original"] = {"anomalias_AD_30003": txt.count("AD Callback got a message"),
                            "predicoes_QP_30002": txt.count("Prediction Callback got a message"),
                            "handoff_REST": txt.count("HandOff request is"),
                            "mantidos_na_servidora": txt.count("is the best one"),
                            "a1_20008": txt.count("Setting Threshold for A1-P")}

    # ---------------- KPIs
    thp_t, delays = defaultdict(float), []
    kpi = run / "raw" / "rdl_kpi_timeseries.csv"
    if kpi.exists():
        with open(kpi, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if float(row["t_end_s"]) < 1.0:
                    continue
                thp_t[row["t_end_s"]] += float(row["throughput_mbps"] or 0.0)
                if row["mean_delay_ms"] not in ("", "nan"):
                    delays.append(float(row["mean_delay_ms"]))
    r["vazao_media_mbps"] = round(statistics.fmean(thp_t.values()), 3) if thp_t else None
    r["atraso_medio_ms"] = round(statistics.fmean(delays), 3) if delays else None
    return r


def _sum(rows: List[Dict[str, Any]], key: str) -> Any:
    vals = [x[key] for x in rows if isinstance(x.get(key), (int, float))]
    return sum(vals) if vals else NR


def _merge(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    out = Counter()
    for x in rows:
        if isinstance(x.get(key), dict):
            for k, v in x[key].items():
                if isinstance(v, (int, float)):
                    out[k] += v
    return dict(sorted(out.items()))


def render(rows: List[Dict[str, Any]], title: str) -> str:
    L: List[str] = [f"# {title}", ""]
    ok = sum(1 for x in rows if x["status"] == "SUCCESS")
    dur = _sum(rows, "duracao_s")
    L += [f"- **Execuções:** {len(rows)} ({ok} com SUCCESS); cenários {sorted({x['cenario'] for x in rows})}; "
          f"baselines {sorted({x['baseline'] for x in rows})}; sementes {sorted({x['semente'] for x in rows})}",
          f"- **Commits:** {sorted({str(x['commit']) for x in rows})}; tempo total de execução: "
          f"{dur if dur == NR else f'{dur / 60:.0f} min'}", ""]
    L += ["## Rede (gNBs, UEs e interações)", "",
          f"- UEs registrados (máximo conectado por execução, somado): {_sum(rows, 'ues_registrados')}; gNBs: {_sum(rows, 'gnbs')}",
          f"- Handovers observados no KPM: {_sum(rows, 'handovers_observados')}; ping-pong (volta à célula em ≤ 5 s): {_sum(rows, 'ping_pong')}",
          f"- Janelas com célula dormindo: {_sum(rows, 'janelas_celula_dormindo')}; mudanças de potência: {_sum(rows, 'mudancas_potencia')}", ""]
    L += ["## Mensagens (RAN, Near-RT RIC e Non-RT RIC)", "",
          f"- Indications KPM (janela × gNB): {_sum(rows, 'indicacoes_kpm')}",
          f"- Propostas das xApps (RMR 30000): {_sum(rows, 'propostas_rmr_30000')}; recusas devolvidas às xApps: {_sum(rows, 'recusas_devolvidas')}",
          "- Políticas A1 (Non-RT RIC → A1 → destino): " + (", ".join(
              f"{t} → {A1_TARGET.get(t, '?')}: {n}" for t, n in _merge(rows, "politicas_a1").items()) or "nenhuma"), ""]
    chains = [x["cadeia_e2"] for x in rows if isinstance(x.get("cadeia_e2"), dict)]
    if chains:
        tot = Counter()
        for c in chains:
            tot.update(c)
        L += ["## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)", "",
              "| " + " | ".join(tot) + " |", "|" + "---|" * len(tot), "| " + " | ".join(str(v) for v in tot.values()) + " |", "",
              f"- Veredito da cadeia: {dict(Counter(x['cadeia_veredito'] for x in rows))}", ""]
    else:
        L += ["## Cadeia E2", "", f"- {NR} (execuções anteriores ao ciclo do docs/16 §10.1)", ""]
    L += ["## Conflitos e oscilações", "",
          f"- Janelas com conflito (mesmo gNB e recurso): {_sum(rows, 'conflitos_mesma_janela')}; em sequência (≤ 5 s): {_sum(rows, 'conflitos_em_sequencia')}",
          f"- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): {_sum(rows, 'oscilacoes')}",
          "- Pares e recursos: " + ("; ".join(f"{k}: {v}" for k, v in _merge(rows, "pares_em_conflito").items()) or "nenhum"),
          "- Resoluções da RDL por estratégia: " + (", ".join(f"{k}: {v}" for k, v in _merge(rows, "resolucoes_por_estrategia").items()) or "nenhuma"),
          "- Tipos de conflito: " + (", ".join(f"{k}: {v}" for k, v in _merge(rows, "tipos_de_conflito").items()) or "nenhum"), ""]
    L += ["## Controle da RAN", "",
          "- Ações por status: " + (", ".join(f"{k}: {v}" for k, v in _merge(rows, "acoes_ran_por_status").items()) or "nenhuma"),
          "- Ações por parâmetro: " + (", ".join(f"{k}: {v}" for k, v in _merge(rows, "acoes_ran_por_parametro").items()) or "nenhuma"), ""]
    L += ["## Regras, políticas e grafo de conhecimento", "",
          "- Janelas decididas por regra: " + (", ".join(f"{k}: {v}" for k, v in _merge(rows, "regras_de_decisao").items()) or "nenhuma"),
          f"- Consultas ao grafo de conhecimento: {_sum(rows, 'consultas_grafo')}; escritas: {_sum(rows, 'escritas_grafo')}", ""]
    ts = [x for x in rows if x.get("ts_original")]
    if ts:
        L += ["## Traffic Steering original (ric-app-ts)", "",
              "- " + ", ".join(f"{k}: {v}" for k, v in _merge(ts, "ts_original").items()), ""]
    L += ["## Por execução", "",
          "| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in rows:
        L.append(f"| {x['cenario']} | {x['baseline']} | {x['semente']} | {x['status']} | {x['propostas_rmr_30000']} | "
                 f"{x['conflitos_mesma_janela']}/{x['conflitos_em_sequencia']} | {x['oscilacoes']} | "
                 f"{x['acoes_ran_por_status'].get('APPLIED', 0)} | {x['handovers_observados']} | {x['vazao_media_mbps']} | {x['atraso_medio_ms']} |")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="cl_piloto_")
    ap.add_argument("--seed", default=None)
    ap.add_argument("--runs", nargs="*", default=None, help="diretórios de execução (no lugar de --prefix/--seed)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--title", default=None)
    a = ap.parse_args()
    if a.runs:
        runs = [Path(p) for p in a.runs]
    else:
        pattern = f"{a.prefix}*" + (f"_seed{a.seed}" if a.seed else "")
        runs = sorted((ROOT / "experiments" / "runs").glob(pattern))
    rows = [analyze(r) for r in runs if (r / "raw" / "closed_loop_log.jsonl").exists()]
    if not rows:
        print("nenhuma execução de malha fechada encontrada")
        return 1
    title = a.title or f"Painel da campanha {a.prefix}{'*' if not a.seed else ''}" + (f" (semente {a.seed})" if a.seed else "")
    text = render(rows, title)
    print(text)
    out = Path(a.out) if a.out else ROOT / "reports" / "avaliacao" / f"painel_{a.prefix.strip('_')}_{a.seed or 'todas'}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "painel.md").write_text(text, encoding="utf-8")
    (out / "painel.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[painel] {out / 'painel.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
