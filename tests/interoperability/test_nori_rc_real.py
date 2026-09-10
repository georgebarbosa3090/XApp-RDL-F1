"""
Testes de Interoperabilidade E2SM-RC / NORI
Valida o ciclo completo de mapeamento RDL -> RC -> E2AP-PDU e o processamento de ACK/Failure.
"""

import pytest
from src.conflict_types import XAppAction
from src.e2.rc.mapper import RCMapper
from src.e2.rc.capability_registry import rc_capability_registry
from src.e2.e2ap.pdu import unwrap_e2ap_pdu, wrap_successful_outcome, wrap_unsuccessful_outcome
from src.e2.e2ap.control import parse_ric_control_ack, parse_ric_control_failure, RICcontrolAcknowledge, RICcontrolFailure
from src.e2.e2ap.constants import PROC_RIC_CONTROL

def test_nori_rc_control_request_full_e2ap_pdu_roundtrip():
    """
    Valida se a mensagem enviada ao NORI está empacotada na E2AP-PDU com procedureCode=204.
    """
    mapper = RCMapper(ran_function_id=3)
    action = XAppAction(
        xapp_id="xslice",
        node_id="gnb_001",
        parameter="PRB_QUOTA",
        value=75.0,
        priority=90
    )
    ctx = mapper.map_action_to_control_request(action, requestor_id=1, instance_id=10)
    
    # Valida envelope E2AP-PDU
    pdu_type, proc_code, crit, inner_bytes = unwrap_e2ap_pdu(ctx.pdu_aper)
    assert pdu_type == "initiatingMessage"
    assert proc_code == PROC_RIC_CONTROL
    assert len(inner_bytes) > 0

def test_nori_rc_control_ack_full_cycle():
    """
    Valida o recebimento e processamento de um RICcontrolAcknowledge encapsulado em E2AP-PDU.
    """
    # Monta ACK interno
    ack_ie = RICcontrolAcknowledge()
    ack_ie.set_val({
        'ricRequestID': {'ricRequestorID': 1, 'ricInstanceID': 10},
        'ranFunctionID': 3
    })
    ack_bytes = ack_ie.to_aper()
    pdu_ack = wrap_successful_outcome(PROC_RIC_CONTROL, ack_bytes)
    
    res = parse_ric_control_ack(pdu_ack)
    assert res["status"] == "ACKNOWLEDGED"
    assert res["requestor_id"] == 1
    assert res["instance_id"] == 10
    assert res["ran_function_id"] == 3

def test_nori_rc_dynamic_capability_registration_and_dispatch():
    """
    Valida o registro de novas capacidades de nós e o despacho customizado de parâmetros.
    """
    rc_capability_registry.register_node_capability(
        node_id="gnb_special",
        param_name="BEAM_DOWNTILT",
        style_type=4,
        action_id=2,
        param_id=12,
        min_val=0.0,
        max_val=15.0,
        unit="degrees"
    )
    style, action_id, param_id = rc_capability_registry.resolve_action("BEAM_DOWNTILT", "gnb_special")
    assert style == 4
    assert action_id == 2
    assert param_id == 12
