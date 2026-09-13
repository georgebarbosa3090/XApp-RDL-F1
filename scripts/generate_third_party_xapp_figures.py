#!/usr/bin/env python3
"""
Script de Geração de Diagramas e Figuras de Arquitetura em Tema Claro (Publicação Científica).
Gera 5 figuras gráficas de alta resolução (300 DPI) em docs/figures/02_cenarios_terceiros/:
 1. fig_traffic_steering_architecture.png
 2. fig_kpimon_architecture.png
 3. fig_qos_xslice_architecture.png
 4. fig_energy_saving_architecture.png
 5. fig_cenarios_xapps_terceiros_interacao.png
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configurar estilo claro (Light Theme) para publicação científica
BG_COLOR = '#FFFFFF'        # Branco puro para impressão/dissertação
BOX_BG = '#F8FAFC'          # Slate 50 leve
BOX_BORDER = '#1E3A8A'      # Azul Marinho 900
TEXT_COLOR = '#0F172A'      # Slate 900
SUBTEXT_COLOR = '#334155'   # Slate 700

ACCENT_BLUE = '#1D4ED8'     # Blue 700
ACCENT_GREEN = '#047857'    # Emerald 700
ACCENT_AMBER = '#B45309'    # Amber 700
ACCENT_PURPLE = '#7E22CE'   # Purple 700
ACCENT_ROSE = '#BE123C'     # Rose 700

OUTPUT_DIR = os.path.join("docs", "figures", "02_cenarios_terceiros")
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
    
    # Título do bloco
    ax.text(
        x + w / 2, y + h * 0.65 if subtitle else y + h * 0.5,
        title,
        ha='center', va='center',
        fontsize=11, fontweight='bold', color=TEXT_COLOR,
        zorder=4
    )
    # Subtítulo (opcional)
    if subtitle:
        ax.text(
            x + w / 2, y + h * 0.3,
            subtitle,
            ha='center', va='center',
            fontsize=8.5, color=SUBTEXT_COLOR, fontweight='medium',
            zorder=4
        )

def draw_arrow(ax, x1, y1, x2, y2, label="", color=ACCENT_BLUE, linestyle='-'):
    """Desenha uma seta indicadora de fluxo de mensagens/controle em tema claro."""
    ax.annotate(
        "",
        xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->,head_width=0.4,head_length=0.6",
            lw=2, color=color, ls=linestyle
        ),
        zorder=2
    )
    if label:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        ax.text(
            mid_x, mid_y + 0.15,
            label,
            ha='center', va='bottom',
            fontsize=8.5, fontweight='bold', color=color,
            bbox=dict(boxstyle="square,pad=0.2", facecolor=BG_COLOR, edgecolor='none', alpha=0.9),
            zorder=5
        )

# -----------------------------------------------------------------------------
# 1. Traffic Steering Architecture (Light Theme)
# -----------------------------------------------------------------------------
def generate_traffic_steering_fig():
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Traffic Steering xApp Architecture (ORAN_SC_OFFICIAL - ric-app-ts)", 
              fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=15)

    # Componentes
    draw_box(ax, 0.5, 4.2, 2.5, 1.2, "A1 Policy Consumer", "Policies: TS Target & SLA", ACCENT_PURPLE, '#F3E8FF')
    draw_box(ax, 0.5, 1.0, 2.5, 1.2, "E2 KPM Subscriber", "RMR 12010 (KPM Indication)", ACCENT_GREEN, '#ECFDF5')
    draw_box(ax, 4.0, 2.5, 2.6, 1.5, "Traffic Steering Engine", "QoE Predictor & HO Logic", ACCENT_AMBER, '#FEF3C7')
    draw_box(ax, 7.5, 2.5, 2.0, 1.5, "E2 RC Controller", "HANDOVER Control (Msg 20000)", ACCENT_ROSE, '#FFE4E6')

    # Setas
    draw_arrow(ax, 3.0, 4.8, 4.0, 3.7, "A1 Policies", ACCENT_PURPLE)
    draw_arrow(ax, 3.0, 1.6, 4.0, 2.8, "KPI Metrics (RRC/PRB)", ACCENT_GREEN)
    draw_arrow(ax, 6.6, 3.25, 7.5, 3.25, "HO Decision", ACCENT_ROSE)

    # Detalhe técnico de protocolo
    ax.text(5.0, 0.5, "Protocols: RMR Msg 20000 (TS_UE_LIST) | E2SM-KPM v3 | E2SM-RC v2 (Handover)", 
            ha='center', fontsize=9.5, fontweight='bold', color=SUBTEXT_COLOR)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_traffic_steering_architecture.png"), dpi=300, facecolor=BG_COLOR)
    plt.close()

# -----------------------------------------------------------------------------
# 2. KPIMON Architecture (Light Theme)
# -----------------------------------------------------------------------------
def generate_kpimon_fig():
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("KPIMON xApp Architecture (ORAN_SC_OFFICIAL - ric-app-kpimon)", 
              fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=15)

    draw_box(ax, 0.5, 2.5, 2.3, 1.5, "E2 Node (gNB / DU)", "E2SM-KPM v3 Metrics", BOX_BORDER, '#EFF6FF')
    draw_box(ax, 3.8, 4.0, 2.6, 1.2, "RMR Indication Handler", "Msg 12010 RIC_INDICATION", ACCENT_GREEN, '#ECFDF5')
    draw_box(ax, 3.8, 1.0, 2.6, 1.2, "KPM Subscription Mgr", "Periodic Reports (10-100ms)", ACCENT_PURPLE, '#F3E8FF')
    draw_box(ax, 7.3, 2.5, 2.2, 1.5, "Prometheus / TS Store", "DRB.UEThpDl, RRU.PrbTot", ACCENT_AMBER, '#FEF3C7')

    draw_arrow(ax, 2.8, 3.5, 3.8, 4.6, "E2 KPM Stream", ACCENT_GREEN)
    draw_arrow(ax, 3.8, 1.6, 2.8, 2.8, "Sub Request", ACCENT_PURPLE)
    draw_arrow(ax, 6.4, 4.6, 7.3, 3.5, "Metrics Telemetry", ACCENT_AMBER)

    ax.text(5.0, 0.5, "Role: Passive Telemetry Exporter | E2SM-KPM v3 Format | Zero Direct E2 Control", 
            ha='center', fontsize=9.5, fontweight='bold', color=SUBTEXT_COLOR)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_kpimon_architecture.png"), dpi=300, facecolor=BG_COLOR)
    plt.close()

# -----------------------------------------------------------------------------
# 3. xSlice Architecture (Light Theme)
# -----------------------------------------------------------------------------
def generate_qos_xslice_fig():
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("xSlice QoS Slicing xApp Architecture (ACADEMIC_REIMPLEMENTATION - Yan et al., 2025)", 
              fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=15)

    draw_box(ax, 0.5, 2.5, 2.4, 1.5, "Slice SLA Monitor", "eMBB & URLLC KPIs", ACCENT_GREEN, '#ECFDF5')
    draw_box(ax, 3.9, 2.5, 2.6, 1.5, "Dynamic PRB Allocator", "PRB_QUOTA Optimization", ACCENT_AMBER, '#FEF3C7')
    draw_box(ax, 7.3, 2.5, 2.3, 1.5, "E2SM-RC Command", "PRB_QUOTA Control (0-100%)", ACCENT_ROSE, '#FFE4E6')

    draw_arrow(ax, 2.9, 3.25, 3.9, 3.25, "SLA Deficit", ACCENT_GREEN)
    draw_arrow(ax, 6.5, 3.25, 7.3, 3.25, "Allocation Cmd", ACCENT_ROSE)

    ax.text(5.0, 0.5, "Target: Guaranteed eMBB >50Mbps & URLLC <5ms | Controlled Parameter: PRB_QUOTA | Priority: 70", 
            ha='center', fontsize=9.5, fontweight='bold', color=SUBTEXT_COLOR)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_qos_xslice_architecture.png"), dpi=300, facecolor=BG_COLOR)
    plt.close()

# -----------------------------------------------------------------------------
# 4. Energy Saving Architecture (Light Theme)
# -----------------------------------------------------------------------------
def generate_energy_saving_fig():
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Energy Saving xApp Architecture (LITERATURE_INSPIRED - Wadud et al., 2024)", 
              fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=15)

    draw_box(ax, 0.5, 2.5, 2.4, 1.5, "Load & Traffic Analyzer", "Low Load Detection (<20%)", ACCENT_GREEN, '#ECFDF5')
    draw_box(ax, 3.9, 2.5, 2.6, 1.5, "Power & Sleep Manager", "Micro-Sleep & TX_POWER", ACCENT_PURPLE, '#F3E8FF')
    draw_box(ax, 7.3, 2.5, 2.3, 1.5, "E2SM-RC Power Controller", "TX_POWER (-10 to 23 dBm)", ACCENT_ROSE, '#FFE4E6')

    draw_arrow(ax, 2.9, 3.25, 3.9, 3.25, "Low Traffic Flag", ACCENT_GREEN)
    draw_arrow(ax, 6.5, 3.25, 7.3, 3.25, "Power Scaling", ACCENT_ROSE)

    ax.text(5.0, 0.5, "Objective: Reduce Base Station Power Consumption | Controlled Parameter: TX_POWER | Priority: 40-60", 
            ha='center', fontsize=9.5, fontweight='bold', color=SUBTEXT_COLOR)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_energy_saving_architecture.png"), dpi=300, facecolor=BG_COLOR)
    plt.close()

# -----------------------------------------------------------------------------
# 5. Third-Party xApps Interaction & H-RDL Conflict Scenario (Light Theme)
# -----------------------------------------------------------------------------
def generate_xapps_interaction_fig():
    fig, ax = plt.subplots(figsize=(12, 7.5), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    plt.title("Cenário de Interação das 4 xApps de Terceiros e Intercepção pelo Middleware H-RDL", 
              fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=15)

    # Bloco superior: 4 xApps de Terceiros
    draw_box(ax, 0.5, 5.3, 2.4, 1.4, "Traffic Steering", "HANDOVER / gNB_01\n(ORAN_SC_OFFICIAL)", ACCENT_AMBER, '#FEF3C7')
    draw_box(ax, 3.3, 5.3, 2.4, 1.4, "KPIMON Telemetry", "KPM Indication Listener\n(ORAN_SC_OFFICIAL)", ACCENT_GREEN, '#ECFDF5')
    draw_box(ax, 6.1, 5.3, 2.4, 1.4, "xSlice QoS Slicing", "PRB_QUOTA = 80%\n(ACADEMIC_REIMPL)", ACCENT_PURPLE, '#F3E8FF')
    draw_box(ax, 8.9, 5.3, 2.6, 1.4, "Energy Saving", "TX_POWER = -10dBm\n(LITERATURE_INSPIRED)", ACCENT_ROSE, '#FFE4E6')

    # Camada Intermediária: Middleware H-RDL
    draw_box(ax, 2.2, 2.5, 7.6, 1.9, "Middleware H-RDL (Resource & Decision Layer)", 
             "Perception Agent (Conflict Detection) --> Reasoning Agent (TVS/EEVS) --> Refinement Agent (Safety Guards)", 
             color=BOX_BORDER, fill='#EFF6FF')

    # Camada Inferior: RAN / E2 Nodes
    draw_box(ax, 3.2, 0.4, 5.6, 1.2, "O-RAN Near-RT RIC & E2 Nodes (ns-3 / 5G-LENA / NORI)", 
             "E2SM-KPM (Telemetria) | E2SM-RC (Controle Sem Colisão)", ACCENT_GREEN, '#F0FDF4')

    # Setas das xApps para H-RDL
    draw_arrow(ax, 1.7, 5.3, 3.5, 4.4, "HANDOVER", ACCENT_AMBER)
    draw_arrow(ax, 4.5, 5.3, 4.5, 4.4, "KPM Sub", ACCENT_GREEN)
    draw_arrow(ax, 7.3, 5.3, 6.5, 4.4, "PRB Req", ACCENT_PURPLE)
    draw_arrow(ax, 10.2, 5.3, 8.5, 4.4, "Power Reduction", ACCENT_ROSE)

    # Seta H-RDL para E2
    draw_arrow(ax, 6.0, 2.5, 6.0, 1.6, "Ações Arbitradas (Zero Colisão)", ACCENT_BLUE)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_cenarios_xapps_terceiros_interacao.png"), dpi=300, facecolor=BG_COLOR)
    plt.close()

if __name__ == "__main__":
    print("[+] Gerando figuras de arquitetura em TEMA CLARO (Publicação)...")
    generate_traffic_steering_fig()
    generate_kpimon_fig()
    generate_qos_xslice_fig()
    generate_energy_saving_fig()
    generate_xapps_interaction_fig()
    print("[OK] 5 figuras salvas com sucesso em: docs/figures/02_cenarios_terceiros/")
