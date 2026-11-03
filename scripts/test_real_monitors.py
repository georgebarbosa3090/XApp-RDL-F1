"""Smoke-test the six terminal renderers against the currently selected run."""

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from src.observability.real_data_telemetry_provider import real_telemetry_provider
from scripts.wsl_pane_monitors import RENDERERS


state = real_telemetry_provider.get_full_real_state()
block1 = state["block1_ran_registration"]
block2 = state["block2_protocol_signaling"]
block3 = state["block3_perception_module"]
block5 = state["block5_refinement_module"]
block6 = state["block6_ran_control_action"]

print("=== VERIFICAÇÃO DOS PAINÉIS DE MONITORAMENTO ===")
print("Execução:", state["active_run_dir"])
print("Status:", state["run_status"], "-", state["run_status_message"])
print("FlowMonitor disponível:", block1["flowmonitor_available"])
print("Fluxos observados:", block1["active_data_flows"])
connected_ues = block1["total_connected_ues"]
prb_utilization = block1["prb_utilization_pct"]
print("UEs conectados:", connected_ues if connected_ues is not None else "não informado")
print("Utilização PRB:", prb_utilization if prb_utilization is not None else "não informada")
print("PCAP E2/KPM:", block2["e2_pcap_available"], "/", block2["kpm_artifact_available"])
print("Avaliação SLA:", block3["sla_evaluation"])
print("Decisão RDL disponível:", block5["decision_artifact_available"])
print(
    "Request/ACK E2SM-RC:",
    block6["control_request_available"],
    "/",
    block6["control_ack_available"],
)

print("\n--- TESTE DOS 6 RENDERERS ---")
for pane_id, renderer in RENDERERS.items():
    output = renderer(state)
    print(f"[{pane_id}] OK: {output.splitlines()[0]}")

print("\nOs renderers exibem o estado e as evidências disponíveis para esta execução.")
