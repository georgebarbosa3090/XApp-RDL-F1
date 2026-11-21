"""
RDL hierárquica na malha fechada (baseline N12: RDL-N1 + RDL-N2 da Fase 2) e governança no Non-RT RIC simulado
(rApp de governança, A1 20000, e A1 20002 do modelo). Sem ns-3. Exige o repositório da Fase 2 ao lado.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "scripts" / "certification"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import run_conflict_experiment as rce  # noqa: E402
from scripts.closed_loop import orchestrator as orc  # noqa: E402

pytestmark = pytest.mark.skipif(not (orc.F2_ROOT / "cardl" / "hierarchy.py").exists(),
                                reason="repositório da Fase 2 (RDL_F2_ROOT) ausente")
CAT = rce.load_catalog()


def _proposal(t, xapp, gnb, parameter, value, priority, k, ue=-1):
    return {"t": t, "xapp_id": xapp, "gnb": gnb, "parameter": parameter, "value": value, "priority": priority,
            "ue": ue, "id": f"{xapp}-g{gnb}-{parameter}-{t:.3f}-{k}"}


def _kpm(t, cells=2, n=4):
    return {"t": t, "cells": [{"gnb": c, "cell_id": c + 1, "prb_util": 0.5} for c in range(cells)],
            "ues": [{"ue": u, "cell_id": u % cells + 1, "gnb": u % cells, "connected": True, "thp_mbps": 1.0,
                     "delay_ms": 10.0, "sinr_db": 8.0, "rsrp_dbm": {"1": -80.0, "2": -82.0}} for u in range(n)]}


def test_n12_routes_by_complexity_and_logs_the_trace(monkeypatch):
    monkeypatch.delenv("CARDL_SELECTION", raising=False)
    monkeypatch.setenv("CARDL_SELECTION", str(Path(orc.F2_ROOT) / "experiments" / "training" / "nao_existe.json"))
    monkeypatch.setattr(orc, "hierarchical_factory", _factory_without_model)
    baseline = orc.WindowBaseline("N12")
    try:
        assert type(baseline.stream.app.reasoning).__name__ == "HierarchicalReasoning"
        # indireto (teto de PRB contra potência no mesmo gNB): C = 2,2 -> RDL-N2, sem modelo -> reserva na RDL-N1
        group = [_proposal(1.0, "xslice", 0, "PRB_QUOTA", 30.0, 80, 1),
                 _proposal(1.0, "energy_saving", 0, "TX_POWER", 10.0, 65, 2)]
        _, entry = baseline.decide(group, 1.0)
        traces = [r for r in entry["resolutions"] if "level" in r]
        assert traces and traces[0]["level"] == "N2" and traces[0]["fallback_reason"] == "sem checkpoint"
        assert traces[0]["t_route"] == 1.0          # relógio simulado do executor
    finally:
        baseline.close()


def _factory_without_model():
    """Fábrica real da Fase 2, sem checkpoint (testa o roteamento sem PyTorch)."""
    if str(orc.F2_ROOT) not in sys.path:
        sys.path.insert(0, str(orc.F2_ROOT))
    from cardl.hierarchy import HierarchicalReasoning
    from cardl.engine import install_reasoning

    def attach(app, clock):
        reasoning = HierarchicalReasoning(app.memory, config={}, inter_cell_rules=app.inter_cell_rules, clock=clock)
        install_reasoning(app, reasoning)
        return reasoning

    return attach, {"checkpoint": None}


def test_governance_rapp_and_model_policy_reach_the_rdl(monkeypatch, tmp_path):
    spec = dict(CAT["scenarios"]["G1"], _id="G1")
    topo = tmp_path / "topo.json"
    topo.write_text(json.dumps(spec["topology"]), encoding="utf-8")
    monkeypatch.setenv("RDL_TOPOLOGY_FILE", str(topo))
    monkeypatch.setattr(orc, "hierarchical_factory", _factory_without_model)
    drivers = orc.build_full_drivers(spec)
    baseline = orc.WindowBaseline("N12")
    try:
        rapp = orc.RAppStep(drivers, baseline, {}, 2, orc.ue_sst_map(spec, {"ue_sst_groups": [1, 2]}))
        assert rapp.governance_enabled
        app = baseline.stream.app
        # relatório com uma xApp barrada 5 vezes pelo Safety Guard: o rApp de governança a põe em quarentena
        view = app._governance_view

        def report():
            r = view()
            r["rejections"] = {"by_xapp": {"rogue": {"SAFETY": 5}}}
            return r

        monkeypatch.setattr(app, "_governance_view", report)
        ev = rapp.step(_kpm(0.2))
        assert "20002->RDL" in ev["delivered"] and "20000->RDL" in ev["delivered"]
        assert app.reasoning.marl_enabled is True
        assert ev["governanca"]["20000"]["body"]["xapp_modes"] == ["rogue:QUARANTINED"]
        assert app.a1_policies.effective_policy().get("xapp_modes") == ["rogue:QUARANTINED"]
    finally:
        baseline.close()


def test_governance_can_be_disabled_and_b0_has_none():
    b3 = orc.WindowBaseline("B3")
    b0 = orc.WindowBaseline("B0")
    try:
        assert not orc.RAppStep([], b3, {}, 2, {}, governance=False).governance_enabled
        assert not orc.RAppStep([], b0, {}, 2, {}).governance_enabled       # sem RDL no laço
        assert orc.RAppStep([], b3, {}, 2, {}).governance_enabled
    finally:
        b3.close()
        b0.close()
