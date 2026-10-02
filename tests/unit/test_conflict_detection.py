import pytest
from src.core.perception import Perception
from src.conflict_types import XAppAction, ConflictType

def test_detect_direct_conflict():
    perception = Perception()
    actions = [
        XAppAction("xslice", "gnb_01", "PRB_QUOTA", 80, 90),
        XAppAction("traffic_steering", "gnb_01", "PRB_QUOTA", 40, 50)
    ]
    conflicts = perception.register_action_group(actions)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.DIRECT

def test_detect_indirect_conflict():
    perception = Perception()
    actions = [
        XAppAction("xslice", "gnb_01", "PRB_QUOTA", 80, 90),
        XAppAction("energy_saving", "gnb_01", "TX_POWER", 10, 40)
    ]
    conflicts = perception.register_action_group(actions)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.INDIRECT
