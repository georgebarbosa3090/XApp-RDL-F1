import pytest
from unittest.mock import MagicMock
from src.e2.control_dispatcher import ControlDispatcher
from src.e2.e2ap.constants import RIC_CONTROL_REQ, RIC_SUBSCRIPTION_REQ
from src.conflict_types import RDLDecision, XAppAction
from src.infrastructure.memory_module import MemoryModule

class MockRMRClient:
    def __init__(self):
        self.sent_messages = []
    def rmr_send(self, payload, mtype, target=None):
        self.sent_messages.append({"payload": payload, "mtype": mtype, "target": target})
        return True

def test_dispatch_uses_ric_control_req_mtype():
    rmr = MockRMRClient()
    sdl = MemoryModule()
    dispatcher = ControlDispatcher(rmr_client=rmr, sdl_repo=sdl)

    action = XAppAction(
        xapp_id="test_xapp",
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=60.0,
        priority=10
    )
    decision = RDLDecision(
        decision_id="dec_01",
        selected_actions=[action],
        safety_result={"is_safe": True},
        affected_node="gnb_01",
        affected_cell="cell_01",
        previous_safe_value=50.0
    )

    ctrl_id = dispatcher.dispatch_control(decision)
    assert ctrl_id is not None
    assert len(rmr.sent_messages) == 1
    sent = rmr.sent_messages[0]
    assert sent["mtype"] == RIC_CONTROL_REQ
    assert sent["mtype"] == 12040
    assert sent["mtype"] != RIC_SUBSCRIPTION_REQ
    assert sent["target"] == "gnb_01"

def test_rollback_uses_ric_control_req_mtype():
    rmr = MockRMRClient()
    sdl = MemoryModule()
    dispatcher = ControlDispatcher(rmr_client=rmr, sdl_repo=sdl)

    action = XAppAction(
        xapp_id="test_xapp",
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=75.0,
        priority=10
    )
    decision = RDLDecision(
        decision_id="dec_02",
        selected_actions=[action],
        safety_result={"is_safe": True},
        affected_node="gnb_01",
        affected_cell="cell_01",
        previous_safe_value=50.0
    )

    ctrl_id = dispatcher.dispatch_control(decision)
    assert ctrl_id is not None
    rmr.sent_messages.clear()

    dispatcher.trigger_rollback(ctrl_id)
    assert len(rmr.sent_messages) == 1
    sent = rmr.sent_messages[0]
    assert sent["mtype"] == RIC_CONTROL_REQ
    assert sent["mtype"] == 12040
    assert len(dispatcher.rollback_history) == 1
    assert dispatcher.rollback_history[0]["requested_value"] == 50.0
    assert dispatcher.pending_requests[ctrl_id]["status"] == "SENT"
    assert dispatcher.pending_requests[ctrl_id]["rollback_status"] == "SENT_UNCONFIRMED"

def test_dispatch_stores_pending_request():
    rmr = MockRMRClient()
    sdl = MemoryModule()
    dispatcher = ControlDispatcher(rmr_client=rmr, sdl_repo=sdl)

    action = XAppAction(
        xapp_id="test_xapp",
        node_id="gnb_01",
        parameter="TX_POWER",
        value=30.0,
        priority=10
    )
    decision = RDLDecision(
        decision_id="dec_03",
        selected_actions=[action],
        safety_result={"is_safe": True},
        affected_node="gnb_01",
        affected_cell="cell_01",
        previous_safe_value=23.0
    )

    ctrl_id = dispatcher.dispatch_control(decision)
    assert ctrl_id in dispatcher.pending_requests
    info = dispatcher.pending_requests[ctrl_id]
    assert info["status"] == "SENT"
    assert info["target_value"] == 30.0
    assert info["previous_safe_value"] == 23.0
