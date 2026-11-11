"""Janela de decisão (doc 09 §2.4): registro de recusas, aviso à xApp, adiamento, validade,
intervalo e cota do caminho crítico, alvos críticos por A1."""
import json
import time
import types

import pytest

from src.conflict_types import XAppAction
from src.core import proposal_registry as preg
from src.core.decision_window import AdaptiveDecisionWindow, Urgency, WindowConfig, parse_critical_targets
from src.core.proposal_registry import ProposalRegistry
from src.core.refinement import Refinement
from src.e2.e2ap.constants import RDL_ACTION_RESULT
from src.infrastructure.memory_module import MemoryModule
from src.interfaces.a1_policy_receiver import A1PolicyManager


def act(xapp, node, param, value, prio, **kw):
    return XAppAction(xapp_id=xapp, node_id=node, parameter=param, value=float(value), priority=prio, **kw)


@pytest.fixture
def app(monkeypatch, tmp_path):
    topo = tmp_path / "topo.json"
    topo.write_text(json.dumps({"neighbors": {"gnb_0": ["gnb_1"]}}), encoding="utf-8")
    monkeypatch.setenv("RDL_TOPOLOGY_FILE", str(topo))
    from src.rdl_xapp import RDLxApp
    instance = RDLxApp()
    instance.dispatcher.dispatch_control = lambda decision, **_: "req"
    sent = []
    instance.xapp = types.SimpleNamespace(rmr_send=lambda payload, mtype, *a, **k: sent.append((json.loads(payload), mtype)) or True,
                                          stop=lambda: None)
    instance.sent = sent
    yield instance
    instance.stop()


# ---------------------------------------------------------------- registro

def test_registry_query_summary_and_persistence():
    memory = MemoryModule()
    reg = ProposalRegistry(max_entries=2, store=memory, clock=iter([1.0, 2.0, 3.0]).__next__)
    a, b, c = act("es", "gnb_0", "PRB_QUOTA", 30, 65), act("x", "gnb_1", "TX_POWER", 10, 50), act("es", "gnb_0", "TX_POWER", 5, 65)
    reg.record(a, preg.LOST_ARBITRATION, "lower utility", winner=b)
    reg.record(b, preg.HYSTERESIS, "Control frequency exceeded", retry_after_ms=412.34)
    reg.record(c, preg.SAFETY, "out of bounds")
    assert [e["action_id"] for e in reg.query()] == [c.action_id, b.action_id]   # limitado a 2, mais recente primeiro
    assert reg.query(xapp_id="x")[0]["retry_after_ms"] == 412.3
    assert reg.query(since=2.5) == reg.query(reason=preg.SAFETY)
    summary = reg.summary()
    assert summary["total"] == 3 and summary["retained"] == 2                   # totais não esquecem o que saiu
    assert summary["by_xapp"]["es"] == {preg.LOST_ARBITRATION: 1, preg.SAFETY: 1}
    assert set(memory._rejections) == {a.action_id, b.action_id, c.action_id}
    with pytest.raises(ValueError):
        reg.record(a, "WHATEVER")


def test_guard_reason_classification():
    assert preg.classify_guard_reason("Control frequency exceeded for gnb_0_PRB_QUOTA") == preg.HYSTERESIS
    assert preg.classify_guard_reason("PRB_QUOTA above A1 policy limit (60)") == preg.SAFETY


# ---------------------------------------------------------------- janela e Safety Guard

def test_critical_quota_downgrades_excess_to_urgent():
    clock = types.SimpleNamespace(now=10.0)
    window = AdaptiveDecisionWindow(WindowConfig(critical_max_per_s=2), clock=lambda: clock.now)
    got = [window.classify_and_admit(act("em", "gnb_0", "PRB_QUOTA", 90, 98)) for _ in range(3)]
    assert got == [Urgency.CRITICAL, Urgency.CRITICAL, Urgency.URGENT] and window.downgraded_count == 1
    assert window.classify_and_admit(act("other", "gnb_0", "PRB_QUOTA", 90, 98)) == Urgency.CRITICAL  # cota por xApp
    clock.now = 11.0
    assert window.classify_and_admit(act("em", "gnb_0", "PRB_QUOTA", 90, 98)) == Urgency.CRITICAL


def test_ttl_defaults_defer_and_cap():
    window = AdaptiveDecisionWindow(WindowConfig(proposal_max_age_ms=1000, defer_default_ttl_ms=2000, defer_max_ttl_ms=3000))
    assert window.ttl_ms(act("a", "n", "PRB_QUOTA", 1, 1)) == 1000
    assert window.ttl_ms(act("a", "n", "PRB_QUOTA", 1, 1, defer_ok=True)) == 2000
    assert window.ttl_ms(act("a", "n", "PRB_QUOTA", 1, 1, defer_ok=True, ttl_ms=60000)) == 3000
    assert window.ttl_ms(act("a", "n", "PRB_QUOTA", 1, 1, defer_ok=True, ttl_ms=10)) == 1000
    old = act("a", "n", "PRB_QUOTA", 1, 1)
    assert window.remaining_ms(old, now=old.arrival_monotonic + 1.5) == pytest.approx(-500)


def test_parse_critical_targets():
    assert parse_critical_targets(["es:CELL_STATE", " *:HANDOVER ", ""]) == {("es", "CELL_STATE"), ("*", "HANDOVER")}
    with pytest.raises(ValueError):
        parse_critical_targets(["CELL_STATE"])


def test_critical_class_has_its_own_shorter_lockout():
    guard = Refinement(MemoryModule())
    normal = act("es", "gnb_0", "PRB_QUOTA", 40, 65)
    critical = act("em", "gnb_0", "PRB_QUOTA", 90, 98, urgency="CRITICAL")
    guard.commit_control_timestamps([normal], timestamp_ms=time.time() * 1000 - 200)   # controle há 200 ms
    assert not guard.validate_single_action(normal, record_timestamp=False)[0]
    assert guard.validate_single_action(critical, record_timestamp=False)[0]
    assert 700 < guard.remaining_lockout_ms(normal) <= 800 and guard.remaining_lockout_ms(critical) == 0
    guard.apply_policy(critical_control_interval_ms=500)
    assert not guard.validate_single_action(critical, record_timestamp=False)[0]


# ---------------------------------------------------------------- RDLxApp

def test_loser_is_registered_and_notified(app):
    winner, loser = act("xslice", "gnb_0", "PRB_QUOTA", 80, 90), act("es", "gnb_0", "PRB_QUOTA", 30, 65)
    app._process_action_group([winner, loser])
    entries = app._rejections_view()["entries"]
    assert [(e["action_id"], e["reason"], e["winner_xapp_id"]) for e in entries] == \
        [(loser.action_id, preg.LOST_ARBITRATION, "xslice")]
    (payload, mtype), = app.sent
    assert mtype == RDL_ACTION_RESULT
    assert payload["status"] == "REJECTED" and payload["xapp_id"] == "es" and payload["reason"] == preg.LOST_ARBITRATION
    assert payload["decision_id"] == entries[0]["decision_id"]


def test_safety_rejection_is_registered(app):
    rogue = act("rogue", "gnb_0", "TX_POWER", 45, 50)
    app._process_action_group([rogue])
    (entry,) = app._rejections_view(reason=preg.SAFETY)["entries"]
    assert entry["action_id"] == rogue.action_id and "out of bounds" in entry["detail"]


def test_hysteresis_rejection_gives_retry_after_and_defers_on_request(app):
    app._process_action_group([act("xslice", "gnb_0", "PRB_QUOTA", 80, 90)])
    plain = act("es", "gnb_0", "PRB_QUOTA", 60, 65)
    deferrable = act("es2", "gnb_0", "PRB_QUOTA", 60, 65, defer_ok=True, ttl_ms=3000)
    app._process_action_group([plain])
    app._process_action_group([deferrable])
    by_id = {e["action_id"]: e for e in app._rejections_view(reason=preg.HYSTERESIS)["entries"]}
    assert 0 < by_id[plain.action_id]["retry_after_ms"] <= 1000 and not by_id[plain.action_id]["deferred"]
    assert by_id[deferrable.action_id]["deferred"]
    assert [a for _, a in app.deferred] == [deferrable]
    assert app._rejections_view()["summary"]["deferred_pending"] == 1
    assert app._release_deferred(now=time.perf_counter()) == 0                   # bloqueio ainda vale
    assert app._release_deferred(now=time.perf_counter() + 2.0) == 1             # volta para a janela
    assert app.proposal_buffer == [deferrable] and app.deferred == []


def test_stale_proposals_are_dropped_before_decision(app):
    fresh = act("xslice", "gnb_0", "PRB_QUOTA", 80, 90)
    old = act("es", "gnb_1", "PRB_QUOTA", 30, 60)
    old.arrival_monotonic -= 5.0
    for a in (old, fresh):
        app.inject_xapp_action(a)
    app.buffer_deadline_ms = 0
    critical, batch = app._take_ready_actions()
    assert critical == [] and batch == [fresh]
    (entry,) = app._rejections_view(reason=preg.STALE)["entries"]
    assert entry["action_id"] == old.action_id


def test_overflow_is_registered(app):
    app.MAX_PROPOSALS = 0
    with pytest.raises(OverflowError):
        app.inject_xapp_action(act("es", "gnb_0", "PRB_QUOTA", 30, 60))
    assert app._rejections_view()["entries"][0]["reason"] == preg.OVERFLOW


def test_fast_path_is_audited(app):
    from src.observability.causal_tracker import causal_tracker
    critical = act("em", "gnb_0", "PRB_QUOTA", 90, 98)
    app.inject_xapp_action(critical)
    group, _ = app._take_ready_actions()
    assert critical.urgency == "CRITICAL"
    app._process_action_group(group, fast_path=True)
    assert [critical.action_id] in causal_tracker.fast_path_decisions.values()


def test_a1_policy_marks_critical_targets_and_interval(app):
    es_sleep = act("es", "gnb_0", "CELL_STATE", 0, 60)
    assert app.decision_window.classify(es_sleep) == Urgency.NORMAL
    ok, _ = app.a1_policies.put_policy("20000", "crit", {"critical_targets": ["es:CELL_STATE"],
                                                         "critical_control_interval_ms": 50})
    assert ok and app.decision_window.classify(es_sleep) == Urgency.CRITICAL
    assert app.refinement.config["critical_control_interval_ms"] == 50
    app.a1_policies.delete_policy("20000", "crit")
    assert app.decision_window.classify(es_sleep) == Urgency.NORMAL
    assert app.refinement.config["critical_control_interval_ms"] == 100


def test_a1_rejects_malformed_critical_targets():
    manager = A1PolicyManager()
    assert not manager.put_policy("20000", "x", {"critical_targets": ["CELL_STATE"]})[0]
    assert not manager.put_policy("20000", "x", {"critical_targets": "es:CELL_STATE"})[0]
    assert not manager.put_policy("20000", "x", {"critical_control_interval_ms": 5})[0]


def test_proposal_handler_reads_defer_fields(app):
    captured = []
    app._enqueue = lambda a: captured.append(a)
    app.oran_strict = False
    msg = {"xapp_id": "es", "node_id": "gnb_0", "parameter": "PRB_QUOTA", "value": 40, "priority": 60,
           "defer_ok": True, "ttl_ms": 2500}
    app._action_proposal_handler(None, {"payload": json.dumps(msg).encode()}, None)
    assert captured[0].defer_ok and captured[0].ttl_ms == 2500
    app._action_proposal_handler(None, {"payload": json.dumps({**msg, "ttl_ms": -1}).encode()}, None)
    assert len(captured) == 1


def test_rejections_http_endpoint(app):
    from fastapi.testclient import TestClient
    app._process_action_group([act("xslice", "gnb_0", "PRB_QUOTA", 80, 90), act("es", "gnb_0", "PRB_QUOTA", 30, 65)])
    body = TestClient(app.health.app).get("/rejections", params={"xapp_id": "es"}).json()
    assert body["summary"]["by_reason"] == {preg.LOST_ARBITRATION: 1}
    assert [e["xapp_id"] for e in body["entries"]] == ["es"]
