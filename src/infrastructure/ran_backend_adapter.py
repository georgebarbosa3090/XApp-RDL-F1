"""
Arquitetura de Adaptação Multibackend RAN (RANBackendAdapter)

Proporciona o desacoplamento formal entre a camada de governança H-RDL (XAppAction, KPMReport, RDLDecision)
e os diferentes backends experimentais suportados pelo projeto:
  1. NORI_NS3: Simulação discreta 5G-LENA + NORI E2SIM (Perfil F1 Congelado)
  2. SRSRAN_OPEN5GS: Testbed de software srsRAN + Open5GS + O-RAN SC (Perfil Testbed srsRAN)
  3. OPENRANBR_PHYSICAL: Infraestrutura e ilhas físicas do programa OpenRAN@Brasil (O-RU/COTS UE)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from src.conflict_types import XAppAction
from src.e2.rc.mapper import RCMapper
from src.e2.rc.capability_registry import rc_capability_registry
from src.observability.logging import setup_logger

logger = setup_logger("RANBackendAdapter")

class UnsupportedBackendError(Exception):
    """Exceção lançada quando um backend RAN não suportado ou desconhecido é configurado."""
    pass

@dataclass
class BackendMetadata:
    backend_id: str
    description: str
    e2ap_version: str
    e2sm_kpm_version: str
    e2sm_rc_version: str
    default_kpm_period_ms: int
    prb_control_style: int
    prb_control_action: int
    required_raw_evidence: List[str]

class RANBackendAdapter(ABC):
    """Interface abstrata base para adaptadores de backend RAN no H-RDL."""

    @property
    @abstractmethod
    def metadata(self) -> BackendMetadata:
        pass

    @abstractmethod
    def register_static_profile_capabilities(self, node_id: str) -> bool:
        """
        Registra capacidades estáticas pré-configuradas do perfil de backend (dev/test/standalone).
        Em ambiente O-RAN estrito real, a descoberta deve advir da RANFunctionDefinition no E2 Setup.
        """
        pass

    def discover_capabilities(self, node_id: str, oran_strict: bool = False) -> bool:
        """
        Em modo estrito O-RAN, o registro automático de capacidades estáticas é desabilitado.
        As capacidades devem ser descobertas via RANFunctionDefinition (E2 Setup).
        """
        if oran_strict:
            logger.info("Modo O_RAN_INTEROP estrito: Descoberta de capacidades vinculada a RANFunctionDefinition.", node_id=node_id)
            return rc_capability_registry.is_action_supported(node_id, "PRB_QUOTA")
        return self.register_static_profile_capabilities(node_id)

    @abstractmethod
    def decode_kpm(self, payload: bytes) -> List[Dict[str, Any]]:
        """Decodifica telemetria KPM recebida pelo backend."""
        pass

    @abstractmethod
    def map_action_to_control_pdu(
        self,
        action: XAppAction,
        requestor_id: int = 1,
        instance_id: int = 1
    ) -> bytes:
        """Mapeia ação H-RDL para o formato PDU de controle E2AP do backend especificando Style/Action apropriados."""
        pass

    @abstractmethod
    def correlate_ack(self, ack_payload_bytes: bytes, allow_test_fallback: bool = True) -> Dict[str, Any]:
        """Correlaciona resposta ACK/Failure do nó E2 com a transação E2AP."""
        pass


class NoriBackendAdapter(RANBackendAdapter):
    """Adaptador para Backend 1: Simulação ns-3 / 5G-LENA + NORI E2SIM."""

    @property
    def metadata(self) -> BackendMetadata:
        return BackendMetadata(
            backend_id="NORI_NS3",
            description="Simulador de eventos discretos ns-3.48 + 5G-LENA v5.1 + NORI E2SIM",
            e2ap_version="v02.03",
            e2sm_kpm_version="v03.00",
            e2sm_rc_version="v01.03",
            default_kpm_period_ms=200,
            prb_control_style=1,
            prb_control_action=1,
            required_raw_evidence=["nori_commit", ".xml", ".raw"]
        )

    def register_static_profile_capabilities(self, node_id: str) -> bool:
        rc_capability_registry.register_node_capability(
            node_id=node_id,
            param_name="PRB_QUOTA",
            style_type=1,
            action_id=1,
            param_id=1,
            min_val=0.0,
            max_val=100.0,
            unit="percent"
        )
        return True

    def decode_kpm(self, payload: bytes) -> List[Dict[str, Any]]:
        from src.e2.kpm_decoder import KpmDecoder
        decoder = KpmDecoder()
        return decoder.decode_indication(payload)

    def map_action_to_control_pdu(
        self,
        action: XAppAction,
        requestor_id: int = 1,
        instance_id: int = 1
    ) -> bytes:
        mapper = RCMapper(ran_function_id=3)
        control_ctx = mapper.map_action_to_control_request(action, requestor_id, instance_id)
        return control_ctx.pdu_aper

    def correlate_ack(self, ack_payload_bytes: bytes, allow_test_fallback: bool = True) -> Dict[str, Any]:
        from src.e2.e2ap.control import parse_ric_control_ack, parse_ric_control_failure
        
        # 1. Tenta decodificar como RICcontrolAcknowledge APER
        try:
            ack_res = parse_ric_control_ack(ack_payload_bytes)
            if ack_res:
                return {
                    "status": "ACK_RECEIVED",
                    "backend": "NORI_NS3",
                    "requestor_id": ack_res.requestor_id,
                    "instance_id": ack_res.instance_id,
                    "ran_function_id": ack_res.ran_function_id,
                    "raw_decoded": True
                }
        except Exception:
            pass

        # 2. Tenta decodificar como RICcontrolFailure APER
        try:
            fail_res = parse_ric_control_failure(ack_payload_bytes)
            if fail_res:
                return {
                    "status": "FAILURE_RECEIVED",
                    "backend": "NORI_NS3",
                    "requestor_id": fail_res.requestor_id,
                    "instance_id": fail_res.instance_id,
                    "ran_function_id": fail_res.ran_function_id,
                    "cause": fail_res.cause,
                    "raw_decoded": True
                }
        except Exception:
            pass

        # 3. Fallback estruturado para JSON / Stubs de Teste (desabilitado em modo estrito)
        if allow_test_fallback:
            try:
                import json
                decoded = json.loads(ack_payload_bytes.decode('utf-8'))
                if isinstance(decoded, dict):
                    st = decoded.get("status", "ACKNOWLEDGED")
                    return {
                        "status": "ACK_RECEIVED" if st in ("ACKNOWLEDGED", "OK", "SUCCESS") else "FAILURE_RECEIVED",
                        "backend": "NORI_NS3",
                        "details": decoded,
                        "raw_decoded": False
                    }
            except Exception:
                pass

        return {
            "status": "MALFORMED_RESPONSE",
            "backend": "NORI_NS3",
            "payload_len": len(ack_payload_bytes),
            "raw_decoded": False
        }


class SrsRanBackendAdapter(RANBackendAdapter):
    """Adaptador para Backend 2: Software RAN srsRAN + Open5GS + O-RAN SC / OpenRAN@Brasil."""

    @property
    def metadata(self) -> BackendMetadata:
        return BackendMetadata(
            backend_id="SRSRAN_OPEN5GS",
            description="Testbed de Software srsRAN gNB + Open5GS 5GC + Near-RT RIC O-RAN SC",
            e2ap_version="v03.00",
            e2sm_kpm_version="v03.00",
            e2sm_rc_version="v03.00",
            default_kpm_period_ms=1000,
            prb_control_style=2,  # Style 2: Slice Level Control
            prb_control_action=6, # Action 6: PRB Allocation
            required_raw_evidence=["srsran_version", "open5gs_version", ".pcap", ".log"]
        )

    def register_static_profile_capabilities(self, node_id: str) -> bool:
        rc_capability_registry.register_node_capability(
            node_id=node_id,
            param_name="PRB_QUOTA",
            style_type=2, # Style 2 para srsRAN
            action_id=6,  # Action 6 para srsRAN PRB Allocation
            param_id=1,
            min_val=0.0,
            max_val=100.0,
            unit="percent"
        )
        return True

    def decode_kpm(self, payload: bytes) -> List[Dict[str, Any]]:
        from src.e2.kpm_decoder import KpmDecoder
        decoder = KpmDecoder()
        return decoder.decode_indication(payload)

    def map_action_to_control_pdu(
        self,
        action: XAppAction,
        requestor_id: int = 1,
        instance_id: int = 1
    ) -> bytes:
        mapper = RCMapper(ran_function_id=3)
        control_ctx = mapper.map_action_to_control_request(action, requestor_id, instance_id)
        return control_ctx.pdu_aper

    def correlate_ack(self, ack_payload_bytes: bytes, allow_test_fallback: bool = True) -> Dict[str, Any]:
        from src.e2.e2ap.control import parse_ric_control_ack, parse_ric_control_failure

        # 1. Tenta decodificar como RICcontrolAcknowledge APER
        try:
            ack_res = parse_ric_control_ack(ack_payload_bytes)
            if ack_res:
                return {
                    "status": "ACK_RECEIVED",
                    "backend": "SRSRAN_OPEN5GS",
                    "requestor_id": ack_res.requestor_id,
                    "instance_id": ack_res.instance_id,
                    "ran_function_id": ack_res.ran_function_id,
                    "raw_decoded": True
                }
        except Exception:
            pass

        # 2. Tenta decodificar como RICcontrolFailure APER
        try:
            fail_res = parse_ric_control_failure(ack_payload_bytes)
            if fail_res:
                return {
                    "status": "FAILURE_RECEIVED",
                    "backend": "SRSRAN_OPEN5GS",
                    "requestor_id": fail_res.requestor_id,
                    "instance_id": fail_res.instance_id,
                    "ran_function_id": fail_res.ran_function_id,
                    "cause": fail_res.cause,
                    "raw_decoded": True
                }
        except Exception:
            pass

        # 3. Fallback para JSON / Stubs de Teste (desabilitado em modo estrito)
        if allow_test_fallback:
            try:
                import json
                decoded = json.loads(ack_payload_bytes.decode('utf-8'))
                if isinstance(decoded, dict):
                    st = decoded.get("status", "ACKNOWLEDGED")
                    return {
                        "status": "ACK_RECEIVED" if st in ("ACKNOWLEDGED", "OK", "SUCCESS") else "FAILURE_RECEIVED",
                        "backend": "SRSRAN_OPEN5GS",
                        "details": decoded,
                        "raw_decoded": False
                    }
            except Exception:
                pass

        return {
            "status": "MALFORMED_RESPONSE",
            "backend": "SRSRAN_OPEN5GS",
            "payload_len": len(ack_payload_bytes),
            "raw_decoded": False
        }


