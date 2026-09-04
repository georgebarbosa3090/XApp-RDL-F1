import pytest
from src.agents.refinement_agent import RefinementAgent
from src.conflict_types import ResolutionAction, ResolutionStrategy, ConflictEvent, XAppAction
import uuid

def test_safety_guard_out_of_bounds(mock_memory, action_tx_power, direct_conflict):
    agent = RefinementAgent(memory=mock_memory)
    
    # Injetando um valor absurdo para forcar o Safety Guard
    action_tx_power.value = 50.0  # Limite e 23 dBm
    
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

def test_safety_guard_single_action_pass_through(mock_memory):
    agent = RefinementAgent(memory=mock_memory)
    clean_action = XAppAction(xapp_id="xslice_oran", node_id="gnb_01", parameter="PRB_QUOTA", value=80.0, priority=90)
    
    is_safe, level, reason = agent.validate_single_action(clean_action)
    assert is_safe is True
    assert "passed" in reason.lower()

def test_safety_guard_single_action_invalid_bounds(mock_memory):
    agent = RefinementAgent(memory=mock_memory)
    invalid_action = XAppAction(xapp_id="energy_saving", node_id="gnb_01", parameter="TX_POWER", value=45.0, priority=65)
    
    is_safe, level, reason = agent.validate_single_action(invalid_action)
    assert is_safe is False
    assert "out of bounds" in reason.lower()
