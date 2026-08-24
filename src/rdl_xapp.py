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

    def _kpm_indication_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
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

    def _action_proposal_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
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

    def _control_ack_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        logger.info("Recebido RIC_CONTROL_ACK", summary=summary)
        xapp_instance.rmr_free(sbuf)

    def _control_failure_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
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
        
        # Resolve conflitos do grupo
        for conflict in conflicts:
            logger.info("Conflito Detectado", conflict_id=conflict.conflict_id, type=conflict.conflict_type.name)
            self.memory.add_conflict(conflict)
            self.metrics.record_conflict(conflict)
            
            resolution = self.reasoning.resolve(conflict)
            # Para validação, passamos a primeira ação ou validamos separadamente
            # Assumimos que Refinement pode validar um lote ou validamos 1 a 1.
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

        # Se alguma ação da janela não esteve em conflito, ela deveria ser executada livremente.
        # Aqui, para simplificar o protótipo, assumimos que as ações sem conflito 
        # (não retornadas pela Perception) podem ser enviadas diretamente se o caso permitir.
        # (Omitted here for brevity, mas o Perception detecta conflitos contra o histórico).

    def _decision_loop(self):
        while self.running:
            time.sleep(0.05) # Verifica a cada 50ms
            
            with self.buffer_lock:
                if self.proposal_buffer:
                    elapsed_ms = (now_ts() - self.window_start) * 1000
                    if elapsed_ms >= self.WINDOW_DURATION_MS:
                        # Flush Window
                        actions_to_process = list(self.proposal_buffer)
                        self.proposal_buffer.clear()
                        self.window_start = 0.0
                        logger.info(f"Decision Window Expired. Processing batch of {len(actions_to_process)} actions.")
                        
                        # Processa fora do lock para não travar RMR
                        threading.Thread(target=self._process_action_group, args=(actions_to_process,), daemon=True).start()

    def _send_control(self, node_id: str, parameter: str, value: float):
        try:
            # Encodifica APER ASN.1 Nativo
            aper_payload = self.rc_encoder.encode_control_request(node_id, parameter, value)
            
            # Formata para o dispatcher RMR do E2 Term
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
