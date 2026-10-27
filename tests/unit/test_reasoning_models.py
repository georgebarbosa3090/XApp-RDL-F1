import pytest
from src.core.reasoning import Reasoning
from src.infrastructure.memory_module import MemoryModule
from src.conflict_types import ConflictEvent, ConflictType, ConflictSeverity, XAppAction, ResolutionStrategy, KPMReport

def test_reasoning_shannon_and_tvs_resolution():
    memory = MemoryModule()
    reasoning = Reasoning(memory)
    
    act_urllc = XAppAction(xapp_id="xslice", node_id="gnb_01", parameter="PRB_QUOTA", value=80.0, priority=90)
    act_embb = XAppAction(xapp_id="traffic_steering", node_id="gnb_01", parameter="PRB_QUOTA", value=40.0, priority=50)
    
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[act_urllc, act_embb],
        affected_kpis=["PRB_QUOTA"],
        description="Disputa direta de cotas de PRB entre fatias"
    )
    
    resolution = reasoning.resolve(conflict)
    assert resolution.strategy_used in (ResolutionStrategy.TVS, ResolutionStrategy.PRIORITY_TABLE)
    assert len(resolution.winning_actions) > 0
    assert resolution.winning_actions[0].xapp_id == "xslice"


def test_large_indirect_conflict_uses_deterministic_bounded_strategy():
    reasoning = Reasoning(MemoryModule(), config={"max_exact_actions": 4})
    actions = [
        XAppAction(f"xapp_{index}", "gnb_01", f"PARAM_{index}", float(index), 50)
        for index in range(12)
    ]
    conflict = ConflictEvent(
        conflict_type=ConflictType.INDIRECT,
        severity=ConflictSeverity.MEDIUM,
        involved_xapps=actions,
        affected_kpis=["DRB.UEThpDl"],
        description="Large indirect conflict",
    )

    resolution = reasoning.resolve(conflict)

    assert resolution.strategy_used == ResolutionStrategy.EEVS
    assert resolution.winning_actions
    assert resolution.confidence == 0.70
    assert resolution.winning_actions == reasoning.resolve(conflict).winning_actions


def test_observed_latency_blocks_energy_policy_score():
    reasoning = Reasoning(MemoryModule())
    action = XAppAction(
        xapp_id="energy_saver",
        node_id="gnb_01",
        parameter="TX_POWER",
        value=10.0,
        priority=60,
    )
    baseline_score = reasoning._calculate_action_scores(action)["sla"]
    reasoning.update_kpm_report(
        KPMReport(
            node_id="gnb_01",
            ue_id="ue_01",
            drb_thp_dl=10.0,
            drb_thp_ul=None,
            drb_delay_dl=8.0,
            prb_used_dl=None,
        )
    )

    assert baseline_score > 0.0
    assert reasoning._calculate_action_scores(action)["sla"] == 0.0
