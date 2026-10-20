"""
Energy Saving Reference xApp (Green RAN & Cell Sleep Optimizer - GreenRAN Edition)
Baseado em: Orange-OpenSource/ns-O-RAN-flexric (xapp_es_with_cell_util)
Adaptado para o Projeto GreenRAN (UFPA / OpenRAN@Brasil - Agro 4.0 e Smart Campus)

Papel no RDL / GreenRAN:
Controladora de Eficiência Energética sustentável com consciência de:
- Estado de Bateria (State-of-Charge - SoC) e Geração Fotovoltaica em nós rurais remotos.
- Proteção de Cobertura Rural (Rural Coverage Guard) para evitar isolamento de UEs/sensores de borda.
- Modos graduados de sono: Micro-Sleep (símbolos OFDM), Redução de Potência e Carrier Shutdown.
- Respeito aos limites físicos de rádio SDR COTS (23 dBm em bancada indoor USRP B210/N310).
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
    ["action_type", "node_id", "greenran_env"]
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
ES_BATTERY_SOC = Gauge(
    "es_battery_soc_ratio",
    "Nivel de carga da bateria (State of Charge - SoC) do nó remoto off-grid",
    ["node_id"]
)
ES_SOLAR_POWER_WATTS = Gauge(
    "es_solar_power_watts",
    "Potencia gerada instantaneamente pelos paineis solares",
    ["node_id"]
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

        # Estado interno de economia de energia e adaptabilidade para Testbed GreenRAN
        target_nodes_raw = os.getenv("TARGET_NODES", "gnb_01,gnb_02")
        self.target_nodes = [n.strip() for n in target_nodes_raw.split(",") if n.strip()]
        
        # Ambiente operacional GreenRAN: "AGRO_RURAL_OFFGRID" ou "CAMPUS_SMART_GRID"
        self.greenran_env = os.getenv("GREENRAN_ENV", "AGRO_RURAL_OFFGRID").upper().strip()
        self.target_parameter = os.getenv("ES_PARAMETER", "TX_POWER")
        
        # Limites físicos de rádio (em bancada/indoor COTS USRP limite é 23 dBm)
        self.max_allowed_tx_power = float(os.getenv("MAX_ALLOWED_TX_POWER", "23.0"))
        self.target_tx_power = float(os.getenv("ES_DEFAULT_VALUE", "20.0"))
        self.priority = int(os.getenv("ES_PRIORITY", "65"))
        self.rdl_endpoint = os.getenv("RDL_HTTP_URL", os.getenv("RDL_ENDPOINT", ""))

        # Parâmetros de sustentabilidade e renováveis (Agro 4.0)
        self.battery_soc = float(os.getenv("BATTERY_SOC_PERCENT", "75.0")) / 100.0  # 0.0 a 1.0
        self.solar_connected = os.getenv("SOLAR_PANEL_CONNECTED", "true").lower() in ("1", "true", "yes")
        self.solar_power_w = float(os.getenv("SOLAR_POWER_WATTS", "120.0")) if self.solar_connected else 0.0
        self.rural_coverage_guard = os.getenv("RURAL_COVERAGE_GUARD", "true").lower() in ("1", "true", "yes")

    def decide_energy_policy(self, node_id: str) -> Dict[str, Any]:
        """
        Calcula a política ótima de economia de energia baseada na telemetria ecológica.
        - Em AGRO_RURAL_OFFGRID: Se bateria estiver baixa (< 30%), propõe Micro-Sleep e redução controlada de TxPower sem criar buraco de cobertura.
        - Em CAMPUS_SMART_GRID: Aplica corte noturno de portadoras secundárias ou Micro-Sleep diurno.
        """
        action_type = "TX_POWER_REDUCTION"
        param = self.target_parameter
        power_val = min(self.target_tx_power, self.max_allowed_tx_power)

        if self.greenran_env == "AGRO_RURAL_OFFGRID":
            # No Agro, se bateria < 35%, entra em modo de contingência severa
            if self.battery_soc < 0.35:
                action_type = "MICRO_SLEEP_AND_THROTTLING"
                # Cobertura rural mínima não pode cair abaixo de 18 dBm para não desconectar tratores de borda
                power_val = 18.0 if self.rural_coverage_guard else 15.0
                target_kwh = 0.15
            else:
                action_type = "MODERATE_POWER_SCALING"
                power_val = 21.0
                target_kwh = 0.28
        else:
            # Em Campus universitário com regime circadiano
            action_type = "CARRIER_MICRO_SLEEP"
            power_val = 20.0
            target_kwh = 0.25

        return {
            "action_type": action_type,
            "parameter": param,
            "target_value": power_val,
            "energy_target_kwh": target_kwh
        }

    def generate_action_proposal(
        self,
        node_id: str = "gnb_01",
        tx_power: Optional[float] = None,
        parameter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Gera proposta estruturada compatível com o componente Perception da xApp RDL / GreenRAN."""
        policy = self.decide_energy_policy(node_id)
        val = tx_power if tx_power is not None else policy["target_value"]
        param = parameter if parameter is not None else policy["parameter"]

        proposal = {
            "xapp_id": self.xapp_id,
            "node_id": node_id,
            "parameter": param,
            "value": round(val, 2),
            "priority": self.priority,
            "greenran_env": self.greenran_env,
            "action_strategy": policy["action_type"],
            "energy_target_kwh": policy["energy_target_kwh"],
            "telemetry_context": {
                "battery_soc_ratio": round(self.battery_soc, 2),
                "solar_power_watts": round(self.solar_power_w, 1),
                "rural_coverage_guard_active": self.rural_coverage_guard,
                "prohibit_urllc_degradation": True
            },
            "timestamp": time.time()
        }

        ES_PROPOSALS_TOTAL.labels(
            action_type=policy["action_type"],
            node_id=node_id,
            greenran_env=self.greenran_env
        ).inc()
        ES_TX_POWER_TARGET.labels(node_id=node_id).set(val)
        ES_BATTERY_SOC.labels(node_id=node_id).set(self.battery_soc)
        ES_SOLAR_POWER_WATTS.labels(node_id=node_id).set(self.solar_power_w)
        ES_ESTIMATED_ENERGY_SAVED.set(0.32 if self.battery_soc < 0.35 else 0.22)

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

        app = FastAPI(title="Energy Saving xApp (GreenRAN Edition)", version="2.0.0")

        @app.get("/health")
        def health():
            return {
                "status": "UP",
                "xapp": self.xapp_id,
                "role": "Energy_Saving",
                "greenran_env": self.greenran_env,
                "battery_soc": self.battery_soc,
                "solar_power_w": self.solar_power_w
            }

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
        logger.info(
            f"Energy Saving xApp (GreenRAN Edition) ativa. Ambiente={self.greenran_env}, "
            f"SoC={self.battery_soc*100}%, Solar={self.solar_power_w}W, Nós={self.target_nodes}..."
        )
        while self.running:
            for node in self.target_nodes:
                proposal = self.generate_action_proposal(node_id=node)
                self._dispatch_proposal(proposal)
                logger.debug(f"[EnergySaving GreenRAN Proposal] Emitida: {proposal}")
            time.sleep(2.5)

    def start(self):
        self.running = True
        t_http = threading.Thread(target=self._run_http, daemon=True)
        t_http.start()

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
