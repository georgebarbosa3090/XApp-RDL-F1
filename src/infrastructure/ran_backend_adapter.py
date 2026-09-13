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
from src.conflict_types import XAppAction, KPMReport, RDLDecision
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
    def discover_capabilities(self, node_id: str) -> bool:
        """Registra capacidades descobertas via E2 Setup / RANFunctionDefinition."""
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
    def correlate_ack(self, ack_payload_bytes: bytes) -> Dict[str, Any]:
        """Correlaciona resposta ACK/Failure do nó E2 com a transação."""
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

    def discover_capabilities(self, node_id: str) -> bool:
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

    def map_action_to_control_pdu(
        self,
        action: XAppAction,
        requestor_id: int = 1,
        instance_id: int = 1
    ) -> bytes:
        mapper = RCMapper(ran_function_id=3)
        control_ctx = mapper.map_action_to_control_request(action, requestor_id, instance_id)
        return control_ctx.pdu_aper

    def correlate_ack(self, ack_payload_bytes: bytes) -> Dict[str, Any]:
        return {"status": "ACKNOWLEDGED", "backend": "NORI_NS3"}


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

    def discover_capabilities(self, node_id: str) -> bool:
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

    def map_action_to_control_pdu(
        self,
        action: XAppAction,
        requestor_id: int = 1,
        instance_id: int = 1
    ) -> bytes:
        # Registra capacidades específicas srsRAN antes do mapeamento
        self.discover_capabilities(action.node_id)
        mapper = RCMapper(ran_function_id=3)
        control_ctx = mapper.map_action_to_control_request(action, requestor_id, instance_id)
        return control_ctx.pdu_aper

    def correlate_ack(self, ack_payload_bytes: bytes) -> Dict[str, Any]:
        return {"status": "ACKNOWLEDGED", "backend": "SRSRAN_OPEN5GS"}
