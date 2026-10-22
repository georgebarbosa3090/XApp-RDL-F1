import pytest
from src.core.reasoning import Reasoning
from src.infrastructure.memory_module import MemoryModule
from src.conflict_types import ConflictEvent, ConflictType, ConflictSeverity, XAppAction, ResolutionStrategy

def test_reasoning_shannon_and_tvs_resolution():
    memory = MemoryModule()
    reasoning = Reasoning(memory)
    
    act_urllc = XAppAction(xapp_id="xslice", node_id="gnb_01", parameter="PRB_QUOTA", value=80.0, priority=90)
    act_embb = XAppAction(xapp_id="traffic_steering", node_id="gnb_01", parameter="PRB_QUOTA", value=40.0, priority=50)
    
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[act_urllc, act_embb],
        affected_kpis=["PRB_QUOTA"],
        description="Disputa direta de cotas de PRB entre fatias"
    )
    
    resolution = reasoning.resolve(conflict)
    assert resolution.strategy_used in (ResolutionStrategy.TVS, ResolutionStrategy.PRIORITY_TABLE)
    assert len(resolution.winning_actions) > 0
    assert resolution.winning_actions[0].xapp_id == "xslice"


def test_large_indirect_conflict_uses_deterministic_bounded_strategy():
    reasoning = Reasoning(MemoryModule(), config={"max_exact_actions": 4})
    actions = [
        XAppAction(f"xapp_{index}", "gnb_01", f"PARAM_{index}", float(index), 50)
        for index in range(12)
    ]
    conflict = ConflictEvent(
        conflict_type=ConflictType.INDIRECT,
        severity=ConflictSeverity.MEDIUM,
        involved_xapps=actions,
        affected_kpis=["DRB.UEThpDl"],
        description="Large indirect conflict",
    )

    resolution = reasoning.resolve(conflict)

    assert resolution.strategy_used == ResolutionStrategy.EEVS
    assert resolution.winning_actions
    assert resolution.confidence == 0.70
    assert resolution.winning_actions == reasoning.resolve(conflict).winning_actions
