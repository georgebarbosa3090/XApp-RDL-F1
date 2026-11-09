"""
Testes do certificador de evidências (scripts/certification/certify_chain.py).

Os diretórios de execução criados aqui são fixtures temporárias de teste: servem
apenas para exercitar as regras do certificador e nunca são evidência experimental.
"""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("certify_chain", ROOT / "scripts" / "certification" / "certify_chain.py")
cert = importlib.util.module_from_spec(SPEC)
sys.modules["certify_chain"] = cert  # dataclasses exigem o módulo registrado
SPEC.loader.exec_module(cert)

FLOWMONITOR = """<?xml version="1.0" ?>
<FlowMonitor><FlowStats>
<Flow flowId="1" txPackets="10" rxPackets="10" rxBytes="1000" txBytes="1000" lostPackets="0"/>
</FlowStats></FlowMonitor>
"""


@pytest.fixture(scope="module")
def policy():
    return cert.load_policy()


@pytest.fixture(scope="module")
def lock():
    return cert.load_versions_lock()


def _write_run(base: Path, run_id: str, manifest: dict, files: dict) -> Path:
    run_dir = base / run_id
    (run_dir / "raw").mkdir(parents=True)
    for rel, content in files.items():
        path = run_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    (run_dir / "execution_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    lines = []
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file()):
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(run_dir).as_posix()}")
    (run_dir / "hashes.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return run_dir


def _base_manifest(**extra):
    manifest = {
        "scenario": "scenario_rdl_direct_prb_conflict", "seed": 1001,
        "command": "./ns3 run ...", "run_status": "SUCCESS", "exit_code": 0,
        "started_at_utc": "2026-11-08T02:00:00Z", "finished_at_utc": "2026-11-08T02:00:30Z",
        "environment": {"os": "Ubuntu 22.04 LTS"},
    }
    manifest.update(extra)
    return manifest


def _rules(report):
    return {c.rule: c.status for c in report.checks}


def test_native_run_is_eligible_for_flowmonitor_only(tmp_path, policy, lock):
    native = lock["profile.native"]
    run_dir = _write_run(tmp_path, "native_conflict_seed1001", _base_manifest(
        source=["NS3_FLOWMONITOR"], backend="NS3_5GLENA",
        ns3_version="3.48", fiveg_lena_version="v5.1",
        ns3_commit=native["ns3_commit"][:7], nr_commit=native["nr_commit"][:7],
    ), {"raw/flowmonitor.xml": FLOWMONITOR})
    report = cert.certify_run(run_dir, policy, lock, [])
    rules = _rules(report)
    assert report.classification == "ELIGIBLE", report.failed()
    assert rules["R6.versions_lock"] == cert.PASS
    assert rules["R11.e2_artifacts"] == cert.NA
    gates = cert.evaluate_gates([report], lock)
    assert gates["G0"]["verdict"] == cert.CERTIFIED
    assert gates["G1"]["verdict"] == cert.NOT_CERTIFIED  # nativa não produz E2


def test_nori_pcap_only_run_does_not_certify_e2_gates(tmp_path, policy, lock):
    nori = lock["profile.nori"]
    run_dir = _write_run(tmp_path, "nori_rc_demo_seed1", _base_manifest(
        source=["NS3_FLOWMONITOR", "NORI_E2", "E2_PCAP"], backend="NORI_NS3",
        ns3_version="3.42", fiveg_lena_version="78b7179",
        ns3_commit=nori["ns3_commit"], nr_commit=nori["nr_commit"],
        nori_commit=nori["nori_commit"], e2sim_commit=nori["e2sim_commit"],
    ), {"raw/flowmonitor.xml": FLOWMONITOR, "raw/e2_sctp.pcap": b"\xd4\xc3\xb2\xa1" + b"\x00" * 60})
    report = cert.certify_run(run_dir, policy, lock, [], tmp_path / "e2_dissection")
    rules = _rules(report)
    assert rules["R11.e2_artifacts"] == cert.NA
    assert rules["R12.rc_correlation"] == cert.NA
    gates = cert.evaluate_gates([report], lock)
    assert gates["G1"]["verdict"] == cert.NOT_CERTIFIED
    assert gates["G4"]["verdict"] == cert.BLOCKED


def test_wrong_nori_commit_fails_versions_lock(tmp_path, policy, lock):
    run_dir = _write_run(tmp_path, "nori_bad_commit", _base_manifest(
        source=["NS3_FLOWMONITOR"], backend="NORI_NS3", ns3_version="3.48",
        fiveg_lena_version="v5.1", nori_commit="9b64c12",
    ), {"raw/flowmonitor.xml": FLOWMONITOR})
    report = cert.certify_run(run_dir, policy, lock, [])
    assert _rules(report)["R6.versions_lock"] == cert.FAIL


def test_synthetic_generator_run_ids_are_flagged(tmp_path, policy, lock):
    patterns = cert.synthetic_run_id_patterns()
    assert any(p.match("S1_B3_seed1001") for _, p in patterns)
    run_dir = _write_run(tmp_path, "S1_B3_seed1001", _base_manifest(
        source=["NS3_FLOWMONITOR"], backend="NS3_5GLENA", ns3_version="3.48", fiveg_lena_version="v5.1",
    ), {"raw/flowmonitor.xml": FLOWMONITOR})
    report = cert.certify_run(run_dir, policy, lock, patterns)
    assert report.classification == "SYNTHETIC_SUSPECT"
    assert not report.publication_eligible


def test_tampered_file_fails_hash_check(tmp_path, policy, lock):
    run_dir = _write_run(tmp_path, "native_tampered", _base_manifest(
        source=["NS3_FLOWMONITOR"], backend="NS3_5GLENA", ns3_version="3.48", fiveg_lena_version="v5.1",
    ), {"raw/flowmonitor.xml": FLOWMONITOR})
    (run_dir / "raw" / "flowmonitor.xml").write_text(FLOWMONITOR.replace('rxPackets="10"', 'rxPackets="99"'))
    report = cert.certify_run(run_dir, policy, lock, [])
    assert _rules(report)["R8.hashes"] == cert.FAIL
    assert not report.publication_eligible


def test_restricted_source_is_not_publishable(tmp_path, policy, lock):
    run_dir = _write_run(tmp_path, "fixture_run", _base_manifest(
        source=["CAUSAL_FIXTURE"], backend="NS3_5GLENA", ns3_version="3.48", fiveg_lena_version="v5.1",
    ), {"raw/flowmonitor.xml": FLOWMONITOR})
    report = cert.certify_run(run_dir, policy, lock, [])
    assert report.classification == "NON_PUBLICATION_SOURCE"


@pytest.mark.parametrize("started,has_v6,expected", [
    ("2026-11-09T03:21:49Z", True, "slice_effect_v6.json"),   # avaliação v6: depois do pré-registro
    ("2026-11-09T00:13:38Z", True, "slice_effect.json"),      # antes do pré-registro: sem efeito retroativo
    ("2026-11-09T03:21:49Z", False, "slice_effect.json"),     # sem arquivo v6 gravado na coleta
    (None, True, "slice_effect.json"),
])
def test_v6_effect_rule_is_adopted_without_retroactive_effect(tmp_path, started, has_v6, expected):
    (tmp_path / "slice_effect.json").write_text("{}", encoding="utf-8")
    if has_v6:
        (tmp_path / "slice_effect_v6.json").write_text("{}", encoding="utf-8")
    assert cert.effect_file_for(tmp_path, started) == expected
    assert "v6-ratio-apply" in cert.G4_EFFECT_RULES and "v1-throughput-share" not in cert.G4_EFFECT_RULES


class _FakeReport:
    def __init__(self, scenario, seed, baseline, source, backend="NORI_NS3", condition="", kpm_t0=True):
        self.facts = {"conflict_scenario": scenario, "scenario": "nori-rc-slicing-flowmon", "seed": seed,
                      "baseline": baseline, "backend": backend, "condition": condition,
                      "decision": {"source": source, "trigger_is_kpm_t0": kpm_t0, "pcap_control_sent_by_xapp": True}}


def _decision(r):
    return r.facts["decision"]


def test_g5_pairs_only_e2_runs_decided_by_their_own_baseline():
    src = cert.G5_DECISION_SOURCE
    runs = [_FakeReport("S8", s, b, src[b]) for s in range(5001, 5031) for b in cert.G5_BASELINES]
    units = cert.g5_paired_units(runs, _decision)
    assert sum(1 for bs in units.values() if set(cert.G5_BASELINES) <= bs) == 30
    # Fonte errada (Control fixo rotulado de B1), pilha nativa ou outra condição não formam par
    bad = [_FakeReport("S8", 6001, "B0", src["B0"]), _FakeReport("S8", 6001, "B1", "FIXED_PROBE"),
           _FakeReport("S8", 6001, "B2", src["B2"]), _FakeReport("S8", 6001, "B3", src["B3"], backend="NS3_5GLENA"),
           _FakeReport("S8", 6002, "B0", src["B0"]), _FakeReport("S8", 6002, "B1", src["B1"]),
           _FakeReport("S8", 6002, "B2", src["B2"]), _FakeReport("S8", 6002, "B3", src["B3"], condition="_bw50")]
    units = cert.g5_paired_units(bad, _decision)
    assert not any(set(cert.G5_BASELINES) <= bs for bs in units.values())
