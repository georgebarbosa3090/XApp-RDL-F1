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
