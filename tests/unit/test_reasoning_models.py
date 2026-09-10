import pytest
from src.agents.reasoning_agent import ReasoningAgent
from src.infrastructure.memory_module import MemoryModule
from src.conflict_types import ConflictEvent, ConflictType, ConflictSeverity, XAppAction, ResolutionStrategy

def test_reasoning_shannon_and_tvs_resolution():
    memory = MemoryModule()
    agent = ReasoningAgent(memory)
    
    act_urllc = XAppAction(xapp_id="xslice", node_id="gnb_01", parameter="PRB_QUOTA", value=80.0, priority=90)
    act_embb = XAppAction(xapp_id="traffic_steering", node_id="gnb_01", parameter="PRB_QUOTA", value=40.0, priority=50)
    
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[act_urllc, act_embb],
        affected_kpis=["PRB_QUOTA"],
        description="Disputa direta de cotas de PRB entre fatias"
    )
    
    resolution = agent.resolve(conflict)
    assert resolution.strategy_used in (ResolutionStrategy.TVS, ResolutionStrategy.PRIORITY_TABLE)
    assert len(resolution.winning_actions) > 0
    assert resolution.winning_actions[0].xapp_id == "xslice"
