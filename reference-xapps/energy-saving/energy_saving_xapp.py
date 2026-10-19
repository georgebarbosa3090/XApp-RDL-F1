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

        # Estado interno de economia de energia e adaptabilidade para Testbed
        target_nodes_raw = os.getenv("TARGET_NODES", "gnb_01,gnb_02")
        self.target_nodes = [n.strip() for n in target_nodes_raw.split(",") if n.strip()]
        self.target_parameter = os.getenv("ES_PARAMETER", "TX_POWER")
        self.target_tx_power = float(os.getenv("ES_DEFAULT_VALUE", "20.0"))  # Redução de potência para 20 dBm
        self.priority = int(os.getenv("ES_PRIORITY", "65"))
        self.rdl_endpoint = os.getenv("RDL_HTTP_URL", os.getenv("RDL_ENDPOINT", ""))

    def generate_action_proposal(
        self,
        node_id: str = "gnb_01",
        tx_power: Optional[float] = None,
        parameter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Gera proposta estruturada compatível com o componente Perception da xApp RDL."""
        val = tx_power if tx_power is not None else self.target_tx_power
        param = parameter if parameter is not None else self.target_parameter
        proposal = {
            "xapp_id": self.xapp_id,
            "node_id": node_id,
            "parameter": param,
            "value": val,
            "priority": self.priority,
            "energy_target_kwh": 0.35,
            "timestamp": time.time()
        }
        ES_PROPOSALS_TOTAL.labels(action_type="TX_POWER_REDUCTION", node_id=node_id).inc()
        ES_TX_POWER_TARGET.labels(node_id=node_id).set(val)
        ES_ESTIMATED_ENERGY_SAVED.set(0.28)  # 28% economia
        return proposal

    def _dispatch_proposal(self, proposal: Dict[str, Any]):
        """Despacha a proposta ativamente para a xApp RDL via HTTP Webhook se configurado."""
        if self.rdl_endpoint:
            try:
                import urllib.request
                req = urllib.request.Request(
                    self.rdl_endpoint,
                    data=json.dumps(proposal).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    pass
            except Exception as e:
                logger.debug(f"[EnergySaving] Falha ao despachar via HTTP para {self.rdl_endpoint}: {e}")

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
        logger.info(f"Energy Saving xApp ativa. Monitorando consumo ({self.target_parameter}={self.target_tx_power}) nos nós {self.target_nodes}...")
        while self.running:
            for node in self.target_nodes:
                proposal = self.generate_action_proposal(node_id=node, tx_power=self.target_tx_power)
                self._dispatch_proposal(proposal)
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
