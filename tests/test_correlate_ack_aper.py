import json
import pytest
from src.e2.e2ap.control import RICcontrolAcknowledge, RICcontrolFailure
from src.e2.e2ap.pdu import wrap_successful_outcome, wrap_unsuccessful_outcome
from src.e2.e2ap.constants import PROC_RIC_CONTROL
from src.infrastructure.ran_backend_factory import get_ran_backend_adapter

def test_correlate_ack_aper_roundtrip():
    adapter = get_ran_backend_adapter("NORI_NS3")

    ack = RICcontrolAcknowledge()
    ack.set_val({
        'ricRequestID': {'ricRequestorID': 1001, 'ricInstanceID': 1},
        'ranFunctionID': 3,
        'ricControlOutcome': b'OK'
    })
    raw_ack = ack.to_aper()
    wrapped_ack = wrap_successful_outcome(PROC_RIC_CONTROL, raw_ack)

    result = adapter.correlate_ack(wrapped_ack)
    assert result["status"] == "ACK_RECEIVED"
    assert result["raw_decoded"] is True
    assert result["requestor_id"] == 1001
    assert result["instance_id"] == 1
    assert result["ran_function_id"] == 3

def test_correlate_failure_aper_roundtrip():
    adapter = get_ran_backend_adapter("NORI_NS3")

    fail = RICcontrolFailure()
    fail.set_val({
        'ricRequestID': {'ricRequestorID': 2002, 'ricInstanceID': 1},
        'ranFunctionID': 3,
        'cause': 4
    })
    raw_fail = fail.to_aper()
    wrapped_fail = wrap_unsuccessful_outcome(PROC_RIC_CONTROL, raw_fail)

    result = adapter.correlate_ack(wrapped_fail)
    assert result["status"] == "FAILURE_RECEIVED"
    assert result["raw_decoded"] is True
    assert result["requestor_id"] == 2002
    assert result["instance_id"] == 1
    assert result["ran_function_id"] == 3
    assert result["cause"] == 4

def test_correlate_ack_srsran_backend():
    adapter = get_ran_backend_adapter("SRSRAN_E2")

    ack = RICcontrolAcknowledge()
    ack.set_val({
        'ricRequestID': {'ricRequestorID': 3003, 'ricInstanceID': 1},
        'ranFunctionID': 3,
        'ricControlOutcome': b'SUCCESS'
    })
    raw_ack = ack.to_aper()
    wrapped_ack = wrap_successful_outcome(PROC_RIC_CONTROL, raw_ack)

    result = adapter.correlate_ack(wrapped_ack)
    assert result["status"] == "ACK_RECEIVED"
    assert result["raw_decoded"] is True
    assert result["requestor_id"] == 3003
    assert result["instance_id"] == 1

def test_correlate_ack_json_fallback():
    adapter = get_ran_backend_adapter("NORI_NS3")
    json_payload = json.dumps({
        "status": "ACK",
        "requestor_id": 4004,
        "instance_id": 1,
        "node_id": "gnb_01"
    }).encode("utf-8")

    result = adapter.correlate_ack(json_payload, allow_test_fallback=True)
    assert result["requestor_id"] == 4004
    assert result["instance_id"] == 1
    assert result["raw_decoded"] is False
