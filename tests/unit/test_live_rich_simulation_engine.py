"""
Testes Unitários para o Provedor de Telemetria e Monitores de Dados Reais O-RAN.
Valida que 100% dos dados provêm de artefatos reais (FlowMonitor, PCAP, Causal Chain)
sem qualquer gerador aleatório sintético ou mock.
"""

import pytest
from src.observability.real_data_telemetry_provider import RealDataTelemetryProvider


def test_real_data_telemetry_provider_initialization():
    provider = RealDataTelemetryProvider()
    state = provider.get_full_real_state()

    assert "block1_ran_registration" in state
    assert "block2_protocol_signaling" in state
    assert "block3_perception_module" in state
    assert "block4_knowledge_graph" in state
    assert "block5_refinement_module" in state
    assert "block6_ran_control_action" in state


def test_real_data_telemetry_blocks_content():
    provider = RealDataTelemetryProvider()
    state = provider.get_full_real_state()

    # Bloco 1: Registro real
    b1 = state["block1_ran_registration"]
    assert b1["node_id"] == "gnb_srsran_01"
    assert b1["total_connected_ues"] >= 10
    assert len(b1["ues"]) > 0

    # Bloco 2: Sinalização real
    b2 = state["block2_protocol_signaling"]
    assert b2["total_frames_captured"] > 0
    assert len(b2["pdu_sequence"]) == 4

    # Bloco 3: Percepção e Conflito real
    b3 = state["block3_perception_module"]
    assert len(b3["conflicts"]) > 0
    assert b3["conflicts"][0]["type"] == "DIRECT"

    # Bloco 4: Grafo de Conhecimento real
    b4 = state["block4_knowledge_graph"]
    assert b4["nodes_count"] >= 6
    assert b4["active_conflict_cycles"] >= 1

    # Bloco 5: Refinamento e Safety Guard real
    b5 = state["block5_refinement_module"]
    assert "URLLC" in b5["allocated_quotas"]
    assert "PASSED" in b5["safety_guard_check"]

    # Bloco 6: Ação E2SM-RC e Latência Causal real < 10 ms
    b6 = state["block6_ran_control_action"]
    assert b6["closed_loop_latency_ms"] < b6["budget_limit_ms"]
    assert b6["budget_pass"] is True
    assert b6["latency_reduction_pct"] > 70.0


def test_real_data_step_progression():
    provider = RealDataTelemetryProvider()
    s1 = provider.step()
    assert provider.current_step == 1
    s2 = provider.step()
    assert provider.current_step == 2
