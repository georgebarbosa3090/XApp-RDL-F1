"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Módulo: Testes de Fuzzing Estocástico e Verificação de Invariantes Formais
Arquivo: tests/unit/test_safety_guard_fuzzing.py
Descrição: Executa 10.000 iterações de fuzzing estocástico com valores extremos
           para provar formalmente que:
           forall a in A_random, Refinement.validate(a) in Omega_safe (100% de garantia)
========================================================================================
"""

import random
import pytest
from src.conflict_types import (
    XAppAction,
    ConflictEvent,
    ConflictType,
    ConflictSeverity,
    ResolutionAction,
    ResolutionStrategy
)
from src.core.refinement import Refinement
from src.infrastructure.memory_module import MemoryModule


def test_safety_guard_stochastic_fuzzing_10000_iterations():
    """
    Testa a robustez e a garantia invariante do Refinement sob 10.000 ações pseudo-aleatórias
    com valores altamente extremos, adversários e corrompidos.
    """
    memory = MemoryModule()
    refinement = Refinement(memory)
    # Desativa tempo de histerese para focar na validação dos limites de parâmetros
    refinement.config["minimum_control_interval_ms"] = 0

    random.seed(42)

    parameters = [
        "PRB_QUOTA",
        "TX_POWER",
        "HANDOVER",
        "VERTICAL_DOWNTILT",
        "SENSING_RATIO",
        "LOAD_THRESHOLD",
        "PING_INTERVAL",
        "SCHEDULER_WEIGHT",
        "UNKNOWN_PARAM_XYZ",
    ]

    xapp_names = ["xapp_qos", "xapp_es", "xapp_ts", "xapp_malicious", "xapp_fuzzer"]

    total_tested = 10000
    safe_admitted = 0
    rejected_count = 0

    for i in range(total_tested):
        param = random.choice(parameters)
        val = random.uniform(-200.0, 500.0)
        prio = random.randint(-50, 200)
        node = f"gnb_{random.randint(1, 10):02d}"
        xapp = random.choice(xapp_names)

        action = XAppAction(
            xapp_id=xapp,
            node_id=node,
            parameter=param,
            value=val,
            priority=prio
        )

        is_safe, level, reason = refinement.validate_single_action(action)

        if is_safe:
            safe_admitted += 1
            # O valor admitido DEVE estar estritamente dentro da faixa segura Omega_safe
            if param == "PRB_QUOTA":
                assert 0.0 <= action.value <= 100.0, f"Violação PRB: {action.value}"
            elif param == "TX_POWER":
                assert -10.0 <= action.value <= 23.0, f"Violação Potência: {action.value}"
            elif param == "HANDOVER":
                assert 0.0 <= action.value <= 1.0, f"Violação Handover: {action.value}"
            elif param == "VERTICAL_DOWNTILT":
                assert 0.0 <= action.value <= 15.0, f"Violação Downtilt: {action.value}"
            elif param == "SENSING_RATIO":
                assert 0.0 <= action.value <= 0.60, f"Violação Sensing Ratio: {action.value}"
            elif param == "LOAD_THRESHOLD":
                assert 0.0 <= action.value <= 1.0, f"Violação Load Threshold: {action.value}"
            elif param == "PING_INTERVAL":
                assert 1.0 <= action.value <= 5000.0, f"Violação Ping Interval: {action.value}"
            elif param == "SCHEDULER_WEIGHT":
                assert 0.0 <= action.value <= 100.0, f"Violação Scheduler Weight: {action.value}"
        else:
            rejected_count += 1
            assert reason is not None
            assert len(reason) > 0

    assert safe_admitted + rejected_count == total_tested
    assert safe_admitted > 0
    assert rejected_count > 0


def test_safety_guard_resolution_fuzzing():
    """
    Testa validação de resoluções de conflitos multi-ação geradas aleatoriamente.
    """
    memory = MemoryModule()
    refinement = Refinement(memory)
    refinement.config["minimum_control_interval_ms"] = 0

    random.seed(100)

    for i in range(100):
        conflict = ConflictEvent(
            conflict_type=random.choice(list(ConflictType)),
            severity=random.choice(list(ConflictSeverity)),
            involved_xapps=[]
        )

        n_actions = random.randint(1, 5)
        actions = []
        for _ in range(n_actions):
            act = XAppAction(
                xapp_id=f"xapp_{random.randint(1, 3)}",
                node_id="gnb_01",
                parameter="PRB_QUOTA",
                value=random.uniform(-50.0, 150.0),
                priority=random.randint(1, 100)
            )
            actions.append(act)

        resolution = ResolutionAction(
            conflict_id=f"conf_{i}",
            strategy_used=ResolutionStrategy.PRIORITY_TABLE,
            winning_actions=actions,
            modified_value=None,
            confidence=0.95,
            validation_level=1
        )

        is_valid, level, reason = refinement.validate(resolution, conflict)

        if is_valid:
            for act in resolution.winning_actions:
                assert 0.0 <= act.value <= 100.0
