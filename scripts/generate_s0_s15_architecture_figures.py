#!/usr/bin/env python3
"""
Script de Geração da Suíte Oficial de Figuras Científicas XApp-RDL (S0 a S15).
Gera 32 figuras de alta resolução (300 DPI, 16:9, padrão IEEE/ACM) em docs/figures/02_cenarios_e_topologias/:
- 16 Versões em Tema Claro (Light) para artigos e dissertação
- 16 Versões em Tema Escuro (Dark) para apresentações

REGRA CIENTÍFICA ABSOLUTA: ZERO DADOS SINTÉTICOS OU NÚMEROS FAKE NAS FIGURAS.
Apenas nomes de métricas monitoradas, arquitetura visual, topologia RAN, pilha Near-RT RIC / H-RDL,
fluxo de telemetria/controle E2 e timeline de eventos.

Autor: Dr. George Alexandro Ferreira Barbosa
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_DIR = os.path.join("docs", "figures", "02_cenarios_e_topologias")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dados dos 16 cenários S0 a S15 baseados no Prompt Master
SCENARIO_SPECS = {
    "S0": {
        "title": "XApp-RDL Experimental Scenario S0 — No-Conflict Control",
        "phase": "Fase 1 (Experimental)",
        "topology_desc": "2 gNodeBs, 30 UEs (3.5 GHz) — Células Sobrepostas",
        "xapps": ["QoS/Slicing xApp", "Traffic Steering xApp"],
        "conflict": "Sem conflito: propostas compatíveis entre fatias e direção de tráfego.",
        "nodes": [
            ("gNB-Macro-01", 1.2, 3.2, 2.2, 1.4, '#1D4ED8', '#EFF6FF', '#1E3A8A'),
            ("gNB-Macro-02", 4.0, 3.2, 2.2, 1.4, '#047857', '#ECFDF5', '#064E3B'),
            ("UE Pool (30 UEs)", 2.4, 0.9, 2.6, 1.2, '#B45309', '#FEF3C7', '#451A03'),
        ],
        "arrows": [
            (2.3, 3.2, 3.0, 2.1, "Enlace NR 3.5GHz", '#1D4ED8'),
            (5.1, 3.2, 4.4, 2.1, "Enlace NR 3.5GHz", '#047857'),
        ],
        "metrics": [
            "False positive rate", "Specificity", "Added decision latency",
            "Throughput delta", "SLA violations count"
        ],
        "f1_stack": True,
        "is_future": False,
        "bg_msg": "H-RDL must not interfere when no conflict exists."
    },
    "S1": {
        "title": "XApp-RDL Experimental Scenario S1 — Direct PRB Conflict",
        "phase": "Fase 1 (Experimental)",
        "topology_desc": "1 gNodeB, 20 UEs — Alta Carga de Tráfego",
        "xapps": ["QoS/Slicing xApp", "Energy Saving xApp"],
        "conflict": "Conflito direto sobre quota de PRBs na mesma célula.",
        "nodes": [
            ("gNB-Macro (Célula Única)", 2.2, 3.2, 3.2, 1.4, '#BE123C', '#FFE4E6', '#4C0519'),
            ("UE Pool High-Load (20 UEs)", 2.2, 0.9, 3.2, 1.2, '#1D4ED8', '#EFF6FF', '#1E3A8A'),
        ],
        "arrows": [
            (3.8, 3.2, 3.8, 2.1, "Disputa Alocação PRB (Wc=200ms)", '#BE123C'),
        ],
        "metrics": [
            "Precision / Recall / F1-score", "Detection latency",
            "PRB utilization", "SLA violation duration", "Recovery time"
        ],
        "f1_stack": True,
        "is_future": False,
        "bg_msg": "Direct PRB resource allocation dispute resolution."
    },
    "S2": {
        "title": "XApp-RDL Experimental Scenario S2 — Energy Saving × QoS",
        "phase": "Fase 1 (Experimental)",
        "topology_desc": "Macro gNodeB + Micro/Small Cell (20 UEs, 3.5 GHz)",
        "xapps": ["Energy Saving xApp", "QoS/Slicing xApp"],
        "conflict": "Energy solicita cell sleep versus QoS requer capacidade URLLC.",
        "nodes": [
            ("Macro gNB (Alta Potência)", 1.0, 3.2, 2.6, 1.4, '#047857', '#ECFDF5', '#064E3B'),
            ("Small Cell (Micro Cobertura)", 4.0, 3.2, 2.6, 1.4, '#7E22CE', '#F3E8FF', '#2E1065'),
            ("Usuários URLLC / eMBB", 2.5, 0.9, 2.6, 1.2, '#1D4ED8', '#EFF6FF', '#1E3A8A'),
        ],
        "arrows": [
            (2.3, 3.2, 3.2, 2.1, "Solicitação Cell Sleep", '#047857'),
            (5.3, 3.2, 4.4, 2.1, "Garantia SLA URLLC", '#7E22CE'),
        ],
        "metrics": [
            "Energy consumption", "URLLC P99 latency", "Packet loss",
            "Throughput", "PRB utilization", "SLA violation duration"
        ],
        "f1_stack": True,
        "is_future": False,
        "bg_msg": "Trade-off entre consumo energético e SLA URLLC."
    },
    "S3": {
        "title": "XApp-RDL Experimental Scenario S3 — Traffic Steering × Slicing",
        "phase": "Fase 1 (Experimental)",
        "topology_desc": "2 gNodeBs, 30 UEs (100 MHz) — Fatias URLLC, eMBB e mMTC",
        "xapps": ["Traffic Steering xApp", "QoS/Slicing xApp"],
        "conflict": "Steering altera carga de células enquanto Slicing preserva quotas de fatia.",
        "nodes": [
            ("gNB-A (Fatia eMBB/URLLC)", 1.0, 3.2, 2.6, 1.4, '#B45309', '#FEF3C7', '#451A03'),
            ("gNB-B (Fatia mMTC/eMBB)", 4.0, 3.2, 2.6, 1.4, '#1D4ED8', '#EFF6FF', '#1E3A8A'),
            ("Pool de Fatias Heterogêneas", 2.5, 0.9, 2.6, 1.2, '#047857', '#ECFDF5', '#064E3B'),
        ],
        "arrows": [
            (2.3, 3.2, 3.2, 2.1, "Comando Handover Steering", '#B45309'),
            (5.3, 3.2, 4.4, 2.1, "Preservação de Quotas SLA", '#1D4ED8'),
        ],
        "metrics": [
            "P99 URLLC latency", "eMBB throughput", "mMTC packet delivery",
            "PRB share", "Jain fairness", "SLA violations count"
        ],
        "f1_stack": True,
        "is_future": False,
        "bg_msg": "Preservação de SLAs multi-fatia sob steering dinâmico."
    },
    "S4": {
        "title": "XApp-RDL Experimental Scenario S4 — Traffic Steering × Energy Saving",
        "phase": "Fase 1 (Experimental)",
        "topology_desc": "2 gNodeBs, 40 UEs — gNB-A Congestionado, gNB-B Low-Power",
        "xapps": ["Traffic Steering xApp", "Energy Saving xApp"],
        "conflict": "TS pretende mover UEs A->B enquanto ES pretende colocar B em sleep.",
        "nodes": [
            ("gNB-A (Overloaded)", 1.0, 3.2, 2.5, 1.4, '#BE123C', '#FFE4E6', '#4C0519'),
            ("gNB-B (Target Sleep)", 4.0, 3.2, 2.5, 1.4, '#047857', '#ECFDF5', '#064E3B'),
            ("Pool de UEs em Handover", 2.5, 0.9, 2.5, 1.2, '#B45309', '#FEF3C7', '#451A03'),
        ],
        "arrows": [
            (2.25, 3.2, 3.2, 2.1, "Handover A -> B", '#BE123C'),
            (5.25, 3.2, 4.3, 2.1, "Solicitação Sleep B", '#047857'),
        ],
        "metrics": [
            "Cell load", "HO success/failure rate", "Ping-pong rate",
            "Energy consumption", "Throughput", "Outage duration"
        ],
        "f1_stack": True,
        "is_future": False,
        "bg_msg": "Conflito entre descarregamento de tráfego e desligamento de célula."
    },
    "S5": {
        "title": "XApp-RDL Experimental Scenario S5 — Temporal Ping-Pong",
        "phase": "Fase 1 (Experimental)",
        "topology_desc": "2 Células Sobrepostas + UEs Móveis em Trajetória de Borda",
        "xapps": ["Traffic Steering / MRO xApp", "Energy / QoS xApp"],
        "conflict": "Decisões alternadas A->B->A em curto intervalo (Oscilação).",
        "nodes": [
            ("Cell A (Origem)", 1.0, 3.2, 2.5, 1.4, '#1D4ED8', '#EFF6FF', '#1E3A8A'),
            ("Cell B (Destino)", 4.0, 3.2, 2.5, 1.4, '#7E22CE', '#F3E8FF', '#2E1065'),
            ("UE em Trajetória Móvel", 2.5, 0.9, 2.5, 1.2, '#BE123C', '#FFE4E6', '#4C0519'),
        ],
        "arrows": [
            (2.25, 3.2, 3.2, 2.1, "Handover A -> B", '#1D4ED8'),
            (5.25, 3.2, 4.3, 2.1, "Reversão B -> A", '#7E22CE'),
        ],
        "metrics": [
            "Handover count", "Ping-pong rate", "Action reversal rate",
            "Control churn", "Dwell time", "Stable recovery time"
        ],
        "f1_stack": True,
        "is_future": False,
        "bg_msg": "Aplicação de hysteresis e cooldown para supressão de ping-pong."
    },
    "S6": {
        "title": "XApp-RDL Experimental Scenario S6 — Multi-xApp Conflict Storm",
        "phase": "Fase 1 (Experimental)",
        "topology_desc": "Múltiplas Células e Tráfego Heterogêneo (Escala 2 a 8 xApps)",
        "xapps": ["QoS/Slicing", "Traffic Steering", "Energy Saving", "Load Balancer", "Beamformer"],
        "conflict": "Múltiplas propostas simultâneas e dependências indiretas complexas.",
        "nodes": [
            ("Cluster Multi-Células", 1.0, 3.2, 2.5, 1.4, '#0891B2', '#E0F2FE', '#083344'),
            ("Conflict Graph Engine", 4.0, 3.2, 2.5, 1.4, '#BE123C', '#FFE4E6', '#4C0519'),
            ("Tráfego de Alta Intensidade", 2.5, 0.9, 2.5, 1.2, '#7E22CE', '#F3E8FF', '#2E1065'),
        ],
        "arrows": [
            (2.25, 3.2, 3.2, 2.1, "Tempestade de Mensagens RMR", '#0891B2'),
            (5.25, 3.2, 4.3, 2.1, "Resolução em Grafo", '#BE123C'),
        ],
        "metrics": [
            "Conflicts per second", "Decision throughput", "Queue depth",
            "CPU / Memory usage", "P95/P99 decision latency", "Rejected actions count"
        ],
        "f1_stack": True,
        "is_future": False,
        "bg_msg": "Avaliação de escalabilidade sob tempestade de conflitos simultâneos."
    },
    "S7": {
        "title": "XApp-RDL Experimental Scenario S7 — Fault / Rogue xApp / Adversarial Control",
        "phase": "Fase 1 (Experimental)",
        "topology_desc": "Infraestrutura Multi-Célula com Injeção de xApp Maliciosa/Defeituosa",
        "xapps": ["xApps Legítimas", "Rogue / Fault-Injection xApp"],
        "conflict": "Comandos obsoletos, duplicados, parâmetros inválidos ou fora de SLA.",
        "nodes": [
            ("gNB Multi-Cell Stack", 1.0, 3.2, 2.5, 1.4, '#047857', '#ECFDF5', '#064E3B'),
            ("Safety Guard L0-L3 Shield", 4.0, 3.2, 2.5, 1.4, '#BE123C', '#FFE4E6', '#4C0519'),
            ("Injetor de Erro / Rogue xApp", 2.5, 0.9, 2.5, 1.2, '#B45309', '#FEF3C7', '#451A03'),
        ],
        "arrows": [
            (2.25, 3.2, 3.2, 2.1, "Proposta Maliciosa/Stale", '#B45309'),
            (5.25, 3.2, 4.3, 2.1, "Bloqueio Determinístico L0", '#BE123C'),
        ],
        "metrics": [
            "Attack / fault rejection rate", "False acceptance rate",
            "Unsafe execution rate", "Isolation time", "SLA impact"
        ],
        "f1_stack": True,
        "is_future": False,
        "bg_msg": "Proteção determinística contra comportamento anômalo ou malicioso."
    },
    "S8": {
        "title": "XApp-RDL Experimental Scenario S8 — Real NORI Closed Loop",
        "phase": "Fase 1 (Experimental - Gates 1–4)",
        "topology_desc": "Co-Simulação ns-3 + 5G-LENA + NORI + E2 Real (Malha Fechada)",
        "xapps": ["KPM Monitor xApp", "Traffic Steering xApp", "H-RDL Core"],
        "conflict": "Validação de loop completo E2AP / E2SM-KPM / E2SM-RC via NORI.",
        "nodes": [
            ("ns-3 / 5G-LENA Simulation", 0.8, 3.2, 2.5, 1.4, '#1D4ED8', '#EFF6FF', '#1E3A8A'),
            ("NORI E2 Interface Node", 3.8, 3.2, 2.5, 1.4, '#047857', '#ECFDF5', '#064E3B'),
            ("RMR Router & H-RDL Core", 2.3, 0.9, 2.5, 1.2, '#7E22CE', '#F3E8FF', '#2E1065'),
        ],
        "arrows": [
            (2.05, 3.2, 3.05, 2.1, "E2SM-KPM Traces (t0)", '#1D4ED8'),
            (5.05, 3.2, 4.05, 2.1, "E2SM-RC Control (t1)", '#047857'),
        ],
        "metrics": [
            "KPM report rate", "Control RTT", "Action application latency",
            "KPI before / after delta", "ACK / Failure rate"
        ],
        "f1_stack": True,
        "is_future": False,
        "bg_msg": "External raw E2 evidence required for closed-loop validation."
    },
    "S9": {
        "title": "XApp-RDL Future Scenario S9 — NTN Terrestrial–Satellite Conflict",
        "phase": "Fase 2 / 6G (Cenário Futuro)",
        "topology_desc": "gNodeB Terrestre + Satélite LEO + Feixe NTN em Movimento",
        "xapps": ["NTN Steering xApp", "QoS / Latency Slicing", "Load Balancer"],
        "conflict": "Seleção Terrestre/NTN vs Latência RTT, Capacidade e Efeito Doppler.",
        "nodes": [
            ("Satélite LEO Orbital", 1.0, 3.2, 2.5, 1.4, '#7E22CE', '#F3E8FF', '#2E1065'),
            ("gNB Terrestre / Gateway", 4.0, 3.2, 2.5, 1.4, '#047857', '#ECFDF5', '#064E3B'),
            ("Estação de Solo & UE NTN", 2.5, 0.9, 2.5, 1.2, '#1D4ED8', '#EFF6FF', '#1E3A8A'),
        ],
        "arrows": [
            (2.25, 3.2, 3.2, 2.1, "Feixe NTN Doppler", '#7E22CE'),
            (5.25, 3.2, 4.3, 2.1, "Backhaul Terrestre", '#047857'),
        ],
        "metrics": [
            "RTT latency", "Doppler shift compensation", "Elevation angle",
            "Handover count", "Outage probability", "Slice SLA"
        ],
        "f1_stack": False,
        "is_future": True,
        "bg_msg": "Future validation scenario: NTN LEO handover & latency arbitration."
    },
    "S10": {
        "title": "XApp-RDL Future Scenario S10 — UAV / Flying gNB / Swarm",
        "phase": "Fase 2 / 6G (Cenário Futuro)",
        "topology_desc": "gNodeB Terrestre + Enxame de UAVs / gNBs Aéreos Relays",
        "xapps": ["UAV Mobility xApp", "Energy Saving xApp", "Load Balancer"],
        "conflict": "Demanda de cobertura em emergência vs Nível de Bateria (SoC).",
        "nodes": [
            ("UAV Enxame Aéreo 01", 1.0, 3.2, 2.5, 1.4, '#B45309', '#FEF3C7', '#451A03'),
            ("UAV Enxame Aéreo 02", 4.0, 3.2, 2.5, 1.4, '#047857', '#ECFDF5', '#064E3B'),
            ("Usuários Terrestres Isolados", 2.5, 0.9, 2.5, 1.2, '#1D4ED8', '#EFF6FF', '#1E3A8A'),
        ],
        "arrows": [
            (2.25, 3.2, 3.2, 2.1, "Relay Aéreo 3D", '#B45309'),
            (5.25, 3.2, 4.3, 2.1, "Reconfiguração de Malha", '#047857'),
        ],
        "metrics": [
            "State of Charge (SoC)", "Coverage probability", "Outage duration",
            "UAV Handovers", "Mesh recovery time", "Energy consumption"
        ],
        "f1_stack": False,
        "is_future": True,
        "bg_msg": "Future validation scenario: Dynamic UAV mesh coverage & SoC management."
    },
    "S11": {
        "title": "XApp-RDL Future Scenario S11 — V2X High-Mobility Platoon",
        "phase": "Fase 2 / 6G (Cenário Futuro)",
        "topology_desc": "Corredor Rodoviário Urbano (110 km/h), RSUs e Pelotão Veicular URLLC",
        "xapps": ["Traffic Steering xApp", "Mobility / MRO xApp", "Platoon QoS xApp"],
        "conflict": "Handover ultra-rápido na região de overlap vs Tolerância Zero de Sinal.",
        "nodes": [
            ("RSU Rodoviária 01", 1.0, 3.2, 2.5, 1.4, '#BE123C', '#FFE4E6', '#4C0519'),
            ("RSU Rodoviária 02", 4.0, 3.2, 2.5, 1.4, '#1D4ED8', '#EFF6FF', '#1E3A8A'),
            ("Pelotão Veicular V2X", 2.5, 0.9, 2.5, 1.2, '#047857', '#ECFDF5', '#064E3B'),
        ],
        "arrows": [
            (2.25, 3.2, 3.2, 2.1, "Telemetria V2X Ultra-Fast", '#BE123C'),
            (5.25, 3.2, 4.3, 2.1, "Cota URLLC Reservada", '#1D4ED8'),
        ],
        "metrics": [
            "Handover failure rate", "Interruption time", "Ping-pong rate",
            "RSRP / RSRQ / SINR", "URLLC latency tail", "Platoon SLA"
        ],
        "f1_stack": False,
        "is_future": True,
        "bg_msg": "Future validation scenario: Ultra-low latency V2X platoon slicing."
    },
    "S12": {
        "title": "XApp-RDL Future Scenario S12 — IIoT / TSN Mission-Critical",
        "phase": "Fase 2 / 6G (Cenário Futuro)",
        "topology_desc": "Ambiente Fabril Inteligente / 5G Privado com Tráfego TSN Determinístico",
        "xapps": ["Industrial QoS xApp", "Energy Saving xApp", "Load Balancer"],
        "conflict": "Reserva estrita TSN industrial vs Eficiência energética/capacidade.",
        "nodes": [
            ("Sensores TSN Fabris", 1.0, 3.2, 2.5, 1.4, '#0891B2', '#E0F2FE', '#083344'),
            ("gNB-DU Industrial TSN", 4.0, 3.2, 2.5, 1.4, '#7E22CE', '#F3E8FF', '#2E1065'),
            ("Robôs & Atuadores TSN", 2.5, 0.9, 2.5, 1.2, '#047857', '#ECFDF5', '#064E3B'),
        ],
        "arrows": [
            (2.25, 3.2, 3.2, 2.1, "Tráfego TSN Determinístico", '#0891B2'),
            (5.25, 3.2, 4.3, 2.1, "Escalonamento Sem Jitter", '#7E22CE'),
        ],
        "metrics": [
            "Control-cycle latency", "Jitter bounds", "Missed control cycles",
            "Packet loss rate", "Availability percentage", "Energy efficiency"
        ],
        "f1_stack": False,
        "is_future": True,
        "bg_msg": "Future validation scenario: Deterministic TSN industrial SLA lock."
    },
    "S13": {
        "title": "XApp-RDL 6G Scenario S13 — SAGIN Multi-Domain",
        "phase": "Fase 3 / 6G (Cenário Avançado)",
        "topology_desc": "Arquitetura 3D Multidomínio: Espacial (LEO) + Aérea (UAV) + Terrestre (O-RAN)",
        "xapps": ["NTN Steering", "UAV Coordination", "QoS Slicing", "Energy Saving"],
        "conflict": "Escassez severa de backhaul vs Priorização de serviços de resgate.",
        "nodes": [
            ("Camada Espacial (LEO)", 1.0, 3.2, 2.5, 1.4, '#BE123C', '#FFE4E6', '#4C0519'),
            ("Camada Terrestre O-RAN", 4.0, 3.2, 2.5, 1.4, '#1D4ED8', '#EFF6FF', '#1E3A8A'),
            ("Enxame Aéreo UAV Relay", 2.5, 0.9, 2.5, 1.2, '#047857', '#ECFDF5', '#064E3B'),
        ],
        "arrows": [
            (2.25, 3.2, 3.2, 2.1, "Backhaul SAGIN", '#BE123C'),
            (5.25, 3.2, 4.3, 2.1, "Link Terrestre Resgate", '#1D4ED8'),
        ],
        "metrics": [
            "Cross-tier latency", "Multi-domain availability", "Critical SLA compliance",
            "Resource allocation efficiency", "Recovery time", "Fairness index"
        ],
        "f1_stack": False,
        "is_future": True,
        "bg_msg": "6G multi-domain SAGIN orchestration & emergency SLA resilience."
    },
    "S14": {
        "title": "XApp-RDL 6G Scenario S14 — ISAC Sensing × Communication",
        "phase": "Fase 3 / 6G (Cenário Avançado)",
        "topology_desc": "gNodeBs 6G de Dupla Função: Sensoriamento RF de Alvos + Comunicação",
        "xapps": ["ISAC / Sensing xApp", "eMBB / QoS xApp", "Beamformer xApp"],
        "conflict": "Disputa por símbolos OFDM, feixes, tempo/frequência e potência de TX.",
        "nodes": [
            ("Sensing Target / Radar", 1.0, 3.2, 2.5, 1.4, '#BE123C', '#FFE4E6', '#4C0519'),
            ("6G ISAC Dual-gNB", 4.0, 3.2, 2.5, 1.4, '#1D4ED8', '#EFF6FF', '#1E3A8A'),
            ("Usuários de Comunicação 6G", 2.5, 0.9, 2.5, 1.2, '#047857', '#ECFDF5', '#064E3B'),
        ],
        "arrows": [
            (2.25, 3.2, 3.2, 2.1, "Feixe de Sensoriamento RF", '#BE123C'),
            (5.25, 3.2, 4.3, 2.1, "Feixe de Dados Comms", '#1D4ED8'),
        ],
        "metrics": [
            "Sensing accuracy / range error", "Radar SINR", "Communication SINR",
            "Throughput", "Latency", "Pareto optimal trade-off frontier"
        ],
        "f1_stack": False,
        "is_future": True,
        "bg_msg": "6G Joint Sensing and Communication (ISAC) resource co-optimization."
    },
    "S15": {
        "title": "XApp-RDL 6G Scenario S15 — Cross-Tier Governance & Anti-Rogue",
        "phase": "Fase 3 / 6G (Cenário Avançado)",
        "topology_desc": "Governança Multi-Loop: Non-RT RIC / SMO -> Near-RT RIC / H-RDL -> E2 Nodes",
        "xapps": ["QoS", "Traffic Steering", "Energy", "Load Balancer", "Beamformer", "ISAC", "Rogue xApp"],
        "conflict": "Conflitos multinível cross-tier com injeção anômala em malhas concorrentes.",
        "nodes": [
            ("SMO / Non-RT RIC Policy", 1.0, 3.2, 2.5, 1.4, '#7E22CE', '#F3E8FF', '#2E1065'),
            ("H-RDL Anti-Rogue Shield", 4.0, 3.2, 2.5, 1.4, '#047857', '#ECFDF5', '#064E3B'),
            ("E2 Nodes & Multi-Domain RAN", 2.5, 0.9, 2.5, 1.2, '#BE123C', '#FFE4E6', '#4C0519'),
        ],
        "arrows": [
            (2.25, 3.2, 3.2, 2.1, "Políticas rApp Non-RT", '#7E22CE'),
            (5.25, 3.2, 4.3, 2.1, "Validação Safety Guard L0-L3", '#047857'),
        ],
        "metrics": [
            "Unsafe execution rate", "Rogue / fault block rate", "False positive rate",
            "Detection latency", "Lockout duration", "PDR stability"
        ],
        "f1_stack": False,
        "is_future": True,
        "bg_msg": "6G Cross-tier multi-loop governance & deterministic anti-rogue protection."
    }
}

def draw_box(ax, x, y, w, h, title, subtitle="", color='#1E3A8A', fill='#F8FAFC', text_color='#0F172A', subtext_color='#334155'):
    rect = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.03,rounding_size=0.06",
        linewidth=1.8, edgecolor=color, facecolor=fill, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h * 0.62 if subtitle else y + h * 0.5, title, ha='center', va='center', fontsize=9.5, fontweight='bold', color=text_color, zorder=4)
    if subtitle:
        ax.text(x + w / 2, y + h * 0.28, subtitle, ha='center', va='center', fontsize=8.0, color=subtext_color, fontweight='medium', zorder=4)

def draw_arrow(ax, x1, y1, x2, y2, label="", color='#1D4ED8', bg_color='#FFFFFF', linestyle='-'):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->,head_width=0.35,head_length=0.5", lw=1.8, color=color, linestyle=linestyle), zorder=2)
    if label:
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mid_x, mid_y + 0.1, label, ha='center', va='bottom', fontsize=8.0, fontweight='bold', color=color,
                bbox=dict(boxstyle="square,pad=0.15", facecolor=bg_color, edgecolor='none', alpha=0.9), zorder=5)

def render_scenario_master(scenario_key, spec, is_light=True):
    bg_color = '#FFFFFF' if is_light else '#0F172A'
    card_bg = '#F8FAFC' if is_light else '#1E293B'
    text_color = '#0F172A' if is_light else '#F8FAFC'
    subtext_color = '#334155' if is_light else '#94A3B8'
    accent_blue = '#1D4ED8' if is_light else '#3B82F6'
    accent_green = '#047857' if is_light else '#10B981'
    accent_red = '#BE123C' if is_light else '#F43F5E'
    accent_purple = '#7E22CE' if is_light else '#A855F7'

    fig, ax = plt.subplots(figsize=(14, 8), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # 1. TOPO: Título Oficial do Cenário
    title_prefix = spec['title']
    ax.text(7.0, 7.6, title_prefix, ha='center', va='center', fontsize=13.0, fontweight='bold', color=text_color)
    ax.text(7.0, 7.25, f"Fase: {spec['phase']} | Topologia Dominante: {spec['topology_desc']}", ha='center', va='center', fontsize=9.5, fontweight='medium', color=subtext_color)

    # 2. CANTO SUPERIOR DIREITO: Pilha Near-RT RIC + H-RDL
    ric_box = patches.FancyBboxPatch((7.2, 3.2), 3.4, 3.6, boxstyle="round,pad=0.04", facecolor=card_bg, edgecolor=accent_blue, lw=2, zorder=2)
    ax.add_patch(ric_box)
    ax.text(8.9, 6.5, "Near-RT RIC (O-RAN SC)", ha='center', va='center', fontsize=10.0, fontweight='bold', color=text_color)

    # xApps no RIC
    xapp_str = " vs ".join(spec['xapps']) if len(spec['xapps']) <= 3 else "Multi-xApp Cluster"
    ax.text(8.9, 6.0, f"xApps: {xapp_str}", ha='center', va='center', fontsize=8.2, fontweight='bold', color=accent_purple)
    
    # Etapas H-RDL
    steps = [
        ("Perception: Conflict Detection", '#3B82F6'),
        ("Reasoning: TVS/EEVS Optimization", '#10B981'),
        ("Refinement & Safety Guard L0-L3", '#F59E0B'),
        ("E2SM-RC Control Encoder", '#EF4444')
    ]
    for idx, (s_name, s_col) in enumerate(steps):
        sy = 5.4 - idx * 0.6
        s_rect = patches.FancyBboxPatch((7.5, sy - 0.2), 2.8, 0.42, boxstyle="round,pad=0.02", facecolor=bg_color, edgecolor=s_col, lw=1.2, zorder=3)
        ax.add_patch(s_rect)
        ax.text(8.9, sy, s_name, ha='center', va='center', fontsize=7.8, fontweight='bold', color=text_color, zorder=4)

    # Setas de fluxo interno H-RDL
    for idx in range(3):
        sy = 5.18 - idx * 0.6
        ax.annotate("", xy=(8.9, sy - 0.2), xytext=(8.9, sy), arrowprops=dict(arrowstyle="->,head_width=0.3", lw=1.5, color=subtext_color), zorder=4)

    # 3. LATERAL DIREITA: Painel "Conflict under Evaluation" & "Monitored Metrics"
    panel_box = patches.FancyBboxPatch((10.8, 0.8), 3.0, 6.0, boxstyle="round,pad=0.04", facecolor=card_bg, edgecolor=accent_red, lw=1.5, zorder=2)
    ax.add_patch(panel_box)
    ax.text(12.3, 6.5, "Conflict under Evaluation", ha='center', va='center', fontsize=9.5, fontweight='bold', color=accent_red)
    
    # Texto formatado do conflito
    conf_text = spec['conflict']
    ax.text(12.3, 5.7, conf_text, ha='center', va='top', fontsize=7.8, color=text_color, wrap=True, multialignment='center')

    ax.text(12.3, 4.3, "Monitored Metrics", ha='center', va='center', fontsize=9.5, fontweight='bold', color=accent_blue)
    ax.text(12.3, 4.0, "(No synthetic/mock numbers)", ha='center', va='center', fontsize=7.2, style='italic', color=subtext_color)

    for idx, m_name in enumerate(spec['metrics']):
        my = 3.6 - idx * 0.4
        ax.text(11.0, my, f"• {m_name}", ha='left', va='center', fontsize=7.6, fontweight='medium', color=text_color)

    # 4. PAINEL DE CO-SIMULAÇÃO (Fase 1 vs Futuro)
    if spec['f1_stack']:
        stack_box = patches.FancyBboxPatch((0.4, 5.6), 6.5, 1.2, boxstyle="round,pad=0.03", facecolor=card_bg, edgecolor=accent_green, lw=1.5, zorder=2)
        ax.add_patch(stack_box)
        ax.text(3.65, 6.4, "Fluxo Experimental Fase 1 (E2 Closed-Loop Stack)", ha='center', va='center', fontsize=9.0, fontweight='bold', color=accent_green)
        ax.text(3.65, 5.95, "ns-3 / 5G-LENA  <--->  NORI (E2 Node)  <--->  E2AP/E2SM  <--->  Near-RT RIC / H-RDL", ha='center', va='center', fontsize=8.0, fontweight='bold', color=text_color)

    # 5. CENTRO: Topologia RAN Dominante
    for title, nx, ny, nw, nh, c_border, c_fill, c_txt in spec['nodes']:
        draw_box(ax, nx, ny, nw, nh, title, "", c_border, c_fill if is_light else '#1E293B', text_color, subtext_color)

    for x1, y1, x2, y2, lbl, col in spec['arrows']:
        draw_arrow(ax, x1, y1, x2, y2, lbl, col, bg_color)

    # Setas Globais Telemetria (KPM) e Controle (RC)
    draw_arrow(ax, 2.5, 4.6, 7.2, 4.6, "Telemetria E2SM-KPM (Dashed)", accent_blue, bg_color, linestyle='--')
    draw_arrow(ax, 7.2, 4.0, 2.5, 4.0, "Ação de Controle E2SM-RC (Solid)", accent_green, bg_color, linestyle='-')

    # 6. INFERIOR: Timeline Event-Driven (t_conflict ... t_recovery)
    time_box = patches.FancyBboxPatch((0.4, 0.8), 10.2, 1.8, boxstyle="round,pad=0.03", facecolor=card_bg, edgecolor=subtext_color, lw=1.2, zorder=2)
    ax.add_patch(time_box)
    ax.text(5.5, 2.3, "Timeline Experimental & Marcadores de Transição de Estado", ha='center', va='center', fontsize=9.0, fontweight='bold', color=text_color)

    stages = [
        ("BASELINE", "t0", 1.2),
        ("PRE-CONFLICT", "t_pre", 2.8),
        ("CONFLICT", "t_conflict", 4.4),
        ("MITIGATION", "t_detect/t_dec", 6.0),
        ("RECOVERY", "t_ACK/t_effect", 7.6),
        ("STEADY STATE", "t_recovery", 9.2)
    ]
    ax.plot([1.2, 9.2], [1.4, 1.4], color=subtext_color, lw=2, zorder=3)
    for st_name, st_t, st_x in stages:
        st_color = accent_red if st_name == "CONFLICT" else (accent_green if st_name in ["MITIGATION", "RECOVERY"] else accent_blue)
        ax.scatter([st_x], [1.4], color=st_color, s=40, zorder=4)
        ax.text(st_x, 1.7, st_name, ha='center', va='center', fontsize=7.5, fontweight='bold', color=st_color)
        ax.text(st_x, 1.1, st_t, ha='center', va='center', fontsize=7.0, color=subtext_color)

    # 7. RODAPÉ: Legenda de Isenção Científica
    disclaimer = 'Legenda: "Experimental scenario — metrics shown are monitored variables, not experimental results."'
    ax.text(7.0, 0.3, disclaimer, ha='center', va='center', fontsize=8.5, fontweight='bold', color=accent_red if is_light else '#F43F5E')

    plt.tight_layout()
    suffix = "_light.png" if is_light else "_dark.png"
    file_name = f"{scenario_key.lower()}_{spec['title'].split(' Scenario ')[1].split(' — ')[1].lower().replace(' ', '_').replace('/', '_').replace('×', 'vs').replace('-', '_')}{suffix}"
    
    # Simplificação padronizada de nome do arquivo
    clean_name = f"{scenario_key.lower()}_architecture_{'light' if is_light else 'dark'}.png"
    file_path = os.path.join(OUTPUT_DIR, clean_name)
    plt.savefig(file_path, dpi=300, facecolor=bg_color)
    plt.close()
    return clean_name

if __name__ == "__main__":
    print("[+] Gerando Suíte Oficial de 32 Figuras Científicas XApp-RDL (S0 a S15)...")
    generated_files = []
    for s_key in [f"S{i}" for i in range(16)]:
        spec = SCENARIO_SPECS[s_key]
        for is_light in [True, False]:
            fname = render_scenario_master(s_key, spec, is_light)
            generated_files.append(fname)
            print(f"  - [{s_key}] Gerada figura: {fname}")

    print(f"\n[OK] Concluído! {len(generated_files)} figuras salvas com sucesso em '{OUTPUT_DIR}'!")
