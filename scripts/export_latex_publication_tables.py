#!/usr/bin/env python3
"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Módulo: [ACAO 5.2] Gerador Automatizado de Tabelas LaTeX para Publicações Científicas
Arquivo: scripts/export_latex_publication_tables.py
Descrição: Processa dados consolidados e gera tabelas LaTeX formatadas com 'booktabs'
           para submissões IEEE (TNSM, TCCN) e SBC (SBRC, CSBC).
========================================================================================
"""

import os
import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

RESULTS_DIR = BASE_DIR / "experiments" / "results"
TABLES_DIR = RESULTS_DIR / "tables"
LATEX_DIR = TABLES_DIR / "latex"
LATEX_DIR.mkdir(parents=True, exist_ok=True)


def export_canonical_baselines_table():
    """Gera Tabela 1 em LaTeX: Comparação Pareada de Baselines (S1)."""
    csv_path = RESULTS_DIR / "canonical_simulation_master.csv"
    if not csv_path.exists():
        csv_path = TABLES_DIR / "table1_canonical_baselines_s1.csv"
    
    if not csv_path.exists():
        print(f"[AVISO] Arquivo {csv_path} não encontrado. Pulando Tabela 1.")
        return

    df = pd.read_csv(csv_path)
    
    tex_path = LATEX_DIR / "table1_canonical_baselines.tex"
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("% Table 1: Baseline Comparison in Scenario S1 (IEEE TNSM Format)\n")
        f.write("\\begin{table*}[t]\n")
        f.write("\\centering\n")
        f.write("\\caption{Desempenho Comparativo dos Baselines de Governança no Cenário S1 ($N=30$ UEs, Canal UMi 3,5 GHz).}\n")
        f.write("\\label{tab:canonical_baselines_s1}\n")
        f.write("\\begin{tabular}{lcccccc}\n")
        f.write("\\toprule\n")
        f.write("\\textbf{Baseline / Estratégia} & \\textbf{Vazão (Mbps)} & \\textbf{Latência Média (ms)} & \\textbf{Latência P95 (ms)} & \\textbf{Violação SLA (\\%)} & \\textbf{Jain ($J$)} & \\textbf{Potência gNB (W)} \\\\\n")
        f.write("\\midrule\n")
        for _, row in df.iterrows():
            b_name = row.get("baseline_name", row.get("baseline_id", "N/A"))
            tput = f"{row.get('throughput_mbps', 0):.1f}"
            lat_m = f"{row.get('mean_latency_ms', 0):.2f}"
            lat_p95 = f"{row.get('p95_latency_ms', 0):.2f}"
            sla_v = f"{row.get('urllc_sla_violation_pct', 0):.1f}\\%"
            jain = f"{row.get('jain_fairness_index', 0):.2f}"
            pwr = f"{row.get('gnb_power_w', 0):.1f}"
            
            if "B3" in str(b_name) or "H-RDL" in str(b_name):
                f.write(f"\\textbf{{{b_name}}} & \\textbf{{{tput}}} & \\textbf{{{lat_m}}} & \\textbf{{{lat_p95}}} & \\textbf{{{sla_v}}} & \\textbf{{{jain}}} & \\textbf{{{pwr}}} \\\\\n")
            else:
                f.write(f"{b_name} & {tput} & {lat_m} & {lat_p95} & {sla_v} & {jain} & {pwr} \\\\\n")
        f.write("\\bottomrule\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table*}\n")
    print(f"[OK] Tabela LaTeX exportada: {tex_path}")


def export_scalability_table():
    """Gera Tabela 2 em LaTeX: Benchmark de Escalabilidade Medida (Gate 3)."""
    csv_path = TABLES_DIR / "gate3_scalability_measured_summary.csv"
    if not csv_path.exists():
        print(f"[AVISO] Arquivo {csv_path} não encontrado. Pulando Tabela de Escalabilidade.")
        return

    df = pd.read_csv(csv_path)
    tex_path = LATEX_DIR / "table2_measured_scalability.tex"
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("% Table 2: Measured Scalability Profile (IEEE TNSM Format)\n")
        f.write("\\begin{table}[t]\n")
        f.write("\\centering\n")
        f.write("\\caption{Perfilamento de Escalabilidade Medida do Pipeline H-RDL ($N_{xApp} \\in [2, 100]$).}\n")
        f.write("\\label{tab:measured_scalability}\n")
        f.write("\\begin{tabular}{ccccccc}\n")
        f.write("\\toprule\n")
        f.write("$N_{xApp}$ & Lat. P50 (ms) & Lat. P95 (ms) & Lat. P99 (ms) & Vazão (prop/s) & CPU (\\%) & RAM (MB) \\\\\n")
        f.write("\\midrule\n")
        for _, row in df.iterrows():
            nx = int(row.get("num_xapps", 0))
            p50 = f"{row.get('p50_latency_ms', 0):.3f}"
            p95 = f"{row.get('p95_latency_ms', 0):.3f}"
            p99 = f"{row.get('p99_latency_ms', 0):.3f}"
            pps = f"{int(row.get('proposals_per_sec', 0)):,}"
            cpu = f"{row.get('cpu_util_pct', 0):.1f}"
            ram = f"{row.get('memory_peak_mb', 0):.2f}"
            f.write(f"{nx} & {p50} & {p95} & {p99} & {pps} & {cpu} & {ram} \\\\\n")
        f.write("\\bottomrule\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")
    print(f"[OK] Tabela LaTeX exportada: {tex_path}")


def export_scenarios_summary_table():
    """Gera Tabela 3 em LaTeX: Portfólio de Cenários S0 a S15."""
    csv_path = RESULTS_DIR / "dataset_s0_s15_validation.csv"
    if not csv_path.exists():
        print(f"[AVISO] Arquivo {csv_path} não encontrado. Pulando Tabela S0-S15.")
        return

    df = pd.read_csv(csv_path)
    tex_path = LATEX_DIR / "table3_scenarios_s0_s15_summary.tex"
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("% Table 3: S0-S15 Scenario Portfolio Validation Summary\n")
        f.write("\\begin{table*}[t]\n")
        f.write("\\centering\n")
        f.write("\\caption{Resumo da Validação Formal dos 16 Cenários Experimentais (S0 a S15).}\n")
        f.write("\\label{tab:scenarios_s0_s15}\n")
        f.write("\\begin{tabular}{clcccc}\n")
        f.write("\\toprule\n")
        f.write("\\textbf{ID} & \\textbf{Cenário Experimental} & \\textbf{Baseline} & \\textbf{H-RDL (F1)} & \\textbf{CA-RDL (F2)} & \\textbf{Latência Decisão (ms)} \\\\\n")
        f.write("\\midrule\n")
        for _, row in df.iterrows():
            cid = row.get("scenario_id", "N/A")
            name = row.get("scenario_name", "N/A")
            base = row.get("baseline_status", "FAIL")
            f1 = row.get("hrdl_f1_status", "PASS")
            f2 = row.get("cardl_f2_status", "PASS")
            lat = f"{row.get('decision_latency_ms', 0):.3f}"
            f.write(f"{cid} & {name} & {base} & \\textbf{{{f1}}} & \\textbf{{{f2}}} & {lat} \\\\\n")
        f.write("\\bottomrule\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table*}\n")
    print(f"[OK] Tabela LaTeX exportada: {tex_path}")


def main():
    print("=" * 80)
    print(" EXPORTADOR DE TABELAS LATEX PARA PUBLICAÇÕES (IEEE / SBC)")
    print("=" * 80)
    export_canonical_baselines_table()
    export_scalability_table()
    export_scenarios_summary_table()
    print("\n[SUCESSO] Todas as tabelas LaTeX foram geradas em experiments/results/tables/latex/\n")


if __name__ == "__main__":
    main()
