import time

import pytest
from src.core.refinement import Refinement
from src.infrastructure.memory_module import MemoryModule
from src.conflict_types import XAppAction

def test_safety_guard_power_bounds():
    memory = MemoryModule()
    refinement = Refinement(memory)
    
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
    refinement = Refinement(memory)
    
    # Ação violando cota de PRB (> 100%)
    invalid_prb = XAppAction("xslice", "gnb_01", "PRB_QUOTA", 120.0, 90)
    is_safe, _, reason = refinement.validate_single_action(invalid_prb)
    assert is_safe is False


def test_safety_guard_default_deny():
    memory = MemoryModule()
    refinement = Refinement(memory)

    # Parâmetro desconhecido/não suportado deve ser rejeitado imediatamente (Default-Deny)
    malicious_act = XAppAction("malicious_xapp", "gnb_01", "UNSUPPORTED_PARAMETER", 42.0, 99)
    is_safe, level, reason = refinement.validate_single_action(malicious_act)
    assert is_safe is False
    assert "default-deny" in reason.lower() or "unsupported" in reason.lower()


def test_safety_guard_transactional_atomic_rollback():
    from src.conflict_types import ConflictEvent, ConflictType, ConflictSeverity, ResolutionAction, ResolutionStrategy
    memory = MemoryModule()
    refinement = Refinement(memory)

    # Batch onde a primeira ação é válida e a segunda viola os limites
    act1 = XAppAction("qos_xapp", "gnb_01", "PRB_QUOTA", 50.0, 80)
    act2 = XAppAction("bad_xapp", "gnb_02", "UNSUPPORTED_PARAM", 10.0, 10)

    conflict = ConflictEvent(conflict_type=ConflictType.DIRECT, severity=ConflictSeverity.HIGH, involved_xapps=[act1, act2])
    resolution = ResolutionAction(
        conflict_id="c_01",
        strategy_used=ResolutionStrategy.PRIORITY_TABLE,
        winning_actions=[act1, act2],
        modified_value=None,
        confidence=1.0,
        validation_level=1
    )

    is_safe, level, reason = refinement.validate(resolution, conflict)
    assert is_safe is False

    # Validação atômica: gnb_01_PRB_QUOTA NÃO pode ter seu timestamp gravado se o lote falhou
    assert "gnb_01_PRB_QUOTA" not in refinement.last_control_time


def test_safety_guard_dynamic_power_ceiling():
    memory = MemoryModule()
    refinement = Refinement(memory)
    # Define limite específico para pico-célula gnb_pico
    refinement.node_capabilities = {"gnb_pico": {"max_tx_power_dbm": 15.0}}

    # 18 dBm é válido para macro (< 23 dBm), mas deve ser rejeitado para gnb_pico (max 15 dBm)
    pico_act = XAppAction("es_xapp", "gnb_pico", "TX_POWER", 18.0, 50)
    is_safe, level, reason = refinement.validate_single_action(pico_act)
    assert is_safe is False
    assert "out of bounds" in reason.lower()


def test_strict_safety_guard_rejects_undiscovered_tx_power_capability():
    from src.e2.rc.capability_registry import rc_capability_registry

    node_id = "strict_safety_unknown_tx_power"
    rc_capability_registry.register_node_capability(
        node_id=node_id,
        param_name="PRB_QUOTA",
        style_type=1,
        action_id=1,
        param_id=1,
        min_val=0,
        max_val=100,
        strict_mode=False,
    )
    refinement = Refinement(MemoryModule(), strict_capabilities=True)
    action = XAppAction("energy_saving", node_id, "TX_POWER", 15.0, 50)

    is_safe, _, reason = refinement.validate_single_action(action)

    assert is_safe is False
    assert "capability not discovered" in reason.lower()


def test_strict_safety_guard_uses_discovered_tx_power_limit():
    from src.e2.rc.capability_registry import rc_capability_registry

    node_id = "strict_safety_discovered_tx_power"
    rc_capability_registry.register_node_capability(
        node_id=node_id,
        param_name="TX_POWER",
        style_type=2,
        action_id=1,
        param_id=3,
        min_val=-10,
        max_val=18,
        unit="dBm",
        strict_mode=True,
    )
    refinement = Refinement(MemoryModule(), strict_capabilities=True)
    action = XAppAction("energy_saving", node_id, "TX_POWER", 18.0, 50)

    is_safe, _, reason = refinement.validate_single_action(action)

    assert is_safe is True
    assert reason == "Passed safety checks"


def test_resolution_rejects_action_inside_control_cooldown():
    from src.conflict_types import (
        ConflictEvent,
        ConflictSeverity,
        ConflictType,
        ResolutionAction,
        ResolutionStrategy,
    )

    action = XAppAction("xslice", "gnb_cooldown", "PRB_QUOTA", 80.0, 90)
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[action],
    )
    resolution = ResolutionAction(
        conflict_id=conflict.conflict_id,
        strategy_used=ResolutionStrategy.TVS,
        winning_actions=[action],
        modified_value=action.value,
        confidence=1.0,
        validation_level=0,
    )
    refinement = Refinement(MemoryModule())
    refinement.last_control_time["gnb_cooldown_PRB_QUOTA"] = time.time() * 1000

    is_safe, _, reason = refinement.validate(resolution, conflict)

    assert is_safe is False
    assert "control frequency exceeded" in reason.lower()
