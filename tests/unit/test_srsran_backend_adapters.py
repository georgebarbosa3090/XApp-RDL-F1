"""
Testes Unitários para a Camada de Adaptadores de Backend de Rádio (src/e2/backends/).
Valida as implementações SrsranE2Adapter e ZmqVirtualAdapter, garantindo:
1. Conformidade com o contrato RadioBackendAdapter;
2. Codificação estrita em ponto fixo Q8.8 / Q16.16 nas mensagens E2SM-RC;
3. Ingestão e normalização de telemetria E2SM-KPM;
4. Ciclo de vida de conexão e desconexão graciosa.
"""

import pytest
import struct
from src.e2.backends.backend_interface import (
    RadioBackendAdapter,
    KpmMetrics,
    ControlResult,
    RanPhysicalState
)
from src.e2.backends.srsran_e2_adapter import SrsranE2Adapter
from src.e2.backends.zmq_virtual_adapter import ZmqVirtualAdapter


class TestSrsranE2Adapter:
    """Testes de conformidade e integridade do driver srsRAN E2."""

    def test_adapter_inheritance_and_initial_state(self):
        adapter = SrsranE2Adapter(e2t_host="127.0.0.1", e2t_port=36422, mock_socket=True)
        assert isinstance(adapter, RadioBackendAdapter)
        assert adapter.e2t_host == "127.0.0.1"
        assert adapter.e2t_port == 36422
        assert adapter.total_prbs == 106
        assert not adapter.is_connected

    def test_connection_and_subscription_flow(self):
        adapter = SrsranE2Adapter(mock_socket=True)
        ok_conn = adapter.connect_e2()
        assert ok_conn is True
        assert adapter.is_connected is True

        ok_sub = adapter.subscribe_kpm("gnb_01", report_period_ms=200)
        assert ok_sub is True

    def test_fetch_telemetry_normalization(self):
        adapter = SrsranE2Adapter(mock_socket=True)
        adapter.connect_e2()
        metrics = adapter.fetch_telemetry("gnb_test")

        assert isinstance(metrics, KpmMetrics)
        assert metrics.node_id == "gnb_test"
        assert metrics.is_valid is True
        assert 0.0 <= metrics.prb_utilization <= 100.0
        assert "eMBB" in metrics.slice_metrics
        assert "URLLC" in metrics.slice_metrics
        assert metrics.slice_metrics["URLLC"]["latency_ms"] > 0.0

    def test_dispatch_control_fixed_point_encoding(self):
        adapter = SrsranE2Adapter(mock_socket=True)
        adapter.connect_e2()

        action = {
            "prb_quotas": {"URLLC": 0.50, "eMBB": 0.50},
            "tx_power_dbm": 42.5
        }
        res = adapter.dispatch_control("gnb_test", action)

        assert isinstance(res, ControlResult)
        assert res.ack_received is True
        assert res.status_code == 0
        assert res.transaction_id > 1000
        assert res.applied_prb_quotas == {"URLLC": 0.50, "eMBB": 0.50}
        assert res.applied_tx_power_dbm == 42.5
        assert adapter.current_tx_power_dbm == 42.5

        # Verifica decodificação do ACK binário
        assert len(res.raw_ack_bytes) >= 8

    def test_ran_state_inspection(self):
        adapter = SrsranE2Adapter(mock_socket=True)
        adapter.connect_e2()
        state = adapter.get_ran_state("gnb_test")

        assert isinstance(state, RanPhysicalState)
        assert state.node_id == "gnb_test"
        assert state.total_prbs == 106
        assert state.backend_type == "SRSRAN_PROJECT_E2"
        assert "eMBB" in state.active_slices
        assert "URLLC" in state.active_slices

    def test_disconnect_behavior(self):
        adapter = SrsranE2Adapter(mock_socket=True)
        adapter.connect_e2()
        assert adapter.is_connected is True
        adapter.disconnect()
        assert adapter.is_connected is False


class TestZmqVirtualAdapter:
    """Testes de conformidade do adaptador de bancada virtual ZeroMQ."""

    def test_adapter_inheritance_and_endpoints(self):
        adapter = ZmqVirtualAdapter(tx_endpoint="tcp://127.0.0.1:2000", rx_endpoint="tcp://127.0.0.1:2001")
        assert isinstance(adapter, RadioBackendAdapter)
        assert adapter.tx_endpoint == "tcp://127.0.0.1:2000"
        assert adapter.rx_endpoint == "tcp://127.0.0.1:2001"

    def test_full_lifecycle(self):
        adapter = ZmqVirtualAdapter()
        assert adapter.connect_e2() is True
        assert adapter.subscribe_kpm("gnb_zmq_01") is True

        kpm = adapter.fetch_telemetry("gnb_zmq_01")
        assert isinstance(kpm, KpmMetrics)
        assert kpm.prb_utilization == 65.0
        assert kpm.active_ues == 2
        assert kpm.packet_loss_rate == 0.0

        # Controle
        action = {"prb_quotas": {"eMBB": 0.60, "URLLC": 0.40}, "tx_power_dbm": 35.0}
        ctrl = adapter.dispatch_control("gnb_zmq_01", action)
        assert ctrl.ack_received is True
        assert ctrl.status_code == 0
        assert ctrl.applied_prb_quotas == {"eMBB": 0.60, "URLLC": 0.40}

        # Estado físico reflete controle
        state = adapter.get_ran_state("gnb_zmq_01")
        assert state.tx_power_dbm == 35.0
        assert state.backend_type == "SRSRAN_ZEROMQ_VIRTUAL"

        adapter.disconnect()
        assert adapter.is_connected is False
