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
    def rmr_send(self, payload, mtype, retries=100):
        logger.warning(
            "Mock RMR cannot transmit messages; configure a real RMR transport for control dispatch."
        )
        return False
    def rmr_send_with_meid(self, payload, mtype, meid):
        return self.rmr_send(payload, mtype)
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
from src.core.inter_cell import InterCellRules, load_inter_cell_config
from src.core.knowledge_graph import KnowledgeGraph
from src.core.decision_window import AdaptiveDecisionWindow, Urgency, WindowConfig, parse_critical_targets
from src.core import proposal_registry as preg
from src.core.proposal_registry import ProposalRegistry
from src.interfaces.a1_policy_receiver import A1PolicyHttpHandler, A1PolicyManager, A1PolicyReceiverServer
from src.interfaces.a1_rmr import A1_POLICY_QUERY, A1_POLICY_REQUEST, A1_POLICY_RESPONSE, handle_policy_request, query_messages
from src.observability.metrics import MetricsServer
from src.e2.kpm_decoder import KpmDecoder
from src.e2.rc_encoder import RCEncoder
from src.e2.rc.mapper import RCMapper
from src.infrastructure.subscription_manager import SubscriptionManager
from src.e2.e2ap.control import parse_ric_control_ack, parse_ric_control_failure
from src.e2.e2ap.constants import (
    RIC_SUBSCRIPTION_REQ,
    RIC_SUBSCRIPTION_RESP,
    RIC_SUBSCRIPTION_FAILURE,
    RIC_SUBSCRIPTION_DELETE_REQ,
    RIC_SUBSCRIPTION_DELETE_RESP,
    RIC_SUBSCRIPTION_DELETE_FAILURE,
    RIC_CONTROL_ACK,
    RIC_CONTROL_FAILURE,
    RIC_INDICATION,
    RDL_ACTION_PROPOSAL,
    RDL_ACTION_RESULT,
    ID_RIC_CONTROL,
    ID_RIC_SUBSCRIPTION,
    ID_RIC_INDICATION,
)
from src.conflict_types import (
    XAppAction,
    KPMReport,
    ConflictEvent,
    ConflictSeverity,
    ConflictType,
    RDLDecision,
    ResolutionAction,
)

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
        else:
            use_fake_sdl = os.getenv("USE_FAKE_SDL", "True").lower() in ("true", "1", "yes")
            rmr_wait_for_ready = os.getenv("RMR_WAIT_FOR_READY", "false" if use_fake_sdl else "true").lower() in ("true", "1", "yes")

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

        # Regras entre células compartilhadas pela percepção (detecção) e pelo raciocínio (EEVS)
        self.inter_cell_rules = InterCellRules.from_config(load_inter_cell_config())
        self.knowledge_graph = KnowledgeGraph(max_events=int(os.getenv("RDL_KG_MAX_EVENTS", "5000")))
        self.perception = Perception(inter_cell_rules=self.inter_cell_rules, knowledge_graph=self.knowledge_graph)
        self.reasoning = Reasoning(self.memory, config={}, inter_cell_rules=self.inter_cell_rules)
        self.refinement = Refinement(
            self.memory,
            strict_capabilities=self.oran_strict,
            committed_action_lookup=self.perception.get_committed_action,
        )
        self.refinement.handover_target_check = self._handover_target_known

        # Políticas A1 (Non-RT RIC / rApp): ajustam pesos, limites e regras entre células.
        # Sem política ativa, vale a configuração de base; remover a política a restaura.
        self._a1_baseline = {
            "weights": {name: getattr(self.reasoning, name) for name in Reasoning._A1_WEIGHTS},
            "minimum_control_interval_ms": self.refinement.config["minimum_control_interval_ms"],
            "critical_control_interval_ms": self.refinement.config["critical_control_interval_ms"],
            "allow_neighbor_sleep": self.inter_cell_rules.allow_neighbor_sleep,
            "low_power_threshold_dbm": self.inter_cell_rules.low_power_threshold_dbm,
        }
        self.a1_policies = A1PolicyManager()
        self.a1_policies.add_listener(self._apply_a1_policy)
        A1PolicyHttpHandler.policy_manager = self.a1_policies
        self.a1_server: Optional[A1PolicyReceiverServer] = None
        a1_port = os.getenv("A1_RECEIVER_PORT")
        if a1_port:
            self.a1_server = A1PolicyReceiverServer(host="127.0.0.1", port=int(a1_port))
            self.a1_server.start()
        self.health = HealthServer(port=8080)
        self.health.knowledge_graph_provider = (
            lambda full=False: self.knowledge_graph.to_dict() if full else self.knowledge_graph.stats()
        )
        self.health.set_state(AppState.STARTING)
        self.health.run()
        self.metrics = MetricsServer(port=8081)
        self.metrics.start()
        self.asn1_decoder = KpmDecoder()
        self.rc_encoder = RCEncoder()
        self.rc_mapper = RCMapper(ran_function_id=3)
        self.backend = get_ran_backend_adapter(os.getenv("RAN_BACKEND"))
        self.allocator = get_ric_request_id_allocator()

        # Subscrição E2 via API REST do SubMgr (O-RAN SC). Em modo estrito usa o endereço
        # padrão da plataforma; fora dele, só quando SUBMGR_URL é configurado.
        submgr_url = os.getenv("SUBMGR_URL") or (
            "http://service-ricplt-submgr-http.ricplt:8088" if self.oran_strict else None
        )
        self.subscription_manager: Optional[SubscriptionManager] = (
            SubscriptionManager(submgr_url=submgr_url) if submgr_url else None
        )
        self.health.subscription_callback = self._subscription_notification_handler

        # Decision Window properties (Feature 1 + Fast-Flush URLLC)
        self.proposal_buffer: List[XAppAction] = []
        self.buffer_lock = threading.Lock()
        self.urgent_event = threading.Event()
        self.window_start: float = 0.0
        self.WINDOW_DURATION_MS = 200
        self.MAX_PROPOSALS = 4096
        # Classes de urgência e janela adaptativa (doc 09 §2.2). Sem RDL_ADAPTIVE_WINDOW=true a janela
        # fica fixa em 200 ms e propostas com prioridade >= 80 antecipam o fechamento, como antes.
        self.decision_window = AdaptiveDecisionWindow(WindowConfig(
            base_window_ms=float(self.WINDOW_DURATION_MS),
            adaptive=os.getenv("RDL_ADAPTIVE_WINDOW", "false").lower() in ("true", "1", "yes"),
            critical_priority=int(os.getenv("RDL_CRITICAL_PRIORITY", "95")),
        ))
        window_cfg = self.decision_window.config
        window_cfg.critical_targets = parse_critical_targets(os.getenv("RDL_CRITICAL_TARGETS", "").split(","))
        window_cfg.critical_max_per_s = float(os.getenv("RDL_CRITICAL_MAX_PER_S", "5"))
        window_cfg.proposal_max_age_ms = float(os.getenv("RDL_PROPOSAL_MAX_AGE_MS", "1000"))
        window_cfg.defer_max_ttl_ms = float(os.getenv("RDL_DEFER_MAX_TTL_MS", "3000"))
        self._critical_targets_baseline = set(window_cfg.critical_targets)
        self._apply_a1_policy(self.a1_policies.effective_policy())
        self.critical_queue: List[XAppAction] = []
        self.buffer_deadline_ms: float = float(self.WINDOW_DURATION_MS)
        # Propostas recusadas pela histerese que pediram adiamento: (pronta em, perf_counter), proposta
        self.deferred: List[Tuple[float, XAppAction]] = []
        self.notify_xapps = os.getenv("RDL_NOTIFY_XAPPS", "true").lower() in ("true", "1", "yes")

        # ACK & Transaction Tracking (suporta UUID string e tuple RICrequestId)
        self.pending_actions_by_id: Dict[str, XAppAction] = {}
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
                self.refinement.memory = self.memory

        # Registro de propostas não atendidas (doc 09 §2.4): consulta em GET /rejections
        self.proposals = ProposalRegistry(max_entries=int(os.getenv("RDL_REJECTION_LOG_SIZE", "5000")),
                                          store=self.memory)
        self.health.rejections_provider = self._rejections_view

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
        self.xapp.register_callback(self._a1_policy_request_handler, A1_POLICY_REQUEST)

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
        self.urgent_event.set()
        self.health.set_state(AppState.STOPPED)
        if getattr(self, "a1_server", None) is not None:
            self.a1_server.stop()
        self.xapp.stop()

    def _apply_a1_policy(self, policy: Dict[str, Any]) -> None:
        """Aplica a política A1 efetiva (tipos 20000 e 20001) sobre a configuração de base."""
        base = self._a1_baseline
        weights = dict(base["weights"])
        if "energy_weight" in policy:
            weights["w_energy"] = weights["w_energy_ind"] = float(policy["energy_weight"])
        if "sla_weight" in policy:
            weights["w_sla"] = weights["w_qos_ind"] = float(policy["sla_weight"])
        self.reasoning.apply_policy(weights, urllc_priority_boost=float(policy.get("urllc_priority_boost", 0.0)))
        self.refinement.apply_policy(
            max_prb_quota=policy.get("max_cell_prb_limit"),
            allow_cell_sleep=bool(policy.get("energy_saving_allowed", True)),
            minimum_control_interval_ms=policy.get("cooling_lockout_ms", base["minimum_control_interval_ms"]),
            critical_control_interval_ms=policy.get("critical_control_interval_ms",
                                                    base["critical_control_interval_ms"]),
        )
        window = getattr(self, "decision_window", None)
        if window is not None:  # o primeiro aviso do A1PolicyManager chega antes da janela existir
            window.config.critical_targets = (
                parse_critical_targets(policy["critical_targets"]) if "critical_targets" in policy
                else set(getattr(self, "_critical_targets_baseline", set()))
            )
        self.inter_cell_rules.allow_neighbor_sleep = bool(policy.get("allow_neighbor_sleep", base["allow_neighbor_sleep"]))
        self.inter_cell_rules.low_power_threshold_dbm = float(
            policy.get("low_power_threshold_dbm", base["low_power_threshold_dbm"])
        )
        logger.info("Política A1 efetiva aplicada", policy=policy)

    def _handover_target_known(self, action: XAppAction) -> bool:
        """Com topologia configurada, o destino do HANDOVER precisa ser uma célula conhecida."""
        known = set(self.inter_cell_rules.neighbors)
        if not known:
            return True
        return self.inter_cell_rules.handover_target(action) in known

    def _a1_policy_request_handler(self, xapp_instance, summary: Dict[str, Any], sbuf: Any):
        """A1 Mediator -> xApp (RMR 20010): aplica a instância e responde 20011."""
        response, ok = handle_policy_request(self.a1_policies, summary.get("payload") or b"", handler_id="iqos-xapp-rdl")
        try:
            self.xapp.rmr_send(json.dumps(response).encode("utf-8"), A1_POLICY_RESPONSE)
        except Exception as exc:
            logger.error("Falha ao responder A1_POLICY_RESPONSE", error=str(exc))
        logger.info("Política A1 recebida pelo A1 Mediator", status=response.get("status"),
                    policy_type_id=response.get("policy_type_id"), policy_instance_id=response.get("policy_instance_id"))
        self._safe_rmr_free(xapp_instance, sbuf)

    def _query_a1_policies(self) -> None:
        """Na partida, pede ao A1 Mediator as instâncias existentes (RMR 20012)."""
        for body in query_messages(list(self.a1_policies.policy_types)):
            try:
                self.xapp.rmr_send(body, A1_POLICY_QUERY)
            except Exception as exc:
                logger.warning("Falha ao consultar políticas A1", error=str(exc))

    def _default_handler(self, xapp_instance, summary, sbuf):
        logger.debug("Mensagem RMR nao mapeada recebida", mtype=summary.get("mtype"))
        self._safe_rmr_free(xapp_instance, sbuf)

    def _entrypoint(self, xapp_instance):
        logger.info(f"xApp Framework Ready (Modo {self.mode} | Backend {self.backend.metadata.backend_id})")
        self._query_a1_policies()
        if self.oran_strict and not self.backend.metadata.protocol_interoperability_verified:
            self.health.set_state(AppState.ERROR)
            self.metrics.ready_state.set(0)
            logger.error(
                "Modo O_RAN_INTEROP bloqueado: codecs APER e descoberta E2 não foram "
                "validados contra schemas e implementação NORI/RIC independentes."
            )
            return
        if isinstance(self.memory, SdlRepository):
            try:
                self.memory.bind_xapp(xapp_instance, required=self.oran_strict)
            except RuntimeError as exc:
                if not self.oran_strict:
                    logger.warning("SDL indisponível; xApp permanece em armazenamento local.", error=str(exc))
                    self.memory = MemoryModule()
                    self.reasoning.memory = self.memory
                    self.refinement.memory = self.memory
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
                if self.oran_strict:
                    self.health.set_state(AppState.DEGRADED)
                    self.metrics.ready_state.set(0)
                    logger.warning("Subscrição KPM não foi aceita pelo SubMgr; xApp mantida em DEGRADED.")
                else:
                    self.health.set_state(AppState.READY)
                    self.metrics.ready_state.set(1)
                    logger.info("Modo governança local: xApp RDL pronta para mediação de conflitos.")
            else:
                # READY somente após a notificação de sucesso do SubMgr.
                self.health.set_state(AppState.SUBSCRIBING)
                self.metrics.ready_state.set(0)
        except Exception as e:
            if self.oran_strict:
                self.health.set_state(AppState.ERROR)
                logger.error(
                    "Modo O_RAN_INTEROP bloqueado: descoberta E2 não forneceu KPM Function ID "
                    "e/ou RC Function ID ao runtime; não será usado ID estático nem retry success-shaped.",
                    error=str(e),
                )
            else:
                self.send_subscription_request(node_id="gnb_01", ran_function_id=2, report_period_ms=kpm_period, xapp_instance=xapp_instance)
                self.health.set_state(AppState.READY)
                self.metrics.ready_state.set(1)

        if not self.decision_loop_started:
            self.decision_loop_started = True
            threading.Thread(target=self._decision_loop, daemon=True).start()

    def send_subscription_request(self, node_id: str = "gnb_01", ran_function_id: Optional[int] = None, report_period_ms: int = 200, xapp_instance: Any = None) -> bool:
        """
        Solicita subscrição E2SM-KPM ao SubMgr pela API REST (``POST /ric/v1/subscriptions``).

        Retorna True quando o SubMgr aceitou o pedido; a subscrição fica pendente
        (``active_subscriptions[node_id] is False``) até a notificação assíncrona.
        Sem SubMgr configurado, retorna False (modo de governança local).
        """
        if self.subscription_manager is None:
            logger.info("SubMgr não configurado (SUBMGR_URL); subscrição E2 não solicitada.", target_node=node_id)
            return False
        try:
            from src.e2.rc.capability_registry import rc_capability_registry
            resolved_fn_id = ran_function_id if ran_function_id is not None else rc_capability_registry.get_kpm_function_id(node_id)
            ctx = self.subscription_manager.request_kpm_subscription(
                meid=node_id, ran_function_id=resolved_fn_id, period_ms=report_period_ms
            )
        except Exception as e:
            logger.error(f"Erro ao solicitar subscrição E2: {e}")
            ctx = None
        if ctx is None:
            logger.warning("SubMgr não aceitou a subscrição KPM", target_node=node_id)
            self.metrics.subs_failures.inc()
            return False
        logger.info(
            "Subscrição KPM aceita pelo SubMgr; aguardando notificação",
            target_node=node_id,
            subscription_id=ctx.subscription_id,
            period_ms=report_period_ms,
        )
        self.active_subscriptions[node_id] = False
        self.metrics.subs_total.inc()
        return True

    def _subscription_notification_handler(self, body: Any) -> Optional[bool]:
        """Trata o resultado assíncrono da subscrição entregue pelo SubMgr via HTTP."""
        if self.subscription_manager is None:
            return None
        result = self.subscription_manager.handle_notification(body)
        if result is None:
            return None
        ctx, success = result
        if success:
            self.active_subscriptions[ctx.meid] = True
            self.health.set_state(AppState.READY)
            self.metrics.ready_state.set(1)
            logger.info("Subscrição E2 confirmada pelo SubMgr", meid=ctx.meid, subscription_id=ctx.subscription_id)
            if not self.decision_loop_started:
                self.decision_loop_started = True
                threading.Thread(target=self._decision_loop, daemon=True).start()
        else:
            self.active_subscriptions.pop(ctx.meid, None)
            self.metrics.subs_failures.inc()
            logger.error("Subscrição E2 recusada", meid=ctx.meid, cause=ctx.error_cause)
            if not any(self.active_subscriptions.values()):
                self.health.set_state(AppState.DEGRADED)
                self.metrics.ready_state.set(0)
        self.metrics.active_e2_nodes.set(sum(self.active_subscriptions.values()))
        self.metrics.active_subs.set(sum(self.active_subscriptions.values()))
        return success

    def _subscription_response_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        """Trata resposta de subscricao E2 (RIC_SUB_RESP) emitida pelo SubMgr."""
        logger.info("RIC_SUB_RESP recebido com sucesso", summary=summary)
        meid = summary.get("meid") if isinstance(summary, dict) else None
        if not meid or meid not in self.active_subscriptions:
            logger.warning("RIC_SUB_RESP recebido sem subscrição local pendente; readiness não alterada.")
            self._safe_rmr_free(xapp_instance, sbuf)
            return
        self.active_subscriptions[meid] = True
        self.health.set_state(AppState.READY)
        self.metrics.ready_state.set(1)
        self.metrics.active_e2_nodes.set(len(self.active_subscriptions))
        self.metrics.active_subs.set(sum(self.active_subscriptions.values()))
        if not self.decision_loop_started:
            self.decision_loop_started = True
            threading.Thread(target=self._decision_loop, daemon=True).start()
        self._safe_rmr_free(xapp_instance, sbuf)

    def _subscription_failure_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        logger.error("RIC_SUBSCRIPTION_FAILURE recebido; xApp não está pronta", summary=summary)
        failed_meid = summary.get("meid") if isinstance(summary, dict) else None
        if failed_meid and failed_meid in self.active_subscriptions:
            self.active_subscriptions.pop(failed_meid, None)
        else:
            self.active_subscriptions.clear()
        if not self.active_subscriptions:
            self.health.set_state(AppState.DEGRADED)
            self.metrics.ready_state.set(0)
        self.metrics.active_e2_nodes.set(len(self.active_subscriptions))
        self.metrics.active_subs.set(sum(self.active_subscriptions.values()))
        self.metrics.subs_failures.inc()
        self._safe_rmr_free(xapp_instance, sbuf)

    def _kpm_indication_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        self.metrics.record_kpm()
        payload = summary.get("payload")
        if payload:
            reports_data = self.backend.decode_kpm(payload)
            if reports_data:
                for data in reports_data:
                    report = KPMReport(
                        node_id=data["node_id"],
                        ue_id=data["ue_id"],
                        drb_thp_dl=data.get("drb_thp_dl"),
                        drb_thp_ul=data.get("drb_thp_ul"),
                        drb_delay_dl=data.get("drb_delay_dl"),
                        prb_used_dl=data.get("prb_used_dl")
                    )
                    self.perception.update_kpm_report(report)
                    self.reasoning.update_kpm_report(report)
            else:
                self.metrics.kpm_decode_err.inc()
        self._safe_rmr_free(xapp_instance, sbuf)

    def _action_proposal_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        """Recebe acoes propostas por outras xApps via RMR e enfileira na janela temporal."""
        payload = summary.get("payload")
        if self.oran_strict:
            logger.error(
                "Proposta externa rejeitada: o transporte atual não fornece identidade de xApp "
                "autenticada para autorização."
            )
            self._safe_rmr_free(xapp_instance, sbuf)
            return
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
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError("value must be a finite number")
                try:
                    value = float(value)
                except (OverflowError, TypeError, ValueError) as exc:
                    raise ValueError("value must be a finite number") from exc
                if not math.isfinite(value):
                    raise ValueError("value must be a finite number")
                if isinstance(priority, bool) or not isinstance(priority, int) or not 0 <= priority <= 100:
                    raise ValueError("priority must be an integer in [0, 100]")
                defer_ok = data.get("defer_ok", False)
                if not isinstance(defer_ok, bool):
                    raise ValueError("defer_ok must be a boolean")
                ttl_ms = data.get("ttl_ms")
                if ttl_ms is not None and (isinstance(ttl_ms, bool) or not isinstance(ttl_ms, (int, float))
                                           or not math.isfinite(float(ttl_ms)) or not 0 < float(ttl_ms) <= 60000):
                    raise ValueError("ttl_ms must be a number in (0, 60000]")
                action = XAppAction(
                    xapp_id=xapp_id,
                    node_id=node_id,
                    parameter=parameter,
                    value=value,
                    priority=priority,
                    defer_ok=defer_ok,
                    ttl_ms=None if ttl_ms is None else float(ttl_ms),
                )
                try:
                    self._enqueue(action)
                except OverflowError:
                    logger.error("Proposal buffer limit reached; incoming action rejected.")
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
            ack_info = self.dispatcher.handle_ack(payload, node_id=summary.get("meid"))
            if ack_info:
                action_id = ack_info.get("action_id")
                action = self.pending_actions_by_id.pop(action_id, None)
                if action is not None:
                    action.t_ack = now_ts()
                    self.perception.commit_actions([action])
                self.metrics.ctrl_ack.inc()
                logger.info(
                    "RIC_CONTROL_ACK correlacionado",
                    control_request_id=ack_info.get("control_request_id"),
                    status=ack_info.get("status"),
                )
            else:
                logger.warning("RIC_CONTROL_ACK recebido sem transação ativa correlacionada.")
        logger.info("Recebido RIC_CONTROL_ACK", summary=summary)
        self._safe_rmr_free(xapp_instance, sbuf)

    def _control_failure_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        logger.warning("Recebido RIC_CONTROL_FAILURE", summary=summary)
        payload = summary.get("payload")
        if payload:
            fail_info = self.dispatcher.handle_failure(payload, node_id=summary.get("meid"))
            if fail_info:
                self.metrics.ctrl_fail.inc()
                self.pending_actions_by_id.pop(fail_info.get("action_id"), None)
            else:
                logger.warning("RIC_CONTROL_FAILURE recebido sem transação ativa correlacionada.")
        self._safe_rmr_free(xapp_instance, sbuf)

    def inject_xapp_action(self, action: XAppAction):
        """API publica para injecao de acoes simuladas (usada em testes)"""
        self._enqueue(action)

    def _enqueue(self, action: XAppAction) -> Urgency:
        """Classifica a proposta e a coloca na fila crítica ou na janela de decisão."""
        with self.buffer_lock:
            full = len(self.proposal_buffer) + len(self.critical_queue) + len(self.deferred) >= self.MAX_PROPOSALS
            if not full:
                downgraded = self.decision_window.downgraded_count
                urgency = self.decision_window.classify_and_admit(action)
                action.urgency = urgency.value
                if self.decision_window.downgraded_count != downgraded:
                    self.metrics.critical_downgraded.inc()
                    logger.warning("Cota de ações críticas excedida; proposta tratada como URGENT",
                                   xapp=action.xapp_id, param=action.parameter)
        if full:
            self._reject(action, preg.OVERFLOW, "Proposal buffer limit reached")
            raise OverflowError("Proposal buffer limit reached")
        with self.buffer_lock:
            self.decision_window.observe_arrival()
            if urgency == Urgency.CRITICAL:
                self.critical_queue.append(action)
                self.urgent_event.set()
                return urgency
            if not self.proposal_buffer:
                self.window_start = now_ts()
                self.buffer_deadline_ms = self.decision_window.window_ms()
            if urgency == Urgency.URGENT:
                # Janela fixa: fecha na hora (fast-flush); adaptativa: espera urgent_window_ms
                urgent_ms = self.decision_window.deadline_ms(urgency) if self.decision_window.config.adaptive else 0.0
                self.buffer_deadline_ms = min(self.buffer_deadline_ms, urgent_ms)
                self.urgent_event.set()
            self.proposal_buffer.append(action)
        return urgency

    def _take_ready_actions(self) -> Tuple[List[XAppAction], List[XAppAction]]:
        """(grupo crítico, lote da janela). O grupo crítico leva junto as propostas pendentes para
        o mesmo nó ou para nós vizinhos, que competem com ele na mesma arbitragem."""
        with self.buffer_lock:
            critical: List[XAppAction] = []
            if self.critical_queue:
                critical = list(self.critical_queue)
                self.critical_queue.clear()
                nodes = {a.node_id for a in critical}
                for node in list(nodes):
                    nodes |= self.inter_cell_rules.neighbors.get(node, set())
                related = [a for a in self.proposal_buffer if a.node_id in nodes]
                if related:
                    critical += related
                    self.proposal_buffer = [a for a in self.proposal_buffer if a.node_id not in nodes]
                    if not self.proposal_buffer:
                        self.window_start = 0.0
            batch: List[XAppAction] = []
            if self.proposal_buffer:
                elapsed_ms = (now_ts() - self.window_start) * 1000
                if elapsed_ms >= self.buffer_deadline_ms:
                    batch = list(self.proposal_buffer)
                    self.proposal_buffer.clear()
                    self.window_start = 0.0
        # Validade: proposta que esperou mais que a validade não é decidida sobre um estado velho
        now = time.perf_counter()
        stale = [a for a in critical + batch if self.decision_window.remaining_ms(a, now) < 0]
        for action in stale:
            age_ms = (now - action.arrival_monotonic) * 1000.0
            self._reject(action, preg.STALE, f"age {age_ms:.0f} ms > ttl {self.decision_window.ttl_ms(action):.0f} ms")
        if stale:
            stale_ids = {a.action_id for a in stale}
            critical = [a for a in critical if a.action_id not in stale_ids]
            batch = [a for a in batch if a.action_id not in stale_ids]
        return critical, batch

    def _release_deferred(self, now: Optional[float] = None) -> int:
        """Devolve à janela as propostas adiadas cujo bloqueio já expirou (são reavaliadas do zero)."""
        now = time.perf_counter() if now is None else now
        with self.buffer_lock:
            ready = [a for t, a in self.deferred if t <= now]
            self.deferred = [(t, a) for t, a in self.deferred if t > now]
        for action in ready:
            try:
                self._enqueue(action)
            except OverflowError:
                pass
        return len(ready)

    def _reject(self, action: XAppAction, reason: str, detail: str = "", decision_id: Optional[str] = None,
                winner: Optional[XAppAction] = None) -> Dict[str, Any]:
        """Registra a proposta não atendida, adia se couber e avisa a xApp."""
        retry_after_ms = None
        deferred = False
        if reason == preg.HYSTERESIS:
            retry_after_ms = self.refinement.remaining_lockout_ms(action)
            remaining = self.decision_window.remaining_ms(action)
            if action.defer_ok and retry_after_ms < remaining:
                ready_at = time.perf_counter() + (retry_after_ms + 5.0) / 1000.0
                with self.buffer_lock:
                    self.deferred.append((ready_at, action))
                deferred = True
                self.metrics.proposals_deferred.inc()
        entry = self.proposals.record(action, reason, detail, decision_id=decision_id, winner=winner,
                                      retry_after_ms=retry_after_ms, deferred=deferred)
        self.metrics.proposals_rejected.labels(reason=reason).inc()
        self._notify_xapp(entry)
        return entry

    def _notify_xapp(self, entry: Dict[str, Any]) -> None:
        """RDL_ACTION_RESULT (30001) para as xApps; cada uma filtra pelo próprio xapp_id."""
        if not self.notify_xapps or isinstance(self.xapp, MockRMRXapp):
            return
        payload = {"status": "REJECTED", **{k: entry[k] for k in (
            "action_id", "xapp_id", "node_id", "parameter", "value", "reason", "detail",
            "retry_after_ms", "deferred", "decision_id", "winner_xapp_id")}}
        try:
            if self.xapp.rmr_send(json.dumps(payload).encode("utf-8"), RDL_ACTION_RESULT):
                self.metrics.rmr_tx.inc()
        except Exception as exc:  # o aviso nunca bloqueia a decisão
            logger.warning("Falha ao enviar RDL_ACTION_RESULT", error=str(exc))

    def _rejections_view(self, xapp_id: Optional[str] = None, node_id: Optional[str] = None,
                         reason: Optional[str] = None, since: float = 0.0, limit: int = 100) -> Dict[str, Any]:
        with self.buffer_lock:
            deferred = len(self.deferred)
        return {"summary": {**self.proposals.summary(), "deferred_pending": deferred},
                "entries": self.proposals.query(xapp_id=xapp_id, node_id=node_id, reason=reason,
                                                since=since, limit=limit)}

    def _process_action_group(self, actions: List[XAppAction], fast_path: bool = False):
        """
        Processa todas as acoes acumuladas na Decision Window (Feature 2):
        1. Identifica conflitos diretos (por alvo) e indiretos (por par de parâmetros);
        2. Arbitra em dois estágios: TVS escolhe um vencedor por (nó, parâmetro); o EEVS
           decide os conflitos indiretos apenas entre esses vencedores. Cada resolução é
           validada pelo Refinement sem auto-bloqueio intra-lote;
        3. Seleciona uma ação por alvo (a incumbente vencedora não é reenviada) e formaliza
           a RDLDecision ANTES do despacho;
        4. Executa o despacho das ações selecionadas via ControlDispatcher propagando a latência de decisão.
        """
        t0 = now_ts()
        if self.oran_strict and not self.backend.metadata.protocol_interoperability_verified:
            logger.error(
                "Despacho de controle bloqueado: interoperabilidade E2 não foi validada."
            )
            return
        for act in actions:
            self.memory.add_action(act)

        from src.observability.causal_tracker import causal_tracker
        causal_tracker.register_proposals([action.action_id for action in actions])

        # 0. Safety Guard por proposta, ANTES da arbitragem: uma ação fora dos limites
        # físicos é descartada sozinha. Se entrasse na arbitragem, a validação da resolução
        # rejeitaria o lote inteiro e uma xApp maliciosa vetaria as ações legítimas com que
        # conflita (observado no cenário S7 de injeção de falhas).
        # Motivo de cada proposta não atendida: action_id -> (motivo, detalhe, vencedora)
        not_served: Dict[str, Tuple[XAppAction, str, str, Optional[XAppAction]]] = {}
        safe_actions: List[XAppAction] = []
        for act in actions:
            within_bounds, reason = self.refinement.check_bounds(act)
            if within_bounds:
                safe_actions.append(act)
            else:
                logger.warning("Proposta bloqueada pelo Safety Guard antes da arbitragem",
                               xapp=act.xapp_id, param=act.parameter, val=act.value, reason=reason)
                causal_tracker.record_safety_validation(intervention=True)
                not_served[act.action_id] = (act, preg.SAFETY, reason, None)
        actions = safe_actions

        conflicts = self.perception.detect_action_group(actions)
        self.metrics.update_active_xapps(len(self.perception.get_active_xapps()))
        for conflict in conflicts:
            try:
                self.knowledge_graph.record_conflict(conflict)
            except Exception as exc:  # o grafo nunca bloqueia a decisão
                logger.warning("Falha ao registrar conflito no grafo de conhecimento", error=str(exc))

        def target_of(act: XAppAction) -> Tuple[str, str]:
            return (act.node_id, act.parameter)

        def is_incumbent(act: XAppAction) -> bool:
            """Ação já confirmada pela RAN: mantê-la não gera novo controle."""
            return self.perception.get_committed_action(act.node_id, act.parameter) is act

        def register(conflict: ConflictEvent) -> None:
            logger.info("Conflito Detectado", conflict_id=conflict.conflict_id, type=conflict.conflict_type.name)
            self.memory.add_conflict(conflict)
            self.metrics.record_conflict(conflict)
            causal_tracker.register_conflict_event(
                conflict.conflict_id,
                conflict.conflict_type.name,
                len(conflict.involved_xapps),
                [action.action_id for action in conflict.involved_xapps],
            )

        def arbitrate(conflict: ConflictEvent) -> Tuple[ResolutionAction, bool, str]:
            t_conflict_start = now_ts()
            resolution = self.reasoning.resolve(conflict)
            # A incumbente não gera controle, logo não passa de novo pela histerese/limites.
            to_validate = [act for act in resolution.winning_actions if not is_incumbent(act)]
            if resolution.winning_actions and not to_validate:
                is_valid, reason = True, "Incumbent kept"
            else:
                check = ResolutionAction(
                    conflict_id=resolution.conflict_id,
                    strategy_used=resolution.strategy_used,
                    winning_actions=to_validate,
                    modified_value=resolution.modified_value,
                    confidence=resolution.confidence,
                    validation_level=resolution.validation_level,
                )
                # Valida contra o histórico de lotes anteriores sem gravar timestamp no meio do lote
                is_valid, _, reason = self.refinement.validate(check, conflict, record_timestamp=False)
            self.memory.add_resolution(resolution)
            self.metrics.record_resolution(resolution, now_ts() - t_conflict_start)
            return resolution, is_valid, reason

        representative: Dict[Tuple[str, str], XAppAction] = {}
        blocked_targets: set = set()
        block_reason: Dict[Tuple[str, str], Tuple[str, str, Optional[XAppAction]]] = {}
        validated_ids: set = set()
        strategy_names: List[str] = []
        action_conflicts: Dict[str, List[str]] = {}

        def admit(target: Tuple[str, str], act: XAppAction, conflict_id: str) -> None:
            representative[target] = act
            validated_ids.add(act.action_id)
            linked = action_conflicts.setdefault(act.action_id, [])
            if conflict_id not in linked:
                linked.append(conflict_id)
            causal_tracker.record_safety_validation()

        # 1. Estágio DIRETO: um vencedor (TVS sobre todos os candidatos) por (nó, parâmetro)
        for conflict in (c for c in conflicts if c.conflict_type == ConflictType.DIRECT):
            register(conflict)
            target = target_of(conflict.involved_xapps[0])
            resolution, is_valid, reason = arbitrate(conflict)
            winner = resolution.winning_actions[0] if resolution.winning_actions else None
            if is_valid and winner is not None:
                admit(target, winner, conflict.conflict_id)
                strategy_names.append(resolution.strategy_used.name)
                logger.info("Conflito Resolvido", conflict=conflict.conflict_id, strategy=resolution.strategy_used.name, action=winner.parameter)
            else:
                blocked_targets.add(target)
                block_reason.setdefault(target, (preg.classify_guard_reason(reason), reason, None))
                logger.warning("Resolucao Rejeitada ou Lote Vazio", reason=reason, conflict=conflict.conflict_id)
                for _ in conflict.involved_xapps:
                    causal_tracker.record_safety_validation(intervention=True)

        # 2. Estágio INDIRETO e ENTRE CÉLULAS: EEVS apenas entre os candidatos que sobreviveram
        # ao estágio direto; os conflitos entre células vêm depois dos indiretos do mesmo nó.
        for conflict in (
            c for kind in (ConflictType.INDIRECT, ConflictType.INTER_CELL)
            for c in conflicts if c.conflict_type == kind
        ):
            register(conflict)
            reduced = [
                act for act in conflict.involved_xapps
                if target_of(act) not in blocked_targets
                and representative.get(target_of(act), act) is act
            ]
            targets = {target_of(act) for act in reduced}
            if (
                len(targets) < 2
                or len({act.xapp_id for act in reduced}) < 2
                or all(is_incumbent(act) for act in reduced)
            ):
                continue  # a oposição foi eliminada no estágio direto
            sub_conflict = ConflictEvent(
                conflict_type=conflict.conflict_type,
                severity=conflict.severity,
                involved_xapps=reduced,
                affected_kpis=conflict.affected_kpis,
                description=conflict.description,
                conflict_id=conflict.conflict_id,
                detected_at=conflict.detected_at,
            )
            resolution, is_valid, reason = arbitrate(sub_conflict)
            winners_by_target: Dict[Tuple[str, str], XAppAction] = {}
            if is_valid:
                for act in resolution.winning_actions:
                    winners_by_target.setdefault(target_of(act), act)
                strategy_names.append(resolution.strategy_used.name)
            else:
                logger.warning("Resolucao Rejeitada ou Lote Vazio", reason=reason, conflict=conflict.conflict_id)
            incumbents = {target_of(act): act for act in reduced if is_incumbent(act)}
            for target in sorted(targets):
                winner = winners_by_target.get(target)
                if winner is None and target in incumbents:
                    # Sem vencedor (resolução rejeitada, p. ex. pela histerese): o alvo de uma ação já
                    # confirmada continua representado por ela e segue como oposição nos conflitos
                    # seguintes. Bloqueá-lo deixava a proposta concorrente passar sem oposição (achado 53).
                    admit(target, incumbents[target], conflict.conflict_id)
                elif winner is None:
                    blocked_targets.add(target)
                    if is_valid:
                        block_reason.setdefault(target, (preg.LOST_ARBITRATION, f"EEVS ({conflict.conflict_type.name})",
                                                         resolution.winning_actions[0] if resolution.winning_actions else None))
                    else:
                        block_reason.setdefault(target, (preg.classify_guard_reason(reason), reason, None))
                    causal_tracker.record_safety_validation(intervention=True)
                else:
                    admit(target, winner, conflict.conflict_id)

        # 3. Seleção final por alvo: vencedor arbitrado ou proposta sem conflito (pass-through)
        proposals_by_target: Dict[Tuple[str, str], List[XAppAction]] = {}
        for act in actions:
            proposals_by_target.setdefault(target_of(act), []).append(act)

        def serve_none(proposals: List[XAppAction], reason: str, detail: str, winner: Optional[XAppAction]) -> None:
            for p in proposals:
                if p is not winner:
                    not_served[p.action_id] = (p, reason, detail, winner)

        all_selected: List[XAppAction] = []
        for target, proposals in proposals_by_target.items():
            if target in blocked_targets:
                serve_none(proposals, *block_reason.get(target, (preg.SAFETY, "target blocked", None)))
                continue
            act = representative.get(target)
            if act is None:
                # Propostas convergentes (mesmo valor) ou única: maior prioridade, depois a mais recente.
                act = max(enumerate(proposals), key=lambda item: (item[1].priority, item[0]))[1]
            if is_incumbent(act):
                logger.info("Valor atual mantido: ação já aplicada venceu a arbitragem", node=act.node_id, param=act.parameter)
                serve_none(proposals, preg.LOST_ARBITRATION, "incumbent kept", act)
                continue
            if act.action_id not in validated_ids:
                is_safe, _, reason = self.refinement.validate_single_action(act, record_timestamp=False)
                if not is_safe:
                    logger.warning("Acao Limpa Bloqueada pelo Safety Guard", reason=reason, param=act.parameter)
                    causal_tracker.record_safety_validation(intervention=True)
                    serve_none(proposals, preg.classify_guard_reason(reason), reason, None)
                    continue
                logger.info("Acao Limpa Admitida (Pass-Through)", xapp=act.xapp_id, param=act.parameter, val=act.value)
                causal_tracker.record_safety_validation()
            serve_none(proposals, preg.LOST_ARBITRATION, "same value as winner" if all(
                p.value == act.value for p in proposals) else "lower utility or priority", act)
            act.t_selection = now_ts()
            all_selected.append(act)

        # Commit atômico dos timestamps de controle para o lote atual
        self.refinement.commit_control_timestamps(all_selected)
        decision_latency_ms = max(0.001, (now_ts() - t0) * 1000.0)

        # 4. Formalização da RDLDecision ANTES do Despacho (Garantia de Rastreabilidade)
        decision = RDLDecision(
            state={"active_xapps": len(self.perception.get_active_xapps())},
            proposals=actions,
            conflicts=conflicts,
            safety_result={"admitted_count": len(all_selected), "rejected_count": max(0, len(actions) - len(all_selected))},
            selected_actions=all_selected,
            reason="CRITICAL_FAST_PATH" if fast_path else "RESOLVED_AND_PASSTHROUGH",
            strategy_used=",".join(strategy_names) if strategy_names else "PASS_THROUGH",
            affected_node=all_selected[0].node_id if all_selected else "gnb_01",
            affected_cell=getattr(all_selected[0], "cell_id", "cell_01") if all_selected else "cell_01",
            previous_safe_value=None,
        )
        logger.info("RDLDecision Formalizada", decision_id=decision.decision_id, strategy=decision.strategy_used, selected_count=len(all_selected))
        if fast_path:
            causal_tracker.record_fast_path(decision.decision_id, [a.action_id for a in all_selected])
            self.metrics.critical_path.inc()
        try:
            source = getattr(getattr(self.reasoning, "last_decision", None), "source", "H_RDL")
            self.knowledge_graph.record_decision(decision.decision_id, decision.strategy_used, all_selected,
                                                 [c.conflict_id for c in conflicts],
                                                 policy=self.a1_policies.effective_policy() or None, source=source)
        except Exception as exc:
            logger.warning("Falha ao registrar decisão no grafo de conhecimento", error=str(exc))

        # 5. Despacho de Controle para Ações Admitidas via ControlDispatcher
        dispatched_actions = []
        for act in all_selected:
            previous_action = self.perception.get_committed_action(act.node_id, act.parameter)
            kpm = self.perception.get_latest_kpm(act.node_id)
            per_action_decision = RDLDecision(
                decision_id=f"{decision.decision_id}-{act.action_id[:6]}",
                state={
                    "kpm_before": {
                        "drb_thp_dl": kpm.drb_thp_dl,
                        "drb_thp_ul": kpm.drb_thp_ul,
                        "drb_delay_dl": kpm.drb_delay_dl,
                        "prb_used_dl": kpm.prb_used_dl,
                    } if kpm is not None else {},
                },
                selected_actions=[act],
                safety_result={"is_safe": True},
                affected_node=act.node_id,
                affected_cell=getattr(act, "cell_id", "cell_01"),
                previous_safe_value=previous_action.value if previous_action else None,
                strategy_used=decision.strategy_used,
                conflict_id=action_conflicts.get(act.action_id, [None])[0],
                conflict_ids=action_conflicts.get(act.action_id, []),
            )
            self.pending_actions_by_id[act.action_id] = act
            control_request_id = self.dispatcher.dispatch_control(
                per_action_decision, decision_latency_ms=decision_latency_ms
            )
            if control_request_id is None:
                self.pending_actions_by_id.pop(act.action_id, None)
                not_served[act.action_id] = (act, preg.DISPATCH_FAILED, "RIC Control not sent", None)
                continue
            self.metrics.ctrl_req.inc()
            dispatched_actions.append(act)
            for conflict_id in action_conflicts.get(act.action_id, []):
                causal_tracker.record_conflict_resolution(conflict_id)

        # 6. Propostas não atendidas: registro, adiamento (se pedido) e aviso à xApp
        for act, reason, detail, winner in not_served.values():
            self._reject(act, reason, detail, decision_id=decision.decision_id, winner=winner)

    def cleanup_expired_transactions(self, timeout_s: float = 5.0) -> int:
        """Limpa correlações de request expiradas; status de controle é gerido pelo dispatcher."""
        return self.allocator.cleanup_expired(timeout_s)

    def _decision_loop(self):
        last_cleanup = now_ts()
        while self.running:
            triggered = self.urgent_event.wait(timeout=0.05)
            if triggered:
                self.urgent_event.clear()

            # Anti-leak cleanup e timeout de controle a cada 1 segundo
            now = now_ts()
            if (now - last_cleanup) >= 1.0:
                self.cleanup_expired_transactions()
                expired = self.dispatcher.check_timeouts(now)
                for request_id in expired:
                    self.metrics.ctrl_timeout.inc()
                    request_info = self.dispatcher.pending_requests.get(request_id, {})
                    self.pending_actions_by_id.pop(request_info.get("action_id"), None)
                self.dispatcher.prune_finalized(now=now)
                last_cleanup = now

            self._release_deferred()
            critical, batch = self._take_ready_actions()
            if critical:
                # Caminho rápido: ação crítica decidida sem esperar a janela (doc 09 §2.2)
                logger.info("Caminho crítico", actions=len(critical))
                self._process_action_group(critical, fast_path=True)
            if batch:
                logger.info(f"Decision Window Flushed. Processing batch of {len(batch)} actions.")
                self._process_action_group(batch)

    def _send_control(
        self,
        node_id: str,
        parameter: str,
        value: float,
        action: Optional[XAppAction] = None,
        decision_id: Optional[str] = None,
    ) -> bool:
        target_action = action or XAppAction(
            xapp_id="hrdl_core",
            node_id=node_id,
            parameter=parameter,
            value=value,
            priority=100,
        )
        if self.oran_strict and not self.backend.metadata.protocol_interoperability_verified:
            logger.error("Controle rejeitado: interoperabilidade E2 não foi validada.")
            return False
        previous_action = self.perception.get_committed_action(node_id, parameter)
        decision = RDLDecision(
            decision_id=decision_id or str(uuid.uuid4())[:8],
            selected_actions=[target_action],
            safety_result={"is_safe": True},
            affected_node=node_id,
            previous_safe_value=previous_action.value if previous_action else None,
        )
        self.pending_actions_by_id[target_action.action_id] = target_action
        request_id = self.dispatcher.dispatch_control(decision)
        if request_id is None:
            self.pending_actions_by_id.pop(target_action.action_id, None)
            return False
        self.metrics.ctrl_req.inc()
        return True


if __name__ == "__main__":
    app = RDLxApp()
    try:
        app.start()
    except KeyboardInterrupt:
        app.stop()
