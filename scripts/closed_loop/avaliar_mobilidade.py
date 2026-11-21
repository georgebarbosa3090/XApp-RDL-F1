"""Medidas de mobilidade numa execução do S5 em malha fechada (proposta P3, docs/16 §10.15).

Complementa ``avaliar_pingpong.py`` (voltas em até 5 s, ações justificadas, perdas depois de handover) com o
que muda quando parte dos UEs anda entre as células (``--ueSpeed`` no ``scenario_rdl_temporal_pingpong.cc``):

- UEs que andam: os ``round(ueMovingFraction × n_ues)`` de menor índice, lidos do comando no manifesto;
- perdas de conexão: episódios (janela com ``connected: true`` seguida de ``connected: false``) por grupo
  e fração de UE-janelas sem conexão;
- trocas de célula: ``troca_conectada`` quando o UE aparece noutra célula sem janela desconectada no meio
  (handover executado) e ``reconexao_outra_celula`` quando volta noutra célula depois de perder a conexão
  (falha de enlace, RLF, e nova seleção de célula; no 5G-LENA não há handover automático);
- handovers aplicados por xApp e UE-janelas mal atendidas (vazão abaixo de 50 % da taxa oferecida).

Uso: python scripts/closed_loop/avaliar_mobilidade.py experiments/runs/<run_id> [...]
"""
import argparse
import csv
import json
import re
from pathlib import Path


def opcao(cmd: str, nome: str, padrao: float) -> float:
    """Último valor de --nome=valor no comando ns-3 (o CommandLine do ns-3 fica com o último)."""
    achados = re.findall(rf"--{nome}=([-+0-9.eE]+)", cmd)
    return float(achados[-1]) if achados else padrao


def avaliar(run: Path) -> dict:
    manifest = json.loads((run / "execution_manifest.json").read_text(encoding="utf-8"))
    cmd = manifest.get("command", "")
    linhas = [json.loads(l) for l in (run / "raw" / "closed_loop_log.jsonl").open(encoding="utf-8")]
    head = next(j for j in linhas if j.get("type") == "header")
    win = [j for j in linhas if j.get("type") == "window"]
    acts = list(csv.DictReader((run / "raw" / "rdl_actuation_log.csv").open(encoding="utf-8")))
    hello = head.get("hello", {})
    n_ues = int(hello.get("n_ues", 0))
    oferta = {int(k): float(v) for k, v in (hello.get("ue_offered_mbps") or {}).items()}
    velocidade = opcao(cmd, "ueSpeed", 0.0)
    fracao = opcao(cmd, "ueMovingFraction", 0.5)
    n_andam = int(round(fracao * n_ues)) if velocidade > 0 else 0
    andam = set(range(n_andam))

    hos = [a for a in acts if a["parameter"] == "HANDOVER" and a["status"] == "APPLIED"]
    por_xapp = {}
    for a in hos:
        por_xapp[a["xapp_id"]] = por_xapp.get(a["xapp_id"], 0) + 1

    campos = ("ue_janelas", "sem_conexao", "perdas", "troca_conectada", "reconexao_outra_celula",
              "reconexao_mesma_celula", "mal_atendidas")
    grupos = {nome: dict.fromkeys(campos, 0) | {"vazao_soma": 0.0} for nome in ("andam", "fixos")}
    estado = {}   # ue -> (conectado na janela anterior, célula da última janela conectada)
    for w in win:
        for u in w["kpm"]["ues"]:
            ue = int(u["ue"])
            g = grupos["andam" if ue in andam else "fixos"]
            con = u.get("connected") is True
            thp = u.get("thp_mbps") or 0.0
            g["ue_janelas"] += 1
            g["vazao_soma"] += thp
            g["sem_conexao"] += not con
            if ue in oferta and thp < 0.5 * oferta[ue]:
                g["mal_atendidas"] += 1
            ant = estado.get(ue)
            if ant is not None:
                con_ant, cel_ant = ant
                if con_ant and not con:
                    g["perdas"] += 1
                if con and cel_ant is not None:
                    if con_ant and u["cell_id"] != cel_ant:
                        g["troca_conectada"] += 1
                    elif not con_ant:
                        g["reconexao_outra_celula" if u["cell_id"] != cel_ant else "reconexao_mesma_celula"] += 1
            cel = u["cell_id"] if con else (ant[1] if ant else None)
            estado[ue] = (con, cel)
    saida = {"run": run.name, "run_status": manifest.get("run_status"), "ue_speed_mps": velocidade,
             "ues_andam": n_andam, "n_ues": n_ues, "handovers": len(hos),
             "handovers_por_xapp": dict(sorted(por_xapp.items()))}
    for nome, g in grupos.items():
        n = g["ue_janelas"] or 1
        saida[nome] = {k: g[k] for k in ("perdas", "troca_conectada", "reconexao_outra_celula",
                                         "reconexao_mesma_celula")}
        saida[nome] |= {"sem_conexao_%": round(100 * g["sem_conexao"] / n, 1),
                        "mal_atendidas_%": round(100 * g["mal_atendidas"] / n, 1),
                        "vazao_media_ue_mbps": round(g["vazao_soma"] / n, 3)}
    return saida


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    a = ap.parse_args()
    for r in a.runs:
        print(json.dumps(avaliar(Path(r)), ensure_ascii=False))


if __name__ == "__main__":
    main()
