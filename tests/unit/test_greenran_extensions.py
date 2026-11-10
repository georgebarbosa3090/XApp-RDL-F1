"""Grafo de conhecimento, janela adaptativa/caminho crítico, A1 via RMR e achado 53."""
import json

import pytest

from src.conflict_types import ConflictEvent, ConflictSeverity, ConflictType, XAppAction
from src.core.decision_window import AdaptiveDecisionWindow, Urgency, WindowConfig
from src.core.knowledge_graph import KnowledgeGraph
from src.interfaces.a1_policy_receiver import A1PolicyManager
from src.interfaces.a1_rmr import (A1_POLICY_QUERY, A1_POLICY_RESPONSE, handle_policy_request,
                                   policy_type_definitions, query_messages)


def act(xapp, node, param, value, prio, ts=None, aid=None):
    a = XAppAction(xapp_id=xapp, node_id=node, parameter=param, value=float(value), priority=prio)
    if ts is not None:
        a.timestamp = ts
    if aid:
        a.action_id = aid
    return a


# ---------------------------------------------------------------- grafo de conhecimento

def test_knowledge_graph_topology_parameters_and_history():
    kg = KnowledgeGraph()
    kg.add_neighbors("gnb_0", "gnb_1")
    kg.add_parameter("PRB_QUOTA", ["DRB.UEThpDl", "RRU.PrbUsedDl"])
    kg.add_parameter("CELL_STATE", ["DRB.UEThpDl", "L1M.DL-sinr"])
    assert kg.neighbors("gnb_1") == {"gnb_0"}
    assert kg.shared_kpis("PRB_QUOTA", "CELL_STATE") == {"DRB.UEThpDl"}

    a, b = act("xslice", "gnb_0", "PRB_QUOTA", 80, 90), act("es", "gnb_0", "PRB_QUOTA", 30, 65)
    conflict = ConflictEvent(ConflictType.DIRECT, ConflictSeverity.HIGH, [a, b])
    kg.record_conflict(conflict)
    kg.record_decision("d1", "TVS", [a], [conflict.conflict_id], policy={"energy_weight": 0.3})
    assert kg.conflicts_on("gnb_0", "PRB_QUOTA") == [f"conflict:{conflict.conflict_id}"]
    assert kg.successors(f"conflict:{conflict.conflict_id}", "RESOLVED_BY") == ["decision:d1"]
    features = kg.context_features("gnb_0", "PRB_QUOTA")
    assert features["neighbor_count"] == 1 and features["recent_conflicts"] == 1
    assert features["recent_decisions"] == 1 and features["distinct_xapps_on_cell"] == 2
    doc = json.loads(kg.to_json())
    assert doc["schema"] == "xapp-rdl/knowledge-graph/v1" and any(e["relation"] == "GOVERNS" for e in doc["edges"])


def test_knowledge_graph_evicts_old_events_with_their_edges():
    kg = KnowledgeGraph(max_events=4)
    for i in range(10):
        kg.record_action(act("x", "gnb_0", "PRB_QUOTA", i, 50, aid=f"a{i}"))
    assert kg.stats()["action"] == 4
    assert len(kg.predecessors("gnb_0", "TARGETS")) == 4      # arestas dos eventos removidos também saem


# ---------------------------------------------------------------- janela adaptativa

def test_urgency_classes_and_critical_targets():
    w = AdaptiveDecisionWindow(WindowConfig(critical_targets={("*", "CELL_STATE")}))
    assert w.classify(act("x", "g", "PRB_QUOTA", 1, 96)) == Urgency.CRITICAL
    assert w.classify(act("x", "g", "CELL_STATE", 1, 10)) == Urgency.CRITICAL
    assert w.classify(act("x", "g", "PRB_QUOTA", 1, 85)) == Urgency.URGENT
    assert w.classify(act("x", "g", "PRB_QUOTA", 1, 50)) == Urgency.NORMAL
    assert w.deadline_ms(Urgency.CRITICAL) == 0.0


def test_adaptive_window_follows_arrival_rate_within_bounds():
    t = [0.0]
    w = AdaptiveDecisionWindow(WindowConfig(min_window_ms=50, max_window_ms=500, target_proposals=8), clock=lambda: t[0])
    for _ in range(300):                     # 100 propostas/s por 3 s (meia-vida da média: 1 s)
        t[0] += 0.01
        w.observe_arrival()
    assert 50 <= w.window_ms() <= 120
    for _ in range(20):                      # 2 propostas/s: limitado ao máximo
        t[0] += 0.5
        w.observe_arrival()
    assert w.window_ms() == 500
    t[0] += 60                               # sem chegadas recentes: janela base
    assert w.window_ms() == 200
    assert AdaptiveDecisionWindow(WindowConfig(adaptive=False)).window_ms() == 200


# ---------------------------------------------------------------- A1 via RMR

def test_a1_rmr_create_update_delete_and_errors():
    mgr = A1PolicyManager()
    seen = []
    mgr.add_listener(seen.append)
    msg = {"operation": "CREATE", "policy_type_id": 20001, "policy_instance_id": "g", "payload": {"energy_weight": 0.4}}
    resp, ok = handle_policy_request(mgr, json.dumps(msg).encode(), "rdl")
    assert ok and resp == {"policy_type_id": 20001, "policy_instance_id": "g", "handler_id": "rdl", "status": "OK"}
    assert seen[-1] == {"energy_weight": 0.4}
    bad = dict(msg, payload={"energy_weight": 2.0})
    resp, ok = handle_policy_request(mgr, json.dumps(bad).encode(), "rdl")
    assert not ok and resp["status"] == "ERROR"
    resp, ok = handle_policy_request(mgr, json.dumps(dict(msg, operation="DELETE")).encode(), "rdl")
    assert ok and resp["status"] == "DELETED" and seen[-1] == {}
    resp, ok = handle_policy_request(mgr, b"{not json", "rdl")
    assert not ok and resp["status"] == "ERROR"


def test_a1_rmr_query_and_type_definitions_include_cardl_type():
    mgr = A1PolicyManager()
    assert [json.loads(m) for m in query_messages(list(mgr.policy_types))] == [
        {"policy_type_id": 20000}, {"policy_type_id": 20001}, {"policy_type_id": 20002}]
    defs = {d["policy_type_id"]: d for d in policy_type_definitions(mgr)}
    assert set(defs) == {20000, 20001, 20002}
    assert defs[20002]["create_schema"]["properties"]["marl_enabled"] == {"type": "boolean"}
    assert all(d["create_schema"]["additionalProperties"] is False for d in defs.values())


# ---------------------------------------------------------------- RDLxApp

@pytest.fixture
def app(monkeypatch, tmp_path):
    topo = tmp_path / "topo.json"
    topo.write_text(json.dumps({"neighbors": {"gnb_0": ["gnb_1"]}}), encoding="utf-8")
    monkeypatch.setenv("RDL_TOPOLOGY_FILE", str(topo))
    from src.rdl_xapp import RDLxApp
    instance = RDLxApp()
    yield instance
    instance.stop()


def test_a1_policy_request_handler_applies_and_answers(app):
    sent = []
    app.xapp.rmr_send = lambda payload, mtype, *a, **k: sent.append((json.loads(payload), mtype)) or True
    msg = {"operation": "CREATE", "policy_type_id": 20000, "policy_instance_id": "gov", "payload": {"max_cell_prb_limit": 60}}
    app._a1_policy_request_handler(app.xapp, {"payload": json.dumps(msg).encode()}, None)
    assert app.refinement.policy_max_prb_quota == 60
    assert sent == [({"policy_type_id": 20000, "policy_instance_id": "gov", "handler_id": "iqos-xapp-rdl", "status": "OK"},
                     A1_POLICY_RESPONSE)]
    sent.clear()
    app._query_a1_policies()
    assert {m for _, m in sent} == {A1_POLICY_QUERY} and len(sent) == 3


def test_handover_to_cell_outside_topology_is_rejected(app):
    assert app.refinement.check_bounds(act("ts", "gnb_0", "HANDOVER", 1, 80))[0]
    ok, reason = app.refinement.check_bounds(act("rogue", "gnb_0", "HANDOVER", 7, 95))
    assert not ok and "topology" in reason


def test_critical_action_takes_related_pending_proposals_with_it(app):
    normal_same = act("es", "gnb_0", "PRB_QUOTA", 30, 65)
    normal_neighbor = act("es", "gnb_1", "CELL_STATE", 0, 60)
    normal_far = act("x", "gnb_9", "PRB_QUOTA", 50, 50)
    for a in (normal_same, normal_neighbor, normal_far):
        app.inject_xapp_action(a)
    critical = act("emergency", "gnb_0", "PRB_QUOTA", 90, 98)
    app.inject_xapp_action(critical)
    group, batch = app._take_ready_actions()
    assert group == [critical, normal_same, normal_neighbor]
    assert app.proposal_buffer == [normal_far] and batch == []


def test_decisions_are_recorded_in_knowledge_graph(app):
    app.dispatcher.dispatch_control = lambda decision, **_: "req"
    app._process_action_group([act("xslice", "gnb_0", "PRB_QUOTA", 80, 90), act("es", "gnb_0", "PRB_QUOTA", 30, 65)])
    stats = app.knowledge_graph.stats()
    assert stats.get("conflict") == 1 and stats.get("decision") == 1
    assert app.health.knowledge_graph_provider(False)["decision"] == 1


def test_incumbent_keeps_opposing_after_rejected_resolution(app, monkeypatch):
    """Achado 53: resolução indireta rejeitada pela histerese não pode tirar a incumbente de cena."""
    import types
    import src.core.perception as perception_module
    import src.core.refinement as refinement_module
    clock = types.SimpleNamespace(now=15.2)
    monkeypatch.setattr(refinement_module, "time", types.SimpleNamespace(time=lambda: clock.now))
    monkeypatch.setattr(perception_module, "time", types.SimpleNamespace(time=lambda: clock.now))
    sent = []

    def dispatch(decision, **_):
        a = decision.selected_actions[0]
        sent.append(a.xapp_id)
        app.perception.commit_actions([a])
        return "req"

    app.dispatcher.dispatch_control = dispatch
    t1 = 76 * 0.2                                   # 15.200000000000001, como no harness nativo
    app._process_action_group([act("es0", "gnb_0", "CELL_STATE", 0, 65, ts=t1), act("es1", "gnb_1", "CELL_STATE", 0, 60, ts=t1),
                               act("ts", "gnb_0", "HANDOVER", 1, 80, ts=t1)])
    assert sorted(sent) == ["es0", "ts"]
    clock.now = 81 * 0.2                            # 16.2: menos de 1000 ms depois (ponto flutuante)
    sent.clear()
    app._process_action_group([act("es0", "gnb_0", "CELL_STATE", 0, 65, ts=clock.now),
                               act("es1", "gnb_1", "CELL_STATE", 0, 60, ts=clock.now)])
    assert "es1" not in sent                        # a RU 1 continua protegida pelo handover confirmado
