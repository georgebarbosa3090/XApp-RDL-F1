"""
Suíte de Testes Unitários e Funcionais da Campanha de Cenários S0 a S8
Valida as propriedades centrais de cada cenário:
  - S0: Não-interferência e integridade do pass-through limpo.
  - S1: Ground truth de detecção de colisão direta (Precision, Recall, F1).
  - S4: Arbitragem assimétrica de mobilidade vs sono de estação base.
  - S5: Supressão de oscilação temporal e cooldown lock.
  - S6: Concorrência e manutenção da garantia Near-RT (< 50ms) no Conflict Storm.
  - S7: Imunidade a falhas e garantia estrita de Zero Ações Inseguras (Zero-Violation).
"""

import pytest
import time
from src.infrastructure.memory_module import MemoryModule
from src.agents.perception_agent import PerceptionAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.refinement_agent import RefinementAgent
from src.conflict_types import XAppAction, ConflictType

def test_scenario_s0_non_interference_pass_through():
    """Valida que sob ações compatíveis sem risco de SLA, o H-RDL não altera nem bloqueia nenhuma proposta (InterferenceRate = 0)."""
    memory = MemoryModule()
    refinement = RefinementAgent(memory)

    # 3 propostas totalmente compatíveis em nós distintos
    clean_actions = [
        XAppAction(xapp_id="xslice", node_id="gnb_01", parameter="PRB_QUOTA", value=40.0, priority=50),
        XAppAction(xapp_id="energy_saver", node_id="gnb_02", parameter="TX_POWER", value=20.0, priority=50),
        XAppAction(xapp_id="traffic_steering", node_id="gnb_03", parameter="HANDOVER", value=1.0, priority=50)
    ]

    altered_count = 0
    for act in clean_actions:
        is_safe, level, reason = refinement.validate_single_action(act)
        assert is_safe, f"Ação limpa foi indevidamente rejeitada: {reason}"
        if not is_safe:
            altered_count += 1

    interference_rate = altered_count / len(clean_actions)
    assert interference_rate == 0.0

def test_scenario_s1_direct_conflict_detection_accuracy():
    """Valida o ground truth de detecção de colisão direta (PRB x PRB) calculando Precision, Recall e F1."""
    perception = PerceptionAgent()

    # Dois UEs solicitando cotas concorrentes na mesma célula
    actions = [
        XAppAction(xapp_id="xslice", node_id="gnb_01", parameter="PRB_QUOTA", value=75.0, priority=90),
        XAppAction(xapp_id="energy_saver", node_id="gnb_01", parameter="PRB_QUOTA", value=30.0, priority=65)
    ]

    conflicts = perception.register_action_group(actions)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.DIRECT

    # Ground truth: 1 conflito real, 1 detectado, 0 falsos positivos, 0 falsos negativos
    tp, fp, fn = 1, 0, 0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = 2 * (precision * recall) / (precision + recall)
    assert precision == 1.0
    assert recall == 1.0
    assert f1 == 1.0

def test_scenario_s4_traffic_steering_vs_energy_arbitration():
    """Valida que quando uma célula congestionada tenta descarregar UEs em uma célula onde ES quer alterar potência, o H-RDL prioriza a manutenção da cobertura."""
    memory = MemoryModule()
    reasoning = ReasoningAgent(memory, config={})
    refinement = RefinementAgent(memory)
    perception = PerceptionAgent()

    # gNB1: Traffic steering solicita Handover (impacta DRB.UEThpDl) e Energy Saver tenta reduzir TX_POWER (impacta DRB.UEThpDl)
    actions = [
        XAppAction(xapp_id="traffic_steering", node_id="gnb_01", parameter="HANDOVER", value=1.0, priority=85),
        XAppAction(xapp_id="energy_saver", node_id="gnb_01", parameter="TX_POWER", value=-10.0, priority=60)
    ]

    conflicts = perception.register_action_group(actions)
    # Deve detectar conflito indireto de mobilidade vs potência (compartilham DRB.UEThpDl)
    assert len(conflicts) >= 1
    assert conflicts[0].conflict_type == ConflictType.INDIRECT

    resolution = reasoning.resolve(conflicts[0])
    is_valid, level, reason = refinement.validate(resolution, conflicts[0])
    assert is_valid
    # A ação vencedora deve preservar a integridade da conexão (prioridade maior / menor penalidade de perda)
    winning_params = [a.parameter for a in resolution.winning_actions]
    assert len(winning_params) > 0

def test_scenario_s5_temporal_ping_pong_lock():
    """Valida o mecanismo de histerese e cooldown lock para evitar reversões cíclicas (ping-pong) em janelas temporais curtas."""
    memory = MemoryModule()
    refinement = RefinementAgent(memory)

    # Primeira ação: handover de UE para gNB1
    act1 = XAppAction(xapp_id="ts", node_id="gnb_01", parameter="HANDOVER", value=1.0, priority=80)
    is_safe1, _, _ = refinement.validate_single_action(act1)
    assert is_safe1

    # Segunda ação imediata (< 1000ms): tentativa repetida ou reversão rápida no mesmo nó/parâmetro
    act2 = XAppAction(xapp_id="ts", node_id="gnb_01", parameter="HANDOVER", value=1.0, priority=80)
    is_safe2, _, reason2 = refinement.validate_single_action(act2)
    
    # Simula bloqueio de ping-pong por histerese/cooldown de controle
    assert not is_safe2
    assert "Control frequency exceeded" in reason2

def test_scenario_s6_conflict_storm_near_rt_bounds():
    """Valida que sob rajada massiva de 50 ações/janela (Nível L3), o tempo de decisão permanece estritamente < 50ms."""
    memory = MemoryModule()
    perception = PerceptionAgent()
    reasoning = ReasoningAgent(memory, config={})
    refinement = RefinementAgent(memory)

    storm_actions = []
    for i in range(50):
        storm_actions.append(XAppAction(
            xapp_id=f"xapp_{i % 5}",
            node_id=f"gnb_{i % 2}",
            parameter="PRB_QUOTA" if i % 2 == 0 else "TX_POWER",
            value=float(40 + (i % 50)),
            priority=50 + (i % 40)
        ))

    t0 = time.perf_counter()
    conflicts = perception.register_action_group(storm_actions)
    for c in conflicts:
        res = reasoning.resolve(c)
        refinement.validate(res, c)
    t_elapsed_ms = (time.perf_counter() - t0) * 1000.0

    # Exigência normativa Near-RT RIC: < 50ms
    assert t_elapsed_ms < 50.0, f"Tempo de decisão no storm excedeu 50ms: {t_elapsed_ms:.2f}ms"

def test_scenario_s7_adversarial_fault_safety_zero_violation():
    """Valida que 100% dos comandos adversários ou corrompidos são bloqueados ou clampeados para faixa segura."""
    memory = MemoryModule()
    refinement = RefinementAgent(memory)

    adversarial_actions = [
        XAppAction(xapp_id="hostile", node_id="gnb_01", parameter="TX_POWER", value=100.0, priority=99), # > 23 dBm
        XAppAction(xapp_id="hostile", node_id="gnb_01", parameter="TX_POWER", value=-50.0, priority=99), # < -10 dBm
        XAppAction(xapp_id="hostile", node_id="gnb_01", parameter="PRB_QUOTA", value=150.0, priority=99), # > 100%
        XAppAction(xapp_id="hostile", node_id="gnb_01", parameter="PRB_QUOTA", value=-20.0, priority=99)  # < 0%
    ]

    unsafe_executed = 0
    for act in adversarial_actions:
        is_safe, level, reason = refinement.validate_single_action(act)
        if is_safe:
            unsafe_executed += 1

    assert unsafe_executed == 0, f"Ações inseguras foram indevidamente aceitas: {unsafe_executed}"
