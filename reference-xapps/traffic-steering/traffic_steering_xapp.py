"""
Traffic Steering Reference xApp (Mobility & Load Balancing Optimizer)
Baseado em: o-ran-sc/ric-app-ts / natanzi/ts-xapp (O-RAN Software Community)
Papel no RDL: Controladora de Mobilidade, Handover e Balanceamento de Tráfego.
Gera propostas de alta prioridade (Prio: 80) para HANDOVER e TX_POWER boost.
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
    class _DummyMetric:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def inc(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
    Counter = Gauge = _DummyMetric
    def generate_latest(): return b""

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [TrafficSteering-xApp] %(message)s')
logger = logging.getLogger("traffic_steering_xapp")

# Prometheus Metrics
TS_PROPOSALS_TOTAL = Counter(
    "ts_proposals_total",
    "Total de propostas de steering emitidas pela TS xApp",
    ["target_action", "node_id"]
)
TS_HANDOVERS_TRIGGERED = Counter(
    "ts_handovers_triggered_total",
    "Contador de handovers propostos para balanceamento de carga",
    ["source_node", "target_node"]
)
TS_CELL_LOAD_ESTIMATE = Gauge(
    "ts_cell_load_ratio",
    "Estimativa de carga de trafego da celula",
    ["node_id"]
)

class TrafficSteeringXApp:
    def __init__(self, http_port: int = 8086, metrics_port: int = 8087, rmr_port: int = 4564):
        self.xapp_id = "traffic_steering_oransc"
        self.http_port = int(os.getenv("HTTP_PORT", str(http_port)))
        self.metrics_port = int(os.getenv("METRICS_PORT", str(metrics_port)))
        self.rmr_port = int(os.getenv("RMR_PORT", str(rmr_port)))
        self.running = False
        self.http_server: Optional[Any] = None
        self.worker_thread: Optional[threading.Thread] = None

        # Estado interno de steering
        self.source_node = "gnb_01"
        self.target_node = "gnb_02"
        self.target_ue = "UE-07"
        self.priority = 80

    def generate_action_proposal(self, source_node: str = "gnb_01", target_node: str = "gnb_02", target_ue: str = "UE-07") -> Dict[str, Any]:
        """Gera proposta estruturada de Handover compatível com o PerceptionAgent da xApp RDL."""
        proposal = {
            "xapp_id": self.xapp_id,
            "node_id": source_node,
            "parameter": "HANDOVER",
            "value": 1.0,
            "target_node": target_node,
            "target_ue": target_ue,
            "priority": self.priority,
            "timestamp": time.time()
        }
        TS_PROPOSALS_TOTAL.labels(target_action="HANDOVER", node_id=source_node).inc()
        TS_HANDOVERS_TRIGGERED.labels(source_node=source_node, target_node=target_node).inc()
        TS_CELL_LOAD_ESTIMATE.labels(node_id=source_node).set(0.72)
        TS_CELL_LOAD_ESTIMATE.labels(node_id=target_node).set(0.35)
        return proposal

    def _run_http(self):
        """Servidor FastAPI para /health, /ready e /metrics."""
        if FastAPI is None:
            logger.warning("FastAPI não instalado. Endpoints HTTP em modo mock.")
            return

        app = FastAPI(title="Traffic Steering xApp (O-RAN SC)", version="1.0.0")

        @app.get("/health")
        def health():
            return {"status": "UP", "xapp": self.xapp_id, "role": "Traffic_Steering"}

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
        """Loop de emissão periódica de propostas de steering e balanceamento."""
        logger.info(f"Traffic Steering xApp ativa. Monitorando mobilidade e propondo handovers...")
        while self.running:
            proposal = self.generate_action_proposal(
                source_node=self.source_node,
                target_node=self.target_node,
                target_ue=self.target_ue
            )
            logger.debug(f"[TrafficSteering Proposal] Emitida: {proposal}")
            time.sleep(3.0)

    def start(self):
        self.running = True
        # Iniciar HTTP em background
        t_http = threading.Thread(target=self._run_http, daemon=True)
        t_http.start()

        # Iniciar Loop de decisões
        self.worker_thread = threading.Thread(target=self._loop, daemon=True)
        self.worker_thread.start()
        logger.info(f"Traffic Steering xApp iniciada com sucesso. HTTP: {self.http_port}, Metrics: {self.http_port}/metrics")

    def stop(self):
        self.running = False
        if self.http_server:
            self.http_server.should_exit = True
        logger.info("Traffic Steering xApp finalizada.")

if __name__ == "__main__":
    app = TrafficSteeringXApp()
    app.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app.stop()
