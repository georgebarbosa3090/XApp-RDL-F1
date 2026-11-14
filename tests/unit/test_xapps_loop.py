"""Malha fechada na bancada NORI com xApps reais (docs/16 §10.2): janela de propostas e decisão por baseline."""
import json

import pytest

from src.closed_loop.xapps_loop import ProposalWindow, decide_xapps

MEID = "gnbd_001_001_00019b_0"
NODE = {"RRU.PrbUsedDl": 90, "RRU.PrbAvailDl": 10}
UES = [{"ue_id": 1, "measurements": {"DRB.NetworkSlicing.SST": 1}},
       {"ue_id": 2, "measurements": {"DRB.NetworkSlicing.SST": 2}}]


def msg(xapp, value, prio, param="PRB_QUOTA", node=MEID):
    return json.dumps({"xapp_id": xapp, "node_id": node, "parameter": param, "value": value, "priority": prio}).encode()


def window():
    w = ProposalWindow()
    w.add(msg("xslice", 40, 90), 1.0, MEID)
    w.add(msg("xslice", 25, 90), 1.1, MEID)                       # a última da xApp vale
    w.add(msg("embb_throughput", 80, 60), 1.2, MEID)
    w.add(msg("ranslicer_greenran", 30, 75, param="TX_POWER"), 1.3, MEID)   # não atuável no NORI
    assert w.add(b"lixo", 1.4) is None and w.rejected == 1
    return w


def test_window_keeps_last_per_xapp_and_drains():
    w = window()
    got = w.drain()
    assert [(p["xapp_id"], p["value"]) for p in got] == [("xslice", 25), ("embb_throughput", 80), ("ranslicer_greenran", 30)]
    assert w.drain() == []


@pytest.mark.parametrize("baseline,expected", [("B1", 25.0), ("B2", 25.0)])
def test_baselines_pick_one_prb_control(baseline, expected):
    r = decide_xapps(baseline, MEID, NODE, UES, window().drain())
    assert r["mode"] == "xapps" and r["actuated"]["value"] == expected and len(r["control_sequence"]) == 1
    assert any(s["parameter"] == "TX_POWER" and not s["actuable"] for s in r["not_actuated"])


def test_b0_sends_every_prb_action_in_arrival_order():
    r = decide_xapps("B0", MEID, NODE, UES, window().drain())
    assert [a["value"] for a in r["actuated_sequence"]] == [25.0, 80.0] and r["actuated"]["value"] == 80.0


def test_empty_window_and_unknown_baseline():
    assert decide_xapps("B3", MEID, NODE, UES, [])["control_sequence"] == []
    with pytest.raises(ValueError):
        decide_xapps("B9", MEID, NODE, UES, [])


def test_b3_uses_the_rdl_pipeline():
    r = decide_xapps("B3", MEID, NODE, UES, window().drain())
    assert r["decision_source"] == "H_RDL" and r["resolutions"]
    assert r["actuated"] is None or r["actuated"]["value"] in (25.0, 80.0)
