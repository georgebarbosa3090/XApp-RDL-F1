import json
import math
import time
import pytest
from src.rdl_xapp import RDLxApp
from src.conflict_types import XAppAction, KPMReport, ConflictType
from src.core.perception import Perception
from src.core.reasoning import Reasoning
from src.infrastructure.memory_module import MemoryModule
from src.infrastructure.ric_request_id_allocator import RicRequestIdAllocator


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


def test_intra_batch_multi_conflict_resolution_no_self_lockout():
    xapp = RDLxApp()
    dispatched = []
    orig_dispatch = xapp.dispatcher.dispatch_control

    def spy_dispatch(decision, *args, **kwargs):
        dispatched.append((decision, kwargs.get("decision_latency_ms")))
        return orig_dispatch(decision, *args, **kwargs)

    xapp.dispatcher.dispatch_control = spy_dispatch

    actions = [
        XAppAction(xapp_id="xapp_low", node_id="gnb_batch", parameter="PRB_QUOTA", value=30.0, priority=10),
        XAppAction(xapp_id="xapp_mid", node_id="gnb_batch", parameter="PRB_QUOTA", value=50.0, priority=50),
        XAppAction(xapp_id="xapp_high", node_id="gnb_batch", parameter="PRB_QUOTA", value=80.0, priority=95),
    ]
    xapp._process_action_group(actions)

    # Deve despachar exatamente 1 decisão deduplicada com o vencedor de maior prioridade (95)
    assert len(dispatched) == 1
    decision, latency_ms = dispatched[0]
    assert len(decision.selected_actions) == 1
    assert decision.selected_actions[0].xapp_id == "xapp_high"
    assert decision.selected_actions[0].value == 80.0
    assert latency_ms is not None and not math.isnan(latency_ms) and latency_ms >= 0.0
    xapp.stop()


def test_convergent_actions_do_not_trigger_direct_conflict():
    p = Perception()
    a1 = XAppAction(xapp_id="xapp_1", node_id="gnb_01", parameter="PRB_QUOTA", value=60.0, priority=50)
    a2 = XAppAction(xapp_id="xapp_2", node_id="gnb_01", parameter="PRB_QUOTA", value=60.0, priority=60)
    conflicts = p.detect_action_group([a1, a2])
    direct_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.DIRECT]
    assert direct_conflicts == []


def test_kpm_ttl_expiration_in_perception():
    p = Perception(kpm_ttl_s=0.5)
    stale_report = KPMReport(
        node_id="gnb_ttl",
        ue_id="ue_1",
        drb_thp_dl=50.0,
        drb_thp_ul=10.0,
        drb_delay_dl=5.0,
        prb_used_dl=50.0,
        timestamp=time.time() - 2.0,
    )
    p.update_kpm_report(stale_report)
    assert p.get_latest_kpm("gnb_ttl") is None
    report, is_valid = p.get_kpm_report_with_ttl("gnb_ttl")
    assert report is None and is_valid is False


def test_earth_power_model_macro_cell_energy_score():
    mem = MemoryModule()
    r = Reasoning(mem, config={})
    act_low = XAppAction(xapp_id="es_xapp", node_id="gnb_macro", parameter="TX_POWER", value=23.0, priority=50)
    act_max = XAppAction(xapp_id="es_xapp", node_id="gnb_macro", parameter="TX_POWER", value=43.0, priority=50)
    score_low = r._calculate_action_scores(act_low)["energy"]
    score_max = r._calculate_action_scores(act_max)["energy"]
    assert score_low > 0.70
    assert score_low > score_max


def test_ric_request_id_allocator_wraparound():
    alloc = RicRequestIdAllocator(base_requestor_id=99)
    alloc._instance_counters[("gnb_1", 3)] = 65534
    id1 = alloc.allocate("gnb_1", 3)
    id2 = alloc.allocate("gnb_1", 3)
    assert id1.requestor_id == 99 and id1.instance_id == 65535
    assert id2.requestor_id == 99 and id2.instance_id == 1


def test_subscription_failure_scoped_per_meid():
    xapp = RDLxApp()
    xapp.active_subscriptions = {"gnb_1": True, "gnb_2": True}
    xapp._subscription_failure_handler(
        xapp.xapp,
        {"meid": "gnb_1", "payload": b"sub_fail"},
        None,
    )
    assert "gnb_1" not in xapp.active_subscriptions
    assert xapp.active_subscriptions.get("gnb_2") is True
    assert xapp.health.state.name != "DEGRADED"

    xapp._subscription_failure_handler(
        xapp.xapp,
        {"meid": "gnb_2", "payload": b"sub_fail"},
        None,
    )
    assert xapp.health.state.name == "DEGRADED"
    xapp.stop()
