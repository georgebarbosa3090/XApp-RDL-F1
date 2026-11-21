# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
URLLC Slice Guard: xApp própria que protege a fatia URLLC limitando a fatia eMBB da célula, a partir do KPM.

Implantação no Near-RT RIC do O-RAN SC (chart deploy/helm/xapp-urllc-slice-guard). A decisão é a do núcleo
``src.xapps.proprias.UrllcSliceGuard``, o mesmo da malha fechada do ns-3 e da bancada NORI:

1. KPM: subscrição E2SM-KPM no SubMgr e Indications pela RMR 12050 (``reference-xapps/common/kpm_runtime.py``).
   A fatia de cada UE vem da medida ``DRB.NetworkSlicing.SST`` e o atraso, de ``DRB.RlcSduDelayDl``;
2. decisão a cada ``DECISION_PERIOD_S``: proteger (teto eMBB baixo) quando o atraso da URLLC passa do limite,
   relaxar com histerese;
3. proposta à RDL pela RMR ``RDL_ACTION_PROPOSAL`` (30000); a recusa volta por ``RDL_ACTION_RESULT`` (30001)
   e devolve a célula ao estado anterior no núcleo.

Sem KPM (``SUBMGR_URL`` vazio ou subscrição recusada) a xApp não propõe nada. Não há carga simulada, perfil
fixo nem métrica estimada: os contadores e medidores de ``/metrics`` vêm das propostas enviadas, das recusas
recebidas e do atraso medido. Até 2026-11-21 esta xApp era ``reference-xapps/qos-xslice`` (``xslice_xapp.py``),
inspirada no xSlice (``peihaoY/xslice-oran``), com carga simulada (``SIMULATED_TRAFFIC_LOAD``) e metadados de
energia fixos; esses trechos foram retirados.
"""

import logging
import os
import sys
import threading
import time
from typing import Any, Dict, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "common"))
sys.path.insert(0, os.path.join(_HERE, "..", ".."))
from rdl_transport import RdlTransport  # noqa: E402  entrega por RMR 30000 / resultado 30001

try:
    from fastapi import FastAPI
    from uvicorn import Config, Server
    from prometheus_client import Counter, Gauge, generate_latest
except ImportError:  # pragma: no cover - imagem sem FastAPI/Prometheus
    FastAPI = None
    Server = None

    class _NoMetric:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

    Counter = Gauge = _NoMetric

    def generate_latest():
        return b""

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [urllc-slice-guard] %(message)s")
logger = logging.getLogger("urllc_slice_guard_xapp")

PROPOSALS = Counter("usg_proposals_total", "Propostas enviadas à RDL", ["node_id", "kind"])
REFUSALS = Counter("usg_refusals_total", "Propostas recusadas pela RDL (RMR 30001)", ["node_id", "reason"])
URLLC_DELAY = Gauge("usg_urllc_delay_ms", "Maior atraso da fatia URLLC medido no KPM", ["node_id"])
EMBB_CAP = Gauge("usg_embb_cap_pct", "Último teto eMBB proposto (PRB_QUOTA)", ["node_id"])


class UrllcSliceGuardXApp:
    """Processo da xApp: KPM do RIC, núcleo ``UrllcSliceGuard``, transporte RMR e API HTTP."""

    def __init__(self, http_port: int = 8082, rmr_port: int = 4562, transport: Optional[Any] = None):
        from src.xapps.proprias import UrllcSliceGuard
        self.http_port = int(os.getenv("HTTP_PORT", str(http_port)))
        self.rmr_port = int(os.getenv("RMR_PORT", str(rmr_port)))
        self.period_s = float(os.getenv("DECISION_PERIOD_S", "1.0"))
        self.transport = transport or RdlTransport(UrllcSliceGuard.XAPP_ID, rmr_port=self.rmr_port)
        self.core = UrllcSliceGuard(transport=self.transport)
        self.transport.on_result = self._on_result      # recusa: métrica e estado do núcleo
        self.xapp_id = self.core.XAPP_ID
        self.last_proposal: Optional[Dict[str, Any]] = None
        self.kpm_attached = False
        self.running = False
        self.http_server: Optional[Any] = None
        self.worker_thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------ decisão
    def _on_result(self, result: Dict[str, Any]) -> None:
        REFUSALS.labels(node_id=str(result.get("node_id")), reason=str(result.get("reason", ""))).inc()
        self.core.on_result(result)
        node = result.get("node_id")
        if node in self.core.cap_pct:
            EMBB_CAP.labels(node_id=node).set(self.core.cap_pct[node])

    def step(self, now: Optional[float] = None) -> list:
        """Uma decisão com o KPM já observado; envia as propostas à RDL e atualiza as métricas."""
        proposals = self.core.decide(time.time() if now is None else now)
        for cell, delay in self.core.last_delay_ms.items():
            URLLC_DELAY.labels(node_id=cell).set(delay)
        for p in proposals:
            self.transport.send(p)
            self.last_proposal = p
            kind = "proteger" if p["priority"] == int(self.core.policy()["usg_priority"]) else "relaxar"
            PROPOSALS.labels(node_id=p["node_id"], kind=kind).inc()
            EMBB_CAP.labels(node_id=p["node_id"]).set(p["value"])
            logger.info("proposta %s: %s PRB_QUOTA=%.0f (prioridade %d)", kind, p["node_id"], p["value"],
                        p["priority"])
        return proposals

    def _loop(self) -> None:
        from kpm_runtime import attach_kpm
        self.kpm_attached = attach_kpm(self.core)
        while self.running:
            self.step()
            time.sleep(self.period_s)

    # ------------------------------------------------------------------ HTTP
    def _run_http(self) -> None:
        if FastAPI is None:
            logger.warning("FastAPI não instalado: sem /health, /ready e /metrics")
            return
        app = FastAPI(title="URLLC Slice Guard", version="2.0.0")

        @app.get("/health")
        def health():
            return {"status": "UP", "xapp": self.xapp_id}

        @app.get("/ready")
        def ready():
            return {"ready": self.kpm_attached, "xapp": self.xapp_id, "kpm": self.kpm_attached}

        @app.get("/metrics")
        def metrics():
            from fastapi.responses import Response
            return Response(content=generate_latest(), media_type="text/plain")

        @app.get("/proposals/latest")
        def latest_proposal():
            return self.last_proposal or {}

        @app.get("/state")
        def state():
            return {"protecting": self.core.protecting, "embb_cap_pct": self.core.cap_pct,
                    "urllc_delay_ms": self.core.last_delay_ms, "policy": self.core.policy()}

        self.http_server = Server(Config(app=app, host="0.0.0.0", port=self.http_port, log_level="warning"))
        self.http_server.run()

    # ------------------------------------------------------------------ ciclo de vida
    def start(self) -> None:
        self.running = True
        self.transport.start()
        threading.Thread(target=self._run_http, daemon=True).start()
        self.worker_thread = threading.Thread(target=self._loop, daemon=True)
        self.worker_thread.start()
        logger.info("URLLC Slice Guard iniciada: HTTP %s, RMR %s", self.http_port, self.rmr_port)

    def stop(self) -> None:
        self.running = False
        self.transport.stop()
        if self.http_server:
            self.http_server.should_exit = True
        logger.info("URLLC Slice Guard finalizada")


if __name__ == "__main__":
    xapp = UrllcSliceGuardXApp()
    xapp.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        xapp.stop()
