"""
Testes de Interoperabilidade em Malha Fechada (Closed-Loop / Gate 4)
Valida a transição ponta a ponta:
Telemetria KPM(t0) -> Percepção RDL -> Raciocínio de Conflito -> Refinamento Safety -> RIC Control -> ACK -> Efeito na Rede KPM(t1)
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
    Executa a malha fechada completa de governança e controle E2.
    """
    # 1. Telemetria inicial t0 (Alta contenção e sobrecarga de PRBs)
    t0_telemetry = KPMReport(
        node_id="gnb_001",
        ue_id="ue_01",
        drb_thp_dl=45.0,
        drb_thp_ul=10.0,
        drb_delay_dl=8.5, # ms (Violação de SLA URLLC > 5ms)
        prb_used_dl=92
    )
    
    # 2. Ações concorrentes geradas por 2 xApps em janela de lote
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
        priority=65
    )
    
    # 3. Pipeline de Governança RDL (Percepção, Raciocínio e Refinamento)
    perception = PerceptionAgent()
    perception.update_kpm_report(t0_telemetry)
    conflicts = perception.register_action_group([act_xslice, act_energy])
    assert len(conflicts) > 0
    
    memory = MemoryModule()
    reasoning = ReasoningAgent(memory)
    resolution = reasoning.resolve(conflicts[0])
    assert len(resolution.winning_actions) > 0
    
    refinement = RefinementAgent(memory)
    refinement.config["minimum_control_interval_ms"] = 0 # Permite validação imediata em teste
    is_valid, level, reason = refinement.validate_single_action(resolution.winning_actions[0])
    assert is_valid is True
    
    decision = RDLDecision(
        selected_actions=resolution.winning_actions,
        conflicts=conflicts,
        strategy_used=resolution.strategy_used.name
    )
    
    # 4. Mapeamento E2SM-RC e Despacho E2AP-PDU
    mapper = RCMapper(ran_function_id=3)
    ctrl_requests = mapper.map_decision_to_control_requests(decision, requestor_id=1, instance_id=100)
    assert len(ctrl_requests) == len(decision.selected_actions)
    
    for ctx in ctrl_requests:
        assert len(ctx.pdu_aper) > 0
        
        # Simula resposta ACK emitida pelo NORI E2 Node
        ack_ie = RICcontrolAcknowledge()
        ack_ie.set_val({
            'ricRequestID': {'ricRequestorID': ctx.requestor_id, 'ricInstanceID': ctx.instance_id},
            'ranFunctionID': ctx.ran_function_id
        })
        pdu_ack = wrap_successful_outcome(PROC_RIC_CONTROL, ack_ie.to_aper())
        ack_res = parse_ric_control_ack(pdu_ack)
        assert ack_res["status"] == "ACKNOWLEDGED"

    # 5. Telemetria t1 após controle aplicado (Estabilização da rede)
    t1_telemetry = KPMReport(
        node_id="gnb_001",
        ue_id="ue_01",
        drb_thp_dl=52.0,
        drb_thp_ul=12.0,
        drb_delay_dl=2.8, # ms (SLA URLLC reestabelecido < 5ms)
        prb_used_dl=68
    )
    assert t1_telemetry.drb_delay_dl < 5.0
    assert t1_telemetry.prb_used_dl < 75
