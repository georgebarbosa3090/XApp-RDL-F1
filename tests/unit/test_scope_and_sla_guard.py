"""Doc 18, Parte A: campos scope/slice_sst/ratio_kind (§4.1), modelo de efeito (§4.2–4.3), guarda de SLA
e motivo SLA_PROTECTION (§4.4)."""
import importlib.util
import json
import types
from pathlib import Path

import pytest

from src.conflict_types import XAppAction, validate_scope_fields
from src.core import proposal_registry as preg
from src.core.effect_model import (DEFAULT_CURVE, EXPECTED_SHA256, SliceEffectModel, build_effect_model,
                                   load_curve, parse_sla_slices, sla_guard)
from src.core.reasoning import Reasoning
from src.e2.backends.testbed_profiles import NS3_NATIVE, apply_scope_defaults, scope_defaults
from src.e2.e2ap.constants import RDL_ACTION_RESULT
from src.e2.v3.codec import CodecError, SlicePrbQuota, quotas_for_proposal

ROOT = Path(__file__).resolve().parents[2]


class _Mem:
    def get_similar_resolutions(self, conflict):
        return []


def quota(xapp, value, prio, **kw):
    kw = {"scope": "slice", "slice_sst": 1, "ratio_kind": "max", "action_id": f"{xapp}-{value}", **kw}
    return XAppAction(xapp_id=xapp, node_id="gnb_0", parameter="PRB_QUOTA", value=float(value), priority=prio, **kw)


def s8():
    """S8 do NORI: xSlice (teto eMBB 25 %, prio. 90) contra eMBB (teto 80 %, prio. 60)."""
    return quota("xapp-qos-xslice", 25, 90), quota("xapp-embb-throughput", 80, 60)


@pytest.fixture
def model():
    return build_effect_model({"effect_model": "curve"})


# ---------------------------------------------------------------- §4.1 esquema

@pytest.mark.parametrize("fields", [
    {}, {"scope": "cell"}, {"scope": "slice"}, {"scope": "slice", "slice_sst": 1, "ratio_kind": "max"},
    {"slice_sst": 2}, {"ratio_kind": "dedicated"}, {"scope": "slice", "slice_sst": 255, "ratio_kind": "min"},
])
def test_valid_scope_fields(fields):
    a = XAppAction(xapp_id="x", node_id="gnb_0", parameter="PRB_QUOTA", value=30.0, priority=50, **fields)
    assert (a.scope, a.slice_sst, a.ratio_kind) == (fields.get("scope"), fields.get("slice_sst"), fields.get("ratio_kind"))


@pytest.mark.parametrize("parameter,fields", [
    ("PRB_QUOTA", {"scope": "cluster"}),
    ("PRB_QUOTA", {"scope": "cell", "slice_sst": 1}),
    ("PRB_QUOTA", {"scope": "cell", "ratio_kind": "max"}),
    ("PRB_QUOTA", {"slice_sst": 256}),
    ("PRB_QUOTA", {"slice_sst": True}),
    ("PRB_QUOTA", {"slice_sst": 1.0}),
    ("PRB_QUOTA", {"ratio_kind": "avg"}),
    ("TX_POWER", {"scope": "slice"}),
    ("TX_POWER", {"slice_sst": 1}),
])
def test_invalid_scope_fields(parameter, fields):
    with pytest.raises(ValueError):
        XAppAction(xapp_id="x", node_id="gnb_0", parameter=parameter, value=30.0, priority=50, **fields)
    with pytest.raises(ValueError):
        validate_scope_fields(parameter, fields.get("scope"), fields.get("slice_sst"), fields.get("ratio_kind"))


def test_cell_scope_is_valid_for_any_parameter():
    XAppAction(xapp_id="x", node_id="gnb_0", parameter="TX_POWER", value=30.0, priority=50, scope="cell")


def test_backend_scope_defaults():
    assert scope_defaults(NS3_NATIVE) == {"scope": "cell"}
    assert scope_defaults("NORI_NS3") == {"scope": "slice", "slice_sst": 1, "ratio_kind": "max", "complement_sst": 2}
    assert scope_defaults("SRSRAN_PROJECT") == {} and scope_defaults("OAI_FLEXRIC") == {}   # A_CONFIRMAR (TB0)
    assert scope_defaults("") == {} and scope_defaults(None) == {}
    with pytest.raises(ValueError):
        scope_defaults({"backend": "X", "proposal_scope": {"scope": "cell", "slice_sst": 1}})


def test_apply_scope_defaults_fills_only_what_is_missing():
    nori, native = scope_defaults("NORI_NS3"), scope_defaults(NS3_NATIVE)
    a = apply_scope_defaults(XAppAction(xapp_id="x", node_id="g", parameter="PRB_QUOTA", value=25.0, priority=90), nori)
    assert (a.scope, a.slice_sst, a.ratio_kind) == ("slice", 1, "max")
    b = apply_scope_defaults(XAppAction(xapp_id="x", node_id="g", parameter="PRB_QUOTA", value=25.0, priority=90,
                                        slice_sst=2), nori)
    assert (b.scope, b.slice_sst, b.ratio_kind) == ("slice", 2, "max")          # o declarado prevalece
    c = apply_scope_defaults(XAppAction(xapp_id="x", node_id="g", parameter="PRB_QUOTA", value=25.0, priority=90,
                                        scope="cell"), nori)
    assert (c.scope, c.slice_sst, c.ratio_kind) == ("cell", None, None)
    d = apply_scope_defaults(XAppAction(xapp_id="x", node_id="g", parameter="TX_POWER", value=20.0, priority=50), nori)
    assert d.scope is None                                                       # slice só vale para PRB_QUOTA
    e = apply_scope_defaults(XAppAction(xapp_id="x", node_id="g", parameter="PRB_QUOTA", value=25.0, priority=90), native)
    assert (e.scope, e.slice_sst, e.ratio_kind) == ("cell", None, None)
    f = apply_scope_defaults(XAppAction(xapp_id="x", node_id="g", parameter="PRB_QUOTA", value=25.0, priority=90,
                                        ratio_kind="min"), native)
    assert (f.scope, f.slice_sst, f.ratio_kind) == ("slice", None, "min")
    g = apply_scope_defaults(XAppAction(xapp_id="x", node_id="g", parameter="PRB_QUOTA", value=25.0, priority=90), {})
    assert g.scope is None


# ---------------------------------------------------------------- codec

def test_codec_quotas_for_proposal():
    assert quotas_for_proposal(25, 1, "max", complement_sst=2) == [SlicePrbQuota(1, 25, 0, 0), SlicePrbQuota(2, 75, 0, 0)]
    assert quotas_for_proposal(40, 2, "max") == [SlicePrbQuota(2, 40, 0, 0)]
    assert quotas_for_proposal(30, 1, "min", complement_sst=2) == [SlicePrbQuota(1, 100, 30, 0)]
    assert quotas_for_proposal(20, 2, "dedicated") == [SlicePrbQuota(2, 100, 20, 20)]
    with pytest.raises(CodecError):
        quotas_for_proposal(30, 1, "avg")
    with pytest.raises(CodecError):
        quotas_for_proposal(130, 1, "max")


def test_nori_quotas_and_reference_proposals_declare_scope():
    from src.closed_loop import hrdl_slice_loop as loop
    assert loop.quotas_for(25) == [SlicePrbQuota(1, 25, 0, 0), SlicePrbQuota(2, 75, 0, 0)]
    state = {"congested": True, "ues_by_sst": {"1": [1], "2": [2]}}
    proposals = loop.reference_proposals(state, "gnb_0")
    assert {(p.scope, p.slice_sst, p.ratio_kind) for p in proposals} == {("slice", 1, "max")}


# ---------------------------------------------------------------- §4.2–4.3 modelo de efeito

def test_curve_sha256_and_ratio():
    curve = load_curve()
    assert curve.sha256 == EXPECTED_SHA256 and curve.base_throughput_mbps == pytest.approx(151.488)
    assert curve.ratio(20) == pytest.approx(76.446 / 151.488)
    assert curve.ratio(35) == pytest.approx(0.8763, abs=1e-4)                 # S8b, doc 18 §4.6
    assert curve.ratio(55) == 1.0 and curve.saturation_cap_pct() == pytest.approx(39.99, abs=0.01)


def test_effect_model_is_off_by_default(monkeypatch):
    monkeypatch.delenv("RDL_EFFECT_MODEL", raising=False)
    assert build_effect_model({}) is None
    assert Reasoning(_Mem()).effect_model_tag == "heuristic"
    with pytest.raises(ValueError):
        build_effect_model({"effect_model": "magic"})


def test_s8_scores_match_the_design(model):
    xs, eb = s8()
    sx, se = model.scores(xs), model.scores(eb)
    assert sx["throughput"] == pytest.approx(246.73 / 302.98, abs=2e-3)       # doc 18 §4.6: 0,814
    assert se["throughput"] == pytest.approx(227.93 / 302.98, abs=2e-3)       # 0,752
    assert sx["sla"] == 1.0 and se["sla"] == pytest.approx(0.5046, abs=1e-4)
    assert model.tag == f"curve:{EXPECTED_SHA256}"


def test_effect_model_ignores_cell_scope_and_other_ratio_kinds(model):
    cell = XAppAction(xapp_id="x", node_id="g", parameter="PRB_QUOTA", value=25.0, priority=90, scope="cell")
    undeclared = XAppAction(xapp_id="x", node_id="g", parameter="PRB_QUOTA", value=25.0, priority=90)
    assert model.scores(cell) is None and model.scores(undeclared) is None
    assert model.scores(quota("x", 25, 90, ratio_kind="min")) is None
    assert model.scores(quota("x", 25, 90, slice_sst=7)) is None


def test_sla_requirements_parsing():
    assert parse_sla_slices("2", {1: 151.0, 2: 151.0}) == {2: 151.0}
    assert parse_sla_slices("2:120, 1:40", {1: 151.0, 2: 151.0}) == {2: 120.0, 1: 40.0}
    with pytest.raises(ValueError):
        parse_sla_slices("3", {1: 151.0, 2: 151.0})


# ---------------------------------------------------------------- §4.4 guarda

def test_guard_removes_the_candidate_that_breaks_the_sla(model):
    xs, eb = s8()
    eligible, excluded = sla_guard([xs, eb], model)
    assert eligible == [xs] and set(excluded) == {eb.action_id}
    assert "s_SLA 0.5046" in excluded[eb.action_id]


def test_guard_when_all_violate_keeps_the_highest_sla(model):
    a, b, c = quota("a", 75, 60), quota("b", 85, 60), quota("c", 75, 50, action_id="c2")
    eligible, excluded = sla_guard([a, b, c], model)
    assert {x.action_id for x in eligible} == {a.action_id, "c2"} and set(excluded) == {b.action_id}


def test_guard_is_inert_without_model_or_with_mixed_scope(model):
    xs, eb = s8()
    assert sla_guard([xs, eb], None) == ([xs, eb], {})
    cell = XAppAction(xapp_id="c", node_id="gnb_0", parameter="PRB_QUOTA", value=80.0, priority=60, scope="cell")
    assert sla_guard([xs, cell], model) == ([xs, cell], {})
    both_ok = [quota("a", 35, 90), quota("b", 55, 60)]                         # S8b: a guarda não age
    assert sla_guard(both_ok, model) == (both_ok, {})


def test_tvs_keeps_todays_choice_without_model_and_protects_with_it(model):
    from src.conflict_types import ConflictEvent, ConflictSeverity, ConflictType
    xs, eb = s8()
    conflict = ConflictEvent(ConflictType.DIRECT, ConflictSeverity.HIGH, [xs, eb])
    plain = Reasoning(_Mem(), config={"effect_model": "heuristic"}).resolve(conflict)
    assert plain.winning_actions == [eb] and plain.sla_excluded == {} and plain.effect_model == "heuristic"
    guarded_reasoning = Reasoning(_Mem(), config={"effect_model": "curve"})
    guarded = guarded_reasoning.resolve(conflict)
    assert guarded.winning_actions == [xs] and set(guarded.sla_excluded) == {eb.action_id}
    assert guarded.effect_model == model.tag
    # §4.3 fica como gancho: a utilidade do TVS continua com os escores heurísticos
    assert guarded_reasoning._tvs_scores(eb) == guarded_reasoning._calculate_action_scores(eb)
    assert guarded_reasoning.effect_scores(eb)["sla"] == pytest.approx(0.5046, abs=1e-4)


# ---------------------------------------------------------------- SLA_PROTECTION no pipeline e no RMR

def test_reason_is_registered():
    assert preg.SLA_PROTECTION in preg.REASONS and preg.SLA_PROTECTION != preg.LOST_ARBITRATION
    assert len(preg.REASONS) == 8


def _app(monkeypatch, effect_model):
    monkeypatch.setenv("RDL_EFFECT_MODEL", effect_model)
    monkeypatch.delenv("RDL_BACKEND_PROFILE", raising=False)
    from src.rdl_xapp import RDLxApp
    instance = RDLxApp()
    instance.dispatcher.dispatch_control = lambda decision, **_: "req"
    sent = []
    instance.xapp = types.SimpleNamespace(rmr_send=lambda payload, mtype, *a, **k: sent.append((json.loads(payload), mtype)) or True,
                                          stop=lambda: None)
    instance.sent = sent
    return instance


def test_pipeline_sends_sla_protection_on_rmr_30001(monkeypatch):
    app = _app(monkeypatch, "curve")
    try:
        xs, eb = s8()
        app._process_action_group([xs, eb])
        entries = app._rejections_view()["entries"]
        assert [(e["xapp_id"], e["reason"], e["winner_xapp_id"]) for e in entries] == \
            [("xapp-embb-throughput", preg.SLA_PROTECTION, "xapp-qos-xslice")]
        (payload, mtype), = app.sent
        assert mtype == RDL_ACTION_RESULT and payload["reason"] == preg.SLA_PROTECTION
        assert payload["detail"].startswith("SLA guard")
    finally:
        app.stop()


def test_pipeline_without_model_keeps_lost_arbitration(monkeypatch):
    app = _app(monkeypatch, "heuristic")
    try:
        xs, eb = s8()
        app._process_action_group([xs, eb])
        entries = app._rejections_view()["entries"]
        assert [(e["xapp_id"], e["reason"]) for e in entries] == [("xapp-qos-xslice", preg.LOST_ARBITRATION)]
    finally:
        app.stop()


def test_rmr_30000_reads_scope_fields_and_backend_defaults(monkeypatch):
    app = _app(monkeypatch, "heuristic")
    try:
        captured = []
        app._enqueue = lambda a: captured.append(a)
        app.oran_strict = False
        base = {"xapp_id": "xslice", "node_id": "gnb_0", "parameter": "PRB_QUOTA", "value": 25, "priority": 90}
        send = lambda msg: app._action_proposal_handler(None, {"payload": json.dumps(msg).encode()}, None)
        send({**base, "scope": "slice", "slice_sst": 2, "ratio_kind": "min"})
        assert (captured[-1].scope, captured[-1].slice_sst, captured[-1].ratio_kind) == ("slice", 2, "min")
        send(base)                                                   # sem perfil declarado: sem escopo
        assert captured[-1].scope is None
        app.scope_defaults = scope_defaults("NORI_NS3")
        send(base)
        assert (captured[-1].scope, captured[-1].slice_sst, captured[-1].ratio_kind) == ("slice", 1, "max")
        n = len(captured)
        for bad in ({"scope": 1}, {"scope": "zone"}, {"slice_sst": "1"}, {"ratio_kind": 3},
                    {"scope": "cell", "slice_sst": 1}, {"parameter": "TX_POWER", "value": 20, "scope": "slice"}):
            send({**base, **bad})
        assert len(captured) == n                                    # propostas inválidas não entram
    finally:
        app.stop()


def test_rapp_does_not_count_sla_protection_as_lost_arbitration():
    spec = importlib.util.spec_from_file_location("greenran_resource_optimizer",
                                                  ROOT / "rapps" / "greenran_resource_optimizer.py")
    r = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r)
    protected = r.plan({}, hour=2, report={"rejections": {"by_xapp": {"xapp2_energysaver": {"SLA_PROTECTION": 30}}}})
    assert protected["policies"]["20001"]["energy_weight"] == pytest.approx(0.45)
    mixed = r.plan({}, hour=2, report={"rejections": {"by_xapp": {"xapp2_energysaver": {
        "LOST_ARBITRATION": 9, "SAFETY": 1, "SLA_PROTECTION": 20}}}})
    assert mixed["policies"]["20001"]["energy_weight"] == pytest.approx(0.55)
