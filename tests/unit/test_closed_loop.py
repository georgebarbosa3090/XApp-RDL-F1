"""
Testes da malha fechada sem ns-3 (docs/16, etapa E1): driver de reprodução do catálogo e baselines
por janela do orquestrador, contra o executor de cronograma (scripts/certification/run_conflict_experiment.py).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "scripts" / "certification"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import run_conflict_experiment as rce  # noqa: E402
from scripts.closed_loop.drivers import ReplayDriver  # noqa: E402
from scripts.closed_loop.orchestrator import WindowBaseline  # noqa: E402

CATALOG = rce.load_catalog()
WINDOW = float(CATALOG.get("decision_window_s", 0.2))


def _closed_loop_schedule(scenario, baseline):
    """Simula o laço do orquestrador: um KPM a cada janela, propostas do driver, decisão do baseline."""
    spec = CATALOG["scenarios"][scenario]
    events = rce.expand_proposals(spec)
    driver = ReplayDriver(events, WINDOW)
    decider = WindowBaseline(baseline)
    t_end = max(e["t"] for e in events) + 2 * WINDOW
    schedule = []
    try:
        k = 1
        while k * WINDOW <= t_end + 1e-9:
            t = round(k * WINDOW, 6)
            props = sorted(driver.on_kpm({"t": t}), key=lambda e: (e["t"], e["id"]))
            actions, _ = decider.decide(props, t)
            schedule += [(t, a["id"]) for a in actions]
            k += 1
    finally:
        decider.close()
    return events, schedule


def test_replay_delivers_each_proposal_once_in_its_window():
    events = rce.expand_proposals(CATALOG["scenarios"]["S6"])
    driver = ReplayDriver(events, WINDOW)
    seen = []
    for k in range(1, 400):
        for e in driver.on_kpm({"t": round(k * WINDOW, 6)}):
            assert k * WINDOW - WINDOW - 1e-9 <= e["t"] < k * WINDOW + 1e-9
            seen.append(e["id"])
    assert sorted(seen) == sorted(e["id"] for e in events)


@pytest.mark.parametrize("scenario", ["S1", "S5", "S8", "S12", "G1"])
@pytest.mark.parametrize("baseline", ["B1", "B2"])
def test_window_baselines_match_schedule_executor(scenario, baseline):
    _, closed = _closed_loop_schedule(scenario, baseline)
    _, _, schedule, _ = rce.decide(scenario, baseline, CATALOG)
    assert closed == [(round(r["time_s"], 6), r["action_id"]) for r in schedule]


@pytest.mark.parametrize("scenario", ["S2", "S8", "S13"])
def test_hrdl_stream_matches_b3m_schedule(scenario, monkeypatch):
    monkeypatch.delenv("RDL_TOPOLOGY_FILE", raising=False)
    if CATALOG["scenarios"][scenario].get("topology"):
        pytest.skip("cenário com topologia: o orquestrador passa o arquivo de topologia; coberto na E1 com ns-3")
    _, closed = _closed_loop_schedule(scenario, "B3M")
    _, _, schedule, _ = rce.decide(scenario, "B3M", CATALOG)
    assert closed == [(round(r["time_s"], 6), r["action_id"]) for r in schedule]


def test_b0_applies_every_proposal_at_window_close():
    events, closed = _closed_loop_schedule("S7", "B0")
    assert sorted(i for _, i in closed) == sorted(e["id"] for e in events)
    for t, i in closed:
        e = next(e for e in events if e["id"] == i)
        assert e["t"] < t <= e["t"] + WINDOW + 1e-9
