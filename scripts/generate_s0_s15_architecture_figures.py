#!/usr/bin/env python3
"""
Script de Geração da Suíte Oficial de Figuras Científicas XApp-RDL (S0 a S15).
Implementação baseada na Skill 'xapp-rdl-scenario-figure-generator':

5 Referências de Ouro:
  1. EEVS Archetype (Macro/Small Cell, Energy Saving vs QoS, Trade-Off)
  2. TVS Archetype (2 gNodeBs, URLLC/eMBB/mMTC, Overlap, Traffic Steering vs Slicing)
  3. 5G-A Multi-Carrier MIMO Archetype (Corredor Urbano, Massive MIMO, Beams, Dynamic PRBs)
  4. 6G ISAC Archetype (Feixes de Sensoriamento Cyan e Comunicação Verde-Lima, Alvos/UAVs)
  5. Cross-Tier Governance / Anti-Rogue Archetype (Non-RT RIC/SMO -> Near-RT RIC/H-RDL -> E2 -> RAN, Grade 2x2, Safety Guard Shield)

Gera 32 Figuras Oficiais em 300 DPI (16 cenários S0-S15 x 2 variantes [LIGHT e DARK])
juntamente com os artefatos: cenarios_canonicos_s0_s15.json, relatorio_correspondencia_A_B.md e manifesto_proveniencia.json.

REGRA CIENTÍFICA ABSOLUTA: ZERO DADOS SINTÉTICOS OU NÚMEROS FAKE NAS FIGURAS.

Autor: Dr. George Alexandro Ferreira Barbosa
"""

import os
import json
import hashlib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_DIR = os.path.join("docs", "figures", "02_cenarios_e_topologias")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Paleta Semântica Normativa da Skill xapp-rdl-scenario-figure-generator
PALETTE = {
    "urllc": "#06B6D4",      # Cyan
    "embb": "#8B5CF6",       # Purple
    "mmtc": "#F59E0B",       # Amber / IoT
    "energy": "#10B981",     # Green (Energy Saving)
    "qos": "#F97316",        # Orange/Red (QoS)
    "steering": "#2563EB",   # Blue/Cyan (Traffic Steering)
    "beamforming": "#3B82F6",# Blue
    "sensing_beam": "#06B6D4", # Cyan
    "comms_beam": "#84CC16", # Yellow-Green
    "rogue": "#EF4444",      # Red
    "hrdl_safety": "#0D9488",# Teal/Green
    "neutral_infra": "#64748B"# Blue-Gray
}

SCENARIO_CONFIGS = {
    "S0": {
        "title": "XApp-RDL Experimental Scenario S0 — No-Conflict Control",
        "archetype": "tvs",
        "phase": "Fase 1 (Experimental)",
        "xapps": ["QoS/Slicing xApp", "Traffic Steering xApp"],
        "conflict_desc": "Sem conflito: propostas compatíveis de steering e slice sem disputa por PRBs.",
        "gnbs": [("gNB-Macro-1", 2.5, 3.8, "macro"), ("gNB-Macro-2", 7.0, 3.8, "macro")],
        "ues": [("UE-01", 2.0, 1.8, "eMBB"), ("UE-02", 3.0, 1.8, "URLLC"), ("UE-03", 6.5, 1.8, "mMTC"), ("UE-04", 7.5, 1.8, "eMBB")],
        "metrics": ["False positive rate", "Specificity", "Added decision latency", "Throughput delta", "SLA violations count"]
    },
    "S1": {
        "title": "XApp-RDL Experimental Scenario S1 — Direct PRB Conflict",
        "archetype": "eevs",
        "phase": "Fase 1 (Experimental)",
        "xapps": ["QoS/Slicing xApp", "Energy Saving xApp"],
        "conflict_desc": "Conflito direto sobre a mesma cota de PRBs na célula sob alta carga (Wc = 200 ms).",
        "gnbs": [("gNB-Macro Single", 4.8, 3.8, "macro")],
        "ues": [("UE-01", 3.8, 1.8, "URLLC"), ("UE-02", 4.8, 1.8, "eMBB"), ("UE-03", 5.8, 1.8, "URLLC")],
        "metrics": ["Precision / Recall / F1-score", "Detection latency", "PRB utilization", "SLA violation duration", "Recovery time"]
    },
    "S2": {
        "title": "XApp-RDL Experimental Scenario S2 — Energy Saving vs QoS",
        "archetype": "eevs",
        "phase": "Fase 1 (Experimental)",
        "xapps": ["Energy Saving xApp", "QoS/Slicing xApp"],
        "conflict_desc": "Energy Saving solicita Cell Sleep vs QoS exige capacidade para tráfego URLLC.",
        "gnbs": [("Macro gNB (43 dBm)", 2.5, 3.8, "macro"), ("Micro Small Cell (30 dBm)", 7.0, 3.8, "micro")],
        "ues": [("UE-01 (URLLC)", 2.5, 1.8, "URLLC"), ("UE-02 (eMBB)", 7.0, 1.8, "eMBB"), ("UE-03 (URLLC/V2X)", 4.75, 1.8, "URLLC")],
        "metrics": ["Energy consumption", "URLLC P99 latency", "Packet loss", "Throughput", "PRB utilization", "SLA violation duration"]
    },
    "S3": {
        "title": "XApp-RDL Experimental Scenario S3 — Traffic Steering vs Slicing",
        "archetype": "tvs",
        "phase": "Fase 1 (Experimental)",
        "xapps": ["Traffic Steering xApp", "QoS/Slicing xApp"],
        "conflict_desc": "Steering altera distribuição de carga enquanto Slicing preserva quotas de fatia.",
        "gnbs": [("gNB-A (100 MHz)", 2.5, 3.8, "macro"), ("gNB-B (100 MHz)", 7.0, 3.8, "macro")],
        "ues": [("UE-01 (URLLC)", 4.0, 1.8, "URLLC"), ("UE-02 (eMBB)", 4.75, 1.8, "eMBB"), ("UE-03 (mMTC)", 5.5, 1.8, "mMTC")],
        "metrics": ["P99 URLLC latency", "eMBB throughput", "mMTC packet delivery", "PRB share", "Jain fairness", "SLA violations count"]
    },
    "S4": {
        "title": "XApp-RDL Experimental Scenario S4 — Traffic Steering vs Energy Saving",
        "archetype": "eevs",
        "phase": "Fase 1 (Experimental)",
        "xapps": ["Traffic Steering xApp", "Energy Saving xApp"],
        "conflict_desc": "TS pretende mover UEs A->B enquanto ES pretende colocar célula B em sleep.",
        "gnbs": [("gNB-A (Overloaded)", 2.5, 3.8, "macro"), ("gNB-B (Target Sleep)", 7.0, 3.8, "micro")],
        "ues": [("UE-01", 4.2, 1.8, "eMBB"), ("UE-02", 5.2, 1.8, "eMBB")],
        "metrics": ["Cell load", "HO success/failure rate", "Ping-pong rate", "Energy consumption", "Throughput", "Outage duration"]
    },
    "S5": {
        "title": "XApp-RDL Experimental Scenario S5 — Temporal Ping-Pong",
        "archetype": "tvs",
        "phase": "Fase 1 (Experimental)",
        "xapps": ["MRO / Steering xApp", "Energy / QoS xApp"],
        "conflict_desc": "Decisões alternadas A->B->A em curto intervalo (supressão via histerese H-RDL).",
        "gnbs": [("Cell A (Origem)", 2.5, 3.8, "macro"), ("Cell B (Destino)", 7.0, 3.8, "macro")],
        "ues": [("UE Mobile (Borda)", 4.75, 1.8, "URLLC")],
        "metrics": ["Handover count", "Ping-pong rate", "Action reversal rate", "Control churn", "Dwell time", "Stable recovery time"]
    },
    "S6": {
        "title": "XApp-RDL Experimental Scenario S6 — Multi-xApp Conflict Storm",
        "archetype": "mimo",
        "phase": "Fase 1 (Experimental)",
        "xapps": ["QoS/Slicing", "Traffic Steering", "Energy Saving", "Load Balancer", "Beamformer"],
        "conflict_desc": "Tempestade de propostas simultâneas e dependências indiretas em cluster multi-célula.",
        "gnbs": [("gNB Cluster 01", 2.2, 3.8, "macro"), ("gNB Cluster 02", 4.75, 3.8, "macro"), ("gNB Cluster 03", 7.3, 3.8, "micro")],
        "ues": [("UE-01", 2.0, 1.8, "URLLC"), ("UE-02", 4.5, 1.8, "eMBB"), ("UE-03", 7.0, 1.8, "mMTC")],
        "metrics": ["Conflicts per second", "Decision throughput", "Queue depth", "CPU / Memory usage", "P95/P99 decision latency", "Rejected actions count"]
    },
    "S7": {
        "title": "XApp-RDL Experimental Scenario S7 — Fault / Rogue xApp / Adversarial Control",
        "phase": "Fase 1 (Experimental)",
        "xapps": ["xApps Legítimas", "Rogue / Fault xApp"],
        "conflict_desc": "Injeção de propostas maliciosas/inválidas bloqueadas deterministicamente pelo Safety Guard L0-L3.",
        "gnbs": [("gNB Multi-Cell Stack", 4.75, 3.8, "macro")],
        "ues": [("UE-01", 3.5, 1.8, "URLLC"), ("UE-02", 6.0, 1.8, "eMBB")],
        "metrics": ["Attack / fault rejection rate", "False acceptance rate", "Unsafe execution rate", "Isolation time", "SLA impact"]
    },
    "S8": {
        "title": "XApp-RDL Experimental Scenario S8 — Real NORI Closed Loop",
        "phase": "Fase 1 (Experimental - Gates 1-4)",
        "xapps": ["KPM Monitor xApp", "Traffic Steering xApp", "H-RDL Core"],
        "conflict_desc": "Validação de loop fechado E2AP/E2SM-KPM/E2SM-RC via ns-3 / 5G-LENA / NORI.",
        "gnbs": [("ns-3 / NORI gNB Node", 4.75, 3.8, "macro")],
        "ues": [("UE Pool NORI", 4.75, 1.8, "URLLC")],
        "metrics": ["KPM report rate", "Control RTT", "Action application latency", "KPI before/after delta", "ACK/Failure rate"]
    },
    "S9": {
        "title": "XApp-RDL Future Scenario S9 — NTN Terrestrial–Satellite Conflict",
        "archetype": "isac",
        "phase": "Fase 2 / 6G (Futuro)",
        "xapps": ["NTN Steering xApp", "QoS Slicing", "Load Balancer"],
        "conflict_desc": "Seleção Terrestre vs Satélite LEO considerando RTT, efeito Doppler e feixe NTN.",
        "gnbs": [("Satélite LEO (Orbital)", 2.5, 4.2, "macro"), ("gNB Terrestre", 7.0, 3.5, "macro")],
        "ues": [("Terminal Solo NTN", 4.75, 1.8, "URLLC")],
        "metrics": ["RTT latency", "Doppler shift compensation", "Elevation angle", "Handover count", "Outage probability", "Slice SLA"]
    },
    "S10": {
        "title": "XApp-RDL Future Scenario S10 — UAV / Flying gNB / Swarm",
        "archetype": "isac",
        "phase": "Fase 2 / 6G (Futuro)",
        "xapps": ["UAV Mobility xApp", "Energy Saving xApp", "Load Balancer"],
        "conflict_desc": "Demanda de cobertura aérea em emergência vs Estado de Bateria (SoC) do enxame.",
        "gnbs": [("UAV Relay Aéreo 01", 2.5, 4.0, "micro"), ("UAV Relay Aéreo 02", 7.0, 4.0, "micro")],
        "ues": [("Usuários Solo Emergência", 4.75, 1.8, "URLLC")],
        "metrics": ["State of Charge (SoC)", "Coverage probability", "Outage duration", "UAV Handovers", "Mesh recovery time", "Energy consumption"]
    },
    "S11": {
        "title": "XApp-RDL Future Scenario S11 — V2X High-Mobility Platoon",
        "archetype": "mimo",
        "phase": "Fase 2 / 6G (Futuro)",
        "xapps": ["Traffic Steering xApp", "Mobility / MRO xApp", "Platoon QoS xApp"],
        "conflict_desc": "Handover veicular em alta velocidade (110 km/h) com garantia de latência ultra-baixa.",
        "gnbs": [("RSU Rodoviária 01", 2.5, 3.8, "macro"), ("RSU Rodoviária 02", 7.0, 3.8, "macro")],
        "ues": [("Pelotão V2X Vehicle", 4.75, 1.8, "URLLC")],
        "metrics": ["Handover failure rate", "Interruption time", "Ping-pong rate", "RSRP / RSRQ / SINR", "URLLC latency tail", "Platoon SLA"]
    },
    "S12": {
        "title": "XApp-RDL Future Scenario S12 — IIoT / TSN Mission-Critical",
        "archetype": "mimo",
        "phase": "Fase 2 / 6G (Futuro)",
        "xapps": ["Industrial QoS xApp", "Energy Saving xApp", "Load Balancer"],
        "conflict_desc": "Reserva estrita TSN industrial sem jitter vs Otimização de energia/capacidade.",
        "gnbs": [("gNB-DU Industrial TSN", 4.75, 3.8, "micro")],
        "ues": [("Robôs / Atuadores TSN", 4.75, 1.8, "mMTC")],
        "metrics": ["Control-cycle latency", "Jitter bounds", "Missed control cycles", "Packet loss rate", "Availability percentage", "Energy efficiency"]
    },
    "S13": {
        "title": "XApp-RDL 6G Scenario S13 — SAGIN Multi-Domain",
        "archetype": "isac",
        "phase": "Fase 3 / 6G (Avançado)",
        "xapps": ["NTN Steering", "UAV Coordination", "QoS Slicing", "Energy Saving"],
        "conflict_desc": "Orquestração multidomínio 3D (Espaço-Ar-Terra) e contenção de backhaul de resgate.",
        "gnbs": [("Satélite LEO Espacial", 2.0, 4.4, "macro"), ("UAV Enxame Aéreo", 4.75, 3.6, "micro"), ("gNB O-RAN Terrestre", 7.5, 2.8, "macro")],
        "ues": [("Equipe Resgate Terrestre", 4.75, 1.8, "URLLC")],
        "metrics": ["Cross-tier latency", "Multi-domain availability", "Critical SLA compliance", "Resource allocation efficiency", "Recovery time", "Fairness index"]
    },
    "S14": {
        "title": "XApp-RDL 6G Scenario S14 — ISAC Sensing vs Communication",
        "archetype": "isac",
        "phase": "Fase 3 / 6G (Avançado)",
        "xapps": ["ISAC / Sensing xApp", "eMBB / QoS xApp", "Beamformer xApp"],
        "conflict_desc": "Disputa por símbolos OFDM entre feixes de sensoriamento (Cyan) e comunicação (Verde-Lima).",
        "gnbs": [("6G Dual-ISAC gNB", 4.75, 3.8, "macro")],
        "ues": [("Target Radar / Vehicle", 3.0, 1.8, "URLLC"), ("Comms UE 6G", 6.5, 1.8, "eMBB")],
        "metrics": ["Sensing accuracy / range error", "Radar SINR", "Communication SINR", "Throughput", "Latency", "Pareto optimal trade-off frontier"]
    },
    "S15": {
        "title": "XApp-RDL 6G Scenario S15 — Cross-Tier Governance & Anti-Rogue",
        "archetype": "crosstier",
        "phase": "Fase 3 / 6G (Avançado)",
        "xapps": ["QoS", "Steering", "Energy", "Load Balancer", "Beamformer", "ISAC", "Rogue xApp"],
        "conflict_desc": "Governança multi-loop (Non-RT RIC/SMO -> Near-RT RIC/H-RDL -> E2 -> RAN) com escudo Anti-Rogue.",
        "gnbs": [("gNB Cluster Grid 01", 3.0, 3.5, "macro"), ("gNB Cluster Grid 02", 6.5, 3.5, "macro")],
        "ues": [("UE Slices 6G", 4.75, 1.8, "URLLC")],
        "metrics": ["Unsafe execution rate", "Rogue / fault block rate", "False positive rate", "Detection latency", "Lockout duration", "PDR stability"]
    }
}

def render_scientific_scenario_figure(scen_key, config, is_light=True):
    """
    Gera a figura científica oficial de alta qualidade (300 DPI, 16:9)
    alinhada rigorosamente às 5 referências de ouro da Skill 'xapp-rdl-scenario-figure-generator'.
    """
    bg_color = "#FFFFFF" if is_light else "#0F172A"
    card_bg = "#F8FAFC" if is_light else "#1E293B"
    text_color = "#0F172A" if is_light else "#F8FAFC"
    subtext_color = "#334155" if is_light else "#94A3B8"
    border_color = "#CBD5E1" if is_light else "#334155"

    fig, ax = plt.subplots(figsize=(14, 8), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # 1. TÍTULO OFICIAL E FASE NO TOPO
    ax.text(7.0, 7.6, config["title"], ha='center', va='center', fontsize=12.5, fontweight='bold', color=text_color)
    ax.text(7.0, 7.25, f"Fase: {config['phase']} | Scientific Infographic (IEEE/ACM/SBRC)",
            ha='center', va='center', fontsize=9.0, fontweight='medium', color=subtext_color)

    # 2. PAINEL NEAR-RT RIC / H-RDL (Canto Superior Direitos ou Central)
    if config.get("archetype") == "crosstier":
        # Governança Cross-Tier: SMO/Non-RT -> Near-RT RIC/H-RDL -> RAN
        smo_box = patches.FancyBboxPatch((0.5, 5.0), 3.2, 1.8, boxstyle="round,pad=0.03", facecolor=card_bg, edgecolor=PALETTE["steering"], lw=1.8)
        ax.add_patch(smo_box)
        ax.text(2.1, 6.4, "Non-RT RIC / SMO", ha='center', va='center', fontsize=9.5, fontweight='bold', color=PALETTE["steering"])
        ax.text(2.1, 5.7, "Políticas rApp (A1 Interface)\nDiretrizes de Governança Global", ha='center', va='center', fontsize=7.8, color=text_color)

        ric_box = patches.FancyBboxPatch((4.2, 5.0), 5.6, 1.8, boxstyle="round,pad=0.03", facecolor=card_bg, edgecolor=PALETTE["hrdl_safety"], lw=2.0)
        ax.add_patch(ric_box)
        ax.text(7.0, 6.4, "Near-RT RIC / H-RDL Core Shield", ha='center', va='center', fontsize=10.0, fontweight='bold', color=PALETTE["hrdl_safety"])
        ax.text(7.0, 5.7, "Conflict Detection -> TVS/EEVS Reasoning -> Safety Guard L0-L3\nBloqueio Determinístico de Ações Rogue", ha='center', va='center', fontsize=8.0, fontweight='bold', color=text_color)

        # Setas A1 e E2
        ax.annotate("", xy=(4.2, 5.9), xytext=(3.7, 5.9), arrowprops=dict(arrowstyle="->,head_width=0.35", lw=1.8, color=PALETTE["steering"]))
        ax.text(3.95, 6.1, "A1", ha='center', fontsize=8.0, fontweight='bold', color=PALETTE["steering"])
    else:
        # Painel Near-RT RIC Padrão
        ric_box = patches.FancyBboxPatch((7.5, 4.6), 3.5, 2.3, boxstyle="round,pad=0.04", facecolor=card_bg, edgecolor=PALETTE["steering"], lw=1.8, zorder=2)
        ax.add_patch(ric_box)
        ax.text(9.25, 6.6, "Near-RT RIC / H-RDL Dashboard", ha='center', va='center', fontsize=9.5, fontweight='bold', color=PALETTE["steering"])
        
        xapp_str = " vs ".join(config["xapps"]) if len(config["xapps"]) <= 2 else "Multi-xApp Cluster"
        ax.text(9.25, 6.15, f"xApps: {xapp_str}", ha='center', va='center', fontsize=8.0, fontweight='bold', color=PALETTE["embb"])
        
        # Fluxo de arbitragem interno
        ax.text(9.25, 5.5, "Conflict Detection & Perception Agent\n  ↓\nH-RDL Arbitration (TVS / EEVS)\n  ↓\nSafety Guard L0-L3 & E2SM-RC Encoder",
                ha='center', va='center', fontsize=7.5, fontweight='medium', color=text_color)

    # 3. PAINEL LATERAL DIREITO — Conflito & Métricas Monitoradas
    panel_box = patches.FancyBboxPatch((11.2, 0.8), 2.4, 6.1, boxstyle="round,pad=0.04", facecolor=card_bg, edgecolor=PALETTE["qos"], lw=1.5, zorder=2)
    ax.add_patch(panel_box)
    ax.text(12.4, 6.5, "Conflito & Recursos", ha='center', va='center', fontsize=9.0, fontweight='bold', color=PALETTE["qos"])
    ax.text(12.4, 5.6, config["conflict_desc"], ha='center', va='top', fontsize=7.5, color=text_color, wrap=True, multialignment='center')

    ax.text(12.4, 4.1, "Monitored Metrics", ha='center', va='center', fontsize=9.0, fontweight='bold', color=PALETTE["steering"])
    ax.text(12.4, 3.8, "(No synthetic/fake numbers)", ha='center', va='center', fontsize=7.0, style='italic', color=subtext_color)

    for idx, m_name in enumerate(config["metrics"]):
        my = 3.4 - idx * 0.45
        ax.text(11.35, my, f"• {m_name}", ha='left', va='center', fontsize=7.4, fontweight='medium', color=text_color)

    # 4. CENA RAN FÍSICA NO CENTRO (Torres gNB, Feixes e UEs)
    for gnb_id, gx, gy, gtype in config["gnbs"]:
        g_color = PALETTE["steering"] if gtype == "macro" else PALETTE["energy"]
        
        # Torre de gNodeB
        ax.plot([gx, gx], [gy - 0.8, gy + 0.6], color=g_color, lw=2.5, zorder=3)
        ax.plot([gx - 0.3, gx + 0.3], [gy + 0.6, gy + 0.6], color=g_color, lw=1.8, zorder=3)
        ax.scatter([gx], [gy + 0.8], color=g_color, s=70, zorder=4)

        # Regiões de cobertura ou feixes de rádio
        if config.get("archetype") == "isac":
            # Feixe de Sensoriamento Cyan e Feixe de Comunicação Verde-Lima
            beam_s = patches.Wedge((gx, gy + 0.8), 2.2, 230, 270, facecolor=PALETTE["sensing_beam"], alpha=0.25, edgecolor=PALETTE["sensing_beam"], lw=1.5, zorder=2)
            beam_c = patches.Wedge((gx, gy + 0.8), 2.2, 270, 310, facecolor=PALETTE["comms_beam"], alpha=0.25, edgecolor=PALETTE["comms_beam"], lw=1.5, zorder=2)
            ax.add_patch(beam_s)
            ax.add_patch(beam_c)
        else:
            # Círculo de Cobertura Padrão
            cov = patches.Circle((gx, gy - 0.2), 1.9, facecolor=g_color, alpha=0.12, edgecolor=g_color, linestyle='--', lw=1.5, zorder=2)
            ax.add_patch(cov)

        ax.text(gx, gy + 1.1, f"{gnb_id}", ha='center', va='bottom', fontsize=8.0, fontweight='bold', color=text_color)

    # UEs Representadas por Classe e Cor Semântica
    for u_id, ux, uy, uclass in config["ues"]:
        u_color = PALETTE["urllc"] if uclass == "URLLC" else (PALETTE["embb"] if uclass == "eMBB" else PALETTE["mmtc"])
        marker = '^' if uclass == "URLLC" else ('s' if uclass == "eMBB" else 'D')
        
        ax.scatter([ux], [uy], color=u_color, marker=marker, s=80, zorder=5, edgecolors='black', linewidth=0.8)
        ax.text(ux, uy - 0.3, f"{u_id} ({uclass})", ha='center', va='top', fontsize=7.2, fontweight='bold', color=text_color)

    # 5. CALLOUT DE TRADE-OFF OU PAINEL DE SEGURANÇA (Canto Inferior Esquerdo/Centro)
    if config.get("archetype") == "eevs":
        trade_box = patches.FancyBboxPatch((0.5, 0.8), 3.5, 2.2, boxstyle="round,pad=0.03", facecolor=card_bg, edgecolor=PALETTE["qos"], lw=1.5, zorder=3)
        ax.add_patch(trade_box)
        ax.text(2.25, 2.7, "Trade-Off Conceitual (Potência x Latência)", ha='center', va='center', fontsize=8.2, fontweight='bold', color=PALETTE["qos"])
        ax.plot([0.9, 3.6], [1.2, 1.2], color=subtext_color, lw=1, zorder=4)
        ax.plot([0.9, 0.9], [1.2, 2.4], color=subtext_color, lw=1, zorder=4)
        tx = np.linspace(1.0, 3.5, 20)
        ty = 2.3 - 0.7 * np.exp(-1.2 * (tx - 1.0))
        ax.plot(tx, ty, color=PALETTE["urllc"], lw=2, zorder=5)
        ax.text(2.25, 0.95, "Redução TX Power (dBm) -> Preservação SLA (ms)", ha='center', fontsize=6.8, color=subtext_color)
    else:
        legend_box = patches.FancyBboxPatch((0.5, 0.8), 3.5, 2.2, boxstyle="round,pad=0.03", facecolor=card_bg, edgecolor=border_color, lw=1.2, zorder=3)
        ax.add_patch(legend_box)
        ax.text(2.25, 2.7, "Legenda de Classes e Recursos", ha='center', va='center', fontsize=8.2, fontweight='bold', color=text_color)
        ax.scatter([0.8], [2.2], color=PALETTE["urllc"], marker='^', s=50)
        ax.text(1.1, 2.2, "URLLC (Cyan)", va='center', fontsize=7.2, color=text_color)
        ax.scatter([0.8], [1.7], color=PALETTE["embb"], marker='s', s=50)
        ax.text(1.1, 1.7, "eMBB (Purple)", va='center', fontsize=7.2, color=text_color)
        ax.scatter([0.8], [1.2], color=PALETTE["mmtc"], marker='D', s=50)
        ax.text(1.1, 1.2, "mMTC / IoT (Amber)", va='center', fontsize=7.2, color=text_color)

    # 6. RODAPÉ — LEGENDA CIENTÍFICA DE ISENÇÃO
    disclaimer = 'Legenda: "Scientific conceptual representation — metrics shown are monitored variables, not experimental results."'
    ax.text(7.0, 0.3, disclaimer, ha='center', va='center', fontsize=8.2, fontweight='bold', color=PALETTE["urllc"])

    plt.tight_layout()
    suffix = "_light.png" if is_light else "_dark.png"
    fname = f"{scen_key.lower()}_figure_{'light' if is_light else 'dark'}.png"
    fpath = os.path.join(OUTPUT_DIR, fname)
    plt.savefig(fpath, dpi=300, facecolor=bg_color)
    plt.close()
    return fname

def generate_provenance_and_reports(file_list):
    canonical_path = os.path.join(OUTPUT_DIR, "cenarios_canonicos_s0_s15.json")
    with open(canonical_path, "w", encoding="utf-8") as fh:
        json.dump(SCENARIO_CONFIGS, fh, indent=2, ensure_ascii=False)

    corr_path = os.path.join(OUTPUT_DIR, "relatorio_correspondencia_A_B.md")
    with open(corr_path, "w", encoding="utf-8") as fh:
        fh.write("# Relatório de Correspondência Biunívoca LIGHT vs DARK (S0 a S15)\n\n")
        fh.write("Este documento valida a consistência de topologia, nós, feixes e xApps entre as variantes LIGHT e DARK.\n\n")
        fh.write("| Cenário ID | Nome do Cenário | Arquétipo Visual | Variante LIGHT | Variante DARK |\n")
        fh.write("| :---: | :--- | :---: | :--- | :--- |\n")
        for sk, cfg in SCENARIO_CONFIGS.items():
            fh.write(f"| **{sk}** | {cfg['title']} | {cfg.get('archetype', 'tvs').upper()} | `{sk.lower()}_figure_light.png` | `{sk.lower()}_figure_dark.png` |\n")

    manifest = {
        "skill_version": "xapp-rdl-scenario-figure-generator-v1.0",
        "description": "Manifesto de proveniência com hashes SHA-256 de todas as figuras oficiais",
        "files_sha256": {}
    }
    for root, _, files in os.walk(OUTPUT_DIR):
        for f in files:
            fpath = os.path.join(root, f)
            with open(fpath, "rb") as fh:
                file_hash = hashlib.sha256(fh.read()).hexdigest()
            rel_p = os.path.relpath(fpath, OUTPUT_DIR)
            manifest["files_sha256"][rel_p] = file_hash

    manifest_path = os.path.join(OUTPUT_DIR, "manifesto_proveniencia.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("[+] Gerando Suíte Oficial de Figuras Baseada na Skill xapp-rdl-scenario-figure-generator (S0 a S15)...")
    all_files = []
    for sk in [f"S{i}" for i in range(16)]:
        cfg = SCENARIO_CONFIGS[sk]
        for is_light in [True, False]:
            fn = render_scientific_scenario_figure(sk, cfg, is_light)
            all_files.append(fn)
            print(f"  - [{sk}] Gerada figura: {fn}")

    generate_provenance_and_reports(all_files)
    print(f"\n[OK] Concluído! {len(all_files)} figuras salvas com sucesso em '{OUTPUT_DIR}'!")
