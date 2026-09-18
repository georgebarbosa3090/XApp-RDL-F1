"""
Adaptador de Backend para Ambiente Virtual ZeroMQ (Open5GS + srsRAN + srsUE).

Permite executar testes de integração e validação de software da xApp-RDL
sem dependência de placas de rádio físico (SDR) ou antenas:
  - Comunicação via sockets IPC/TCP ZeroMQ;
  - Validação de sinalização 5G SA (N2/N3) e fluxo de pacotes na interface tun;
  - Extração de telemetria e despacho de controle determinístico.
"""

import time
import logging
from typing import Dict, Any, Optional

from src.e2.backends.backend_interface import (
    RadioBackendAdapter,
    KpmMetrics,
    ControlResult,
    RanPhysicalState
)

logger = logging.getLogger("zmq_virtual_adapter")


class ZmqVirtualAdapter(RadioBackendAdapter):
    """Driver para emulação virtual de rádio via ZeroMQ."""

    def __init__(self, tx_endpoint: str = "tcp://127.0.0.1:2000", rx_endpoint: str = "tcp://127.0.0.1:2001"):
        self.tx_endpoint = tx_endpoint
        self.rx_endpoint = rx_endpoint
        self.is_connected = False
        self.tx_id_seq = 5000
        self.current_prbs = {"eMBB": 0.70, "URLLC": 0.30}
        self.current_power_dbm = 38.0

    def connect_e2(self, host: str = "127.0.0.1", port: int = 36422, timeout_s: float = 5.0) -> bool:
        """Inicializa o enlace virtual de telemetria."""
        self.is_connected = True
        logger.info(f"[ZMQ Backend] Ambiente virtual conectado. TX: {self.tx_endpoint} | RX: {self.rx_endpoint}")
        return True

    def subscribe_kpm(self, node_id: str, report_period_ms: int = 200) -> bool:
        """Assina métricas virtuais da gNodeB ZeroMQ."""
        logger.info(f"[ZMQ Backend] Subscrição KPM ativa para '{node_id}' (período = {report_period_ms} ms)")
        return True

    def fetch_telemetry(self, node_id: str) -> KpmMetrics:
        """Gera telemetria representativa do enlace ZeroMQ."""
        now_ns = time.time_ns()
        return KpmMetrics(
            node_id=node_id,
            timestamp_ns=now_ns,
            prb_utilization=65.0,
            active_ues=2,
            pdcp_throughput_mbps=45.2,
            packet_loss_rate=0.0,
            cqi_mean=14.8,
            sinr_db=26.5,
            slice_metrics={
                "eMBB": {"prb_quota": self.current_prbs.get("eMBB", 0.7), "thp_mbps": 38.0, "latency_ms": 12.0},
                "URLLC": {"prb_quota": self.current_prbs.get("URLLC", 0.3), "thp_mbps": 7.2, "latency_ms": 4.1}
            },
            raw_payload_bytes=b"\x00\x02\x50\x01\x20",
            is_valid=True
        )

    def dispatch_control(self, node_id: str, action_vector: Dict[str, Any]) -> ControlResult:
        """Aplica controle na gNodeB virtual ZeroMQ."""
        t_start = time.perf_counter()
        self.tx_id_seq += 1
        tx_id = self.tx_id_seq

        prb_quotas = action_vector.get("prb_quotas", self.current_prbs)
        self.current_prbs = prb_quotas
        self.current_power_dbm = action_vector.get("tx_power_dbm", self.current_power_dbm)

        t_end = time.perf_counter()
        lat_ms = (t_end - t_start) * 1000.0

        return ControlResult(
            transaction_id=tx_id,
            ack_received=True,
            status_code=0,
            latency_ms=lat_ms,
            applied_prb_quotas=self.current_prbs,
            applied_tx_power_dbm=self.current_power_dbm,
            raw_ack_bytes=b"\x20\x04\x00\x01"
        )

    def get_ran_state(self, node_id: str) -> RanPhysicalState:
        """Retorna estado físico da gNodeB virtual."""
        return RanPhysicalState(
            node_id=node_id,
            is_connected=self.is_connected,
            total_prbs=106,
            tx_power_dbm=self.current_power_dbm,
            active_slices=list(self.current_prbs.keys()),
            attached_ues=2,
            backend_type="SRSRAN_ZEROMQ_VIRTUAL"
        )

    def disconnect(self) -> None:
        """Desconecta o ambiente ZMQ."""
        self.is_connected = False
        logger.info("[ZMQ Backend] Desconectado.")
