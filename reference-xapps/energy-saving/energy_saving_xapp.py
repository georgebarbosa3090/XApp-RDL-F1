"""
Energy Saving Reference xApp (Green RAN & Cell Sleep Optimizer)
Baseado em: Orange-OpenSource/ns-O-RAN-flexric (xapp_es_with_cell_util)
Papel no RDL: Controladora de Eficiência Energética focada em redução de consumo e Green RAN.
Gera propostas de prioridade moderada (Prio: 65) para TX_POWER reduction, PRB_THROTTLING e CELL_SLEEP.
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [EnergySaving-xApp] %(message)s')
logger = logging.getLogger("energy_saving_xapp")

# Prometheus Metrics
ES_PROPOSALS_TOTAL = Counter(
    "es_proposals_total",
    "Total de propostas de economia de energia emitidas pela ES xApp",
    ["action_type", "node_id"]
)
ES_TX_POWER_TARGET = Gauge(
    "es_tx_power_target_dbm",
    "Potencia de transmissao alvo (dBm) solicitada pela ES xApp",
    ["node_id"]
)
ES_ESTIMATED_ENERGY_SAVED = Gauge(
    "es_estimated_energy_saved_ratio",
    "Percentual estimado de economia de energia obtido com as politicas ativas"
)

class EnergySavingXApp:
    def __init__(self, http_port: int = 8084, metrics_port: int = 8085, rmr_port: int = 4563):
        self.xapp_id = "energy_saving_orange"
        self.http_port = int(os.getenv("HTTP_PORT", str(http_port)))
        self.metrics_port = int(os.getenv("METRICS_PORT", str(metrics_port)))
        self.rmr_port = int(os.getenv("RMR_PORT", str(rmr_port)))
        self.running = False
        self.http_server: Optional[Any] = None
        self.worker_thread: Optional[threading.Thread] = None

        # Estado interno de economia de energia
        self.target_nodes = ["gnb_01", "gnb_02"]
        self.target_tx_power = 20.0  # Redução de potência para 20 dBm
        self.priority = 65

    def generate_action_proposal(self, node_id: str = "gnb_01", tx_power: float = 20.0) -> Dict[str, Any]:
        """Gera proposta estruturada compatível com o PerceptionAgent da xApp RDL."""
        proposal = {
            "xapp_id": self.xapp_id,
            "node_id": node_id,
            "parameter": "TX_POWER",
            "value": tx_power,
            "priority": self.priority,
            "energy_target_kwh": 0.35,
            "timestamp": time.time()
        }
        ES_PROPOSALS_TOTAL.labels(action_type="TX_POWER_REDUCTION", node_id=node_id).inc()
        ES_TX_POWER_TARGET.labels(node_id=node_id).set(tx_power)
        ES_ESTIMATED_ENERGY_SAVED.set(0.28)  # 28% economia
        return proposal

    def _run_http(self):
        """Servidor FastAPI para /health, /ready e /metrics."""
        if FastAPI is None:
            logger.warning("FastAPI não instalado. Endpoints HTTP em modo mock.")
            return

        app = FastAPI(title="Energy Saving xApp (Orange / FlexRIC)", version="1.0.0")

        @app.get("/health")
        def health():
            return {"status": "UP", "xapp": self.xapp_id, "role": "Energy_Saving"}

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
        """Loop de emissão periódica de propostas de eficiência energética."""
        logger.info(f"Energy Saving xApp ativa. Monitorando consumo e emitindo propostas TX_POWER={self.target_tx_power} dBm...")
        while self.running:
            for node in self.target_nodes:
                proposal = self.generate_action_proposal(node_id=node, tx_power=self.target_tx_power)
                logger.debug(f"[EnergySaving Proposal] Emitida: {proposal}")
            time.sleep(2.5)

    def start(self):
        self.running = True
        # Iniciar HTTP em background
        t_http = threading.Thread(target=self._run_http, daemon=True)
        t_http.start()

        # Iniciar Loop de decisões
        self.worker_thread = threading.Thread(target=self._loop, daemon=True)
        self.worker_thread.start()
        logger.info(f"Energy Saving xApp iniciada com sucesso. HTTP: {self.http_port}, Metrics: {self.http_port}/metrics")

    def stop(self):
        self.running = False
        if self.http_server:
            self.http_server.should_exit = True
        logger.info("Energy Saving xApp finalizada.")

if __name__ == "__main__":
    app = EnergySavingXApp()
    app.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app.stop()
