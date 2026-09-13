#!/usr/bin/env python3
"""
Script de Geração do Diagrama de Fluxo Arquitetural do H-RDL.
Gera a figura pura de arquitetura de sistema docs/figures/01_arquitetura_e_modelagem/fig_fluxo_funcional_arquitetura_rdl.png.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BG_COLOR = '#FFFFFF'
BOX_BG = '#F8FAFC'
BOX_BORDER = '#1E3A8A'
TEXT_COLOR = '#0F172A'
SUBTEXT_COLOR = '#334155'
ACCENT_BLUE = '#1D4ED8'
ACCENT_GREEN = '#047857'
ACCENT_AMBER = '#B45309'
ACCENT_PURPLE = '#7E22CE'
ACCENT_ROSE = '#BE123C'

OUTPUT_DIR = os.path.join("docs", "figures", "01_arquitetura_e_modelagem")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_architectural_flow_fig():
    fig, ax = plt.subplots(figsize=(11, 6), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Fluxo Funcional da Arquitetura Middleware H-RDL (Resource & Decision Layer)", 
              fontsize=13.5, fontweight='bold', color=TEXT_COLOR, pad=15)

    # 1. RMR / E2 Receiver
    rect1 = patches.FancyBboxPatch((0.5, 2.2), 2.2, 1.8, boxstyle="round,pad=0.03", facecolor='#EFF6FF', edgecolor=ACCENT_BLUE, lw=2)
    ax.add_patch(rect1)
    ax.text(1.6, 3.4, "RMR Message Receiver", ha='center', fontweight='bold', fontsize=10, color=TEXT_COLOR)
    ax.text(1.6, 2.7, "RMR 12010 (KPM)\nRMR 20000 (TS)\nDecodificação APER", ha='center', fontsize=8.5, color=SUBTEXT_COLOR)

    # 2. Perception Agent
    rect2 = patches.FancyBboxPatch((3.2, 2.2), 2.2, 1.8, boxstyle="round,pad=0.03", facecolor='#ECFDF5', edgecolor=ACCENT_GREEN, lw=2)
    ax.add_patch(rect2)
    ax.text(4.3, 3.4, "Perception Agent", ha='center', fontweight='bold', fontsize=10, color=TEXT_COLOR)
    ax.text(4.3, 2.7, "Detecção de Colisão\nClassificação Direto/\nIndireto (ConflictSet)", ha='center', fontsize=8.5, color=SUBTEXT_COLOR)

    # 3. Reasoning Agent
    rect3 = patches.FancyBboxPatch((5.9, 2.2), 2.2, 1.8, boxstyle="round,pad=0.03", facecolor='#FEF3C7', edgecolor=ACCENT_AMBER, lw=2)
    ax.add_patch(rect3)
    ax.text(7.0, 3.4, "Reasoning Agent", ha='center', fontweight='bold', fontsize=10, color=TEXT_COLOR)
    ax.text(7.0, 2.7, "Otimização TVS/EEVS\nResolução Multiobjetivo\n(RDLDecision)", ha='center', fontsize=8.5, color=SUBTEXT_COLOR)

    # 4. Refinement Agent
    rect4 = patches.FancyBboxPatch((8.6, 2.2), 2.1, 1.8, boxstyle="round,pad=0.03", facecolor='#FFE4E6', edgecolor=ACCENT_ROSE, lw=2)
    ax.add_patch(rect4)
    ax.text(9.65, 3.4, "Refinement Agent", ha='center', fontweight='bold', fontsize=10, color=TEXT_COLOR)
    ax.text(9.65, 2.7, "Safety Guards L0-L3\nCooldown Histerese\nE2SM-RC Encoder", ha='center', fontsize=8.5, color=SUBTEXT_COLOR)

    # Setas de fluxo
    ax.annotate("", xy=(3.2, 3.1), xytext=(2.7, 3.1), arrowprops=dict(arrowstyle="->,head_width=0.4", lw=2, color=ACCENT_BLUE))
    ax.annotate("", xy=(5.9, 3.1), xytext=(5.4, 3.1), arrowprops=dict(arrowstyle="->,head_width=0.4", lw=2, color=ACCENT_GREEN))
    ax.annotate("", xy=(8.6, 3.1), xytext=(8.1, 3.1), arrowprops=dict(arrowstyle="->,head_width=0.4", lw=2, color=ACCENT_AMBER))

    # Detalhe de Malha Fechada
    ax.text(5.5, 0.7, "Malha Fechada Near-RT: Janela em Lote (200ms) | Transaction Tracking RTT | E2SM-KPM / E2SM-RC", 
            ha='center', fontsize=9, fontweight='bold', color=SUBTEXT_COLOR)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_fluxo_funcional_arquitetura_rdl.png"), dpi=300, facecolor=BG_COLOR)
    plt.close()

if __name__ == "__main__":
    generate_architectural_flow_fig()
    print("[OK] Figura funcional da arquitetura H-RDL salva com sucesso!")
