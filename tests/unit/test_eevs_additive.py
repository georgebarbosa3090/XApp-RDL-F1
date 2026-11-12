"""EEVS com agregação aditiva (achado 55; pré-registro 09) e o baseline B3A do driver nativo."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from src.core.reasoning import Reasoning
from src.infrastructure.memory_module import MemoryModule

ROOT = Path(__file__).resolve().parents[2]


def _driver():
    spec = importlib.util.spec_from_file_location("run_conflict_experiment", ROOT / "scripts/certification/run_conflict_experiment.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_conflict_experiment"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_invalid_aggregation_is_rejected(monkeypatch):
    monkeypatch.delenv("RDL_EEVS_AGGREGATION", raising=False)
    assert Reasoning(MemoryModule()).eevs_aggregation == "additive"                  # padrão desde o pré-registro 09
    with pytest.raises(ValueError):
        Reasoning(MemoryModule(), config={"eevs_aggregation": "median"})
    monkeypatch.setenv("RDL_EEVS_AGGREGATION", "additive")
    assert Reasoning(MemoryModule()).eevs_aggregation == "additive"


def test_b3a_admits_the_evacuation_handover_in_s13(monkeypatch):
    monkeypatch.delenv("RDL_EEVS_AGGREGATION", raising=False)
    drv = _driver()
    catalog = json.loads((ROOT / "simulations/ns3/conflicts/catalog.json").read_text(encoding="utf-8"))
    params = lambda sched: sorted({(r["parameter"], r["xapp_id"]) for r in sched})
    _, _, mean, _ = drv.decide("S13", "B3M", catalog)
    _, _, additive, _ = drv.decide("S13", "B3", catalog)
    _, _, alias, _ = drv.decide("S13", "B3A", catalog)
    assert params(alias) == params(additive)                                         # B3A = apelido do B3
    assert params(mean) == [("CELL_STATE", "fault_injector")]                      # achado 55
    assert params(additive) == [("CELL_STATE", "fault_injector"), ("HANDOVER", "traffic_steering")]
    _, _, s0_mean, _ = drv.decide("S0", "B3M", catalog)
    _, _, s0_add, _ = drv.decide("S0", "B3", catalog)
    assert params(s0_mean) == params(s0_add)                                       # conflito direto: TVS, igual
    import os
    assert "RDL_EEVS_AGGREGATION" not in os.environ                                # o decisor restaura o ambiente
