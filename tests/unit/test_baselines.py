# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""Regra única dos baselines B0–B2 (src/core/baselines.py) e o uso dela no orquestrador da malha fechada."""

import sys
from pathlib import Path

import pytest

from src.core import baselines as bl

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "scripts" / "certification"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _p(pid, t, target, priority):
    return {"id": pid, "t": t, "gnb": target, "parameter": "PRB_QUOTA", "ue": -1, "priority": priority}


PROPOSALS = [_p("late-high", 2.0, 0, 90), _p("early-low", 1.0, 0, 60), _p("other", 1.5, 1, 50)]
TARGET = (lambda e: (e["gnb"], e["parameter"], e["ue"]))
ARRIVAL = (lambda e: (e["t"], e["id"]))
PRIORITY = (lambda e: e["priority"])


def test_b0_keeps_everything_in_arrival_order():
    assert [e["id"] for e in bl.select(PROPOSALS, "B0", TARGET, ARRIVAL, PRIORITY)] == ["early-low", "other", "late-high"]


def test_b1_first_arrival_per_target_in_first_appearance_order():
    assert [e["id"] for e in bl.select(PROPOSALS, "B1", TARGET, ARRIVAL, PRIORITY)] == ["early-low", "other"]


def test_b2_highest_priority_then_arrival():
    tie = PROPOSALS + [_p("early-high", 0.5, 0, 90)]
    assert [e["id"] for e in bl.select(tie, "B2", TARGET, ARRIVAL, PRIORITY)] == ["early-high", "other"]


def test_unknown_per_target_baseline():
    with pytest.raises(ValueError):
        bl.choose(PROPOSALS, "B3", ARRIVAL, PRIORITY)


@pytest.mark.parametrize("baseline, rule, ids", [
    ("B0", bl.B0_AT_WINDOW_CLOSE, ["early-low", "other", "late-high"]),
    ("B1", "fifo-per-target", ["early-low", "other"]),
    ("B2", "static-priority-per-target", ["late-high", "other"]),
])
def test_orchestrator_window_baseline_uses_the_shared_rule(baseline, rule, ids):
    from scripts.closed_loop.orchestrator import WindowBaseline
    wb = WindowBaseline(baseline)
    winners, entry = wb.decide(PROPOSALS, 2.2)
    assert [w["id"] for w in winners] == ids and entry["rule"] == rule
    wb.close()
