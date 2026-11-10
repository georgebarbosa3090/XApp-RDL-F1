"""Conflitos entre células, parâmetro CELL_STATE e políticas A1 ligadas à decisão (adequação GreenRAN)."""
import time

import pytest

from src.conflict_types import ConflictEvent, ConflictSeverity, ConflictType, XAppAction
from src.core.inter_cell import (
    HANDOVER_INTO_REDUCED_CELL,
    HANDOVER_PING_PONG,
    NEIGHBOR_SLEEP,
    InterCellRules,
    default_handover_target,
)
from src.core.perception import Perception
from src.core.reasoning import Reasoning
from src.core.refinement import Refinement
from src.infrastructure.memory_module import MemoryModule
from src.interfaces.a1_policy_receiver import A1PolicyManager


def act(xapp, node, param, value, prio, ts=None):
    a = XAppAction(xapp_id=xapp, node_id=node, parameter=param, value=float(value), priority=prio)
    if ts is not None:
        a.timestamp = ts
    return a


def inter_cell(conflicts):
    return [c for c in conflicts if c.conflict_type == ConflictType.INTER_CELL]


def reasons(conflicts):
    return sorted(c.description.split()[2] for c in inter_cell(conflicts))


# --- regras -------------------------------------------------------------------------

@pytest.mark.parametrize("node,value,expected", [
    ("gnb_0", 1, "gnb_1"),
    ("gnb_268_341_00000001#g0", 1, "gnb_268_341_00000001#g1"),
    ("gnb_0", 1.5, None),
    ("gnb_0", -1, None),
    ("macro", 1, None),
])
def test_default_handover_target(node, value, expected):
    assert default_handover_target(act("ts", node, "HANDOVER", value, 80)) == expected


def test_rules_ignore_same_xapp_and_same_node():
    rules = InterCellRules()
    ho = act("ts", "gnb_0", "HANDOVER", 1, 80)
    assert rules.pair_conflict(ho, act("ts", "gnb_1", "CELL_STATE", 0, 60)) is None
    assert rules.pair_conflict(ho, act("es", "gnb_0", "CELL_STATE", 0, 60)) is None


def test_low_power_threshold():
    rules = InterCellRules(low_power_threshold_dbm=10.0)
    ho = act("ts", "gnb_0", "HANDOVER", 1, 80)
    assert rules.pair_conflict(ho, act("es", "gnb_1", "TX_POWER", 10, 65)) == HANDOVER_INTO_REDUCED_CELL
    assert rules.pair_conflict(ho, act("es", "gnb_1", "TX_POWER", 20, 65)) is None


# --- percepção ----------------------------------------------------------------------

def test_detects_handover_into_cell_being_switched_off():
    p = Perception()
    conflicts = p.detect_action_group([
        act("traffic_steering", "gnb_0", "HANDOVER", 1, 80),
        act("energy_saving", "gnb_1", "CELL_STATE", 0, 65),
    ])
    found = inter_cell(conflicts)
    assert len(found) == 1 and HANDOVER_INTO_REDUCED_CELL in found[0].description
    assert found[0].severity == ConflictSeverity.HIGH
    assert {a.node_id for a in found[0].involved_xapps} == {"gnb_0", "gnb_1"}


def test_detects_handover_into_cell_kept_in_low_power_by_incumbent():
    p = Perception()
    p.commit_actions([act("energy_saving", "gnb_1", "TX_POWER", 0, 65)])
    conflicts = p.detect_action_group([act("traffic_steering", "gnb_0", "HANDOVER", 1, 80)])
    assert reasons(conflicts) == [HANDOVER_INTO_REDUCED_CELL]


def test_detects_ping_pong_in_same_window_and_against_recent_incumbent():
    p = Perception()
    same_window = p.detect_action_group([
        act("traffic_steering", "gnb_0", "HANDOVER", 1, 80),
        act("load_balancer", "gnb_1", "HANDOVER", 0, 70),
    ])
    assert reasons(same_window) == [HANDOVER_PING_PONG]

    p2 = Perception()
    p2.commit_actions([act("traffic_steering", "gnb_0", "HANDOVER", 1, 80, ts=time.time() - 1.0)])
    assert reasons(p2.detect_action_group([act("load_balancer", "gnb_1", "HANDOVER", 0, 70)])) == [HANDOVER_PING_PONG]


def test_old_handover_outside_window_is_not_ping_pong():
    p = Perception(inter_cell_rules=InterCellRules(pingpong_window_s=5.0))
    p.commit_actions([act("traffic_steering", "gnb_0", "HANDOVER", 1, 80, ts=time.time() - 60.0)])
    assert inter_cell(p.detect_action_group([act("load_balancer", "gnb_1", "HANDOVER", 0, 70)])) == []


def test_neighbor_sleep_needs_topology_and_policy():
    actions = [act("es_a", "gnb_0", "CELL_STATE", 0, 60), act("es_b", "gnb_1", "CELL_STATE", 0, 60)]
    assert inter_cell(Perception().detect_action_group(actions)) == []

    rules = InterCellRules.from_config({"neighbors": {"gnb_0": ["gnb_1"]}})
    assert reasons(Perception(inter_cell_rules=rules).detect_action_group(actions)) == [NEIGHBOR_SLEEP]

    rules.allow_neighbor_sleep = True
    assert inter_cell(Perception(inter_cell_rules=rules).detect_action_group(actions)) == []


def test_unrelated_actions_produce_no_inter_cell_conflict():
    conflicts = Perception().detect_action_group([
        act("xslice", "gnb_0", "PRB_QUOTA", 80, 90),
        act("energy_saving", "gnb_1", "TX_POWER", 30, 65),
        act("traffic_steering", "gnb_0", "HANDOVER", 2, 80),
    ])
    assert inter_cell(conflicts) == []


# --- raciocínio ---------------------------------------------------------------------

def test_eevs_never_admits_both_sides_of_inter_cell_conflict():
    ho = act("traffic_steering", "gnb_0", "HANDOVER", 1, 80)
    sleep = act("energy_saving", "gnb_1", "CELL_STATE", 0, 65)
    conflict = ConflictEvent(ConflictType.INTER_CELL, ConflictSeverity.HIGH, [ho, sleep])
    resolution = Reasoning(MemoryModule()).resolve(conflict)
    assert resolution.winning_actions == [ho]


def test_cell_state_scores():
    r = Reasoning(MemoryModule())
    off = r._calculate_action_scores(act("energy_saving", "gnb_1", "CELL_STATE", 0, 65))
    on = r._calculate_action_scores(act("xslice", "gnb_1", "CELL_STATE", 1, 90))
    assert off["energy"] > on["energy"] and off["throughput"] < on["throughput"]


# --- Safety Guard -------------------------------------------------------------------

def test_cell_state_bounds_and_policy():
    ref = Refinement(MemoryModule())
    assert ref.check_bounds(act("es", "gnb_1", "CELL_STATE", 0, 60))[0]
    assert not ref.check_bounds(act("es", "gnb_1", "CELL_STATE", 2, 60))[0]
    assert not ref.check_bounds(act("es", "gnb_1", "CELL_STATE", 0.5, 60))[0]
    ref.apply_policy(allow_cell_sleep=False)
    ok, reason = ref.check_bounds(act("es", "gnb_1", "CELL_STATE", 0, 60))
    assert not ok and "A1" in reason
    assert ref.check_bounds(act("es", "gnb_1", "CELL_STATE", 1, 60))[0]


def test_a1_prb_limit_only_tightens():
    ref = Refinement(MemoryModule())
    ref.apply_policy(max_prb_quota=60)
    assert ref.check_bounds(act("xslice", "gnb_0", "PRB_QUOTA", 60, 90))[0]
    ok, reason = ref.check_bounds(act("xslice", "gnb_0", "PRB_QUOTA", 70, 90))
    assert not ok and "A1" in reason
    ref.apply_policy(max_prb_quota=None)
    assert ref.check_bounds(act("xslice", "gnb_0", "PRB_QUOTA", 70, 90))[0]


# --- A1 -----------------------------------------------------------------------------

def test_greenran_policy_type_validation_and_effective_merge():
    mgr = A1PolicyManager()
    seen = []
    mgr.add_listener(seen.append)
    assert seen == [{}]
    assert mgr.put_policy("20001", "p1", {"energy_weight": 0.3, "allow_neighbor_sleep": True})[0]
    assert not mgr.put_policy("20001", "bad", {"energy_weight": 0.9})[0]
    assert not mgr.put_policy("20001", "bad", {"allow_neighbor_sleep": "yes"})[0]
    assert mgr.put_policy("20000", "p0", {"max_cell_prb_limit": 70})[0]
    assert seen[-1] == {"energy_weight": 0.3, "allow_neighbor_sleep": True, "max_cell_prb_limit": 70}
    assert mgr.delete_policy("20001", "p1")
    assert seen[-1] == {"max_cell_prb_limit": 70}


def test_rdl_xapp_applies_and_reverts_a1_policy():
    from src.rdl_xapp import RDLxApp

    app = RDLxApp()
    base_w_energy = app.reasoning.w_energy
    base_interval = app.refinement.config["minimum_control_interval_ms"]
    try:
        assert app.a1_policies.put_policy("20001", "green", {
            "energy_weight": 0.5, "sla_weight": 0.3, "allow_neighbor_sleep": True, "low_power_threshold_dbm": 5,
        })[0]
        assert app.a1_policies.put_policy("20000", "gov", {
            "energy_saving_allowed": False, "max_cell_prb_limit": 60, "cooling_lockout_ms": 300, "urllc_priority_boost": 10,
        })[0]
        assert app.reasoning.w_energy == app.reasoning.w_energy_ind == 0.5
        assert app.reasoning.w_sla == app.reasoning.w_qos_ind == 0.3
        assert app.reasoning.urllc_priority_boost == 10
        assert app.refinement.policy_max_prb_quota == 60
        assert app.refinement.policy_allow_cell_sleep is False
        assert app.refinement.config["minimum_control_interval_ms"] == 300
        assert app.inter_cell_rules.allow_neighbor_sleep is True
        assert app.inter_cell_rules.low_power_threshold_dbm == 5
        # A percepção e o raciocínio usam o mesmo objeto de regras
        assert app.perception.inter_cell_rules is app.reasoning.inter_cell_rules is app.inter_cell_rules

        app.a1_policies.delete_policy("20000", "gov")
        app.a1_policies.delete_policy("20001", "green")
        assert app.reasoning.w_energy == base_w_energy
        assert app.refinement.policy_max_prb_quota is None
        assert app.refinement.policy_allow_cell_sleep is True
        assert app.refinement.config["minimum_control_interval_ms"] == base_interval
        assert app.inter_cell_rules.allow_neighbor_sleep is False
    finally:
        app.stop()


def test_rdl_xapp_resolves_inter_cell_conflict_end_to_end():
    from src.rdl_xapp import RDLxApp

    app = RDLxApp()
    sent = []
    app.dispatcher.dispatch_control = lambda decision, **_: sent.append(decision.selected_actions[0]) or "req"
    try:
        ho = act("traffic_steering", "gnb_0", "HANDOVER", 1, 80)
        sleep = act("energy_saving", "gnb_1", "CELL_STATE", 0, 65)
        app._process_action_group([ho, sleep])
        assert sent == [ho]
    finally:
        app.stop()


def test_example_topology_file_loads(monkeypatch):
    from pathlib import Path
    from src.core.inter_cell import load_inter_cell_config

    path = Path(__file__).resolve().parents[2] / "configs" / "testbed_ufpa" / "topology.example.json"
    monkeypatch.setenv("RDL_TOPOLOGY_FILE", str(path))
    rules = InterCellRules.from_config(load_inter_cell_config())
    assert rules.are_neighbors("ufpa_ru_ext_0", "ufpa_ru_ext_1")
    assert rules.are_neighbors("ufpa_ru_int_1", "ufpa_ru_ext_1")  # vizinhança simétrica
    assert not rules.are_neighbors("ufpa_ru_ext_0", "ufpa_ru_int_1")
    assert rules.allow_neighbor_sleep is False


def test_committed_handover_keeps_protecting_target_until_replaced():
    p = Perception(inter_cell_rules=InterCellRules(pingpong_window_s=5.0))
    p.commit_actions([act("traffic_steering", "gnb_0", "HANDOVER", 1, 80, ts=time.time() - 60.0)])
    assert reasons(p.detect_action_group([act("energy_saving", "gnb_1", "TX_POWER", 0, 65)])) == [HANDOVER_INTO_REDUCED_CELL]
    # Novo handover do mesmo nó de origem para outra célula substitui o anterior
    p.commit_actions([act("traffic_steering", "gnb_0", "HANDOVER", 2, 80)])
    assert inter_cell(p.detect_action_group([act("energy_saving", "gnb_1", "TX_POWER", 0, 65)])) == []


def test_handover_hold_limits_protection():
    p = Perception(inter_cell_rules=InterCellRules(handover_hold_s=30.0))
    p.commit_actions([act("traffic_steering", "gnb_0", "HANDOVER", 1, 80, ts=time.time() - 60.0)])
    assert inter_cell(p.detect_action_group([act("energy_saving", "gnb_1", "TX_POWER", 0, 65)])) == []
