#!/usr/bin/env python3
"""
Scientific Figure Generator: H-RDL (Phase 1) Dedicated Architecture Diagram.
Padrão Visual: IEEE Transactions / OpenTwin / OAI / SBC SBRC.

Gera o diagrama arquitetural completo e exclusivo da H-RDL em alta resolução (300 DPI),
com suporte simultâneo a formatos PNG, SVG e PDF vetorial.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ArrowStyle, PathPatch
from matplotlib.path import Path

def create_hrdl_architecture_diagram():
    # Dimensões e proporções da figura
    fig, ax = plt.subplots(figsize=(16, 12), dpi=300)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    # Paleta de Cores Sóbria e Científica (IEEE Guidelines)
    NAVY = '#17324D'       # Estruturas e Títulos principais
    BLUE_DARK = '#1E40AF'  # Near-RT RIC Core
    BLUE_MED = '#2D6F9F'   # Módulos de Processamento
    BLUE_LIGHT = '#F0F6FB' # Fundo dos módulos da Fase 1
    GREEN_DARK = '#15803D' # xApps e Ações Válidas
    GREEN_LIGHT = '#F0FDF4'# Fundo das xApps
    ORANGE_DARK = '#C2410C'# Governança e Safety Guards
    ORANGE_LIGHT = '#FFF7ED'# Fundo Safety Guard
    RED_DARK = '#B91C1C'   # Ações Rejeitadas e Conflitos
    RED_LIGHT = '#FEF2F2'  # Fundo Rejeição
    GRAY_DARK = '#334155'  # Linhas e Conectores
    GRAY_MED = '#64748B'   # Textos secundários
    TEAL_DARK = '#0F766E'  # Interfaces E2 e Telemetria
    TEAL_LIGHT = '#F0FDFA' # Fundo Nós E2

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # -------------------------------------------------------------------------
    # Helper: Desenhar caixas arredondadas com sombra sutil e estilo clean
    # -------------------------------------------------------------------------
    def draw_box(x, y, w, h, bg_color, border_color, border_width=1.5, linestyle='-', radius=1.5):
        # Sombra sutil
        shadow = FancyBboxPatch(
            (x + 0.25, y - 0.25), w, h,
            boxstyle=f"round,pad=0,rounding_size={radius}",
            facecolor='#000000', alpha=0.03, edgecolor='none', zorder=1
        )
        ax.add_patch(shadow)

        box = FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0,rounding_size={radius}",
            facecolor=bg_color, edgecolor=border_color,
            linewidth=border_width, linestyle=linestyle, zorder=2
        )
        ax.add_patch(box)
        return box

    def draw_arrow(x1, y1, x2, y2, color=GRAY_DARK, width=1.5, style='->', linestyle='-', label="", label_pos=0.5, label_offset=(0, 0)):
        arrow = patches.FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle=ArrowStyle("Simple, tail_width=0.8, head_width=3.5, head_length=4.5"),
            color=color, linewidth=width, linestyle=linestyle, zorder=4
        )
        ax.add_patch(arrow)
        if label:
            lx = x1 + (x2 - x1) * label_pos + label_offset[0]
            ly = y1 + (y2 - y1) * label_pos + label_offset[1]
            ax.text(lx, ly, label, fontsize=7.8, fontweight='bold', color=color,
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor=color, alpha=0.95, lw=0.8),
                    ha='center', va='center', zorder=5)

    # =========================================================================
    # 1. CABEÇALHO CIENTÍFICO E METADADOS DO DIAGRAMA
    # =========================================================================
    ax.text(50, 97.8, "ARQUITETURA DETERMINÍSTICA DO MIDDLEWARE H-RDL (FASE 1)", 
            fontsize=15, fontweight='black', color=NAVY, ha='center', va='center')
    ax.text(50, 95.6, "Safe Closed-Loop Multi-xApp Conflict Mitigation in Open RAN Near-RT RIC via Hierarchical Utility & Deterministic Safety Guards",
            fontsize=9.5, fontweight='medium', color=GRAY_DARK, ha='center', va='center', style='italic')

    # =========================================================================
    # 2. CONTAINER GLOBAL: NEAR-RT RIC CLUSTER (Plataforma O-RAN)
    # =========================================================================
    draw_box(4, 25.5, 92, 67.5, '#F8FAFC', NAVY, border_width=2.0, radius=2.5)
    ax.text(6.5, 91.0, "O-RAN Near-RT RIC Platform (Time-scale: 10 ms – 1 s)", 
            fontsize=11, fontweight='black', color=NAVY, ha='left', va='center')
    ax.text(93.5, 91.0, "Standard: O-RAN WG3 E2SM-RC v01.03 / E2SM-KPM v02.03", 
            fontsize=8.5, fontweight='bold', color=BLUE_MED, ha='right', va='center')

    # -------------------------------------------------------------------------
    # 2.1. CAMADA SUPERIOR: xApps Concorrentes de Referência
    # -------------------------------------------------------------------------
    draw_box(7, 76.5, 86, 12.5, '#F1F5F9', '#CBD5E1', border_width=1.0, radius=2.0)
    ax.text(9, 86.8, "CAMADA DE APLICAÇÕES NEAR-RT (CONCURRENT xApps)", fontsize=9, fontweight='black', color=GRAY_DARK)

    # xApp 1: xSlice (QoS)
    draw_box(9, 78.5, 25, 7, GREEN_LIGHT, GREEN_DARK, border_width=1.5)
    ax.text(21.5, 83.7, "xApp-QoS-Slice", fontsize=10, fontweight='bold', color=GREEN_DARK, ha='center')
    ax.text(21.5, 80.7, "Alocação Dinâmica de PRBs\n(URLLC, eMBB, mMTC)", fontsize=7.5, color=GRAY_DARK, ha='center')

    # xApp 2: Energy Saving (ES)
    draw_box(37.5, 78.5, 25, 7, GREEN_LIGHT, GREEN_DARK, border_width=1.5)
    ax.text(50, 83.7, "xApp-Energy-Saving", fontsize=10, fontweight='bold', color=GREEN_DARK, ha='center')
    ax.text(50, 80.7, "Modulação de Potência de Tx\n(Cell On/Off & Micro-Sleep)", fontsize=7.5, color=GRAY_DARK, ha='center')

    # xApp 3: Traffic Steering (TS)
    draw_box(66, 78.5, 25, 7, GREEN_LIGHT, GREEN_DARK, border_width=1.5)
    ax.text(78.5, 83.7, "xApp-Traffic-Steering", fontsize=10, fontweight='bold', color=GREEN_DARK, ha='center')
    ax.text(78.5, 80.7, "Mobilidade & Handover\n(A3-Offset & Tilt de Antena)", fontsize=7.5, color=GRAY_DARK, ha='center')

    # -------------------------------------------------------------------------
    # 2.2. BARRAMENTO DE MENSAGERIA INTERNA: RMR BUS (RIC Message Router)
    # -------------------------------------------------------------------------
    draw_box(7, 69.5, 86, 4.2, '#EFF6FF', BLUE_MED, border_width=1.5, radius=1.0)
    ax.text(50, 71.6, "RMR Message Bus  ·  Ingestão Assíncrona de Propostas [xApp_ID, Cell_ID, RCP, Action_Value, Priority, TTL]",
            fontsize=8.5, fontweight='bold', color=BLUE_MED, ha='center', va='center')

    # Setas das xApps para o RMR Bus
    draw_arrow(21.5, 78.5, 21.5, 73.7, color=GREEN_DARK, label="Proposta 1", label_pos=0.5)
    draw_arrow(50, 78.5, 50, 73.7, color=GREEN_DARK, label="Proposta 2", label_pos=0.5)
    draw_arrow(78.5, 78.5, 78.5, 73.7, color=GREEN_DARK, label="Proposta 3", label_pos=0.5)

    # =========================================================================
    # 3. NÚCLEO DETERMINÍSTICO H-RDL (Hierarchical Resource and Decision Layer)
    # =========================================================================
    draw_box(20, 27.5, 60, 37.5, BLUE_LIGHT, BLUE_MED, border_width=2.0, radius=2.5)
    ax.text(22, 63.5, "NÚCLEO DETERMINÍSTICO H-RDL (Arbitragem Sub-Milissegundo · T_dec ≤ 0.262 ms)", 
            fontsize=9.8, fontweight='black', color=BLUE_MED, ha='left')

    # 3.1. Decision Window & Time Synchronizer
    draw_box(23, 55.5, 54, 5.5, '#FFFFFF', BLUE_MED, border_width=1.2)
    ax.text(50, 59.2, "1. Decision Window & Time Synchronizer (W_sync = 10 – 200 ms)", 
            fontsize=8.8, fontweight='bold', color=NAVY, ha='center')
    ax.text(50, 57.0, "Agrupamento temporal de propostas concorrentes em lotes sincronizados", 
            fontsize=7.5, color=GRAY_DARK, ha='center')

    draw_arrow(50, 69.5, 50, 61.2, color=BLUE_MED, label="Lote de Propostas", label_pos=0.5, label_offset=(11, 0))

    # 3.2. Perception Agent (Detecção Formal de Conflitos C1-C4)
    draw_box(23, 46.5, 54, 6.8, '#FFFFFF', BLUE_MED, border_width=1.2)
    ax.text(50, 51.6, "2. Perception Agent (Detecção Formal de Conflitos C1–C4)", 
            fontsize=8.8, fontweight='bold', color=NAVY, ha='center')
    ax.text(50, 49.4, "Matriz de Adjacência de Conflitos · Detecção Direta (PRB/Potência) e Indireta (QoS/TVS)", 
            fontsize=7.5, color=GRAY_DARK, ha='center')
    ax.text(50, 47.7, "Classes: C1 (PRB Collision) | C2 (Power Overload) | C3 (Parameter Flipping) | C4 (Cross-Domain)", 
            fontsize=7.0, fontweight='bold', color=ORANGE_DARK, ha='center')

    draw_arrow(50, 55.5, 50, 53.3, color=BLUE_MED)

    # 3.3. Reasoning Agent (Arbitragem Heurística & Utilidade Multiobjetivo)
    draw_box(23, 37.5, 54, 6.8, '#FFFFFF', BLUE_MED, border_width=1.2)
    ax.text(50, 42.6, "3. Reasoning Agent (Arbitragem de Prioridade & Funções de Utilidade)", 
            fontsize=8.8, fontweight='bold', color=NAVY, ha='center')
    ax.text(50, 40.4, "Otimização Pareto de Utilidade TVS (Throughput vs Slicing) e EEVS (Energy vs SLA)", 
            fontsize=7.5, color=GRAY_DARK, ha='center')
    ax.text(50, 38.7, "Hierarquia Canônica de Fatias: Slice-URLLC (w=0.7) ≻ Slice-eMBB (w=0.3) ≻ Slice-mMTC", 
            fontsize=7.0, fontweight='bold', color=GREEN_DARK, ha='center')

    draw_arrow(50, 46.5, 50, 44.3, color=BLUE_MED, label="Conflitos Mapeados", label_pos=0.5, label_offset=(11, 0))

    # 3.4. Refinement Agent & Deterministic Safety Guards
    draw_box(23, 28.5, 54, 7.0, ORANGE_LIGHT, ORANGE_DARK, border_width=1.5)
    ax.text(50, 33.8, "4. Refinement Agent & Deterministic Safety Guards (Unsafe ≡ 0)", 
            fontsize=8.8, fontweight='bold', color=ORANGE_DARK, ha='center')
    ax.text(50, 31.6, "Projeção no Envelope Seguro: a_final = argmin ||a - a_prop||² sujeito a a ∈ Ω_safe", 
            fontsize=7.5, fontweight='bold', color=NAVY, ha='center')
    ax.text(50, 29.9, "Invariantes: Σ PRB ≤ 100% · P_min ≤ P_tx ≤ P_max · Cooldown Lockout (anti-pingpong)", 
            fontsize=7.0, color=ORANGE_DARK, ha='center')

    draw_arrow(50, 37.5, 50, 35.5, color=BLUE_MED, label="Ação Candidata", label_pos=0.5, label_offset=(11, 0))

    # =========================================================================
    # 4. MÓDULOS LATERAIS: TELEMETRIA, MEMÓRIA E QUARENTENA
    # =========================================================================
    # Lateral Esquerda: Telemetria E2SM-KPM & State Buffer
    draw_box(6, 39.5, 12.5, 25, TEAL_LIGHT, TEAL_DARK, border_width=1.2)
    ax.text(12.25, 62.0, "E2SM-KPM\nIngestion", fontsize=8.5, fontweight='bold', color=TEAL_DARK, ha='center')
    ax.text(12.25, 54.5, "• KPM v02.03/v03.00\n• ASN.1 APER Parser\n• PRB Usage per Slice\n• RLC Buffer & HOL\n• Packet Drop Rate\n• SINR & MCS", 
            fontsize=7.0, color=GRAY_DARK, ha='left')
    draw_arrow(18.5, 50.0, 23, 50.0, color=TEAL_DARK, label="RAN State", label_pos=0.5)

    # Lateral Direita Superior: Memória Histórica de Decisão
    draw_box(81.5, 51.5, 12.5, 13.5, '#F8FAFC', BLUE_MED, border_width=1.2)
    ax.text(87.75, 62.2, "Memory Module", fontsize=8.5, fontweight='bold', color=BLUE_MED, ha='center')
    ax.text(87.75, 56.5, "• Tabela de Confiança\n• Histórico de Decisões\n• Trava Anti-Flapping\n• Perfil das Células", 
            fontsize=7.0, color=GRAY_DARK, ha='left')
    draw_arrow(77, 40.9, 81.5, 53.5, color=BLUE_MED, linestyle='--', label="Histórico", label_pos=0.5)

    # Lateral Direita Inferior: Quarentena / Ações Bloqueadas
    draw_box(81.5, 28.5, 12.5, 14.5, RED_LIGHT, RED_DARK, border_width=1.2)
    ax.text(87.75, 40.8, "Quarantine Log", fontsize=8.5, fontweight='bold', color=RED_DARK, ha='center')
    ax.text(87.75, 33.5, "• Ações Inseguras (0%)\n• Rejeição Determinística\n• Fallback Seguro\n• Rastreio de Motivo", 
            fontsize=7.0, color=RED_DARK, ha='left')
    draw_arrow(77, 32.0, 81.5, 32.0, color=RED_DARK, label="Rejeição / Mod", label_pos=0.5)

    # =========================================================================
    # 5. CAMADA DE DESPACHO E CODEC ASN.1 APER (E2SM-RC Format 1)
    # =========================================================================
    draw_box(20, 16.5, 60, 7.5, '#FFFFFF', BLUE_MED, border_width=1.5, radius=1.5)
    ax.text(50, 21.8, "Action Arbiter & E2SM-RC ASN.1 APER Codec Engine", 
            fontsize=9.5, fontweight='bold', color=NAVY, ha='center')
    ax.text(50, 19.5, "Geração de RIC Control Request (19 Bytes) · Message Type 12040 · RPC Control Header & Message Format 1", 
            fontsize=7.5, color=GRAY_DARK, ha='center')
    ax.text(50, 17.8, "Correlação de Request ID, Instance ID e Monitoramento de Timeout Local / Rollback Seguro", 
            fontsize=7.2, color=BLUE_MED, ha='center')

    draw_arrow(50, 28.5, 50, 24.0, color=ORANGE_DARK, label="Ação Segura Validada (a*)", label_pos=0.5)

    # =========================================================================
    # 6. CAMADA DE INFRAESTRUTURA DE RÁDIO: E2 NODE / SIMULADOR ns-3 / 5G-LENA
    # =========================================================================
    draw_box(4, 2.5, 92, 10.5, TEAL_LIGHT, TEAL_DARK, border_width=2.0, radius=2.5)
    ax.text(6.5, 11.4, "E2 Node / RAN Physical Subsystem (ns-3.48 + 5G-LENA v5.1 + NORI E2 Agent)", 
            fontsize=10.0, fontweight='black', color=TEAL_DARK, ha='left')
    ax.text(93.5, 11.4, "3GPP TR 38.901 Channel Model  ·  gNodeB / O-DU / O-CU Desagregados", 
            fontsize=7.8, fontweight='semibold', color=GRAY_DARK, ha='right')

    # Subcomponentes do Nó E2
    draw_box(7, 4.0, 26, 5.5, '#FFFFFF', TEAL_DARK, border_width=1.0)
    ax.text(20, 7.8, "NORI E2 Agent Interface", fontsize=8.2, fontweight='bold', color=TEAL_DARK, ha='center')
    ax.text(20, 5.5, "SCTP Socket Listener (:36422)\nE2AP Protocol Processing", fontsize=7.0, color=GRAY_DARK, ha='center')

    draw_box(37, 4.0, 26, 5.5, '#FFFFFF', TEAL_DARK, border_width=1.0)
    ax.text(50, 7.8, "MAC Scheduler & PHY Layer", fontsize=8.2, fontweight='bold', color=TEAL_DARK, ha='center')
    ax.text(50, 5.5, "Dynamic PRB Allocation (OFDM)\nPower & Beam Adaptation", fontsize=7.0, color=GRAY_DARK, ha='center')

    draw_box(67, 4.0, 26, 5.5, '#FFFFFF', TEAL_DARK, border_width=1.0)
    ax.text(80, 7.8, "E2SM-KPM / RC Handlers", fontsize=8.2, fontweight='bold', color=TEAL_DARK, ha='center')
    ax.text(80, 5.5, "RIC_CONTROL_ACKNOWLEDGE\nTelemetria Periódica / Eventos", fontsize=7.0, color=GRAY_DARK, ha='center')

    # =========================================================================
    # 7. ENLACES DE CIRCUITO FECHADO E2 (Closed-Loop Flows)
    # =========================================================================
    # Seta de Controle: H-RDL -> Nó E2 (Downlink Control)
    draw_arrow(43, 16.5, 43, 9.8, color=BLUE_DARK, width=2.0, label="RIC_CONTROL_REQ (E2SM-RC)", label_pos=0.5, label_offset=(-12, 0))

    # Seta de Confirmação ACK: Nó E2 -> H-RDL (Uplink ACK)
    draw_arrow(57, 9.8, 57, 16.5, color=GREEN_DARK, width=1.5, linestyle='--', label="RIC_CONTROL_ACK (Success)", label_pos=0.5, label_offset=(12, 0))

    # Seta de Loopback de Telemetria: Nó E2 -> E2SM-KPM Ingestion
    path_data = [
        (Path.MOVETO, (7, 6.75)),
        (Path.LINETO, (2, 6.75)),
        (Path.LINETO, (2, 52)),
        (Path.LINETO, (6, 52))
    ]
    codes, verts = zip(*path_data)
    path = Path(verts, codes)
    patch = PathPatch(path, facecolor='none', edgecolor=TEAL_DARK, linewidth=1.8, linestyle=':', zorder=3)
    ax.add_patch(patch)
    ax.annotate('', xy=(6, 52), xytext=(4, 52),
                arrowprops=dict(arrowstyle="-|>", color=TEAL_DARK, lw=1.8, mutation_scale=15), zorder=5)
    ax.text(2.5, 30, "Telemetria E2SM-KPM (SCTP:36422)\nRealimentação Contínua da RAN", 
            fontsize=7.5, fontweight='bold', color=TEAL_DARK, rotation=90, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor=TEAL_DARK, lw=0.8))

    # =========================================================================
    # 8. RODAPÉ DE RASTREABILIDADE & NOTAS TÉCNICAS
    # =========================================================================
    footer_text = (
        "Legenda Metodológica: "
        "Caixas Azuis = Módulos de Decisão H-RDL (Fase 1); "
        "Caixas Laranjas = Camada de Blindagem Determinística (Safety Guards); "
        "Caixas Verdes = Aplicações xApps; "
        "Caixas Teal = Nós E2 e Telemetria de Rádio. "
        "Garantias Arquiteturais: Taxa de Violação Insegura ≡ 0,0%, Latência de Decisão T_dec ≤ 0,262 ms, Taxa de Fechamento Causal CRE = 100,0%."
    )
    ax.text(50, 0.8, footer_text, fontsize=7.2, color=GRAY_MED, ha='center', va='center', style='italic')

    # Salvar em múltiplos formatos
    out_dir_1 = "docs/figures/01_arquitetura_e_governanca"
    out_dir_2 = "docs/figures"
    os.makedirs(out_dir_1, exist_ok=True)
    os.makedirs(out_dir_2, exist_ok=True)

    filenames = [
        os.path.join(out_dir_1, "fig_arquitetura_hrdl_fase1_deterministica.png"),
        os.path.join(out_dir_1, "fig_arquitetura_hrdl_fase1_deterministica.pdf"),
        os.path.join(out_dir_1, "fig_arquitetura_hrdl_fase1_deterministica.svg"),
        os.path.join(out_dir_2, "fig_arquitetura_hrdl_fase1_deterministica.png"),
        os.path.join(out_dir_2, "fig_arquitetura_hrdl_fase1_deterministica.pdf"),
        os.path.join(out_dir_2, "fig_arquitetura_hrdl_fase1_deterministica.svg"),
    ]

    for fname in filenames:
        plt.savefig(fname, bbox_inches='tight', pad_inches=0.1, dpi=300)
        print(f"[OK] Gerada Figura de Arquitetura Aprimorada: {fname}")

    plt.close(fig)

if __name__ == "__main__":
    create_hrdl_architecture_diagram()
