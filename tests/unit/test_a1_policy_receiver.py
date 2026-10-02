"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Módulo: Testes Unitários do Receptor de Políticas A1-P (O-RAN WG2)
Arquivo: tests/unit/test_a1_policy_receiver.py
========================================================================================
"""

import pytest
from src.interfaces.a1_policy_receiver import A1PolicyManager


def test_a1_policy_manager_crud():
    manager = A1PolicyManager()

    # 1. Validação de tipos suportados
    assert "20000" in manager.policy_types

    # 2. Inserção de política válida
    valid_policy = {
        "urllc_priority_boost": 15.0,
        "energy_saving_allowed": True,
        "max_cell_prb_limit": 85.0,
        "cooling_lockout_ms": 1000.0
    }
    ok, msg = manager.put_policy("20000", "policy_s01", valid_policy)
    assert ok is True
    assert "successfully" in msg

    # 3. Consulta de política existente
    retrieved = manager.get_policy("20000", "policy_s01")
    assert retrieved is not None
    assert retrieved["max_cell_prb_limit"] == 85.0

    # 4. Inserção de política com parâmetro fora dos limites
    invalid_policy = {
        "max_cell_prb_limit": 150.0  # Inválido (> 100)
    }
    ok_inv, msg_inv = manager.put_policy("20000", "policy_s02", invalid_policy)
    assert ok_inv is False
    assert "out of bounds" in msg_inv

    # 5. Remoção de política
    assert manager.delete_policy("20000", "policy_s01") is True
    assert manager.get_policy("20000", "policy_s01") is None
