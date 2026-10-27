import pytest
from src.e2.rc.control_parameter import RAN_PARAMETERS
from src.e2.rc.capability_registry import rc_capability_registry, ControlActionCapability
from src.e2.rc_encoder import PARAM_PROFILES
from src.core.refinement import Refinement
from src.conflict_types import XAppAction
from src.infrastructure.memory_module import MemoryModule

def test_tx_power_bounds_canonical_alignment():
    assert RAN_PARAMETERS["TX_POWER"].max_value == 43.0
    assert PARAM_PROFILES["TX_POWER"]["max"] == 430
    cap = rc_capability_registry.get_action_capability("TX_POWER", "gnb_01", strict_mode=False)
    assert cap.max_value == 43.0

def test_safety_accepts_valid_macro_tx_power():
    memory = MemoryModule()
    refinement = Refinement(memory=memory, strict_capabilities=False)
    
    # 40 dBm (antes era rejeitado com teto de 23 dBm)
    action_40 = XAppAction(xapp_id="power_xapp", node_id="gnb_01", parameter="TX_POWER", value=40.0, priority=1)
    is_safe, level, reason = refinement.validate_single_action(action_40)
    assert is_safe is True
    assert reason == "Passed safety checks"

    # 43 dBm (limite máximo permitido para macro gNB)
    action_43 = XAppAction(xapp_id="power_xapp", node_id="gnb_01", parameter="TX_POWER", value=43.0, priority=1)
    is_safe, level, reason = refinement.validate_single_action(action_43)
    assert is_safe is True

def test_safety_rejects_out_of_bounds_tx_power():
    memory = MemoryModule()
    refinement = Refinement(memory=memory, strict_capabilities=False)

    # 50 dBm (acima de 43 dBm)
    action_50 = XAppAction(xapp_id="power_xapp", node_id="gnb_01", parameter="TX_POWER", value=50.0, priority=1)
    is_safe, level, reason = refinement.validate_single_action(action_50)
    assert is_safe is False
    assert "TX Power out of bounds" in reason

    # -15 dBm (abaixo de -10 dBm)
    action_neg = XAppAction(xapp_id="power_xapp", node_id="gnb_01", parameter="TX_POWER", value=-15.0, priority=1)
    is_safe, level, reason = refinement.validate_single_action(action_neg)
    assert is_safe is False
    assert "TX Power out of bounds" in reason

def test_strict_mode_default_deny_when_undiscovered():
    memory = MemoryModule()
    refinement = Refinement(memory=memory, strict_capabilities=True)

    action = XAppAction(xapp_id="power_xapp", node_id="unknown_gnb", parameter="TX_POWER", value=40.0, priority=1)
    is_safe, level, reason = refinement.validate_single_action(action)
    assert is_safe is False
    assert "capability not discovered" in reason
