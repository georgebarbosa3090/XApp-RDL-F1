# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""Modo de operação (RDL_MODE): o padrão do chart usa RMR real e um modo desconhecido não sobe."""

import re
from pathlib import Path

import pytest
import yaml

import src.rdl_xapp as rx

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("raw, mode", [
    (None, "OFFLINE_SIMULATION"), ("", "OFFLINE_SIMULATION"), ("simulation", "OFFLINE_SIMULATION"),
    ("governance", "GOVERNANCE"), (" Governance ", "GOVERNANCE"),
    ("o_ran_interop", "O_RAN_INTEROP"), ("oran-strict", "O_RAN_INTEROP"), ("STRICT", "O_RAN_INTEROP"),
])
def test_parse_rdl_mode(raw, mode):
    assert rx.parse_rdl_mode(raw) == mode


def test_unknown_mode_fails_at_startup(monkeypatch):
    monkeypatch.setenv("RDL_MODE", "standalone")
    with pytest.raises(ValueError, match="RDL_MODE desconhecido"):
        rx.RDLxApp(serve_http=False)


def test_chart_and_deploy_script_use_a_real_rmr_mode():
    values = yaml.safe_load((ROOT / "deploy/helm/iqos-xapp-rdl/values.yaml").read_text(encoding="utf-8"))
    assert rx.parse_rdl_mode(values["env"]["rdlMode"]) == "GOVERNANCE"
    script = (ROOT / "scripts/deploy_helm.sh").read_text(encoding="utf-8")
    for raw in re.findall(r'env\.rdlMode="([^"]+)"', script):
        assert rx.parse_rdl_mode(raw) in ("GOVERNANCE", "O_RAN_INTEROP")


def test_governance_without_ricxappframe_refuses_mock(monkeypatch):
    monkeypatch.setenv("RDL_MODE", "governance")
    monkeypatch.setattr(rx, "_HAS_RICXAPPFRAME", False)
    with pytest.raises(RuntimeError, match="MockRMRXapp"):
        rx.RDLxApp(serve_http=False)


class _FakeRealRMR(rx.MockRMRXapp):
    """Substituto do RMRXapp do ricxappframe: registra que o transporte real foi escolhido."""


def test_governance_uses_the_real_rmr_transport(monkeypatch):
    monkeypatch.setenv("RDL_MODE", "governance")
    monkeypatch.setenv("USE_FAKE_SDL", "true")
    monkeypatch.setattr(rx, "_HAS_RICXAPPFRAME", True)
    monkeypatch.setattr(rx, "_RealRMRXapp", _FakeRealRMR)
    app = rx.RDLxApp(serve_http=False)
    assert app.mode == "GOVERNANCE" and not app.oran_strict
    assert type(app.xapp) is _FakeRealRMR


def test_offline_simulation_keeps_the_mock_and_no_http(monkeypatch):
    monkeypatch.setenv("RDL_MODE", "OFFLINE_SIMULATION")
    monkeypatch.setenv("RDL_E2_NODE", "gnb_07")
    app = rx.RDLxApp(serve_http=False)
    assert type(app.xapp) is rx.MockRMRXapp
    assert app.health.server_thread is None
    assert app.e2_node_id == "gnb_07"
