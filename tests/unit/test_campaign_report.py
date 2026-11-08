"""Testes do gerador do relatório da campanha (scripts/certification/generate_campaign_report.py)."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "generate_campaign_report", ROOT / "scripts" / "certification" / "generate_campaign_report.py"
)
report = importlib.util.module_from_spec(_spec)
sys.modules["generate_campaign_report"] = report
_spec.loader.exec_module(report)


def _run(scenario, baseline, seed, **metrics):
    base = {"thp_pre": 1.0, "thp_conflict": 1.0, "thp_post": 1.0, "delay_conflict_ms": 10.0,
            "actions_applied": 5, "handovers": 0, "unsafe_applied": 0, "oscillations": 0}
    base.update(metrics)
    return {"run_id": f"nr_{scenario}_{baseline}_seed{seed}", "scenario": scenario, "baseline": baseline,
            "seed": seed, "run_status": "SUCCESS", **base}


def _index(rows):
    return {(r["scenario"], r["baseline"], r["seed"]): r for r in rows}


def test_paired_rules():
    rows = []
    for seed, (b0, b3) in enumerate([(20.0, 10.0), (22.0, 11.0), (21.0, 10.5)], start=1):
        rows += [_run("S6", "B0", seed, delay_conflict_ms=b0), _run("S6", "B3", seed, delay_conflict_ms=b3)]
    runs = _index(rows)
    assert report.evaluate_check_in("S6", ("paired", "delay_conflict_ms", "B3", "B0", "<0"), runs)[0] == report.PASS
    assert report.evaluate_check_in("S6", ("paired", "delay_conflict_ms", "B3", "B0", ">0"), runs)[0] == report.FAIL
    assert report.evaluate_check_in("S6", ("paired", "delay_conflict_ms", "B3", "B0", "=0"), runs)[0] == report.FAIL
    assert report.evaluate_check_in("S6", ("paired", "delay_conflict_ms", "B3", "B0", "<=0"), runs)[0] == report.PASS


def test_paired_rules_inconclusive_and_zero():
    rows = []
    for seed, (b0, b3) in enumerate([(10.0, 12.0), (10.0, 8.0), (10.0, 10.5)], start=1):
        rows += [_run("S2", "B0", seed, delay_conflict_ms=b0), _run("S2", "B3", seed, delay_conflict_ms=b3),
                 _run("S2", "B1", seed, delay_conflict_ms=b3)]
    runs = _index(rows)
    assert report.evaluate_check_in("S2", ("paired", "delay_conflict_ms", "B3", "B0", "<0"), runs)[0] == report.INCONCLUSIVE
    # "não piora" com IC contendo zero e média desfavorável (+0,17 ms): não demonstrado
    assert report.evaluate_check_in("S2", ("paired", "delay_conflict_ms", "B3", "B0", "<=0"), runs)[0] == report.INCONCLUSIVE
    assert report.fmt(-0.0) == "0,00" and report.fmt(-0.001) == "-0,0010" and report.fmt(2e-7) == "2,0e-07"
    res, evidence = report.evaluate_check_in("S2", ("paired", "delay_conflict_ms", "B3", "B1", "=0"), runs)
    assert res == report.PASS and "zero em todas" in evidence


def test_all_seeds_rule_and_verdict():
    runs = _index([_run("S7", "B3", s, unsafe_applied=0) for s in (1, 2)] +
                  [_run("S7", "B0", s, unsafe_applied=10 if s == 1 else 0) for s in (1, 2)])
    assert report.evaluate_check_in("S7", ("all", "unsafe_applied", "B3", "==", 0), runs)[0] == report.PASS
    assert report.evaluate_check_in("S7", ("all", "unsafe_applied", "B0", ">", 0), runs)[0] == report.FAIL
    assert report.hypothesis_verdict([report.PASS, report.PASS]) == report.SUPPORTED
    assert report.hypothesis_verdict([report.PASS, report.INCONCLUSIVE]) == report.OPEN
    assert report.hypothesis_verdict([report.INCONCLUSIVE, report.FAIL]) == report.REFUTED


def test_build_report_has_per_seed_tables_commands_and_hypotheses(tmp_path):
    rows = []
    for seed in (1001, 1002):
        for bl in ("B0", "B1", "B2", "B3"):
            rows.append(_run("S7", bl, seed, unsafe_applied=0 if bl == "B3" else 10, thp_conflict=5.0 + seed % 2))
    analysis = {"generated_at_utc": "2026-01-01T00:00:00Z", "runs": rows, "skipped": [],
                "aggregate": [{"scenario": "S7", "baseline": bl, "n": 2,
                               **{m: {"mean": 1.0, "sd": 0.0, "ci95": 0.0} for m, _ in report.METRICS}}
                              for bl in ("B0", "B1", "B2", "B3")]}
    manifests = {r["run_id"]: {"command": f"./ns3 run 'scratch/scenario_rdl_fault_injection --seed={r['seed']}'",
                               "run_status": "SUCCESS", "started_at_utc": "2026-01-01T00:00:00Z",
                               "finished_at_utc": "2026-01-01T00:01:00Z", "scenario_sha256": "a" * 64,
                               "action_schedule_sha256": ("b" if r["baseline"] == "B3" else "c") * 64,
                               "ns3_version": "3.48", "repo_git_sha": "abc1234"} for r in rows}
    catalog = json.loads(report.CATALOG.read_text(encoding="utf-8"))
    path = tmp_path / "conflict_analysis_x.json"
    text = report.build_report(analysis, path, catalog, manifests, None, None, [("nr_x__T", "FAILED", "msg")])
    assert "### 6.1 Semente 1001" in text and "### 6.2 Semente 1002" in text
    assert "### H7 (S7, ação insegura): SUPORTADA" in text
    assert "run_conflict_campaign.py" in text and "source ~/.venvs/xapp-rdl/bin/activate" in text
    assert "B0 = B1 = B2 · B3" in text
    assert "./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1001'" in text
    assert "`nr_x__T`" in text
