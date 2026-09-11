"""
ISAC Radar Reference xApp (6G Integrated Sensing and Communication)
Papel no RDL: Controladora de Sensoriamento Ambiental e Radar.
Gera propostas para SENSING_RATIO e RADAR_BURST_PERIOD (Prioridade: 85, Fatia: SENSING).
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [ISAC-Radar-xApp] %(message)s')
logger = logging.getLogger("isac_radar_xapp")

ISAC_PROPOSALS_TOTAL = Counter(
    "isac_radar_proposals_total",
    "Total de propostas de alocacao de sensoriamento emitidas",
    ["node_id"]
)
ISAC_SENSING_RATIO = Gauge(
    "isac_radar_sensing_ratio",
    "Fracao de recursos de radio solicitados para sensoriamento",
    ["node_id"]
)

class ISACRadarXApp:
    def __init__(self, http_port: int = 8090, metrics_port: int = 8091, rmr_port: int = 4566):
        self.xapp_id = "isac_radar_sensing_6g"
        self.http_port = int(os.getenv("HTTP_PORT", str(http_port)))
        self.metrics_port = int(os.getenv("METRICS_PORT", str(metrics_port)))
        self.rmr_port = int(os.getenv("RMR_PORT", str(rmr_port)))
        self.running = False
        self.http_server: Optional[Any] = None
        self.worker_thread: Optional[threading.Thread] = None

        self.target_nodes = ["gnb_01", "gnb_02"]
        self.default_sensing_ratio = 0.35  # 35% de recursos para sensoriamento
        self.priority = 85

    def generate_action_proposal(self, node_id: str = "gnb_01", sensing_ratio: float = 0.35) -> Dict[str, Any]:
        """Gera proposta estruturada de alocacao de recursos ISAC."""
        proposal = {
            "xapp_id": self.xapp_id,
            "node_id": node_id,
            "parameter": "SENSING_RATIO",
            "value": sensing_ratio,
            "priority": self.priority,
            "slice_type": "SENSING",
            "timestamp": time.time()
        }
        ISAC_PROPOSALS_TOTAL.labels(node_id=node_id).inc()
        ISAC_SENSING_RATIO.labels(node_id=node_id).set(sensing_ratio)
        return proposal

    def _run_http(self):
        if FastAPI is None:
            return

        app = FastAPI(title="ISAC Radar xApp (6G Sensing)", version="1.0.0")

        @app.get("/health")
        def health():
            return {"status": "UP", "xapp": self.xapp_id, "role": "ISAC_Radar_Sensing"}

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
        logger.info(f"ISAC Radar xApp ativa. Monitorando alvos e solicitando quota de sensoriamento={self.default_sensing_ratio}...")
        while self.running:
            for node in self.target_nodes:
                proposal = self.generate_action_proposal(node_id=node, sensing_ratio=self.default_sensing_ratio)
                logger.debug(f"[ISAC Radar Proposal] Emitida: {proposal}")
            time.sleep(2.5)

    def start(self):
        self.running = True
        t_http = threading.Thread(target=self._run_http, daemon=True)
        t_http.start()
        self.worker_thread = threading.Thread(target=self._loop, daemon=True)
        self.worker_thread.start()
        logger.info(f"ISAC Radar xApp iniciada. HTTP: {self.http_port}")

    def stop(self):
        self.running = False
        if self.http_server:
            self.http_server.should_exit = True
        logger.info("ISAC Radar xApp finalizada.")

if __name__ == "__main__":
    app = ISACRadarXApp()
    app.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app.stop()
