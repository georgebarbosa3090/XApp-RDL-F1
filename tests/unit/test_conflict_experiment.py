"""
Testes do driver de experimentos de conflito (scripts/certification/run_conflict_experiment.py)
e do Safety Guard por proposta aplicado antes da arbitragem na RDLxApp.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

from src.conflict_types import XAppAction

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "run_conflict_experiment", ROOT / "scripts" / "certification" / "run_conflict_experiment.py"
)
driver = importlib.util.module_from_spec(SPEC)
sys.modules["run_conflict_experiment"] = driver
SPEC.loader.exec_module(driver)


@pytest.fixture(scope="module")
def catalog():
    return driver.load_catalog()


def _two_xapp_spec():
    return {
        "proposals": [
            {"xapp_id": "xslice", "gnb": 0, "parameter": "PRB_QUOTA", "value": 75, "priority": 90,
             "start": 10.0, "end": 12.0, "period": 1.0},
            {"xapp_id": "energy_saving", "gnb": 0, "parameter": "PRB_QUOTA", "value": 30, "priority": 65,
             "start": 10.05, "end": 12.0, "period": 1.0},
        ]
    }


def test_catalog_covers_all_scenarios(catalog):
    # S0–S7, S9–S15, G1–G2: pilha nativa (ns-3.48); S8: só bancada NORI (ns3 = null)
    assert sorted(catalog["scenarios"]) == sorted([f"S{i}" for i in range(16)] + ["G1", "G2"])
    for sid, spec in catalog["scenarios"].items():
        if sid == "S8":
            assert spec["ns3"] is None and spec["backend"] == "NORI_NS3"
        else:
            assert (ROOT / "simulations" / "ns3" / f"{spec['ns3']}.cc").exists()
        assert driver.expand_proposals(spec)


def test_expand_proposals_is_periodic_and_sorted():
    events = driver.expand_proposals(_two_xapp_spec())
    assert [e["t"] for e in events] == [10.0, 10.05, 11.0, 11.05]
    assert len({e["id"] for e in events}) == 4


def test_b0_applies_every_proposal_on_arrival():
    events = driver.expand_proposals(_two_xapp_spec())
    schedule, _ = driver.baseline_b0(events, 0.2)
    assert [(r["time_s"], r["value"]) for r in schedule] == [(10.0, 75), (10.05, 30), (11.0, 75), (11.05, 30)]


def test_b1_fifo_and_b2_priority_pick_one_per_target_at_window_close():
    events = driver.expand_proposals(_two_xapp_spec())
    fifo, _ = driver.baseline_b1(events, 0.2)
    prio, _ = driver.baseline_b2(events, 0.2)
    assert [(r["time_s"], r["xapp_id"]) for r in fifo] == [(10.2, "xslice"), (11.2, "xslice")]
    assert [(r["time_s"], r["xapp_id"]) for r in prio] == [(10.2, "xslice"), (11.2, "xslice")]

    # Energia chega primeiro, na mesma janela: FIFO e prioridade divergem
    reversed_spec = _two_xapp_spec()
    reversed_spec["proposals"][0]["start"] = 10.05
    reversed_spec["proposals"][1]["start"] = 10.0
    events = driver.expand_proposals(reversed_spec)
    fifo, _ = driver.baseline_b1(events, 0.2)
    prio, _ = driver.baseline_b2(events, 0.2)
    assert [r["xapp_id"] for r in fifo] == ["energy_saving", "energy_saving"]
    assert [r["xapp_id"] for r in prio] == ["xslice", "xslice"]


def test_b3_uses_real_hrdl_pipeline(catalog):
    spec, events, schedule, log = driver.decide("S1", "B3", catalog)
    assert schedule and all(r["xapp_id"] == "xslice" and r["value"] == 75 for r in schedule)
    resolutions = [res for w in log for res in w["resolutions"]]
    assert resolutions and all(r["strategy"] == "TVS" and r["conflict_type"] == "DIRECT" for r in resolutions)


def test_b3_blocks_unsafe_proposals_without_vetoing_legitimate_ones(catalog):
    _, _, b0, _ = driver.decide("S7", "B0", catalog)
    _, _, b3, _ = driver.decide("S7", "B3", catalog)
    assert any(r["parameter"] == "TX_POWER" and r["value"] == 60 for r in b0)
    assert not any(r["xapp_id"] == "rogue_xapp" for r in b3)
    assert any(r["xapp_id"] == "xslice" and r["parameter"] == "PRB_QUOTA" for r in b3)


def test_write_outputs_produces_schedule_readable_by_actuation(tmp_path, catalog):
    spec, events, schedule, log = driver.decide("S1", "B2", catalog)
    schedule_path, decision_path = driver.write_outputs(tmp_path, "S1", "B2", spec, events, schedule, log)
    lines = schedule_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "time_s,gnb,parameter,value,ue,xapp_id,action_id"
    assert len(lines) == len(schedule) + 1
    assert decision_path.exists()


def test_campaign_seed_parsing():
    spec = importlib.util.spec_from_file_location(
        "run_conflict_campaign", ROOT / "scripts" / "certification" / "run_conflict_campaign.py"
    )
    campaign = importlib.util.module_from_spec(spec)
    sys.modules["run_conflict_campaign"] = campaign
    spec.loader.exec_module(campaign)
    assert campaign.parse_seeds(["1001-1003", "1005", "1002"]) == [1001, 1002, 1003, 1005]


def test_campaign_run_state(tmp_path):
    campaign = sys.modules.get("run_conflict_campaign")
    if campaign is None:
        test_campaign_seed_parsing()
        campaign = sys.modules["run_conflict_campaign"]
    run = tmp_path / "nr_S1_B0_seed1"
    assert campaign.run_state(run) == "MISSING"
    run.mkdir()
    (run / "execution_manifest.json").write_text('{"run_status": "FAILED"}', encoding="utf-8")
    assert campaign.run_state(run) == "INCOMPLETE"  # sem hashes: interrompida
    (run / "hashes.sha256").write_text("x  y\n", encoding="utf-8")
    assert campaign.run_state(run) == "FAILED"
    (run / "execution_manifest.json").write_text('{"run_status": "SUCCESS"}', encoding="utf-8")
    assert campaign.run_state(run) == "SUCCESS"


def test_campaign_requeues_interrupted_and_failed_runs(tmp_path):
    campaign = sys.modules.get("run_conflict_campaign")
    if campaign is None:
        test_campaign_seed_parsing()
        campaign = sys.modules["run_conflict_campaign"]
    runs = tmp_path / "runs"

    def make(name, status, hashes=True):
        d = runs / name
        d.mkdir(parents=True)
        (d / "execution_manifest.json").write_text(f'{{"run_status": "{status}"}}', encoding="utf-8")
        if hashes:
            (d / "hashes.sha256").write_text("x  y\n", encoding="utf-8")

    make("nr_S1_B0_seed1", "SUCCESS")
    make("nr_S1_B1_seed1", "SUCCESS", hashes=False)  # interrompida
    make("nr_S1_B2_seed1", "FAILED")
    args = ([1], ["S1"], ["B0", "B1", "B2", "B3"], tmp_path)

    jobs = campaign.select_jobs(*args, retry_failed=False, stamp="T")
    assert jobs == [("S1", "B1", 1), ("S1", "B3", 1)]  # interrompida volta para a fila
    assert not (runs / "nr_S1_B1_seed1").exists()

    jobs = campaign.select_jobs(*args, retry_failed=True, stamp="T")
    assert jobs == [("S1", "B1", 1), ("S1", "B2", 1), ("S1", "B3", 1)]
    assert (tmp_path / "runs_failed" / "nr_S1_B2_seed1__T" / "hashes.sha256").exists()


def test_to_wsl_path_conversion():
    assert driver.to_wsl(Path("C:/dados/x/file.csv")) == "/mnt/c/dados/x/file.csv"


def test_rdl_xapp_drops_unsafe_proposal_before_arbitration():
    from src.rdl_xapp import RDLxApp

    app = RDLxApp()
    try:
        dispatched = []
        app.dispatcher.dispatch_control = lambda decision, *a, **k: dispatched.append(decision.selected_actions[0]) or "id"
        rogue = XAppAction("rogue_xapp", "gnb_safety", "TX_POWER", 60.0, 100)
        legit = XAppAction("xslice", "gnb_safety", "PRB_QUOTA", 70.0, 90)
        app._process_action_group([rogue, legit])
        assert [a.xapp_id for a in dispatched] == ["xslice"]
    finally:
        app.stop()


def test_b3_inter_cell_schedules_for_s4_and_s5(catalog):
    """Pré-registro 08, H9.1: cronograma determinístico do B3 nos conflitos entre células."""
    _, _, s4, _ = driver.decide("S4", "B3", catalog)
    assert [(e["gnb"], e["parameter"], e["time_s"]) for e in s4] == [(0, "HANDOVER", 15.2)]
    _, _, s4_b0, _ = driver.decide("S4", "B0", catalog)
    assert sum(1 for e in s4_b0 if e["parameter"] == "TX_POWER" and e["gnb"] == 1) == 10

    _, _, s5, _ = driver.decide("S5", "B3", catalog)
    assert [(e["xapp_id"], e["time_s"]) for e in s5] == [("traffic_steering", t) for t in (18.2, 20.2, 22.2, 24.2)]
    _, _, s5_b0, _ = driver.decide("S5", "B0", catalog)
    assert len(s5_b0) == 8
