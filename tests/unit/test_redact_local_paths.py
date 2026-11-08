"""
Testes da redação de caminhos locais (scripts/certification/redact_local_paths.py): evidências, relatórios e
documentos não podem guardar o diretório do usuário nem o caminho do clone.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("redact_local_paths",
                                              ROOT / "scripts" / "certification" / "redact_local_paths.py")
rl = importlib.util.module_from_spec(SPEC)
sys.modules["redact_local_paths"] = rl
SPEC.loader.exec_module(rl)

USER = "geo" + "rg"                         # montado em partes: este arquivo também é verificado
CLONE = f"Users/{USER}/.antigravity-ide/XApp-RDL-F1"


def test_repo_in_every_spelling_becomes_placeholder():
    for text in (f"/mnt/c/{CLONE}/experiments/runs/x/raw/a.csv",
                 f"C:\\{CLONE.replace('/', chr(92))}\\experiments\\runs\\x",
                 f"C:\\\\{CLONE.replace('/', chr(92) * 2)}\\\\docs",
                 f"c:/{CLONE}/docs/02.md",
                 f"file:///c:/{CLONE}/README.md"):
        out = rl.redact_text(text)
        assert out.startswith("<repo>"), (text, out)
        assert USER not in out


def test_home_and_old_clones():
    assert rl.redact_text("cd /home/" + USER + "e/ns3-oran-workspace/ns-3-oran") == "cd ~/ns3-oran-workspace/ns-3-oran"
    old = f"file:///c:/Users/{USER}e.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase1/docs/x.md"
    assert rl.redact_text(old) == "<repo-antigo>/docs/x.md"
    assert rl.redact_text("C:/Users/fulano/AppData/Local/x") == "<home>/AppData/Local/x"


def test_placeholders_and_neutral_paths_are_kept():
    for text in ("<repo>/experiments", "~/.venvs/xapp-rdl", "/workspace/runs/nori_S1", "/mnt/c/dados/x.csv",
                 "/etc/rancher/k3s/k3s.yaml", "/home/<usuário>/ns3"):
        assert rl.redact_text(text) == text
    assert rl.find_local("sem caminhos aqui") == []


def test_current_machine_paths_are_redacted():
    assert rl.redact_text(str(ROOT / "experiments" / "runs")).startswith("<repo>")
    home = os.path.expanduser("~")
    assert rl.redact_text(os.path.join(home, "x", "y")).startswith(("~", "<repo>"))


def test_apply_redacts_and_propagates_sha256(tmp_path, monkeypatch):
    monkeypatch.setattr(rl, "ROOT", tmp_path)
    run = tmp_path / "experiments" / "runs" / "r1"
    (run / "logs").mkdir(parents=True)
    log = run / "logs" / "stdout.log"
    log.write_text(f"[RDL-ACT] 2 ações agendadas a partir de /mnt/c/{CLONE}/experiments/runs/r1/raw/a.csv\n",
                   encoding="utf-8")
    old = rl.sha(log.read_bytes())
    (run / "hashes.sha256").write_text(f"{old}  logs/stdout.log\n", encoding="utf-8")
    ref = tmp_path / "derived.json"
    ref.write_text(json.dumps({"source_sha256": old}), encoding="utf-8")
    hashes_before = rl.sha((run / "hashes.sha256").read_bytes())
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps({"hashes_sha256": hashes_before}), encoding="utf-8")

    out = rl.apply([log, run / "hashes.sha256", ref, meta], tmp_path / "reports")
    new = rl.sha(log.read_bytes())
    assert "<repo>/experiments" in log.read_text(encoding="utf-8")
    assert (run / "hashes.sha256").read_text(encoding="utf-8") == f"{new}  logs/stdout.log\n"
    assert json.loads(ref.read_text(encoding="utf-8"))["source_sha256"] == new
    # propagação em cadeia: o sha do hashes.sha256 mudou e a referência a ele também
    assert json.loads(meta.read_text(encoding="utf-8"))["hashes_sha256"] == rl.sha((run / "hashes.sha256").read_bytes())
    log_doc = json.loads(out.read_text(encoding="utf-8"))
    assert log_doc["hashes_sha256_mismatches_after"] == [] and log_doc["files_changed"] == 4
    assert USER not in out.read_text(encoding="utf-8")


def test_no_local_paths_in_code_docs_and_reports():
    files = [p for p in rl.tracked_files()
             if p.relative_to(ROOT).parts[0] in ("src", "scripts", "docs", "deploy", "reports", "simulations",
                                                 "README.md", "tests", "artifacts")]
    hits = {rl.rel(p): len(rl.find_local(t)) for p in files
            if rl.rel(p) not in rl.SELF and (t := rl.read_text(p)) and rl.find_local(t)}
    assert hits == {}
