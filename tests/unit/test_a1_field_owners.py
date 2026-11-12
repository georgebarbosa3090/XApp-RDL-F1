"""Quinto aspecto da governança (doc 11 §5.1): dono e precedência por campo da política A1 e
conflito entre rApps (duas instâncias escrevendo o mesmo campo com valores diferentes)."""
import importlib.util
import json
from pathlib import Path

import pytest

from src.interfaces.a1_policy_receiver import A1PolicyManager
from src.interfaces.a1_rmr import handle_policy_request

ROOT = Path(__file__).resolve().parents[2]
OWNERS = json.loads((ROOT / "configs" / "a1_field_owners.example.json").read_text(encoding="utf-8"))


def test_without_owners_most_recent_wins_and_conflict_is_reported():
    m = A1PolicyManager()
    assert m.put_policy("20000", "ops-a", {"cooling_lockout_ms": 2000})[0]
    assert m.put_policy("20000", "ops-b", {"cooling_lockout_ms": 500, "max_cell_prb_limit": 70})[0]
    assert m.effective_policy() == {"cooling_lockout_ms": 500, "max_cell_prb_limit": 70}
    (c,) = m.conflicts()
    assert c["field"] == "cooling_lockout_ms" and c["rule"] == "most_recent" and c["winner"] == "20000:ops-b"
    assert [w["policy"] for w in c["writers"]] == ["20000:ops-b", "20000:ops-a"]
    assert m.put_policy("20000", "ops-a", {"cooling_lockout_ms": 2000})[0]        # reescrita volta a vencer
    assert m.effective_policy()["cooling_lockout_ms"] == 2000
    assert m.put_policy("20000", "ops-b", {"cooling_lockout_ms": 2000, "max_cell_prb_limit": 70})[0]
    assert m.conflicts() == []                                                   # mesmo valor não é conflito


def test_non_owner_is_refused_also_over_rmr():
    m = A1PolicyManager()
    m.set_field_owners(OWNERS)
    ok, reason = m.put_policy("20000", "greenran", {"cooling_lockout_ms": 300})
    assert not ok and "owned by" in reason
    msg = {"operation": "CREATE", "policy_type_id": 20000, "policy_instance_id": "some-rapp",
           "payload": {"xapp_modes": ["es:QUARANTINED"]}}
    response, applied = handle_policy_request(m, json.dumps(msg).encode(), handler_id="rdl")
    assert not applied and response["status"] == "ERROR" and "owned by" in response["reason"]
    assert m.put_policy("20000", "greenran-night", {"energy_saving_allowed": False})[0]   # glob greenran*
    assert m.put_policy("20000", "free", {})[0]


def test_owner_precedence_beats_recency_and_deleting_restores():
    m = A1PolicyManager()
    m.set_field_owners(OWNERS)
    assert m.put_policy("20000", "operator-maint", {"xapp_modes": ["rogue:MANAGED"]})[0]
    assert m.put_policy("20000", "rdl-governance", {"xapp_modes": ["rogue:QUARANTINED"], "xapp_priority_caps": ["es:60"]})[0]
    eff = m.effective_policy()
    assert eff["xapp_modes"] == ["rogue:MANAGED"]                  # operador vence, mesmo escrevendo antes
    assert eff["xapp_priority_caps"] == ["es:60"]                  # campo sem disputa
    (c,) = m.conflicts()
    assert c["rule"] == "owner_precedence" and c["winner"] == "20000:operator-maint"
    assert [w["rank"] for w in c["writers"]] == [0, 1]
    m.delete_policy("20000", "operator-maint")
    assert m.effective_policy()["xapp_modes"] == ["rogue:QUARANTINED"] and m.conflicts() == []
    assert m.field_owners_view()["20000"]["xapp_modes"] == ["operator*", "rdl-governance"]


def test_writer_without_right_after_map_change_goes_last():
    m = A1PolicyManager()
    assert m.put_policy("20001", "legacy", {"energy_weight": 0.5})[0]
    m.set_field_owners(OWNERS)                                     # "legacy" deixa de ser dono
    assert m.put_policy("20001", "greenran", {"energy_weight": 0.2})[0]
    assert m.effective_policy()["energy_weight"] == 0.2
    assert m.conflicts()[0]["writers"][-1]["policy"] == "20001:legacy"


@pytest.mark.parametrize("bad", [{"30000": {"x": ["a"]}}, {"20000": {"nope": ["a"]}}, {"20000": {"cooling_lockout_ms": []}}])
def test_owner_map_validation(bad):
    with pytest.raises(ValueError):
        A1PolicyManager().set_field_owners(bad)


def test_rdl_applies_precedence_and_reports_rapp_conflicts(monkeypatch, tmp_path):
    path = tmp_path / "owners.json"
    path.write_text(json.dumps(OWNERS), encoding="utf-8")
    monkeypatch.setenv("RDL_A1_FIELD_OWNERS", str(path))
    from src.rdl_xapp import RDLxApp
    app = RDLxApp()
    try:
        assert app.a1_policies.put_policy("20001", "greenran", {"energy_weight": 0.45})[0]
        assert app.a1_policies.put_policy("20001", "operator-day", {"energy_weight": 0.1})[0]
        assert app.a1_policies.put_policy("20001", "greenran", {"energy_weight": 0.5})[0]   # reescreve depois
        assert app.reasoning.w_energy == pytest.approx(0.1)                                 # operador vence
        report = app._governance_view()
        (c,) = report["rapp_conflicts"]
        assert c["field"] == "energy_weight" and c["winner"] == "20001:operator-day"
        assert report["a1_field_owners"]["20001"]["energy_weight"] == ["operator*", "greenran*"]
        assert not app.a1_policies.put_policy("20000", "greenran", {"cooling_lockout_ms": 300})[0]
    finally:
        app.stop()


def test_governance_rapp_recommends_resolving_rapp_conflicts():
    spec = importlib.util.spec_from_file_location("governance_rapp", ROOT / "rapps" / "governance_rapp.py")
    rapp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rapp)
    report = {"rapp_conflicts": [{"field": "energy_weight", "rule": "owner_precedence", "winner": "20001:operator-day",
                                  "writers": [{"policy": "20001:operator-day"}, {"policy": "20001:greenran"}]}]}
    (rec,) = rapp.decide(report)["recommendations"]
    assert rec["action"] == "RESOLVE_A1_FIELD_CONFLICT" and rec["writers"] == ["20001:operator-day", "20001:greenran"]
    assert rapp.decide(report)["modes"] == {}                       # a decisão é do operador, não do rApp
