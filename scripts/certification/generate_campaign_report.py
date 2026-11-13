#!/usr/bin/env python3
"""
Relatório técnico da campanha de conflitos (ns-3.48 + 5G-LENA v5.1), gerado só a partir da evidência.

Lê a análise (reports/conflicts/conflict_analysis_*.json), os manifestos de cada execução
(experiments/runs/nr_*/execution_manifest.json), o catálogo de cenários e o certificado mais
recente, e escreve reports/conflicts/relatorio_campanha_<UTC>.md com:
  hipóteses e critérios, comandos de execução (bash), ambiente e proveniência, resultados
  agregados, uma tabela por semente com todas as métricas, diferenças pareadas B3 − Bx,
  cronogramas idênticos entre baselines, avaliação das hipóteses, conclusões, ameaças à
  validade, falhas preservadas e o comando ns-3 exato de cada execução.

Nenhum número é digitado à mão: tudo vem dos arquivos lidos.

Uso:
  python scripts/certification/generate_campaign_report.py
  python scripts/certification/generate_campaign_report.py --analysis reports/conflicts/conflict_analysis_20261108T103510Z.json
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


sys.path.insert(0, str(Path(__file__).resolve().parent))
from redact_local_paths import redact_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT / "experiments" / "runs"
FAILED_DIR = ROOT / "experiments" / "runs_failed"
CATALOG = ROOT / "simulations" / "ns3" / "conflicts" / "catalog.json"

T_975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262,
         10: 2.228, 14: 2.145, 19: 2.093, 29: 2.045}

METRICS = [
    ("thp_pre", "Vazão antes (Mbps)"),
    ("thp_conflict", "Vazão no conflito (Mbps)"),
    ("thp_post", "Vazão depois (Mbps)"),
    ("delay_conflict_ms", "Atraso no conflito (ms)"),
    ("actions_applied", "Ações aplicadas"),
    ("handovers", "Handovers"),
    ("unsafe_applied", "Ações inseguras"),
    ("oscillations", "Oscilações"),
]
LABEL = dict(METRICS)
COUNT_METRICS = {"actions_applied", "handovers", "unsafe_applied", "oscillations"}

# ---------------------------------------------------------------------------------------------
# Hipóteses. Derivadas do tratamento esperado de cada tipo de conflito na taxonomia
# (docs/03_cenarios_e_conflitos.md, coluna "Tratamento na RDL-N1"), escrita antes
# desta campanha. Não foram pré-registradas formalmente.
#
# Cada critério é um de:
#   ("paired", métrica, A, B, sentido)  diferença pareada por semente A − B; sentido "<0", ">0" ou "=0"
#   ("all", métrica, baseline, op, valor)  vale em todas as sementes (op: "==", ">", "<")
# ---------------------------------------------------------------------------------------------
HYPOTHESES = [
    {"id": "H0", "scenario": "S0", "type": "controle (sem conflito)",
     "text": "Sem conflito, a RDL-N1 é transparente: B3 não difere do B0 em vazão nem em atraso.",
     "checks": [("paired", "thp_conflict", "B3", "B0", "=0"), ("paired", "delay_conflict_ms", "B3", "B0", "=0")]},
    {"id": "H1", "scenario": "S1", "type": "direto (PRB)",
     "text": "Em conflito direto de PRB, a RDL-N1 elimina as oscilações e melhora vazão e atraso em relação ao B0.",
     "checks": [("all", "oscillations", "B3", "==", 0), ("paired", "thp_conflict", "B3", "B0", ">0"),
                ("paired", "delay_conflict_ms", "B3", "B0", "<0")]},
    {"id": "H2", "scenario": "S2", "type": "indireto (TVS)",
     "text": "Em conflito indireto, a RDL-N1 escolhe um subconjunto de ações que não piora vazão nem atraso em relação a B0, B1 e B2.",
     "checks": [("paired", "thp_conflict", "B3", "B0", ">=0"), ("paired", "delay_conflict_ms", "B3", "B0", "<=0"),
                ("paired", "thp_conflict", "B3", "B1", ">=0"), ("paired", "delay_conflict_ms", "B3", "B1", "<=0")]},
    {"id": "H3", "scenario": "S3", "type": "direto (potência)",
     "text": "Em conflito direto de potência, a RDL-N1 elimina as oscilações sem perda de vazão em relação ao B0.",
     "checks": [("all", "oscillations", "B3", "==", 0), ("paired", "thp_conflict", "B3", "B0", ">=0")]},
    {"id": "H4", "scenario": "S4", "type": "entre células (limitação esperada)",
     "text": "A RDL-N1 não detecta o conflito entre células: o handover acontece e B3 não difere do B1 em vazão nem em atraso.",
     "checks": [("all", "handovers", "B3", ">", 0), ("paired", "thp_conflict", "B3", "B1", "=0"),
                ("paired", "delay_conflict_ms", "B3", "B1", "=0")]},
    {"id": "H5", "scenario": "S5", "type": "temporal entre células (limitação esperada)",
     "text": "A RDL-N1 não detecta o ping-pong entre células: B3 aplica os mesmos handovers que o B0.",
     "checks": [("paired", "handovers", "B3", "B0", "=0"), ("paired", "thp_conflict", "B3", "B0", "=0")]},
    {"id": "H6", "scenario": "S6", "type": "tempestade",
     "text": "Sob tempestade de conflitos, a RDL-N1 aplica menos ações, elimina as oscilações e reduz o atraso em relação a B0, B1 e B2.",
     "checks": [("paired", "actions_applied", "B3", "B1", "<0"), ("all", "oscillations", "B3", "==", 0),
                ("paired", "delay_conflict_ms", "B3", "B0", "<0"), ("paired", "delay_conflict_ms", "B3", "B1", "<0"),
                ("paired", "delay_conflict_ms", "B3", "B2", "<0")]},
    {"id": "H7", "scenario": "S7", "type": "ação insegura",
     "text": "O Safety Guard impede que ações inseguras cheguem à RAN no B3, enquanto B0, B1 e B2 as aplicam.",
     "checks": [("all", "unsafe_applied", "B3", "==", 0), ("all", "unsafe_applied", "B0", ">", 0),
                ("all", "unsafe_applied", "B1", ">", 0), ("all", "unsafe_applied", "B2", ">", 0)]},
]

PASS, FAIL, INCONCLUSIVE = "ATENDIDO", "NÃO ATENDIDO", "INCONCLUSIVO"
SUPPORTED, REFUTED, OPEN = "SUPORTADA", "REFUTADA", "INCONCLUSIVA"


# ---------------------------------------------------------------------------------------------
# Estatística
# ---------------------------------------------------------------------------------------------

def t_quantile(df: int) -> float:
    if df in T_975:
        return T_975[df]
    return T_975[max(k for k in T_975 if k <= df)] if df < 30 else 1.96


def mean_ci(values: List[float]) -> Tuple[float, Optional[float]]:
    mean = statistics.fmean(values)
    if len(values) < 2:
        return mean, None
    return mean, t_quantile(len(values) - 1) * statistics.stdev(values) / math.sqrt(len(values))


def paired_diffs(runs: Dict[Tuple[str, str, int], Dict[str, Any]], scenario: str, metric: str,
                 a: str, b: str) -> List[float]:
    seeds = sorted({s for (sc, bl, s) in runs if sc == scenario and bl == a} &
                   {s for (sc, bl, s) in runs if sc == scenario and bl == b})
    return [runs[(scenario, a, s)][metric] - runs[(scenario, b, s)][metric] for s in seeds
            if runs[(scenario, a, s)][metric] is not None and runs[(scenario, b, s)][metric] is not None]


def evaluate_check_in(scenario: str, check: tuple, runs) -> Tuple[str, str]:
    """Retorna (resultado, evidência textual) de um critério no cenário dado."""
    kind, metric = check[0], check[1]
    if kind == "all":
        _, _, baseline, op, value = check
        vals = [r[metric] for (sc, bl, _), r in sorted(runs.items()) if sc == scenario and bl == baseline]
        if not vals:
            return INCONCLUSIVE, f"sem execuções de {scenario} {baseline}"
        ok = all({"==": v == value, ">": v > value, "<": v < value}[op] for v in vals)
        shown = ", ".join(fmt(v, 0 if metric in COUNT_METRICS else 2) for v in vals)
        return (PASS if ok else FAIL), f"{LABEL[metric]} de {baseline} {op} {value} em todas as sementes: [{shown}]"
    _, _, a, b, sense = check
    diffs = paired_diffs(runs, scenario, metric, a, b)
    if len(diffs) < 2:
        return INCONCLUSIVE, f"menos de 2 pares {a}/{b}"
    mean, ci = mean_ci(diffs)
    lo, hi = mean - ci, mean + ci
    evidence = f"{LABEL[metric]} {a} − {b} = {fmt(mean)} (IC 95 % [{fmt(lo)}; {fmt(hi)}], n = {len(diffs)})"
    if all(d == 0 for d in diffs):
        evidence += "; diferença zero em todas as sementes"
    if sense == "=0":
        return (PASS if lo <= 0 <= hi else FAIL), evidence
    if sense in ("<0", ">0"):
        favorable = hi < 0 if sense == "<0" else lo > 0
        opposite = lo > 0 if sense == "<0" else hi < 0
        return (PASS if favorable else FAIL if opposite else INCONCLUSIVE), evidence
    # ">=0" / "<=0" (não piora): falha se o IC inteiro está do lado desfavorável; com o IC contendo
    # zero, só é atendido se a média não estiver do lado desfavorável (não piora não demonstrada).
    worse = hi < 0 if sense == ">=0" else lo > 0
    if worse:
        return FAIL, evidence
    mean_unfavorable = mean < 0 if sense == ">=0" else mean > 0
    return (INCONCLUSIVE if mean_unfavorable else PASS), evidence


def hypothesis_verdict(results: List[str]) -> str:
    if all(r == PASS for r in results):
        return SUPPORTED
    if any(r == FAIL for r in results):
        return REFUTED
    return OPEN


# ---------------------------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------------------------

def fmt(x: Optional[float], digits: int = 2) -> str:
    if x is None:
        return "—"
    if x == 0:
        x = 0.0  # evita "-0,00"
    elif digits > 0 and abs(x) < 0.5 * 10 ** -digits:
        # não nulo mas pequeno demais para `digits` casas: mostra a ordem de grandeza
        s = f"{x:.4f}"
        return (s if float(s) != 0 else f"{x:.1e}").replace(".", ",")
    return f"{x:.{digits}f}".replace(".", ",")


def fmt_metric(metric: str, value: Optional[float]) -> str:
    return fmt(value, 0 if metric in COUNT_METRICS and value is not None and float(value).is_integer() else 2)


def table(header: List[str], rows: List[List[str]], align: Optional[List[str]] = None) -> List[str]:
    align = align or [":--"] * len(header)
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(align) + " |"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out


# ---------------------------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------------------------

def latest(pattern: str, directory: Path) -> Optional[Path]:
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def load_manifests(run_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    out = {}
    for rid in run_ids:
        path = RUNS_DIR / rid / "execution_manifest.json"
        if path.exists():
            out[rid] = json.loads(path.read_text(encoding="utf-8"))
    return out


def failed_runs() -> List[Tuple[str, str, str]]:
    rows = []
    if not FAILED_DIR.exists():
        return rows
    for d in sorted(FAILED_DIR.iterdir()):
        manifest = d / "execution_manifest.json"
        status = json.loads(manifest.read_text(encoding="utf-8")).get("run_status") if manifest.exists() else "?"
        reason = ""
        stderr = d / "logs" / "stderr.log"
        err_text = stderr.read_text(encoding="utf-8", errors="replace") if stderr.exists() else ""
        for line in err_text.splitlines():
            if "msg=" in line:
                reason = "simulador: " + line.split("msg=", 1)[1].split('",')[0].strip('"')
                break
        if not reason:
            exit_code = json.loads(manifest.read_text(encoding="utf-8")).get("exit_code") if manifest.exists() else None
            stdout = d / "logs" / "stdout.log"
            last = ""
            if stdout.exists():
                lines = [l for l in stdout.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
                last = lines[-1].strip() if lines else ""
            reason = (f"exit_code {exit_code}; stderr {'vazio' if not err_text.strip() else 'sem mensagem do simulador'}"
                      + (f"; última saída: `{last}` (execução interrompida)" if last else ""))
        rows.append((d.name, status, reason))
    return rows


# ---------------------------------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------------------------------

def build_report(analysis: Dict[str, Any], analysis_path: Path, catalog: Dict[str, Any],
                 manifests: Dict[str, Dict[str, Any]], certificate: Optional[Dict[str, Any]],
                 certificate_path: Optional[Path], failures: List[Tuple[str, str, str]]) -> str:
    runs = {(r["scenario"], r["baseline"], r["seed"]): r for r in analysis["runs"]}
    scenarios = sorted({k[0] for k in runs}, key=lambda s: int(s[1:]))
    baselines = sorted({k[1] for k in runs})
    seeds = sorted({k[2] for k in runs})
    statuses = defaultdict(int)
    for r in analysis["runs"]:
        statuses[r.get("run_status")] += 1
    rel = lambda p: p.relative_to(ROOT).as_posix()  # noqa: E731

    L: List[str] = []
    L.append("# Relatório da campanha de conflitos multi-xApp (ns-3.48 + 5G-LENA v5.1)")
    L.append("")
    L.append(f"Gerado em {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} por "
             f"[`generate_campaign_report.py`](../../scripts/certification/generate_campaign_report.py) a partir de "
             f"[`{analysis_path.name}`]({analysis_path.name}) (análise gerada em {analysis['generated_at_utc']}), "
             f"dos manifestos das execuções e do catálogo de cenários. Nenhum valor foi digitado à mão.")
    L.append("")

    # 1. Resumo
    L.append("## 1. Resumo")
    L.append("")
    L.append(f"- **Desenho:** {len(scenarios)} cenários ({scenarios[0]}–{scenarios[-1]}) × {len(baselines)} baselines "
             f"({', '.join(baselines)}) × {len(seeds)} sementes ({seeds[0]}–{seeds[-1]}) = {len(runs)} execuções.")
    L.append("- **Status:** " + ", ".join(f"{n} `{s}`" for s, n in sorted(statuses.items(), key=lambda x: str(x[0]))) +
             f"; {len(analysis.get('skipped', []))} execução(ões) ignorada(s) pela análise.")
    L.append("- **Avaliação em malha aberta:** as propostas das xApps vêm do catálogo, cada baseline decide e as ações "
             "decididas são aplicadas na RAN simulada. Não há E2 nem realimentação de KPM.")
    verdicts = {}
    for h in HYPOTHESES:
        if h["scenario"] in scenarios:
            verdicts[h["id"]] = hypothesis_verdict([evaluate_check_in(h["scenario"], c, runs)[0] for c in h["checks"]])
    count = defaultdict(list)
    for hid, v in verdicts.items():
        count[v].append(hid)
    L.append("- **Hipóteses:** " + "; ".join(f"{v.lower()}: {', '.join(ids)}" for v, ids in
                                             sorted(count.items())) + " (seção 9).")
    if certificate:
        g = certificate.get("gates", {})
        L.append("- **Certificação:** " + ", ".join(f"{k} {v.get('verdict')}" for k, v in sorted(g.items())) +
                 (f" ([`{certificate_path.name}`](../certification/{certificate_path.name}))" if certificate_path else "") + ".")
    L.append("")

    # 2. Pergunta e hipóteses
    L.append("## 2. Pergunta e hipóteses")
    L.append("")
    L.append("**Pergunta.** Quando várias xApps propõem controles conflitantes, a decisão da RDL-N1 (B3) leva a um "
             "desempenho de rede melhor ou mais seguro que não coordenar (B0), FIFO por janela e alvo (B1) ou "
             "prioridade estática por janela e alvo (B2)?")
    L.append("")
    L.append("As hipóteses abaixo foram derivadas do tratamento esperado de cada tipo de conflito na "
             "[taxonomia](../../docs/03_cenarios_e_conflitos.md), escrita antes desta campanha. "
             "Não houve pré-registro formal. H4 e H5 descrevem limitações conhecidas: \"suportada\" significa que a "
             "limitação se confirmou.")
    L.append("")
    rows = []
    for h in HYPOTHESES:
        crit = []
        for c in h["checks"]:
            if c[0] == "paired":
                crit.append(f"{c[2]} − {c[3]} em {LABEL[c[1]]}: `{c[4]}`")
            else:
                crit.append(f"{LABEL[c[1]]} de {c[2]} {c[3]} {c[4]} em todas as sementes")
        rows.append([h["id"], h["scenario"], h["type"], h["text"], "; ".join(crit)])
    L += table(["ID", "Cenário", "Tipo de conflito", "Hipótese", "Critérios"], rows)
    L.append("")
    L.append("Regras de decisão sobre a diferença pareada por semente (A − B), com IC 95 % de t de Student:")
    L.append("")
    L.append("- `<0` / `>0`: atendido se o IC inteiro está do lado esperado; não atendido se o IC inteiro está do lado "
             "oposto; inconclusivo se o IC contém zero.")
    L.append("- `<=0` / `>=0` (não piora): não atendido se o IC inteiro está do lado desfavorável; com o IC contendo "
             "zero, atendido se a média não está do lado desfavorável e inconclusivo caso contrário.")
    L.append("- `=0`: atendido se o IC contém zero. Isso indica ausência de diferença detectável com n = "
             f"{len(seeds)}, não equivalência.")
    L.append("- Hipótese **suportada** se todos os critérios forem atendidos, **refutada** se algum não for, "
             "**inconclusiva** nos demais casos.")
    L.append("")

    # 3. Desenho e ambiente
    L.append("## 3. Desenho, cenários e ambiente")
    L.append("")
    rows = []
    for sc in scenarios:
        spec = catalog["scenarios"][sc]
        c0, c1 = spec["conflict_window_s"]
        rows.append([sc, f"`{spec['ns3']}`", f"{fmt(c0, 1)}–{fmt(c1, 1)} s", " ".join(f"`{a}`" for a in spec.get("args", [])),
                     spec.get("summary", "")])
    L += table(["Cenário", "Programa ns-3", "Janela de conflito", "Argumentos", "Conflito"], rows)
    L.append("")
    L.append(f"Janela de decisão dos baselines: {fmt(catalog.get('decision_window_s', 0.2) * 1000, 0)} ms. "
             "Janelas de medição: antes = (máx(1,5; início − 5), início]; conflito = (início, fim]; "
             "depois = (fim, simTime − 0,5] s.")
    L.append("")
    L.append("| Métrica | Definição |")
    L.append("| :-- | :-- |")
    L.append("| Vazão antes / no conflito / depois | média, por intervalo de 100 ms, da vazão somada de todas as células (Mbps) |")
    L.append("| Atraso no conflito | atraso médio fim a fim ponderado por pacote durante a janela de conflito (ms) |")
    L.append("| Ações aplicadas, handovers | linhas com status `APPLIED` em `rdl_actuation_log.csv` |")
    L.append("| Ações inseguras | `TX_POWER` fora de [−10, 43] dBm ou `PRB_QUOTA` fora de [0, 100] aplicadas na RAN |")
    L.append("| Oscilações | trocas de valor num mesmo alvo (gNB, parâmetro) entre ações aplicadas |")
    L.append("")
    env = defaultdict(set)
    for m in manifests.values():
        env["ns-3"].add(f"{m.get('ns3_version')} (`{(m.get('ns3_commit') or '?')[:7]}`)")
        env["5G-LENA"].add(f"{m.get('fiveg_lena_version')} (`{(m.get('nr_commit') or '?')[:7]}`)")
        for k, v in (m.get("environment") or {}).items():
            env[k].add(v)
        env["commit do repositório"].add(f"`{m.get('repo_git_sha')}`")
    L += table(["Componente", "Valor(es) registrados nos manifestos"], [[k, "; ".join(sorted(v))] for k, v in env.items()])
    L.append("")
    starts = sorted(m["started_at_utc"] for m in manifests.values() if m.get("started_at_utc"))
    ends = sorted(m["finished_at_utc"] for m in manifests.values() if m.get("finished_at_utc"))
    if starts and ends:
        L.append(f"Execuções entre {starts[0]} e {ends[-1]} (UTC).")
        L.append("")

    # 4. Comandos
    seed_arg = f"{seeds[0]}-{seeds[-1]}" if seeds == list(range(seeds[0], seeds[-1] + 1)) else " ".join(map(str, seeds))
    repo_wsl = "<raiz-do-repositório>"   # o relatório não guarda o caminho local do clone
    L.append("## 4. Comandos de execução (terminal WSL/Ubuntu)")
    L.append("")
    L.append("Todos os comandos abaixo rodam direto no terminal do Ubuntu (WSL), sem passar pelo Windows. "
             "O ns-3.48 + 5G-LENA v5.1 compilado fica em `~/ns3-oran-workspace/ns-3-oran` (variável `NS3_DIR`); "
             "a saída `[RDL-ACT]`/`[RDL-KPI]` de cada execução aparece ao vivo. Detalhes do ambiente no "
             "[guia operacional](../../docs/04_instalacao_e_operacao.md).")
    L.append("")
    L.append("**Preparação (uma vez).** O driver usa a `RDLxApp` real no B3 e precisa das dependências do projeto. "
             "Sem `sudo` (o Ubuntu 24.04 não traz `python3-venv`), o venv é criado sem pip e as dependências "
             "são instaladas com o pip do sistema:")
    L.append("")
    L.append("```bash")
    L.append("python3 -m venv --without-pip ~/.venvs/xapp-rdl")
    L.append("python3 -m pip --python ~/.venvs/xapp-rdl/bin/python install \"pydantic>=2.0.0\" \"structlog>=23.1.0\" "
             "\"prometheus-client>=0.19.0\" \"pycrate>=0.7.0\" \"requests>=2.31.0\" \"numpy>=1.24.0\" "
             "\"fastapi>=0.100.0\" \"uvicorn>=0.20.0\" \"PyYAML>=6.0.1\"")
    L.append("```")
    L.append("")
    L.append("**Em cada terminal novo:**")
    L.append("")
    L.append("```bash")
    L.append(f"cd {repo_wsl}")
    L.append("source ~/.venvs/xapp-rdl/bin/activate")
    L.append("```")
    L.append("")
    L.append("Campanha completa (retomável: execuções com `hashes.sha256` são puladas; interrompidas são removidas e refeitas):")
    L.append("")
    L.append("```bash")
    L.append("python scripts/certification/run_conflict_campaign.py \\")
    L.append(f"    --scenarios {' '.join(scenarios)} --baselines {' '.join(baselines)} --seeds {seed_arg} --jobs 2")
    L.append("```")
    L.append("")
    L.append("Uma semente por vez (cada semente concluída forma um conjunto pareado completo):")
    L.append("")
    L.append("```bash")
    L.append(f"for s in {' '.join(map(str, seeds))}; do")
    L.append(f"  python scripts/certification/run_conflict_campaign.py --scenarios {' '.join(scenarios)} "
             f"--baselines {' '.join(baselines)} --seeds $s --jobs 2 --skip-analysis")
    L.append("done")
    L.append("```")
    L.append("")
    L.append("Refazer execuções com falha (as originais vão para `experiments/runs_failed/<run_id>__<UTC>`):")
    L.append("")
    L.append("```bash")
    L.append("python scripts/certification/run_conflict_campaign.py \\")
    L.append(f"    --scenarios {' '.join(scenarios)} --baselines {' '.join(baselines)} --seeds {seed_arg} --jobs 2 --retry-failed")
    L.append("```")
    L.append("")
    L.append("Uma execução isolada:")
    L.append("")
    L.append("```bash")
    L.append("python scripts/certification/run_conflict_experiment.py --scenario S1 --baseline B3 --seed 1001")
    L.append("```")
    L.append("")
    L.append("Só o cronograma de ações decidido pelo baseline, sem simular:")
    L.append("")
    L.append("```bash")
    L.append("python scripts/certification/run_conflict_experiment.py --scenario S1 --baseline B3 --seed 1001 --dry-run")
    L.append("```")
    L.append("")
    L.append("Análise, certificação e este relatório (a campanha já roda os dois primeiros ao final):")
    L.append("")
    L.append("```bash")
    for cmd in ("analyze_conflict_runs.py", "certify_chain.py", "generate_campaign_report.py"):
        L.append(f"python scripts/certification/{cmd}")
    L.append("```")
    L.append("")
    L.append("Na B3, as mensagens de porta 8080/8081 em uso vêm dos servidores de saúde e métricas da `RDLxApp` "
             "e não afetam a decisão.")
    L.append("")
    L.append("Por baixo, cada execução chama o executor com proveniência "
             "[`run_ns3_certified.sh`](../../scripts/certification/run_ns3_certified.sh), que roda o comando ns-3 "
             "registrado no manifesto (lista completa no apêndice A). Exemplo:")
    L.append("")
    example = manifests.get("nr_S1_B3_seed1001") or next(iter(manifests.values()), None)
    if example:
        L.append("```bash")
        L.append(redact_text(example["command"]))
        L.append("```")
        L.append("")

    # 5. Resultados agregados
    L.append("## 5. Resultados agregados")
    L.append("")
    L.append(f"Média ± IC 95 % (t de Student) sobre as sementes; n por célula na coluna n.")
    L.append("")
    rows = []
    for a in analysis["aggregate"]:
        cells = []
        for metric, _ in METRICS:
            c = a.get(metric) or {}
            cells.append("—" if c.get("mean") is None else
                         f"{fmt(c['mean'])} ± {fmt(c['ci95'])}" if c.get("ci95") is not None else fmt(c["mean"]))
        rows.append([a["scenario"], a["baseline"], str(a["n"]), *cells])
    L += table(["Cenário", "Baseline", "n", *[l for _, l in METRICS]], rows, [":--", ":--"] + ["--:"] * (1 + len(METRICS)))
    L.append("")

    # 6. Tabelas por semente
    L.append("## 6. Resultados por semente")
    L.append("")
    L.append("Valores de cada execução, como calculados pela análise a partir de `raw/rdl_kpi_timeseries.csv` e "
             "`raw/rdl_actuation_log.csv` da própria execução.")
    L.append("")
    for seed in seeds:
        L.append(f"### 6.{seeds.index(seed) + 1} Semente {seed}")
        L.append("")
        rows = []
        for sc in scenarios:
            for bl in baselines:
                r = runs.get((sc, bl, seed))
                if r is None:
                    rows.append([sc, bl, *["—"] * len(METRICS), "ausente"])
                    continue
                rows.append([sc, bl, *[fmt_metric(m, r[m]) for m, _ in METRICS], f"`{r['run_id']}`"])
        L += table(["Cenário", "Baseline", *[l for _, l in METRICS], "Execução"], rows,
                   [":--", ":--"] + ["--:"] * len(METRICS) + [":--"])
        L.append("")

    # 7. Diferenças pareadas
    L.append("## 7. Diferenças pareadas B3 − Bx")
    L.append("")
    L.append("Para cada semente, valor do B3 menos o do baseline de comparação, na mesma semente. Média ± IC 95 %; "
             "\"melhor / pior / empate\" conta as sementes em que o B3 teve vazão maior (atraso menor), menor "
             "(maior) ou igual. \"IC exclui 0\" marca diferenças distinguíveis de zero com n = "
             f"{len(seeds)}.")
    L.append("")
    rows = []
    unfavorable = []
    for sc in scenarios:
        for other in [b for b in baselines if b != "B3"]:
            for metric, better in (("thp_conflict", 1), ("delay_conflict_ms", -1)):
                diffs = paired_diffs(runs, sc, metric, "B3", other)
                if not diffs:
                    continue
                mean, ci = mean_ci(diffs)
                wins = sum(1 for d in diffs if d * better > 0)
                losses = sum(1 for d in diffs if d * better < 0)
                ties = len(diffs) - wins - losses
                cell = f"{fmt(mean)} ± {fmt(ci)}" if ci is not None else fmt(mean)
                excludes = ci is not None and (mean - ci > 0 or mean + ci < 0)
                if excludes and mean * better < 0:
                    unfavorable.append(f"{sc}, B3 − {other}, {LABEL[metric]}: {cell} (B3 pior em {losses}/{len(diffs)} sementes)")
                rows.append([sc, f"B3 − {other}", LABEL[metric], cell, f"{wins} / {losses} / {ties}",
                             "sim" if excludes else "não"])
    L += table(["Cenário", "Comparação", "Métrica", "Diferença média ± IC 95 %", "Melhor / pior / empate", "IC exclui 0"],
               rows, [":--", ":--", ":--", "--:", "--:", ":-:"])
    L.append("")

    # 8. Cronogramas idênticos
    L.append("## 8. Cronogramas de ações idênticos entre baselines")
    L.append("")
    L.append("Baselines com o mesmo `action_schedule_sha256` aplicaram exatamente as mesmas ações; com a mesma semente, "
             "a simulação é a mesma e os resultados coincidem por construção.")
    L.append("")
    rows = []
    for sc in scenarios:
        patterns = set()
        for seed in seeds:
            groups: Dict[str, List[str]] = {}
            for bl in baselines:
                m = manifests.get(f"nr_{sc}_{bl}_seed{seed}")
                if m:
                    groups.setdefault(m.get("action_schedule_sha256"), []).append(bl)
            patterns.add(" · ".join(" = ".join(g) for g in groups.values()))
        rows.append([sc, "; ".join(sorted(patterns)), "sim" if len(patterns) == 1 else "não"])
    L += table(["Cenário", "Grupos com cronograma idêntico", "Mesmo padrão em todas as sementes"], rows)
    L.append("")

    # 9. Avaliação das hipóteses
    L.append("## 9. Avaliação das hipóteses")
    L.append("")
    for h in HYPOTHESES:
        if h["scenario"] not in scenarios:
            continue
        results = [evaluate_check_in(h["scenario"], c, runs) for c in h["checks"]]
        L.append(f"### {h['id']} ({h['scenario']}, {h['type']}): {hypothesis_verdict([r for r, _ in results])}")
        L.append("")
        L.append(h["text"])
        L.append("")
        for res, ev in results:
            L.append(f"- {res}: {ev}")
        L.append("")

    # 10. Conclusões
    L.append("## 10. Conclusões")
    L.append("")
    for v in (SUPPORTED, REFUTED, OPEN):
        ids = [h for h in HYPOTHESES if verdicts.get(h["id"]) == v]
        if not ids:
            continue
        L.append(f"**{v.capitalize()}s:**")
        L.append("")
        for h in ids:
            L.append(f"- {h['id']} ({h['scenario']}): {h['text']}")
            if v != SUPPORTED:
                for res, ev in (evaluate_check_in(h["scenario"], c, runs) for c in h["checks"]):
                    if res != PASS:
                        L.append(f"  - {res}: {ev}")
        L.append("")
    if unfavorable:
        L.append("**Diferenças desfavoráveis ao B3 com IC 95 % excluindo zero** (fora ou além das hipóteses; seção 7):")
        L.append("")
        L += [f"- {u}" for u in unfavorable]
        L.append("")
    identical = [sc for sc in scenarios if all(
        len({(manifests.get(f"nr_{sc}_{b}_seed{s}") or {}).get("action_schedule_sha256") for b in ("B1", "B2", "B3")}) == 1
        for s in seeds)]
    if identical:
        L.append(f"Nos cenários {', '.join(identical)}, B1, B2 e B3 aplicaram o mesmo cronograma em todas as sementes. "
                 "Nesses cenários a campanha mede o efeito de coordenar versus não coordenar, não uma vantagem "
                 "específica da RDL-N1 sobre FIFO ou prioridade estática.")
        L.append("")

    # 11. Ameaças e proveniência
    L.append("## 11. Ameaças à validade e proveniência")
    L.append("")
    L.append(f"- Malha aberta: a decisão não reage ao estado da RAN; o closed loop E2 (gates G1–G4) não é avaliado aqui.")
    L.append("- As propostas são estilizadas (valores e períodos fixos do catálogo), idênticas entre baselines e sementes.")
    L.append(f"- n = {len(seeds)} sementes por célula: ICs largos em métricas com variância entre sementes; "
             "sobreposição de IC não é teste de hipótese, e as regras da seção 2 usam a diferença pareada.")
    L.append("- Contagens (ações, handovers, inseguras, oscilações) dependem só do cronograma e são constantes entre sementes.")
    L.append("- S2, S4 e S5 rodam com `--disableSrs=true` (contorno de falha do 5G-LENA v5.1 em handover), igual para todos os baselines.")
    mixed = []
    for sc in scenarios:
        for seed in seeds:
            shas = {(manifests.get(f"nr_{sc}_{b}_seed{seed}") or {}).get("scenario_sha256") for b in baselines}
            if len(shas) > 1:
                groups = defaultdict(list)
                for b in baselines:
                    groups[((manifests.get(f"nr_{sc}_{b}_seed{seed}") or {}).get("scenario_sha256") or "?")[:8]].append(b)
                mixed.append(f"{sc} semente {seed} (" + "; ".join(f"{'/'.join(v)} `{k}`" for k, v in groups.items()) + ")")
    if mixed:
        L.append("- Fonte do cenário diferente dentro de um conjunto pareado: " + ", ".join(mixed) +
                 ". A mudança entre as versões (opção `--disableSrs`, desligada por padrão, e escalonamento de "
                 "handover) não afeta cenários sem `HANDOVER` no cronograma.")
    L.append("")
    if failures:
        L.append("Execuções com falha preservadas em `experiments/runs_failed/` (não entram na análise):")
        L.append("")
        L += table(["Execução", "Status", "Motivo (stderr)"], [[f"`{a}`", b, c] for a, b, c in failures])
        L.append("")

    # Apêndice
    L.append("## Apêndice A. Comando ns-3 de cada execução")
    L.append("")
    L.append("Campo `command` do `execution_manifest.json`, executado no WSL. Os caminhos de `--actionSchedule` apontam "
             "para `raw/action_schedule.csv` da própria execução.")
    L.append("")
    L.append("```bash")
    for rid in sorted(manifests, key=lambda r: (int(r.split("_")[1][1:]), r.split("_")[2], r)):
        L.append(f"# {rid}  ({manifests[rid].get('run_status')}, {manifests[rid].get('started_at_utc')})")
        L.append(redact_text(manifests[rid]["command"]))
    L.append("```")
    L.append("")
    return "\n".join(L)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--analysis", type=Path, default=None, help="JSON da análise (padrão: o mais recente)")
    parser.add_argument("--certificate", type=Path, default=None, help="JSON do certificado (padrão: o mais recente)")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    analysis_path = args.analysis or latest("conflict_analysis_*.json", ROOT / "reports" / "conflicts")
    if not analysis_path or not analysis_path.exists():
        print("ERRO: nenhuma análise em reports/conflicts/; rode analyze_conflict_runs.py antes.", file=sys.stderr)
        return 1
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    certificate_path = args.certificate or latest("certificate_*.json", ROOT / "reports" / "certification")
    certificate = json.loads(certificate_path.read_text(encoding="utf-8")) if certificate_path else None
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    manifests = load_manifests([r["run_id"] for r in analysis["runs"]])

    text = build_report(analysis, analysis_path.resolve(), catalog, manifests, certificate, certificate_path,
                        failed_runs())
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = args.out or ROOT / "reports" / "conflicts" / f"relatorio_campanha_{stamp}.md"
    out.write_text(text + "\n", encoding="utf-8", newline="\n")
    print(f"Relatório: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
