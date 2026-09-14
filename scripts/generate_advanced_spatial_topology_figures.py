#!/usr/bin/env python3
"""
Script de Geração de Figuras de Topologia Espacial e Cenários (S0 a S13).
Gera figuras 100% puramente estruturais, topológicas e arquiteturais em Tema Claro (Light) e Tema Escuro (Dark)
a 300 DPI em docs/figures/02_cenarios_e_topologias/:

REGRA CIENTÍFICA ABSOLUTA: ZERO DADOS SINTÉTICOS OU NÚMEROS FAKE NAS FIGURAS.
Apenas caixas estruturais, componentes de rede O-RAN, nós E2, xApps e setas de fluxo funcional.

Cenários Gerados:
 S0:  fig_topologia_cenarios_ns3.png (Topologia Geral de Rede O-RAN / ns-3)
 S1:  scenario_1_eevs_energy_vs_qos.png / _light.png (Topologia EEVS Energy Saving x QoS)
 S2:  scenario_2_tvs_traffic_steering_slicing.png / _light.png (Topologia TVS Traffic Steering x Slice)
 S3:  scenario_3_5ga_multicarrier_mimo.png / _light.png (Topologia 5G-A Multi-Carrier MIMO)
 S4:  scenario_4_6g_isac_sensing_coexistence.png / _light.png (Topologia 6G ISAC Sensing Coexistence)
 S5:  scenario_5_6g_cross_tier_governance.png / _light.png (Topologia 6G Cross-Tier Governance)
 S9:  scenario_9_ntn_orbital_handover.png / _light.png (Topologia NTN LEO Orbital Handover)
 S10: scenario_10_uav_swarm_coverage.png / _light.png (Topologia UAV Swarm Coverage)
 S11: scenario_11_v2x_highway_platoon.png / _light.png (Topologia V2X Highway Platoon)
 S12: scenario_12_iiot_factory_tsn.png / _light.png (Topologia IIoT Factory TSN)
 S13: scenario_13_emergency_sagin_multidomain.png / _light.png (Topologia Emergency SAGIN Multi-Domain)

Autor: Dr. George Alexandro Ferreira Barbosa
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
    ax.text(x + w / 2, y + h * 0.62 if subtitle else y + h * 0.5, title, ha='center', va='center', fontsize=10.5, fontweight='bold', color=text_color, zorder=4)
    if subtitle:
        ax.text(x + w / 2, y + h * 0.3, subtitle, ha='center', va='center', fontsize=8.5, color=subtext_color, fontweight='medium', zorder=4)

def draw_arrow(ax, x1, y1, x2, y2, label="", color='#1D4ED8', bg_color='#FFFFFF'):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", lw=2, color=color), zorder=2)
    if label:
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mid_x, mid_y + 0.15, label, ha='center', va='bottom', fontsize=8.5, fontweight='bold', color=color,
                bbox=dict(boxstyle="square,pad=0.2", facecolor=bg_color, edgecolor='none', alpha=0.9), zorder=5)

def render_scenario_0():
    bg_color = '#FFFFFF'
    text_color = '#0F172A'
    subtext_color = '#334155'

    fig, ax = plt.subplots(figsize=(11, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Topologia Geral de Rede O-RAN e Nós E2 no Co-Simulador ns-3 / NORI", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.5, 4.0, 3.2, 1.5, "Near-RT RIC Core", "Plataforma O-RAN SC Release J\nxApps & E2 Manager", '#1D4ED8', '#EFF6FF', text_color, subtext_color)
    draw_box(ax, 4.1, 4.0, 3.2, 1.5, "Middleware H-RDL", "Perception / Reasoning / Refinement\nArbitragem e Mediação Conflito", '#047857', '#ECFDF5', text_color, subtext_color)
    draw_box(ax, 7.7, 4.0, 2.8, 1.5, "Interface E2AP / E2SM", "E2SM-KPM v2.0 (Telemetria)\nE2SM-RC v1.0 (Controle)", '#7E22CE', '#F3E8FF', text_color, subtext_color)

    draw_box(ax, 0.5, 0.8, 4.5, 1.7, "Nós O-DU / O-CU (5G-LENA)", "Células gNB Macro & Small Cells\nEscalonadores MAC / PRBs / RRC", '#B45309', '#FEF3C7', text_color, subtext_color)
    draw_box(ax, 6.0, 0.8, 4.5, 1.7, "Pool de Terminais de Usuário (UEs)", "Fatias eMBB, URLLC, mMTC\nMobilidade e Perfis de Tráfego", '#BE123C', '#FFE4E6', text_color, subtext_color)

    draw_arrow(ax, 3.7, 4.75, 4.1, 4.75, "RMR Sub", '#1D4ED8', bg_color)
    draw_arrow(ax, 7.3, 4.75, 7.7, 4.75, "Payload APER", '#047857', bg_color)
    draw_arrow(ax, 2.75, 2.5, 2.75, 4.0, "Subscrição E2", '#B45309', bg_color)
    draw_arrow(ax, 8.25, 2.5, 8.25, 4.0, "Telemetria KPM", '#BE123C', bg_color)
    draw_arrow(ax, 5.0, 1.65, 6.0, 1.65, "Enlace de Rádio NR", '#047857', bg_color)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig_topologia_cenarios_ns3.png"), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_1(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S1: Trade-Off EEVS — Energy Saving x QoS Slicing", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 3.8, 3.8, 1.6, "Energy Saving xApp", "Desativação de Células / Carrier Aggregation\nFoco em Eficiência Energética", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)
    draw_box(ax, 5.4, 3.8, 3.8, 1.6, "QoS Slicing xApp", "Garantia de Vazão e SLA de Fatias\nFoco em Experiência do Usuário", '#1D4ED8', '#EFF6FF' if is_light else '#1E3A8A', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "Arbitrador H-RDL (Reasoning)", "Resolução Multiobjetivo Pareto\nMediação de Conflito Indireto", '#7E22CE', '#F3E8FF' if is_light else '#2E1065', text_color, subtext_color)

    draw_arrow(ax, 2.7, 3.8, 4.5, 2.4, "Intenção de Economia", '#047857', bg_color)
    draw_arrow(ax, 7.3, 3.8, 5.5, 2.4, "Demanda de Banda SLA", '#1D4ED8', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_1_eevs_energy_vs_qos" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_2(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S2: Conflito TVS — Traffic Steering x QoS Slicing", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 3.8, 3.8, 1.6, "Traffic Steering xApp", "Reorientação de Tráfego Inter-Células\nRedirecionamento de UEs", '#B45309', '#FEF3C7' if is_light else '#451A03', text_color, subtext_color)
    draw_box(ax, 5.4, 3.8, 3.8, 1.6, "QoS / xSlice xApp", "Alocação Direta de PRBs por Fatia\nPreservação de Banda Reservada", '#1D4ED8', '#EFF6FF' if is_light else '#1E3A8A', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "Arbitrador H-RDL (Perception)", "Detecção de Colisão Direta/Indireta\nAjuste Dinâmico de Pesos (TVS)", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_arrow(ax, 2.7, 3.8, 4.5, 2.4, "Comando HO / Steering", '#B45309', bg_color)
    draw_arrow(ax, 7.3, 3.8, 5.5, 2.4, "Reativação de PRBs", '#1D4ED8', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_2_tvs_traffic_steering_slicing" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_3(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S3: 5G-Advanced Multi-Carrier MIMO & Load Balancing", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 3.8, 3.8, 1.6, "Load-Balancer xApp", "Balanceamento de Carga Multi-Portadora\nDistribuição Eficiente de PRBs", '#0891B2', '#E0F2FE' if is_light else '#083344', text_color, subtext_color)
    draw_box(ax, 5.4, 3.8, 3.8, 1.6, "Beamformer xApp", "Otimização de Feixe Massive MIMO\nFormação de Feixes Direcionais", '#7E22CE', '#F3E8FF' if is_light else '#2E1065', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "Camada H-RDL 5G-A Guard", "Coordenação Espacial e Espectral\nEliminação de Interferência Co-Canal", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_arrow(ax, 2.7, 3.8, 4.5, 2.4, "Matriz de Carga Carrier", '#0891B2', bg_color)
    draw_arrow(ax, 7.3, 3.8, 5.5, 2.4, "Vetor de Feixes MIMO", '#7E22CE', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_3_5ga_multicarrier_mimo" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_4(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S4: 6G ISAC Radar & Coexistência Comunicação/Sensing", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 3.8, 3.8, 1.6, "ISAC Radar xApp", "Sensoriamento RF & Detecção Ambiental\nMapeamento Espacial e Rastreamento", '#BE123C', '#FFE4E6' if is_light else '#4C0519', text_color, subtext_color)
    draw_box(ax, 5.4, 3.8, 3.8, 1.6, "Comms Scheduler xApp", "Alocação de Tráfego de Dados 6G\nGarantia de Débito de Comunicação", '#1D4ED8', '#EFF6FF' if is_light else '#1E3A8A', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "Arbitrador Co-Sensing H-RDL", "Particionamento Ortogonal de Subportadoras\nZero Interferência Radar-Comunicação", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_arrow(ax, 2.7, 3.8, 4.5, 2.4, "Pulso Radar ISAC", '#BE123C', bg_color)
    draw_arrow(ax, 7.3, 3.8, 5.5, 2.4, "Requisito de Banda Comms", '#1D4ED8', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_4_6g_isac_sensing_coexistence" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_5(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S5: Governança Cross-Tier 6G & Security Guardian", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 3.8, 3.8, 1.6, "Sec-Guardian xApp", "Verificação Zero-Trust de Intenções\nDetecção de Comandos Maliciosos", '#7E22CE', '#F3E8FF' if is_light else '#2E1065', text_color, subtext_color)
    draw_box(ax, 5.4, 3.8, 3.8, 1.6, "Cross-Tier xApp Manager", "Orquestração Multidomínio Near-RT / Non-RT\nAplicação de Políticas Globais", '#B45309', '#FEF3C7' if is_light else '#451A03', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "Refinement Agent (Safety L0-L3)", "Validação Estrita de Limites e História\nBloqueio Instantâneo de Comandos Inválidos", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_arrow(ax, 2.7, 3.8, 4.5, 2.4, "Filtro de Segurança", '#7E22CE', bg_color)
    draw_arrow(ax, 7.3, 3.8, 5.5, 2.4, "Política Hierárquica", '#B45309', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_5_6g_cross_tier_governance" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_9(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S9: NTN LEO Satellite Orbital Handover & Compensação Doppler", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 4.0, 3.8, 1.5, "Sat_LEO_01 (Orbital Node)", "Vetor Orbital | Efeito Doppler\nxApp: NTN-Steering (PROPOSED)", '#7E22CE', '#F3E8FF' if is_light else '#2E1065', text_color, subtext_color)
    draw_box(ax, 5.4, 4.0, 3.8, 1.5, "Sat_LEO_02 (Target Node)", "Passagem Orbital Programada\nxApp: Satellite-HO (PROPOSED)", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "Estação de Solo & Terminal UE NTN", "Feixe NTN | Malha Fechada E2\nControle de Handover Inter-Orbital", '#1D4ED8', '#EFF6FF' if is_light else '#1E3A8A', text_color, subtext_color)

    draw_arrow(ax, 2.7, 4.0, 4.5, 2.4, "KPM Doppler Feeder", '#7E22CE', bg_color)
    draw_arrow(ax, 7.3, 4.0, 5.5, 2.4, "Handover Command", '#047857', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_9_ntn_orbital_handover" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_10(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S10: Cobertura Aérea Dinâmica UAV Swarm & Gestão de Bateria SoC", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 3.8, 3.8, 1.6, "UAV_Base_01 (Enxame Aéreo)", "Estado de Bateria Reduzido (SoC)\nxApp: Energy-Conserver UAV (PROPOSED)", '#B45309', '#FEF3C7' if is_light else '#451A03', text_color, subtext_color)
    draw_box(ax, 5.4, 3.8, 3.8, 1.6, "UAV_Base_02 (Relay Substituto)", "Estado de Bateria Pleno (SoC)\nxApp: UAV-Mobility (PROPOSED)", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "Usuários Terrestres em Emergência", "Manutenção de Cobertura 3D sem Desconexão", '#1D4ED8', '#EFF6FF' if is_light else '#1E3A8A', text_color, subtext_color)

    draw_arrow(ax, 2.7, 3.8, 4.5, 2.4, "Alerta de Bateria", '#B45309', bg_color)
    draw_arrow(ax, 7.3, 3.8, 5.5, 2.4, "Reconfiguração de Feixe 3D", '#047857', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_10_uav_swarm_coverage" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_11(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S11: V2X Highway Platoon em Alta Velocidade & Fatia URLLC", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 3.8, 3.8, 1.6, "Infraestrutura RSU Rodoviária", "Handover Veicular Ultra-Rápido\nxApp: V2X-Mobility (PROPOSED)", '#BE123C', '#FFE4E6' if is_light else '#4C0519', text_color, subtext_color)
    draw_box(ax, 5.4, 3.8, 3.8, 1.6, "Pelotão Veicular Conectado", "Garantia de Latência Ultra-Baixa\nxApp: Platoon-QoS (PROPOSED)", '#1D4ED8', '#EFF6FF' if is_light else '#1E3A8A', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "Middleware H-RDL no Near-RT RIC", "Arbitragem de Espectro V2X & Zero Perda de Sinal", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_arrow(ax, 2.7, 3.8, 4.5, 2.4, "Telemetry V2X", '#BE123C', bg_color)
    draw_arrow(ax, 7.3, 3.8, 5.5, 2.4, "Cota URLLC Reservada", '#1D4ED8', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_11_v2x_highway_platoon" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_12(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    plt.title("Cenário S12: IIoT Factory TSN — Latência Determinística e Trava de Jitter", fontsize=13.5, fontweight='bold', color=text_color, pad=15)

    draw_box(ax, 0.8, 3.8, 3.8, 1.6, "Ambiente Industrial TSN", "Sensores & Atuadores Robóticos\nxApp: Industrial-QoS (PROPOSED)", '#0891B2', '#E0F2FE' if is_light else '#083344', text_color, subtext_color)
    draw_box(ax, 5.4, 3.8, 3.8, 1.6, "gNB-DU Industrial", "Escalonamento Determinístico\nSupressão de Jitter", '#7E22CE', '#F3E8FF' if is_light else '#2E1065', text_color, subtext_color)

    draw_box(ax, 3.1, 0.8, 3.8, 1.6, "H-RDL Industrial Guard", "Garantia de SLA TSN & Zero Perda de Pacote", '#047857', '#ECFDF5' if is_light else '#064E3B', text_color, subtext_color)

    draw_arrow(ax, 2.7, 3.8, 4.5, 2.4, "Traffic Flow TSN", '#0891B2', bg_color)
    draw_arrow(ax, 7.3, 3.8, 5.5, 2.4, "Prioridade Determinística", '#7E22CE', bg_color)

    plt.tight_layout()
    suffix = "_light.png" if is_light else ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, "scenario_12_iiot_factory_tsn" + suffix), dpi=300, facecolor=bg_color)
    plt.close()

def render_scenario_13(is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
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
    print("[+] Gerando figuras de topologia espacial pura sem dados numéricos (S0 a S13)...")
    render_scenario_0()
    for is_light in [True, False]:
        render_scenario_1(is_light)
        render_scenario_2(is_light)
        render_scenario_3(is_light)
        render_scenario_4(is_light)
        render_scenario_5(is_light)
        render_scenario_9(is_light)
        render_scenario_10(is_light)
        render_scenario_11(is_light)
        render_scenario_12(is_light)
        render_scenario_13(is_light)
    print("[OK] Todas as figuras de topologia estrutural sem dados foram salvas com sucesso!")
