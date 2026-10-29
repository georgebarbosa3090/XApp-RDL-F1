#!/usr/bin/env python3
"""
Monitores tmux no WSL para artefatos vinculados às execuções ns-3.
Skill: 09-cognitive-conflict-orchestrator & 08-ns3-oran-simulation-specialist

Exibe FlowMonitor e logs disponíveis, além de indicar explicitamente a
ausência de evidências KPM, RDL ou E2SM-RC na execução selecionada.

Uso:
  python3 scripts/wsl_pane_monitors.py pane1 [S0..S15]   # Estado e fluxos FlowMonitor
  python3 scripts/wsl_pane_monitors.py pane2 [S0..S15]   # Log e artefatos E2/KPM
  python3 scripts/wsl_pane_monitors.py pane3 [S0..S15]   # KPIs do FlowMonitor
  python3 scripts/wsl_pane_monitors.py pane4 [S0..S15]   # Endpoints IP observados
  python3 scripts/wsl_pane_monitors.py pane5 [S0..S15]   # Evidência de decisão RDL
  python3 scripts/wsl_pane_monitors.py pane6 [S0..S15]   # Evidência E2SM-RC

Se o cenário não for especificado, monitora dinamicamente a execução mais recente
em experiments/results/ns3_runs/, inclusive o log durante a execução. As métricas
do FlowMonitor só ficam disponíveis quando o XML é produzido ao final.
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
    status = state.get("run_status", "unknown").upper()
    status_message = state.get("run_status_message", "")
    lines = [
        f"{BOLD}{color}=== {title} ==={RESET}",
        f"Cenário Ativo: {BOLD}[{sid}] {stitle}{RESET}",
        f"Execução: {DIM}{rdir}{RESET}",
        f"Estado: {BOLD}{status}{RESET} | {status_message}",
        f"Motor RAN: {CYAN}ns-3 + 5G-LENA{RESET} | Atualização: 1 s",
        "----------------------------------------------------------------",
    ]
    return lines


def render_pane1(state):
    b1 = state["block1_ran_registration"]
    lines = _render_header("[JANELA 1] EXECUÇÃO E FLUXOS FLOWMONITOR", CYAN, state)
    prb = b1["prb_utilization_pct"]
    lines.append(
        f"Fluxos com dados: {BOLD}{b1['active_data_flows']}{RESET} | "
        f"RX: {b1['total_packets_rx']} pacotes | TX: {b1['total_packets_tx']} | "
        f"Perda: {b1['total_packets_lost']} | Volume RX: {b1['total_traffic_mb']} MB"
    )
    lines.append(f"PRB: {prb if prb is not None else 'não fornecido pelo FlowMonitor'}")
    lines.append("----------------------------------------------------------------")
    lines.append(f"{'Flow':<7} {'Origem':<16} {'Destino':<16} {'Vazão':<12} {'Atraso':<10} {'Perda'}")
    lines.append("----------------------------------------------------------------")
    
    flows = b1.get("flows", [])
    if not flows:
        if b1.get("flowmonitor_error"):
            lines.append(f"{RED}FlowMonitor inválido: {b1['flowmonitor_error']}{RESET}")
        else:
            lines.append(f"{YELLOW}Aguardando flowmonitor.xml desta execução...{RESET}")
    else:
        for flow in flows[:8]:
            loss_pct = (
                100 * flow["lost_pkts"] / flow["tx_pkts"]
                if flow["tx_pkts"]
                else 0.0
            )
            lines.append(
                f"{flow['flow_id']:<7} {str(flow['src_ip'] or 'N/D'):<16} "
                f"{str(flow['dst_ip'] or 'N/D'):<16} {flow['throughput_mbps']:>6.2f} Mbps  "
                f"{flow['delay_ms']:>6.2f} ms  {loss_pct:.2f}%"
            )
    return "\n".join(lines)


def render_pane2(state):
    b2 = state["block2_protocol_signaling"]
    lines = _render_header("[JANELA 2] LOG DA SIMULAÇÃO E EVIDÊNCIAS E2", MAGENTA, state)
    lines.append("----------------------------------------------------------------")
    lines.append(
        f"PCAP E2 desta execução: "
        f"{GREEN + 'presente' + RESET if b2['e2_pcap_available'] else YELLOW + 'não encontrado' + RESET}"
    )
    lines.append(
        f"Artefato KPM desta execução: "
        f"{GREEN + 'presente' + RESET if b2['kpm_artifact_available'] else YELLOW + 'não encontrado' + RESET}"
    )
    lines.append("Últimas linhas de execution.log:")
    log_lines = b2["recent_execution_log"]
    if log_lines:
        lines.extend(f"  {line}" for line in log_lines[-6:])
    else:
        lines.append(f"{DIM}Log ainda não disponível.{RESET}")
    return "\n".join(lines)


def render_pane3(state):
    b3 = state["block3_perception_module"]
    lines = _render_header("[JANELA 3] KPIs DO FLOWMONITOR", YELLOW, state)
    lines.append(f"Vazão agregada: {b3['throughput_mbps'] if b3['throughput_mbps'] is not None else 'N/D'} Mbps")
    lines.append(f"Atraso médio por pacote: {b3['mean_delay_ms'] if b3['mean_delay_ms'] is not None else 'N/D'} ms")
    lines.append(f"Perda de pacotes: {b3['loss_ratio_pct'] if b3['loss_ratio_pct'] is not None else 'N/D'}%")
    lines.append(f"PRB: não fornecido pelo FlowMonitor | SLA: {b3['sla_evaluation']}")
    lines.append("----------------------------------------------------------------")
    lines.append(f"Detecção de conflitos: {b3['conflict_detection']}")
    return "\n".join(lines)


def render_pane4(state):
    b4 = state["block4_knowledge_graph"]
    lines = _render_header("[JANELA 4] TOPOLOGIA IP OBSERVADA", GREEN, state)
    lines.append(
        f"Métricas do Grafo: {BOLD}{b4['nodes_count']} Nós{RESET} | "
        f"{BOLD}{b4['edges_count']} Fluxos{RESET} | Fonte: {b4['topology_source']}"
    )
    lines.append("----------------------------------------------------------------")
    lines.append("Endpoints IP encontrados no FlowMonitor:")
    for n in b4["nodes"][:5]:
        lines.append(f"• Nó [{n['type']}]: {n['label']}")
    lines.append("Fluxos:")
    for e in b4["edges"][:4]:
        lines.append(f"  {e['source']} ──({e['rel']})──► {e['target']}")
    if b4["active_conflict_cycles"] is None:
        lines.append("Conflitos: não avaliados por este artefato.")
    return "\n".join(lines)


def render_pane5(state):
    b5 = state["block5_refinement_module"]
    lines = _render_header("[JANELA 5] DECISÃO RDL E SAFETY", MAGENTA, state)
    lines.append("----------------------------------------------------------------")
    lines.append(f"Artefato de decisão desta execução: {b5['decision_status']}")
    if not b5["decision_artifact_available"]:
        lines.append("Sem evidência para exibir política, arbitragem ou resultado do Safety Guard.")
    return "\n".join(lines)


def render_pane6(state):
    b6 = state["block6_ran_control_action"]
    lines = _render_header("[JANELA 6] AÇÃO E2SM-RC E MALHA FECHADA", BLUE, state)
    lines.append(f"Request E2SM-RC desta execução: {'presente' if b6['control_request_available'] else 'não encontrado'}")
    lines.append(f"ACK E2SM-RC desta execução: {'presente' if b6['control_ack_available'] else 'não encontrado'}")
    if not b6["closed_loop_evidence_available"]:
        lines.append("Malha fechada não comprovada: faltam evidências de request e ACK associadas a este run.")
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
