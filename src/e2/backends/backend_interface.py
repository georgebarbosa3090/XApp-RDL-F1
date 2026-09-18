"""
Interface Abstrata de Backend de Rádio para a xApp-RDL (Fase 1 H-RDL e Fase 2 CA-RDL).

Permite que a camada de decisão opere de forma 100% polimórfica e agnóstica
ao ambiente subjacente:
  - ns-3 / 5G-LENA / NORI (Co-Simulação)
  - Open5GS + srsRAN Project em modo ZeroMQ Virtual
  - Open5GS + srsRAN Project com USRP SDR (B210 / X310) e UEs COTS reais.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time


@dataclass
class KpmMetrics:
    """Telemetria física de rádio normalizada extraída de RICindication (E2SM-KPM)."""
    node_id: str
    timestamp_ns: int
    prb_utilization: float           # 0.0 a 100.0%
    active_ues: int
    pdcp_throughput_mbps: float
    packet_loss_rate: float          # 0.0 a 1.0
    cqi_mean: float                  # 0.0 a 15.0
    sinr_db: float
    slice_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    raw_payload_bytes: bytes = b""
    is_valid: bool = True


@dataclass
class ControlResult:
    """Resultado formal do despacho de controle E2SM-RC."""
    transaction_id: int
    ack_received: bool
    status_code: int                 # 0: Sucesso / ACK, 1: Falha / NACK, 2: Timeout
    latency_ms: float
    applied_prb_quotas: Dict[str, float] = field(default_factory=dict)
    applied_tx_power_dbm: Optional[float] = None
    raw_ack_bytes: bytes = b""


@dataclass
class RanPhysicalState:
    """Estado físico corrente da gNodeB reportado ou inspecionado."""
    node_id: str
    is_connected: bool
    total_prbs: int
    tx_power_dbm: float
    active_slices: List[str] = field(default_factory=list)
    attached_ues: int = 0
    backend_type: str = "GENERIC"


class RadioBackendAdapter(ABC):
    """Contrato abstrato obrigatório para qualquer backend de rádio."""

    @abstractmethod
    def connect_e2(self, host: str, port: int, timeout_s: float = 5.0) -> bool:
        """Estabelece a conexão E2 (SCTP) com o Near-RT RIC ou com o E2 Node."""
        pass

    @abstractmethod
    def subscribe_kpm(self, node_id: str, report_period_ms: int = 200) -> bool:
        """Dispara a subscrição de métricas de rádio E2SM-KPM."""
        pass

    @abstractmethod
    def fetch_telemetry(self, node_id: str) -> KpmMetrics:
        """Lê a indicação periódica mais recente do E2 Node."""
        pass

    @abstractmethod
    def dispatch_control(self, node_id: str, action_vector: Dict[str, Any]) -> ControlResult:
        """Codifica e emite uma mensagem de controle E2SM-RC (Radio Resource Allocation)."""
        pass

    @abstractmethod
    def get_ran_state(self, node_id: str) -> RanPhysicalState:
        """Obtém o estado físico corrente da célula."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Encerra graciosamente a conexão e libera recursos de rede."""
        pass
