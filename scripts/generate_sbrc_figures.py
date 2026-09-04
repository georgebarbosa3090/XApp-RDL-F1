#!/usr/bin/env python3
"""
Gerador de Figuras Científicas de Arquitetura, Componentes e Resultados para Artigo SBRC (Tema Claro)
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Padrão: 300 DPI, fundo branco puro, paleta científica nítida (SBC/IEEE Light Style).
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Configuração global de fontes e estilo limpo
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
# 1. FIGURA ARQUITETURAL: Arquitetura da xApp RDL no Near-RT RIC (Tema Claro)
# =============================================================================
def generate_architecture_figure():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Fundo do Container Principal: Near-RT RIC
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

    # Setas das xApps para RMR
    for x in [22, 50, 78]:
        ax.annotate('', xy=(x, 69.2), xytext=(x, 74),
                    arrowprops=dict(facecolor='#4A5568', edgecolor='#4A5568', width=1.5, headwidth=6, shrink=0.05))

    # Core da xApp RDL
    rdl_box = patches.FancyBboxPatch((7, 21), 86, 41, boxstyle="round,pad=1.0",
                                     facecolor="#FFFFFF", edgecolor="#805AD5", linewidth=2.0)
    ax.add_patch(rdl_box)
    ax.text(9, 59.5, "xApp RDL (Resource and Decision Layer) — Motor de Mitigação H-RDL", fontsize=11.5, fontweight='bold', color="#553C9A")

    # Submódulo: Decision Window
    ax.add_patch(patches.FancyBboxPatch((9, 44), 18, 12, boxstyle="round,pad=0.5", facecolor="#FAF5FF", edgecolor="#9F7AEA", linewidth=1.2))
    ax.text(18, 52.5, "Decision Window", ha='center', fontsize=9.5, fontweight='bold', color="#6B46C1")
    ax.text(18, 47.5, "Buffer em Lote\nΔt = 200 ms", ha='center', fontsize=8.5, color="#553C9A")

    # Submódulo: PerceptionAgent
    ax.add_patch(patches.FancyBboxPatch((30, 44), 22, 12, boxstyle="round,pad=0.5", facecolor="#EBF8FF", edgecolor="#4299E1", linewidth=1.2))
    ax.text(41, 52.5, "PerceptionAgent", ha='center', fontsize=9.5, fontweight='bold', color="#2B6CB0")
    ax.text(41, 47.5, "Detecção Direta/Indireta\nGrafo de Dependência KPI", ha='center', fontsize=8.5, color="#2C5282")

    # Submódulo: ReasoningAgent
    ax.add_patch(patches.FancyBboxPatch((55, 44), 20, 12, boxstyle="round,pad=0.5", facecolor="#F0FFF4", edgecolor="#48BB78", linewidth=1.2))
    ax.text(65, 52.5, "ReasoningAgent", ha='center', fontsize=9.5, fontweight='bold', color="#276749")
    ax.text(65, 47.5, "Heurísticas TVS & EEVS\nPrioridade de Serviço", ha='center', fontsize=8.5, color="#22543D")

    # Submódulo: RefinementAgent / Safety Guards
    ax.add_patch(patches.FancyBboxPatch((78, 44), 13, 12, boxstyle="round,pad=0.5", facecolor="#FFF5F5", edgecolor="#F56565", linewidth=1.2))
    ax.text(84.5, 52.5, "Refinement", ha='center', fontsize=9, fontweight='bold', color="#C53030")
    ax.text(84.5, 47.5, "Safety Guards\nPtx / PRBs / Hyst", ha='center', fontsize=8, color="#9B2C2C")

    # Setas internas do Pipeline RDL
    ax.annotate('', xy=(30, 50), xytext=(27, 50), arrowprops=dict(facecolor='#805AD5', edgecolor='#805AD5', width=1.5, headwidth=5))
    ax.annotate('', xy=(55, 50), xytext=(52, 50), arrowprops=dict(facecolor='#805AD5', edgecolor='#805AD5', width=1.5, headwidth=5))
    ax.annotate('', xy=(78, 50), xytext=(75, 50), arrowprops=dict(facecolor='#805AD5', edgecolor='#805AD5', width=1.5, headwidth=5))

    # Módulos de Suporte: Shared Data Layer & ASN.1 Codecs
    ax.add_patch(patches.FancyBboxPatch((10, 24), 24, 15, boxstyle="round,pad=0.5", facecolor="#F7FAFC", edgecolor="#A0AEC0", linewidth=1.0))
    ax.text(22, 35, "Shared Data Layer (SDL)", ha='center', fontsize=9, fontweight='bold', color="#2D3748")
    ax.text(22, 29, "Redis DBAAS / Memória\nHistórico de Ações & Resoluções", ha='center', fontsize=8, color="#4A5568")

    ax.add_patch(patches.FancyBboxPatch((38, 24), 26, 15, boxstyle="round,pad=0.5", facecolor="#F7FAFC", edgecolor="#A0AEC0", linewidth=1.0))
    ax.text(51, 35, "Codecs O-RAN E2 (pycrate)", ha='center', fontsize=9, fontweight='bold', color="#2D3748")
    ax.text(51, 29, "E2SM-KPM v2.0 (Decoder)\nE2SM-RC v1.0 (APER Encoder)", ha='center', fontsize=8, color="#4A5568")

    ax.add_patch(patches.FancyBboxPatch((68, 24), 22, 15, boxstyle="round,pad=0.5", facecolor="#F7FAFC", edgecolor="#A0AEC0", linewidth=1.0))
    ax.text(79, 35, "Observabilidade", ha='center', fontsize=9, fontweight='bold', color="#2D3748")
    ax.text(79, 29, "FastAPI Health (:8080)\nPrometheus Metrics (:8081)", ha='center', fontsize=8, color="#4A5568")

    # Camada Inferior: Rede 5G NR / O-RAN E2 Nodes
    gnodeb_box = patches.FancyBboxPatch((4, 2), 92, 12, boxstyle="round,pad=0.8",
                                        facecolor="#E2E8F0", edgecolor="#2D3748", linewidth=1.8)
    ax.add_patch(gnodeb_box)
    ax.text(50, 10.5, "Infraestrutura de Acesso de Rádio (E2 Nodes / gNodeBs 5G NR)", ha='center', fontsize=11, fontweight='bold', color="#1A202C")
    ax.text(25, 5.5, "Macro gNB (Banda n78 3.5GHz)\nFatias URLLC + eMBB", ha='center', fontsize=8.5, color="#2D3748")
    ax.text(75, 5.5, "Micro gNB / Small Cell\nFatias eMBB + mMTC", ha='center', fontsize=8.5, color="#2D3748")

    # Conexão E2 (SCTP 36422)
    ax.annotate('', xy=(50, 14.5), xytext=(50, 21),
                arrowprops=dict(facecolor='#E53E3E', edgecolor='#E53E3E', width=2, headwidth=7))
    ax.text(52, 17.5, "Interface E2 (E2AP / SCTP :36422) — E2SM-KPM / E2SM-RC", fontsize=8.5, fontweight='bold', color="#C53030")

    save_fig(fig, "fig_arquitetura_rdl_sbrc.png")

# =============================================================================
# 2. FIGURA DE COMPONENTES E FLUXO DECISÓRIO (Tema Claro)
# =============================================================================
def generate_component_flow_figure():
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 96, "Fluxo Operacional de Arbitragem em Lote e Mitigação de Conflitos (H-RDL)", 
            ha='center', fontsize=12, fontweight='bold', color="#1A365D")

    steps = [
        ("Etapa 1: Ingestão em Lote", "Recepção de Propostas RMR\nAgrupamento no Buffer (200ms)\nKPM Metrics Indication", 5, "#EBF8FF", "#3182CE"),
        ("Etapa 2: Grafo & Percepção", "Cruzamento Par a Par\nDetecção Direta/Indireta\nIdentificação de KPI Cross-Impact", 28, "#FAF5FF", "#805AD5"),
        ("Etapa 3: Raciocínio TVS/EEVS", "Otimização Multiobjetivo\nURLLC > eMBB > mMTC\nPonderação de Utilidade", 51, "#F0FFF4", "#38A169"),
        ("Etapa 4: Safety Guards", "Clamping de Potência (≤23dBm)\nOrçamento PRB (≤100%)\nFiltro Anti Ping-Pong (≥1s)", 74, "#FFF5F5", "#E53E3E")
    ]

    for title, desc, x, bg, border in steps:
        ax.add_patch(patches.FancyBboxPatch((x, 40), 21, 48, boxstyle="round,pad=0.8", facecolor=bg, edgecolor=border, linewidth=1.5))
        ax.text(x + 10.5, 83, title, ha='center', fontsize=9.5, fontweight='bold', color=border)
        ax.text(x + 10.5, 60, desc, ha='center', fontsize=8.5, color="#2D3748", linespacing=1.4)

    # Setas entre etapas
    for x in [26, 49, 72]:
        ax.annotate('', xy=(x + 2, 64), xytext=(x - 1, 64), arrowprops=dict(facecolor='#4A5568', edgecolor='#4A5568', width=2, headwidth=6))

    # Saída Final: E2SM-RC Control Message
    ax.add_patch(patches.FancyBboxPatch((15, 10), 70, 20, boxstyle="round,pad=0.8", facecolor="#EDF2F7", edgecolor="#2B6CB0", linewidth=1.5))
    ax.text(50, 24, "Saída Determinística: E2SM-RC Control Message (APER ASN.1)", ha='center', fontsize=10.5, fontweight='bold', color="#2B6CB0")
    ax.text(50, 16, "Execução no E2 Node (gNodeB) em tempo sub-milissegundo com garantia estrita de SLA", ha='center', fontsize=9, color="#4A5568")

    # Seta para saída
    ax.annotate('', xy=(50, 31), xytext=(84.5, 40), arrowprops=dict(facecolor='#2B6CB0', edgecolor='#2B6CB0', width=1.5, headwidth=6))

    save_fig(fig, "fig_componentes_fluxo_decisao.png")

# =============================================================================
# 3. FIGURA DE TOPOLOGIA ESPACIAL ns-3 5G-LENA (Tema Claro)
# =============================================================================
def generate_topology_figure():
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=300)
    
    ax.set_xlim(-15, 215)
    ax.set_ylim(-15, 135)
    ax.set_facecolor('#FFFFFF')
    
    # Borda da área de simulação
    rect = patches.Rectangle((0, 0), 200, 120, linewidth=1.5, edgecolor='#A0AEC0', facecolor='#F7FAFC', linestyle='--')
    ax.add_patch(rect)
    ax.text(100, 122, "Área de Simulação ns-3 5G-LENA (200m × 120m)", ha='center', fontsize=10, fontweight='bold', color='#4A5568')

    # Macro gNB (gNodeB 1)
    ax.plot(60, 60, marker='^', markersize=14, color='#2B6CB0', markeredgecolor='#1A365D', markeredgewidth=1.5)
    circle1 = patches.Circle((60, 60), 55, color='#3182CE', alpha=0.12, linestyle=':')
    ax.add_patch(circle1)
    ax.text(60, 70, "Macro gNB 1\n(3.5 GHz n78, 100MHz)", ha='center', fontsize=8.5, fontweight='bold', color='#2B6CB0')

    # Micro gNB (gNodeB 2)
    ax.plot(140, 60, marker='^', markersize=14, color='#38A169', markeredgecolor='#22543D', markeredgewidth=1.5)
    circle2 = patches.Circle((140, 60), 45, color='#48BB78', alpha=0.12, linestyle=':')
    ax.add_patch(circle2)
    ax.text(140, 70, "Micro gNB 2\n(Green Cell, 20dBm)", ha='center', fontsize=8.5, fontweight='bold', color='#276749')

    # Conexão E2 / X2 Backhaul
    ax.plot([60, 140], [60, 60], color='#E53E3E', linestyle='-', linewidth=2, label='Xn / E2 Interface')
    ax.text(100, 62.5, "E2 Link (SCTP :36422)", ha='center', fontsize=8, fontweight='bold', color='#C53030')

    # Distribuição de UEs por fatias
    np.random.seed(42)
    # URLLC UEs (Vermelho)
    x_urllc = np.random.uniform(40, 80, 8)
    y_urllc = np.random.uniform(30, 80, 8)
    ax.scatter(x_urllc, y_urllc, c='#E53E3E', marker='o', s=50, edgecolors='#9B2C2C', label='UEs URLLC (5QI 82, SLA ≤ 5ms)', zorder=5)

    # eMBB UEs (Azul)
    x_embb = np.random.uniform(70, 130, 12)
    y_embb = np.random.uniform(20, 100, 12)
    ax.scatter(x_embb, y_embb, c='#3182CE', marker='s', s=45, edgecolors='#1A365D', label='UEs eMBB (5QI 9, Greedy Tput)', zorder=5)

    # mMTC UEs (Verde)
    x_mmtc = np.random.uniform(120, 170, 10)
    y_mmtc = np.random.uniform(30, 90, 10)
    ax.scatter(x_mmtc, y_mmtc, c='#38A169', marker='D', s=40, edgecolors='#22543D', label='UEs mMTC (5QI 79, IoT Sensor)', zorder=5)

    ax.set_xlabel("Distância no Eixo X (metros)", fontsize=9.5, fontweight='bold')
    ax.set_ylabel("Distância no Eixo Y (metros)", fontsize=9.5, fontweight='bold')
    ax.legend(loc='upper right', framealpha=0.95, fontsize=8.5)
    ax.grid(True, linestyle=':', alpha=0.5, color='#CBD5E0')

    save_fig(fig, "fig_topologia_cenarios_ns3.png")

# =============================================================================
# 4. FIGURA DE RESULTADOS CIENTÍFICOS MULTIDIMENSIONAIS (Tema Claro)
# =============================================================================
def generate_results_figure():
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 9), dpi=300)
    
    # Cores científicas claras
    c_base = '#CBD5E0'  # Cinza claro para baseline
    c_rdl = '#3182CE'   # Azul vibrante para Fase 1 RDL
    edge_base = '#718096'
    edge_rdl = '#1A365D'

    # (a) Latência URLLC (Mean, Median, P95, P99)
    labels = ['Média', 'Mediana', 'P95', 'P99']
    base_lat = [11.79, 0.0, 53.14, 139.41]
    rdl_lat = [2.85, 2.79, 3.08, 3.09]
    x = np.arange(len(labels))
    width = 0.35

    ax1.bar(x - width/2, base_lat, width, label='Baseline (Sem RDL)', color=c_base, edgecolor=edge_base, linewidth=1.2)
    ax1.bar(x + width/2, rdl_lat, width, label='Fase 1: H-RDL (Proposta)', color=c_rdl, edgecolor=edge_rdl, linewidth=1.2)
    ax1.axhline(y=5.0, color='#E53E3E', linestyle='--', linewidth=1.5, label='Limite de SLA (5 ms)')
    ax1.set_ylabel("Latência URLLC (ms)", fontsize=9.5, fontweight='bold')
    ax1.set_title("(a) Distribuição de Latência URLLC e SLA", fontsize=10.5, fontweight='bold', color='#1A365D')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.legend(fontsize=8.5)
    ax1.grid(True, linestyle=':', alpha=0.5)

    # (b) Taxa de Conflitos e Eficiência de Arbitragem
    categories = ['Conflitos Ocorridos', 'Conflitos Não Resolvidos', 'Violação de SLA (%)']
    base_conf = [34.67, 34.67, 29.17]
    rdl_conf = [30.67, 0.67, 0.0]
    x2 = np.arange(len(categories))

    ax2.bar(x2 - width/2, base_conf, width, label='Baseline', color=c_base, edgecolor=edge_base, linewidth=1.2)
    ax2.bar(x2 + width/2, rdl_conf, width, label='Fase 1: H-RDL', color='#38A169', edgecolor='#22543D', linewidth=1.2)
    ax2.set_ylabel("Percentual (%)", fontsize=9.5, fontweight='bold')
    ax2.set_title("(b) Conflitos entre xApps e Violações de SLA", fontsize=10.5, fontweight='bold', color='#1A365D')
    ax2.set_xticks(x2)
    ax2.set_xticklabels(categories, fontsize=8.5)
    ax2.legend(fontsize=8.5)
    ax2.grid(True, linestyle=':', alpha=0.5)

    # (c) Throughput Total Agregado (Mbps) e PDR (%)
    metrics_tput = ['Vazão Útil (Mbps / 10)', 'PDR (%)', 'Jain Fairness (×100)']
    base_tput = [15.65, 39.28, 14.14]
    rdl_tput = [111.12, 99.53, 91.64]
    x3 = np.arange(len(metrics_tput))

    ax3.bar(x3 - width/2, base_tput, width, label='Baseline', color=c_base, edgecolor=edge_base, linewidth=1.2)
    ax3.bar(x3 + width/2, rdl_tput, width, label='Fase 1: H-RDL', color='#805AD5', edgecolor='#44337A', linewidth=1.2)
    ax3.set_ylabel("Escore Normalizado", fontsize=9.5, fontweight='bold')
    ax3.set_title("(c) Desempenho de Rede, Confiabilidade e Equidade", fontsize=10.5, fontweight='bold', color='#1A365D')
    ax3.set_xticks(x3)
    ax3.set_xticklabels(metrics_tput, fontsize=8.5)
    ax3.legend(fontsize=8.5)
    ax3.grid(True, linestyle=':', alpha=0.5)

    # (d) Estabilidade de Handover e Eficiência Energética
    metrics_stab = ['Ping-Pong (ev/min)', 'Potência Média (dBm)', 'Eficiência Energ. (×10)']
    base_stab = [22.0, 39.01, 10.0]
    rdl_stab = [0.0, 33.89, 11.45]
    x4 = np.arange(len(metrics_stab))

    ax4.bar(x4 - width/2, base_stab, width, label='Baseline', color=c_base, edgecolor=edge_base, linewidth=1.2)
    ax4.bar(x4 + width/2, rdl_stab, width, label='Fase 1: H-RDL', color='#DD6B20', edgecolor='#7B341E', linewidth=1.2)
    ax4.set_ylabel("Valores / Taxas", fontsize=9.5, fontweight='bold')
    ax4.set_title("(d) Estabilidade de Mobilidade e Consumo Energético", fontsize=10.5, fontweight='bold', color='#1A365D')
    ax4.set_xticks(x4)
    ax4.set_xticklabels(metrics_stab, fontsize=8.5)
    ax4.legend(fontsize=8.5)
    ax4.grid(True, linestyle=':', alpha=0.5)

    plt.tight_layout()
    save_fig(fig, "fig_resultados_comparativos_sbrc.png")

if __name__ == "__main__":
    print("Iniciando gerador de figuras SBRC (Tema Claro)...")
    generate_architecture_figure()
    generate_component_flow_figure()
    generate_topology_figure()
    generate_results_figure()
    print("[SUCESSO] Todas as 4 figuras SBRC foram geradas com sucesso em alta resolução (300 DPI)!")
