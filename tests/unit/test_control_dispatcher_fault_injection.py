"""
Testes Unitários de Injeção de Falhas, ACK Tracker e Rollback de Segurança
Valida o comportamento do ControlDispatcher sob condições normais, falhas E2AP e timeouts.
"""

import pytest
import time
import uuid
from src.coordination.control_dispatcher import ControlDispatcher
from src.conflict_types import RDLDecision, XAppAction
from src.e2.e2ap.control import (
    RICcontrolAcknowledge,
    RICcontrolFailure,
    wrap_successful_outcome,
    wrap_unsuccessful_outcome,
    PROC_RIC_CONTROL
)
from src.e2.e2ap.constants import CRITICALITY_IGNORE

class MockRMR:
    def __init__(self):
        self.sent_messages = []
    def rmr_send(self, payload, mtype, target):
        self.sent_messages.append({"payload": payload, "mtype": mtype, "target": target})
        return True

class MockSDL:
    def __init__(self):
        self.db = {}
    def save_control_request(self, req_id, info):
        self.db[req_id] = info
    def update_control_result(self, req_id, status):
        if req_id in self.db:
            self.db[req_id]["status"] = status

def test_control_dispatcher_successful_dispatch_and_ack():
    rmr = MockRMR()
    sdl = MockSDL()
    dispatcher = ControlDispatcher(rmr_client=rmr, sdl_repo=sdl, default_timeout_s=5.0)

    action = XAppAction(xapp_id="xslice", node_id="gnb_01", parameter="PRB_QUOTA", value=60.0, priority=90)
    decision = RDLDecision(
        decision_id="dec_001",
        selected_actions=[action],
        safety_result={"is_safe": True, "level": 1, "reason": "OK"}
    )
    decision.previous_safe_value = 50.0

    ctrl_id = dispatcher.dispatch_control(decision)
    assert ctrl_id is not None
    assert len(rmr.sent_messages) == 1
    assert rmr.sent_messages[0]["target"] == "gnb_01"
    assert ctrl_id in dispatcher.pending_requests
    assert dispatcher.pending_requests[ctrl_id]["status"] == "SENT"

    req_info = dispatcher.pending_requests[ctrl_id]
    req_id = req_info["requestor_id"]
    inst_id = req_info["instance_id"]

    # Simular recebimento de RIC_CONTROL_ACK
    ack = RICcontrolAcknowledge()
    ack.set_val({
        'ricRequestID': {'ricRequestorID': req_id, 'ricInstanceID': inst_id},
        'ranFunctionID': 3,
        'ricControlOutcome': b'OK'
    })
    ack_pdu = wrap_successful_outcome(PROC_RIC_CONTROL, ack.to_aper(), criticality=CRITICALITY_IGNORE)

    ack_res = dispatcher.handle_ack(ack_pdu)
    assert ack_res is not None
    assert ack_res["status"] == "ACKNOWLEDGED"
    assert dispatcher.pending_requests[ctrl_id]["status"] == "ACKNOWLEDGED"

def test_control_dispatcher_failure_triggers_rollback():
    rmr = MockRMR()
    sdl = MockSDL()
    dispatcher = ControlDispatcher(rmr_client=rmr, sdl_repo=sdl, default_timeout_s=5.0)

    action = XAppAction(xapp_id="energy_saver", node_id="gnb_02", parameter="TX_POWER", value=20.0, priority=50)
    decision = RDLDecision(
        decision_id="dec_002",
        selected_actions=[action],
        safety_result={"is_safe": True, "level": 1, "reason": "OK"}
    )
    decision.previous_safe_value = 43.0

    ctrl_id = dispatcher.dispatch_control(decision)
    assert ctrl_id is not None
    assert len(rmr.sent_messages) == 1

    req_info = dispatcher.pending_requests[ctrl_id]
    req_id = req_info["requestor_id"]
    inst_id = req_info["instance_id"]

    # Simular recebimento de RIC_CONTROL_FAILURE
    fail = RICcontrolFailure()
    fail.set_val({
        'ricRequestID': {'ricRequestorID': req_id, 'ricInstanceID': inst_id},
        'ranFunctionID': 3,
        'cause': 2 # RAN resource limitation
    })
    fail_pdu = wrap_unsuccessful_outcome(PROC_RIC_CONTROL, fail.to_aper(), criticality=CRITICALITY_IGNORE)

    fail_res = dispatcher.handle_failure(fail_pdu)
    assert fail_res is not None
    assert fail_res["status"] == "ROLLED_BACK"
    assert dispatcher.pending_requests[ctrl_id]["status"] == "ROLLED_BACK"

    # Verifica se comando de restauração (rollback) foi emitido via RMR
    assert len(rmr.sent_messages) == 2
    assert len(dispatcher.rollback_history) == 1
    assert dispatcher.rollback_history[0]["restored_value"] == 43.0

def test_control_dispatcher_timeout_triggers_rollback():
    rmr = MockRMR()
    sdl = MockSDL()
    dispatcher = ControlDispatcher(rmr_client=rmr, sdl_repo=sdl, default_timeout_s=1.0)

    action = XAppAction(xapp_id="xslice", node_id="gnb_01", parameter="PRB_QUOTA", value=75.0, priority=80)
    decision = RDLDecision(
        decision_id="dec_003",
        selected_actions=[action],
        safety_result={"is_safe": True, "level": 1, "reason": "OK"}
    )
    decision.previous_safe_value = 50.0

    ctrl_id = dispatcher.dispatch_control(decision)
    assert ctrl_id is not None

    # Verifica sem timeout inicialmente
    timed_out = dispatcher.check_timeouts(now=time.time())
    assert len(timed_out) == 0

    # Simula passagem de tempo (2.0 segundos depois)
    timed_out = dispatcher.check_timeouts(now=time.time() + 2.0)
    assert len(timed_out) == 1
    assert timed_out[0] == ctrl_id
    assert dispatcher.pending_requests[ctrl_id]["status"] == "ROLLED_BACK"
    assert len(dispatcher.rollback_history) == 1
    assert dispatcher.rollback_history[0]["restored_value"] == 50.0

def test_control_dispatcher_safety_guard_blocks_dispatch():
    rmr = MockRMR()
    sdl = MockSDL()
    dispatcher = ControlDispatcher(rmr_client=rmr, sdl_repo=sdl)

    action = XAppAction(xapp_id="malicious_xapp", node_id="gnb_01", parameter="PRB_QUOTA", value=150.0, priority=100)
    unsafe_decision = RDLDecision(
        decision_id="dec_unsafe",
        selected_actions=[action],
        safety_result={"is_safe": False, "level": 3, "reason": "PRB_QUOTA out of bounds (> 100%)"}
    )

    ctrl_id = dispatcher.dispatch_control(unsafe_decision)
    assert ctrl_id is None
    assert len(rmr.sent_messages) == 0
    assert len(dispatcher.pending_requests) == 0
