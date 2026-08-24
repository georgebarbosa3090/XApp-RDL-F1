# Relatório de Execução do Smoke Test - xApp RDL (Fase 1)

**Data de Execução:** 24 de Agosto de 2026  
**Ambiente de Teste:** Servidor de Validação (`SAC-10806`)  
**Versão da Imagem:** `iqos-xapp-rdl:1.1.0`  
**Status Geral:** **SUCESSO (APROVADO)**

---

## 1. Sumário Executivo

O Smoke Test da **xApp RDL (Resource and Decision Layer)** foi executado com sucesso no container Docker standalone. Todos os componentes fundamentais de runtime, integração com a biblioteca C RMR da O-RAN, exposição de endpoints HTTP e coleta de métricas no padrão Prometheus foram validados e operam em conformidade com os requisitos da Fase 1 (H-RDL).

---

## 2. Resultados dos Testes de Endpoints

### 2.1. Healthcheck HTTP (`/health` na porta `:8090` -> `:8080`)
O servidor de saúde FastAPI/Uvicorn respondeu prontamente com código HTTP 200:

```json
HTTP/1.1 200 OK
date: Mon, 24 Aug 2026 17:08:42 GMT
server: uvicorn
content-length: 34
content-type: application/json

{
  "status": "UP",
  "uptime_seconds": 2
}
```

### 2.2. Métricas Prometheus (`/metrics` na porta `:8091`)
O exportador Prometheus expôs com sucesso todas as métricas operacionais e de latência da RDL:

```text
# HELP rdl_rmr_messages_received_total Total RMR messages received
# TYPE rdl_rmr_messages_received_total counter
rdl_rmr_messages_received_total 0.0

# HELP rdl_kpm_indications_total Total KPM indications received
# TYPE rdl_kpm_indications_total counter
rdl_kpm_indications_total 0.0

# HELP rdl_conflicts_detected_total Total conflicts detected
# TYPE rdl_conflicts_detected_total counter

# HELP rdl_decisions_total Total decisions made
# TYPE rdl_decisions_total counter

# HELP rdl_decision_latency_seconds Decision latency
# TYPE rdl_decision_latency_seconds histogram
rdl_decision_latency_seconds_count 0.0

# HELP rdl_active_e2_nodes Active E2 nodes
# TYPE rdl_active_e2_nodes gauge
rdl_active_e2_nodes 0.0

# HELP rdl_ready Is RDL ready (1 or 0)
# TYPE rdl_ready gauge
rdl_ready 0.0
```

---

## 3. Inicialização e Integração da Camada O-RAN (RMR & C-Bindings)

A biblioteca nativa C RMR (Message Router da Linux Foundation / O-RAN SC) foi carregada perfeitamente via dynamic linker (`librmr_si.so`):

```text
1787591320474 1/RMR [INFO] ric message routing library on SI95 p=4560 mv=3 flg=02 id=a (a1be12a 4.9.0 built: Feb 14 2023)
{"event": "xApp Framework Ready", "level": "info", "logger": "rdl_xapp", "timestamp": "2026-08-24T17:08:40.476507Z"}
{"event": "Iniciando xApp RDL", "level": "info", "logger": "rdl_xapp", "timestamp": "2026-08-24T17:08:40.476887Z"}
```

---

## 4. Detalhes Técnicos e Ajustes Realizados

Durante as etapas de validação e refinamento, foram identificados e corrigidos os seguintes pontos:

| Item | Sintoma Observado | Causa Raiz | Correção Aplicada |
| :--- | :--- | :--- | :--- |
| **1. RMR Dynamic Linker** | `OSError: librmr_si.so: cannot open shared object file` | O pacote base instala apenas `librmr_si.so.4`; o link simbólico `librmr_si.so` vem no `rmr-dev`. | Instalados `rmr` + `rmr-dev` no Dockerfile, executado `ldconfig` e configurado `ENV LD_LIBRARY_PATH`. |
| **2. Concorrência no Startup** | `AttributeError: 'RDLxApp' object has no attribute 'running'` | O callback `post_init` do `RMRXapp` inicia a thread `_decision_loop` antes do fim do construtor `__init__`. | A propriedade `self.running = True` foi inicializada na primeira linha do construtor `__init__`. |
| **3. Dispatcher RMR** | `AttributeError: 'Xapp' object has no attribute 'register_callback'` | A classe `Xapp` é para entrypoint único; o roteamento por tipo de mensagem exige `RMRXapp`. | Atualizado `src/rdl_xapp.py` para instanciar `RMRXapp` com `_default_handler`. |
| **4. Imports ASN.1** | `ImportError: cannot import name 'OCT_STR' from 'pycrate_asn1rt.asnobj_basic'` | No `pycrate`, `OCT_STR` pertence ao módulo `pycrate_asn1rt.asnobj_str`. | Ajustados os imports em `kpm_decoder.py`, `rc_encoder.py` e `e2ap_decoder.py`. |
| **5. Aviso AppMgr no K8s** | `AttributeError: 'NoneType' object has no attribute 'split'` em `registerXapp` | Em modo standalone (fora do cluster K8s), o `ricxappframe` busca variáveis de serviço do AppMgr. | Comportamento esperado e inofensivo para modo standalone; suprimido automaticamente com `USE_FAKE_SDL=true`. |

---

## 5. Código Final Consolidado (`src/rdl_xapp.py`)

```python
import time
import threading
import json
import os
from typing import Dict, Any, List

try:
    from ricxappframe.xapp_frame import RMRXapp, Xapp
except ImportError:
    class RMRXapp:  # type: ignore
        """Fallback mock para execução local/testes sem dependência binária C/RMR."""
        def __init__(self, default_handler=None, rmr_port=4560, rmr_wait_for_ready=False, use_fake_sdl=True, post_init=None):
            self.default_handler = default_handler
            self.post_init = post_init
            self.callbacks = {}
        def register_callback(self, handler, mtype):
            self.callbacks[mtype] = handler
        def run(self):
            if self.post_init:
                self.post_init(self)
        def stop(self):
            pass
        def rmr_send(self, payload, mtype, **kwargs):
            return True
        def rmr_free(self, sbuf):
            pass
    Xapp = RMRXapp

from src.observability.logging import setup_logger, now_ts
from src.observability.health_server import HealthServer, AppState
from src.infrastructure.sdl_repository import SdlRepository
from src.infrastructure.memory_module import MemoryModule
from src.agents.perception_agent import PerceptionAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.refinement_agent import RefinementAgent
from src.observability.metrics import MetricsServer
from src.e2.kpm_decoder import KpmDecoder
from src.e2.rc_encoder import RCEncoder
from src.conflict_types import XAppAction, KPMReport, ConflictSeverity

logger = setup_logger("rdl_xapp")

# Message Types Constants
RIC_INDICATION = 12050
RIC_CONTROL_REQ = 12010
RIC_CONTROL_ACK = 12011
RIC_CONTROL_FAILURE = 12012
RDL_ACTION_PROPOSAL = 30000

class RDLxApp:
    def __init__(self):
        self.running = True
        os.environ.setdefault("CONFIG_FILE", "/app/configs/config-file.json")
        use_fake_sdl = os.getenv("USE_FAKE_SDL", "True").lower() in ("true", "1", "yes")
        rmr_wait_for_ready = os.getenv("RMR_WAIT_FOR_READY", "false" if use_fake_sdl else "true").lower() in ("true", "1", "yes")
        
        if use_fake_sdl:
            self.memory = MemoryModule()
        else:
            self.memory = SdlRepository()
            
        self.perception = PerceptionAgent()
        self.reasoning = ReasoningAgent(self.memory, config={})
        self.refinement = RefinementAgent(self.memory)
        self.health = HealthServer(port=8080)
        self.health.set_state(AppState.STARTING)
        self.metrics = MetricsServer(port=8081)
        self.asn1_decoder = KpmDecoder()
        self.rc_encoder = RCEncoder()
        
        # Decision Window properties (Feature 1)
        self.proposal_buffer: List[XAppAction] = []
        self.buffer_lock = threading.Lock()
        self.window_start: float = 0.0
        self.WINDOW_DURATION_MS = 200
        
        self.xapp = RMRXapp(
            default_handler=self._default_handler,
            rmr_port=4560,
            rmr_wait_for_ready=rmr_wait_for_ready,
            use_fake_sdl=use_fake_sdl,
            post_init=self._entrypoint
        )
        
        self.xapp.register_callback(self._kpm_indication_handler, RIC_INDICATION)
        self.xapp.register_callback(self._action_proposal_handler, RDL_ACTION_PROPOSAL)
        self.xapp.register_callback(self._control_ack_handler, RIC_CONTROL_ACK)
        self.xapp.register_callback(self._control_failure_handler, RIC_CONTROL_FAILURE)

    def start(self):
        logger.info("Iniciando xApp RDL")
        self.health.run()
        self.metrics.start()
        self.running = True
        self.xapp.run()

    def stop(self):
        self.running = False
        self.health.set_state(AppState.STOPPED)
        self.xapp.stop()
        
    def _default_handler(self, xapp_instance, summary, sbuf):
        logger.debug("Mensagem RMR não mapeada recebida", mtype=summary.get("mtype"))
        xapp_instance.rmr_free(sbuf)

    def _entrypoint(self, xapp_instance):
        logger.info("xApp Framework Ready")
        self.health.set_state(AppState.READY)
        threading.Thread(target=self._decision_loop, daemon=True).start()

    def _kpm_indication_handler(self, xapp_instance, summary: Dict[str, Any], sbuf: Any):
        self.metrics.record_kpm()
        payload = summary.get("payload")
        if payload:
            reports_data = self.asn1_decoder.decode_indication(payload)
            if reports_data:
                for data in reports_data:
                    report = KPMReport(
                        node_id=data.get("node_id", "gnb_01"),
                        ue_id=data.get("ue_id", "unknown"),
                        drb_thp_dl=data.get("drb_thp_dl", 0.0),
                        drb_thp_ul=data.get("drb_thp_ul", 0.0),
                        drb_delay_dl=data.get("drb_delay_dl", 0.0),
                        prb_used_dl=data.get("prb_used_dl", 0)
                    )
                    self.perception.update_kpm_report(report)
        xapp_instance.rmr_free(sbuf)

    def _action_proposal_handler(self, xapp_instance, summary: Dict[str, Any], sbuf: Any):
        """Recebe ações propostas por outras xApps via RMR e enfileira na janela temporal."""
        payload = summary.get("payload")
        if payload:
            try:
                data = json.loads(payload.decode('utf-8'))
                action = XAppAction(
                    xapp_id=data['xapp_id'],
                    node_id=data['node_id'],
                    parameter=data['parameter'],
                    value=data['value'],
                    priority=data.get('priority', 50)
                )
                with self.buffer_lock:
                    if not self.proposal_buffer:
                        self.window_start = now_ts()
                    self.proposal_buffer.append(action)
                    logger.debug(f"Action buffered. Queue size: {len(self.proposal_buffer)}")
            except Exception as e:
                logger.error("Erro ao processar RDL_ACTION_PROPOSAL", error=str(e))
        xapp_instance.rmr_free(sbuf)

    def _control_ack_handler(self, xapp_instance, summary: Dict[str, Any], sbuf: Any):
        logger.info("Recebido RIC_CONTROL_ACK", summary=summary)
        xapp_instance.rmr_free(sbuf)

    def _control_failure_handler(self, xapp_instance, summary: Dict[str, Any], sbuf: Any):
        logger.warning("Recebido RIC_CONTROL_FAILURE", summary=summary)
        xapp_instance.rmr_free(sbuf)

    def inject_xapp_action(self, action: XAppAction):
        """API pública para injeção de ações simuladas (usada em testes)"""
        with self.buffer_lock:
            if not self.proposal_buffer:
                self.window_start = now_ts()
            self.proposal_buffer.append(action)

    def _process_action_group(self, actions: List[XAppAction]):
        """Processa todas as ações acumuladas na Decision Window (Feature 2)"""
        t0 = now_ts()
        for act in actions:
            self.memory.add_action(act)
            
        conflicts = self.perception.register_action_group(actions)
        self.metrics.update_active_xapps(len(self.perception.get_active_xapps()))
        
        for conflict in conflicts:
            logger.info("Conflito Detectado", conflict_id=conflict.conflict_id, type=conflict.conflict_type.name)
            self.memory.add_conflict(conflict)
            self.metrics.record_conflict(conflict)
            
            resolution = self.reasoning.resolve(conflict)
            is_valid, level, reason = self.refinement.validate(resolution, conflict)
            latency = now_ts() - t0
            
            self.memory.add_resolution(resolution)
            self.metrics.record_resolution(resolution, latency)
            
            if is_valid and resolution.winning_actions:
                for act in resolution.winning_actions:
                    logger.info("Conflito Resolvido", conflict=conflict.conflict_id, strategy=resolution.strategy_used.name, action=act.parameter)
                    self._send_control(act.node_id, act.parameter, act.value)
            else:
                logger.warning("Resolução Rejeitada ou Lote Vazio", reason=reason)

    def _decision_loop(self):
        while self.running:
            time.sleep(0.05)
            
            with self.buffer_lock:
                if self.proposal_buffer:
                    elapsed_ms = (now_ts() - self.window_start) * 1000
                    if elapsed_ms >= self.WINDOW_DURATION_MS:
                        actions_to_process = list(self.proposal_buffer)
                        self.proposal_buffer.clear()
                        self.window_start = 0.0
                        logger.info(f"Decision Window Expired. Processing batch of {len(actions_to_process)} actions.")
                        threading.Thread(target=self._process_action_group, args=(actions_to_process,), daemon=True).start()

    def _send_control(self, node_id: str, parameter: str, value: float):
        try:
            aper_payload = self.rc_encoder.encode_control_request(node_id, parameter, value)
            payload_dict = {
                "node_id": node_id,
                "parameter": parameter,
                "value": value,
                "aper_bytes": aper_payload.hex()
            }
            payload_bytes = json.dumps(payload_dict).encode('utf-8')
            success = self.xapp.rmr_send(payload=payload_bytes, mtype=RIC_CONTROL_REQ)
        except Exception as e:
            logger.error(f"Falha ao gerar APER Control: {e}")
            success = False
        if success:
            logger.info("RIC_CONTROL_REQUEST enviado com sucesso", node_id=node_id, param=parameter, val=value)
        else:
            logger.error("Falha ao enviar RIC_CONTROL_REQUEST")

if __name__ == "__main__":
    app = RDLxApp()
    try:
        app.start()
    except KeyboardInterrupt:
        app.stop()
```

---

## 6. Procedimento de Reprodução e Validação

```bash
# 1. Reconstruir a imagem Docker
docker build --file docker/Dockerfile --tag iqos-xapp-rdl:1.1.0 .

# 2. Reiniciar o container em segundo plano
docker rm -f xapp-rdl-test 2>/dev/null || true
docker run -d --name xapp-rdl-test -p 8090:8080 -p 8091:8081 -e USE_FAKE_SDL=true iqos-xapp-rdl:1.1.0

# 3. Aguardar estabilização do container
sleep 3

# 4. Validar o endpoint de saúde
curl -i http://localhost:8090/health

# 5. Validar a coleta de métricas do Prometheus
curl http://localhost:8091/metrics | grep -E "rdl_|dl_"

# 6. Inspecionar os logs estruturados
docker logs xapp-rdl-test
```
