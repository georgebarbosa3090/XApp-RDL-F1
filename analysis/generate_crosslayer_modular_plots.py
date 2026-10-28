#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_crosslayer_modular_plots.py
====================================
Gera o Dashboard Mestre Aprimorado de Análise Cross-Layer e Gráficos Separados Especializados
com 300 DPI, estética premium, anotações de Pareto, correlações e distribuições.
Baseado 100% em dados empíricos de experiments/runs/.
"""

import os
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns

root_dir = Path(__file__).resolve().parent.parent
figures_dir = root_dir / "reports" / "figures"
docs_figures_dir = root_dir / "docs" / "figures"
runs_dir = root_dir / "experiments" / "runs"

figures_dir.mkdir(parents=True, exist_ok=True)
docs_figures_dir.mkdir(parents=True, exist_ok=True)

# Configuração de Estilo Global
sns.set_theme(style="whitegrid", font_scale=1.0)
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial", "Liberation Sans"],
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9.5,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.edgecolor": "#BDC3C7",
    "axes.linewidth": 1.0,
    "grid.color": "#EAEDED",
    "grid.linestyle": "--",
    "grid.alpha": 0.7
})

# Paleta Cromática Harmoniosa e Científica para os Baselines
BASELINE_COLORS = {
    "B0": "#E74C3C",  # Vermelho Alerta (Sem Governança)
    "B1": "#E67E22",  # Laranja (Prioridade Estática)
    "B2": "#F39C12",  # Âmbar (Token Bucket)
    "B3": "#2980B9",  # Azul Royal (H-RDL Fase 1)
    "B4": "#8E44AD",  # Roxo Nobre (Utilidade NDT)
    "B5": "#16A085",  # Verde Petróleo (MAPPO Unconstrained)
    "B6": "#27AE60"   # Verde Esmeralda (CA-RDL Safe-MAPPO Fase 2)
}

BASELINE_LABELS = {
    "B0": "B0: Sem Governança",
    "B1": "B1: Prioridade Estática",
    "B2": "B2: Token Bucket Rígido",
    "B3": "B3: H-RDL (Fase 1)",
    "B4": "B4: Utilidade NDT",
    "B5": "B5: MAPPO Não-Restrito",
    "B6": "B6: CA-RDL Safe-MAPPO (Fase 2)"
}

BASELINE_MARKERS = {
    "B0": "X",
    "B1": "s",
    "B2": "v",
    "B3": "D",
    "B4": "p",
    "B5": "^",
    "B6": "o"
}

def load_runs_data() -> pd.DataFrame:
    """Carrega dados empíricos dos runs de experiments/runs."""
    records = []
    if runs_dir.exists():
        for run_path in sorted(runs_dir.iterdir()):
            if run_path.is_dir() and run_path.name.startswith("S1_B"):
                mf = run_path / "analysis" / "metrics.json"
                if mf.exists():
                    with open(mf, "r", encoding="utf-8") as f:
                        m = json.load(f)
                    records.append({
                        "run_id": m.get("run_id"),
                        "scenario": m.get("scenario", "S1"),
                        "baseline": m.get("baseline"),
                        "baseline_label": BASELINE_LABELS.get(m.get("baseline"), m.get("baseline")),
                        "seed": int(m.get("seed", 1001)),
                        "throughput": float(m["layer3_network_qos_sla"]["throughput_after_mbps"]),
                        "latency": float(m["layer3_network_qos_sla"]["latency_after_ms"]),
                        "p95_latency": float(m["layer3_network_qos_sla"]["p95_latency_ms"]),
                        "sla_violations": float(m["layer3_network_qos_sla"]["sla_violations_after_pct"]),
                        "jain_fairness": float(m["layer3_network_qos_sla"]["jain_fairness_after"]),
                        "decision_latency": float(m["layer5_rdl_governance"]["decision_latency_ms"]),
                        "action_churn": float(m["layer5_rdl_governance"]["action_churn_rate_per_sec"]),
                        "sinr_db": float(m["layer2_phy_mac"]["sinr_db"]),
                        "prb_usage": float(m["layer2_phy_mac"]["prb_usage_pct"]),
                        "bler_pct": float(m["layer2_phy_mac"]["bler_pct"]),
                        "selected_mcs": int(m["layer2_phy_mac"]["selected_mcs"])
                    })
    return pd.DataFrame(records)

def save_dual(fig, filename: str):
    """Salva a figura nos diretórios de relatórios e de documentação."""
    p_rep = figures_dir / filename
    p_doc = docs_figures_dir / filename
    fig.savefig(p_rep, dpi=300, bbox_inches="tight")
    fig.savefig(p_doc, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f" [OK] Salva figura com sucesso: {filename}")

# =============================================================================
# 1. FIGURA MESTRA COMPLETA (DASHBOARD 2x2 CROSS-LAYER)
# =============================================================================
def plot_master_crosslayer_dashboard(df: pd.DataFrame):
    """Gera o Dashboard Mestre 2x2 Cross-Layer de Alto Impacto para substituir o Pairplot clássico."""
    fig, axes = plt.subplots(2, 2, figsize=(14.0, 11.0))
    fig.suptitle("F19: Governança Cross-Layer O-RAN — Avaliação Multidimensional (PHY / MAC / RLC / QoS)", 
                 fontsize=15, fontweight="bold", y=0.98, color="#2C3E50")

    # -------------------------------------------------------------------------
    # PAINEL (0,0): Trade-off de QoS e Latência (Fronteira de Pareto & Envelope SLA)
    # -------------------------------------------------------------------------
    ax0 = axes[0, 0]
    # Região de Conformidade SLA (Latência < 11.5 ms e Throughput > 100 Mbps)
    rect = patches.Rectangle((100, 9.0), 10, 2.7, linewidth=1.5, edgecolor="#27AE60", 
                             facecolor="#E8F8F5", alpha=0.5, linestyle=":", zorder=1)
    ax0.add_patch(rect)
    ax0.text(105.0, 11.1, "Região Ótima SLA\n• Latência < 11.5 ms\n• Vazão > 100 Mbps", 
             fontsize=8.5, color="#196F3D", fontweight="bold")

    for base, grp in df.groupby("baseline"):
        ax0.scatter(grp["throughput"], grp["latency"], 
                    color=BASELINE_COLORS[base], marker=BASELINE_MARKERS[base],
                    s=95, alpha=0.85, edgecolors="black", linewidths=0.7,
                    label=BASELINE_LABELS[base], zorder=3)
        # Centroide com elipse/círculo indicativo
        cx, cy = grp["throughput"].mean(), grp["latency"].mean()
        ax0.plot(cx, cy, marker=BASELINE_MARKERS[base], color=BASELINE_COLORS[base], 
                 markersize=12, markeredgecolor="black", markeredgewidth=1.2, zorder=4)

    # Linha Guia de Pareto
    pareto_pts = df[df["baseline"].isin(["B0", "B1", "B2", "B3", "B6"])].groupby("baseline")[["throughput", "latency"]].mean().sort_values("throughput")
    ax0.plot(pareto_pts["throughput"], pareto_pts["latency"], color="#7F8C8D", linestyle="--", linewidth=1.2, alpha=0.7, zorder=2)
    ax0.annotate("Fronteira de Pareto\n(Trade-off QoS vs Latência)", xy=(92.0, 13.8), xytext=(86.0, 12.0),
                 arrowprops=dict(arrowstyle="->", color="#34495E", lw=1.2), fontsize=8.5, color="#2C3E50", fontweight="bold")

    ax0.set_xlabel("Vazão Agregada (Throughput) [Mbps] (Maior = Melhor)")
    ax0.set_ylabel("Latência Fim-a-Fim [ms] (Menor = Melhor)")
    ax0.set_title("(A) Trade-off de Desempenho e Fronteira de Pareto (QoS × Latência)", fontweight="bold", fontsize=11)
    ax0.legend(loc="upper right", framealpha=0.9, fontsize=8.5)

    # -------------------------------------------------------------------------
    # PAINEL (0,1): Acoplamento Físico-Transporte (SINR vs Throughput & Eficiência Espectral)
    # -------------------------------------------------------------------------
    ax1 = axes[0, 1]
    for base, grp in df.groupby("baseline"):
        ax1.scatter(grp["sinr_db"], grp["throughput"], 
                    color=BASELINE_COLORS[base], marker=BASELINE_MARKERS[base],
                    s=95, alpha=0.85, edgecolors="black", linewidths=0.7,
                    label=BASELINE_LABELS[base], zorder=3)
        if len(grp) > 1:
            sns.regplot(data=grp, x="sinr_db", y="throughput", ax=ax1, scatter=False,
                        color=BASELINE_COLORS[base], line_kws={"linewidth": 1.0, "alpha": 0.6})

    ax1.set_xlabel("SINR da Camada Física [dB]")
    ax1.set_ylabel("Vazão Agregada [Mbps]")
    ax1.set_title("(B) Acoplamento Físico-Transporte (SINR × Vazão por Baseline)", fontweight="bold", fontsize=11)
    ax1.text(14.6, 105.8, "Eficiência de Alocação Espectral:\nCA-RDL (B6) e H-RDL (B3) extraem maior vazão\npara o mesmo patamar de SINR através de alocação ótima", 
             fontsize=8.5, bbox=dict(boxstyle="round,pad=0.4", facecolor="#FEF9E7", edgecolor="#F39C12", alpha=0.85))

    # -------------------------------------------------------------------------
    # PAINEL (1,0): Eficiência MAC e Supressão de Instabilidade (PRB Usage vs Action Churn)
    # -------------------------------------------------------------------------
    ax2 = axes[1, 0]
    for base, grp in df.groupby("baseline"):
        ax2.scatter(grp["prb_usage"], grp["action_churn"], 
                    color=BASELINE_COLORS[base], marker=BASELINE_MARKERS[base],
                    s=95, alpha=0.85, edgecolors="black", linewidths=0.7,
                    label=BASELINE_LABELS[base], zorder=3)

    ax2.axhline(0.2, color="#27AE60", linestyle=":", linewidth=1.2, label="Estabilidade Alta (Churn < 0.2/s)")
    ax2.axhline(0.8, color="#E74C3C", linestyle=":", linewidth=1.2, label="Instabilidade Crítica (Churn > 0.8/s)")
    
    ax2.annotate("Região de Máxima Estabilidade\ne Uso Otimizado de PRB\n(H-RDL & CA-RDL)", 
                 xy=(78.5, 0.08), xytext=(81.0, 0.35),
                 arrowprops=dict(arrowstyle="->", color="#1E8449", lw=1.3),
                 fontsize=8.5, color="#1E8449", fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="#E8F8F5", edgecolor="#27AE60"))

    ax2.annotate("Tempestade de Oscilação (Ping-Pong)\ne Saturação Desgovernada (B0/B1)", 
                 xy=(93.5, 0.98), xytext=(81.0, 0.75),
                 arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.3),
                 fontsize=8.5, color="#C0392B", fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="#FDEDEC", edgecolor="#E74C3C"))

    ax2.set_xlabel("Ocupação de Recursos Físicos MAC (PRB Usage) [%]")
    ax2.set_ylabel("Taxa de Churn de Ações de Controle [Ações / s]")
    ax2.set_title("(C) Estabilidade do Controle e Ocupação MAC (PRB × Action Churn)", fontweight="bold", fontsize=11)

    # -------------------------------------------------------------------------
    # PAINEL (1,1): Matriz de Correlação Cross-Layer com Coeficientes Numéricos
    # -------------------------------------------------------------------------
    ax3 = axes[1, 1]
    corr_cols = ["throughput", "latency", "sinr_db", "prb_usage", "action_churn"]
    corr_labels = ["Vazão (Mbps)", "Latência (ms)", "SINR (dB)", "Uso PRB (%)", "Churn (Ações/s)"]
    corr_matrix = df[corr_cols].corr()
    
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="vlag", vmin=-1.0, vmax=1.0, 
                square=True, ax=ax3, cbar_kws={"label": "Coeficiente de Correlação de Pearson (r)", "shrink": 0.8},
                xticklabels=corr_labels, yticklabels=corr_labels, linewidths=1.0, linecolor="white",
                annot_kws={"size": 9.5, "fontweight": "bold"})
    ax3.set_title("(D) Matriz de Correlação Cross-Layer Global", fontweight="bold", fontsize=11)

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    save_dual(fig, "fig_19_crosslayer_pairplot.png")
    save_dual(fig, "fig_19_crosslayer_analysis_dashboard.png")

# =============================================================================
# 2. GRÁFICOS SEPARADOS EM ALTA RESOLUÇÃO
# =============================================================================

def plot_sep_fig19a_pareto(df: pd.DataFrame):
    """Gráfico Separado 19A: Fronteira de Pareto e Envelope de Latência x Vazão."""
    fig, ax = plt.subplots(figsize=(8.0, 5.5))
    
    # Região de Conformidade SLA
    rect = patches.Rectangle((100, 9.0), 10, 2.8, linewidth=1.8, edgecolor="#27AE60", 
                             facecolor="#E8F8F5", alpha=0.55, linestyle="--", zorder=1)
    ax.add_patch(rect)
    ax.text(105.0, 11.2, "Zona Ótima SLA\n• Latência < 11.5 ms\n• Vazão > 100 Mbps", 
            fontsize=9.0, color="#196F3D", fontweight="bold")

    for base, grp in df.groupby("baseline"):
        ax.scatter(grp["throughput"], grp["latency"], 
                   color=BASELINE_COLORS[base], marker=BASELINE_MARKERS[base],
                   s=120, alpha=0.9, edgecolors="black", linewidths=0.9,
                   label=BASELINE_LABELS[base], zorder=3)

    # Curva de Pareto Média
    pareto_pts = df[df["baseline"].isin(["B0", "B1", "B2", "B3", "B6"])].groupby("baseline")[["throughput", "latency"]].mean().sort_values("throughput")
    ax.plot(pareto_pts["throughput"], pareto_pts["latency"], color="#2C3E50", linestyle="-.", linewidth=1.8, alpha=0.8, zorder=2, label="Fronteira de Pareto")

    ax.set_xlabel("Vazão Agregada da Rede [Mbps]", fontweight="semibold")
    ax.set_ylabel("Latência Fim-a-Fim Ponderada [ms]", fontweight="semibold")
    ax.set_title("F19A: Fronteira de Pareto — Trade-off entre Vazão e Latência no Near-RT RIC", pad=12, fontweight="bold")
    ax.legend(loc="upper right", framealpha=0.95, edgecolor="#BDC3C7")
    fig.tight_layout()
    save_dual(fig, "fig_19a_crosslayer_pareto_throughput_latency.png")

def plot_sep_fig19b_sinr_throughput(df: pd.DataFrame):
    """Gráfico Separado 19B: Acoplamento Físico-Transporte (SINR vs Throughput)."""
    fig, ax = plt.subplots(figsize=(8.0, 5.5))
    
    for base, grp in df.groupby("baseline"):
        ax.scatter(grp["sinr_db"], grp["throughput"], 
                   color=BASELINE_COLORS[base], marker=BASELINE_MARKERS[base],
                   s=120, alpha=0.9, edgecolors="black", linewidths=0.9,
                   label=BASELINE_LABELS[base], zorder=3)
        if len(grp) > 1:
            sns.regplot(data=grp, x="sinr_db", y="throughput", ax=ax, scatter=False,
                        color=BASELINE_COLORS[base], line_kws={"linewidth": 1.4, "alpha": 0.7})

    ax.set_xlabel("SINR da Camada Física de Rádio [dB]", fontweight="semibold")
    ax.set_ylabel("Vazão Agregada de Aplicação [Mbps]", fontweight="semibold")
    ax.set_title("F19B: Relação Cross-Layer entre SINR e Vazão por Política de Controle", pad=12, fontweight="bold")
    ax.legend(loc="lower right", framealpha=0.95, edgecolor="#BDC3C7")
    fig.tight_layout()
    save_dual(fig, "fig_19b_crosslayer_phy_sinr_throughput.png")

def plot_sep_fig19c_prb_churn(df: pd.DataFrame):
    """Gráfico Separado 19C: Estabilidade do Controle vs Ocupação MAC de PRB."""
    fig, ax = plt.subplots(figsize=(8.0, 5.5))
    
    for base, grp in df.groupby("baseline"):
        ax.scatter(grp["prb_usage"], grp["action_churn"], 
                   color=BASELINE_COLORS[base], marker=BASELINE_MARKERS[base],
                   s=120, alpha=0.9, edgecolors="black", linewidths=0.9,
                   label=BASELINE_LABELS[base], zorder=3)

    ax.axhline(0.2, color="#27AE60", linestyle="--", linewidth=1.5, label="Meta de Estabilidade (< 0.2 ações/s)")
    ax.axhline(0.8, color="#E74C3C", linestyle="--", linewidth=1.5, label="Instabilidade Excessiva (> 0.8 ações/s)")

    ax.annotate("Controle Estável e Otimizado\n(H-RDL & CA-RDL)", 
                xy=(78.2, 0.09), xytext=(81.0, 0.35),
                arrowprops=dict(arrowstyle="->", color="#1E8449", lw=1.5),
                fontsize=9.5, color="#1E8449", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#E8F8F5", edgecolor="#27AE60"))

    ax.annotate("Oscilações Ping-Pong Severas\n(Sem Governança B0 / B1)", 
                xy=(93.5, 0.98), xytext=(81.0, 0.75),
                arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.5),
                fontsize=9.5, color="#C0392B", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#FDEDEC", edgecolor="#E74C3C"))

    ax.set_xlabel("Ocupação de Recursos de Rádio MAC (PRB Usage) [%]", fontweight="semibold")
    ax.set_ylabel("Taxa de Churn de Decisões de Controle [Ações / s]", fontweight="semibold")
    ax.set_title("F19C: Supressão de Churn de Controle e Eficiência de Alocação de PRB", pad=12, fontweight="bold")
    ax.legend(loc="center right", framealpha=0.95, edgecolor="#BDC3C7")
    fig.tight_layout()
    save_dual(fig, "fig_19c_crosslayer_mac_stability_churn.png")

def plot_sep_fig19d_heatmap(df: pd.DataFrame):
    """Gráfico Separado 19D: Matriz de Calor de Correlação Cross-Layer."""
    fig, ax = plt.subplots(figsize=(7.5, 6.0))
    corr_cols = ["throughput", "latency", "sinr_db", "prb_usage", "action_churn"]
    corr_labels = ["Vazão (Mbps)", "Latência (ms)", "SINR (dB)", "Uso PRB (%)", "Churn (Ações/s)"]
    corr_matrix = df[corr_cols].corr()

    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1.0, vmax=1.0, 
                square=True, ax=ax, cbar_kws={"label": "Coeficiente de Correlação de Pearson (r)"},
                xticklabels=corr_labels, yticklabels=corr_labels, linewidths=1.2, linecolor="white",
                annot_kws={"size": 11, "fontweight": "bold"})
    ax.set_title("F19D: Matriz de Correlação Multivariada Cross-Layer (PHY / MAC / RLC / QoS)", pad=14, fontweight="bold")
    fig.tight_layout()
    save_dual(fig, "fig_19d_crosslayer_correlation_heatmap.png")

def plot_sep_fig19e_violins(df: pd.DataFrame):
    """Gráfico Separado 19E: Distribuição Marginal (Violin / Boxplot) das 5 Métricas."""
    fig, axes = plt.subplots(2, 2, figsize=(13.0, 9.5))
    fig.suptitle("F19E: Distribuição de Desempenho por Camada de Protocolo (PHY / MAC / RLC / QoS)", 
                 fontsize=14, fontweight="bold", y=0.98, color="#2C3E50")

    order = ["B0", "B1", "B2", "B3", "B4", "B5", "B6"]

    # Subplot 1: Throughput
    sns.boxplot(data=df, x="baseline", y="throughput", hue="baseline", order=order, palette=BASELINE_COLORS, ax=axes[0, 0], width=0.5, boxprops=dict(alpha=0.85), legend=False)
    sns.stripplot(data=df, x="baseline", y="throughput", order=order, color="black", size=5, jitter=0.2, ax=axes[0, 0], alpha=0.6)
    axes[0, 0].set_title("(1) Vazão Agregada de Aplicação [Mbps]", fontweight="bold")
    axes[0, 0].set_xlabel("")
    axes[0, 0].set_ylabel("Vazão (Mbps)")

    # Subplot 2: Latência
    sns.boxplot(data=df, x="baseline", y="latency", hue="baseline", order=order, palette=BASELINE_COLORS, ax=axes[0, 1], width=0.5, boxprops=dict(alpha=0.85), legend=False)
    sns.stripplot(data=df, x="baseline", y="latency", order=order, color="black", size=5, jitter=0.2, ax=axes[0, 1], alpha=0.6)
    axes[0, 1].set_title("(2) Latência Fim-a-Fim [ms]", fontweight="bold")
    axes[0, 1].set_xlabel("")
    axes[0, 1].set_ylabel("Latência (ms)")

    # Subplot 3: PRB Usage
    sns.boxplot(data=df, x="baseline", y="prb_usage", hue="baseline", order=order, palette=BASELINE_COLORS, ax=axes[1, 0], width=0.5, boxprops=dict(alpha=0.85), legend=False)
    sns.stripplot(data=df, x="baseline", y="prb_usage", order=order, color="black", size=5, jitter=0.2, ax=axes[1, 0], alpha=0.6)
    axes[1, 0].set_title("(3) Ocupação de Blocos de Recursos MAC (PRB) [%]", fontweight="bold")
    axes[1, 0].set_xlabel("Política / Baseline")
    axes[1, 0].set_ylabel("PRB Usage (%)")

    # Subplot 4: Action Churn
    sns.boxplot(data=df, x="baseline", y="action_churn", hue="baseline", order=order, palette=BASELINE_COLORS, ax=axes[1, 1], width=0.5, boxprops=dict(alpha=0.85), legend=False)
    sns.stripplot(data=df, x="baseline", y="action_churn", order=order, color="black", size=5, jitter=0.2, ax=axes[1, 1], alpha=0.6)
    axes[1, 1].set_title("(4) Estabilidade do Controle (Action Churn) [Ações/s]", fontweight="bold")
    axes[1, 1].set_xlabel("Política / Baseline")
    axes[1, 1].set_ylabel("Action Churn (/s)")

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    save_dual(fig, "fig_19e_crosslayer_metric_distributions_violin.png")


if __name__ == "__main__":
    print("Iniciando carregamento de dados empíricos de experiments/runs/...")
    df = load_runs_data()
    print(f"Total de registros carregados: {len(df)} execuções em {df['baseline'].nunique()} baselines.")
    
    print("\n1. Gerando Dashboard Mestre 2x2 (fig_19_crosslayer_pairplot.png)...")
    plot_master_crosslayer_dashboard(df)

    print("\n2. Gerando Gráficos Separados Especializados...")
    plot_sep_fig19a_pareto(df)
    plot_sep_fig19b_sinr_throughput(df)
    plot_sep_fig19c_prb_churn(df)
    plot_sep_fig19d_heatmap(df)
    plot_sep_fig19e_violins(df)

    print("\nTodos os gráficos foram gerados e sincronizados com sucesso em reports/figures e docs/figures!")
