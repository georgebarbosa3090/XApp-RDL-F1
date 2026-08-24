import pytest
from src.agents.refinement_agent import RefinementAgent
from src.conflict_types import ResolutionAction, ResolutionStrategy, ConflictEvent
import uuid

def test_safety_guard_out_of_bounds(mock_memory, action_tx_power, direct_conflict):
    agent = RefinementAgent(memory=mock_memory)
    
    # Injetando um valor absurdo para forçar o Safety Guard
    action_tx_power.value = 50.0  # Limite é 23 dBm
    
    resolution = ResolutionAction(
        conflict_id=direct_conflict.conflict_id,
        strategy_used=ResolutionStrategy.TVS,
        winning_actions=[action_tx_power],
        modified_value=50.0,
        confidence=1.0,
        validation_level=0
    )
    
    is_valid, level, reason = agent.validate(resolution, direct_conflict)
    assert is_valid is False
    assert "out of bounds" in reason.lower()

def test_safety_guard_frequency_limit(mock_memory, action_prb_quota, direct_conflict):
    agent = RefinementAgent(memory=mock_memory)
    
    resolution = ResolutionAction(
        conflict_id=direct_conflict.conflict_id,
        strategy_used=ResolutionStrategy.TVS,
        winning_actions=[action_prb_quota],
        modified_value=50.0,
        confidence=1.0,
        validation_level=0
    )
    
    # Primeira chamada deve passar
    is_valid, level, reason = agent.validate(resolution, direct_conflict)
    assert is_valid is True
    
    # Segunda chamada imediata (mesmo alvo) deve falhar pelo limite de 1000ms
    is_valid_2, level_2, reason_2 = agent.validate(resolution, direct_conflict)
    assert is_valid_2 is False
    assert "frequency exceeded" in reason_2.lower()
