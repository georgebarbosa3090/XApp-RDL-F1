"""Governança hierárquica (doc 11): registro e modos (nível 1), interceptação por rota (nível 2),
conflito implícito (nível 3), relatório e rApp de governança (nível 4)."""
import json
import time
import types

import pytest

from src.conflict_types import ConflictType, XAppAction
from src.core import proposal_registry as preg
from src.core.implicit_conflict import ImplicitConflictDetector
from src.e2.e2ap.constants import RIC_CONTROL_ACK, RIC_CONTROL_FAILURE
from src.e2.rc_encoder import RCEncoder
from src.e2.v3 import codec as v3
from src.governance import interception as icpt
from src.governance.xapp_registry import MANAGED, ON_DEMAND, QUARANTINED, XAppEntry, XAppRegistry, parse_pairs
from src.interfaces.a1_policy_receiver import A1PolicyManager

REGISTRY = {"xapps": {
    "xslice": {"sources": ["^ricxapp-xslice-"], "max_priority": 90},
    "energy_saving": {"sources": ["^ricxapp-es-"], "mode": "ON_DEMAND", "max_priority": 70},
    "third_ts": {"intercept_requestor_ids": [1010], "default_priority": 75},
}}


def act(xapp, node, param, value, prio, **kw):
    return XAppAction(xapp_id=xapp, node_id=node, parameter=param, value=float(value), priority=prio, **kw)


def rdl_control(requestor, parameter, value, instance=1, ran_function=3):
    header, message = RCEncoder().encode_control_pdu("gnb", parameter, value)
    return v3.encode_ric_control_request(requestor, instance, ran_function, header, message)


# ---------------------------------------------------------------- nível 1: registro

def test_registry_authorization_strict_and_lenient():
    reg = XAppRegistry.from_dict(REGISTRY)
    assert reg.authorize("xslice", "ricxapp-xslice-7f9:4560", strict=True) == (True, "registered")
    assert not reg.authorize("xslice", "ricxapp-rogue-1:4560", strict=True)[0]       # origem forjada
    assert not reg.authorize("xslice", None, strict=True)[0]
    assert not reg.authorize("ghost", "anything:4560", strict=True)[0]                 # não registrada
    assert reg.authorize("ghost", None, strict=False)[0]                               # bancada local
    assert not reg.authorize("xslice", "ricxapp-rogue-1:4560", strict=False)[0]        # origem conhecida não confere
    assert reg.mode("energy_saving") == ON_DEMAND and reg.mode("ghost") == MANAGED
    assert reg.priority_cap("energy_saving") == 70 and reg.priority_cap("ghost") == 100
    assert reg.by_requestor(1010).xapp_id == "third_ts" and reg.by_requestor(1) is None


def test_registry_a1_overrides_and_validation():
    reg = XAppRegistry.from_dict(REGISTRY)
    reg.apply_policy(modes={"xslice": QUARANTINED, "newcomer": ON_DEMAND}, caps={"energy_saving": 50})
    assert not reg.authorize("xslice", "ricxapp-xslice-1:4560", strict=True)[0]
    assert reg.priority_cap("energy_saving") == 50 and reg.mode("newcomer") == ON_DEMAND
    snap = reg.snapshot()
    assert snap["xapps"]["xslice"]["effective_mode"] == QUARANTINED
    assert snap["xapps"]["newcomer"]["registered"] is False
    reg.apply_policy()                                                                  # política removida
    assert reg.mode("xslice") == MANAGED
    with pytest.raises(ValueError):
        reg.apply_policy(modes={"x": "SOMETIMES"})
    with pytest.raises(ValueError):
        XAppEntry("bad", mode="LOUD")
    with pytest.raises(ValueError):
        XAppRegistry([XAppEntry("a", intercept_requestor_ids=[1]), XAppEntry("b", intercept_requestor_ids=[1])])
    with pytest.raises(ValueError):
        parse_pairs(["semdoispontos"])


def test_registry_from_env(tmp_path, monkeypatch):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(REGISTRY), encoding="utf-8")
    monkeypatch.setenv("RDL_XAPP_REGISTRY", str(path))
    assert XAppRegistry.from_env().configured
    monkeypatch.delenv("RDL_XAPP_REGISTRY")
    assert not XAppRegistry.from_env().configured


def test_a1_schema_for_governance_fields():
    m = A1PolicyManager()
    assert m.put_policy("20000", "gov", {"xapp_modes": ["rogue:QUARANTINED"], "xapp_priority_caps": ["es:60"]})[0]
    assert not m.put_policy("20000", "gov", {"xapp_modes": ["rogue:LOUD"]})[0]
    assert not m.put_policy("20000", "gov", {"xapp_priority_caps": ["es:101"]})[0]


# ---------------------------------------------------------------- nível 2: codec da interceptação

def test_intercepted_rdl_profile_control_and_responses():
    ctl = icpt.decode_intercepted_control(rdl_control(1010, "TX_POWER", 20.5, instance=4))
    assert (ctl.requestor_id, ctl.instance_id, ctl.parameter, ctl.value) == (1010, 4, "TX_POWER", 20.5)
    ack = v3.parse_ric_control_outcome(icpt.build_control_ack(1010, 4, 3))
    assert ack["outcome"] == "ACK" and (ack["ric_requestor_id"], ack["ric_instance_id"]) == (1010, 4)
    failure = icpt.build_control_failure(1010, 4, 3)
    assert v3.parse_ric_control_outcome(failure)["outcome"] == "FAILURE"
    assert icpt.cause_of(failure) == icpt.CAUSE_CONTROL_FAILED_TO_EXECUTE
    assert icpt.cause_of(icpt.build_control_ack(1, 1, 1)) is None


def test_intercepted_nori_slice_quota_control():
    codec = icpt._nori_codec()
    if codec is None:
        pytest.skip("ASN.1 do NORI fora do cache local")
    msg = codec.rc_slice_quota_message([v3.SlicePrbQuota(2, 25), v3.SlicePrbQuota(1, 75)])
    ctl = icpt.decode_intercepted_control(v3.encode_ric_control_request(1010, 1, 300, codec.rc_slice_quota_header(), msg))
    assert (ctl.parameter, ctl.value, ctl.encoding) == ("PRB_QUOTA", 75.0, "E2SM-RC-v03.01-slice-quota")


def test_interception_rejects_what_it_cannot_read():
    with pytest.raises(icpt.InterceptionError):
        icpt.decode_intercepted_control(b"\x00garbage")
    with pytest.raises(icpt.InterceptionError):
        icpt.decode_intercepted_control(icpt.build_control_ack(1, 1, 1))              # não é Request
    with pytest.raises(icpt.InterceptionError):
        icpt.decode_intercepted_control(v3.encode_ric_control_request(1, 1, 1, b"h", b"not-rc"))


# ---------------------------------------------------------------- nível 3: detector

def test_implicit_detector_needs_grace_and_persistence():
    committed = {}
    clock = types.SimpleNamespace(now=100.0)
    det = ImplicitConflictDetector(lambda n, p: committed.get((n, p)), grace_s=2.0, persistence=3,
                                   clock=lambda: clock.now)
    sleep = act("es", "gnb_1", "CELL_STATE", 0, 65)
    sleep.t_ack = 99.5
    committed[("gnb_1", "CELL_STATE")] = sleep
    assert det.observe("gnb_1", {"drb_thp_dl": 12.0}) == []                     # ainda no período de graça
    clock.now = 103.0
    assert det.observe("gnb_1", {"drb_thp_dl": 12.0}) == []
    assert det.observe("gnb_1", {"drb_thp_dl": 12.0}) == []
    (finding, action), = det.observe("gnb_1", {"drb_thp_dl": 12.0})              # 3 seguidas
    assert finding.parameter == "CELL_STATE" and action is sleep and "12.00 Mb/s" in finding.detail
    assert det.observe("gnb_1", {"drb_thp_dl": 12.0}) == []                     # um achado por episódio
    assert det.observe("gnb_1", {"drb_thp_dl": 0.0}) == []                      # coerente: episódio fecha
    quota = act("xslice", "gnb_2", "PRB_QUOTA", 60, 90)
    quota.t_ack = 50.0
    committed[("gnb_2", "PRB_QUOTA")] = quota
    for _ in range(2):
        assert det.observe("gnb_2", {"sst1_prb_share_pct": 85.0}) == []
    (finding, _), = det.observe("gnb_2", {"sst1_prb_share_pct": 85.0})
    assert finding.to_conflict(quota).conflict_type == ConflictType.IMPLICIT
    assert det.observe("gnb_3", {"drb_thp_dl": 50.0}) == []                     # sem ação confirmada


# ---------------------------------------------------------------- RDLxApp

class FakeRmr:
    def __init__(self):
        self.rts = []
        self.freed = []

    def rmr_rts(self, sbuf, new_payload=None, new_mtype=None, retries=100):
        self.rts.append((new_mtype, new_payload))
        return True

    def rmr_free(self, sbuf):
        self.freed.append(sbuf)


@pytest.fixture
def app(monkeypatch, tmp_path):
    reg = tmp_path / "registry.json"
    reg.write_text(json.dumps(REGISTRY), encoding="utf-8")
    topo = tmp_path / "topo.json"
    topo.write_text(json.dumps({"neighbors": {"gnb_0": ["gnb_1"]}}), encoding="utf-8")
    monkeypatch.setenv("RDL_XAPP_REGISTRY", str(reg))
    monkeypatch.setenv("RDL_TOPOLOGY_FILE", str(topo))
    from src.rdl_xapp import RDLxApp
    instance = RDLxApp()
    instance.dispatched = []

    def dispatch(decision, **_):
        a = decision.selected_actions[0]
        instance.dispatched.append(a)
        return f"req-{a.action_id[:6]}"
    instance.dispatcher.dispatch_control = dispatch
    yield instance
    instance.stop()


def test_adaptive_window_is_on_by_default(app):
    assert app.decision_window.config.adaptive is True


def test_strict_mode_accepts_registered_source_only(app):
    queued = []
    app._enqueue = lambda a: queued.append(a)
    app.oran_strict = True
    msg = {"xapp_id": "xslice", "node_id": "gnb_0", "parameter": "PRB_QUOTA", "value": 80, "priority": 90}
    app._action_proposal_handler(None, {"payload": json.dumps(msg).encode(), "message source": "ricxapp-xslice-1:4560"}, None)
    app._action_proposal_handler(None, {"payload": json.dumps(msg).encode(), "message source": "evil-0:4560"}, None)
    assert [a.xapp_id for a in queued] == ["xslice"]
    assert app._rejections_view(reason=preg.UNAUTHORIZED)["entries"][0]["xapp_id"] == "xslice"
    app.xapp_registry = XAppRegistry()                                     # estrito sem registro: descarta
    app._action_proposal_handler(None, {"payload": json.dumps(msg).encode(), "message source": "ricxapp-xslice-1:4560"}, None)
    assert len(queued) == 1


def test_quarantine_and_priority_cap_from_a1(app):
    assert app.a1_policies.put_policy("20000", "gov", {"xapp_modes": ["rogue:QUARANTINED"],
                                                       "xapp_priority_caps": ["xslice:60"]})[0]
    assert app._enqueue(act("rogue", "gnb_0", "TX_POWER", 10, 50)) is None
    assert app._rejections_view(reason=preg.UNAUTHORIZED)["entries"][0]["xapp_id"] == "rogue"
    capped = act("xslice", "gnb_0", "PRB_QUOTA", 80, 98)                    # seria CRITICAL
    app._enqueue(capped)
    assert capped.priority == 60 and capped.requested_priority == 98 and capped.urgency != "CRITICAL"


def test_on_demand_xapp_is_decided_alone_until_there_is_contention(app):
    lone = act("energy_saving", "gnb_0", "TX_POWER", 20, 60)
    app._enqueue(lone)
    assert app.on_demand_queue == [lone] and app.proposal_buffer == []
    (taken,) = app._take_on_demand()
    app._process_action_group([taken], on_demand=True)
    assert app.dispatched == [lone]
    app._enqueue(act("xslice", "gnb_1", "PRB_QUOTA", 80, 90))              # outra xApp no vizinho
    contended = act("energy_saving", "gnb_0", "PRB_QUOTA", 30, 60)
    app._enqueue(contended)
    assert contended in app.proposal_buffer and app.on_demand_queue == []  # volta à janela


def test_stale_on_demand_proposal_is_dropped(app):
    old = act("energy_saving", "gnb_5", "TX_POWER", 20, 60)
    old.arrival_monotonic -= 10
    app._enqueue(old)
    assert app._take_on_demand() == []
    assert app._rejections_view(reason=preg.STALE)["entries"][0]["action_id"] == old.action_id


def test_intercepted_control_wins_and_gets_ack(app):
    rmr = FakeRmr()
    app._intercepted_control_handler(rmr, {"payload": rdl_control(1010, "PRB_QUOTA", 70, instance=9), "meid": "gnb_0"}, "sbuf1")
    (action,) = app.proposal_buffer
    assert (action.xapp_id, action.priority, action.intercepted) == ("third_ts", 75, True)
    app._process_action_group(list(app.proposal_buffer))
    assert app.dispatched == [action] and rmr.rts == []                    # espera o ACK do nó
    app.dispatcher.handle_ack = lambda payload, node_id=None: {"action_id": action.action_id}
    app._control_ack_handler(None, {"payload": b"ack", "meid": "gnb_0"}, None)
    (mtype, pdu), = rmr.rts
    out = v3.parse_ric_control_outcome(pdu)
    assert mtype == RIC_CONTROL_ACK and (out["ric_requestor_id"], out["ric_instance_id"]) == (1010, 9)
    assert rmr.freed == ["sbuf1"] and app._intercepts == {}


def test_intercepted_control_that_loses_gets_failure(app):
    rmr = FakeRmr()
    app._intercepted_control_handler(rmr, {"payload": rdl_control(1010, "PRB_QUOTA", 30), "meid": "gnb_0"}, "sbuf2")
    app.proposal_buffer.append(act("xslice", "gnb_0", "PRB_QUOTA", 80, 90))
    app._process_action_group(list(app.proposal_buffer))
    (mtype, pdu), = rmr.rts
    assert mtype == RIC_CONTROL_FAILURE and icpt.cause_of(pdu) == icpt.CAUSE_CONTROL_FAILED_TO_EXECUTE
    entry = app._rejections_view(xapp_id="third_ts")["entries"][0]
    assert entry["reason"] == preg.LOST_ARBITRATION and entry["winner_xapp_id"] == "xslice"


def test_intercepted_control_unknown_requestor_or_garbage(app):
    rmr = FakeRmr()
    app._intercepted_control_handler(rmr, {"payload": rdl_control(4242, "PRB_QUOTA", 30), "meid": "gnb_0"}, "s3")
    assert rmr.rts[0][0] == RIC_CONTROL_FAILURE and app.proposal_buffer == []
    assert app._rejections_view(reason=preg.UNAUTHORIZED)["entries"][0]["xapp_id"] == "requestor:4242"
    app._intercepted_control_handler(rmr, {"payload": b"\x00junk", "meid": "gnb_0"}, "s4")
    assert "s4" in rmr.freed


def test_stuck_intercept_expires_with_failure(app):
    rmr = FakeRmr()
    app._intercepted_control_handler(rmr, {"payload": rdl_control(1010, "PRB_QUOTA", 70), "meid": "gnb_0"}, "s5")
    aid = next(iter(app._intercepts))
    xi, sb, ctl, _ = app._intercepts[aid]
    app._intercepts[aid] = (xi, sb, ctl, time.time() - 60)
    assert app._expire_intercepts() == 1
    assert icpt.cause_of(rmr.rts[0][1]) == icpt.CAUSE_UNSPECIFIED


def test_implicit_conflict_reaches_graph_and_governance_report(app):
    sleep = act("energy_saving", "gnb_1", "CELL_STATE", 0, 65)
    sleep.t_ack = time.time() - 10
    app.perception.commit_actions([sleep])
    app._intercept_history["gnb_1"] = {"third_ts": time.time()}
    app.implicit.persistence = 1
    (record,) = app.observe_kpm_metrics("gnb_1", {"drb_thp_dl": 8.0, "prb_used_dl": 40})
    assert record["suspects"] == ["third_ts"]
    assert app.knowledge_graph.stats().get("conflict") == 1
    report = app._governance_view()
    assert report["implicit_conflicts"][0]["conflict_id"] == record["conflict_id"]
    assert report["xapps"]["xapps"]["energy_saving"]["effective_mode"] == ON_DEMAND
    assert report["window"]["adaptive"] is True


def test_governance_and_decisions_endpoints(app):
    from fastapi.testclient import TestClient
    client = TestClient(app.health.app)
    app._process_action_group([act("xslice", "gnb_0", "PRB_QUOTA", 80, 90), act("es", "gnb_0", "PRB_QUOTA", 30, 65)])
    body = client.get("/decisions", params={"node": "gnb_0"}).json()
    assert [e["xapp_id"] for e in body["entries"]] == ["es"]
    assert client.get("/decisions", params={"node": "gnb_9"}).json()["entries"] == []
    assert "implicit_conflicts" in client.get("/governance").json()


# ---------------------------------------------------------------- nível 4: rApp de governança

def test_governance_rapp_decisions():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("governance_rapp", Path(__file__).resolve().parents[2] / "rapps" / "governance_rapp.py")
    rapp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rapp)
    report = {
        "rejections": {"by_xapp": {"rogue": {"SAFETY": 7}, "spoofer": {"UNAUTHORIZED": 25}, "xslice": {"LOST_ARBITRATION": 40}}},
        "critical_downgrades_by_xapp": {"pushy": 12, "rogue": 30},
        "implicit_conflicts": [
            {"node_id": "gnb_1", "parameter": "CELL_STATE", "detail": "x", "suspects": ["third_ts"]},
            {"node_id": "gnb_2", "parameter": "PRB_QUOTA", "detail": "y", "suspects": ["out-of-band"]},
            {"node_id": "gnb_3", "parameter": "PRB_QUOTA", "detail": "z", "suspects": ["requestor:4242"]},
        ],
        "xapps": {"xapps": {"third_ts": {}, "xslice": {}}},
    }
    d = rapp.decide(report)
    assert d["modes"] == {"rogue": "QUARANTINED", "spoofer": "QUARANTINED", "third_ts": "QUARANTINED"}
    assert d["caps"] == {"pushy": 94}                                       # rogue já em quarentena
    assert "xslice" not in d["modes"]                                      # perder arbitragem não é falta
    assert {r["action"] for r in d["recommendations"]} == {"UNDEPLOY_CANDIDATE", "INVESTIGATE_OUT_OF_BAND", "UNDEPLOY"}
    body = rapp.policy_body("ric1", "svc", "rdl-governance", d["policy_data"])
    assert body["policytype_id"] == "20000"
    assert A1PolicyManager().put_policy("20000", "gov", body["policy_data"])[0]   # o A1 da RDL aceita
    again = rapp.decide({"rejections": {"by_xapp": {}}}, previous=d)
    assert again["modes"] == d["modes"]                                    # quarentena não expira sozinha
