"""
Testes Unitários para a Camada Multibackend (RANBackendAdapter & Factory)
Valida a alternância dinâmica de backends (NORI_NS3 vs SRSRAN_OPEN5GS)
e o mapeamento de controles E2SM-RC específicos para srsRAN (Style 2 / Action 6).
"""

import pytest
from src.conflict_types import XAppAction
from src.infrastructure.ran_backend_adapter import NoriBackendAdapter, SrsRanBackendAdapter
from src.infrastructure.ran_backend_factory import get_ran_backend_adapter
from src.e2.rc.capability_registry import rc_capability_registry

def test_nori_backend_adapter_metadata_and_capabilities():
    adapter = NoriBackendAdapter()
    assert adapter.metadata.backend_id == "NORI_NS3"
    assert adapter.metadata.e2ap_version == "v02.03"
    assert adapter.metadata.default_kpm_period_ms == 200
    assert adapter.metadata.protocol_interoperability_verified is False

    # Registra e resolve capacidade NORI
    adapter.discover_capabilities("gnb_nori_01")
    style, action, param_id = rc_capability_registry.resolve_action("PRB_QUOTA", "gnb_nori_01", strict_mode=True)
    assert style == 1
    assert action == 1
    assert adapter.discover_capabilities("gnb_nori_strict", oran_strict=True) is False

def test_srsran_backend_adapter_metadata_and_style2_mapping():
    adapter = SrsRanBackendAdapter()
    assert adapter.metadata.backend_id == "SRSRAN_OPEN5GS"
    assert adapter.metadata.e2ap_version == "v03.00"
    assert adapter.metadata.default_kpm_period_ms == 1000

    # Registra e resolve capacidade srsRAN (Style 2 / Action 6)
    adapter.discover_capabilities("gnb_srsran_01")
    style, action, param_id = rc_capability_registry.resolve_action("PRB_QUOTA", "gnb_srsran_01", strict_mode=True)
    assert style == 2
    assert action == 6

    action_obj = XAppAction(
        xapp_id="xslice",
        node_id="gnb_srsran_01",
        parameter="PRB_QUOTA",
        value=75.0,
        priority=80
    )
    pdu_bytes = adapter.map_action_to_control_pdu(action_obj)
    assert len(pdu_bytes) > 0

def test_ran_backend_factory():
    nori = get_ran_backend_adapter("NORI_NS3")
    assert isinstance(nori, NoriBackendAdapter)

    srsran = get_ran_backend_adapter("SRSRAN_OPEN5GS")
    assert isinstance(srsran, SrsRanBackendAdapter)

    default_adapter = get_ran_backend_adapter(None)
    assert isinstance(default_adapter, NoriBackendAdapter)

def test_backend_adapters_decode_kpm_and_correlate_ack():
    nori = NoriBackendAdapter()
    srsran = SrsRanBackendAdapter()

    # Teste decode_kpm com payload invalido (deve retornar lista vazia sem quebrar)
    assert nori.decode_kpm(b"") == []
    assert srsran.decode_kpm(b"") == []

    # Teste correlate_ack
    ack_nori = nori.correlate_ack(b'{"status":"OK"}')
    assert ack_nori.get("status") == "ACK_RECEIVED"
    assert ack_nori.get("backend") == "NORI_NS3"

    ack_srsran = srsran.correlate_ack(b'{"status":"OK"}')
    assert ack_srsran.get("status") == "ACK_RECEIVED"
    assert ack_srsran.get("backend") == "SRSRAN_OPEN5GS"


def test_capability_registry_function_ids_and_actions():
    from src.e2.rc.capability_registry import RanFunctionCapabilityRegistry, CapabilityNotDiscoveredError

    reg = RanFunctionCapabilityRegistry()
    # 1. Registro dinâmico de function IDs
    reg.register_ran_function_id("gnb_01", "RC", 3)
    reg.register_ran_function_id("gnb_01", "KPM", 2)
    assert reg.get_rc_function_id("gnb_01") == 3
    assert reg.get_kpm_function_id("gnb_01") == 2

    # 2. Defaults em modo não-estrito
    assert reg.get_rc_function_id(None) == 3
    assert reg.get_kpm_function_id(None) == 2

    # 3. Exceções em modo estrito para nós não descobertos
    import os
    old_env = os.environ.get("RDL_MODE")
    try:
        os.environ["RDL_MODE"] = "oran-strict"
        with pytest.raises(CapabilityNotDiscoveredError):
            reg.get_rc_function_id("gnb_undiscovered")
        with pytest.raises(CapabilityNotDiscoveredError):
            reg.get_kpm_function_id("gnb_undiscovered")
    finally:
        if old_env is not None:
            os.environ["RDL_MODE"] = old_env
        else:
            os.environ.pop("RDL_MODE", None)

    # 4. is_action_supported
    assert reg.is_action_supported("gnb_01", "UNKNOWN_PARAM") is False
    assert reg.is_action_supported("gnb_default", "PRB_QUOTA") is True


