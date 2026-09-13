"""
Testes de Integração E2 Local (Local Protocol Layer / Codec & Mapper Integration)
Valida a integração em malha fechada local dos módulos H-RDL:
KPMReport -> PerceptionAgent -> ReasoningAgent -> RefinementAgent -> RCMapper -> RICcontrolAcknowledge
"""

import pytest
from src.conflict_types import XAppAction, KPMReport, RDLDecision
from src.agents.perception_agent import PerceptionAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.refinement_agent import RefinementAgent
from src.infrastructure.memory_module import MemoryModule
from src.e2.rc.mapper import RCMapper
from src.e2.e2ap.control import parse_ric_control_ack, RICcontrolAcknowledge
from src.e2.e2ap.pdu import wrap_successful_outcome
from src.e2.e2ap.constants import PROC_RIC_CONTROL

def test_closed_loop_telemetry_to_control_and_ack_pipeline():
    """
    Executa a malha fechada local de governança e controle E2.
    """
    t0_telemetry = KPMReport(
        node_id="gnb_001",
        ue_id="ue_01",
        drb_thp_dl=45.0,
        drb_thp_ul=10.0,
        drb_delay_dl=8.5,
        prb_used_dl=92
    )
    
    act_xslice = XAppAction(
        xapp_id="xslice",
        node_id="gnb_001",
        parameter="PRB_QUOTA",
        value=80.0,
        priority=90
    )
    act_energy = XAppAction(
        xapp_id="energy_saving",
        node_id="gnb_001",
        parameter="PRB_QUOTA",
        value=30.0,
        priority=70
    )

    perception = PerceptionAgent()
    perception.update_kpm_report(t0_telemetry)
    conflicts = perception.register_action_group([act_xslice, act_energy])
    assert len(conflicts) > 0

    memory = MemoryModule()
    reasoning = ReasoningAgent(memory)
    resolution = reasoning.resolve(conflicts[0])
    assert len(resolution.winning_actions) > 0

    refinement = RefinementAgent(memory)
    refinement.config["minimum_control_interval_ms"] = 0
    is_valid, level, reason = refinement.validate_single_action(resolution.winning_actions[0])
    assert is_valid is True
    safe_action = resolution.winning_actions[0]

    decision = RDLDecision(
        selected_actions=[safe_action],
        conflicts=conflicts,
        strategy_used=resolution.strategy_used.name
    )

    rc_mapper = RCMapper(ran_function_id=3)
    ctrl_requests = rc_mapper.map_decision_to_control_requests(decision, requestor_id=1, instance_id=100)
    assert len(ctrl_requests) > 0
    assert len(ctrl_requests[0].pdu_aper) > 0

    ack_ie = RICcontrolAcknowledge()
    ack_ie.set_val({
        'ricRequestID': {'ricRequestorID': ctrl_requests[0].requestor_id, 'ricInstanceID': ctrl_requests[0].instance_id},
        'ranFunctionID': ctrl_requests[0].ran_function_id
    })
    mock_ack_raw = wrap_successful_outcome(PROC_RIC_CONTROL, ack_ie.to_aper())
    ack_parsed = parse_ric_control_ack(mock_ack_raw)
    assert ack_parsed["status"] == "ACKNOWLEDGED"
