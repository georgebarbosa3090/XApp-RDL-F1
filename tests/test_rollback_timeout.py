import time
import pytest
from src.e2.control_dispatcher import ControlDispatcher
from src.conflict_types import RDLDecision, XAppAction
from src.infrastructure.memory_module import MemoryModule
from src.observability.causal_tracker import causal_tracker
from src.e2.e2ap.control import RICcontrolAcknowledge, RICcontrolFailure
from src.e2.e2ap.pdu import wrap_successful_outcome, wrap_unsuccessful_outcome
from src.e2.e2ap.constants import PROC_RIC_CONTROL

class MockRMR:
    def __init__(self):
        self.sent = []
    def rmr_send(self, payload, mtype, target=None):
        self.sent.append((payload, mtype, target))
        return True

def test_dispatch_and_ack_integration():
    rmr = MockRMR()
    sdl = MemoryModule()
    dispatcher = ControlDispatcher(rmr_client=rmr, sdl_repo=sdl)

    action = XAppAction(xapp_id="xapp_1", node_id="gnb_01", parameter="PRB_QUOTA", value=80.0, priority=1)
    decision = RDLDecision(
        decision_id="dec_int_01",
        selected_actions=[action],
        safety_result={"is_safe": True},
        affected_node="gnb_01",
        affected_cell="cell_01",
        previous_safe_value=50.0
    )

    ctrl_id = dispatcher.dispatch_control(decision)
    assert ctrl_id in dispatcher.pending_requests
    req_info = dispatcher.pending_requests[ctrl_id]
    req_id = req_info["requestor_id"]
    causal_tracker.record_decision(
        action_id=action.action_id,
        decision_id=decision.decision_id,
        ric_request_id=causal_tracker.correlation_id(
            req_info["meid"], req_info["ran_function_id"], req_id, req_info["instance_id"]
        ),
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        old_val=50.0,
        new_val=80.0,
        strategy="PASS_THROUGH"
    )

    # Injetar ACK correspondente
    ack = RICcontrolAcknowledge()
    ack.set_val({
        'ricRequestID': {'ricRequestorID': req_id, 'ricInstanceID': req_info["instance_id"]},
        'ranFunctionID': req_info["ran_function_id"]
    })
    wrapped_ack = wrap_successful_outcome(PROC_RIC_CONTROL, ack.to_aper())

    time.sleep(0.01)
    ack_res = dispatcher.handle_ack(wrapped_ack)
    assert ack_res is not None
    assert ack_res["status"] == "ACKNOWLEDGED"

    # Verificar CausalTracker
    record = causal_tracker.records[action.action_id]
    assert record.ack_status == "ACKNOWLEDGED"
    assert record.rtt_ms > 0

def test_failure_triggers_rollback():
    rmr = MockRMR()
    sdl = MemoryModule()
    dispatcher = ControlDispatcher(rmr_client=rmr, sdl_repo=sdl)

    action = XAppAction(xapp_id="xapp_2", node_id="gnb_01", parameter="TX_POWER", value=40.0, priority=1)
    decision = RDLDecision(
        decision_id="dec_fail_01",
        selected_actions=[action],
        safety_result={"is_safe": True},
        affected_node="gnb_01",
        affected_cell="cell_01",
        previous_safe_value=23.0
    )

    ctrl_id = dispatcher.dispatch_control(decision)
    req_info = dispatcher.pending_requests[ctrl_id]
    req_id = req_info["requestor_id"]
    causal_tracker.record_decision(
        action_id=action.action_id,
        decision_id=decision.decision_id,
        ric_request_id=causal_tracker.correlation_id(
            req_info["meid"], req_info["ran_function_id"], req_id, req_info["instance_id"]
        ),
        node_id="gnb_01",
        parameter="TX_POWER",
        old_val=23.0,
        new_val=40.0,
        strategy="PASS_THROUGH"
    )

    # Injetar Failure
    fail = RICcontrolFailure()
    fail.set_val({
        'ricRequestID': {'ricRequestorID': req_id, 'ricInstanceID': req_info["instance_id"]},
        'ranFunctionID': req_info["ran_function_id"],
        'cause': 3
    })
    wrapped_fail = wrap_unsuccessful_outcome(PROC_RIC_CONTROL, fail.to_aper())

    fail_res = dispatcher.handle_failure(wrapped_fail)
    assert fail_res is not None
    assert fail_res["status"] == "FAILED"
    assert fail_res["rollback_status"] == "SENT_UNCONFIRMED"
    assert len(dispatcher.rollback_history) == 1
    assert dispatcher.rollback_history[0]["requested_value"] == 23.0

    record = causal_tracker.records[action.action_id]
    assert record.ack_status == "FAILED"
    assert record.cause_code == 3

def test_check_timeouts_triggers_rollback():
    rmr = MockRMR()
    sdl = MemoryModule()
    dispatcher = ControlDispatcher(rmr_client=rmr, sdl_repo=sdl, default_timeout_s=1.0)

    action = XAppAction(xapp_id="xapp_3", node_id="gnb_01", parameter="PRB_QUOTA", value=90.0, priority=1)
    decision = RDLDecision(
        decision_id="dec_to_01",
        selected_actions=[action],
        safety_result={"is_safe": True},
        affected_node="gnb_01",
        affected_cell="cell_01",
        previous_safe_value=50.0
    )

    ctrl_id = dispatcher.dispatch_control(decision)
    assert ctrl_id in dispatcher.pending_requests

    # Não enviar ACK, simular avanço no tempo
    future_time = time.time() + 5.0
    timed_out = dispatcher.check_timeouts(now=future_time)
    assert ctrl_id in timed_out
    assert dispatcher.pending_requests[ctrl_id]["status"] == "TIMEOUT"
    assert dispatcher.pending_requests[ctrl_id]["rollback_status"] == "SENT_UNCONFIRMED"
    assert len(dispatcher.rollback_history) == 1
    assert dispatcher.rollback_history[0]["requested_value"] == 50.0

def test_anti_leak_cleanup():
    rmr = MockRMR()
    sdl = MemoryModule()
    dispatcher = ControlDispatcher(rmr_client=rmr, sdl_repo=sdl, default_timeout_s=0.5)

    ctrl_ids = []
    for i in range(10):
        act = XAppAction(xapp_id=f"xapp_{i}", node_id="gnb_01", parameter="PRB_QUOTA", value=float(10 + i), priority=1)
        dec = RDLDecision(
            decision_id=f"dec_leak_{i}",
            selected_actions=[act],
            safety_result={"is_safe": True},
            affected_node="gnb_01",
            affected_cell="cell_01",
            previous_safe_value=50.0
        )
        ctrl_ids.append(dispatcher.dispatch_control(dec))

    assert len(dispatcher.pending_requests) == 10
    future = time.time() + 2.0
    timed_out = dispatcher.check_timeouts(now=future)
    assert len(timed_out) == 10
    assert len(dispatcher.req_key_to_id) == 0
