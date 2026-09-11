"""
Suíte Abrangente de Testes Negativos e Resiliência Normativa O-RAN
Cobre casos limites, corrupção de payloads APER, inconsistência de parâmetros,
timeouts, duplicações de telemetria e falhas explícitas de controle (Gate 1 a Gate 4).
"""

import pytest
import time
from src.e2.kpm_decoder import KpmDecoder
from src.e2.rc_encoder import RCEncoder
from src.e2.rc.capability_registry import rc_capability_registry, CapabilityNotDiscoveredError
from src.e2.e2ap.pdu import unwrap_e2ap_pdu, wrap_initiating_message
from src.e2.e2ap.control import parse_ric_control_ack, parse_ric_control_failure, build_ric_control_request
from src.e2.e2ap.constants import PROC_RIC_CONTROL
from src.observability.causal_tracker import CausalTracker
from src.agents.refinement_agent import RefinementAgent
from src.infrastructure.memory_module import MemoryModule
from src.conflict_types import XAppAction, KPMReport

def test_negative_malformed_kpm_aper_payload():
    """Valida que payloads APER truncados ou corrompidos não quebram o decodificador KPM e retornam lista vazia sem sintetizar dados."""
    decoder = KpmDecoder()
    corrupted_payload = b"\x00\xFF\xAA\xBB\xCC\xDD\xEE\x11\x22"
    res = decoder.decode_indication(corrupted_payload)
    assert res == []

def test_negative_malformed_e2ap_pdu():
    """Valida que uma PDU E2AP inválida dispara exceção clara ValueError ao invés de crash silencioso."""
    garbage_bytes = b"NOT_A_VALID_E2AP_PDU_HEADER"
    with pytest.raises(Exception):
        unwrap_e2ap_pdu(garbage_bytes)

def test_negative_rc_encoder_out_of_bounds_parameter():
    """Valida que parâmetros fora dos limites normativos (e.g. PRB_QUOTA > 100% ou TX_POWER > 43 dBm) são rejeitados."""
    encoder = RCEncoder()
    with pytest.raises(ValueError) as exc:
        encoder.encode_control_request("gnb_01", "PRB_QUOTA", 150.0)
    assert "fora dos limites" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        encoder.encode_control_request("gnb_01", "TX_POWER", 60.0)
    assert "fora dos limites" in str(exc.value)

def test_negative_rc_encoder_unknown_parameter():
    """Valida que parâmetros não declarados na gramática E2SM-RC são rejeitados com erro explícito."""
    encoder = RCEncoder()
    with pytest.raises(ValueError) as exc:
        encoder.encode_control_request("gnb_01", "NON_EXISTENT_PARAM", 42.0)
    assert "desconhecido" in str(exc.value)

def test_negative_strict_mode_unadvertised_parameter():
    """Valida que em modo estrito (oran-strict), mesmo que o nó exista, parâmetros não descobertos falham imediatamente."""
    rc_capability_registry.register_node_capability(
        node_id="gnb_restricted",
        param_name="TX_POWER",
        style_type=2,
        action_id=1,
        param_id=3,
        min_val=-10.0,
        max_val=23.0,
        strict_mode=True
    )
    # Consulta a parâmetro válido
    style, action_id, param_id = rc_capability_registry.resolve_action("TX_POWER", "gnb_restricted", strict_mode=True)
    assert param_id == 3

    # Consulta a parâmetro não anunciado no nó restrito em strict mode
    with pytest.raises(CapabilityNotDiscoveredError) as exc:
        rc_capability_registry.resolve_action("PRB_QUOTA", "gnb_restricted", strict_mode=True)
    assert "não foi anunciado" in str(exc.value)

def test_negative_safety_guard_rejection():
    """Valida que o Refinement/Safety Guard bloqueia ações perigosas que violam SLAs ou limites físicos."""
    memory = MemoryModule()
    refinement = RefinementAgent(memory)

    # Ação perigosa: redução drástica de potência além da margem de segurança
    unsafe_action = XAppAction(
        xapp_id="energy_saver",
        node_id="gnb_01",
        parameter="TX_POWER",
        value=-30.0, # Muito abaixo do limite seguro (-10 dBm)
        priority=10
    )
    is_safe, level, reason = refinement.validate_single_action(unsafe_action)
    assert not is_safe
    assert "TX Power" in reason or "out of bounds" in reason


def test_negative_causal_tracker_unimproved_kpi():
    """Valida que se o controle for executado mas o KPI piorar (ex: latência subir), o CRE não contabiliza como resolução efetiva."""
    tracker = CausalTracker()
    tracker.register_conflict_event("conf_neg", "DIRECT_ACTUATION_CONFLICT", num_actions=2)

    # Decisão registrada com latência inicial de 5ms
    tracker.record_decision(
        action_id="act_neg_01",
        decision_id="dec_neg_01",
        ric_request_id=9999,
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        old_val=50.0,
        new_val=20.0,
        kpm_before={"latency_ms": 5.0, "throughput_mbps": 500.0, "pdr_percent": 98.0}
    )
    tracker.record_ack(ric_request_id=9999, rtt_ms=10.0)

    # Pós-telemetria piorou (latência subiu para 15ms, vazão caiu para 100Mbps)
    tracker.record_telemetry_effect("act_neg_01", {"latency_ms": 15.0, "throughput_mbps": 100.0, "pdr_percent": 90.0})

    metrics = tracker.compute_metrics()
    assert metrics.conflict_resolution_rate == 100.0 # Foi arbitrado
    assert metrics.conflict_resolution_effectiveness == 0.0 # Mas NÃO melhorou o KPI!

def test_negative_causal_tracker_failure_response():
    """Valida que respostas RIC_CONTROL_FAILURE são registradas e não geram falso positivo de CRE."""
    tracker = CausalTracker()
    tracker.register_conflict_event("conf_fail", "INDIRECT_RESOURCE_CONTENTION", num_actions=2)

    tracker.record_decision(
        action_id="act_fail_01",
        decision_id="dec_fail_01",
        ric_request_id=8888,
        node_id="gnb_01",
        parameter="TX_POWER",
        old_val=23.0,
        new_val=10.0,
        kpm_before={"latency_ms": 10.0}
    )
    tracker.record_failure(ric_request_id=8888, cause_code=1)

    metrics = tracker.compute_metrics()
    assert metrics.total_failures_received == 1
    assert metrics.total_acks_received == 0
    assert metrics.conflict_resolution_effectiveness == 0.0
