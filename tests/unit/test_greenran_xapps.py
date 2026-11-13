"""RANSlicer-GreenRAN, EnergySaver-GreenRAN e rApp-ResourceOptimizer do GreenRAN (doc 12)."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference-xapps" / "common"))
from rdl_transport import RdlTransport  # noqa: E402

from src.conflict_types import XAppAction  # noqa: E402
from src.greenran.common import CellSample, SeasonalProfile, SliceKpi, normalize_kpm  # noqa: E402
from src.greenran.ranslicer_greenran import RanSlicer  # noqa: E402
from src.greenran.energysaver_greenran import ACTIVE, EVACUATING, SLEEP, EnergySaver  # noqa: E402

# as regras testadas aqui são as de decisão; a observação mínima tem teste próprio (test_energysaver_greenran_melhorias)
EnergySaver.DEFAULTS = {**EnergySaver.DEFAULTS, "es_min_observation_s": 0.0}
from src.interfaces.a1_policy_receiver import A1PolicyManager  # noqa: E402


def transport(xapp_id):
    t = RdlTransport(xapp_id, mode="none")
    t.start()
    return t


def a1_msg(type_id, instance, payload):
    return json.dumps({"operation": "CREATE", "policy_type_id": type_id, "policy_instance_id": instance,
                       "payload": payload}).encode()


def test_normalize_kpm_merges_node_and_ue_reports():
    s = normalize_kpm("gnb_0", {"node": {"RRU.PrbUsedDl": 60, "RRU.PrbAvailDl": 40}}, t=1.0)
    assert s.load_pct == 60.0
    s = normalize_kpm("gnb_0", {"ues": [
        {"measurements": {"DRB.NetworkSlicing.SST": 1, "DRB.UEThpDl": 12000, "RRU.PrbUsedDl": 30, "DRB.RlcSduDelayDl": 40}},
        {"measurements": {"DRB.NetworkSlicing.SST": 1, "DRB.UEThpDl": 8000, "RRU.PrbUsedDl": 20, "DRB.RlcSduDelayDl": 120}},
        {"measurements": {"DRB.NetworkSlicing.SST": 2, "DRB.UEThpDl": 500, "RRU.PrbUsedDl": 10}}]}, t=2.0, previous=s)
    assert s.load_pct == 60.0 and s.total_ues == 3
    assert s.slices[1].thp_mbps == pytest.approx(20.0) and s.slices[1].delay_ms == 120 and s.slices[2].ues == 1


def test_seasonal_profile():
    p = SeasonalProfile(alpha=0.5)
    p.update("c", 3, 10.0)
    p.update("c", 3, 20.0)
    assert p.expected("c", 3) == 15.0 and p.expected("c", 4, default=7) == 7 and p.expected("x", 1) is None
    assert p.to_dict()["c"][3] == 15.0


# ---------------------------------------------------------------- RANSlicer-GreenRAN

def sample(cell, load, thp, delay, prb=50, ues=2):
    return CellSample(cell, 0.0, load_pct=load, slices={1: SliceKpi(thp_mbps=thp, delay_ms=delay, prb_used=prb, ues=ues),
                                                       2: SliceKpi(thp_mbps=0.5, prb_used=10, ues=3)})


def test_ranslicer_computes_safe_quota_from_measured_efficiency():
    x = RanSlicer(transport=transport("ranslicer_greenran"))
    x.observe(sample("gnb_0", load=60, thp=25.0, delay=40))       # eMBB ≈ 50 % dos PRBs → 0,5 Mb/s por ponto
    (p,) = x.step(now=0)
    assert p["parameter"] == "PRB_QUOTA" and p["priority"] == 90       # vazão 25 < alvo 30: SLA em risco
    assert p["value"] == 69.0                                          # 30 × 1,15 ÷ 0,5 = 69
    assert x.step(now=1)[0]["value"] == 69.0                           # ainda em risco: repete
    resp = x.handle_a1(a1_msg(21000, "greenran-ranslicer", {"embb_min_thp_mbps": 10, "mmtc_min_prb_pct": 20}))
    assert resp["status"] == "OK"
    (p,) = x.step(now=2)
    assert p["value"] == 23.0 and p["priority"] == 75                  # 10 × 1,15 ÷ 0,5 = 23
    assert x.step(now=3) == []                                         # mudança < 2 pontos: nada


def test_ranslicer_delay_raises_quota_and_learned_policy_is_shielded():
    x = RanSlicer(transport=transport("ranslicer_greenran"), learned_policy=lambda state: 99.0)
    x.handle_a1(a1_msg(21000, "op", {"embb_min_thp_mbps": 5, "ranslicer_learned_policy": True, "mmtc_min_prb_pct": 15}))
    x.observe(sample("gnb_0", load=60, thp=30.0, delay=250))
    (p,) = x.step(now=0)
    assert p["value"] == 85.0                                          # política pede 99; escudo corta em 100 − 15
    low = RanSlicer(transport=transport("ranslicer_greenran"), learned_policy=lambda state: 1.0)
    low.handle_a1(a1_msg(21000, "op", {"ranslicer_learned_policy": True}))
    low.observe(sample("gnb_0", load=60, thp=40.0, delay=10))
    assert low.step(now=0)[0]["value"] == 44.0                         # eficiência 40 ÷ 50 = 0,8: 30 × 1,15 ÷ 0,8 → 44; não desce abaixo
    assert low.handle_a1(a1_msg(21000, "op", {"es_sleep_threshold_pct": 5}))["status"] == "ERROR"


# ---------------------------------------------------------------- EnergySaver-GreenRAN

def cell(cid, load, ues):
    s = CellSample(cid, 0.0, load_pct=load, slices={1: SliceKpi(ues=ues)} if ues else {})
    return s


def test_energysaver_evacuates_then_sleeps_and_wakes():
    hour = {"h": 2}
    x = EnergySaver(transport=transport("energysaver_greenran"), neighbors={"gnb_0": ["gnb_1"], "gnb_1": ["gnb_0"]},
                    hour_of=lambda t: hour["h"])
    x.observe(cell("gnb_0", 30, 5))
    x.observe(cell("gnb_1", 5, 2))
    (p,) = x.step(now=0)
    assert (p["node_id"], p["parameter"], p["value"]) == ("gnb_1", "HANDOVER", 0.0) and x.state["gnb_1"] == EVACUATING
    x.observe(cell("gnb_1", 0, 0))
    (p,) = x.step(now=1)
    assert (p["parameter"], p["value"]) == ("CELL_STATE", 0.0) and x.state["gnb_1"] == SLEEP
    assert x.step(now=2) == [] or all(q["node_id"] != "gnb_0" or q["parameter"] != "CELL_STATE" for q in x.sent)
    x.observe(cell("gnb_0", 75, 9))                                    # vizinha quente: religa
    (p,) = x.step(now=3)
    assert (p["node_id"], p["parameter"], p["value"]) == ("gnb_1", "CELL_STATE", 1.0) and x.state["gnb_1"] == ACTIVE


def test_energysaver_respects_window_min_cells_and_rejections():
    hour = {"h": 14}
    x = EnergySaver(transport=transport("energysaver_greenran"), neighbors={"gnb_0": ["gnb_1"], "gnb_1": ["gnb_0"]},
                    hour_of=lambda t: hour["h"])
    x.observe(cell("gnb_0", 20, 5))
    x.observe(cell("gnb_1", 0, 0))
    assert [(p["node_id"], p["parameter"]) for p in x.step(now=0)] == [("gnb_0", "TX_POWER")]   # de dia: só a potência da moderada
    hour["h"] = 23
    x.handle_a1(a1_msg(21001, "greenran-energysaver", {"es_min_active_cells": 2}))
    assert all(p["parameter"] != "CELL_STATE" for p in x.step(now=1))  # 2 células mínimas: não desliga
    x.handle_a1(a1_msg(21001, "greenran-energysaver", {"es_min_active_cells": 1, "es_tx_power_reduction": False}))
    (p,) = x.step(now=2)
    assert p["parameter"] == "CELL_STATE" and x.state["gnb_1"] == SLEEP
    x.on_result({"node_id": "gnb_1", "parameter": "CELL_STATE", "reason": "SAFETY"})
    assert x.state["gnb_1"] == ACTIVE                                  # recusado pela RDL
    assert x.status()["xapp_id"] == "energysaver_greenran"


def test_greenran_proposals_go_through_the_rdl_pipeline(monkeypatch, tmp_path):
    topo = tmp_path / "topo.json"
    topo.write_text(json.dumps({"neighbors": {"gnb_0": ["gnb_1"]}}), encoding="utf-8")
    monkeypatch.setenv("RDL_TOPOLOGY_FILE", str(topo))
    from src.rdl_xapp import RDLxApp
    app = RDLxApp()
    try:
        sent = []
        app.dispatcher.dispatch_control = lambda decision, **_: sent.append(decision.selected_actions[0]) or "req"
        slicer = RanSlicer(transport=transport("ranslicer_greenran"))
        slicer.observe(sample("gnb_1", load=60, thp=25.0, delay=40))
        saver = EnergySaver(transport=transport("energysaver_greenran"), neighbors={"gnb_0": ["gnb_1"], "gnb_1": ["gnb_0"]},
                            hour_of=lambda t: 2)
        saver.observe(cell("gnb_0", 30, 5))
        saver.observe(cell("gnb_1", 0, 0))
        props = slicer.step(now=0) + saver.step(now=0)
        actions = [XAppAction(xapp_id=p["xapp_id"], node_id=p["node_id"], parameter=p["parameter"],
                              value=p["value"], priority=p["priority"]) for p in props]
        app._process_action_group(actions)
        # PRB_QUOTA (90) e CELL_STATE=0 (65) na mesma célula: conflito indireto decidido pelo EEVS
        assert {a.parameter for a in sent} <= {"PRB_QUOTA", "CELL_STATE"} and sent
        assert app.knowledge_graph.stats().get("conflict", 0) >= 1
    finally:
        app.stop()


# ---------------------------------------------------------------- rApp-ResourceOptimizer

def _rapp():
    spec = importlib.util.spec_from_file_location("greenran_resource_optimizer", ROOT / "rapps" / "greenran_resource_optimizer.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_rapp_plans_three_policies_accepted_by_a1_and_owners():
    r = _rapp()
    owners = json.loads((ROOT / "configs" / "a1_field_owners.example.json").read_text(encoding="utf-8"))
    night = r.plan({"cameras": 4, "camera_mbps": 5}, hour=2)
    assert night["policies"]["20001"]["energy_weight"] == 0.45 and night["sla_at_risk"] is False
    assert night["policies"]["21000"]["embb_min_thp_mbps"] == 20.0
    m = A1PolicyManager()
    m.set_field_owners(owners)
    for t, data in night["policies"].items():
        assert m.put_policy(t, r.INSTANCES[t], data)[0], t              # esquema e donos aceitam
    risk = r.plan({"cameras": 4, "camera_mbps": 5}, hour=2, kpi={"embb_delay_ms": 150, "embb_thp_mbps": 30})
    assert risk["sla_at_risk"] and risk["policies"]["20001"]["sla_weight"] == 0.75
    assert risk["policies"]["20001"]["allow_neighbor_sleep"] is False
    assert risk["policies"]["21001"]["es_min_active_cells"] == 2 and risk["policies"]["21000"]["slice_safety_margin"] == 0.30
    implicit = r.plan({}, hour=2, report={"implicit_conflicts": [{"node_id": "gnb_1"}]})
    assert implicit["policies"]["21001"]["es_sleep_threshold_pct"] == 0.0
    losing = r.plan({}, hour=2, report={"rejections": {"by_xapp": {"energysaver_greenran": {"LOST_ARBITRATION": 9, "SAFETY": 1}}}})
    assert losing["policies"]["20001"]["energy_weight"] == pytest.approx(0.55)
    day = r.plan({"energy_priority": "low"}, hour=14)
    assert day["policies"]["20001"]["energy_weight"] == 0.05


def test_rapp_intent_text_and_dry_run(capsys):
    r = _rapp()
    intent = r.parse_intent_text("6 câmeras a 25 Mb/s com atraso de 100 ms, economizar energia ao máximo e 2 células ativas")
    assert intent == {"cameras": 6, "camera_mbps": 25.0, "max_delay_ms": 100.0, "energy_priority": "high", "min_active_cells": 2}
    assert r.main(["--intent-text", "economizar energia", "--dry-run", "--hour", "3"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert {b["policytype_id"] for b in out["policies"]} == {"20001", "21000", "21001"}
