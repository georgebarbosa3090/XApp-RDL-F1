import pytest
import uuid
from src.conflict_types import XAppAction, ConflictEvent, ConflictType, ConflictSeverity
from src.infrastructure.memory_module import MemoryModule

@pytest.fixture
def mock_memory():
    return MemoryModule()

@pytest.fixture
def action_tx_power():
    return XAppAction(
        xapp_id="xapp_1",
        node_id="gnb_01",
        parameter="TX_POWER",
        value=20.0,
        priority=60
    )

@pytest.fixture
def action_prb_quota():
    return XAppAction(
        xapp_id="xapp_2",
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=50.0,
        priority=80
    )

@pytest.fixture
def direct_conflict(action_tx_power):
    # Duas ações apontando para o mesmo parâmetro
    action2 = XAppAction(
        xapp_id="xapp_2",
        node_id="gnb_01",
        parameter="TX_POWER",
        value=15.0,
        priority=80
    )
    return ConflictEvent(
        conflict_id=str(uuid.uuid4()),
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[action_tx_power, action2],
        affected_kpis=["DRB.UEThpDl", "DRB.RlcSduDelayDl"],
        detected_at=0.0,
        description="Conflito direto em TX_POWER"
    )
