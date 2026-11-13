"""
Testes de regressão das correções da avaliação técnica (nov/2026):
envio RMR com MEID, subscrição REST do SubMgr, readiness, slew-rate,
detecção de conflitos por grupo, arbitragem em dois estágios e rollback.
"""

import time

import pytest

from src.conflict_types import ConflictType, RDLDecision, XAppAction
from src.core.perception import Perception
from src.core.reasoning import Reasoning
from src.core.refinement import Refinement
from src.e2.control_dispatcher import ControlDispatcher
from src.e2.e2ap.constants import RIC_CONTROL_REQ
from src.e2.e2ap.control import RICcontrolRequest
from src.e2.e2ap.pdu import unwrap_e2ap_pdu
from src.e2.e2ap.subscription import TIME_TO_WAIT_VALUES, build_ric_subscription_request_payload
from src.infrastructure.memory_module import MemoryModule
from src.infrastructure.rmr_transport import send_rmr_message
from src.infrastructure.subscription_manager import SubscriptionManager
from src.observability.health_server import HAS_FASTAPI, SUBSCRIPTION_NOTIFICATION_PATH, AppState, HealthServer


# ---------------------------------------------------------------------------
# Envio RMR com MEID
# ---------------------------------------------------------------------------

class _FakeMbufContents:
    def __init__(self, state):
        self.state = state


class _FakeMbuf:
    def __init__(self, state=0):
        self.contents = _FakeMbufContents(state)


class FakeRmrModule:
    """Imita a API ``ricxappframe.rmr.rmr`` usada pelo transporte."""
    RMR_OK = 0
    RMR_ERR_RETRY = 10

    def __init__(self, states):
        self.states = list(states)
        self.alloc_kwargs = None
        self.freed = []
        self.send_calls = 0

    def rmr_alloc_msg(self, **kwargs):
        self.alloc_kwargs = kwargs
        return _FakeMbuf()

    def rmr_send_msg(self, mrc, sbuf):
        self.send_calls += 1
        return _FakeMbuf(self.states.pop(0))

    def rmr_free_msg(self, sbuf):
        self.freed.append(sbuf)


class RealLikeXapp:
    """Cliente com contexto RMR (``_mrc``) e a assinatura real ``rmr_send(payload, mtype, retries)``."""
    _mrc = object()

    def rmr_send(self, payload, mtype, retries=100):  # pragma: no cover - não deve ser usado
        raise AssertionError("rmr_send não define MEID e não deve ser usado para E2AP")


def test_rmr_transport_sets_meid_and_frees_buffer():
    rmr = FakeRmrModule([0])
    assert send_rmr_message(RealLikeXapp(), b"\x00\x01", RIC_CONTROL_REQ, "gnb_42", rmr_module=rmr) is True
    assert rmr.alloc_kwargs["meid"] == "gnb_42"
    assert rmr.alloc_kwargs["mtype"] == RIC_CONTROL_REQ
    assert len(rmr.freed) == 1


def test_rmr_transport_retries_only_on_retry_state():
    rmr = FakeRmrModule([10, 10, 0])
    assert send_rmr_message(RealLikeXapp(), b"x", RIC_CONTROL_REQ, "gnb_01", rmr_module=rmr) is True
    assert rmr.send_calls == 3

    rmr = FakeRmrModule([2, 0])  # erro definitivo (ex.: sem endpoint)
    assert send_rmr_message(RealLikeXapp(), b"x", RIC_CONTROL_REQ, "gnb_01", rmr_module=rmr) is False
    assert rmr.send_calls == 1
    assert len(rmr.freed) == 1


def test_rmr_transport_refuses_clients_without_meid_support():
    class LegacyClient:
        def rmr_send(self, payload, mtype, retries=100):
            return True

    assert send_rmr_message(LegacyClient(), b"x", RIC_CONTROL_REQ, "gnb_01") is False
    assert send_rmr_message(RealLikeXapp(), b"x", RIC_CONTROL_REQ, "", rmr_module=FakeRmrModule([0])) is False


def test_dispatcher_sends_control_with_target_meid(monkeypatch):
    rmr = FakeRmrModule([0])
    monkeypatch.setattr("src.infrastructure.rmr_transport._rmr", rmr)
    dispatcher = ControlDispatcher(rmr_client=RealLikeXapp(), sdl_repo=MemoryModule())
    action = XAppAction("xslice", "gnb_meid", "PRB_QUOTA", 60.0, 50)
    decision = RDLDecision(selected_actions=[action], safety_result={"is_safe": True})
    assert dispatcher.dispatch_control(decision) is not None
    assert rmr.alloc_kwargs["meid"] == "gnb_meid"


# ---------------------------------------------------------------------------
# Subscrição REST do SubMgr
# ---------------------------------------------------------------------------

def test_subscription_payload_matches_submgr_rest_schema():
    payload = build_ric_subscription_request_payload(
        target_node="gnb_01", ran_function_id=2, report_period_ms=200, xapp_event_instance_id=7
    )
    endpoint = payload["ClientEndpoint"]
    assert set(endpoint) == {"Host", "HTTPPort", "RMRPort"}
    assert isinstance(endpoint["HTTPPort"], int) and isinstance(endpoint["RMRPort"], int)
    detail = payload["SubscriptionDetails"][0]
    assert detail["XappEventInstanceId"] == 7
    assert detail["EventTriggers"] and all(isinstance(b, int) and 0 <= b <= 255 for b in detail["EventTriggers"])
    action = detail["ActionToBeSetupList"][0]
    assert all(isinstance(b, int) and 0 <= b <= 255 for b in action["ActionDefinition"])
    assert action["ActionType"] in ("insert", "policy", "report")
    assert action["SubsequentAction"]["TimeToWait"] in TIME_TO_WAIT_VALUES
    with pytest.raises(ValueError):
        build_ric_subscription_request_payload(ran_function_id=5000)


class _FakeResponse:
    def __init__(self, data, status_code=201):
        self._data = data
        self.status_code = status_code
        self.content = b"{}" if data is not None else b""

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._data


def test_subscription_manager_pending_until_notification(monkeypatch):
    posted = {}

    def fake_post(url, json, timeout):
        posted["url"], posted["body"] = url, json
        return _FakeResponse({"SubscriptionId": "sub-abc", "SubscriptionInstances": None})

    monkeypatch.setattr("src.infrastructure.subscription_manager.requests.post", fake_post)
    manager = SubscriptionManager(submgr_url="http://submgr:8088/")
    ctx = manager.request_kpm_subscription("gnb_01", 2)
    assert posted["url"] == "http://submgr:8088/ric/v1/subscriptions"
    assert ctx is not None and ctx.status == "PENDING"

    assert manager.handle_notification({"SubscriptionId": "unknown"}) is None
    ctx2, ok = manager.handle_notification({
        "SubscriptionId": "sub-abc",
        "SubscriptionInstances": [{"XappEventInstanceId": ctx.xapp_event_instance_id, "E2EventInstanceId": 9}],
    })
    assert ok is True and ctx2.status == "ACTIVE" and ctx2.e2_event_instance_id == 9


def test_subscription_manager_rejects_missing_id_and_error_notification(monkeypatch):
    monkeypatch.setattr(
        "src.infrastructure.subscription_manager.requests.post",
        lambda url, json, timeout: _FakeResponse({}),
    )
    manager = SubscriptionManager(submgr_url="http://submgr:8088")
    assert manager.request_kpm_subscription("gnb_01", 2) is None

    monkeypatch.setattr(
        "src.infrastructure.subscription_manager.requests.post",
        lambda url, json, timeout: _FakeResponse({"SubscriptionId": "sub-x"}),
    )
    assert manager.request_kpm_subscription("gnb_01", 2) is not None
    ctx, ok = manager.handle_notification({
        "SubscriptionId": "sub-x",
        "SubscriptionInstances": [{"XappEventInstanceId": 1, "E2EventInstanceId": 0, "ErrorCause": "E2 timeout"}],
    })
    assert ok is False and ctx.status == "FAILED"
    assert "gnb_01" not in manager.active_subscriptions


def test_rdl_xapp_becomes_ready_only_after_submgr_notification(monkeypatch):
    from src.rdl_xapp import RDLxApp

    monkeypatch.setenv("SUBMGR_URL", "http://submgr:8088")
    monkeypatch.setattr(
        "src.infrastructure.subscription_manager.requests.post",
        lambda url, json, timeout: _FakeResponse({"SubscriptionId": "sub-ready"}),
    )
    app = RDLxApp()
    try:
        app._entrypoint(app.xapp)
        assert app.health.state == AppState.SUBSCRIBING
        assert app.active_subscriptions == {"gnb_01": False}

        assert app._subscription_notification_handler({"SubscriptionId": "other"}) is None
        assert app.health.state == AppState.SUBSCRIBING

        ok = app._subscription_notification_handler({
            "SubscriptionId": "sub-ready",
            "SubscriptionInstances": [{"XappEventInstanceId": 1, "E2EventInstanceId": 3}],
        })
        assert ok is True
        assert app.health.state == AppState.READY
        assert app.active_subscriptions == {"gnb_01": True}
    finally:
        app.stop()


def test_rdl_xapp_without_submgr_stays_in_local_governance(monkeypatch):
    from src.rdl_xapp import RDLxApp

    monkeypatch.delenv("SUBMGR_URL", raising=False)
    app = RDLxApp()
    try:
        assert app.subscription_manager is None
        assert app.send_subscription_request("gnb_01") is False
    finally:
        app.stop()


@pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI indisponível")
def test_health_server_ready_and_subscription_callback():
    from fastapi.testclient import TestClient

    server = HealthServer(port=0)
    client = TestClient(server.app)
    server.set_state(AppState.SUBSCRIBING)
    assert client.get("/ready").status_code == 503

    received = []
    server.subscription_callback = lambda body: received.append(body) or True
    response = client.post(SUBSCRIPTION_NOTIFICATION_PATH, json={"SubscriptionId": "s1"})
    assert response.status_code == 200 and received == [{"SubscriptionId": "s1"}]

    server.subscription_callback = lambda body: None
    assert client.post(SUBSCRIPTION_NOTIFICATION_PATH, json={"SubscriptionId": "x"}).status_code == 404
    assert client.post(SUBSCRIPTION_NOTIFICATION_PATH, content=b"not json").status_code == 400


# ---------------------------------------------------------------------------
# Slew-rate
# ---------------------------------------------------------------------------

def test_slew_rate_uses_committed_state_from_perception():
    perception = Perception()
    perception.commit_actions([XAppAction("es", "gnb_slew", "PRB_QUOTA", 40.0, 60)])
    refinement = Refinement(
        MemoryModule(),
        config={"enforce_slew_rate": True, "minimum_control_interval_ms": 0},
        committed_action_lookup=perception.get_committed_action,
    )
    big_jump = XAppAction("xslice", "gnb_slew", "PRB_QUOTA", 90.0, 90)
    ok, _, reason = refinement.validate_single_action(big_jump, record_timestamp=False)
    assert ok is False and "slew-rate" in reason
    small_step = XAppAction("xslice", "gnb_slew", "PRB_QUOTA", 60.0, 90)
    assert refinement.validate_single_action(small_step, record_timestamp=False)[0] is True


def test_slew_rate_fails_closed_without_committed_state_source():
    refinement = Refinement(MemoryModule(), config={"enforce_slew_rate": True, "minimum_control_interval_ms": 0})
    ok, _, reason = refinement.validate_single_action(
        XAppAction("xslice", "gnb_01", "PRB_QUOTA", 60.0, 90), record_timestamp=False
    )
    assert ok is False and "committed-state" in reason


# ---------------------------------------------------------------------------
# Detecção de conflitos por grupo
# ---------------------------------------------------------------------------

def test_direct_conflict_is_one_event_per_target():
    perception = Perception()
    actions = [
        XAppAction("xslice", "gnb_01", "PRB_QUOTA", 80, 90),
        XAppAction("ts", "gnb_01", "PRB_QUOTA", 40, 80),
        XAppAction("es", "gnb_01", "PRB_QUOTA", 20, 65),
    ]
    conflicts = perception.detect_action_group(actions)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.DIRECT
    assert len(conflicts[0].involved_xapps) == 3


def test_conflict_detection_scales_linearly():
    perception = Perception()
    many = [XAppAction(f"x{i}", "gnb_01", "PRB_QUOTA", float(i % 100), 50) for i in range(4000)]
    t0 = time.perf_counter()
    conflicts = perception.detect_action_group(many)
    elapsed = time.perf_counter() - t0
    assert len(conflicts) == 1
    assert len(conflicts[0].involved_xapps) == 4000
    assert elapsed < 1.0


def test_repeated_proposals_from_same_xapp_are_deduplicated():
    perception = Perception()
    first = XAppAction("xslice", "gnb_01", "PRB_QUOTA", 50, 90)
    latest = XAppAction("xslice", "gnb_01", "PRB_QUOTA", 70, 90)
    other = XAppAction("es", "gnb_01", "PRB_QUOTA", 30, 60)
    conflicts = perception.detect_action_group([first, latest, other])
    assert len(conflicts) == 1
    involved = conflicts[0].involved_xapps
    assert latest in involved and first not in involved


def test_indirect_conflict_against_committed_state():
    perception = Perception()
    incumbent = XAppAction("es", "gnb_01", "TX_POWER", 20.0, 65)
    perception.commit_actions([incumbent])
    new = XAppAction("xslice", "gnb_01", "PRB_QUOTA", 80, 90)
    conflicts = perception.detect_action_group([new])
    assert [c.conflict_type for c in conflicts] == [ConflictType.INDIRECT]
    assert incumbent in conflicts[0].involved_xapps and new in conflicts[0].involved_xapps


def test_eevs_exact_search_only_enumerates_compatible_subsets():
    reasoning = Reasoning(MemoryModule(), config={"max_exact_subsets": 3})
    perception = Perception()
    a = XAppAction("xslice", "gnb_01", "PRB_QUOTA", 80, 90)
    b = XAppAction("ts", "gnb_01", "HANDOVER", 1, 80)
    conflict = perception.detect_action_group([a, b])[0]
    resolution = reasoning.resolve(conflict)
    targets = [(act.node_id, act.parameter) for act in resolution.winning_actions]
    assert len(targets) == len(set(targets))
    assert resolution.confidence == 0.88  # (1+1)*(1+1)-1 = 3 subconjuntos: busca exata


# ---------------------------------------------------------------------------
# Arbitragem em dois estágios
# ---------------------------------------------------------------------------

def _spy_dispatch(app):
    dispatched = []
    original = app.dispatcher.dispatch_control

    def spy(decision, *args, **kwargs):
        dispatched.append(decision.selected_actions[0])
        return original(decision, *args, **kwargs)

    app.dispatcher.dispatch_control = spy
    return dispatched


def test_incumbent_winner_is_not_redispatched():
    from src.rdl_xapp import RDLxApp

    app = RDLxApp()
    try:
        dispatched = _spy_dispatch(app)
        incumbent = XAppAction("xslice", "gnb_inc", "PRB_QUOTA", 80.0, 95)
        app.perception.commit_actions([incumbent])
        challenger = XAppAction("es", "gnb_inc", "PRB_QUOTA", 20.0, 10)
        app._process_action_group([challenger])
        assert dispatched == []
    finally:
        app.stop()


def test_direct_stage_winner_is_not_overridden_by_priority_merge():
    from src.rdl_xapp import RDLxApp

    app = RDLxApp()
    try:
        dispatched = _spy_dispatch(app)
        actions = [
            XAppAction("xapp_low", "gnb_two_stage", "PRB_QUOTA", 30.0, 10),
            XAppAction("xapp_mid", "gnb_two_stage", "PRB_QUOTA", 50.0, 50),
            XAppAction("xapp_high", "gnb_two_stage", "PRB_QUOTA", 80.0, 95),
        ]
        app._process_action_group(actions)
        assert [a.xapp_id for a in dispatched] == ["xapp_high"]
    finally:
        app.stop()


def test_indirect_stage_arbitrates_only_direct_stage_winners():
    from src.rdl_xapp import RDLxApp

    app = RDLxApp()
    try:
        dispatched = _spy_dispatch(app)
        resolved = []
        original_resolve = app.reasoning.resolve

        def spy_resolve(conflict):
            resolved.append(conflict)
            return original_resolve(conflict)

        app.reasoning.resolve = spy_resolve
        prb_low = XAppAction("xapp_low", "gnb_indirect", "PRB_QUOTA", 30.0, 10)
        prb_high = XAppAction("xslice", "gnb_indirect", "PRB_QUOTA", 80.0, 95)
        handover = XAppAction("ts", "gnb_indirect", "HANDOVER", 1.0, 80)
        app._process_action_group([prb_low, prb_high, handover])

        indirect = [c for c in resolved if c.conflict_type == ConflictType.INDIRECT]
        assert len(indirect) == 1
        # O perdedor do estágio direto não volta a competir no estágio indireto.
        assert prb_low not in indirect[0].involved_xapps
        assert prb_high in indirect[0].involved_xapps and handover in indirect[0].involved_xapps

        targets = [(a.node_id, a.parameter) for a in dispatched]
        assert dispatched and len(targets) == len(set(targets))
        assert prb_low not in dispatched
    finally:
        app.stop()


def test_indirect_loser_target_is_blocked(monkeypatch):
    """EEVS por média (B3M): combinar ES com URLLC baixa a média e só a URLLC passa."""
    monkeypatch.setenv("RDL_EEVS_AGGREGATION", "mean")
    from src.rdl_xapp import RDLxApp

    app = RDLxApp()
    try:
        dispatched = _spy_dispatch(app)
        urllc = XAppAction("xslice", "gnb_eevs", "PRB_QUOTA", 80.0, 95)
        energy = XAppAction("energy_saving", "gnb_eevs", "TX_POWER", 10.0, 40)
        app._process_action_group([urllc, energy])
        assert dispatched == [urllc]
    finally:
        app.stop()


def test_additive_eevs_admits_compatible_energy_action_with_urllc():
    """EEVS aditivo (padrão): a ação de energia compatível entra junto com a URLLC; a penalidade de 0,20 por
    combiná-las não compensa o ganho somado de energia (risco documentado no doc 02 §4.3)."""
    from src.rdl_xapp import RDLxApp

    app = RDLxApp()
    try:
        assert app.reasoning.eevs_aggregation == "additive"
        dispatched = _spy_dispatch(app)
        urllc = XAppAction("xslice", "gnb_eevs", "PRB_QUOTA", 80.0, 95)
        energy = XAppAction("energy_saving", "gnb_eevs", "TX_POWER", 10.0, 40)
        app._process_action_group([urllc, energy])
        assert sorted(a.parameter for a in dispatched) == ["PRB_QUOTA", "TX_POWER"]
    finally:
        app.stop()


# ---------------------------------------------------------------------------
# Dispatcher: anti-leak e rollback
# ---------------------------------------------------------------------------

class RecordingRmr:
    def __init__(self):
        self.sent = []

    def rmr_send_with_meid(self, payload, mtype, meid):
        self.sent.append((payload, mtype, meid))
        return True


def _dispatch(dispatcher, node="gnb_01", value=60.0, previous=50.0):
    action = XAppAction("xslice", node, "PRB_QUOTA", value, 50)
    decision = RDLDecision(selected_actions=[action], safety_result={"is_safe": True}, previous_safe_value=previous)
    return dispatcher.dispatch_control(decision)


def test_prune_finalized_removes_only_old_terminal_requests():
    dispatcher = ControlDispatcher(rmr_client=RecordingRmr(), sdl_repo=MemoryModule(), default_timeout_s=1.0)
    old_id = _dispatch(dispatcher)
    live_id = _dispatch(dispatcher, value=70.0)
    dispatcher.pending_requests[old_id]["status"] = "ACKNOWLEDGED"
    dispatcher.pending_requests[old_id]["finalized_at"] = time.time() - 1000
    assert dispatcher.prune_finalized(max_age_s=300) == 1
    assert old_id not in dispatcher.pending_requests
    assert live_id in dispatcher.pending_requests


def test_rollback_uses_fresh_request_id_and_no_ack():
    rmr = RecordingRmr()
    dispatcher = ControlDispatcher(rmr_client=rmr, sdl_repo=MemoryModule(), default_timeout_s=1.0)
    ctrl_id = _dispatch(dispatcher, node="gnb_rollback_fresh", value=75.0, previous=50.0)
    original = dispatcher.pending_requests[ctrl_id]

    expired = dispatcher.check_timeouts(now=time.time() + 5.0)
    assert ctrl_id in expired
    assert original["rollback_status"] == "SENT_UNCONFIRMED"
    assert original["rollback_request_id"] != (original["requestor_id"], original["instance_id"])

    payload, mtype, meid = rmr.sent[-1]
    assert mtype == RIC_CONTROL_REQ and meid == "gnb_rollback_fresh"
    pdu_type, _, _, inner = unwrap_e2ap_pdu(payload)
    request = RICcontrolRequest()
    request.from_aper(inner)
    fields = request()
    assert fields["ricControlAckRequest"] == 0
    assert fields["ricRequestID"]["ricInstanceID"] == original["rollback_request_id"][1]


def test_rollback_rejects_out_of_bounds_previous_value():
    dispatcher = ControlDispatcher(rmr_client=RecordingRmr(), sdl_repo=MemoryModule())
    ctrl_id = _dispatch(dispatcher, node="gnb_rollback_oob", previous=500.0)
    assert dispatcher.trigger_rollback(ctrl_id) is False
    assert dispatcher.pending_requests[ctrl_id]["rollback_status"] == "UNAVAILABLE"


def test_rollback_history_is_bounded():
    dispatcher = ControlDispatcher(rmr_client=RecordingRmr(), sdl_repo=MemoryModule())
    dispatcher.MAX_ROLLBACK_HISTORY = 3
    for i in range(5):
        ctrl_id = _dispatch(dispatcher, node=f"gnb_hist_{i}")
        assert dispatcher.trigger_rollback(ctrl_id) is True
    assert len(dispatcher.rollback_history) == 3
    assert dispatcher.rollback_history[-1]["node_id"] == "gnb_hist_4"
