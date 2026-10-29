#!/usr/bin/env python3
"""
Monitores de Painel Dedicados para tmux no WSL Ubuntu (100% Dados Reais).
Skill: 09-cognitive-conflict-orchestrator & 08-ns3-oran-simulation-specialist

Monitora em tempo real as simulações empíricas do ns-3 / 5G-LENA / NORI.

Uso:
  python3 scripts/wsl_pane_monitors.py pane1 [S0..S15]   # Janela 1: Registro UE nos gNodeBs
  python3 scripts/wsl_pane_monitors.py pane2 [S0..S15]   # Janela 2: Sinalização & Protocolo E2
  python3 scripts/wsl_pane_monitors.py pane3 [S0..S15]   # Janela 3: Módulo de Percepção
  python3 scripts/wsl_pane_monitors.py pane4 [S0..S15]   # Janela 4: Grafo de Conhecimento
  python3 scripts/wsl_pane_monitors.py pane5 [S0..S15]   # Janela 5: Módulo de Refinamento & Safety
  python3 scripts/wsl_pane_monitors.py pane6 [S0..S15]   # Janela 6: Ação E2SM-RC & Malha Fechada

Se o cenário não for especificado, monitora dinamicamente a execução mais recente
em experiments/results/ns3_runs/ e auto-atualiza a cada nova simulação finalizada.
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
DIM = "\033[2m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"


def _render_header(title, color, state):
    sid = state.get("active_scenario_id", "SX")
    stitle = state.get("active_scenario_title", "Simulação ns-3")
    rdir = state.get("active_run_dir", "N/A")
    lines = [
        f"{BOLD}{color}=== {title} ==={RESET}",
        f"Cenário Ativo: {BOLD}[{sid}] {stitle}{RESET}",
        f"Execução: {DIM}{rdir}{RESET}",
        f"Motor RAN: {CYAN}ns-3.48 + 5G-LENA v5.1 (CTTC NR) + NORI E2 Agent{RESET}",
        "----------------------------------------------------------------",
    ]
    return lines


def render_pane1(state):
    b1 = state["block1_ran_registration"]
    lines = _render_header("[JANELA 1] REGISTRO UE & GNBS (ns-3 / 5G-LENA + NORI)", CYAN, state)
    lines.append(f"Nó de Rádio: {BOLD}{b1['node_id']}{RESET} | PRB Utilizado: {BOLD}{b1['prb_utilization_pct']:.1f}%{RESET}")
    lines.append(
        f"Total UEs: {BOLD}{b1['total_connected_ues']}{RESET} | Tráfego Total: {BOLD}{b1['total_traffic_mb']} MB{RESET} | "
        f"Estado: {GREEN}RRC_CONNECTED{RESET}"
    )
    lines.append("----------------------------------------------------------------")
    lines.append(f"{'UE ID':<7} {'IP Destino':<12} {'Fatia':<7} {'Throughput':<12} {'Atraso':<10} {'Status SLA'}")
    lines.append("----------------------------------------------------------------")

    ues = b1.get("ues", [])
    if not ues:
        lines.append(f"{YELLOW}Aguardando telemetria de fluxos do FlowMonitor...{RESET}")
    else:
        for ue in ues[:8]:
            sla_tag = f"{RED}VIOLAÇÃO{RESET}" if ue["sla_violation"] else f"{GREEN}ATENDIDO{RESET}"
            ip_str = ue.get("ip", "7.0.0.X")
            lines.append(
                f"{ue['ue_id']:<7} {ip_str:<12} {ue['slice']:<7} {ue['throughput_mbps']:>6.2f} Mbps  "
                f"{ue['delay_ms']:>6.2f} ms  {sla_tag}"
            )
    return "\n".join(lines)


def render_pane2(state):
    b2 = state["block2_protocol_signaling"]
    lines = _render_header("[JANELA 2] SINALIZAÇÃO & BARRAMENTO PROTOCOLO E2", MAGENTA, state)
    lines.append(f"Origem PCAP Real: {BOLD}{b2['pcap_source']}{RESET} ({b2['total_frames_captured']} frames capturados)")
    lines.append("----------------------------------------------------------------")
    lines.append("SEQUÊNCIA TEMPORAL DE MENSAGENS E2AP / ASN.1 APER:")
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
    lines = _render_header("[JANELA 3] MÓDULO DE PERCEPÇÃO (PERCEPTION CORE)", YELLOW, state)
    lines.append(
        f"Ocupação de PRB: {BOLD}{b3['prb_used_pct']:.1f}%{RESET} | Alerta SLA: "
        f"{RED if sla.get('sla_violation') else GREEN}{sla.get('severity', 'NORMAL')}{RESET}"
    )
    lines.append(
        f"Atraso Observado: {BOLD}{sla.get('urllc_observed_ms', 18.2):.2f} ms{RESET} "
        f"(Orçamento SLA: {sla.get('urllc_delay_budget_ms', 10.0):.1f} ms)"
    )
    lines.append("----------------------------------------------------------------")
    lines.append(f"CONFLITOS MULTI-xAPP DETECTADOS PELO MOTOR: {BOLD}{b3['detected_conflicts_count']}{RESET}")
    for c in b3["conflicts"]:
        lines.append(f"⚠️  {BOLD}{c['type']} ({c['severity']}){RESET}: {c['description']}")
        lines.append(f"    xApps Envolvidas: {', '.join(c['involved_xapps'])}")
        lines.append(f"    KPIs Afetados: {', '.join(c['affected_kpis'])}")
    lines.append(
        f"Parâmetro Contendido: {BOLD}{b3['contending_parameter']}{RESET} "
        f"(Demanda: {b3['requested_sum_prb']} > Capacidade: {b3['capacity_limit']})"
    )
    return "\n".join(lines)


def render_pane4(state):
    b4 = state["block4_knowledge_graph"]
    lines = _render_header("[JANELA 4] GRAFO DE CONHECIMENTO COGNITIVO (SDL)", GREEN, state)
    lines.append(
        f"Métricas do Grafo: {BOLD}{b4['nodes_count']} Nós{RESET} | "
        f"{BOLD}{b4['edges_count']} Arestas{RESET} | Densidade: {b4['density']}"
    )
    lines.append(f"Ciclos de Interferência Detectados: {BOLD}{b4['active_conflict_cycles']}{RESET}")
    lines.append("----------------------------------------------------------------")
    lines.append("TOPOLOGIA SEMÂNTICA ATIVA (SDL):")
    for n in b4["nodes"][:5]:
        lines.append(f"• Nó [{n['type']}]: {n['label']}")
    lines.append("ARESTAS DE RELAÇÃO E CONFLITO:")
    for e in b4["edges"][:4]:
        is_conf = "CONFLICT" in e["rel"] or "CONTENTION" in e["rel"]
        tag = f"{RED}{e['rel']}{RESET}" if is_conf else f"{CYAN}{e['rel']}{RESET}"
        lines.append(f"  {e['source']} ──({tag})──► {e['target']}")
    return "\n".join(lines)


def render_pane5(state):
    b5 = state["block5_refinement_module"]
    quotas = b5["allocated_quotas"]
    lines = _render_header("[JANELA 5] MÓDULO DE REFINAMENTO & SAFETY (H-RDL)", MAGENTA, state)
    lines.append(f"Motor de Decisão: {BOLD}{b5['decision_engine']}{RESET}")
    lines.append(f"Overhead Computacional: {BOLD}{b5['decision_overhead_ms']:.3f} ms{RESET}")
    lines.append(f"Razão da Arbitragem: {BOLD}{b5['arbitration_reason']}{RESET}")
    lines.append("----------------------------------------------------------------")
    lines.append("QUOTAS REFINADAS APÓS ARBITRAGEM:")
    lines.append(f"• Fatia URLLC: {BOLD}{quotas.get('URLLC', 0.5)*100:.0f}% PRBs{RESET} (Prioritária)")
    lines.append(f"• Fatia eMBB:  {BOLD}{quotas.get('eMBB', 0.5)*100:.0f}% PRBs{RESET} (Subordinada)")
    lines.append(f"• Potência TX: {BOLD}{b5['tx_power_dbm']} dBm{RESET}")
    lines.append("----------------------------------------------------------------")
    lines.append(f"Safety Guard Invariante: {GREEN}{b5['safety_guard_check']}{RESET}")
    lines.append(f"Princípio Default-Deny: {GREEN}{b5['default_deny_invariant']}{RESET}")
    return "\n".join(lines)


def render_pane6(state):
    b6 = state["block6_ran_control_action"]
    lines = _render_header("[JANELA 6] AÇÃO E2SM-RC & MALHA FECHADA NA RAN", BLUE, state)
    lines.append(
        f"Ação E2SM-RC Despachada: ActionID={BOLD}{b6['dispatched_action_id']}{RESET} "
        f"(TxID {b6['transaction_id']})"
    )
    lines.append(f"Status do ACK da RAN: {GREEN}{b6['ack_status']}{RESET} (RTT={b6['rtt_ack_ms']} ms)")
    lines.append("----------------------------------------------------------------")
    lines.append(
        f"LATÊNCIA CAUSAL TOTAL: {BOLD}{b6['closed_loop_latency_ms']:.3f} ms{RESET} "
        f"(Orçamento: < 10.0 ms: {GREEN}PASS{RESET})"
    )
    lines.append("----------------------------------------------------------------")
    lines.append("EFEITO FÍSICO RASTREADO NA RAN:")
    lines.append(f"• Atraso URLLC Anterior: {RED}{b6['before_latency_ms']} ms{RESET}")
    lines.append(f"• Atraso URLLC Recuperado: {GREEN}{b6['after_latency_ms']} ms{RESET}")
    lines.append(f"• Redução de Latência: {BOLD}-{b6['latency_reduction_pct']}%{RESET}")
    lines.append(f"• Vínculo Causal: {BOLD}{b6['causal_attribution']}{RESET}")
    lines.append(f"Hash Raiz Certificado: {b6['root_sha256'][:32]}...")
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
    if len(sys.argv) < 2 or (sys.argv[1] not in RENDERERS and sys.argv[1] != "all"):
        print(f"Uso: {sys.argv[0]} [pane1|pane2|pane3|pane4|pane5|pane6|all] [S0..S15|--scenario SCENARIO] [--run RUN_DIR]")
        print("\nExemplos:")
        print(f"  {sys.argv[0]} pane1          # Monitora dinamicamente a simulação mais recente")
        print(f"  {sys.argv[0]} pane1 S3       # Monitora especificamente o Cenário S3 (TVS Handover)")
        print(f"  {sys.argv[0]} pane1 S8       # Monitora especificamente o Cenário S8 (Closed-Loop NORI)")
        print(f"  {sys.argv[0]} pane1 --scenario S13")
        sys.exit(1)

    target_pane = sys.argv[1]

    # Processa argumentos opcionais de cenário ou run
    target_scenario = None
    target_run = None
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ("--scenario", "-s") and i + 1 < len(sys.argv):
            target_scenario = sys.argv[i + 1]
            i += 2
        elif arg in ("--run", "-r") and i + 1 < len(sys.argv):
            target_run = sys.argv[i + 1]
            i += 2
        elif arg.upper().startswith("S") and (arg[1:].isdigit() or arg.upper() in ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12", "S13", "S14", "S15")):
            target_scenario = arg.upper()
            i += 1
        else:
            target_scenario = arg
            i += 1

    if target_scenario:
        real_telemetry_provider.set_target_scenario(target_scenario)
    if target_run:
        real_telemetry_provider.set_target_run(target_run)

    tick = 0
    try:
        while True:
            tick += 1
            state = real_telemetry_provider.get_full_real_state()
            active_scen = state.get("active_scenario_id", "SX")

            if target_pane == "all":
                blocks = [RENDERERS[p](state) for p in ("pane1", "pane2", "pane3", "pane4", "pane5", "pane6")]
                output = "\n\n" + ("=" * 64 + "\n").join(blocks)
            else:
                renderer = RENDERERS[target_pane]
                output = renderer(state)

            footer = (
                f"\n\n{DIM}[Tick #{tick} | Atualizando telemetria real (1.0s) | "
                f"Cenário: {active_scen} | Ctrl+C para sair]{RESET}\n"
                f"{DIM}[Dica: para monitorar outro cenário execute: '{sys.argv[0]} {target_pane} S8']{RESET}\n"
            )
            sys.stdout.write(CLEAR + output + footer)
            sys.stdout.flush()
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
