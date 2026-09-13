#!/usr/bin/env python3
"""
Script de Geração das Figuras de Topologia Espacial para Cenários Avançados S9 a S13 (5G-A / 6G).
Gera figuras em Tema Claro (Light) e Tema Escuro (Dark) a 300 DPI em docs/figures/02_cenarios_e_topologias/:
 1. scenario_9_ntn_orbital_handover.png / scenario_9_ntn_orbital_handover_light.png
 2. scenario_10_uav_swarm_coverage.png / scenario_10_uav_swarm_coverage_light.png
 3. scenario_11_v2x_highway_platoon.png / scenario_11_v2x_highway_platoon_light.png
 4. scenario_12_iiot_factory_tsn.png / scenario_12_iiot_factory_tsn_light.png
 5. scenario_13_emergency_sagin_multidomain.png / scenario_13_emergency_sagin_multidomain_light.png
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_DIR = os.path.join("docs", "figures", "02_cenarios_e_topologias")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def draw_box(ax, x, y, w, h, title, subtitle="", color='#1E3A8A', fill='#F8FAFC', text_color='#0F172A', subtext_color='#334155'):
    rect = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.03,rounding_size=0.08",
        linewidth=2, edgecolor=color, facecolor=fill, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h * 0.65 if subtitle else y + h * 0.5, title, ha='center', va='center', fontsize=10.5, fontweight='bold', color=text_color, zorder=4)
    if subtitle:
        ax.text(x + w / 2, y + h * 0.3, subtitle, ha='center', va='center', fontsize=8.5, color=subtext_color, fontweight='medium', zorder=4)

def draw_arrow(ax, x1, y1, x2, y2, label="", color='#1D4ED8', bg_color='#FFFFFF'):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", lw=2, color=color), zorder=2)
    if label:
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mid_x, mid_y + 0.15, label, ha='center', va='bottom', fontsize=8.5, fontweight='bold', color=color,
                bbox=dict(boxstyle="square,pad=0.2", facecolor=bg_color, edgecolor='none', alpha=0.9), zorder=5)

def render_scenario_9(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    box_bg = '#F8FAFC' if is_light else '#1E293B'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S9: NTN LEO Satellite Orbital Handover & Compensação Doppler", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 4.0, 3.8, 1.5, "Sat_LEO_01 (Orbital Node)", "V_orbit = 7.5 km/s | Doppler Shift\nxApp: NTN-Steering (PROPOSED)", '#7E22CE', '#F3E8FF' if is_light else '#2E1065', text_color, subtext_color)
    draw_box(ax, 5.4, 4.0, 3.8, 1.5, "Sat_LEO_02 (Target Node)", "Previsão de Passagem Orbital\nxApp: Satellite-HO (PROPOSED)", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "Estação de Solo & Terminal UE NTN", "Feixe NTN 6G | Malha Fechada E2\nControle de Handover Inter-Orbital", '#1D4ED8', '#EFF6FF' if is_light else '#1E3A8A', text_color, subtext_color)

    draw_arrow(ax, 2.7, 4.0, 4.5, 2.4, "KPM Doppler Feeder", '#7E22CE', bg_color)
    draw_arrow(ax, 7.3, 4.0, 5.5, 2.4, "Handover Command", '#047857', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_9_ntn_orbital_handover" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_10(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    box_bg = '#F8FAFC' if is_light else '#1E293B'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S10: Cobertura Aérea Dinâmica UAV Swarm & Gestão de Bateria SoC", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 3.8, 3.8, 1.6, "UAV_Base_01 (Enxame Aéreo)", "Nível de Bateria SoC = 15%\nxApp: Energy-Conserver UAV (PROPOSED)", '#B45309', '#FEF3C7' if is_light else '#451A03', text_color, subtext_color)
    draw_box(ax, 5.4, 3.8, 3.8, 1.6, "UAV_Base_02 (Relay Substituto)", "Nível de Bateria SoC = 95%\nxApp: UAV-Mobility (PROPOSED)", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "Usuários Terrestres em Emergência", "Manutenção de Cobertura 3D sem Desconexão", '#1D4ED8', '#EFF6FF' if is_light else '#1E3A8A', text_color, subtext_color)

    draw_arrow(ax, 2.7, 3.8, 4.5, 2.4, "Alerta de Bateria", '#B45309', bg_color)
    draw_arrow(ax, 7.3, 3.8, 5.5, 2.4, "Reconfiguração de Feixe 3D", '#047857', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_10_uav_swarm_coverage" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_11(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    box_bg = '#F8FAFC' if is_light else '#1E293B'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S11: V2X Highway Platoon em Alta Velocidade (110 km/h) & URLLC Sub-10ms", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 3.8, 3.8, 1.6, "Infraestrutura RSU Rodoviária", "Handover Ultra-Rápido a 110 km/h\nxApp: V2X-Mobility (PROPOSED)", '#BE123C', '#FFE4E6' if is_light else '#4C0519', text_color, subtext_color)
    draw_box(ax, 5.4, 3.8, 3.8, 1.6, "Pelotão Veicular Conectado", "Garantia de Latência URLLC < 10ms\nxApp: Platoon-QoS (PROPOSED)", '#1D4ED8', '#EFF6FF' if is_light else '#1E3A8A', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "Middleware H-RDL no Near-RT RIC", "Arbitragem de Espectro V2X & Zero Dropped Calls", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_arrow(ax, 2.7, 3.8, 4.5, 2.4, "Telemetry V2X", '#BE123C', bg_color)
    draw_arrow(ax, 7.3, 3.8, 5.5, 2.4, "Cota URLLC Reservada", '#1D4ED8', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_11_v2x_highway_platoon" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_12(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    box_bg = '#F8FAFC' if is_light else '#1E293B'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S12: IIoT Factory TSN — Latência Determinística e Trava de Jitter", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 3.8, 3.8, 1.6, "Ambiente Industrial TSN", "Sensores & Atuadores Robóticos\nxApp: Industrial-QoS (PROPOSED)", '#0891B2', '#E0F2FE' if is_light else '#083344', text_color, subtext_color)
    draw_box(ax, 5.4, 3.8, 3.8, 1.6, "gNB-DU Industrial 5G-A", "Escalonamento Determinístico Sub-ms\nSupressão de Jitter", '#7E22CE', '#F3E8FF' if is_light else '#2E1065', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "H-RDL Industrial Guard", "Garantia de SLA TSN & Zero Perda de Pacote", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_arrow(ax, 2.7, 3.8, 4.5, 2.4, "Traffic Flow TSN", '#0891B2', bg_color)
    draw_arrow(ax, 7.3, 3.8, 5.5, 2.4, "Prioridade Determinística", '#7E22CE', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_12_iiot_factory_tsn" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_13(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    box_bg = '#F8FAFC' if is_light else '#1E293B'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S13: Emergency SAGIN — Orquestração Multidomínio Satélite-UAV-Terrestre", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 3.8, 3.8, 1.6, "Camada Espacial e Aérea (SAGIN)", "Satélite LEO + Enxame UAV\nxApp: Rescue-QoS (PROPOSED)", '#BE123C', '#FFE4E6' if is_light else '#4C0519', text_color, subtext_color)
    draw_box(ax, 5.4, 3.8, 3.8, 1.6, "Rede Terrestre de Resgate", "Equipes de Emergência & Drones\nGarantia de Resiliência", '#1D4ED8', '#EFF6FF' if is_light else '#1E3A8A', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "Orquestrador Multidomínio H-RDL", "Alocação Cross-Tier e Manutenção de SLA de Crise", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_arrow(ax, 2.7, 3.8, 4.5, 2.4, "SAGIN Backhaul", '#BE123C', bg_color)
    draw_arrow(ax, 7.3, 3.8, 5.5, 2.4, "Canal Crítico de Resgate", '#1D4ED8', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_13_emergency_sagin_multidomain" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

if __name__ == "__main__":
    print("[+] Gerando figuras de topologia espacial para cenários avançados S9 a S13 (Light & Dark)...")
    for is_light in [True, False]:
        render_scenario_9(is_light)
        render_scenario_10(is_light)
        render_scenario_11(is_light)
        render_scenario_12(is_light)
        render_scenario_13(is_light)
    print("[OK] Todas as 10 figuras de topologia espacial S9-S13 geradas com sucesso!")
