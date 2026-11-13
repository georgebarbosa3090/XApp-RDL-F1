# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""Proveniência do código nos manifestos (auditoria de 2026-11-13, R3): regra R15 do certificador,
SO por perfil do lock (R7) e commit/árvore suja no decision_log do executor nativo."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "certification"))

import certify_chain as cc  # noqa: E402
import run_conflict_experiment as rce  # noqa: E402


def _r15(tmp_path, manifest, events=None, name="nori_S8_B3_seed1"):
    run = tmp_path / name
    run.mkdir()
    report = cc.RunReport(run_id=name, path=str(run), kind="run")
    original = cc.ROOT
    if events is not None:
        cc.ROOT = tmp_path
        log = tmp_path / "experiments" / "xapp_logs" / name
        log.mkdir(parents=True)
        (log / "kpm_probe_events.jsonl").write_text(events, encoding="utf-8")
    try:
        cc._check_repo_commit(run, manifest, report)
    finally:
        cc.ROOT = original
    return [c for c in report.checks if c.rule == "R15.repo_commit"][0]


def test_r15_manifest_commit_passes(tmp_path):
    check = _r15(tmp_path, {"repo_git_sha": "d0cbd8f", "repo_dirty": False})
    assert check.status == cc.PASS and "manifesto" in check.detail


def test_r15_dirty_tree_warns(tmp_path):
    check = _r15(tmp_path, {"repo_git_sha": "d0cbd8f", "repo_dirty": True, "repo_dirty_paths": ["src/core/reasoning.py"]})
    assert check.status == cc.WARN and "src/core/reasoning.py" in check.detail


def test_r15_falls_back_to_the_kpm_probe_log(tmp_path):
    events = '{"event": "start", "src_commit": "87d5282ea8f35edd68c65225b16e339677b64eab"}\n'
    check = _r15(tmp_path, {}, events=events)
    assert check.status == cc.PASS and "kpm-probe" in check.detail


def test_r15_missing_commit_warns(tmp_path):
    assert _r15(tmp_path, {}).status == cc.WARN


def test_lock_profiles_declare_the_os_of_their_runs():
    lock = cc.load_versions_lock()
    assert lock["profile.native"]["os"] == "Ubuntu 24.04"
    assert lock["profile.nori"]["os"] == "Ubuntu 20.04"


def test_executor_records_full_sha_and_dirty_flag(monkeypatch):
    outputs = {("rev-parse", "HEAD"): "0123456789abcdef0123456789abcdef01234567\n"}

    def fake_git(args):
        if args[-2:] == ["rev-parse", "HEAD"]:
            return outputs[("rev-parse", "HEAD")]
        return " M src/core/reasoning.py\n"

    monkeypatch.setattr(rce, "_git", fake_git)
    assert rce.repo_git_sha() == "0123456789abcdef0123456789abcdef01234567"
    assert rce.repo_dirty() is True
    monkeypatch.setattr(rce, "_git", lambda args: None)
    assert rce.repo_git_sha() == "unknown" and rce.repo_dirty() is None
