import pytest
from src.conflict_types import XAppAction, RDLDecision
from src.e2.rc.mapper import RCMapper
from src.e2.e2ap.control import RICcontrolRequest

def test_rc_mapper_decision_to_e2ap_pdu():
    """Valida o mapeamento formal de uma RDLDecision em mensagens E2AP RICcontrolRequest."""
    mapper = RCMapper(ran_function_id=3)
    
    actions = [
        XAppAction(xapp_id="xslice", node_id="gnb_01", parameter="PRB_QUOTA", value=80.0, priority=90),
        XAppAction(xapp_id="energy_saving", node_id="gnb_01", parameter="TX_POWER", value=20.0, priority=65)
    ]
    
    decision = RDLDecision(
        decision_id="dec_test_01",
        selected_actions=actions,
        reason="RESOLVED_AND_PASSTHROUGH",
        strategy_used="TVS_MULTI_OBJECTIVE"
    )
    
    control_contexts = mapper.map_decision_to_control_requests(decision)
    
    assert len(control_contexts) == 2
    
    # Valida primeira PDU (PRB_QUOTA)
    ctx1 = control_contexts[0]
    assert ctx1.node_id == "gnb_01"
    assert ctx1.ran_function_id == 3
    assert len(ctx1.pdu_aper) > 0
    
    # Desserializa a E2AP-PDU completa e o RICcontrolRequest interno
    from src.e2.e2ap.pdu import unwrap_e2ap_pdu
    from src.e2.e2ap.constants import PROC_RIC_CONTROL
    
    pdu_type, proc_code, crit, inner_bytes = unwrap_e2ap_pdu(ctx1.pdu_aper)
    assert pdu_type == "initiatingMessage"
    assert proc_code == PROC_RIC_CONTROL
    
    pdu = RICcontrolRequest()
    pdu.from_aper(inner_bytes)
    val = pdu()
    assert val['ranFunctionID'] == 3
    assert len(val['ricControlHeader']) > 0
    assert len(val['ricControlMessage']) > 0
