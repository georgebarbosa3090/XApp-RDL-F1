"""
Bouncer Reference xApp (O-RAN SC Standard b-xapp)
Papel no RDL: Benchmarking de Latencia de Loopback E2 e Mensageria RMR.
Gera propostas para PING_INTERVAL e E2_LOOPBACK_FLAG (Prioridade: 40).
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [Bouncer-xApp] %(message)s')
logger = logging.getLogger("bouncer_xapp")

BOUNCER_PROPOSALS_TOTAL = Counter(
    "bouncer_proposals_total",
    "Total de pings de loopback emitidos",
    ["node_id"]
)

class BouncerXApp:
    def __init__(self, http_port: int = 8096, metrics_port: int = 8097, rmr_port: int = 4569):
        self.xapp_id = "bouncer_oransc"
        self.http_port = int(os.getenv("HTTP_PORT", str(http_port)))
        self.metrics_port = int(os.getenv("METRICS_PORT", str(metrics_port)))
        self.rmr_port = int(os.getenv("RMR_PORT", str(rmr_port)))
        self.running = False
        self.http_server: Optional[Any] = None
        self.worker_thread: Optional[threading.Thread] = None

        self.target_nodes = ["gnb_01", "gnb_02", "gnb_03"]
        self.default_ping_interval = 100.0  # 100 ms
        self.priority = 40

    def generate_action_proposal(self, node_id: str = "gnb_01", interval_ms: float = 100.0) -> Dict[str, Any]:
        """Gera proposta estruturada de teste de latencia de loopback."""
        proposal = {
            "xapp_id": self.xapp_id,
            "node_id": node_id,
            "parameter": "PING_INTERVAL",
            "value": interval_ms,
            "priority": self.priority,
            "slice_type": "BestEffort",
            "timestamp": time.time()
        }
        BOUNCER_PROPOSALS_TOTAL.labels(node_id=node_id).inc()
        return proposal

    def _run_http(self):
        if FastAPI is None:
            return

        app = FastAPI(title="Bouncer xApp (O-RAN SC)", version="1.0.0")

        @app.get("/health")
        def health():
            return {"status": "UP", "xapp": self.xapp_id, "role": "E2_Loopback_Bouncer"}

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
        logger.info(f"Bouncer xApp ativa. Emitindo pings de teste interval={self.default_ping_interval}ms...")
        while self.running:
            for node in self.target_nodes:
                proposal = self.generate_action_proposal(node_id=node, interval_ms=self.default_ping_interval)
                logger.debug(f"[Bouncer Proposal] Emitida: {proposal}")
            time.sleep(2.0)

    def start(self):
        self.running = True
        t_http = threading.Thread(target=self._run_http, daemon=True)
        t_http.start()
        self.worker_thread = threading.Thread(target=self._loop, daemon=True)
        self.worker_thread.start()
        logger.info(f"Bouncer xApp iniciada. HTTP: {self.http_port}")

    def stop(self):
        self.running = False
        if self.http_server:
            self.http_server.should_exit = True
        logger.info("Bouncer xApp finalizada.")

if __name__ == "__main__":
    app = BouncerXApp()
    app.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app.stop()
