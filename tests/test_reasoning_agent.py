import pytest
from src.agents.reasoning_agent import ReasoningAgent
from src.conflict_types import ResolutionStrategy

def test_resolve_by_tvs_priority(mock_memory, direct_conflict):
    agent = ReasoningAgent(memory=mock_memory, config={})
    
    # Resolve the direct conflict using TVS combinatorics
    resolution = agent.resolve(direct_conflict)
    
    # Verify that a resolution action is generated
    assert resolution is not None
    assert resolution.conflict_id == direct_conflict.conflict_id
    assert resolution.strategy_used in [ResolutionStrategy.TVS, ResolutionStrategy.EEVS]
    
    # TVS should penalize the contradictory actions (same parameter, different values) 
    # and pick the one with better utility. Our mock assigns arbitrary score.
    # We just ensure it selected exactly one action for this strict direct conflict.
    assert len(resolution.winning_actions) == 1
    assert resolution.modified_value in [15.0, 20.0]

def test_indirect_heuristic(mock_memory, action_tx_power, action_prb_quota):
    # If conflict is INDIRECT, it goes to the heuristic (Phase 1)
    agent = ReasoningAgent(memory=mock_memory, config={})
    
    from src.conflict_types import ConflictEvent, ConflictType, ConflictSeverity
    import uuid
    
    indirect_conflict = ConflictEvent(
        conflict_id=str(uuid.uuid4()),
        conflict_type=ConflictType.INDIRECT,
        severity=ConflictSeverity.MEDIUM,
        involved_xapps=[action_tx_power, action_prb_quota],
        affected_kpis=["DRB.UEThpDl"],
        detected_at=0.0,
        description="Conflito indireto simulado"
    )
    
    resolution = agent.resolve(indirect_conflict)
    
    assert resolution.strategy_used == ResolutionStrategy.EEVS
    assert len(resolution.winning_actions) > 0
