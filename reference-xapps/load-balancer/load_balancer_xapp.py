"""
Load Balancer Reference xApp (O-RAN SC Standard lb-xapp)
Papel no RDL: Balanceamento de Carga entre Portadoras e Estacoes-Base Vizinhas.
Gera propostas para LOAD_THRESHOLD e CARRIER_PRB_ALLOCATION (Prioridade: 70).
"""

import time
import os
import threading
import logging
from typing import Dict, Any, Optional

try:
    from fastapi import FastAPI
    from uvicorn import Config, Server
    from prometheus_client import Counter, Gauge, generate_latest
except ImportError:
    FastAPI = None
    Server = None
    class _DummyMetric:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def inc(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
    Counter = Gauge = _DummyMetric
    def generate_latest(): return b""

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [LoadBalancer-xApp] %(message)s')
logger = logging.getLogger("load_balancer_xapp")

LB_PROPOSALS_TOTAL = Counter(
    "load_balancer_proposals_total",
    "Total de propostas de balanceamento de carga emitidas",
    ["node_id"]
)
LB_LOAD_THRESHOLD = Gauge(
    "load_balancer_load_threshold",
    "Limiar de ocupacao de PRB para disparo de offload",
    ["node_id"]
)

class LoadBalancerXApp:
    def __init__(self, http_port: int = 8094, metrics_port: int = 8095, rmr_port: int = 4568):
        self.xapp_id = "load_balancer_oransc"
        self.http_port = int(os.getenv("HTTP_PORT", str(http_port)))
        self.metrics_port = int(os.getenv("METRICS_PORT", str(metrics_port)))
        self.rmr_port = int(os.getenv("RMR_PORT", str(rmr_port)))
        self.running = False
        self.http_server: Optional[Any] = None
        self.worker_thread: Optional[threading.Thread] = None

        self.target_nodes = ["gnb_01", "gnb_02"]
        self.default_load_threshold = 0.75  # 75% PRB threshold
        self.priority = 70

    def generate_action_proposal(self, node_id: str = "gnb_01", threshold: float = 0.75) -> Dict[str, Any]:
        """Gera proposta estruturada de threshold de balanceamento de carga."""
        proposal = {
            "xapp_id": self.xapp_id,
            "node_id": node_id,
            "parameter": "LOAD_THRESHOLD",
            "value": threshold,
            "priority": self.priority,
            "slice_type": "eMBB",
            "timestamp": time.time()
        }
        LB_PROPOSALS_TOTAL.labels(node_id=node_id).inc()
        LB_LOAD_THRESHOLD.labels(node_id=node_id).set(threshold)
        return proposal

    def _run_http(self):
        if FastAPI is None:
            return

        app = FastAPI(title="Load Balancer xApp (O-RAN SC)", version="1.0.0")

        @app.get("/health")
        def health():
            return {"status": "UP", "xapp": self.xapp_id, "role": "Load_Balancer"}

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
        logger.info(f"Load Balancer xApp ativa. Monitorando ocupacao de celula threshold={self.default_load_threshold}...")
        while self.running:
            for node in self.target_nodes:
                proposal = self.generate_action_proposal(node_id=node, threshold=self.default_load_threshold)
                logger.debug(f"[LB Proposal] Emitida: {proposal}")
            time.sleep(3.0)

    def start(self):
        self.running = True
        t_http = threading.Thread(target=self._run_http, daemon=True)
        t_http.start()
        self.worker_thread = threading.Thread(target=self._loop, daemon=True)
        self.worker_thread.start()
        logger.info(f"Load Balancer xApp iniciada. HTTP: {self.http_port}")

    def stop(self):
        self.running = False
        if self.http_server:
            self.http_server.should_exit = True
        logger.info("Load Balancer xApp finalizada.")

if __name__ == "__main__":
    app = LoadBalancerXApp()
    app.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app.stop()
