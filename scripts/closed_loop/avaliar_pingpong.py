"""Critério de conflito legítimo de ping-pong numa execução em malha fechada (docs/16 §10.14).

Para cada handover aplicado (``raw/rdl_actuation_log.csv``), confere no KPM da janela da decisão
(``raw/closed_loop_log.jsonl``) se a ação era justificada quando foi pedida:

- Load Balancer: carga (uso de PRB) da célula de origem menos a do destino ≥ ``--lb-gap`` pontos (padrão 30);
- Traffic Steering: UE mal atendido (vazão média em 1 s abaixo de 50 % da taxa oferecida) e RSRP do destino
  maior que o da servidora.

Conta também as voltas (o mesmo UE volta à célula de origem por handover pedido em até 5 s) e as perdas de
conexão (``connected: false``) em até ``--rlf-s`` segundos depois de um handover pedido.

Uso: python scripts/closed_loop/avaliar_pingpong.py experiments/runs/<run_id> [...]
"""
import argparse
import csv
import json
from pathlib import Path


def carregar(run: Path):
    linhas = [json.loads(l) for l in (run / "raw" / "closed_loop_log.jsonl").open(encoding="utf-8")]
    head = next(j for j in linhas if j.get("type") == "header")
    win = [j for j in linhas if j.get("type") == "window"]
    acts = list(csv.DictReader((run / "raw" / "rdl_actuation_log.csv").open(encoding="utf-8")))
    return head, win, acts


def janela_ate(win, t):
    """Última janela de KPM com t ≤ instante da ação (o que a xApp via ao propor)."""
    ant = None
    for j in win:
        if j["t"] > t + 1e-9:
            break
        ant = j
    return ant


def avaliar(run: Path, lb_gap: float, rlf_s: float) -> dict:
    head, win, acts = carregar(run)
    oferta = {int(k): float(v) for k, v in (head.get("hello", {}).get("ue_offered_mbps") or {}).items()}
    hos = [a for a in acts if a["parameter"] == "HANDOVER" and a["status"] == "APPLIED"]
    res = {"run": run.name, "handovers": len(hos), "lb": 0, "lb_ok": 0, "ts": 0, "ts_ok": 0,
           "voltas_5s": 0, "voltas_justificadas": 0, "perdas_conexao": 0}
    util_med = {}
    for j in win:
        for c in j["kpm"]["cells"]:
            util_med.setdefault(c["cell_id"], []).append(c.get("prb_util") or 0.0)
    res["uso_prb_medio_%"] = {c: round(100 * sum(v) / len(v), 1) for c, v in sorted(util_med.items())}
    feitos = []   # (t, ue, origem, destino, justificado)
    for a in hos:
        t, ue, xid = float(a["time_s"]), int(a["ue"]), a["xapp_id"]
        orig, dest = int(a["gnb"]) + 1, int(float(a["value"])) + 1     # cell_id = índice da gNB + 1
        j = janela_ate(win, t)
        if j is None:
            continue
        cel = {c["cell_id"]: c for c in j["kpm"]["cells"]}
        ok = False
        if xid == "load_balancer":
            res["lb"] += 1
            u0, u1 = cel.get(orig, {}).get("prb_util"), cel.get(dest, {}).get("prb_util")
            ok = u0 is not None and u1 is not None and 100 * (u0 - u1) >= lb_gap
            res["lb_ok"] += ok
        elif xid == "traffic_steering":
            res["ts"] += 1
            ant = [w for w in win if t - 1.0 < w["t"] <= t + 1e-9]
            thp = [u["thp_mbps"] or 0.0 for w in ant for u in w["kpm"]["ues"] if u["ue"] == ue]
            uk = next((u for u in j["kpm"]["ues"] if u["ue"] == ue), None)
            mal = bool(thp) and ue in oferta and sum(thp) / len(thp) < 0.5 * oferta[ue]
            rs = (uk or {}).get("rsrp_dbm") or {}
            melhor = str(dest) in rs and str(orig) in rs and rs[str(dest)] > rs[str(orig)]
            ok = mal and melhor
            res["ts_ok"] += ok
        for (t0, ue0, o0, d0, ok0) in feitos:
            if ue0 == ue and o0 == dest and d0 == orig and 0 < t - t0 <= 5.0:
                res["voltas_5s"] += 1
                res["voltas_justificadas"] += ok0 and ok
                break
        feitos.append((t, ue, orig, dest, ok))
    for (t0, ue0, _, _, _) in feitos:
        for w in win:
            if t0 < w["t"] <= t0 + rlf_s and any(u["ue"] == ue0 and u.get("connected") is False
                                                 for u in w["kpm"]["ues"]):
                res["perdas_conexao"] += 1
                break
    res["criterio"] = (res["voltas_justificadas"] > 0 and res["perdas_conexao"] == 0)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--lb-gap", type=float, default=30.0)
    ap.add_argument("--rlf-s", type=float, default=3.0)
    a = ap.parse_args()
    for r in a.runs:
        print(json.dumps(avaliar(Path(r), a.lb_gap, a.rlf_s), ensure_ascii=False))


if __name__ == "__main__":
    main()
