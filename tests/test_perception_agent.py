import pytest
from src.agents.perception_agent import PerceptionAgent
from src.conflict_types import XAppAction, ConflictType

def test_detect_direct_conflict(action_tx_power):
    agent = PerceptionAgent()
    
    action2 = XAppAction(
        xapp_id="xapp_2",
        node_id="gnb_01",
        parameter="TX_POWER",
        value=15.0,
        priority=80
    )
    
    # Processando em lote (Janela de 200ms)
    conflicts = agent.register_action_group([action_tx_power, action2])
    
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.DIRECT
    assert "TX_POWER" in conflicts[0].description
    assert len(conflicts[0].involved_xapps) == 2

def test_detect_indirect_conflict(action_tx_power, action_prb_quota):
    agent = PerceptionAgent()
    
    # Ambas afetam Throughput e Delay
    conflicts = agent.register_action_group([action_tx_power, action_prb_quota])
    
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.INDIRECT
    assert len(conflicts[0].involved_xapps) == 2
    
def test_no_conflict():
    agent = PerceptionAgent()
    
    # Ações em nós diferentes não devem causar conflito
    action1 = XAppAction("xapp_1", "gnb_01", "TX_POWER", 20.0, 50)
    action2 = XAppAction("xapp_2", "gnb_02", "TX_POWER", 20.0, 50)
    
    conflicts = agent.register_action_group([action1, action2])
    assert len(conflicts) == 0
