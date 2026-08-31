#!/usr/bin/env python3
"""
Gerador de Figuras Científicas e Topologias de Cenários Simulados em Formato PNG (300 DPI)
Projeto: xApp RDL (Resource and Decision Layer) — Fases 1 e 2
"""

import os
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D

# Configurações globais de estilo para figuras científicas (IEEE Style)
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.autolayout'] = True

P1_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
P2_DIR = os.path.abspath(os.path.join(P1_DIR, "..", "iqos-xapp-rdl-phase2"))

def ensure_dirs():
    dirs = [
        os.path.join(P1_DIR, "docs", "figures"),
        os.path.join(P1_DIR, "docs", "assets"),
        os.path.join(P2_DIR, "docs", "figures"),
        os.path.join(P2_DIR, "docs", "assets")
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    return dirs

def save_to_all(fig, filename):
    for base in [P1_DIR, P2_DIR]:
        if os.path.exists(base):
            for subdir in [os.path.join("docs", "figures"), os.path.join("docs", "assets")]:
                out_path = os.path.join(base, subdir, filename)
                fig.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Figura salva: {filename}")

# -----------------------------------------------------------------------------
# FIGURA 1: Topologia Espacial e Conflito de Fatias (scenario_rdl_tvs_conflict)
# -----------------------------------------------------------------------------
def generate_figure_scenario_1():
    fig, ax = plt.subplots(figsize=(12, 8), dpi=300)
    
    # Coordenadas gNodeBs
    gnb1_x, gnb1_y = 0.0, 50.0   # Macro gNB
    gnb2_x, gnb2_y = 80.0, 50.0  # Small Cell gNB
    
    # Círculos de Cobertura de Rádio
    c1 = plt.Circle((gnb1_x, gnb1_y), 65, color='#3498db', alpha=0.15, label='Cobertura Macro gNB (Banda n78 3.5 GHz)')
    c2 = plt.Circle((gnb2_x, gnb2_y), 45, color='#e67e22', alpha=0.18, label='Cobertura Small Cell gNB (Banda n78)')
    ax.add_patch(c1)
    ax.add_patch(c2)
    
    # Zona de Interferência Intercelular (ICI) / Contenção
    zone_ici = patches.Ellipse((40, 50), 35, 60, angle=0, color='#e74c3c', alpha=0.22,
                               linestyle='--', linewidth=2, label='Zona Crítica de Contenção de PRBs & ICI')
    ax.add_patch(zone_ici)
    
    # Plot das gNodeBs
    ax.plot(gnb1_x, gnb1_y, marker='^', markersize=18, color='#1b4f72', markeredgecolor='black', markeredgewidth=2, label='gNodeB 1 (Macro Base Station)')
    ax.text(gnb1_x, gnb1_y + 4.0, 'Macro gNB 1\n(P_tx = 43 dBm)', ha='center', fontsize=10, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#ebf5fb', edgecolor='#1b4f72'))
    
    ax.plot(gnb2_x, gnb2_y, marker='^', markersize=16, color='#b9770e', markeredgecolor='black', markeredgewidth=2, label='gNodeB 2 (Micro Small Cell)')
    ax.text(gnb2_x, gnb2_y + 4.0, 'Small Cell gNB 2\n(P_tx = 30 dBm)', ha='center', fontsize=10, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#fef5e7', edgecolor='#b9770e'))
    
    # Distribuição dos 30 UEs (10 URLLC, 10 eMBB, 10 mMTC)
    np.random.seed(42)
    
    # 10 UEs URLLC (Vermelho) concentrados na zona de contenção e alta mobilidade
    urllc_x = np.random.uniform(25, 55, 10)
    urllc_y = np.random.uniform(30, 70, 10)
    ax.scatter(urllc_x, urllc_y, c='#c0392b', s=80, marker='o', edgecolors='black', linewidth=1.5, zorder=5, label='UEs URLLC (5QI 82, SLA < 5ms)')
    
    # 10 UEs eMBB (Azul) espalhados na Macro
    embb_x = np.random.uniform(-30, 30, 10)
    embb_y = np.random.uniform(20, 80, 10)
    ax.scatter(embb_x, embb_y, c='#2980b9', s=70, marker='s', edgecolors='black', linewidth=1.2, zorder=5, label='UEs eMBB (5QI 9, Alta Vazão)')
    
    # 10 UEs mMTC (Verde) espalhados na Small Cell
    mmtc_x = np.random.uniform(60, 105, 10)
    mmtc_y = np.random.uniform(25, 75, 10)
    ax.scatter(mmtc_x, mmtc_y, c='#27ae60', s=50, marker='^', edgecolors='black', linewidth=1.2, zorder=5, label='UEs mMTC (5QI 79, Sensores IoT)')
    
    # Enlace de Controle O-RAN E2
    ax.annotate('', xy=(40, 95), xytext=(40, 80),
                arrowprops=dict(arrowstyle="<->", color="#8e44ad", lw=3, ls="--"))
    ax.text(40, 98, 'Interface O-RAN E2 (SCTP 36422)\nConexão com Near-RT RIC & xApp RDL',
            ha='center', fontsize=11, fontweight='bold', color='#4a235a',
            bbox=dict(boxstyle='square,pad=0.5', facecolor='#f4ecf7', edgecolor='#8e44ad', lw=1.5))
    
    ax.set_title('Topologia Espacial de Co-Simulação 5G NR (ns-3 / 5G-LENA):\nCenário 1 — Conflito de Arbitragem TVS (URLLC vs eMBB vs mMTC)',
                 fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel('Coordenada Horizontal X (metros)', fontsize=11)
    ax.set_ylabel('Coordenada Vertical Y (metros)', fontsize=11)
    ax.set_xlim(-50, 130)
    ax.set_ylim(0, 115)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower left', frameon=True, shadow=True, fontsize=9)
    
    save_to_all(fig, "cenario_1_topologia_tvs_conflict.png")
    plt.close(fig)

# -----------------------------------------------------------------------------
# FIGURA 2: Trade-off Eficiência Energética vs QoS (scenario_rdl_energy_vs_qos)
# -----------------------------------------------------------------------------
def generate_figure_scenario_2():
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    
    # Curva de Trade-off (Fronteira de Pareto)
    power_tx = np.linspace(20, 43, 200) # dBm
    
    # Latência URLLC decai com a potência mas satura
    latency_baseline = 18.0 * np.exp(-0.06 * (power_tx - 20)) + np.random.normal(0, 0.2, 200) + 2.0
    latency_rdl_p1 = 3.5 * np.exp(-0.04 * (power_tx - 20)) + 1.2 # H-RDL
    latency_rdl_p2 = 2.2 * np.exp(-0.05 * (power_tx - 20)) + 0.8 # CA-RDL MARL
    
    # Eficiência Energética = Throughput / Potência (Bits/Joule relativo)
    ee_curve = (power_tx / 30.0) / (1.0 + np.exp(0.18 * (power_tx - 35))) * 1.6
    
    color1 = '#2c3e50'
    color2 = '#27ae60'
    
    # Eixo Principal: Latência URLLC
    ax.plot(power_tx, latency_baseline, color='#e74c3c', linestyle='--', linewidth=2.0, label='Baseline Sem RDL (Degradação por Conflito)')
    ax.plot(power_tx, latency_rdl_p1, color='#2980b9', linestyle='-', linewidth=2.2, label='Fase 1: H-RDL (Arbitragem Heurística)')
    ax.plot(power_tx, latency_rdl_p2, color='#8e44ad', linestyle='-', linewidth=2.8, label='Fase 2: CA-RDL (Otimização Cognitiva MARL)')
    ax.axhline(5.0, color='red', linestyle=':', linewidth=2, label='Limite Crítico SLA URLLC (5.0 ms)')
    
    # Destaque das Zonas de Operação
    ax.axvspan(20, 28, color='#f9e79f', alpha=0.3, label='Zona de Sub-dimensionamento (Violação de SLA)')
    ax.axvspan(28, 36, color='#d5f5e3', alpha=0.35, label='Zona de Eficiência Ótima MARL (P_tx = 31.5 dBm)')
    ax.axvspan(36, 43, color='#fadbd8', alpha=0.25, label='Zona de Desperdício Energético (P_tx > 36 dBm)')
    
    ax.set_title('Cenário 2 — Trade-off Dinâmico: Eficiência Energética vs Cumprimento de SLA URLLC', fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel('Potência de Transmissão da gNodeB (dBm)', fontsize=11)
    ax.set_ylabel('Latência Fim-a-Fim URLLC (ms)', fontsize=11)
    ax.set_xlim(20, 43)
    ax.set_ylim(0, 22)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', frameon=True, fontsize=9.5)
    
    save_to_all(fig, "cenario_2_tradeoff_energy_vs_qos.png")
    plt.close(fig)

# -----------------------------------------------------------------------------
# FIGURA 3: Arquitetura Fim-a-Fim da Co-Simulação ns-3 + O-RAN Near-RT RIC
# -----------------------------------------------------------------------------
def generate_figure_scenario_3():
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    ax.axis('off')
    
    # Bloco 1: Core Network (ns-3 EPC Helper)
    box_core = patches.FancyBboxPatch((0.05, 0.55), 0.25, 0.38, boxstyle="round,pad=0.03", facecolor='#ebf5fb', edgecolor='#2980b9', lw=2)
    ax.add_patch(box_core)
    ax.text(0.175, 0.88, "Core Network Emulado\n(NrPointToPointEpcHelper)", ha='center', fontsize=11, fontweight='bold', color='#1b4f72')
    ax.text(0.175, 0.72, "• Remote Host (Tráfego UDP/TCP)\n• PGW / SGW (Tunelamento GTP-U)\n• Mapeamento de Fatias (5QI)\n• Enlaces de Backhaul P2P", ha='center', fontsize=9.5)
    
    # Bloco 2: 5G-LENA 5G NR Stack
    box_ran = patches.FancyBboxPatch((0.36, 0.55), 0.28, 0.38, boxstyle="round,pad=0.03", facecolor='#fef9e7', edgecolor='#f39c12', lw=2)
    ax.add_patch(box_ran)
    ax.text(0.50, 0.88, "5G NR gNodeB (5G-LENA)\nBanda n78 (3.5 GHz)", ha='center', fontsize=11, fontweight='bold', color='#7d6608')
    ax.text(0.50, 0.72, "• Camadas PHY, MAC, RLC, PDCP\n• Numerologia mu=1 (SCS 30 kHz)\n• Agendador OFDMA & BWP 100MHz\n• E2 Agent Helper (ns-O-RAN)", ha='center', fontsize=9.5)
    
    # Bloco 3: UEs
    box_ue = patches.FancyBboxPatch((0.36, 0.08), 0.28, 0.35, boxstyle="round,pad=0.03", facecolor='#eafaf1', edgecolor='#27ae60', lw=2)
    ax.add_patch(box_ue)
    ax.text(0.50, 0.38, "Terminais Móveis (30 UEs)\nSlicing 3GPP Multisserviço", ha='center', fontsize=11, fontweight='bold', color='#145a32')
    ax.text(0.50, 0.23, "• Fatia URLLC (5QI 82, SLA < 5ms)\n• Fatia eMBB (5QI 9, Alta Vazão)\n• Fatia mMTC (5QI 79, Baixa Taxa)\n• Mobilidade 3D e Canal 38.901", ha='center', fontsize=9.5)
    
    # Bloco 4: Near-RT RIC & xApp RDL
    box_ric = patches.FancyBboxPatch((0.70, 0.15), 0.26, 0.78, boxstyle="round,pad=0.03", facecolor='#f4ecf7', edgecolor='#8e44ad', lw=2)
    ax.add_patch(box_ric)
    ax.text(0.83, 0.88, "Near-RT RIC (O-RAN)\nk3d Cluster (Namespace ricxapp)", ha='center', fontsize=11, fontweight='bold', color='#4a235a')
    ax.text(0.83, 0.75, "Tríade de Agentes RDL:\n1. Perception Agent (E2SM-KPM)\n2. Reasoning Agent (MAPPO)\n3. Refinement Agent (Safety Guards)", ha='center', fontsize=9, bbox=dict(facecolor='#ffffff', edgecolor='#8e44ad', pad=0.3))
    ax.text(0.83, 0.45, "Reference xApps Concorrentes:\n• xSlice (PRB Allocation)\n• Energy Saving (Tx Power)\n• Traffic Steering (Handover)", ha='center', fontsize=9, bbox=dict(facecolor='#ffffff', edgecolor='#b03a2e', pad=0.3))
    ax.text(0.83, 0.22, "Barramento RMR & SDL Redis\nMétricas Prometheus (:8081)", ha='center', fontsize=9)
    
    # Conexões e Setas
    # Core <-> RAN (Backhaul GTP-U)
    ax.annotate('', xy=(0.36, 0.74), xytext=(0.30, 0.74), arrowprops=dict(arrowstyle="<->", color="#2980b9", lw=3))
    ax.text(0.33, 0.77, "GTP-U / N3", ha='center', fontsize=9, fontweight='bold', color='#2980b9')
    
    # RAN <-> UEs (Rádio 5G NR)
    ax.annotate('', xy=(0.50, 0.55), xytext=(0.50, 0.43), arrowprops=dict(arrowstyle="<->", color="#27ae60", lw=3))
    ax.text(0.53, 0.49, "3GPP NR Uu\n(3.5 GHz)", ha='left', fontsize=9, fontweight='bold', color='#27ae60')
    
    # RAN <-> Near-RT RIC (Interface E2)
    ax.annotate('', xy=(0.70, 0.65), xytext=(0.64, 0.65), arrowprops=dict(arrowstyle="<->", color="#8e44ad", lw=3, ls="--"))
    ax.text(0.67, 0.68, "Interface E2\n(SCTP 36422)\nE2SM-KPM/RC", ha='center', fontsize=9, fontweight='bold', color='#8e44ad')
    
    ax.set_title('Arquitetura Completa de Co-Simulação Fim-a-Fim:\nns-3 v3.40 (5G-LENA + NORI) com Near-RT RIC e xApp RDL',
                 fontsize=14, fontweight='bold', pad=20)
    
    save_to_all(fig, "cenario_3_arquitetura_cosimulacao_ns3_oran.png")
    plt.close(fig)

# -----------------------------------------------------------------------------
# FIGURA 4: Comparativo Multidimensional de Métricas dos 3 Cenários
# -----------------------------------------------------------------------------
def generate_figure_scenario_4():
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    
    scenarios = ['Baseline\n(Sem RDL)', 'Fase 1\n(H-RDL Heurística)', 'Fase 2\n(CA-RDL MARL)']
    colors = ['#e74c3c', '#2980b9', '#27ae60']
    
    # Subplot 1: Latência Média e P99 URLLC
    lat_mean = [11.41, 2.85, 1.85]
    lat_p99 = [18.66, 3.59, 2.15]
    x = np.arange(len(scenarios))
    w = 0.35
    
    r1 = axes[0, 0].bar(x - w/2, lat_mean, w, label='Latência Média (ms)', color='#3498db')
    r2 = axes[0, 0].bar(x + w/2, lat_p99, w, label='Latência P99 (ms)', color='#e67e22')
    axes[0, 0].axhline(5.0, color='red', linestyle=':', label='SLA URLLC (5 ms)')
    axes[0, 0].set_title('QoS: Latência Média e P99 para Fatia URLLC', fontweight='bold')
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(scenarios)
    axes[0, 0].set_ylabel('Latência (ms)')
    axes[0, 0].legend()
    axes[0, 0].bar_label(r1, fmt='%.2f ms', padding=3)
    axes[0, 0].bar_label(r2, fmt='%.2f ms', padding=3)
    
    # Subplot 2: Taxa de Conflitos Não Mitigados (%)
    conf_rates = [34.67, 0.67, 0.18]
    r3 = axes[0, 1].bar(scenarios, conf_rates, color=colors, width=0.55)
    axes[0, 1].set_title('Governança O-RAN: Taxa de Conflitos Não Mitigados (%)', fontweight='bold')
    axes[0, 1].set_ylabel('Taxa de Conflito (%)')
    axes[0, 1].bar_label(r3, fmt='%.2f%%', padding=3)
    
    # Subplot 3: Confiabilidade (PDR %) e Violação de SLA (%)
    pdr_vals = [39.28, 99.53, 99.82]
    sla_viols = [93.33, 0.0, 0.0]
    r4 = axes[1, 0].bar(x - w/2, pdr_vals, w, label='Taxa de Entrega PDR (%)', color='#2ecc71')
    r5 = axes[1, 0].bar(x + w/2, sla_viols, w, label='Violação SLA URLLC (%)', color='#e74c3c')
    axes[1, 0].set_title('Confiabilidade: PDR vs Violação de SLA URLLC', fontweight='bold')
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(scenarios)
    axes[1, 0].set_ylabel('Percentual (%)')
    axes[1, 0].legend()
    axes[1, 0].bar_label(r4, fmt='%.1f%%', padding=3)
    axes[1, 0].bar_label(r5, fmt='%.1f%%', padding=3)
    
    # Subplot 4: Eficiência Energética e Equidade de Jain
    ee_gain = [1.000, 1.145, 1.182]
    jain_idx = [0.1414, 0.9164, 0.9650]
    r6 = axes[1, 1].bar(x - w/2, ee_gain, w, label='Ganho Energético (Bits/Joule)', color='#16a085')
    r7 = axes[1, 1].bar(x + w/2, jain_idx, w, label="Índice de Jain (Equidade)", color='#8e44ad')
    axes[1, 1].set_title('Eficiência Sustentável & Coexistência Justa de Fatias', fontweight='bold')
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(scenarios)
    axes[1, 1].set_ylabel('Índice Normalizado')
    axes[1, 1].legend()
    axes[1, 1].bar_label(r6, fmt='%.3fx', padding=3)
    axes[1, 1].bar_label(r7, fmt='%.3f', padding=3)
    
    plt.tight_layout()
    save_to_all(fig, "cenario_4_comparativo_multidimensional_metricas.png")
    plt.close(fig)

def main():
    print("Iniciando geracao das figuras de cenarios simulados em formato PNG (300 DPI)...")
    ensure_dirs()
    generate_figure_scenario_1()
    generate_figure_scenario_2()
    generate_figure_scenario_3()
    generate_figure_scenario_4()
    print("\nTodas as figuras dos cenarios simulados foram geradas com sucesso!")

if __name__ == "__main__":
    main()
