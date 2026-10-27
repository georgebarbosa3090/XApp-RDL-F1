import time
import threading
import json
import os
import uuid
import math
from typing import Dict, Any, List, Optional, Tuple

try:
    from ricxappframe.xapp_frame import RMRXapp as _RealRMRXapp, Xapp as _RealXapp
    _HAS_RICXAPPFRAME = True
except (ImportError, OSError, Exception):
    _HAS_RICXAPPFRAME = False
    _RealRMRXapp = None
    _RealXapp = None

class MockRMRXapp:
    """Fallback mock para execucao local/testes sem dependencia binaria C/RMR."""
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
    def register(self):
        return True
    def deregister(self):
        return True
    def rmr_send(self, payload, mtype, *args, **kwargs):
        logger.warning(
            "Mock RMR cannot transmit messages; configure a real RMR transport for control dispatch."
        )
        return False
    def rmr_free(self, sbuf):
        pass

Xapp = _RealXapp if _RealXapp is not None else MockRMRXapp
RMRXapp = _RealRMRXapp if _RealRMRXapp is not None else MockRMRXapp

from src.observability.logging import setup_logger, now_ts
from src.observability.health_server import HealthServer, AppState
from src.infrastructure.sdl_repository import SdlRepository
from src.infrastructure.memory_module import MemoryModule
from src.core.perception import Perception
from src.core.reasoning import Reasoning
from src.core.refinement import Refinement
from src.observability.metrics import MetricsServer
from src.e2.kpm_decoder import KpmDecoder
from src.e2.rc_encoder import RCEncoder
from src.e2.rc.mapper import RCMapper
from src.e2.e2ap.subscription import build_ric_subscription_request_payload
from src.e2.e2ap.control import parse_ric_control_ack, parse_ric_control_failure
from src.e2.e2ap.constants import (
    RIC_SUBSCRIPTION_REQ,
    RIC_SUBSCRIPTION_RESP,
    RIC_SUBSCRIPTION_FAILURE,
    RIC_SUBSCRIPTION_DELETE_REQ,
    RIC_SUBSCRIPTION_DELETE_RESP,
    RIC_SUBSCRIPTION_DELETE_FAILURE,
    RIC_CONTROL_REQ,
    RIC_CONTROL_ACK,
    RIC_CONTROL_FAILURE,
    RIC_INDICATION,
    RDL_ACTION_PROPOSAL,
    ID_RIC_CONTROL,
    ID_RIC_SUBSCRIPTION,
    ID_RIC_INDICATION
)
from src.conflict_types import XAppAction, KPMReport, ConflictSeverity, RDLDecision

from src.infrastructure.ran_backend_factory import get_ran_backend_adapter
from src.infrastructure.ric_request_id_allocator import get_ric_request_id_allocator

logger = setup_logger("rdl_xapp")

# Aliases de conveniência
RIC_SUB_REQ = RIC_SUBSCRIPTION_REQ
RIC_SUB_RESP = RIC_SUBSCRIPTION_RESP
RIC_SUB_FAILURE = RIC_SUBSCRIPTION_FAILURE

class RDLxApp:
    def __init__(self):
        self.running = True
        os.environ.setdefault("CONFIG_FILE", "/app/configs/config-file.json")
        
        # Modos de Operação (O_RAN_INTEROP / ORAN-STRICT | SIMULATION / OFFLINE_SIMULATION | STANDALONE)
        raw_mode = os.getenv("RDL_MODE", "OFFLINE_SIMULATION").upper()
        self.mode = "O_RAN_INTEROP" if raw_mode in ("O_RAN_INTEROP", "ORAN-STRICT", "ORAN_STRICT", "STRICT") else raw_mode
        self.oran_strict = (self.mode == "O_RAN_INTEROP")
        
        if self.mode == "O_RAN_INTEROP":
            if not _HAS_RICXAPPFRAME:
                raise RuntimeError(
                    "ImportError: ricxappframe / RMR é obrigatório no modo O_RAN_INTEROP. "
                    "Fallback para MockRMR é estritamente proibido em ambiente O-RAN estrito."
                )
            use_fake_sdl = False
            rmr_wait_for_ready = os.getenv("RMR_WAIT_FOR_READY", "false").lower() in ("true", "1", "yes")
            self.dispatch_raw_aper = True
        else:
            use_fake_sdl = os.getenv("USE_FAKE_SDL", "True").lower() in ("true", "1", "yes")
            rmr_wait_for_ready = os.getenv("RMR_WAIT_FOR_READY", "false" if use_fake_sdl else "true").lower() in ("true", "1", "yes")
            self.dispatch_raw_aper = os.getenv("DISPATCH_RAW_APER_CONTROL", "False").lower() in ("true", "1", "yes")
        
        if use_fake_sdl:
            self.memory = MemoryModule()
        else:
            try:
                self.memory = SdlRepository()
            except Exception as exc:
                if self.oran_strict:
                    raise RuntimeError("SDL/DBaaS obrigatório no modo O_RAN_INTEROP; fallback local proibido.") from exc
                logger.warning("SDL indisponível no ambiente local. Utilizando MemoryModule.")
                self.memory = MemoryModule()
            
        self.perception = Perception()
        self.reasoning = Reasoning(self.memory, config={})
        self.refinement = Refinement(self.memory, strict_capabilities=self.oran_strict)
        self.health = HealthServer(port=8080)
        self.health.set_state(AppState.STARTING)
        self.health.run()
        self.metrics = MetricsServer(port=8081)
        self.metrics.start()
        self.asn1_decoder = KpmDecoder()
        self.rc_encoder = RCEncoder()
        self.rc_mapper = RCMapper(ran_function_id=3)
        self.backend = get_ran_backend_adapter(os.getenv("RAN_BACKEND"))
        self.allocator = get_ric_request_id_allocator()
        
        # Decision Window properties (Feature 1)
        self.proposal_buffer: List[XAppAction] = []
        self.buffer_lock = threading.Lock()
        self.window_start: float = 0.0
        self.WINDOW_DURATION_MS = 200
        self.MAX_PROPOSALS = 4096

        # ACK & Transaction Tracking (suporta UUID string e tuple RICrequestId)
        self.pending_transactions: Dict[Any, float] = {}
        self.active_subscriptions: Dict[str, bool] = {}
        self.decision_loop_started = False
        
        if self.mode == "O_RAN_INTEROP":
            self.xapp = _RealRMRXapp(
                default_handler=self._default_handler,
                rmr_port=4560,
                rmr_wait_for_ready=rmr_wait_for_ready,
                use_fake_sdl=use_fake_sdl,
                post_init=self._entrypoint
            )
        else:
            self.xapp = MockRMRXapp(
                default_handler=self._default_handler,
                rmr_port=4560,
                rmr_wait_for_ready=False,
                use_fake_sdl=use_fake_sdl,
                post_init=self._entrypoint
            )

        if isinstance(self.memory, SdlRepository):
            try:
                self.memory.bind_xapp(self.xapp, required=self.oran_strict)
            except RuntimeError as exc:
                if self.oran_strict:
                    raise RuntimeError("SDL obrigatório indisponível no modo O_RAN_INTEROP.") from exc
                logger.warning("SDL indisponível; utilizando armazenamento local não persistente.", error=str(exc))
                self.memory = MemoryModule()
                self.reasoning.memory = self.memory
        
        from src.e2.control_dispatcher import ControlDispatcher
        self.dispatcher = ControlDispatcher(
            rmr_client=self.xapp,
            sdl_repo=self.memory,
            backend=self.backend,
            default_timeout_s=5.0
        )
        
        self.xapp.register_callback(self._kpm_indication_handler, RIC_INDICATION)
        self.xapp.register_callback(self._action_proposal_handler, RDL_ACTION_PROPOSAL)
        self.xapp.register_callback(self._control_ack_handler, RIC_CONTROL_ACK)
        self.xapp.register_callback(self._control_failure_handler, RIC_CONTROL_FAILURE)
        self.xapp.register_callback(self._subscription_response_handler, RIC_SUB_RESP)
        self.xapp.register_callback(self._subscription_failure_handler, RIC_SUB_FAILURE)

    def _safe_rmr_free(self, xapp_instance: Any, sbuf: Any):
        """Libera buffer RMR com segurança, ignorando objetos mock ou inválidos."""
        if not xapp_instance or not sbuf:
            return
        if hasattr(sbuf, "__class__") and sbuf.__class__.__name__ == "MockSbuf":
            return
        try:
            if hasattr(xapp_instance, "rmr_free"):
                xapp_instance.rmr_free(sbuf)
        except Exception:
            pass

    def start(self):
        logger.info(f"Iniciando xApp RDL (H-RDL Fase 1 | Modo: {self.mode})")
        self.health.run()
        self.metrics.start()
        self.running = True
        self.xapp.run()

    def stop(self):
        self.running = False
        self.health.set_state(AppState.STOPPED)
        self.xapp.stop()
        
    def _default_handler(self, xapp_instance, summary, sbuf):
        logger.debug("Mensagem RMR nao mapeada recebida", mtype=summary.get("mtype"))
        self._safe_rmr_free(xapp_instance, sbuf)

    def _entrypoint(self, xapp_instance):
        logger.info(f"xApp Framework Ready (Modo {self.mode} | Backend {self.backend.metadata.backend_id})")
        if isinstance(self.memory, SdlRepository):
            try:
                self.memory.bind_xapp(xapp_instance, required=self.oran_strict)
            except RuntimeError as exc:
                if not self.oran_strict:
                    logger.warning("SDL indisponível; xApp permanece em armazenamento local.", error=str(exc))
                    self.memory = MemoryModule()
                    self.reasoning.memory = self.memory
                else:
                    self.health.set_state(AppState.ERROR)
                    logger.error("SDL obrigatório indisponível; xApp mantida fora de READY.", error=str(exc))
                    return

        if self.oran_strict or self.mode == "O_RAN_INTEROP":
            logger.info(
                "Modo O_RAN_INTEROP: capacidades devem estar previamente carregadas pela integração "
                "de descoberta E2; este runtime não consome RAN Function Definition."
            )
        else:
            # Registra capacidades estaticas pre-configuradas em modo DEV/UNIT/OFFLINE
            self.backend.register_static_profile_capabilities("gnb_01")
        # Inicia subscricao E2SM-KPM com o tempo de reporte padrao do backend
        kpm_period = self.backend.metadata.default_kpm_period_ms
        from src.e2.rc.capability_registry import rc_capability_registry
        try:
            kpm_fn_id = rc_capability_registry.get_kpm_function_id("gnb_01")
            if self.oran_strict:
                rc_capability_registry.get_rc_function_id("gnb_01")
            subscribed = self.send_subscription_request(node_id="gnb_01", ran_function_id=kpm_fn_id, report_period_ms=kpm_period, xapp_instance=xapp_instance)
            if not subscribed:
                self.health.set_state(AppState.DEGRADED)
                logger.warning("Subscrição KPM não foi aceita pelo transporte; xApp mantida em DEGRADED.")
            else:
                self.health.set_state(AppState.SUBSCRIBING)
        except Exception as e:
            if self.oran_strict:
                self.health.set_state(AppState.ERROR)
                logger.error(
                    "Modo O_RAN_INTEROP bloqueado: descoberta E2 não forneceu KPM Function ID "
                    "e/ou RC Function ID ao runtime; não será usado ID estático nem retry success-shaped.",
                    error=str(e),
                )
            else:
                subscribed = self.send_subscription_request(node_id="gnb_01", ran_function_id=2, report_period_ms=kpm_period, xapp_instance=xapp_instance)
                if subscribed:
                    self.health.set_state(AppState.SUBSCRIBING)
                else:
                    self.health.set_state(AppState.DEGRADED)


    def send_subscription_request(self, node_id: str = "gnb_01", ran_function_id: Optional[int] = None, report_period_ms: int = 200, xapp_instance: Any = None) -> bool:
        """
        Emite requisicao de subscricao E2 (RIC_SUB_REQ) com payloads APER normativos.
        """
        try:
            from src.e2.rc.capability_registry import rc_capability_registry
            resolved_fn_id = ran_function_id if ran_function_id is not None else rc_capability_registry.get_kpm_function_id(node_id)
            sub_req_payload = build_ric_subscription_request_payload(
                target_node=node_id,
                ran_function_id=resolved_fn_id,
                report_period_ms=report_period_ms
            )
            payload_bytes = json.dumps(sub_req_payload).encode('utf-8')
            target_xapp = xapp_instance or getattr(self, "xapp", None)
            if target_xapp:
                success = target_xapp.rmr_send(payload=payload_bytes, mtype=RIC_SUB_REQ)
            else:
                success = False
            if success:
                logger.info("RIC_SUB_REQ emitido com sucesso para Subscription Manager", target_node=node_id, period_ms=report_period_ms)
                self.active_subscriptions[node_id] = True
            else:
                logger.warning("Falha ao enviar RIC_SUB_REQ via RMR")
            return bool(success)
        except Exception as e:
            logger.error(f"Erro ao construir e emitir RIC_SUB_REQ: {e}")
            return False

    def _subscription_response_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        """Trata resposta de subscricao E2 (RIC_SUB_RESP) emitida pelo SubMgr."""
        logger.info("RIC_SUB_RESP recebido com sucesso", summary=summary)
        if not any(self.active_subscriptions.values()):
            logger.warning("RIC_SUB_RESP recebido sem subscrição local pendente; readiness não alterada.")
            self._safe_rmr_free(xapp_instance, sbuf)
            return
        self.health.set_state(AppState.READY)
        if not self.decision_loop_started:
            self.decision_loop_started = True
            threading.Thread(target=self._decision_loop, daemon=True).start()
        self._safe_rmr_free(xapp_instance, sbuf)

    def _subscription_failure_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        logger.error("RIC_SUBSCRIPTION_FAILURE recebido; xApp não está pronta", summary=summary)
        self.active_subscriptions.clear()
        self.health.set_state(AppState.DEGRADED)
        self._safe_rmr_free(xapp_instance, sbuf)

    def _kpm_indication_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        self.metrics.record_kpm()
        payload = summary.get("payload")
        if payload:
            reports_data = self.backend.decode_kpm(payload)
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
        self._safe_rmr_free(xapp_instance, sbuf)

    def _action_proposal_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        """Recebe acoes propostas por outras xApps via RMR e enfileira na janela temporal."""
        payload = summary.get("payload")
        if payload:
            try:
                if not isinstance(payload, bytes) or len(payload) > 65536:
                    raise ValueError("Proposal payload must be bytes with at most 65536 bytes")
                data = json.loads(payload.decode("utf-8"), parse_constant=self._reject_json_constant)
                if not isinstance(data, dict):
                    raise ValueError("Proposal must be a JSON object")
                xapp_id = data.get("xapp_id")
                node_id = data.get("node_id")
                parameter = data.get("parameter")
                value = data.get("value")
                priority = data.get("priority", 50)
                if not isinstance(xapp_id, str) or not xapp_id.strip() or len(xapp_id) > 128:
                    raise ValueError("xapp_id must be a non-empty string of at most 128 characters")
                if not isinstance(node_id, str) or not node_id.strip() or len(node_id) > 128:
                    raise ValueError("node_id must be a non-empty string of at most 128 characters")
                if not isinstance(parameter, str) or not parameter.strip():
                    raise ValueError("parameter must be a non-empty string")
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ValueError("value must be a finite number")
                if isinstance(priority, bool) or not isinstance(priority, int) or not 0 <= priority <= 100:
                    raise ValueError("priority must be an integer in [0, 100]")
                action = XAppAction(
                    xapp_id=xapp_id,
                    node_id=node_id,
                    parameter=parameter,
                    value=float(value),
                    priority=priority
                )
                with self.buffer_lock:
                    if len(self.proposal_buffer) >= self.MAX_PROPOSALS:
                        logger.error("Proposal buffer limit reached; incoming action rejected.")
                    else:
                        if not self.proposal_buffer:
                            self.window_start = now_ts()
                        self.proposal_buffer.append(action)
                        logger.debug(f"Action buffered. Queue size: {len(self.proposal_buffer)}")
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as e:
                logger.error("Erro ao processar RDL_ACTION_PROPOSAL", error=str(e))
        self._safe_rmr_free(xapp_instance, sbuf)

    @staticmethod
    def _reject_json_constant(value: str):
        raise ValueError(f"Invalid JSON numeric constant: {value}")

    def _control_ack_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        """Trata confirmacoes de execucao de controle emitidas pelo E2 Node / E2Term."""
        payload = summary.get("payload")
        if payload:
            try:
                # 1) Dispatcher trata APER e aciona causal_tracker
                self.dispatcher.handle_ack(payload, node_id=summary.get("meid"))

                # 2) Correlaciona via backend e limpa pending_transactions locais
                ack_info = self.backend.correlate_ack(payload, allow_test_fallback=not self.oran_strict)
                req_id = ack_info.get("requestor_id")
                inst_id = ack_info.get("instance_id")
                node_id = ack_info.get("node_id", "gnb_01")
                from src.e2.rc.capability_registry import rc_capability_registry
                ran_fn_id = ack_info.get("ran_function_id") or rc_capability_registry.get_rc_function_id(node_id)
                
                tx_key = (node_id, ran_fn_id, req_id, inst_id) if req_id is not None else None
                if not tx_key or tx_key not in self.pending_transactions:
                    data = json.loads(payload.decode('utf-8')) if isinstance(payload, bytes) and payload.startswith(b'{') else {}
                    tx_key = data.get("transaction_id")
                
                if tx_key and tx_key in self.pending_transactions:
                    rtt_ms = (now_ts() - self.pending_transactions.pop(tx_key)) * 1000.0
                    if req_id is not None and ran_fn_id is not None:
                        self.allocator.pop_correlation(node_id, ran_fn_id, req_id, inst_id)
                    from src.observability.causal_tracker import causal_tracker
                    if req_id is not None and ran_fn_id is not None:
                        correlation_id = causal_tracker.correlation_id(
                            node_id, ran_fn_id, req_id, inst_id
                        )
                        causal_tracker.record_ack(correlation_id, rtt_ms=rtt_ms)
                    logger.info("RIC_CONTROL_ACK recebido e confirmado", key=str(tx_key), rtt_ms=f"{rtt_ms:.2f}ms", status=ack_info.get("status"))
                else:
                    logger.info("RIC_CONTROL_ACK recebido sem transacao pendente", status=ack_info.get("status"))
            except Exception as err:
                logger.warning("Falha ao processar RIC_CONTROL_ACK", error=str(err))
        logger.info("Recebido RIC_CONTROL_ACK", summary=summary)
        self._safe_rmr_free(xapp_instance, sbuf)

    def _control_failure_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        logger.warning("Recebido RIC_CONTROL_FAILURE", summary=summary)
        payload = summary.get("payload")
        if payload:
            try:
                # 1) Dispatcher trata APER e aciona rollback
                self.dispatcher.handle_failure(payload, node_id=summary.get("meid"))

                # 2) Correlaciona via backend e limpa pending_transactions locais
                fail_info = self.backend.correlate_ack(payload, allow_test_fallback=not self.oran_strict)
                req_id = fail_info.get("requestor_id")
                inst_id = fail_info.get("instance_id")
                node_id = fail_info.get("node_id", "gnb_01")
                cause = fail_info.get("cause", 1)
                from src.e2.rc.capability_registry import rc_capability_registry
                ran_fn_id = fail_info.get("ran_function_id") or rc_capability_registry.get_rc_function_id(node_id)
                
                tx_key = (node_id, ran_fn_id, req_id, inst_id) if req_id is not None else None
                if not tx_key or tx_key not in self.pending_transactions:
                    data = json.loads(payload.decode('utf-8')) if isinstance(payload, bytes) and payload.startswith(b'{') else {}
                    tx_key = data.get("transaction_id")
                    
                if tx_key and tx_key in self.pending_transactions:
                    del self.pending_transactions[tx_key]
                    if req_id is not None:
                        self.allocator.pop_correlation(node_id, ran_fn_id, req_id, inst_id)
                    from src.observability.causal_tracker import causal_tracker
                    if req_id is not None and ran_fn_id is not None:
                        correlation_id = causal_tracker.correlation_id(
                            node_id, ran_fn_id, req_id, inst_id
                        )
                        causal_tracker.record_failure(correlation_id, cause_code=cause)
            except Exception as e:
                logger.debug(f"Falha ao correlacionar failure payload: {e}")
        self._safe_rmr_free(xapp_instance, sbuf)

    def inject_xapp_action(self, action: XAppAction):
        """API publica para injecao de acoes simuladas (usada em testes)"""
        with self.buffer_lock:
            if len(self.proposal_buffer) >= self.MAX_PROPOSALS:
                raise OverflowError("Proposal buffer limit reached")
            if not self.proposal_buffer:
                self.window_start = now_ts()
            self.proposal_buffer.append(action)

    def _process_action_group(self, actions: List[XAppAction]):
        """
        Processa todas as acoes acumuladas na Decision Window (Feature 2):
        1. Identifica conflitos diretos e indiretos;
        2. Arbitra conflitos via ReasoningAgent e valida via RefinementAgent;
        3. Formaliza a RDLDecision ANTES do despacho;
        4. Executa o despacho das ações selecionadas via ControlDispatcher.
        """
        t0 = now_ts()
        for act in actions:
            self.memory.add_action(act)
            
        conflicts = self.perception.detect_action_group(actions)
        self.metrics.update_active_xapps(len(self.perception.get_active_xapps()))
        
        # Mapeia acoes em conflito para isolar as acoes limpas
        conflicting_action_keys = set()
        for conflict in conflicts:
            for act in conflict.involved_xapps:
                conflicting_action_keys.add((act.node_id, act.parameter, act.xapp_id))

        # 1. Resolver conflitos do grupo
        selected_winning_actions = []
        strategy_names = []
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
                    selected_winning_actions.append(act)
                strategy_names.append(resolution.strategy_used.name)
            else:
                logger.warning("Resolucao Rejeitada ou Lote Vazio", reason=reason)

        # 2. Seleção de Ações Limpas (Conflict-Free Pass-Through Pipeline)
        clean_actions = [
            act for act in actions 
            if (act.node_id, act.parameter, act.xapp_id) not in conflicting_action_keys
        ]
        
        selected_clean_actions = []
        for clean_act in clean_actions:
            is_safe, level, reason = self.refinement.validate_single_action(clean_act)
            if is_safe:
                logger.info("Acao Limpa Admitida (Pass-Through)", xapp=clean_act.xapp_id, param=clean_act.parameter, val=clean_act.value)
                selected_clean_actions.append(clean_act)
            else:
                logger.warning("Acao Limpa Bloqueada pelo Safety Guard", reason=reason, param=clean_act.parameter)

        # 3. Formalização da RDLDecision ANTES do Despacho (Garantia de Rastreabilidade)
        all_selected = selected_winning_actions + selected_clean_actions
        decision = RDLDecision(
            state={"active_xapps": len(self.perception.get_active_xapps())},
            proposals=actions,
            conflicts=conflicts,
            safety_result={"admitted_count": len(all_selected), "rejected_count": len(actions) - len(all_selected)},
            selected_actions=all_selected,
            reason="RESOLVED_AND_PASSTHROUGH",
            strategy_used=",".join(strategy_names) if strategy_names else "PASS_THROUGH",
            affected_node=all_selected[0].node_id if all_selected else "gnb_01",
            affected_cell=getattr(all_selected[0], "cell_id", "cell_01") if all_selected else "cell_01",
            previous_safe_value=None,
        )
        logger.info("RDLDecision Formalizada", decision_id=decision.decision_id, strategy=decision.strategy_used, selected_count=len(all_selected))

        # 4. Despacho de Controle para Ações Admitidas via ControlDispatcher
        dispatched_actions = []
        from src.observability.causal_tracker import causal_tracker
        for act in all_selected:
            per_action_decision = RDLDecision(
                decision_id=f"{decision.decision_id}-{act.action_id[:6]}",
                selected_actions=[act],
                safety_result={"is_safe": True},
                affected_node=act.node_id,
                affected_cell=getattr(act, "cell_id", "cell_01"),
                previous_safe_value=None,
                strategy_used=decision.strategy_used,
            )
            control_request_id = self.dispatcher.dispatch_control(per_action_decision)
            if control_request_id is None:
                continue
            dispatched_actions.append(act)
            request_info = self.dispatcher.pending_requests.get(control_request_id, {})
            causal_tracker.record_decision(
                action_id=act.action_id,
                decision_id=per_action_decision.decision_id,
                ric_request_id=causal_tracker.correlation_id(
                    request_info.get("meid", act.node_id),
                    request_info.get("ran_function_id", 0),
                    request_info.get("requestor_id", 0),
                    request_info.get("instance_id", 0),
                ),
                node_id=act.node_id,
                parameter=act.parameter,
                old_val=None,
                new_val=act.value,
                kpm_before=(
                    self.perception.latest_kpm.__dict__
                    if self.perception.latest_kpm is not None
                    else {}
                ),
                strategy=decision.strategy_used,
            )
        self.perception.commit_actions(dispatched_actions)

    def cleanup_expired_transactions(self, timeout_s: float = 5.0) -> int:
        """Limpa transações pendentes expiradas para evitar vazamento de memória (Anti-Leak)."""
        now = now_ts()
        expired_keys = [k for k, ts in list(self.pending_transactions.items()) if (now - ts) > timeout_s]
        for k in expired_keys:
            self.pending_transactions.pop(k, None)
        self.allocator.cleanup_expired(timeout_s)
        return len(expired_keys)

    def _decision_loop(self):
        last_cleanup = now_ts()
        while self.running:
            time.sleep(0.05) # Verifica a cada 50ms
            
            # Anti-leak cleanup e timeout de controle a cada 1 segundo
            now = now_ts()
            if (now - last_cleanup) >= 1.0:
                self.cleanup_expired_transactions()
                self.dispatcher.check_timeouts(now)
                last_cleanup = now

            actions_to_process = []
            with self.buffer_lock:
                if self.proposal_buffer:
                    elapsed_ms = (now_ts() - self.window_start) * 1000
                    if elapsed_ms >= self.WINDOW_DURATION_MS:
                        # Flush Window
                        actions_to_process = list(self.proposal_buffer)
                        self.proposal_buffer.clear()
                        self.window_start = 0.0
                        logger.info(f"Decision Window Expired. Processing batch of {len(actions_to_process)} actions.")
            if actions_to_process:
                self._process_action_group(actions_to_process)

    def _send_control(self, node_id: str, parameter: str, value: float, action: Optional[XAppAction] = None, decision_id: Optional[str] = None):
        correlation_key = None
        ric_req_key = None
        tx_id = None
        try:
            target_action = action or XAppAction(xapp_id="hrdl_core", node_id=node_id, parameter=parameter, value=value, priority=100)
            from src.e2.rc.capability_registry import rc_capability_registry
            ran_fn_id = rc_capability_registry.get_rc_function_id(node_id)
            req_id_obj = self.allocator.allocate(
                node_id=node_id,
                ran_function_id=ran_fn_id,
                decision_id=decision_id,
                action_id=getattr(target_action, "action_id", None)
            )
            requestor_id = req_id_obj.requestor_id
            instance_id = req_id_obj.instance_id
            correlation_key = (node_id, ran_fn_id, requestor_id, instance_id)
            aper_payload = self.backend.map_action_to_control_pdu(target_action, requestor_id=requestor_id, instance_id=instance_id)
            
            tx_id = str(uuid.uuid4())[:8]
            ric_req_key = (node_id, ran_fn_id, requestor_id, instance_id)
            self.pending_transactions[ric_req_key] = now_ts()
            self.pending_transactions[tx_id] = now_ts()
            
            if self.dispatch_raw_aper:
                # Envio direto do buffer binario APER para o E2Term / NORI
                success = self.xapp.rmr_send(payload=aper_payload, mtype=RIC_CONTROL_REQ)
            else:
                # Formata para o dispatcher RMR com envelope estruturado e hex APER
                payload_dict = {
                    "transaction_id": tx_id,
                    "decision_id": decision_id,
                    "action_id": getattr(target_action, "action_id", ""),
                    "node_id": node_id,
                    "parameter": parameter,
                    "value": value,
                    "requestor_id": requestor_id,
                    "instance_id": instance_id,
                    "ran_function_id": ran_fn_id,
                    "aper_bytes": aper_payload.hex() if isinstance(aper_payload, bytes) else str(aper_payload)
                }
                payload_bytes = json.dumps(payload_dict).encode('utf-8')
                success = self.xapp.rmr_send(payload=payload_bytes, mtype=RIC_CONTROL_REQ)
        except Exception as e:
            logger.error(f"Falha ao gerar APER Control via backend {self.backend.metadata.backend_id}: {e}")
            success = False
        if success:
            logger.info("RIC_CONTROL_REQUEST enviado com sucesso", node_id=node_id, param=parameter, val=value, backend=self.backend.metadata.backend_id, raw_aper=self.dispatch_raw_aper, decision_id=decision_id, action_id=getattr(action, "action_id", None))
        else:
            logger.error("Falha ao enviar RIC_CONTROL_REQUEST")
            if correlation_key is not None:
                self.allocator.pop_correlation(*correlation_key)
            if ric_req_key is not None:
                self.pending_transactions.pop(ric_req_key, None)
            if tx_id is not None:
                self.pending_transactions.pop(tx_id, None)



if __name__ == "__main__":
    app = RDLxApp()
    try:
        app.start()
    except KeyboardInterrupt:
        app.stop()
