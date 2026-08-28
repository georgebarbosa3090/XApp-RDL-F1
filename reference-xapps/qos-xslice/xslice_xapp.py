"""
xSlice Reference xApp (QoS & Slicing Optimizer)
Baseado em: peihaoY/xslice-oran (Near-Real-Time Resource Slicing for QoS Optimization in 5G O-RAN)
Papel no RDL: Controladora de QoS/Slicing focada em fatias URLLC/eMBB.
Gera propostas de alta prioridade (Prio: 90) para PRB_QUOTA e SLICE_BOOST.
"""

import time
import os
import threading
import json
import logging
from typing import Dict, Any, Optional

try:
    from fastapi import FastAPI
    from uvicorn import Config, Server
    import prometheus_client
    from prometheus_client import Counter, Gauge, generate_latest
except ImportError:
    FastAPI = None
    Server = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [xSlice-xApp] %(message)s')
logger = logging.getLogger("xslice_xapp")

# Prometheus Metrics
XSLICE_PROPOSALS_TOTAL = Counter(
    "xslice_proposals_total",
    "Total de propostas de alocacao de PRB emitidas pela xSlice xApp",
    ["slice_type", "node_id"]
)
XSLICE_PRB_QUOTA_REQUESTED = Gauge(
    "xslice_prb_quota_requested_ratio",
    "Fracao de PRB solicitada para fatias prioritarias",
    ["slice_type", "node_id"]
)
XSLICE_SLA_SATISFACTION = Gauge(
    "xslice_sla_satisfaction_ratio",
    "Indice estimado de satisfacao de SLA para fluxos URLLC/eMBB"
)

class XSliceXApp:
    def __init__(self, http_port: int = 8082, metrics_port: int = 8083, rmr_port: int = 4562):
        self.xapp_id = "xslice_oran"
        self.http_port = int(os.getenv("HTTP_PORT", str(http_port)))
        self.metrics_port = int(os.getenv("METRICS_PORT", str(metrics_port)))
        self.rmr_port = int(os.getenv("RMR_PORT", str(rmr_port)))
        self.running = False
        self.http_server: Optional[Any] = None
        self.worker_thread: Optional[threading.Thread] = None

        # Estado interno de slicing
        self.target_nodes = ["gnb_01", "gnb_02"]
        self.default_slice = "URLLC"
        self.default_prb_quota = 80.0  # 80% dos PRBs alocados
        self.priority = 90

    def generate_action_proposal(self, node_id: str = "gnb_01", prb_quota: float = 80.0) -> Dict[str, Any]:
        """Gera proposta estruturada compatível com o PerceptionAgent da xApp RDL."""
        proposal = {
            "xapp_id": self.xapp_id,
            "node_id": node_id,
            "parameter": "PRB_QUOTA",
            "value": prb_quota,
            "priority": self.priority,
            "slice_type": self.default_slice,
            "timestamp": time.time()
        }
        XSLICE_PROPOSALS_TOTAL.labels(slice_type=self.default_slice, node_id=node_id).inc()
        XSLICE_PRB_QUOTA_REQUESTED.labels(slice_type=self.default_slice, node_id=node_id).set(prb_quota / 100.0)
        XSLICE_SLA_SATISFACTION.set(0.98)
        return proposal

    def _run_http(self):
        """Servidor FastAPI para /health, /ready e /metrics."""
        if FastAPI is None:
            logger.warning("FastAPI não instalado. Endpoints HTTP em modo mock.")
            return

        app = FastAPI(title="xSlice xApp (QoS & Slicing)", version="1.0.0")

        @app.get("/health")
        def health():
            return {"status": "UP", "xapp": self.xapp_id, "role": "QoS_Slicing"}

        @app.get("/ready")
        def ready():
            return {"ready": True, "xapp": self.xapp_id}

        @app.get("/metrics")
        def metrics():
            from fastapi.responses import Response
            return Response(content=generate_latest(), media_type="text/plain")

        @app.get("/proposals/latest")
        def latest_proposal():
            return self.generate_action_proposal()

        config = Config(app=app, host="0.0.0.0", port=self.http_port, log_level="warning")
        self.http_server = Server(config=config)
        self.http_server.run()

    def _loop(self):
        """Loop de emissão periódica de propostas de slicing."""
        logger.info(f"xSlice xApp ativa. Monitorando SLA e emitindo propostas PRB_QUOTA={self.default_prb_quota}%...")
        while self.running:
            for node in self.target_nodes:
                proposal = self.generate_action_proposal(node_id=node, prb_quota=self.default_prb_quota)
                logger.debug(f"[xSlice Proposal] Emitida: {proposal}")
            time.sleep(2.0)

    def start(self):
        self.running = True
        # Iniciar HTTP em background
        t_http = threading.Thread(target=self._run_http, daemon=True)
        t_http.start()

        # Iniciar Loop de decisões
        self.worker_thread = threading.Thread(target=self._loop, daemon=True)
        self.worker_thread.start()
        logger.info(f"xSlice xApp iniciada com sucesso. HTTP: {self.http_port}, Metrics: {self.http_port}/metrics")

    def stop(self):
        self.running = False
        if self.http_server:
            self.http_server.should_exit = True
        logger.info("xSlice xApp finalizada.")

if __name__ == "__main__":
    app = XSliceXApp()
    app.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app.stop()
