"""
Testes de Interoperabilidade E2SM-RC / NORI
Valida o ciclo completo de mapeamento RDL -> RC -> E2AP-PDU com ProtocolIE-Container e o processamento de ACK/Failure.
"""

import pytest
from src.conflict_types import XAppAction
from src.e2.rc.mapper import RCMapper
from src.e2.rc.capability_registry import rc_capability_registry, CapabilityNotDiscoveredError
from src.e2.e2ap.pdu import unwrap_e2ap_pdu, wrap_successful_outcome, wrap_unsuccessful_outcome
from src.e2.e2ap.control import parse_ric_control_ack, parse_ric_control_failure, RICcontrolAcknowledge, RICcontrolFailure, RICcontrolRequest
from src.e2.e2ap.constants import (
    PROC_RIC_CONTROL,
    IE_RIC_REQUEST_ID,
    IE_RAN_FUNCTION_ID,
    IE_RIC_CONTROL_HEADER,
    IE_RIC_CONTROL_MESSAGE,
    IE_RIC_CONTROL_ACK_REQUEST
)

def test_nori_rc_control_request_full_e2ap_pdu_roundtrip():
    """
    Valida se a mensagem enviada ao NORI está empacotada na E2AP-PDU com procedureCode=4 (id-RICcontrol)
    e contém o ProtocolIE-Container com todos os IEs obrigatórios.
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

    # Valida decodificação do ProtocolIE-Container
    req = RICcontrolRequest()
    req.from_aper(inner_bytes)
    val = req()
    assert val['ranFunctionID'] == 3
    assert val['ricRequestID']['ricInstanceID'] == 10
    assert len(val['protocolIEs']) == 5
    ie_ids = [ie['id'] for ie in val['protocolIEs']]
    assert IE_RIC_REQUEST_ID in ie_ids
    assert IE_RAN_FUNCTION_ID in ie_ids
    assert IE_RIC_CONTROL_HEADER in ie_ids
    assert IE_RIC_CONTROL_MESSAGE in ie_ids
    assert IE_RIC_CONTROL_ACK_REQUEST in ie_ids

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

def test_nori_rc_strict_mode_capability_not_discovered():
    """
    Valida que em modo estrito O_RAN_INTEROP (strict_mode=True), defaults são estritamente proibidos
    e uma exceção CapabilityNotDiscoveredError é levantada se o nó não foi descoberto.
    """
    with pytest.raises(CapabilityNotDiscoveredError):
        rc_capability_registry.resolve_action("PRB_QUOTA", node_id="gnb_unknown_node", strict_mode=True)
