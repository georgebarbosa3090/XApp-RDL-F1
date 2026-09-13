#!/usr/bin/env python3
"""
Script de Geração de Diagramas Topológicos e Cenários S1 a S5 em Tema Claro (Publicação Científica).
Gera 6 figuras de alta resolução (300 DPI) em docs/figures/03_cenarios_espaciais/:
 1. fig_topologia_espacial_parametrizada.png
 2. fig_scenario_1_direct_prb_conflict.png
 3. fig_scenario_2_indirect_tvs_conflict.png
 4. fig_scenario_3_cross_layer_energy_qos.png
 5. fig_scenario_4_mobility_vs_energy.png
 6. fig_scenario_5_temporal_pingpong_hysteresis.png
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Estilo de Publicação em Tema Claro (Light Theme)
BG_COLOR = '#FFFFFF'        # Branco puro para publicação
BOX_BG = '#F8FAFC'          # Slate 50
BOX_BORDER = '#1E3A8A'      # Azul Marinho 900
TEXT_COLOR = '#0F172A'      # Slate 900
SUBTEXT_COLOR = '#334155'   # Slate 700

ACCENT_BLUE = '#1D4ED8'     # Blue 700
ACCENT_GREEN = '#047857'    # Emerald 700
ACCENT_AMBER = '#B45309'    # Amber 700
ACCENT_PURPLE = '#7E22CE'   # Purple 700
ACCENT_ROSE = '#BE123C'     # Rose 700
ACCENT_CYAN = '#0891B2'     # Cyan 700

OUTPUT_DIR = os.path.join("docs", "figures", "03_cenarios_espaciais")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def draw_box(ax, x, y, w, h, title, subtitle="", color=BOX_BORDER, fill=BOX_BG):
    """Desenha um bloco estilizado de componente com borda arredondada e texto em tema claro."""
    rect = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.03,rounding_size=0.08",
        linewidth=2,
        edgecolor=color,
        facecolor=fill,
        zorder=3
    )
    ax.add_patch(rect)
    ax.text(
        x + w / 2, y + h * 0.65 if subtitle else y + h * 0.5,
        title, ha='center', va='center',
        fontsize=10.5, fontweight='bold', color=TEXT_COLOR, zorder=4
    )
    if subtitle:
        ax.text(
            x + w / 2, y + h * 0.3,
            subtitle, ha='center', va='center',
            fontsize=8.5, color=SUBTEXT_COLOR, fontweight='medium', zorder=4
        )

def draw_arrow(ax, x1, y1, x2, y2, label="", color=ACCENT_BLUE, linestyle='-'):
    """Desenha uma seta indicadora de fluxo de mensagens/controle em tema claro."""
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", lw=2, color=color, ls=linestyle),
        zorder=2
    )
    if label:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        ax.text(
            mid_x, mid_y + 0.15, label, ha='center', va='bottom',
            fontsize=8.5, fontweight='bold', color=color,
            bbox=dict(boxstyle="square,pad=0.2", facecolor=BG_COLOR, edgecolor='none', alpha=0.9),
            zorder=5
        )

# -----------------------------------------------------------------------------

# 1. Topologia Espacial Parametrizada
# -----------------------------------------------------------------------------
def generate_topologia_espacial_fig():
    fig, ax = plt.subplots(figsize=(10, 8), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(-1, 11)
    ax.set_ylim(-1, 9)
    ax.set_aspect('equal')
    ax.axis('off')

    plt.title("Topologia Espacial Parametrizada da Rede O-RAN Multi-Célula / Multi-Slice", 
              fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=15)

    # Células / Cobertura de gNodeBs
    gnb1_center = (3.0, 5.0)
    gnb2_center = (7.0, 5.0)
    gnb3_center = (5.0, 2.0)

    # Círculos de Cobertura
    circle1 = patches.Circle(gnb1_center, radius=2.8, facecolor='#DBEAFE', edgecolor=ACCENT_BLUE, alpha=0.4, lw=2, ls='--')
    circle2 = patches.Circle(gnb2_center, radius=2.8, facecolor='#FEF3C7', edgecolor=ACCENT_AMBER, alpha=0.4, lw=2, ls='--')
    circle3 = patches.Circle(gnb3_center, radius=2.5, facecolor='#F3E8FF', edgecolor=ACCENT_PURPLE, alpha=0.4, lw=2, ls='--')

    ax.add_patch(circle1)
    ax.add_patch(circle2)
    ax.add_patch(circle3)

    # gNodeBs Icons/Nodes
    ax.scatter([gnb1_center[0]], [gnb1_center[1]], s=350, color=ACCENT_BLUE, marker='^', zorder=5, label="gNB_01 (Macro cell)")
    ax.scatter([gnb2_center[0]], [gnb2_center[1]], s=350, color=ACCENT_AMBER, marker='^', zorder=5, label="gNB_02 (Small cell)")
    ax.scatter([gnb3_center[0]], [gnb3_center[1]], s=350, color=ACCENT_PURPLE, marker='^', zorder=5, label="gNB_03 (Macro cell)")

    ax.text(gnb1_center[0], gnb1_center[1] + 0.4, "gNB_01\n(eMBB Slice)", ha='center', fontsize=9.5, fontweight='bold', color=ACCENT_BLUE)
    ax.text(gnb2_center[0], gnb2_center[1] + 0.4, "gNB_02\n(Energy Saver)", ha='center', fontsize=9.5, fontweight='bold', color=ACCENT_AMBER)
    ax.text(gnb3_center[0], gnb3_center[1] - 0.6, "gNB_03\n(URLLC Slice)", ha='center', fontsize=9.5, fontweight='bold', color=ACCENT_PURPLE)

    # User Equipments (UEs)
    ue_embb_x = [2.0, 2.5, 3.8, 3.2]
    ue_embb_y = [5.5, 4.2, 5.8, 6.2]
    ax.scatter(ue_embb_x, ue_embb_y, s=80, color=ACCENT_BLUE, marker='o', zorder=6, label="UE eMBB (>50 Mbps)")

    ue_urllc_x = [4.8, 5.2, 5.5, 4.2]
    ue_urllc_y = [2.5, 1.5, 2.8, 2.0]
    ax.scatter(ue_urllc_x, ue_urllc_y, s=80, color=ACCENT_PURPLE, marker='s', zorder=6, label="UE URLLC (<5 ms)")

    # UEs em Zona de Conflito de Cobertura / Handover
    ue_ho_x = [5.0, 5.2]
    ue_ho_y = [5.0, 4.6]
    ax.scatter(ue_ho_x, ue_ho_y, s=120, color=ACCENT_ROSE, marker='*', zorder=7, label="UE em Fronteira de Conflito")
    ax.text(5.1, 5.3, "Zona de Conflito\n(TS vs ES vs xSlice)", ha='center', fontsize=8.5, fontweight='bold', color=ACCENT_ROSE,
            bbox=dict(boxstyle="square,pad=0.2", facecolor='#FFF1F2', edgecolor=ACCENT_ROSE, alpha=0.9))

    # Conexões E2 ao Near-RT RIC
    ax.plot([3.0, 5.0], [5.0, 7.8], color=BOX_BORDER, ls=':', lw=1.5)
    ax.plot([7.0, 5.0], [5.0, 7.8], color=BOX_BORDER, ls=':', lw=1.5)
    ax.plot([5.0, 5.0], [2.0, 7.8], color=BOX_BORDER, ls=':', lw=1.5)

    # Near-RT RIC / H-RDL Box
    ric_box = patches.FancyBboxPatch((3.0, 7.4), 4.0, 1.2, boxstyle="round,pad=0.05", facecolor='#EFF6FF', edgecolor=BOX_BORDER, lw=2, zorder=8)
    ax.add_patch(ric_box)
    ax.text(5.0, 8.0, "O-RAN Near-RT RIC (H-RDL Middleware)", ha='center', fontsize=11, fontweight='bold', color=TEXT_COLOR, zorder=9)
    ax.text(5.0, 7.6, "Perception Agent | Reasoning Agent (TVS/EEVS) | Safety Guards", ha='center', fontsize=8.5, color=SUBTEXT_COLOR, zorder=9)

    ax.legend(loc='lower left', fontsize=8.5, frameon=True, facecolor='#F8FAFC', edgecolor='#CBD5E1')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_topologia_espacial_parametrizada.png"), dpi=300, facecolor=BG_COLOR)
    plt.close()

# -----------------------------------------------------------------------------
# 2. Scenario 1: Direct PRB Conflict
# -----------------------------------------------------------------------------
def generate_scenario_1_fig():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5), facecolor=BG_COLOR)
    fig.suptitle("Cenário S1: Conflito Direto de PRB em gNB_01 (Demanda > 100% Capacidade)", 
                 fontsize=14, fontweight='bold', color=TEXT_COLOR, y=0.98)

    # Painel 1: Demandas Sobrepostas
    ax1.set_facecolor(BG_COLOR)
    categories = ['xSlice Req', 'Energy Saver Req', 'Capacidade Total']
    values = [75.0, 30.0, 100.0]
    colors = [ACCENT_BLUE, ACCENT_AMBER, '#64748B']

    bars = ax1.bar(categories, values, color=colors, width=0.55, edgecolor=BOX_BORDER, lw=1.5)
    ax1.axhline(100.0, color=ACCENT_ROSE, linestyle='--', lw=2, label="Capacidade Máxima (100% PRB)")
    ax1.set_ylabel("Cota de PRB (%)", fontsize=10, fontweight='bold', color=TEXT_COLOR)
    ax1.set_ylim(0, 120)
    ax1.grid(axis='y', linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', fontsize=8.5)

    for bar in bars:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.0f}%", ha='center', va='bottom', fontweight='bold', color=TEXT_COLOR)

    ax1.set_title("(A) Solicitantes Concorrentes", fontsize=11, fontweight='bold', color=TEXT_COLOR)

    # Painel 2: Resolução pelo H-RDL
    ax2.set_facecolor(BG_COLOR)
    res_categories = ['xSlice Alocado', 'Energy Saver Alocado', 'PRB Total Utilizado']
    res_values = [75.0, 25.0, 100.0]
    res_colors = [ACCENT_GREEN, ACCENT_CYAN, '#1E293B']

    res_bars = ax2.bar(res_categories, res_values, color=res_colors, width=0.55, edgecolor=BOX_BORDER, lw=1.5)
    ax2.axhline(100.0, color=ACCENT_GREEN, linestyle='-', lw=2, label="Limite Seguro Restabelecido")
    ax2.set_ylabel("Cota Arbitrada (%)", fontsize=10, fontweight='bold', color=TEXT_COLOR)
    ax2.set_ylim(0, 120)
    ax2.grid(axis='y', linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right', fontsize=8.5)

    for bar in res_bars:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.0f}%", ha='center', va='bottom', fontweight='bold', color=TEXT_COLOR)

    ax2.set_title("(B) Resolução sem Violação pelo H-RDL", fontsize=11, fontweight='bold', color=TEXT_COLOR)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_scenario_1_direct_prb_conflict.png"), dpi=300, facecolor=BG_COLOR)
    plt.close()

# -----------------------------------------------------------------------------
# 3. Scenario 2: Indirect TVS Conflict
# -----------------------------------------------------------------------------
def generate_scenario_2_fig():
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S2: Conflito Indireto TVS (Throughput vs Slicing SLA)", 
              fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=15)

    # Blocos de xApps
    rect_xs = patches.FancyBboxPatch((0.8, 3.8), 2.8, 1.5, boxstyle="round,pad=0.03", facecolor='#F3E8FF', edgecolor=ACCENT_PURPLE, lw=2)
    rect_kpi = patches.FancyBboxPatch((0.8, 1.0), 2.8, 1.5, boxstyle="round,pad=0.03", facecolor='#ECFDF5', edgecolor=ACCENT_GREEN, lw=2)

    ax.add_patch(rect_xs)
    ax.add_patch(rect_kpi)

    ax.text(2.2, 4.7, "xSlice xApp", ha='center', fontweight='bold', fontsize=11, color=TEXT_COLOR)
    ax.text(2.2, 4.2, "Requisita PRB_QUOTA = 80%\npara eMBB Slice", ha='center', fontsize=8.5, color=SUBTEXT_COLOR)

    ax.text(2.2, 1.9, "KPIMON xApp", ha='center', fontweight='bold', fontsize=11, color=TEXT_COLOR)
    ax.text(2.2, 1.4, "Detecta Queda de Vazão\nem URLLC Slice", ha='center', fontsize=8.5, color=SUBTEXT_COLOR)

    # Bloco H-RDL Decision
    rdl_box = patches.FancyBboxPatch((4.5, 2.0), 4.8, 2.4, boxstyle="round,pad=0.05", facecolor='#EFF6FF', edgecolor=BOX_BORDER, lw=2)
    ax.add_patch(rdl_box)
    ax.text(6.9, 3.8, "Arbitragem de Conflito Indireto (H-RDL)", ha='center', fontweight='bold', fontsize=11, color=TEXT_COLOR)
    ax.text(6.9, 3.2, "• Interseção de Métricas: PRB_QUOTA & DRB.UEThpDl\n• Modelo de Raciocínio TVS (Throughput-Value Scaling)\n• Ajuste da cota eMBB para 60% preservando URLLC", 
            ha='center', fontsize=9, color=SUBTEXT_COLOR)

    # Setas
    ax.annotate("", xy=(4.5, 4.3), xytext=(3.6, 4.3), arrowprops=dict(arrowstyle="->", lw=2, color=ACCENT_PURPLE))
    ax.annotate("", xy=(4.5, 2.2), xytext=(3.6, 2.2), arrowprops=dict(arrowstyle="->", lw=2, color=ACCENT_GREEN))

    ax.text(4.05, 4.5, "PRB Req", fontsize=8.5, color=ACCENT_PURPLE, fontweight='bold')
    ax.text(4.05, 2.4, "SLA Alarm", fontsize=8.5, color=ACCENT_GREEN, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_scenario_2_indirect_tvs_conflict.png"), dpi=300, facecolor=BG_COLOR)
    plt.close()

# -----------------------------------------------------------------------------
# 4. Scenario 3: Cross-Layer Energy vs QoS
# -----------------------------------------------------------------------------
def generate_scenario_3_fig():
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    plt.title("Cenário S3: Multi-Métrica Cross-Layer (Economia de Energia vs SLA de QoS)", 
              fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=15)

    tx_power = np.linspace(-10, 23, 100)
    # Trade-off curves
    energy_savings = 100 - (tx_power + 10) * 2.8  # Economia % diminui com mais potência
    ue_throughput = 10 + (tx_power + 10) * 2.5    # Vazão aumenta com mais potência

    ax.plot(tx_power, energy_savings, color=ACCENT_AMBER, lw=2.5, label="Economia de Energia (%) [Energy Saver]")
    ax.plot(tx_power, ue_throughput, color=ACCENT_BLUE, lw=2.5, label="Vazão Média UE (Mbps) [xSlice SLA]")

    # Ponto de Equilíbrio Pareto
    pareto_x = 12.5
    pareto_y = 36.0
    ax.scatter([pareto_x], [pareto_y], s=180, color=ACCENT_ROSE, zorder=6, label="Ponto de Operação Pareto (H-RDL EEVS)")
    ax.axvline(pareto_x, color=ACCENT_ROSE, linestyle='--', lw=1.5)

    ax.text(pareto_x + 1, pareto_y + 5, f"P_opt = {pareto_x:.1f} dBm\nSLA Preservado & EE Optim", 
            fontsize=9, fontweight='bold', color=ACCENT_ROSE,
            bbox=dict(boxstyle="square,pad=0.3", facecolor='#FFF1F2', edgecolor=ACCENT_ROSE, alpha=0.9))

    ax.set_xlabel("Potência de Transmissão da gNB TX_POWER (dBm)", fontsize=10, fontweight='bold', color=TEXT_COLOR)
    ax.set_ylabel("Valor Relativo de Desempenho", fontsize=10, fontweight='bold', color=TEXT_COLOR)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='center left', fontsize=9.5)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_scenario_3_cross_layer_energy_qos.png"), dpi=300, facecolor=BG_COLOR)
    plt.close()

# -----------------------------------------------------------------------------
# 5. Scenario 4: Mobility (TS) vs Energy Saver
# -----------------------------------------------------------------------------
def generate_scenario_4_fig():
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S4: Mobilidade (Traffic Steering) vs Economia de Energia (Energy Saver)", 
              fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=15)

    # gNB 01 & gNB 02
    draw_box(ax, 0.8, 2.2, 2.8, 2.5, "gNB_01 (Célula Alvo)", "Energy Saver solicita TX_POWER = -10 dBm\n(Tentativa de Sono)", ACCENT_AMBER, '#FEF3C7')
    draw_box(ax, 6.4, 2.2, 2.8, 2.5, "gNB_02 (Célula Origem)", "Congestionada (Carga > 90%)\nSLA eMBB em risco", ACCENT_BLUE, '#EFF6FF')

    # Traffic Steering Action
    draw_arrow(ax, 6.4, 4.0, 3.6, 4.0, "Traffic Steering: HANDOVER (UE_101 -> gNB_01)", ACCENT_ROSE)

    # H-RDL Decision Box
    dec_box = patches.FancyBboxPatch((3.2, 0.5), 3.6, 1.2, boxstyle="round,pad=0.03", facecolor='#F0FDF4', edgecolor=ACCENT_GREEN, lw=2)
    ax.add_patch(dec_box)
    ax.text(5.0, 1.2, "Decisão de Arbitragem H-RDL", ha='center', fontweight='bold', fontsize=10, color=ACCENT_GREEN)
    ax.text(5.0, 0.8, "Prioriza Cobertura & Conexão:\nBloqueia Sono de gNB_01 / Mantém TX_POWER = 20 dBm", ha='center', fontsize=8.5, color=SUBTEXT_COLOR)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_scenario_4_mobility_vs_energy.png"), dpi=300, facecolor=BG_COLOR)
    plt.close()

# -----------------------------------------------------------------------------
# 6. Scenario 5: Temporal Ping-Pong Hysteresis
# -----------------------------------------------------------------------------
def generate_scenario_5_fig():
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    plt.title("Cenário S5: Histerese Temporal e Supressão de Oscilação (Ping-Pong Lock)", 
              fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=15)

    time_ms = np.linspace(0, 3000, 300)

    # Simulação de solicitação de Handover repetida
    ho_requests = np.zeros_like(time_ms)
    ho_requests[(time_ms >= 200) & (time_ms <= 300)] = 1.0
    ho_requests[(time_ms >= 500) & (time_ms <= 600)] = 1.0  # Tentativa rápida (ping-pong)
    ho_requests[(time_ms >= 2200) & (time_ms <= 2300)] = 1.0 # Tentativa após cooldown

    # Ações Executadas pelo H-RDL
    ho_executed = np.zeros_like(time_ms)
    ho_executed[(time_ms >= 200) & (time_ms <= 300)] = 1.0
    ho_executed[(time_ms >= 500) & (time_ms <= 600)] = 0.0  # Bloqueado por Cooldown Lock (< 1000ms)
    ho_executed[(time_ms >= 2200) & (time_ms <= 2300)] = 1.0 # Permitido após expirar janela

    ax.plot(time_ms, ho_requests + 0.05, color=ACCENT_AMBER, lw=2, ls='--', label="Solicitação de Handover (xApp TS)")
    ax.step(time_ms, ho_executed, color=ACCENT_GREEN, lw=2.5, where='post', label="Ação Autorizada pelo H-RDL")

    ax.axvspan(300, 1300, color='#FFE4E6', alpha=0.5, label="Janela de Cooldown Lock (1000ms)")
    ax.text(800, 0.5, "Ping-Pong Bloqueado\n(Frequência Excedida)", ha='center', fontsize=9, fontweight='bold', color=ACCENT_ROSE)

    ax.set_xlabel("Tempo de Simulação (ms)", fontsize=10, fontweight='bold', color=TEXT_COLOR)
    ax.set_ylabel("Estado da Ação (0 = Bloqueado, 1 = Executado)", fontsize=10, fontweight='bold', color=TEXT_COLOR)
    ax.set_ylim(-0.1, 1.3)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_scenario_5_temporal_pingpong_hysteresis.png"), dpi=300, facecolor=BG_COLOR)
    plt.close()

if __name__ == "__main__":
    print("[+] Gerando figuras topológicas dos Cenários S1 a S5 e Topologia Espacial (Tema Claro)...")
    generate_topologia_espacial_fig()
    generate_scenario_1_fig()
    generate_scenario_2_fig()
    generate_scenario_3_fig()
    generate_scenario_4_fig()
    generate_scenario_5_fig()
    print("[OK] 6 figuras salvas com sucesso em: docs/figures/03_cenarios_espaciais/")
