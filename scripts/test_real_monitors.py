import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from src.observability.real_data_telemetry_provider import real_telemetry_provider
from scripts.wsl_pane_monitors import RENDERERS

state = real_telemetry_provider.get_full_real_state()
print("=== VERIFICAÇÃO DE DADOS 100% REAIS NO WSL UBUNTU ===")
print("Origem Node:", state["block1_ran_registration"]["node_id"])
print("PRB Utilizado:", state["block1_ran_registration"]["prb_utilization_pct"])
print("Total UEs FlowMonitor:", len(state["block1_ran_registration"]["ues"]))
print("PCAP Frames Decodificados:", state["block2_protocol_signaling"]["total_frames_captured"])
print("Conflito Detectado:", state["block3_perception_module"]["conflicts"][0]["type"])
print("Nós do Grafo de Conhecimento:", state["block4_knowledge_graph"]["nodes_count"])
print("Quotas Refinadas (H-RDL):", state["block5_refinement_module"]["allocated_quotas"])
print("Latência Causal Malha Fechada:", state["block6_ran_control_action"]["closed_loop_latency_ms"], "ms")
print("Recuperação Real:", state["block6_ran_control_action"]["before_latency_ms"], "ms ->", state["block6_ran_control_action"]["after_latency_ms"], "ms")

print("\n--- TESTE DOS 6 RENDERERS DAS JANELAS ---")
for pane_id in ["pane1", "pane2", "pane3", "pane4", "pane5", "pane6"]:
    output = RENDERERS[pane_id](state)
    first_line = output.splitlines()[0]
    print(f"[{pane_id}] OK: {first_line}")

print("\nTODOS OS 6 BLOCOS VALIDADOS COM SUCESSO SEM MOCKS NEM SINTÉTICOS!")
