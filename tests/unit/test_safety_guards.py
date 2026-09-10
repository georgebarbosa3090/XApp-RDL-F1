import pytest
from src.agents.refinement_agent import RefinementAgent
from src.infrastructure.memory_module import MemoryModule
from src.conflict_types import XAppAction

def test_safety_guard_power_bounds():
    memory = MemoryModule()
    refinement = RefinementAgent(memory)
    
    # Ação dentro dos limites (-10 a 23 dBm)
    valid_act = XAppAction("energy_saving", "gnb_01", "TX_POWER", 20.0, 50)
    is_safe, level, reason = refinement.validate_single_action(valid_act)
    assert is_safe is True
    
    # Ação violando limite máximo (> 23 dBm) em outro nó
    invalid_act = XAppAction("energy_saving", "gnb_02", "TX_POWER", 35.0, 50)
    is_safe_inv, level_inv, reason_inv = refinement.validate_single_action(invalid_act)
    assert is_safe_inv is False
    assert "out of bounds" in reason_inv.lower()



def test_safety_guard_prb_bounds():
    memory = MemoryModule()
    refinement = RefinementAgent(memory)
    
    # Ação violando cota de PRB (> 100%)
    invalid_prb = XAppAction("xslice", "gnb_01", "PRB_QUOTA", 120.0, 90)
    is_safe, _, reason = refinement.validate_single_action(invalid_prb)
    assert is_safe is False
