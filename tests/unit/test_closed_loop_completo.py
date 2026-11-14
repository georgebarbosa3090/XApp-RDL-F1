"""
Modo --xapps completo do orquestrador (docs/16): todas as xApps de cada cenário (pelo papel no catálogo e
pelo closed_loop.json) recebem KPM e propõem; sem ns-3.
"""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "scripts" / "certification"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import run_conflict_experiment as rce  # noqa: E402
from scripts.closed_loop import orchestrator as orc  # noqa: E402

CAT = rce.load_catalog()
CFG = json.loads(orc.CLOSED_LOOP_CFG.read_text(encoding="utf-8"))


def _kpm(t, spec, cells=3):
    n = sum(int(g.split(",")[0]) for g in next(a for a in spec["args"] if a.startswith("--ueGroups=")).split("=", 1)[1].split(";"))
    ues = []
    for u in range(n):
        g = u % cells
        rsrp = {str(c + 1): (-80.0 if c == g else -86.0 - 3 * c) for c in range(cells)}
        ues.append({"ue": u, "cell_id": g + 1, "gnb": g, "connected": True, "thp_mbps": 0.5, "delay_ms": 15.0,
                    "sinr_db": 8.0, "rsrp_dbm": rsrp})
    return {"t": t, "cells": [{"gnb": c, "cell_id": c + 1, "prb_util": 0.05 + 0.4 * (c == 0)} for c in range(cells)],
            "ues": ues}


@pytest.mark.parametrize("scenario", sorted(CFG["scenarios"]))
def test_full_drivers_build_and_propose(scenario, monkeypatch, tmp_path):
    spec = dict(CAT["scenarios"][scenario], _id=scenario)
    if spec.get("topology"):
        topo = tmp_path / "topo.json"
        topo.write_text(json.dumps(spec["topology"]), encoding="utf-8")
        monkeypatch.setenv("RDL_TOPOLOGY_FILE", str(topo))
    roles = {p["xapp_id"] for p in spec["proposals"]}
    if "traffic_steering" in roles:   # sem a opção, o papel usa o TS original (processo; testado em test_ts_original)
        from scripts.closed_loop.ts_driver import TsOriginalDriver
        assert any(isinstance(d, TsOriginalDriver) for d in orc.build_full_drivers(spec, "t"))
    # aqui, as xApps em Python: o TS entra pela derivada (controle pareado)
    drivers = orc.build_full_drivers(spec, "t", derivado=("traffic_steering",))
    assert drivers, scenario
    props = []
    for k in range(1, 60):
        for d in drivers:
            got = d.on_kpm(_kpm(round(0.2 * k, 3), spec))
            for p in got:
                assert {"t", "xapp_id", "gnb", "parameter", "value", "priority", "ue", "id"} <= set(p)
                assert p["parameter"] in ("PRB_QUOTA", "TX_POWER", "HANDOVER", "CELL_STATE")
            props += got
            d.on_decision(set())
    # as xApps leem o KPM: com carga e sinal sintéticos, ao menos uma propõe em cada cenário
    assert props or roles <= {"energy_saving", "energy_saving_ru0", "energy_saving_ru1", "fault_injector"}, scenario


def test_ue_sst_map_from_groups():
    spec = CAT["scenarios"]["G1"]
    m = orc.ue_sst_map(spec, [1, 2])
    assert m[0] == 1 and m[5] == 1 and m[6] == 2 and len(m) == 36


def test_rapp_delivers_a1_policies_to_rdl_and_greenran_xapps(monkeypatch, tmp_path):
    spec = dict(CAT["scenarios"]["G1"], _id="G1")
    topo = tmp_path / "topo.json"
    topo.write_text(json.dumps(spec["topology"]), encoding="utf-8")
    monkeypatch.setenv("RDL_TOPOLOGY_FILE", str(topo))
    drivers = orc.build_full_drivers(spec)
    baseline = orc.WindowBaseline("B3")
    try:
        rapp = orc.RAppStep(drivers, baseline, {}, 2, orc.ue_sst_map(spec, [1, 2]))
        ev = rapp.step(_kpm(0.2, spec, cells=2))
        assert sorted(ev["delivered"]) == ["20001->RDL", "21000->ranslicer_greenran", "21001->energysaver_greenran"]
        assert rapp.step(_kpm(0.4, spec, cells=2)) is None            # próximo passo só depois de 10 s
        saver = next(d.app for d in drivers if getattr(d, "app", None) and d.app.XAPP_ID == "energysaver_greenran")
        assert saver.policy()["es_sleep_start_hour"] == 22               # política 21001 aplicada
        assert "energy_weight" in str(ev["policies"]["20001"])
    finally:
        baseline.close()
