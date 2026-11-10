"""
Testes do porte dos cenários S0–S8 para a bancada NORI (src/closed_loop/catalog_loop.py), da
formatação ao vivo dos eventos da xApp e da separação nativa × NORI no catálogo.
"""

import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from src.closed_loop import catalog_loop as cl

ROOT = Path(__file__).resolve().parents[2]
CATALOG = cl.load_catalog(ROOT / "simulations" / "ns3" / "conflicts" / "catalog.json")
NODE = {"RRU.PrbUsedDl": 236, "RRU.PrbAvailDl": 139}
UES = [{"ue_id": 1, "measurements": {"DRB.NetworkSlicing.SST": 1}},
       {"ue_id": 2, "measurements": {"DRB.NetworkSlicing.SST": 2}}]


def decide(scenario):
    return cl.decide_catalog(scenario, "gnb_268_341_00000001", NODE, UES, CATALOG)


def test_catalog_scenarios_and_s8_is_nori_only():
    assert sorted(CATALOG["scenarios"]) == sorted([f"S{i}" for i in range(16)] + ["G1", "G2"])
    assert CATALOG["scenarios"]["S8"]["ns3"] is None and CATALOG["scenarios"]["S8"]["backend"] == "NORI_NS3"
    assert all(spec["ns3"] for sid, spec in CATALOG["scenarios"].items() if sid != "S8")


def test_actions_keep_the_source_gnb_in_the_target():
    acts = cl.catalog_actions(CATALOG, "S6", "gnb")
    assert {a.node_id for a in acts} == {"gnb#g0", "gnb#g1", "gnb#g2", "gnb#g3"}
    assert len(acts) == 8          # primeira ocorrência por xApp/gNB/parâmetro


@pytest.mark.parametrize("scenario,actuated,quotas", [
    ("S0", ("xslice", 80.0), [80, 20]),
    ("S1", ("xslice", 75.0), [75, 25]),
    ("S2", ("xslice", 80.0), [80, 20]),
    ("S3", None, []),
    ("S4", None, []),
    ("S5", None, []),
    ("S6", ("xslice", 85.0), [85, 15]),
    ("S7", ("xslice", 70.0), [70, 30]),
    ("S8", ("embb_throughput", 80.0), [80, 20]),
])
def test_hrdl_decision_and_nori_actuation_per_scenario(scenario, actuated, quotas):
    r = decide(scenario)
    assert r["decision_source"] == "H_RDL" and r["mode"] == "catalog"
    got = (r["actuated"]["xapp_id"], r["actuated"]["value"]) if r["actuated"] else None
    assert got == actuated
    assert [q["max_prb_ratio"] for q in r["quotas"]] == quotas


def test_non_actuable_reasons():
    s3 = decide("S3")
    assert s3["not_actuated"][0]["parameter"] == "TX_POWER"
    assert "E2SM-RC do NORI" in s3["not_actuated"][0]["reason"]
    s5 = decide("S5")
    reasons = {x["target"].rsplit("#", 1)[-1]: x["reason"] for x in s5["not_actuated"]}
    assert "log" in reasons["g0"]
    # Ping-pong entre células (regra HANDOVER_PING_PONG): o handover de volta do Load
    # Balancer perde para o do Traffic Steering (prioridade 80 > 70) e nem chega ao NORI.
    assert "g1" not in reasons
    assert s5["not_selected"] == ["S5-load_balancer-g1-HANDOVER"]


def test_inter_cell_conflict_in_s4_blocks_power_cut_on_handover_target():
    # Regra HANDOVER_INTO_REDUCED_CELL: o Energy Saving derrubaria a potência da gNB 1
    # (0 dBm) enquanto o Traffic Steering move UEs para ela; vence o handover (80 > 65).
    s4 = decide("S4")
    assert s4["not_selected"] == ["S4-energy_saving-g1-TX_POWER"]
    assert [x["parameter"] for x in s4["not_actuated"]] == ["HANDOVER"]


def test_safety_guard_blocks_rogue_xapp_in_s7():
    r = decide("S7")
    assert set(r["not_selected"]) == {"S7-rogue_xapp-g0-TX_POWER", "S7-rogue_xapp-g1-PRB_QUOTA"}


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_format_xapp_events_renders_decision_control_and_ack():
    fx = _load("format_xapp_events", "scripts/observe/format_xapp_events.py")
    decision = decide("S2")
    events = [
        {"t_utc": "2026-11-08T20:00:00.000Z", "event": "kpm", "format": 3,
         "ues": [{"ue_id": 1, "DRB.NetworkSlicing.SST": 1, "RRU.PrbUsedDl": 119}]},
        {"t_utc": "2026-11-08T20:00:01.000Z", "event": "control_request", "decision_source": "H_RDL",
         "decision": decision, "ric_requestor_id": 1003, "ric_instance_id": 1, "ran_function_id": 300,
         "quotas": decision["quotas"], "rmr_ok": True, "length": 116},
        {"t_utc": "2026-11-08T20:00:01.002Z", "event": "control_outcome", "outcome": "ACK",
         "ric_requestor_id": 1003, "ric_instance_id": 1, "correlated_with_request": True, "latency_ms": 2.0},
    ]
    buf = io.StringIO()
    with redirect_stdout(buf):
        for ev in events:
            fx.fmt(ev, False)
    text = buf.getvalue()
    assert "KPM UEs: UE 1 SST 1 PRB 119" in text
    assert "INDIRECT->EEVS" in text and "cenário S2" in text
    assert "RIC Control -> nó: RICrequestID 1003/1" in text and "SST 1 teto 80 %" in text
    assert "RIC Control ACK do nó" in text


def test_native_campaign_rejects_nori_only_s8(capsys):
    camp = _load("run_conflict_campaign", "scripts/certification/run_conflict_campaign.py")
    with pytest.raises(SystemExit):
        camp.main(["--scenarios", "S8", "--seeds", "1001"])
    assert "só da bancada NORI" in capsys.readouterr().err


@pytest.mark.parametrize("baseline,sequence,final", [
    ("B0", [80.0, 25.0], [25, 75]),   # sem coordenação: as duas, na ordem de chegada (desempate pelo id); vale a última
    ("B1", [80.0], [80, 20]),         # FIFO: a primeira a chegar (embb_throughput, pelo id)
    ("B2", [25.0], [25, 75]),         # prioridade estática: xslice (90) sobre embb_throughput (60)
])
def test_baselines_on_s8_follow_the_native_semantics(baseline, sequence, final):
    r = cl.decide_baseline("S8", baseline, "gnb", NODE, UES, CATALOG)
    assert r["decision_source"] == f"BASELINE_{baseline}" and r["baseline"] == baseline
    assert [a["value"] for a in r["actuated_sequence"]] == sequence
    assert len(r["control_sequence"]) == len(sequence)
    assert [q["max_prb_ratio"] for q in r["quotas"]] == final


def test_baselines_match_the_native_driver_on_the_first_window():
    drv = _load("run_conflict_experiment", "scripts/certification/run_conflict_experiment.py")
    for scenario in ("S1", "S7"):
        spec = CATALOG["scenarios"][scenario]
        events = drv.expand_proposals(spec)
        first_t = events[0]["t"]
        for baseline, fn in (("B1", drv.baseline_b1), ("B2", drv.baseline_b2)):
            schedule, _ = fn([e for e in events if e["t"] < first_t + 0.2], 0.2)
            native = [s["value"] for s in schedule if s["parameter"] == "PRB_QUOTA" and s["gnb"] == 0]
            ours = [a["value"] for a in cl.decide_baseline(scenario, baseline, "gnb", NODE, UES, CATALOG)["actuated_sequence"]]
            assert ours == native[:1], (scenario, baseline, ours, native)


def test_unknown_baseline_is_rejected():
    with pytest.raises(ValueError):
        cl.decide_baseline("S8", "B9", "gnb", NODE, UES, CATALOG)
