#!/usr/bin/env python3
"""
Gerador Completo de Figuras Científicas de Cenários, Arquitetura e Estatística Multi-Semente (Tema Claro)
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Padrão: 300 DPI, fundo branco puro, paleta científica nítida (SBC/IEEE Light Style).
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.0

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIRS = [
    os.path.join(BASE_DIR, "paper_sbrc", "figures"),
    os.path.join(BASE_DIR, "docs", "figures"),
    os.path.join(BASE_DIR, "experiments", "results")
]

for d in OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

def save_fig(fig, filename):
    for d in OUTPUT_DIRS:
        path = os.path.join(d, filename)
        fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"[OK] Figura salva: {filename}")

# =============================================================================
# 1. ARQUITETURA GERAL DA xAPP RDL NO NEAR-RT RIC (Tema Claro)
# =============================================================================
def generate_architecture_figure():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ric_box = patches.FancyBboxPatch((4, 18), 92, 78, boxstyle="round,pad=1.5",
                                     facecolor="#F8FAFC", edgecolor="#2B6CB0", linewidth=2.0)
    ax.add_patch(ric_box)
    ax.text(6, 93, "Near-RT RIC (RAN Intelligent Controller) — Namespace `ricxapp`", 
            fontsize=13, fontweight='bold', color="#1A365D")

    # Camada 1: 3 Reference xApps
    xapps_box = patches.FancyBboxPatch((7, 72), 86, 17, boxstyle="round,pad=0.8",
                                       facecolor="#EDF2F7", edgecolor="#4A5568", linestyle="--", linewidth=1.2)
    ax.add_patch(xapps_box)
    ax.text(9, 86.5, "Tríade de xApps Abertas de Referência (Produtoras de Propostas)", fontsize=11, fontweight='bold', color="#2D3748")

    # xApp 1: xSlice
    ax.add_patch(patches.FancyBboxPatch((9, 74), 26, 11, boxstyle="round,pad=0.5", facecolor="#EBF8FF", edgecolor="#3182CE", linewidth=1.5))
    ax.text(22, 82.5, "1. xSlice (peihaoY)", ha='center', fontsize=10, fontweight='bold', color="#2B6CB0")
    ax.text(22, 78.5, "QoS & Slicing (URLLC/eMBB)\nPRB_QUOTA = 80% (Prio: 90)", ha='center', fontsize=8.5, color="#2C5282")

    # xApp 2: Energy Saving
    ax.add_patch(patches.FancyBboxPatch((37, 74), 26, 11, boxstyle="round,pad=0.5", facecolor="#F0FFF4", edgecolor="#38A169", linewidth=1.5))
    ax.text(50, 82.5, "2. Energy Saving (Orange)", ha='center', fontsize=10, fontweight='bold', color="#276749")
    ax.text(50, 78.5, "Green RAN & Cell Sleep\nTX_POWER = 20 dBm (Prio: 65)", ha='center', fontsize=8.5, color="#22543D")

    # xApp 3: Traffic Steering
    ax.add_patch(patches.FancyBboxPatch((65, 74), 26, 11, boxstyle="round,pad=0.5", facecolor="#FEFCBF", edgecolor="#D69E2E", linewidth=1.5))
    ax.text(78, 82.5, "3. Traffic Steering (O-RAN SC)", ha='center', fontsize=10, fontweight='bold', color="#975A16")
    ax.text(78, 78.5, "Mobility & Load Balance\nHANDOVER (Prio: 80)", ha='center', fontsize=8.5, color="#744210")

    # Barramento RMR
    rmr_box = patches.Rectangle((7, 65.5), 86, 3.5, facecolor="#CBD5E0", edgecolor="#718096", linewidth=1.0)
    ax.add_patch(rmr_box)
    ax.text(50, 67.2, "Barramento RMR (RIC Message Router) — Sub-ms Message Bus", ha='center', fontsize=9.5, fontweight='bold', color="#1A202C")

    for x in [22, 50, 78]:
        ax.annotate('', xy=(x, 69.2), xytext=(x, 74),
                    arrowprops=dict(facecolor='#4A5568', edgecolor='#4A5568', width=1.5, headwidth=6, shrink=0.05))

    # Core da xApp RDL
    rdl_box = patches.FancyBboxPatch((7, 21), 86, 41, boxstyle="round,pad=1.0",
                                     facecolor="#FFFFFF", edgecolor="#805AD5", linewidth=2.0)
    ax.add_patch(rdl_box)
    ax.text(9, 59.5, "xApp RDL (Resource and Decision Layer) — Motor de Mitigação H-RDL Reforçado", fontsize=11.5, fontweight='bold', color="#553C9A")

    # Submódulo: Decision Window
    ax.add_patch(patches.FancyBboxPatch((9, 44), 17, 12, boxstyle="round,pad=0.5", facecolor="#FAF5FF", edgecolor="#9F7AEA", linewidth=1.2))
    ax.text(17.5, 52.5, "Decision Window", ha='center', fontsize=9.5, fontweight='bold', color="#6B46C1")
    ax.text(17.5, 47.5, "Buffer em Lote\nΔt = 200 ms", ha='center', fontsize=8.5, color="#553C9A")

    # Submódulo: PerceptionAgent
    ax.add_patch(patches.FancyBboxPatch((28, 44), 21, 12, boxstyle="round,pad=0.5", facecolor="#EBF8FF", edgecolor="#4299E1", linewidth=1.2))
    ax.text(38.5, 52.5, "PerceptionAgent", ha='center', fontsize=9.5, fontweight='bold', color="#2B6CB0")
    ax.text(38.5, 47.5, "Grafo de KPIs\nDetecção Par a Par", ha='center', fontsize=8.5, color="#2C5282")

    # Submódulo: ReasoningAgent
    ax.add_patch(patches.FancyBboxPatch((51, 44), 21, 12, boxstyle="round,pad=0.5", facecolor="#F0FFF4", edgecolor="#48BB78", linewidth=1.2))
    ax.text(61.5, 52.5, "ReasoningAgent", ha='center', fontsize=9.5, fontweight='bold', color="#276749")
    ax.text(61.5, 47.5, "Modelos 5G Calibrados\nHeurísticas TVS & EEVS", ha='center', fontsize=8.5, color="#22543D")

    # Submódulo: RefinementAgent & Pass-Through
    ax.add_patch(patches.FancyBboxPatch((74, 44), 17, 12, boxstyle="round,pad=0.5", facecolor="#FFF5F5", edgecolor="#F56565", linewidth=1.2))
    ax.text(82.5, 52.5, "Refinement & PT", ha='center', fontsize=9, fontweight='bold', color="#C53030")
    ax.text(82.5, 47.5, "Safety Guards\nPass-Through Limpo", ha='center', fontsize=8, color="#9B2C2C")

    # Setas internas
    ax.annotate('', xy=(28, 50), xytext=(26, 50), arrowprops=dict(facecolor='#805AD5', edgecolor='#805AD5', width=1.5, headwidth=5))
    ax.annotate('', xy=(51, 50), xytext=(49, 50), arrowprops=dict(facecolor='#805AD5', edgecolor='#805AD5', width=1.5, headwidth=5))
    ax.annotate('', xy=(74, 50), xytext=(72, 50), arrowprops=dict(facecolor='#805AD5', edgecolor='#805AD5', width=1.5, headwidth=5))

    # Suporte
    ax.add_patch(patches.FancyBboxPatch((10, 24), 24, 15, boxstyle="round,pad=0.5", facecolor="#F7FAFC", edgecolor="#A0AEC0", linewidth=1.0))
    ax.text(22, 35, "Shared Data Layer (SDL)", ha='center', fontsize=9, fontweight='bold', color="#2D3748")
    ax.text(22, 29, "Redis DBAAS Real\nHistórico & Resoluções", ha='center', fontsize=8, color="#4A5568")

    ax.add_patch(patches.FancyBboxPatch((38, 24), 26, 15, boxstyle="round,pad=0.5", facecolor="#F7FAFC", edgecolor="#A0AEC0", linewidth=1.0))
    ax.text(51, 35, "Codecs O-RAN E2", ha='center', fontsize=9, fontweight='bold', color="#2D3748")
    ax.text(51, 29, "E2SM-KPM v2.0 (Decoder)\nE2SM-RC v1.0 (APER Encoder)", ha='center', fontsize=8, color="#4A5568")

    ax.add_patch(patches.FancyBboxPatch((68, 24), 22, 15, boxstyle="round,pad=0.5", facecolor="#F7FAFC", edgecolor="#A0AEC0", linewidth=1.0))
    ax.text(79, 35, "ACK & Observabilidade", ha='center', fontsize=9, fontweight='bold', color="#2D3748")
    ax.text(79, 29, "Rastreamento de ACK/RTT\nFastAPI :8080 / Prom :8081", ha='center', fontsize=8, color="#4A5568")

    # Camada E2 Nodes
    gnodeb_box = patches.FancyBboxPatch((4, 2), 92, 12, boxstyle="round,pad=0.8",
                                        facecolor="#E2E8F0", edgecolor="#2D3748", linewidth=1.8)
    ax.add_patch(gnodeb_box)
    ax.text(50, 10.5, "Infraestrutura de Acesso de Rádio (E2 Nodes / gNodeBs 5G NR)", ha='center', fontsize=11, fontweight='bold', color="#1A202C")
    ax.text(25, 5.5, "Macro gNB (3.5 GHz n78)\nFatias URLLC + eMBB", ha='center', fontsize=8.5, color="#2D3748")
    ax.text(75, 5.5, "Micro gNB / Small Cell\nFatias eMBB + mMTC", ha='center', fontsize=8.5, color="#2D3748")

    ax.annotate('', xy=(50, 14.5), xytext=(50, 21),
                arrowprops=dict(facecolor='#E53E3E', edgecolor='#E53E3E', width=2, headwidth=7))
    ax.text(52, 17.5, "Interface E2 (E2AP / SCTP :36422) — E2SM-KPM / E2SM-RC", fontsize=8.5, fontweight='bold', color="#C53030")

    save_fig(fig, "fig_arquitetura_rdl_sbrc.png")

# =============================================================================
# 2. FLUXO DE COMPONENTES E PIPELINE DE PASS-THROUGH (Tema Claro)
# =============================================================================
def generate_decision_flow_figure():
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 95, "Pipeline de Decisão em Lote e Pass-Through Contínuo da xApp RDL",
            ha='center', fontsize=12, fontweight='bold', color="#1A365D")

    # Etapa 1: Ingestão de Propostas
    ax.add_patch(patches.FancyBboxPatch((4, 55), 18, 30, boxstyle="round,pad=0.6", facecolor="#EBF8FF", edgecolor="#3182CE", linewidth=1.5))
    ax.text(13, 80, "1. Ingestão RMR", ha='center', fontsize=10, fontweight='bold', color="#2B6CB0")
    ax.text(13, 72, "Propostas xApps:\n• xSlice (PRBs)\n• Energy (Ptx)\n• Traffic (HO)", ha='center', fontsize=8.5, color="#2C5282")
    ax.text(13, 58, "Janela Δt = 200 ms", ha='center', fontsize=8, fontweight='bold', color="#1A365D")

    # Seta para Buffer
    ax.annotate('', xy=(24, 70), xytext=(22, 70), arrowprops=dict(facecolor='#3182CE', edgecolor='#3182CE', width=1.5, headwidth=5))

    # Etapa 2: Segregação e Detecção de Conflitos
    ax.add_patch(patches.FancyBboxPatch((25, 55), 22, 30, boxstyle="round,pad=0.6", facecolor="#FAF5FF", edgecolor="#805AD5", linewidth=1.5))
    ax.text(36, 80, "2. PerceptionAgent", ha='center', fontsize=10, fontweight='bold', color="#6B46C1")
    ax.text(36, 72, "Detecção Par a Par:\n• Grafo de KPIs\n• Conflito Direto\n• Conflito Indireto", ha='center', fontsize=8.5, color="#553C9A")
    ax.text(36, 58, "Divisão do Lote", ha='center', fontsize=8, fontweight='bold', color="#44337A")

    # Ramo Superior: Ações em Conflito -> ReasoningAgent
    ax.annotate('', xy=(50, 78), xytext=(47, 78), arrowprops=dict(facecolor='#E53E3E', edgecolor='#E53E3E', width=1.5, headwidth=5))
    ax.text(48.5, 81, "Em Conflito", ha='center', fontsize=7.5, fontweight='bold', color="#E53E3E")

    ax.add_patch(patches.FancyBboxPatch((50, 65), 22, 26, boxstyle="round,pad=0.6", facecolor="#FFF5F5", edgecolor="#E53E3E", linewidth=1.5))
    ax.text(61, 85, "3A. ReasoningAgent", ha='center', fontsize=9.5, fontweight='bold', color="#C53030")
    ax.text(61, 78, "Otimização Combinatória:\n• Shannon + SINR Real\n• Fila M/G/1 Sigmoide\n• Earth Power Model\n• Heurísticas TVS/EEVS", ha='center', fontsize=7.8, color="#742A2A")

    # Ramo Inferior: Ações Limpas -> Pass-Through
    ax.annotate('', xy=(50, 40), xytext=(36, 55), arrowprops=dict(facecolor='#38A169', edgecolor='#38A169', width=1.5, headwidth=5))
    ax.text(41, 45, "Ações Limpas\n(Pass-Through)", ha='center', fontsize=7.5, fontweight='bold', color="#276749")

    ax.add_patch(patches.FancyBboxPatch((50, 26), 22, 24, boxstyle="round,pad=0.6", facecolor="#F0FFF4", edgecolor="#38A169", linewidth=1.5))
    ax.text(61, 44, "3B. Pass-Through", ha='center', fontsize=9.5, fontweight='bold', color="#276749")
    ax.text(61, 35, "Validação Direta:\n• Isenção de Contenda\n• Despacho Contínuo\n• Zero Atraso Buffer", ha='center', fontsize=7.8, color="#22543D")

    # Convergência para RefinementAgent & Safety Guards
    ax.annotate('', xy=(75, 78), xytext=(72, 78), arrowprops=dict(facecolor='#805AD5', edgecolor='#805AD5', width=1.5, headwidth=5))
    ax.annotate('', xy=(75, 40), xytext=(72, 40), arrowprops=dict(facecolor='#805AD5', edgecolor='#805AD5', width=1.5, headwidth=5))

    ax.add_patch(patches.FancyBboxPatch((75, 30), 21, 55, boxstyle="round,pad=0.6", facecolor="#F7FAFC", edgecolor="#4A5568", linewidth=1.8))
    ax.text(85.5, 80, "4. RefinementAgent", ha='center', fontsize=10, fontweight='bold', color="#2D3748")
    ax.text(85.5, 72, "Safety Guards:\n• Clamping de Potência\n  (-10 a 23 dBm)\n• Teto PRB ≤ 100%\n• Histerese de HO\n  (Δt ≥ 1000 ms)", ha='center', fontsize=8, color="#4A5568")
    ax.text(85.5, 48, "Codificação E2:\n• APER Encoder\n• E2SM-RC v1.0\n• RIC_CONTROL_REQ", ha='center', fontsize=8, fontweight='bold', color="#1A202C")
    ax.text(85.5, 34, "Rastreamento:\n• TX_ID Assíncrono\n• RTT E2 Medido", ha='center', fontsize=8, color="#2B6CB0")

    # Saída para E2 Nodes
    ax.annotate('', xy=(85.5, 12), xytext=(85.5, 30), arrowprops=dict(facecolor='#E53E3E', edgecolor='#E53E3E', width=2, headwidth=6))
    ax.text(85.5, 6, "E2 Nodes (gNodeBs)", ha='center', fontsize=9.5, fontweight='bold', color="#C53030")

    save_fig(fig, "fig_componentes_fluxo_decisao.png")

# =============================================================================
# 3. TOPOLOGIA ESPACIAL DOS CENÁRIOS NO ns-3 (Tema Claro)
# =============================================================================
def generate_ns3_topology_figure():
    fig, ax = plt.subplots(figsize=(11, 6.8), dpi=300)
    ax.set_xlim(-15, 215)
    ax.set_ylim(-10, 130)

    # Área de simulação
    scenario_box = patches.Rectangle((0, 0), 200, 120, fill=True, facecolor="#F8FAFC", edgecolor='#A0AEC0', linestyle='--', linewidth=1.5, label='Grid ns-3 (200m × 120m)')
    ax.add_patch(scenario_box)

    # Coordenadas das 2 gNodeBs
    gnb1_x, gnb1_y = 60.0, 60.0   # Macro gNB 1
    gnb2_x, gnb2_y = 140.0, 60.0  # Micro gNB 2

    # Coberturas
    c1 = plt.Circle((gnb1_x, gnb1_y), 65, color='#3182CE', alpha=0.12, label='Cobertura Macro gNB 1 (3.5 GHz n78, 100 MHz, 43 dBm)')
    c2 = plt.Circle((gnb2_x, gnb2_y), 65, color='#38A169', alpha=0.12, label='Cobertura Micro gNB 2 (3.5 GHz n78, 100 MHz, 30 dBm)')
    ax.add_patch(c1)
    ax.add_patch(c2)

    # Zona de Sobreposição / Contenção
    ici_zone = patches.Rectangle((75, 15), 50, 90, color='#E53E3E', alpha=0.10, linestyle=':', linewidth=1.5, label='Zona de Contenção de PRBs e Handover (Interferência ICI)')
    ax.add_patch(ici_zone)

    # gNodeBs
    ax.plot(gnb1_x, gnb1_y, marker='^', markersize=16, color='#1A365D', markeredgecolor='black', markeredgewidth=1.5, label='Macro gNodeB 1 (Altura 25m)')
    ax.text(gnb1_x, gnb1_y + 7.0, 'Macro gNodeB 1\n(X=60m, Y=60m)', ha='center', fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#EBF8FF', edgecolor='#3182CE'))

    ax.plot(gnb2_x, gnb2_y, marker='^', markersize=16, color='#22543D', markeredgecolor='black', markeredgewidth=1.5, label='Micro gNodeB 2 (Altura 25m)')
    ax.text(gnb2_x, gnb2_y + 7.0, 'Micro gNodeB 2\n(X=140m, Y=60m)', ha='center', fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#F0FFF4', edgecolor='#38A169'))

    # UEs determinísticos
    np.random.seed(101)
    urllc_x = np.random.uniform(78, 122, 10)
    urllc_y = np.random.uniform(25, 95, 10)
    ax.scatter(urllc_x, urllc_y, c='#E53E3E', s=65, marker='o', edgecolors='black', linewidth=1.0, zorder=5, label='10 UEs URLLC (5QI 82, SLA ≤ 5 ms)')

    embb_x = np.random.uniform(15, 75, 10)
    embb_y = np.random.uniform(15, 105, 10)
    ax.scatter(embb_x, embb_y, c='#3182CE', s=60, marker='s', edgecolors='black', linewidth=1.0, zorder=5, label='10 UEs eMBB (5QI 9, Fluxo Contínuo)')

    mmtc_x = np.random.uniform(125, 185, 10)
    mmtc_y = np.random.uniform(15, 105, 10)
    ax.scatter(mmtc_x, mmtc_y, c='#38A169', s=55, marker='^', edgecolors='black', linewidth=1.0, zorder=5, label='10 UEs mMTC (5QI 79, Tráfego Intermitente)')

    # SCTP E2 Indication
    ax.annotate('', xy=(100, 115), xytext=(100, 105), arrowprops=dict(arrowstyle="<->", color="#805AD5", lw=2, ls="--"))
    ax.text(100, 118, 'Interface E2 (SCTP :36422) ao Near-RT RIC', ha='center', fontsize=9.5, fontweight='bold', color='#553C9A',
            bbox=dict(boxstyle='square,pad=0.3', facecolor='#FAF5FF', edgecolor='#805AD5', lw=1.0))

    ax.set_title('Topologia Espacial 5G NR Parametrizada no ns-3 (5G-LENA):\n2 gNodeBs (Banda n78, 3.5 GHz, 100 MHz, mu=1) e 30 UEs Fatiados',
                 fontsize=11.5, fontweight='bold', pad=12, color="#1A365D")
    ax.set_xlabel('Coordenada Horizontal X (metros)', fontsize=9.5, fontweight='bold')
    ax.set_ylabel('Coordenada Vertical Y (metros)', fontsize=9.5, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower left', frameon=True, fontsize=8, ncol=2)

    save_fig(fig, "fig_topologia_cenarios_ns3.png")

# =============================================================================
# 4. CENÁRIO 1: TRADE-OFF ENERGY SAVING VS SLA URLLC (EEVS)
# =============================================================================
def generate_scenario_1_figure():
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 95, "Cenário 1: Conflito de Arbitragem EEVS (Energy Saving vs Garantia de SLA URLLC)",
            ha='center', fontsize=12, fontweight='bold', color="#1A365D")

    # Macro Cell (Esquerda)
    ax.add_patch(patches.FancyBboxPatch((8, 30), 38, 55, boxstyle="round,pad=1.0", facecolor="#EBF8FF", edgecolor="#3182CE", linewidth=1.8))
    ax.text(27, 80, "Macro gNodeB 1 (Área Central)", ha='center', fontsize=10.5, fontweight='bold', color="#2B6CB0")
    ax.text(27, 72, "Banda n78 (3.5 GHz), 100 MHz\nCarga Alta: 15 UEs Ativos", ha='center', fontsize=9, color="#2D3748")
    
    # Demanda xSlice
    ax.add_patch(patches.Rectangle((12, 48), 30, 18, facecolor="#FFFFFF", edgecolor="#3182CE", linestyle="--"))
    ax.text(27, 60, "xSlice Demanda:", ha='center', fontsize=9, fontweight='bold', color="#2B6CB0")
    ax.text(27, 53, "PRB_QUOTA = 80%\nPrioridade: 90 (URLLC)", ha='center', fontsize=8.5, color="#2D3748")
    
    ax.text(27, 36, "SLA Requerido: Latência ≤ 5 ms\nVazão Alvo: ≥ 25 Mbps", ha='center', fontsize=8.5, color="#C53030", fontweight='bold')

    # Micro Cell (Direita)
    ax.add_patch(patches.FancyBboxPatch((54, 30), 38, 55, boxstyle="round,pad=1.0", facecolor="#F0FFF4", edgecolor="#38A169", linewidth=1.8))
    ax.text(73, 80, "Micro gNodeB 2 (Small Cell)", ha='center', fontsize=10.5, fontweight='bold', color="#276749")
    ax.text(73, 72, "Baixa Carga / Sono Seletivo\n15 UEs Periféricos", ha='center', fontsize=9, color="#2D3748")

    # Demanda Energy Saving
    ax.add_patch(patches.Rectangle((58, 48), 30, 18, facecolor="#FFFFFF", edgecolor="#38A169", linestyle="--"))
    ax.text(73, 60, "Energy Saving Demanda:", ha='center', fontsize=9, fontweight='bold', color="#276749")
    ax.text(73, 53, "TX_POWER = 20 dBm\nPrioridade: 65 (Green)", ha='center', fontsize=8.5, color="#2D3748")

    ax.text(73, 36, "Alvo: -28% Consumo Elétrico\nHibernação de Portadora", ha='center', fontsize=8.5, color="#22543D", fontweight='bold')

    # Conflito Central e Arbitragem RDL
    ax.add_patch(patches.FancyBboxPatch((20, 5), 60, 18, boxstyle="round,pad=0.8", facecolor="#FAF5FF", edgecolor="#805AD5", linewidth=1.8))
    ax.text(50, 18, "Arbitragem Multiobjetivo da xApp RDL (Heurística EEVS)", ha='center', fontsize=10, fontweight='bold', color="#553C9A")
    ax.text(50, 10, "Decisão: Priorização incondicional de URLLC na Macro Cell + Corte de potência restrito apenas à Micro Cell sem UEs críticos.",
            ha='center', fontsize=8.5, color="#4A5568")

    save_fig(fig, "fig_cenario1_energy_vs_qos.png")

# =============================================================================
# 5. CENÁRIO 2: CONFLITO DE TRAFFIC STEERING VS SLICING QOS (TVS)
# =============================================================================
def generate_scenario_2_figure():
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 95, "Cenário 2: Conflito de Arbitragem TVS (Traffic Steering vs Fatiamento QoS)",
            ha='center', fontsize=12, fontweight='bold', color="#1A365D")

    # gNodeB 1 Origem
    ax.add_patch(patches.FancyBboxPatch((6, 32), 38, 52, boxstyle="round,pad=0.8", facecolor="#EBF8FF", edgecolor="#3182CE", linewidth=1.5))
    ax.text(25, 78, "gNodeB 1 (Origem)", ha='center', fontsize=10, fontweight='bold', color="#2B6CB0")
    ax.text(25, 71, "Carga: 80% (Saturada)\nFatia URLLC + eMBB", ha='center', fontsize=8.5, color="#2D3748")
    ax.text(25, 58, "TS xApp Solicita:\nHANDOVER para gNB 2\n(Prioridade: 80)", ha='center', fontsize=8.5, color="#975A16", fontweight='bold')
    ax.text(25, 42, "xSlice Alerta:\nMigração gera pico de atraso\nViolando SLA de 5 ms", ha='center', fontsize=8, color="#C53030")

    # gNodeB 2 Destino
    ax.add_patch(patches.FancyBboxPatch((56, 32), 38, 52, boxstyle="round,pad=0.8", facecolor="#F0FFF4", edgecolor="#38A169", linewidth=1.5))
    ax.text(75, 78, "gNodeB 2 (Destino)", ha='center', fontsize=10, fontweight='bold', color="#276749")
    ax.text(75, 71, "Carga: 35% (Disponível)\nFatia mMTC + eMBB", ha='center', fontsize=8.5, color="#2D3748")
    ax.text(75, 58, "TS xApp Tenta:\nRebalancear carga\nequalizando UEs", ha='center', fontsize=8.5, color="#276749")
    ax.text(75, 42, "Risco: Efeito Ping-Pong\n22 eventos/min sem controle", ha='center', fontsize=8, color="#C53030")

    # Seta de Handover com Bloqueio de Ping-Pong
    ax.annotate('', xy=(56, 58), xytext=(44, 58),
                arrowprops=dict(facecolor='#E53E3E', edgecolor='#E53E3E', width=2, headwidth=7))
    ax.text(50, 62, "Tentativa de Handover", ha='center', fontsize=8.5, fontweight='bold', color='#E53E3E')

    # Solução RDL
    ax.add_patch(patches.FancyBboxPatch((15, 6), 70, 20, boxstyle="round,pad=0.8", facecolor="#FAF5FF", edgecolor="#805AD5", linewidth=1.8))
    ax.text(50, 21, "Governança da xApp RDL (Heurística TVS + Safety Guards)", ha='center', fontsize=10, fontweight='bold', color="#553C9A")
    ax.text(50, 12, "1. Handover de UEs URLLC bloqueado para manter estabilidade do SLA.\n2. Handover de fluxos eMBB aprovado com histerese mínima de 1000 ms (Zero Ping-Pong).",
            ha='center', fontsize=8.5, color="#4A5568")

    save_fig(fig, "fig_cenario2_tvs_conflict.png")

# =============================================================================
# 6. GRÁFICO ESTATÍSTICO MULTI-SEMENTE COM BARRAS DE ERRO (IC 95%)
# =============================================================================
def generate_multiseed_errorbar_figure():
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 9), dpi=300)

    # Dados das 30 sementes independentes
    # (a) Latência URLLC (Mean e P99)
    labels1 = ['Latência Média', 'Latência P99 (Cauda)']
    base_mean1 = [11.66, 139.73]
    base_err1 = [0.61, 4.96]
    rdl_mean1 = [2.82, 3.09]
    rdl_err1 = [0.08, 0.10]
    x1 = np.arange(len(labels1))
    width = 0.35

    ax1.bar(x1 - width/2, base_mean1, width, yerr=base_err1, capsize=5, label='Baseline (Sem RDL)', color='#CBD5E0', edgecolor='#718096', linewidth=1.2)
    ax1.bar(x1 + width/2, rdl_mean1, width, yerr=rdl_err1, capsize=5, label='Fase 1: H-RDL Reforçada', color='#3182CE', edgecolor='#1A365D', linewidth=1.2)
    ax1.axhline(y=5.0, color='#E53E3E', linestyle='--', linewidth=1.5, label='Limite de SLA URLLC (5 ms)')
    ax1.set_ylabel("Latência URLLC (ms)", fontsize=9.5, fontweight='bold')
    ax1.set_title("(a) Latência URLLC (Média ± IC 95%, N = 30)", fontsize=10.5, fontweight='bold', color='#1A365D')
    ax1.set_xticks(x1)
    ax1.set_xticklabels(labels1)
    ax1.legend(fontsize=8.5)
    ax1.grid(True, linestyle=':', alpha=0.5)

    # (b) Conflitos e Violação de SLA
    labels2 = ['Taxa de Conflitos (%)', 'Violação de SLA (%)']
    base_mean2 = [34.81, 28.98]
    base_err2 = [1.05, 1.15]
    rdl_mean2 = [0.68, 0.00]
    rdl_err2 = [0.08, 0.00]
    x2 = np.arange(len(labels2))

    ax2.bar(x2 - width/2, base_mean2, width, yerr=base_err2, capsize=5, label='Baseline', color='#CBD5E0', edgecolor='#718096', linewidth=1.2)
    ax2.bar(x2 + width/2, rdl_mean2, width, yerr=rdl_err2, capsize=5, label='Fase 1: H-RDL Reforçada', color='#38A169', edgecolor='#22543D', linewidth=1.2)
    ax2.set_ylabel("Percentual (%)", fontsize=9.5, fontweight='bold')
    ax2.set_title("(b) Conflitos e Violação de SLA (Média ± IC 95%)", fontsize=10.5, fontweight='bold', color='#1A365D')
    ax2.set_xticks(x2)
    ax2.set_xticklabels(labels2)
    ax2.legend(fontsize=8.5)
    ax2.grid(True, linestyle=':', alpha=0.5)

    # (c) Vazão e PDR
    labels3 = ['Vazão Útil (Mbps / 10)', 'PDR (%)', 'Jain Fairness (×100)']
    base_mean3 = [15.64, 39.54, 14.20]
    base_err3 = [0.72, 2.13, 1.10]
    rdl_mean3 = [111.08, 99.53, 91.60]
    rdl_err3 = [1.57, 0.11, 0.70]
    x3 = np.arange(len(labels3))

    ax3.bar(x3 - width/2, base_mean3, width, yerr=base_err3, capsize=5, label='Baseline', color='#CBD5E0', edgecolor='#718096', linewidth=1.2)
    ax3.bar(x3 + width/2, rdl_mean3, width, yerr=rdl_err3, capsize=5, label='Fase 1: H-RDL Reforçada', color='#805AD5', edgecolor='#44337A', linewidth=1.2)
    ax3.set_ylabel("Valores Normalizados", fontsize=9.5, fontweight='bold')
    ax3.set_title("(c) Desempenho e Equidade (Média ± IC 95%)", fontsize=10.5, fontweight='bold', color='#1A365D')
    ax3.set_xticks(x3)
    ax3.set_xticklabels(labels3)
    ax3.legend(fontsize=8.5)
    ax3.grid(True, linestyle=':', alpha=0.5)

    # (d) Ping-Pong e Potência
    labels4 = ['Ping-Pong (ev/min)', 'Potência Média (dBm)', 'Tempo Decisão RDL (ms)']
    base_mean4 = [21.93, 39.01, 0.0]
    base_err4 = [1.47, 0.39, 0.0]
    rdl_mean4 = [0.00, 33.89, 14.20]
    rdl_err4 = [0.00, 0.28, 0.47]
    x4 = np.arange(len(labels4))

    ax4.bar(x4 - width/2, base_mean4, width, yerr=base_err4, capsize=5, label='Baseline', color='#CBD5E0', edgecolor='#718096', linewidth=1.2)
    ax4.bar(x4 + width/2, rdl_mean4, width, yerr=rdl_err4, capsize=5, label='Fase 1: H-RDL Reforçada', color='#DD6B20', edgecolor='#7B341E', linewidth=1.2)
    ax4.set_ylabel("Métricas Operacionais", fontsize=9.5, fontweight='bold')
    ax4.set_title("(d) Estabilidade e Eficiência (Média ± IC 95%)", fontsize=10.5, fontweight='bold', color='#1A365D')
    ax4.set_xticks(x4)
    ax4.set_xticklabels(labels4)
    ax4.legend(fontsize=8.5)
    ax4.grid(True, linestyle=':', alpha=0.5)

    plt.tight_layout()
    save_fig(fig, "fig_estatistica_multi_semente_ic95.png")

if __name__ == "__main__":
    print("Gerando conjunto completo de figuras em tema claro (300 DPI)...")
    generate_architecture_figure()
    generate_decision_flow_figure()
    generate_ns3_topology_figure()
    generate_scenario_1_figure()
    generate_scenario_2_figure()
    generate_multiseed_errorbar_figure()
    print("[SUCESSO] Todas as figuras foram geradas com sucesso!")
