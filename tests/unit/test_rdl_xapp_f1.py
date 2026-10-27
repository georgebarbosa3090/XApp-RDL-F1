import json
import pytest
from src.rdl_xapp import RDLxApp
from src.conflict_types import XAppAction

def test_rdl_xapp_f1_lifecycle():
    xapp = RDLxApp()
    assert xapp.backend is not None
    assert xapp.allocator is not None

    action = XAppAction(
        xapp_id="xApp_QoS",
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=75.0,
        priority=10
    )
    xapp.inject_xapp_action(action)
    assert len(xapp.proposal_buffer) == 1

    xapp._process_action_group(xapp.proposal_buffer)

    summary_ack = {
        "payload": json.dumps({"status": "ACKNOWLEDGED", "transaction_id": "tx_123"}).encode('utf-8')
    }
    xapp._control_ack_handler(xapp.xapp, summary_ack, None)
    xapp._control_failure_handler(xapp.xapp, summary_ack, None)
    xapp.stop()


def test_strict_mode_rejects_proposals_without_authenticated_sender():
    xapp = RDLxApp()
    xapp.oran_strict = True
    before = len(xapp.proposal_buffer)
    payload = json.dumps({
        "xapp_id": "claimed_identity",
        "node_id": "gnb_01",
        "parameter": "PRB_QUOTA",
        "value": 50,
        "priority": 50,
    }).encode("utf-8")

    xapp._action_proposal_handler(xapp.xapp, {"payload": payload}, None)

    assert len(xapp.proposal_buffer) == before
    xapp.stop()


def test_strict_entrypoint_fails_closed_without_verified_protocol_adapter():
    xapp = RDLxApp()
    xapp.oran_strict = True

    xapp._entrypoint(xapp.xapp)

    assert xapp.health.state.name == "ERROR"
    assert not xapp.active_subscriptions
    xapp.stop()


def test_proposal_validation_rejects_non_finite_priority_and_overflow():
    xapp = RDLxApp()
    payloads = [
        {"xapp_id": "test", "node_id": "gnb_01", "parameter": "PRB_QUOTA", "value": float("nan")},
        {"xapp_id": "test", "node_id": "gnb_01", "parameter": "PRB_QUOTA", "value": 50, "priority": 101},
    ]
    for data in payloads:
        xapp._action_proposal_handler(
            xapp.xapp,
            {"payload": json.dumps(data).encode("utf-8")},
            None,
        )
    assert xapp.proposal_buffer == []

    xapp.MAX_PROPOSALS = 1
    valid = json.dumps({
        "xapp_id": "test",
        "node_id": "gnb_01",
        "parameter": "PRB_QUOTA",
        "value": 50,
        "priority": 50,
    }).encode("utf-8")
    xapp._action_proposal_handler(xapp.xapp, {"payload": valid}, None)
    xapp._action_proposal_handler(xapp.xapp, {"payload": valid}, None)
    assert len(xapp.proposal_buffer) == 1
    xapp.stop()
