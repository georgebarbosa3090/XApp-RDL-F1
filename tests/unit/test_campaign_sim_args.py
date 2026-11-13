"""Repasse de --sim-arg e --run-suffix no executor de campanha (docs/17 §3.3, etapa EN1)."""
import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CERT = ROOT / "scripts" / "certification"
if str(CERT) not in sys.path:
    sys.path.insert(0, str(CERT))
import run_conflict_campaign as camp  # noqa: E402


def test_run_id_with_suffix_matches_analyzer_pattern():
    import analyze_conflict_runs as an
    rid = camp.run_id_of("G1", "B3", 13001, "U")
    assert rid == "nr_G1_B3U_seed13001"
    assert an.RUN_PATTERN.match(rid).group(2) == "B3U"
    assert camp.run_id_of("G1", "B3", 13001) == "nr_G1_B3_seed13001"


def test_run_one_forwards_sim_args_and_run_id(monkeypatch, tmp_path):
    seen = {}

    class FakeProc:
        stdout = io.StringIO("")

        def wait(self):
            return 0

    def fake_popen(cmd, **kwargs):
        seen["cmd"] = cmd
        return FakeProc()

    monkeypatch.setattr(camp.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(camp, "disk_ok", lambda: True)
    rid, code, _ = camp.run_one("G1", "B3", 13001, tmp_path, ["--powerAllocation=used"], "U")
    assert (rid, code) == ("nr_G1_B3U_seed13001", 0)
    cmd = seen["cmd"]
    assert cmd[cmd.index("--run-id") + 1] == "nr_G1_B3U_seed13001"
    assert "--sim-arg=--powerAllocation=used" in cmd


@pytest.mark.parametrize("extra", [["--run-suffix", "UU"], ["--run-suffix", "u"], ["--baselines", "B3M", "--run-suffix", "U"]])
def test_invalid_suffix_is_rejected(extra):
    with pytest.raises(SystemExit):
        camp.main(["--scenarios", "G1", "--seeds", "1", *extra])
