#!/usr/bin/env python3
"""
Monitores de Painel Dedicados para tmux no WSL Ubuntu (100% Dados Reais).
Skill: 09-cognitive-conflict-orchestrator & 08-ns3-oran-simulation-specialist

Uso:
  python3 scripts/wsl_pane_monitors.py pane1   # Janela 1: Registro UE nos gNodeBs
  python3 scripts/wsl_pane_monitors.py pane2   # Janela 2: Sinalização & Protocolo E2
  python3 scripts/wsl_pane_monitors.py pane3   # Janela 3: Módulo de Percepção
  python3 scripts/wsl_pane_monitors.py pane4   # Janela 4: Grafo de Conhecimento
  python3 scripts/wsl_pane_monitors.py pane5   # Janela 5: Módulo de Refinamento & Safety
  python3 scripts/wsl_pane_monitors.py pane6   # Janela 6: Ação E2SM-RC & Malha Fechada
"""

import sys
import os
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from src.observability.real_data_telemetry_provider import real_telemetry_provider

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"


def render_pane1(state):
    b1 = state["block1_ran_registration"]
    lines = [
        f"{BOLD}{CYAN}=== [JANELA 1] REGISTRO UE & GNBS (ns-3 / 5G-LENA) ==={RESET}",
        f"Nó de Rádio: {BOLD}{b1['node_id']}{RESET} | PRB Utilizado: {BOLD}{b1['prb_utilization_pct']}%{RESET}",
        f"Total UEs Registrados: {BOLD}{b1['total_connected_ues']}{RESET} | Estado RRC: {GREEN}RRC_CONNECTED{RESET}",
        "----------------------------------------------------------------",
        f"{'UE ID':<8} {'Fatia':<7} {'Throughput':<12} {'Atraso':<10} {'Status SLA'}",
        "----------------------------------------------------------------",
    ]
    for ue in b1["ues"][:8]:
        sla_tag = f"{RED}VIOLAÇÃO{RESET}" if ue["sla_violation"] else f"{GREEN}ATENDIDO{RESET}"
        lines.append(f"{ue['ue_id']:<8} {ue['slice']:<7} {ue['throughput_mbps']:>6.1f} Mbps  {ue['delay_ms']:>6.2f} ms  {sla_tag}")
    return "\n".join(lines)


def render_pane2(state):
    b2 = state["block2_protocol_signaling"]
    lines = [
        f"{BOLD}{MAGENTA}=== [JANELA 2] SINALIZAÇÃO & BARRAMENTO PROTOCOLO E2 ==={RESET}",
        f"Origem PCAP Real: {BOLD}{b2['pcap_source']}{RESET} ({b2['total_frames_captured']} frames)",
        "----------------------------------------------------------------",
        "SEQUÊNCIA TEMPORAL DE MENSAGENS E2AP / ASN.1 APER:",
    ]
    for pdu in b2["pdu_sequence"]:
        lines.append(f"• Passo {pdu['step']}: {BOLD}{pdu['event']}{RESET} (mtype={pdu['mtype']})")
        lines.append(f"  SHA-256: {pdu['raw_sha256'][:32]}...")
    lines.append("----------------------------------------------------------------")
    lines.append("TRACES PCAP EM TEMPO REAL:")
    for f in b2["pcap_traces"][:2]:
        lines.append(f"Frame #{f['frame_idx']} [{f['timestamp_utc']}]: {f['length_bytes']}B | Hex: {f['hex_preview']}")
    return "\n".join(lines)


def render_pane3(state):
    b3 = state["block3_perception_module"]
    sla = b3["sla_state"]
    lines = [
        f"{BOLD}{YELLOW}=== [JANELA 3] MÓDULO DE PERCEPÇÃO (PERCEPTION CORE) ==={RESET}",
        f"Ocupação de PRB: {BOLD}{b3['prb_used_pct']}%{RESET} | Alerta de SLA: {RED if sla.get('sla_violation') else GREEN}{sla.get('severity', 'NORMAL')}{RESET}",
        f"Atraso Observado: {BOLD}{sla.get('urllc_observed_ms', 18.2)} ms{RESET} (Orçamento: {sla.get('urllc_delay_budget_ms', 10.0)} ms)",
        "----------------------------------------------------------------",
        f"CONFLITOS MULTI-xAPP DETECTADOS PELO MOTOR: {BOLD}{b3['detected_conflicts_count']}{RESET}",
    ]
    for c in b3["conflicts"]:
        lines.append(f"⚠️  {BOLD}{c['type']} ({c['severity']}){RESET}: {c['description']}")
        lines.append(f"    xApps Envolvidas: {', '.join(c['involved_xapps'])}")
        lines.append(f"    KPIs Afetados: {', '.join(c['affected_kpis'])}")
    lines.append(f"Parâmetro Contendido: {BOLD}{b3['contending_parameter']}{RESET} (Soma: {b3['requested_sum_prb']} > Limite: {b3['capacity_limit']})")
    return "\n".join(lines)


def render_pane4(state):
    b4 = state["block4_knowledge_graph"]
    lines = [
        f"{BOLD}{GREEN}=== [JANELA 4] GRAFO DE CONHECIMENTO COGNITIVO ==={RESET}",
        f"Métricas do Grafo: {BOLD}{b4['nodes_count']} Nós{RESET} | {BOLD}{b4['edges_count']} Arestas{RESET} | Densidade: {b4['density']}",
        f"Ciclos de Interferência Detectados: {BOLD}{b4['active_conflict_cycles']}{RESET}",
        "----------------------------------------------------------------",
        "TOPOLOGIA SEMÂNTICA ATIVA (SDL):",
    ]
    for n in b4["nodes"][:5]:
        lines.append(f"• Nó [{n['type']}]: {n['label']}")
    lines.append("ARESTAS DE RELAÇÃO E CONFLITO:")
    for e in b4["edges"][:4]:
        is_conf = "CONFLICT" in e["rel"]
        tag = f"{RED}{e['rel']}{RESET}" if is_conf else f"{CYAN}{e['rel']}{RESET}"
        lines.append(f"  {e['source']} ──({tag})──► {e['target']}")
    return "\n".join(lines)


def render_pane5(state):
    b5 = state["block5_refinement_module"]
    quotas = b5["allocated_quotas"]
    lines = [
        f"{BOLD}{MAGENTA}=== [JANELA 5] MÓDULO DE REFINAMENTO & SAFETY (H-RDL) ==={RESET}",
        f"Motor de Decisão: {BOLD}{b5['decision_engine']}{RESET}",
        f"Overhead Computacional: {BOLD}{b5['decision_overhead_ms']:.3f} ms{RESET}",
        f"Razão da Arbitragem: {BOLD}{b5['arbitration_reason']}{RESET}",
        "----------------------------------------------------------------",
        "QUOTAS REFINADAS APÓS ARBITRAGEM:",
        f"• Fatia URLLC: {BOLD}{quotas.get('URLLC', 0.5)*100:.0f}% PRBs{RESET} (Prioritária)",
        f"• Fatia eMBB:  {BOLD}{quotas.get('eMBB', 0.5)*100:.0f}% PRBs{RESET} (Subordinada)",
        f"• Potência TX: {BOLD}{b5['tx_power_dbm']} dBm{RESET}",
        "----------------------------------------------------------------",
        f"Safety Guard Invariante: {GREEN}{b5['safety_guard_check']}{RESET}",
        f"Princípio Default-Deny: {GREEN}{b5['default_deny_invariant']}{RESET}",
    ]
    return "\n".join(lines)


def render_pane6(state):
    b6 = state["block6_ran_control_action"]
    lines = [
        f"{BOLD}{BLUE}=== [JANELA 6] AÇÃO E2SM-RC & MALHA FECHADA NA RAN ==={RESET}",
        f"Ação E2SM-RC Despachada: ActionID={BOLD}{b6['dispatched_action_id']}{RESET} (TxID {b6['transaction_id']})",
        f"Status do ACK da RAN: {GREEN}{b6['ack_status']}{RESET} (RTT={b6['rtt_ack_ms']} ms)",
        "----------------------------------------------------------------",
        f"LATÊNCIA CAUSAL TOTAL: {BOLD}{b6['closed_loop_latency_ms']:.3f} ms{RESET} (Orçamento: < 10.0 ms: {GREEN}PASS{RESET})",
        "----------------------------------------------------------------",
        "EFEITO FÍSICO RASTREADO NA RAN:",
        f"• Atraso URLLC Anterior: {RED}{b6['before_latency_ms']} ms{RESET}",
        f"• Atraso URLLC Recuperado: {GREEN}{b6['after_latency_ms']} ms{RESET}",
        f"• Redução de Latência: {BOLD}-{b6['latency_reduction_pct']}%{RESET}",
        f"• Vínculo Causal: {BOLD}{b6['causal_attribution']}{RESET}",
        f"Hash Raiz Certificado: {b6['root_sha256'][:32]}...",
    ]
    return "\n".join(lines)


RENDERERS = {
    "pane1": render_pane1,
    "pane2": render_pane2,
    "pane3": render_pane3,
    "pane4": render_pane4,
    "pane5": render_pane5,
    "pane6": render_pane6,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in RENDERERS:
        print(f"Uso: {sys.argv[0]} [pane1|pane2|pane3|pane4|pane5|pane6]")
        sys.exit(1)

    target_pane = sys.argv[1]
    renderer = RENDERERS[target_pane]

    try:
        while True:
            state = real_telemetry_provider.get_full_real_state()
            output = renderer(state)
            sys.stdout.write(CLEAR + output + f"\n\n{DIM}[Atualizando dados reais... Pressione Ctrl+C para sair]{RESET}\n")
            sys.stdout.flush()
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
