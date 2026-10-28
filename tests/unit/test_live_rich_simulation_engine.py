"""
Testes Unitários para o Motor de Simulação Rica 6-Blocos O-RAN.
Valida conformidade funcional e limites 3GPP/O-RAN WG3 dos 6 blocos integrados.
"""

import pytest
from src.observability.live_rich_simulation_engine import RichSimulationEngine


def test_rich_simulation_engine_initialization():
    engine = RichSimulationEngine()
    state = engine.get_full_state()

    assert "block1_ran_registration" in state
    assert "block2_protocol_signaling" in state
    assert "block3_perception_module" in state
    assert "block4_knowledge_graph" in state
    assert "block5_refinement_module" in state
    assert "block6_ran_control_action" in state
    assert state["block1_ran_registration"]["total_connected_ues"] >= 10


def test_rich_simulation_engine_tvs_scenario_step():
    engine = RichSimulationEngine()
    engine.trigger_scenario("tvs_conflict")
    state = engine.step()

    # Bloco 1: UEs
    ues = state["block1_ran_registration"]["ues"]
    assert len(ues) > 0
    assert all("sinr_db" in u and "thp_dl_mbps" in u for u in ues)

    # Bloco 2: Protocol traces
    traces = state["block2_protocol_signaling"]["latest_traces"]
    assert len(traces) > 0
    assert any("RIC_INDICATION" in t.get("mtype_name", "") for t in traces)

    # Bloco 3: Percepção e Conflito Direto
    conflicts = state["block3_perception_module"]["active_conflicts"]
    assert len(conflicts) > 0
    assert conflicts[0]["type"] == "DIRECT"

    # Bloco 4: Grafo de Conhecimento
    kg = state["block4_knowledge_graph"]
    assert kg["metrics"]["conflict_cycles_count"] >= 1
    assert any(e.get("rel") == "DIRECT_CONFLICT" for e in kg["edges"])

    # Bloco 5: Refinamento TVS
    ref = state["block5_refinement_module"]
    assert ref["strategy"] == "TVS"
    assert ref["safety_guard"]["is_safe"] is True

    # Bloco 6: Ação E2SM-RC e Latência Causal < 10 ms
    b6 = state["block6_ran_control_action"]
    assert b6["closed_loop_latency_ms"] < b6["budget_ms"]
    assert len(b6["recent_actions"]) > 0


def test_rich_simulation_engine_eevs_scenario_step():
    engine = RichSimulationEngine()
    engine.trigger_scenario("eevs_conflict")
    state = engine.step()

    conflicts = state["block3_perception_module"]["active_conflicts"]
    assert len(conflicts) > 0
    assert conflicts[0]["type"] == "INDIRECT"

    ref = state["block5_refinement_module"]
    assert ref["strategy"] == "EEVS"


def test_rich_simulation_engine_pause_resume():
    engine = RichSimulationEngine()
    engine.is_paused = True
    state1 = engine.step()
    tick1 = state1["tick"]

    state2 = engine.step()
    assert state2["tick"] == tick1
    assert state2["is_paused"] is True
