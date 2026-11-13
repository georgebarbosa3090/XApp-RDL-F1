# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
Rogue Stress Reference xApp (6G Cross-Tier Governance & Security Evaluation)
Papel no RDL: Emuladora de xApp de terceiro descalibrada ou maliciosa.
Escrita para este projeto. Alterna TX_POWER entre 45 dBm (fora do limite) e 5 dBm a cada
0,5 s para exercitar o Safety Guard e a histerese da RDL. Não gera PRB_QUOTA inválida (a
proposta insegura de PRB está no cenário S7 do catálogo) e não envia as propostas à RDL.
"""

import time
import os
import threading
import logging
from typing import Dict, Any, Optional

import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from rdl_transport import RdlTransport  # noqa: E402  entrega por RMR 30000 / resultado 30001

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [Rogue-xApp] %(message)s')
logger = logging.getLogger("rogue_xapp")

ROGUE_PROPOSALS_TOTAL = Counter(
    "rogue_proposals_total",
    "Total de propostas conflitantes emitidas pela Rogue xApp",
    ["node_id", "parameter"]
)

class RogueXApp:
    def __init__(self, http_port: int = 8092, metrics_port: int = 8093, rmr_port: int = 4567):
        self.xapp_id = "rogue_vendor_stress_6g"
        self.http_port = int(os.getenv("HTTP_PORT", str(http_port)))
        self.metrics_port = int(os.getenv("METRICS_PORT", str(metrics_port)))
        self.rmr_port = int(os.getenv("RMR_PORT", str(rmr_port)))
        self.transport = RdlTransport(self.xapp_id, rmr_port=self.rmr_port)
        self.running = False
        self.http_server: Optional[Any] = None
        self.worker_thread: Optional[threading.Thread] = None

        self.target_nodes = ["gnb_01", "gnb_02"]
        self.toggle = False
        self.priority = 50

    def generate_action_proposal(self, node_id: str = "gnb_01") -> Dict[str, Any]:
        """Gera propostas com oscilacao continua (Parameter Flipping) para testar histerese e seguranca."""
        self.toggle = not self.toggle
        power_val = 45.0 if self.toggle else 5.0 # Alterna entre potencia excessiva (fora de faixa) e permitida
        
        proposal = {
            "xapp_id": self.xapp_id,
            "node_id": node_id,
            "parameter": "TX_POWER",
            "value": power_val,
            "priority": self.priority,
            "slice_type": "BestEffort",
            "timestamp": time.time()
        }
        ROGUE_PROPOSALS_TOTAL.labels(node_id=node_id, parameter="TX_POWER").inc()
        return proposal

    def _run_http(self):
        if FastAPI is None:
            return

        app = FastAPI(title="Rogue Stress xApp (Security & Flapping Test)", version="1.0.0")

        @app.get("/health")
        def health():
            return {"status": "UP", "xapp": self.xapp_id, "role": "Rogue_Stress_Tester"}

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
        """Propõe só a partir do KPM (núcleo src.xapps.derivadas.RogueDerivada; reference-xapps/common/kpm_runtime.py)."""
        from kpm_runtime import make_core, run_kpm_loop
        from src.xapps.derivadas import RogueDerivada
        self.core = make_core(RogueDerivada, self.transport)
        run_kpm_loop(self, self.core, 0.5)

    def start(self):
        self.running = True
        self.transport.start()
        t_http = threading.Thread(target=self._run_http, daemon=True)
        t_http.start()
        self.worker_thread = threading.Thread(target=self._loop, daemon=True)
        self.worker_thread.start()
        logger.info(f"Rogue xApp iniciada. HTTP: {self.http_port}")

    def stop(self):
        self.running = False
        self.transport.stop()
        if self.http_server:
            self.http_server.should_exit = True
        logger.info("Rogue xApp finalizada.")

if __name__ == "__main__":
    app = RogueXApp()
    app.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app.stop()
