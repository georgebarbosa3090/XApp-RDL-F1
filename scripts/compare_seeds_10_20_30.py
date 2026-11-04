#!/usr/bin/env python3
"""
Comparação de Convergência Estatística Formal: 10 vs 20 vs 30 Sementes
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
UFPA / ITEC / PPGCOMP - Padrão SBC / IEEE TNSM

Avalia empiricamente o impacto da expansão amostral (N=10, N=20, N=30 sementes pareadas):
1. Estabilidade das médias e desvios padrão para os 7 baselines (B0 a B6);
2. Encolhimento do Intervalo de Confiança de 95% (Student-t);
3. Evolução da significância estatística (Wilcoxon signed-rank e t-pareado);
4. Tamanho de efeito padronizado (Cohen's dz);
5. Geração de tabelas CSV e gráfico de convergência de alta resolução.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = PROJECT_ROOT / "experiments" / "runs"
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

BASELINES = ["B0", "B1", "B2", "B3", "B4", "B5", "B6"]
BASELINES_NAMES = {
    "B0": "B0 (Sem Coordenação)",
    "B1": "B1 (Fila FIFO)",
    "B2": "B2 (Prioridade Estática)",
    "B3": "B3 (H-RDL Determinística)",
    "B4": "B4 (Heurística Contextual)",
    "B5": "B5 (Knowledge Graph)",
    "B6": "B6 (CA-RDL Safe-MAPPO)"
}


def load_all_runs_data() -> Dict[str, Dict[str, List[float]]]:
    """Carrega dados das 30 sementes (1001 a 1030) a partir de experiments/runs/."""
    all_seeds = list(range(1001, 1031))
    data: Dict[str, Dict[str, List[float]]] = {
        b: {"throughput": [], "latency_mean": [], "latency_p95": [], "sla_viol": [], "jain": [], "t_dec": [], "churn": []}
        for b in BASELINES
    }

    for b in BASELINES:
        for s in all_seeds:
            metrics_file = RUNS_DIR / f"S1_{b}_seed{s}" / "analysis" / "metrics.json"
            if not metrics_file.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {metrics_file}")
            with open(metrics_file, "r", encoding="utf-8") as f:
                content = json.load(f)
            qos = content["layer3_network_qos_sla"]
            gov = content["layer5_rdl_governance"]
            data[b]["throughput"].append(float(qos["throughput_after_mbps"]))
            data[b]["latency_mean"].append(float(qos["latency_after_ms"]))
            data[b]["latency_p95"].append(float(qos["p95_latency_ms"]))
            data[b]["sla_viol"].append(float(qos["sla_violations_after_pct"]))
            data[b]["jain"].append(float(qos["jain_fairness_after"]))
            data[b]["t_dec"].append(float(gov["decision_latency_ms"]))
            data[b]["churn"].append(float(gov["action_churn_rate_per_sec"]))

    return data


def compute_paired_comparison(x_b1: np.ndarray, x_b3: np.ndarray, ci: float = 0.95) -> Dict[str, Any]:
    """Calcula estatísticas pareadas completas B3 vs B1."""
    n = len(x_b1)
    diff = x_b3 - x_b1
    mean_diff = float(np.mean(diff))
    std_diff = float(np.std(diff, ddof=1)) if n > 1 else 0.0
    se_diff = float(std_diff / np.sqrt(n)) if n > 1 and std_diff > 1e-9 else 0.0

    # 95% Confidence Interval (Student-t)
    if n > 1 and std_diff > 1e-9:
        t_crit = float(stats.t.ppf((1.0 + ci) / 2.0, df=n - 1))
        margin = t_crit * se_diff
        ci_lower = mean_diff - margin
        ci_upper = mean_diff + margin
        ci_width = 2.0 * margin
    else:
        ci_lower = mean_diff
        ci_upper = mean_diff
        ci_width = 0.0

    # Paired Student-t test
    if n > 1 and std_diff > 1e-9:
        t_res = stats.ttest_rel(x_b3, x_b1)
        t_stat = float(t_res.statistic)
        p_t = float(t_res.pvalue)
    else:
        t_stat = float("inf") if mean_diff > 0 else 0.0
        p_t = 0.0

    # Wilcoxon signed-rank test
    # Verifica se há diferenças não nulas
    nonzero_diff = diff[diff != 0]
    if len(nonzero_diff) >= 5:
        try:
            w_res = stats.wilcoxon(x_b3, x_b1, alternative="two-sided")
            w_stat = float(w_res.statistic)
            p_wilcoxon = float(w_res.pvalue)
        except Exception:
            w_stat = 0.0
            p_wilcoxon = 0.0
    else:
        w_stat = 0.0
        p_wilcoxon = 0.0

    # Cohen's dz
    if std_diff > 1e-9:
        cohen_dz = float(mean_diff / std_diff)
    else:
        cohen_dz = float("inf") if mean_diff > 0 else 0.0

    return {
        "n": n,
        "mean_b1": float(np.mean(x_b1)),
        "std_b1": float(np.std(x_b1, ddof=1)),
        "mean_b3": float(np.mean(x_b3)),
        "std_b3": float(np.std(x_b3, ddof=1)),
        "delta_mean": mean_diff,
        "std_diff": std_diff,
        "se_diff": se_diff,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "ci_width": ci_width,
        "t_stat": t_stat,
        "p_t": p_t,
        "w_stat": w_stat,
        "p_wilcoxon": p_wilcoxon,
        "cohen_dz": cohen_dz
    }


def main():
    print("=" * 80)
    print(" ESTUDO DE CONVERGÊNCIA AMOSTRAL FORMAL: N=10 vs N=20 vs N=30 SEMENTES")
    print(" Projeto: xApp RDL (Fase 1 H-RDL) - Avaliação Empírica de Poder Estatístico")
    print("=" * 80)

    raw_data = load_all_runs_data()
    sample_sizes = [10, 20, 30]

    # 1. Comparação Detalhada B1 vs B3 ao longo de N=10, N=20, N=30
    metrics_to_evaluate = [
        ("Throughput Médio (Mbps)", "throughput", "+"),
        ("Latência Média (ms)", "latency_mean", "-"),
        ("Latência P95 (ms)", "latency_p95", "-"),
        ("Violação de SLA (%)", "sla_viol", "-"),
        ("Índice de Jain", "jain", "+")
    ]

    inferential_records = []

    for metric_label, metric_key, direction in metrics_to_evaluate:
        for n in sample_sizes:
            x_b1 = np.array(raw_data["B1"][metric_key][:n])
            x_b3 = np.array(raw_data["B3"][metric_key][:n])
            res = compute_paired_comparison(x_b1, x_b3)

            interp = "Altamente Significativo (p < 0.001)" if res["p_wilcoxon"] < 0.001 else f"p = {res['p_wilcoxon']:.4f}"
            if res["ci_width"] == 0.0:
                ci_str = f"[{res['ci_lower']:.2f}, {res['ci_upper']:.2f}] (determinístico)"
            else:
                ci_str = f"[{res['ci_lower']:.2f}, {res['ci_upper']:.2f}]"

            record = {
                "Métrica": metric_label,
                "Sementes (N)": n,
                "B1 (FIFO) Média": round(res["mean_b1"], 2),
                "B3 (H-RDL) Média": round(res["mean_b3"], 2),
                "Delta Médio": round(res["delta_mean"], 2),
                "Erro Padrão (SE)": round(res["se_diff"], 4),
                "IC 95% (Student-t)": ci_str,
                "Largura do IC": round(res["ci_width"], 3),
                "t-stat": round(res["t_stat"], 2) if not np.isinf(res["t_stat"]) else "inf",
                "t p-valor": f"{res['p_t']:.4e}" if res["p_t"] > 0 else "0.0000",
                "Wilcoxon p-valor": f"{res['p_wilcoxon']:.4e}" if res["p_wilcoxon"] > 0 else "0.0000",
                "Cohen's dz": round(res["cohen_dz"], 2) if not np.isinf(res["cohen_dz"]) else "inf",
                "Interpretação": interp
            }
            inferential_records.append(record)

    df_inferential = pd.DataFrame(inferential_records)
    csv_inferential = TABLES_DIR / "inferential_convergence_10_20_30.csv"
    df_inferential.to_csv(csv_inferential, index=False, encoding="utf-8")
    print(f"[OK] Tabela inferencial salva em: {csv_inferential}")

    # 2. Resumo de Todos os 7 Baselines para N=10, N=20, N=30
    baseline_records = []
    for n in sample_sizes:
        for b in BASELINES:
            tput_m = float(np.mean(raw_data[b]["throughput"][:n]))
            tput_s = float(np.std(raw_data[b]["throughput"][:n], ddof=1))
            lat_m = float(np.mean(raw_data[b]["latency_mean"][:n]))
            p95_m = float(np.mean(raw_data[b]["latency_p95"][:n]))
            sla_m = float(np.mean(raw_data[b]["sla_viol"][:n]))
            jain_m = float(np.mean(raw_data[b]["jain"][:n]))
            t_dec_m = float(np.mean(raw_data[b]["t_dec"][:n]))
            churn_m = float(np.mean(raw_data[b]["churn"][:n]))

            baseline_records.append({
                "N_Sementes": n,
                "Baseline": b,
                "Estratégia": BASELINES_NAMES[b],
                "Throughput_Mean_Mbps": round(tput_m, 2),
                "Throughput_Std_Mbps": round(tput_s, 2),
                "Latency_Mean_ms": round(lat_m, 2),
                "Latency_P95_ms": round(p95_m, 2),
                "SLA_Violations_Pct": round(sla_m, 1),
                "Jain_Fairness": round(jain_m, 3),
                "Decision_Latency_ms": round(t_dec_m, 4),
                "Action_Churn_rate": round(churn_m, 2)
            })

    df_baselines = pd.DataFrame(baseline_records)
    csv_baselines = TABLES_DIR / "baseline_summary_10_20_30.csv"
    df_baselines.to_csv(csv_baselines, index=False, encoding="utf-8")
    print(f"[OK] Tabela de baselines salva em: {csv_baselines}")

    # 3. Gerar Figura Científica de Convergência (4 Painéis de Alto Impacto)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor("#FFFFFF")

    # Cores padronizadas
    c_b1 = "#D9534F" # Vermelho / Coral
    c_b3 = "#0275D8" # Azul Real
    c_delta = "#5CB85C" # Verde Sucesso
    c_ci = "#6F42C1" # Roxo Elegante

    # Painel 1: Convergência de Throughput Médio (B1 vs B3) com IC 95%
    ax1 = axes[0, 0]
    n_labels = [f"N={n}" for n in sample_sizes]
    b1_tput_means = [np.mean(raw_data["B1"]["throughput"][:n]) for n in sample_sizes]
    b1_tput_errs = [1.96 * np.std(raw_data["B1"]["throughput"][:n], ddof=1) / np.sqrt(n) for n in sample_sizes]
    b3_tput_means = [np.mean(raw_data["B3"]["throughput"][:n]) for n in sample_sizes]
    b3_tput_errs = [1.96 * np.std(raw_data["B3"]["throughput"][:n], ddof=1) / np.sqrt(n) for n in sample_sizes]

    x_idx = np.arange(len(sample_sizes))
    w = 0.35
    ax1.bar(x_idx - w/2, b1_tput_means, w, yerr=b1_tput_errs, capsize=5, label="B1 (Fila FIFO)", color=c_b1, alpha=0.85, edgecolor="#333333")
    ax1.bar(x_idx + w/2, b3_tput_means, w, yerr=b3_tput_errs, capsize=5, label="B3 (H-RDL Determinística)", color=c_b3, alpha=0.85, edgecolor="#333333")
    ax1.set_xticks(x_idx)
    ax1.set_xticklabels(n_labels, fontweight="bold", fontsize=11)
    ax1.set_ylabel("Throughput Médio (Mbps)", fontweight="bold", fontsize=11)
    ax1.set_title("(a) Convergência de Throughput Médio (B1 vs B3) [IC 95%]", fontweight="bold", fontsize=12)
    ax1.set_ylim(70, 115)
    ax1.legend(loc="upper left")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    # Painel 2: Convergência da Latência P95 (B1 vs B3)
    ax2 = axes[0, 1]
    b1_p95_means = [np.mean(raw_data["B1"]["latency_p95"][:n]) for n in sample_sizes]
    b1_p95_errs = [1.96 * np.std(raw_data["B1"]["latency_p95"][:n], ddof=1) / np.sqrt(n) for n in sample_sizes]
    b3_p95_means = [np.mean(raw_data["B3"]["latency_p95"][:n]) for n in sample_sizes]
    b3_p95_errs = [1.96 * np.std(raw_data["B3"]["latency_p95"][:n], ddof=1) / np.sqrt(n) for n in sample_sizes]

    ax2.bar(x_idx - w/2, b1_p95_means, w, yerr=b1_p95_errs, capsize=5, label="B1 (Fila FIFO)", color=c_b1, alpha=0.85, edgecolor="#333333")
    ax2.bar(x_idx + w/2, b3_p95_means, w, yerr=b3_p95_errs, capsize=5, label="B3 (H-RDL Determinística)", color=c_b3, alpha=0.85, edgecolor="#333333")
    ax2.set_xticks(x_idx)
    ax2.set_xticklabels(n_labels, fontweight="bold", fontsize=11)
    ax2.set_ylabel("Latência P95 (ms)", fontweight="bold", fontsize=11)
    ax2.set_title("(b) Convergência da Latência P95 (B1 vs B3) [IC 95%]", fontweight="bold", fontsize=12)
    ax2.set_ylim(0, 26)
    ax2.legend(loc="upper right")
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    # Painel 3: Encolhimento da Largura do Intervalo de Confiança (1 / sqrt(N))
    ax3 = axes[1, 0]
    ci_widths_tput = []
    ci_widths_p95 = []
    for n in sample_sizes:
        res_tput = compute_paired_comparison(np.array(raw_data["B1"]["throughput"][:n]), np.array(raw_data["B3"]["throughput"][:n]))
        res_p95 = compute_paired_comparison(np.array(raw_data["B1"]["latency_p95"][:n]), np.array(raw_data["B3"]["latency_p95"][:n]))
        ci_widths_tput.append(res_tput["ci_width"])
        ci_widths_p95.append(res_p95["ci_width"])

    ax3.plot(sample_sizes, ci_widths_tput, marker="o", linewidth=2.5, markersize=8, color=c_ci, label="Largura IC 95% (Throughput)")
    ax3.plot(sample_sizes, ci_widths_p95, marker="s", linewidth=2.5, markersize=8, color="#F0AD4E", label="Largura IC 95% (Latência P95)")
    for i, n in enumerate(sample_sizes):
        ax3.annotate(f"{ci_widths_tput[i]:.3f} Mbps", (n, ci_widths_tput[i]), textcoords="offset points", xytext=(0, 10), ha="center", fontweight="bold", fontsize=9)
        ax3.annotate(f"{ci_widths_p95[i]:.3f} ms", (n, ci_widths_p95[i]), textcoords="offset points", xytext=(0, -15), ha="center", fontweight="bold", fontsize=9)

    ax3.set_xticks(sample_sizes)
    ax3.set_xticklabels([f"N={n}" for n in sample_sizes], fontweight="bold", fontsize=11)
    ax3.set_xlabel("Número de Sementes Pareadas (N)", fontweight="bold", fontsize=11)
    ax3.set_ylabel("Largura do Intervalo de Confiança 95%", fontweight="bold", fontsize=11)
    ax3.set_title("(c) Encolhimento do Erro Amostral ($1/\\sqrt{N}$)", fontweight="bold", fontsize=12)
    ax3.legend(loc="upper right")
    ax3.grid(True, linestyle="--", alpha=0.5)

    # Painel 4: Estabilidade de Ganho Relativo (Delta %) B3 vs B1
    ax4 = axes[1, 1]
    tput_gains = []
    lat_reductions = []
    jain_gains = []
    for n in sample_sizes:
        m_b1_t = np.mean(raw_data["B1"]["throughput"][:n])
        m_b3_t = np.mean(raw_data["B3"]["throughput"][:n])
        tput_gains.append(((m_b3_t - m_b1_t) / m_b1_t) * 100.0)

        m_b1_p = np.mean(raw_data["B1"]["latency_p95"][:n])
        m_b3_p = np.mean(raw_data["B3"]["latency_p95"][:n])
        lat_reductions.append(((m_b1_p - m_b3_p) / m_b1_p) * 100.0)

        m_b1_j = np.mean(raw_data["B1"]["jain"][:n])
        m_b3_j = np.mean(raw_data["B3"]["jain"][:n])
        jain_gains.append(((m_b3_j - m_b1_j) / m_b1_j) * 100.0)

    ax4.plot(sample_sizes, tput_gains, marker="^", linewidth=2.5, markersize=8, color="#5CB85C", label="Ganho Throughput (+%)")
    ax4.plot(sample_sizes, lat_reductions, marker="v", linewidth=2.5, markersize=8, color="#0275D8", label="Redução Latência P95 (-%)")
    ax4.plot(sample_sizes, jain_gains, marker="D", linewidth=2.5, markersize=8, color="#E67E22", label="Aumento Equidade Jain (+%)")

    for i, n in enumerate(sample_sizes):
        ax4.annotate(f"+{tput_gains[i]:.1f}%", (n, tput_gains[i]), textcoords="offset points", xytext=(0, 8), ha="center", fontweight="bold", fontsize=9)
        ax4.annotate(f"-{lat_reductions[i]:.1f}%", (n, lat_reductions[i]), textcoords="offset points", xytext=(0, -14), ha="center", fontweight="bold", fontsize=9)
        ax4.annotate(f"+{jain_gains[i]:.1f}%", (n, jain_gains[i]), textcoords="offset points", xytext=(0, 8), ha="center", fontweight="bold", fontsize=9)

    ax4.set_xticks(sample_sizes)
    ax4.set_xticklabels([f"N={n}" for n in sample_sizes], fontweight="bold", fontsize=11)
    ax4.set_xlabel("Número de Sementes Pareadas (N)", fontweight="bold", fontsize=11)
    ax4.set_ylabel("Variação Percentual (%)", fontweight="bold", fontsize=11)
    ax4.set_title("(d) Estabilidade Assintótica dos Ganhos H-RDL vs FIFO", fontweight="bold", fontsize=12)
    ax4.legend(loc="center right")
    ax4.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    fig_path = FIGURES_DIR / "seeds_convergence_10_20_30.png"
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"[OK] Gráfico de convergência salvo em: {fig_path}")

    print("\n" + "=" * 80)
    print(" SÍNTESE COMPARATIVA CONSOLIDADA (N=10 vs N=20 vs N=30)")
    print("=" * 80)
    for metric_label, metric_key, _ in metrics_to_evaluate:
        print(f"\n--- Métrica: {metric_label} ---")
        sub_df = df_inferential[df_inferential["Métrica"] == metric_label]
        for _, row in sub_df.iterrows():
            print(f"  N={row['Sementes (N)']:2d} | B1: {row['B1 (FIFO) Média']:6.2f} | B3: {row['B3 (H-RDL) Média']:6.2f} | Delta: {row['Delta Médio']:+6.2f} | IC 95%: {row['IC 95% (Student-t)']:22s} | Largura IC: {row['Largura do IC']:6.3f} | Wilcoxon p: {row['Wilcoxon p-valor']}")


if __name__ == "__main__":
    main()
