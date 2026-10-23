import hashlib
import json

from scripts.validate_provenance import validate_run_directory


def _write_hashes(run_dir):
    lines = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name != "hashes.sha256":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{digest}  {path.relative_to(run_dir).as_posix()}")
    (run_dir / "hashes.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_manifest(run_dir, **updates):
    manifest = {
        "source": "NORI_E2",
        "publication_eligible": True,
        "backend": "NORI_NS3_5GLENA",
        "ns3_version": "3.48",
        "fiveg_lena_version": "5.1",
        "nori_commit": "a" * 40,
        "scenario": "S1",
        "seed": 1,
        "run_status": "SUCCESS",
        "exit_code": 0,
        "command": "./ns3 run scenario",
        "started_at_utc": "2026-10-23T12:00:00Z",
        "finished_at_utc": "2026-10-23T12:01:00Z",
    }
    manifest.update(updates)
    (run_dir / "execution_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )


def test_provenance_rejects_inferred_source_and_eligibility(tmp_path):
    (tmp_path / "evidence.xml").write_text("<FlowMonitor/>", encoding="utf-8")
    (tmp_path / "indication.raw").write_bytes(b"raw")
    _write_manifest(
        tmp_path,
        source=None,
        publication_eligible=None,
    )
    _write_hashes(tmp_path)

    assert not validate_run_directory(str(tmp_path))


def test_provenance_rejects_unsuccessful_run(tmp_path):
    (tmp_path / "evidence.xml").write_text("<FlowMonitor/>", encoding="utf-8")
    (tmp_path / "indication.raw").write_bytes(b"raw")
    _write_manifest(tmp_path, exit_code=1, run_status="FAILED")
    _write_hashes(tmp_path)

    assert not validate_run_directory(str(tmp_path))


def test_provenance_requires_each_raw_evidence_class(tmp_path):
    (tmp_path / "indication.raw").write_bytes(b"raw")
    _write_manifest(tmp_path)
    _write_hashes(tmp_path)

    assert not validate_run_directory(str(tmp_path))


def test_local_fixture_is_never_publication_eligible(tmp_path):
    _write_manifest(
        tmp_path,
        source="CAUSAL_FIXTURE",
        publication_eligible=False,
    )

    assert validate_run_directory(str(tmp_path))


def test_provenance_rejects_hash_paths_outside_run(tmp_path):
    (tmp_path / "evidence.xml").write_text("<FlowMonitor/>", encoding="utf-8")
    (tmp_path / "indication.raw").write_bytes(b"raw")
    _write_manifest(tmp_path)
    (tmp_path / "hashes.sha256").write_text(
        f"{'0' * 64}  ..\\outside.raw\n", encoding="utf-8"
    )

    assert not validate_run_directory(str(tmp_path))
