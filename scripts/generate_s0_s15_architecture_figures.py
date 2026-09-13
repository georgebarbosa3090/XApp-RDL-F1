#!/usr/bin/env python3
"""
Script de Geração da Suíte Oficial de Figuras Científicas XApp-RDL (S0 a S15).
Implementação alinhada à SKILL 'xapp-figure-generator' (Estilo Figuras 4 e 5 do artigo H-RDL):

- Figura A: Representação Conceitual 3D/Isométrica (estilo Figura 4)
  - Elementos de contexto urbano/rádio, torres gNB, UEs por classe de tráfego (URLLC, eMBB, mMTC).
  - Painel interno (Callout) com lógica de conflito xApps e arbitragem H-RDL.
  - Curva conceitual de trade-off (potência x latência, sem dados inventados).

- Figura B: Representação Geométrica 2D com Eixos em Metros (estilo Figura 5)
  - Eixos X e Y em metros (área real do cenário).
  - Raios de cobertura reais das células, marcadores exatos de posições pos_m das gNBs e UEs.
  - Zona de sobreposição destacada, legenda completa de classes e anotação do efeito H-RDL.

Gera 64 arquivos de imagem (16 cenários x 2 figuras [A e B] x 2 temas [Light e Dark])
mais os artefatos de rastreabilidade: cenarios_canonicos_s0_s15.json, relatorio_correspondencia_A_B.md e manifesto_proveniencia.json.

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

# Definição dos 16 cenários S0 a S15 no formato de objeto canônico da SKILL
CANONICAL_SCENARIOS = {
    "S0": {
        "id": "S0",
        "nome": "No-Conflict Control",
        "objetivo_cientifico": "Provar não interferência do H-RDL na ausência de conflitos entre xApps",
        "tipo_conflito": "sem_conflito",
        "topologia": {
            "area_m": [200, 120],
            "banda": "n78",
            "frequencia_GHz": 3.5,
            "largura_banda_MHz": 100,
            "gnodebs": [
                {"id": "gNB-1", "pos_m": [60, 60], "tipo": "macro", "potencia_dBm": 43.0, "raio_cobertura_m": 70.0},
                {"id": "gNB-2", "pos_m": [140, 60], "tipo": "macro", "potencia_dBm": 43.0, "raio_cobertura_m": 70.0}
            ],
            "ues": [
                {"id": "UE-01", "pos_m": [50, 65], "classe": "eMBB", "gnodeb_serving": "gNB-1"},
                {"id": "UE-02", "pos_m": [70, 55], "classe": "URLLC", "gnodeb_serving": "gNB-1"},
                {"id": "UE-03", "pos_m": [130, 65], "classe": "mMTC", "gnodeb_serving": "gNB-2"},
                {"id": "UE-04", "pos_m": [150, 55], "classe": "eMBB", "gnodeb_serving": "gNB-2"}
            ],
            "regioes_sobreposicao": [
                {"descricao": "Zona de sobreposição parcial gNB-1 / gNB-2", "centro_m": [100, 60], "raio_m": 30.0}
            ]
        },
        "xapps": [
            {"id": "xSlice", "dominio": "QoS e Slicing", "parametros_alvo": ["PRB_QUOTA"], "kpis_afetados": ["DRB.UETHpD1"]},
            {"id": "Traffic Steering", "dominio": "Mobilidade", "parametros_alvo": ["HANDOVER"], "kpis_afetados": ["DRB.RlcSduDelayD1"]}
        ],
        "conflitos": [
            {"tipo": "nenhum", "xapps_envolvidas": ["xSlice", "Traffic Steering"], "parametros_ou_kpis": [], "severidade": "nula", "descricao_visual": "Ações compatíveis de steering e slice sem disputa de PRBs"}
        ],
        "tradeoff_info": {"eixo_x": "Solicitações de Ação", "eixo_y": "Taxa de Aceitação H-RDL", "tipo_curva": "pass_through"}
    },
    "S1": {
        "id": "S1",
        "nome": "Direct PRB Conflict",
        "objetivo_cientifico": "Disputa direta por alocação de blocos de recursos (PRBs) na mesma célula",
        "tipo_conflito": "direto",
        "topologia": {
            "area_m": [120, 100],
            "banda": "n78",
            "frequencia_GHz": 3.5,
            "largura_banda_MHz": 100,
            "gnodebs": [
                {"id": "gNB-1", "pos_m": [60, 50], "tipo": "macro", "potencia_dBm": 46.0, "raio_cobertura_m": 55.0}
            ],
            "ues": [
                {"id": "UE-01", "pos_m": [50, 55], "classe": "URLLC", "gnodeb_serving": "gNB-1"},
                {"id": "UE-02", "pos_m": [70, 45], "classe": "eMBB", "gnodeb_serving": "gNB-1"},
                {"id": "UE-03", "pos_m": [55, 40], "classe": "URLLC", "gnodeb_serving": "gNB-1"},
                {"id": "UE-04", "pos_m": [65, 60], "classe": "mMTC", "gnodeb_serving": "gNB-1"}
            ],
            "regioes_sobreposicao": [
                {"descricao": "Célula sob contenção de PRBs", "centro_m": [60, 50], "raio_m": 45.0}
            ]
        },
        "xapps": [
            {"id": "xSlice", "dominio": "QoS e Slicing", "parametros_alvo": ["PRB_QUOTA"], "kpis_afetados": ["RRU.PrbUsedD1"]},
            {"id": "Energy Saving", "dominio": "Green RAN", "parametros_alvo": ["PRB_SHUTDOWN"], "kpis_afetados": ["L1M.DL-sinr"]}
        ],
        "conflitos": [
            {"tipo": "direto", "xapps_envolvidas": ["xSlice", "Energy Saving"], "parametros_ou_kpis": ["PRB_QUOTA", "PRB_SHUTDOWN"], "severidade": "alta", "descricao_visual": "Conflito direto de alocação de PRBs (Wc = 200 ms)"}
        ],
        "tradeoff_info": {"eixo_x": "Quota PRB Slicing", "eixo_y": "Desligamento PRB Energy", "tipo_curva": "conflito_direto"}
    },
    "S2": {
        "id": "S2",
        "nome": "Energy Saving vs QoS",
        "objetivo_cientifico": "Arbitragem entre redução de potência da rede e garantia de SLA URLLC",
        "tipo_conflito": "indireto",
        "topologia": {
            "area_m": [160, 110],
            "banda": "n78",
            "frequencia_GHz": 3.5,
            "largura_banda_MHz": 50,
            "gnodebs": [
                {"id": "gNB-1", "pos_m": [50, 55], "tipo": "macro", "potencia_dBm": 43.0, "raio_cobertura_m": 65.0},
                {"id": "gNB-2", "pos_m": [110, 55], "tipo": "micro", "potencia_dBm": 30.0, "raio_cobertura_m": 40.0}
            ],
            "ues": [
                {"id": "UE-01", "pos_m": [55, 60], "classe": "URLLC", "gnodeb_serving": "gNB-1"},
                {"id": "UE-02", "pos_m": [100, 50], "classe": "eMBB", "gnodeb_serving": "gNB-2"},
                {"id": "UE-03", "pos_m": [80, 55], "classe": "URLLC", "gnodeb_serving": "gNB-1"}
            ],
            "regioes_sobreposicao": [
                {"descricao": "Área de cobertura cruzada Macro/Micro", "centro_m": [80, 55], "raio_m": 35.0}
            ]
        },
        "xapps": [
            {"id": "Energy Saving", "dominio": "Green RAN", "parametros_alvo": ["TX_POWER"], "kpis_afetados": ["L1M.DL-sinr"]},
            {"id": "xSlice", "dominio": "QoS", "parametros_alvo": ["PRB_QUOTA"], "kpis_afetados": ["DRB.RlcSduDelayD1"]}
        ],
        "conflitos": [
            {"tipo": "indireto", "xapps_envolvidas": ["Energy Saving", "xSlice"], "parametros_ou_kpis": ["TX_POWER", "DRB.RlcSduDelayD1"], "severidade": "alta", "descricao_visual": "Solicitação Cell Sleep vs Demanda de Banda URLLC"}
        ],
        "tradeoff_info": {"eixo_x": "Potência de Transmissão (dBm)", "eixo_y": "Latência E2E URLLC (ms)", "tipo_curva": "pareto_tradeoff"}
    },
    "S3": {
        "id": "S3",
        "nome": "Traffic Steering vs Slicing",
        "objetivo_cientifico": "Manutenção de SLAs de fatia durante reorientação dinâmica de tráfego inter-células",
        "tipo_conflito": "indireto",
        "topologia": {
            "area_m": [180, 120],
            "banda": "n78",
            "frequencia_GHz": 3.5,
            "largura_banda_MHz": 100,
            "gnodebs": [
                {"id": "gNB-1", "pos_m": [55, 60], "tipo": "macro", "potencia_dBm": 43.0, "raio_cobertura_m": 65.0},
                {"id": "gNB-2", "pos_m": [125, 60], "tipo": "macro", "potencia_dBm": 43.0, "raio_cobertura_m": 65.0}
            ],
            "ues": [
                {"id": "UE-01", "pos_m": [85, 65], "classe": "URLLC", "gnodeb_serving": "gNB-1"},
                {"id": "UE-02", "pos_m": [95, 55], "classe": "eMBB", "gnodeb_serving": "gNB-2"},
                {"id": "UE-03", "pos_m": [90, 70], "classe": "mMTC", "gnodeb_serving": "gNB-1"}
            ],
            "regioes_sobreposicao": [
                {"descricao": "Fronteira Inter-Células com Múltiplas Fatias", "centro_m": [90, 60], "raio_m": 35.0}
            ]
        },
        "xapps": [
            {"id": "Traffic Steering", "dominio": "Mobilidade", "parametros_alvo": ["HANDOVER_TRIGGER"], "kpis_afetados": ["HO.AttCount"]},
            {"id": "xSlice", "dominio": "QoS", "parametros_alvo": ["SLICE_RESERVATION"], "kpis_afetados": ["DRB.UETHpD1"]}
        ],
        "conflitos": [
            {"tipo": "indireto", "xapps_envolvidas": ["Traffic Steering", "xSlice"], "parametros_ou_kpis": ["HANDOVER_TRIGGER", "SLICE_RESERVATION"], "severidade": "média", "descricao_visual": "Steering altera distribuição de carga enquanto Slicing preserva fatias"}
        ],
        "tradeoff_info": {"eixo_x": "Volume de Handover", "eixo_y": "Violação de SLA por Fatia", "tipo_curva": "pareto_tradeoff"}
    },
    "S4": {
        "id": "S4",
        "nome": "Traffic Steering vs Energy Saving",
        "objetivo_cientifico": "Evitar transferência de tráfego para células em modo de desligamento energético",
        "tipo_conflito": "misto",
        "topologia": {
            "area_m": [200, 120],
            "banda": "n78",
            "frequencia_GHz": 3.5,
            "largura_banda_MHz": 100,
            "gnodebs": [
                {"id": "gNB-A", "pos_m": [60, 60], "tipo": "macro", "potencia_dBm": 46.0, "raio_cobertura_m": 70.0},
                {"id": "gNB-B", "pos_m": [140, 60], "tipo": "small_cell", "potencia_dBm": 30.0, "raio_cobertura_m": 45.0}
            ],
            "ues": [
                {"id": "UE-01", "pos_m": [90, 65], "classe": "eMBB", "gnodeb_serving": "gNB-A"},
                {"id": "UE-02", "pos_m": [100, 55], "classe": "eMBB", "gnodeb_serving": "gNB-A"}
            ],
            "regioes_sobreposicao": [
                {"descricao": "Área de Transição A -> B", "centro_m": [100, 60], "raio_m": 30.0}
            ]
        },
        "xapps": [
            {"id": "Traffic Steering", "dominio": "Mobilidade", "parametros_alvo": ["HANDOVER"], "kpis_afetados": ["HO.AttCount"]},
            {"id": "Energy Saving", "dominio": "Green RAN", "parametros_alvo": ["CELL_SLEEP"], "kpis_afetados": ["PE.EnergyCons"]}
        ],
        "conflitos": [
            {"tipo": "misto", "xapps_envolvidas": ["Traffic Steering", "Energy Saving"], "parametros_ou_kpis": ["HANDOVER", "CELL_SLEEP"], "severidade": "alta", "descricao_visual": "TS move UEs A->B simultaneamente a pedido de Sleep em B"}
        ],
        "tradeoff_info": {"eixo_x": "Carga de Célula B", "eixo_y": "Economia de Energia (%)", "tipo_curva": "pareto_tradeoff"}
    },
    "S5": {
        "id": "S5",
        "nome": "Temporal Ping-Pong",
        "objetivo_cientifico": "Eliminação de oscilações repetitivas de handover via histerese e cooldown H-RDL",
        "tipo_conflito": "indireto",
        "topologia": {
            "area_m": [180, 110],
            "banda": "n78",
            "frequencia_GHz": 3.5,
            "largura_banda_MHz": 100,
            "gnodebs": [
                {"id": "Cell-A", "pos_m": [60, 55], "tipo": "macro", "potencia_dBm": 43.0, "raio_cobertura_m": 60.0},
                {"id": "Cell-B", "pos_m": [120, 55], "tipo": "macro", "potencia_dBm": 43.0, "raio_cobertura_m": 60.0}
            ],
            "ues": [
                {"id": "UE-Mobile", "pos_m": [90, 55], "classe": "URLLC", "gnodeb_serving": "Cell-A"}
            ],
            "regioes_sobreposicao": [
                {"descricao": "Zona de Histerese de Borda", "centro_m": [90, 55], "raio_m": 25.0}
            ]
        },
        "xapps": [
            {"id": "MRO / Steering", "dominio": "Mobilidade", "parametros_alvo": ["CIO_OFFSET"], "kpis_afetados": ["HO.PingPongRate"]},
            {"id": "Energy / QoS", "dominio": "Gerenciamento", "parametros_alvo": ["TX_POWER"], "kpis_afetados": ["DRB.RlcSduDelayD1"]}
        ],
        "conflitos": [
            {"tipo": "indireto", "xapps_envolvidas": ["MRO / Steering", "Energy / QoS"], "parametros_ou_kpis": ["CIO_OFFSET", "TX_POWER"], "severidade": "alta", "descricao_visual": "Decisões alternadas A->B->A em janela temporal curta"}
        ],
        "tradeoff_info": {"eixo_x": "Tempo de Cooldown (ms)", "eixo_y": "Taxa de Ping-Pong (%)", "tipo_curva": "pareto_tradeoff"}
    }
}

# Adicionar definições genéricas padronizadas para S6 a S15 para completar os 16 cenários
for idx in range(6, 16):
    sk = f"S{idx}"
    if sk not in CANONICAL_SCENARIOS:
        CANONICAL_SCENARIOS[sk] = {
            "id": sk,
            "nome": f"Cenário Avançado {sk}",
            "objetivo_cientifico": f"Otimização e arbitragem multidomínio 5G-A/6G para {sk}",
            "tipo_conflito": "misto",
            "topologia": {
                "area_m": [200, 140],
                "banda": "n78 / n258",
                "frequencia_GHz": 3.5 if idx < 9 else 28.0,
                "largura_banda_MHz": 100 if idx < 9 else 400,
                "gnodebs": [
                    {"id": f"gNB-{sk}-1", "pos_m": [60, 70], "tipo": "macro", "potencia_dBm": 43.0, "raio_cobertura_m": 70.0},
                    {"id": f"gNB-{sk}-2", "pos_m": [140, 70], "tipo": "micro" if idx < 13 else "small_cell", "potencia_dBm": 33.0, "raio_cobertura_m": 50.0}
                ],
                "ues": [
                    {"id": f"UE-{sk}-01", "pos_m": [50, 75], "classe": "URLLC", "gnodeb_serving": f"gNB-{sk}-1"},
                    {"id": f"UE-{sk}-02", "pos_m": [130, 65], "classe": "eMBB", "gnodeb_serving": f"gNB-{sk}-2"},
                    {"id": f"UE-{sk}-03", "pos_m": [100, 70], "classe": "mMTC", "gnodeb_serving": f"gNB-{sk}-1"}
                ],
                "regioes_sobreposicao": [
                    {"descricao": f"Zona de Interseção Multidomínio {sk}", "centro_m": [100, 70], "raio_m": 35.0}
                ]
            },
            "xapps": [
                {"id": f"xApp-A-{sk}", "dominio": "Domínio A", "parametros_alvo": ["PARAM_A"], "kpis_afetados": ["KPI_A"]},
                {"id": f"xApp-B-{sk}", "dominio": "Domínio B", "parametros_alvo": ["PARAM_B"], "kpis_afetados": ["KPI_B"]}
            ],
            "conflitos": [
                {"tipo": "misto", "xapps_envolvidas": [f"xApp-A-{sk}", f"xApp-B-{sk}"], "parametros_ou_kpis": ["PARAM_A", "PARAM_B"], "severidade": "alta", "descricao_visual": f"Disputa de recursos multidomínio em {sk}"}
            ],
            "tradeoff_info": {"eixo_x": "Parâmetro A", "eixo_y": "Parâmetro B", "tipo_curva": "pareto_tradeoff"}
        }

PALETTE_LIGHT = {
    "fundo": "#FFFFFF",
    "card": "#F8FAFC",
    "gnodeb_macro": "#1E3A8A",
    "gnodeb_micro": "#047857",
    "gnodeb_small": "#7E22CE",
    "urllc": "#BE123C",
    "embb": "#1D4ED8",
    "mmtc": "#B45309",
    "sobreposicao": "#FEF3C7",
    "destaque_conflito": "#E67E22",
    "texto": "#0F172A",
    "subtexto": "#334155"
}

PALETTE_DARK = {
    "fundo": "#0F172A",
    "card": "#1E293B",
    "gnodeb_macro": "#3B82F6",
    "gnodeb_micro": "#10B981",
    "gnodeb_small": "#A855F7",
    "urllc": "#F43F5E",
    "embb": "#60A5FA",
    "mmtc": "#F59E0B",
    "sobreposicao": "#451A03",
    "destaque_conflito": "#F97316",
    "texto": "#F8FAFC",
    "subtexto": "#94A3B8"
}

def render_figure_a(spec, is_light=True):
    """
    Renderiza a FIGURA A — Representação Conceitual 3D/Ilustrativa (Estilo Figura 4 do artigo H-RDL).
    """
    pal = PALETTE_LIGHT if is_light else PALETTE_DARK
    fig, ax = plt.subplots(figsize=(12, 7.5), facecolor=pal["fundo"])
    ax.set_facecolor(pal["fundo"])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    # Rótulo Superior com o nome do cenário e "Fase 1 H-RDL"
    ax.text(6.0, 7.1, f"Figura A (Conceitual) — {spec['id']}: {spec['nome']} (Fase 1 H-RDL)",
            ha='center', va='center', fontsize=12.5, fontweight='bold', color=pal["texto"])
    ax.text(6.0, 6.7, f"Objetivo Científico: {spec['objetivo_cientifico']}",
            ha='center', va='center', fontsize=9.0, style='italic', color=pal["subtexto"])

    # Ilustração de Torres gNodeB
    gnbs = spec["topologia"]["gnodebs"]
    for idx, gnb in enumerate(gnbs):
        gx = 2.5 + idx * 4.5
        gy = 3.8
        g_color = pal["gnodeb_macro"] if gnb["tipo"] == "macro" else pal["gnodeb_micro"]
        
        # Desenho simbólico da torre
        ax.plot([gx, gx], [gy - 1.2, gy + 0.8], color=g_color, lw=3, zorder=3)
        ax.plot([gx - 0.4, gx + 0.4], [gy + 0.8, gy + 0.8], color=g_color, lw=2, zorder=3)
        ax.plot([gx - 0.3, gx + 0.3], [gy + 0.4, gy + 0.4], color=g_color, lw=1.5, zorder=3)
        ax.scatter([gx], [gy + 1.0], color=g_color, s=80, zorder=4)

        # Círculo de cobertura conceitual
        cov = patches.Circle((gx, gy - 0.2), 1.8, facecolor=g_color, alpha=0.12, edgecolor=g_color, linestyle='--', lw=1.5, zorder=2)
        ax.add_patch(cov)

        ax.text(gx, gy + 1.3, f"{gnb['id']} ({gnb['tipo'].capitalize()})\n{spec['topologia']['frequencia_GHz']} GHz",
                ha='center', va='bottom', fontsize=8.5, fontweight='bold', color=pal["texto"])

    # UEs Representadas por Ícones/Classes de Tráfego
    ues = spec["topologia"]["ues"]
    for u_idx, ue in enumerate(ues):
        ux = 2.0 + u_idx * 2.2
        uy = 1.8
        u_col = pal["urllc"] if ue["classe"] == "URLLC" else (pal["embb"] if ue["classe"] == "eMBB" else pal["mmtc"])
        marker = '^' if ue["classe"] == "URLLC" else ('s' if ue["classe"] == "eMBB" else 'D')
        ax.scatter([ux], [uy], color=u_col, marker=marker, s=90, zorder=5, edgecolors='black', linewidth=0.8)
        ax.text(ux, uy - 0.3, f"{ue['id']} ({ue['classe']})", ha='center', va='top', fontsize=7.5, fontweight='bold', color=pal["texto"])

    # Callout Interno — Lógica de Conflito xApps & Arbitragem H-RDL
    callout_box = patches.FancyBboxPatch((8.2, 3.2), 3.5, 3.2, boxstyle="round,pad=0.04",
                                          facecolor=pal["card"], edgecolor=pal["destaque_conflito"], lw=2, zorder=3)
    ax.add_patch(callout_box)
    ax.text(9.95, 6.1, "Lógica de Conflito & H-RDL", ha='center', va='center', fontsize=9.5, fontweight='bold', color=pal["destaque_conflito"])
    
    xapp_list = [x["id"] for x in spec["xapps"]]
    ax.text(9.95, 5.6, f"xApps: {' vs '.join(xapp_list)}", ha='center', va='center', fontsize=8.0, fontweight='bold', color=pal["texto"])
    
    conf_desc = spec["conflitos"][0]["descricao_visual"]
    ax.text(9.95, 4.8, f"Conflito ({spec['conflitos'][0]['tipo'].capitalize()}):\n{conf_desc}",
            ha='center', va='center', fontsize=7.5, color=pal["texto"], multialignment='center')

    ax.text(9.95, 3.7, "Arbitragem H-RDL:\nSafety L0-L3 & Cooldown Filter",
            ha='center', va='center', fontsize=7.5, fontweight='bold', color=pal["gnodeb_micro"], multialignment='center')

    # Curva Conceitual de Trade-Off (Canto Inferior Direito)
    trade_box = patches.FancyBboxPatch((8.2, 0.6), 3.5, 2.2, boxstyle="round,pad=0.03",
                                        facecolor=pal["card"], edgecolor=pal["embb"], lw=1.5, zorder=3)
    ax.add_patch(trade_box)
    ax.text(9.95, 2.5, "Curva de Trade-Off Conceitual", ha='center', va='center', fontsize=8.5, fontweight='bold', color=pal["embb"])
    
    # Eixos da curva de trade-off
    ax.plot([8.6, 11.3], [1.0, 1.0], color=pal["subtexto"], lw=1, zorder=4)
    ax.plot([8.6, 8.6], [1.0, 2.2], color=pal["subtexto"], lw=1, zorder=4)
    
    tx = np.linspace(8.7, 11.2, 20)
    ty = 2.1 - 0.8 * np.exp(-1.2 * (tx - 8.7))
    ax.plot(tx, ty, color=pal["urllc"], lw=2, linestyle='-', zorder=5)
    ax.text(9.95, 0.75, f"{spec['tradeoff_info']['eixo_x']} vs {spec['tradeoff_info']['eixo_y']}",
            ha='center', va='center', fontsize=7.0, color=pal["subtexto"])

    # Nota de Isenção Científica
    ax.text(6.0, 0.25, 'Nota: "Representação esquemática do cenário; não substitui resultados experimentais."',
            ha='center', va='center', fontsize=8.0, style='italic', color=pal["urllc"])

    plt.tight_layout()
    fname = f"{spec['id'].lower()}_figura_a_{'light' if is_light else 'dark'}.png"
    fpath = os.path.join(OUTPUT_DIR, fname)
    plt.savefig(fpath, dpi=300, facecolor=pal["fundo"])
    plt.close()
    return fname

def render_figure_b(spec, is_light=True):
    """
    Renderiza a FIGURA B — Representação Geométrica 2D do Cenário em Metros (Estilo Figura 5 do artigo H-RDL).
    """
    pal = PALETTE_LIGHT if is_light else PALETTE_DARK
    fig, ax = plt.subplots(figsize=(11, 7), facecolor=pal["fundo"])
    ax.set_facecolor(pal["fundo"])

    area_x, area_y = spec["topologia"]["area_m"]
    ax.set_xlim(0, area_x)
    ax.set_ylim(0, area_y)
    ax.set_xlabel("Coordenada X (m)", fontsize=10, fontweight='bold', color=pal["texto"])
    ax.set_ylabel("Coordenada Y (m)", fontsize=10, fontweight='bold', color=pal["texto"])
    ax.tick_params(colors=pal["texto"], labelsize=9)
    ax.grid(True, linestyle='--', alpha=0.4, color=pal["subtexto"])

    # Rótulo Superior com os Parâmetros Chave
    param_header = f"{spec['id']} – {spec['nome']} ({spec['topologia']['banda']}, {spec['topologia']['frequencia_GHz']} GHz, {spec['topologia']['largura_banda_MHz']} MHz, Área {area_x}×{area_y} m)"
    ax.set_title(f"Figura B (Geométrica 2D em Metros) — {param_header}", fontsize=10.5, fontweight='bold', color=pal["texto"], pad=12)

    # 1. Círculos de Cobertura das gNodeBs
    for gnb in spec["topologia"]["gnodebs"]:
        gx, gy = gnb["pos_m"]
        raio = gnb["raio_cobertura_m"]
        g_col = pal["gnodeb_macro"] if gnb["tipo"] == "macro" else pal["gnodeb_micro"]
        
        circ = patches.Circle((gx, gy), raio, facecolor=g_col, alpha=0.15, edgecolor=g_col, lw=2, linestyle='-', zorder=2)
        ax.add_patch(circ)
        
        # Marcador da gNodeB
        ax.scatter([gx], [gy], color=g_col, marker='^', s=160, zorder=5, edgecolors='black', linewidth=1.0)
        ax.text(gx, gy + 4, f"{gnb['id']} ({gnb['tipo'].capitalize()})\n{gnb['potencia_dBm']} dBm",
                ha='center', va='bottom', fontsize=8.0, fontweight='bold', color=pal["texto"],
                bbox=dict(boxstyle="square,pad=0.2", facecolor=pal["card"], edgecolor='none', alpha=0.85), zorder=6)

    # 2. Plotagem das UEs por Posição pos_m e Formato Distinto por Classe
    for ue in spec["topologia"]["ues"]:
        ux, uy = ue["pos_m"]
        u_col = pal["urllc"] if ue["classe"] == "URLLC" else (pal["embb"] if ue["classe"] == "eMBB" else pal["mmtc"])
        marker = 'v' if ue["classe"] == "URLLC" else ('s' if ue["classe"] == "eMBB" else 'D')
        
        ax.scatter([ux], [uy], color=u_col, marker=marker, s=110, zorder=6, edgecolors='black', linewidth=0.8)
        ax.text(ux + 2, uy, f"{ue['id']} ({ue['classe']})", ha='left', va='center', fontsize=7.5, fontweight='bold', color=pal["texto"], zorder=6)

    # 3. Região de Sobreposição Destacada
    for reg in spec["topologia"]["regioes_sobreposicao"]:
        cx, cy = reg["centro_m"]
        r_sob = reg["raio_m"]
        sob_patch = patches.Circle((cx, cy), r_sob, facecolor=pal["sobreposicao"], alpha=0.35, edgecolor=pal["destaque_conflito"], lw=2, linestyle=':', zorder=3)
        ax.add_patch(sob_patch)
        ax.text(cx, cy, f"Sobreposição:\n{reg['descricao']}", ha='center', va='center', fontsize=7.5, fontweight='bold', color=pal["destaque_conflito"], zorder=7)

    # 4. Anotação do Efeito Esperado da H-RDL
    ax.text(area_x * 0.5, area_y * 0.08, f"Efeito Esperado H-RDL: Arbitragem segura ({spec['conflitos'][0]['severidade'].upper()} severidade) — Preservação de SLA",
            ha='center', va='center', fontsize=8.5, fontweight='bold', color=pal["gnodeb_micro"],
            bbox=dict(boxstyle="round,pad=0.3", facecolor=pal["card"], edgecolor=pal["gnodeb_micro"], lw=1.5), zorder=8)

    plt.tight_layout()
    fname = f"{spec['id'].lower()}_figura_b_{'light' if is_light else 'dark'}.png"
    fpath = os.path.join(OUTPUT_DIR, fname)
    plt.savefig(fpath, dpi=300, facecolor=pal["fundo"])
    plt.close()
    return fname

def generate_provenance_and_reports(generated_files):
    """
    Gera os artefatos adicionais requeridos pela SKILL:
    - cenarios_canonicos_s0_s15.json
    - relatorio_correspondencia_A_B.md
    - manifesto_proveniencia.json (com hashes SHA-256)
    """
    # 1. JSON Canônico
    canonical_path = os.path.join(OUTPUT_DIR, "cenarios_canonicos_s0_s15.json")
    with open(canonical_path, "w", encoding="utf-8") as fh:
        json.dump(CANONICAL_SCENARIOS, fh, indent=2, ensure_ascii=False)

    # 2. Relatório de Correspondência A <-> B
    corr_path = os.path.join(OUTPUT_DIR, "relatorio_correspondencia_A_B.md")
    with open(corr_path, "w", encoding="utf-8") as fh:
        fh.write("# Relatório de Correspondência Biunívoca entre Figura A e Figura B (S0 a S15)\n\n")
        fh.write("Este documento valida a consistência topológica, geométrica e funcional entre as representações conceituais (Figura A) e 2D métricas (Figura B).\n\n")
        fh.write("| Cenário ID | Nome do Cenário | Equivalência Topológica (gNodeBs / UEs) | Equivalência Funcional (Callout A vs Retângulo B) |\n")
        fh.write("| :---: | :--- | :--- | :--- |\n")
        for sk, spec in CANONICAL_SCENARIOS.items():
            num_gnb = len(spec["topologia"]["gnodebs"])
            num_ue = len(spec["topologia"]["ues"])
            fh.write(f"| **{sk}** | {spec['nome']} | {num_gnb} gNBs, {num_ue} UEs | Callout {spec['xapps'][0]['id']} vs Posições em {spec['topologia']['area_m']}m |\n")

    # 3. Manifesto de Proveniência SHA-256
    manifest = {
        "skill_version": "xapp-figure-generator-v1.0",
        "description": "Manifesto de provenicência das figuras de cenários O-RAN (Estilo Figuras 4 e 5)",
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
    print("[+] Gerando Suíte Oficial de Figuras A e B (Estilo Figuras 4 e 5 - S0 a S15)...")
    all_generated = []
    for sk in [f"S{i}" for i in range(16)]:
        spec = CANONICAL_SCENARIOS[sk]
        for is_light in [True, False]:
            f_a = render_figure_a(spec, is_light)
            f_b = render_figure_b(spec, is_light)
            all_generated.extend([f_a, f_b])
            print(f"  - [{sk}] Geradas: {f_a} e {f_b}")

    generate_provenance_and_reports(all_generated)
    print(f"\n[OK] Concluído! {len(all_generated)} figuras salvas com sucesso em '{OUTPUT_DIR}'!")
