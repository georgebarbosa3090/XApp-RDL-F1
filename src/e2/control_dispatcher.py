import time
import uuid
import threading
from math import isfinite
from typing import Dict, Optional, List, Any, Tuple
from src.e2.rc_encoder import E2SMRCEncoder, ControlAction
from src.e2.e2ap.control import parse_ric_control_ack, parse_ric_control_failure, build_ric_control_request
from src.e2.e2ap.constants import (
    RIC_CONTROL_REQ,
    RIC_CONTROL_ACK,
    RIC_CONTROL_FAILURE,
)
from src.infrastructure.sdl_repository import SdlRepository
from src.infrastructure.ran_backend_adapter import RANBackendAdapter
from src.infrastructure.ric_request_id_allocator import get_ric_request_id_allocator
from src.conflict_types import RDLDecision as Decision
from src.observability.logging import setup_logger
from src.observability.causal_tracker import causal_tracker

logger = setup_logger("ControlDispatcher")

class ControlDispatcher:
    def __init__(self, rmr_client, sdl_repo: SdlRepository,
                 backend: Optional[RANBackendAdapter] = None,
                 default_timeout_s: float = 5.0):
        self.rmr = rmr_client
        self.sdl = sdl_repo
        self.backend = backend
        self.allocator = get_ric_request_id_allocator()
        self.encoder = E2SMRCEncoder()
        self.default_timeout_s = default_timeout_s
        self.pending_requests: Dict[str, Dict[str, Any]] = {}
        self.req_key_to_id: Dict[Tuple[str, int, int, int], str] = {}
        self.rollback_history: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def dispatch_control(self, decision: Decision) -> Optional[str]:
        # Suporta tanto safety_result dict quanto safety_validation booleano
        is_safe = False
        if hasattr(decision, "safety_result") and isinstance(decision.safety_result, dict):
            is_safe = decision.safety_result.get("is_safe") is True
        elif hasattr(decision, "safety_validation"):
            is_safe = getattr(decision, "safety_validation") is True
            
        selected_act = None
        if hasattr(decision, "selected_actions") and decision.selected_actions:
            selected_act = decision.selected_actions[0]
        elif hasattr(decision, "selected_action"):
            selected_act = getattr(decision, "selected_action")

        if not is_safe or selected_act is None:
            logger.warning(f"Decisão {getattr(decision, 'decision_id', 'unknown')} ignorada por falha de safety guard ou ausência de ação.")
            return None

        if hasattr(selected_act, "action") and isinstance(selected_act.action, dict):
            action_data = selected_act.action
            param = action_data.get("parameter", "PRB_QUOTA")
            val = action_data.get("value", 50.0)
            target_node = getattr(decision, "affected_node", "gnb_01")
        else:
            param = getattr(selected_act, "parameter", "PRB_QUOTA")
            val = getattr(selected_act, "value", 50.0)
            target_node = getattr(selected_act, "node_id", getattr(decision, "affected_node", "gnb_01"))

        try:
            val = float(val)
        except (TypeError, ValueError):
            logger.error("Ação de controle rejeitada: valor não numérico.")
            return None
        if not isinstance(target_node, str) or not target_node.strip() or not isfinite(val):
            logger.error("Ação de controle rejeitada: nó ou valor inválido.")
            return None

        target_cell = getattr(decision, "affected_cell", "cell_01")
        action_id = getattr(selected_act, "action_id", str(uuid.uuid4())[:8])
        
        from src.e2.rc.capability_registry import (
            CapabilityNotDiscoveredError,
            rc_capability_registry,
        )
        try:
            capability = rc_capability_registry.get_action_capability(
                param, target_node, strict_mode=None
            )
            if not capability.min_value <= val <= capability.max_value:
                logger.error(
                    "Ação de controle fora da capacidade anunciada",
                    node_id=target_node,
                    parameter=param,
                    value=val,
                    min_value=capability.min_value,
                    max_value=capability.max_value,
                )
                return None
            ran_fn_id = rc_capability_registry.get_rc_function_id(target_node)
            style_type, ctrl_action_id, param_id = rc_capability_registry.resolve_action(
                param_name=param, node_id=target_node
            )
        except (CapabilityNotDiscoveredError, KeyError, ValueError) as exc:
            logger.error("Ação de controle sem capacidade RC válida", error=str(exc))
            return None

        # Alocar IDs
        req_id_obj = self.allocator.allocate(
            node_id=target_node,
            ran_function_id=ran_fn_id,
            decision_id=getattr(decision, "decision_id", None),
            action_id=action_id
        )
        control_request_id = str(uuid.uuid4())
        requestor_id = req_id_obj.requestor_id
        instance_id = req_id_obj.instance_id

        # Usa backend como fonte única de encoding, quando disponível
        try:
            if self.backend is not None:
                pdu_aper = self.backend.map_action_to_control_pdu(
                    selected_act, requestor_id=requestor_id, instance_id=instance_id
                )
            else:
                encoded = self.encoder.encode_control_parts(
                    node_id=target_node, parameter=param, value=val,
                    style_type=style_type, action_id=ctrl_action_id, param_id=param_id,
                )
                ctrl_ctx = build_ric_control_request(
                    node_id=target_node,
                    ran_function_id=ran_fn_id,
                    header_bytes=encoded.header_aper,
                    message_bytes=encoded.message_aper,
                    requestor_id=requestor_id,
                    instance_id=instance_id,
                    ack_request=1,
                )
                pdu_aper = ctrl_ctx.pdu_aper
        except Exception as exc:
            self.allocator.pop_correlation(target_node, ran_fn_id, requestor_id, instance_id)
            logger.error("Falha ao codificar RIC_CONTROL_REQUEST", error=str(exc))
            return None
        payload = pdu_aper
        
        # Armazenar tracking
        now = time.time()
        tracking_info = {
            "control_request_id": control_request_id,
            "requestor_id": requestor_id,
            "instance_id": instance_id,
            "ran_function_id": ran_fn_id,
            "meid": target_node,
            "decision_id": getattr(decision, "decision_id", control_request_id),
            "action_id": action_id,
            "parameter": param,
            "target_value": val,
            "previous_safe_value": getattr(decision, "previous_safe_value", None),
            "style_type": style_type,
            "control_action_id": ctrl_action_id,
            "parameter_id": param_id,
            "sent_at": now,
            "timeout_at": now + self.default_timeout_s,
            "status": "SENT"
        }
        
        key = (target_node, ran_fn_id, requestor_id, instance_id)
        with self._lock:
            if key in self.req_key_to_id:
                self.allocator.pop_correlation(target_node, ran_fn_id, requestor_id, instance_id)
                logger.error("RICrequestID duplicado enquanto ainda estava pendente", key=key)
                return None
            self.pending_requests[control_request_id] = tracking_info
            self.req_key_to_id[key] = control_request_id
        
        try:
            self.sdl.save_control_request(control_request_id, tracking_info)
        except Exception as e:
            logger.warning(f"Não foi possível persistir no SDL: {e}")
            
        # Enviar via RMR (Message Type 12040 = RIC_CONTROL_REQUEST)
        logger.info(f"Enviando RIC_CONTROL_REQUEST {control_request_id} (ReqID {requestor_id}) para MEID {target_node}")
        try:
            sent = self.rmr.rmr_send(payload, RIC_CONTROL_REQ, target_node)
        except Exception as exc:
            sent = False
            logger.error("Exceção ao enviar RIC_CONTROL_REQUEST via RMR", error=str(exc))
        if not sent:
            tracking_info["status"] = "SEND_FAILED"
            with self._lock:
                self.pending_requests.pop(control_request_id, None)
                self.req_key_to_id.pop(key, None)
            self.allocator.pop_correlation(target_node, ran_fn_id, requestor_id, instance_id)
            logger.error(f"RMR rejeitou RIC_CONTROL_REQUEST {control_request_id}; despacho cancelado.")
            return None
        return control_request_id

    def _find_request(self, parsed: Dict[str, Any], node_id: Optional[str]) -> Optional[Tuple[str, Tuple[str, int, int, int]]]:
        requestor_id = parsed["requestor_id"]
        instance_id = parsed["instance_id"]
        ran_function_id = parsed["ran_function_id"]
        with self._lock:
            if node_id:
                key = (node_id, ran_function_id, requestor_id, instance_id)
                control_id = self.req_key_to_id.get(key)
                return (control_id, key) if control_id else None
            matches = [
                (key, control_id)
                for key, control_id in self.req_key_to_id.items()
                if key[1:] == (ran_function_id, requestor_id, instance_id)
            ]
            if len(matches) != 1:
                logger.error(
                    "Resposta E2 sem nó de origem ou com correlação ambígua",
                    ran_function_id=ran_function_id,
                    requestor_id=requestor_id,
                    instance_id=instance_id,
                    matches=len(matches),
                )
                return None
            key, control_id = matches[0]
            return control_id, key

    def handle_ack(self, payload: bytes, node_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Trata o RIC_CONTROL_ACK decodificando a PDU E2AP canônica.
        """
        try:
            parsed = parse_ric_control_ack(payload)
            match = self._find_request(parsed, node_id)
            if not match:
                logger.warning("CORRELATION_ERROR: RIC_CONTROL_ACK sem requisição pendente correspondente.")
                return None
            ctrl_id, key = match
            req_id = parsed["requestor_id"]
            inst_id = parsed["instance_id"]
            with self._lock:
                info = self.pending_requests.get(ctrl_id)
            if info is not None:
                info["status"] = "ACKNOWLEDGED"
                info["ack_received_at"] = time.time()
                rtt_ms = (info["ack_received_at"] - info["sent_at"]) * 1000.0
                try:
                    self.sdl.update_control_result(ctrl_id, "ACKNOWLEDGED")
                except Exception as exc:
                    logger.warning("Falha ao persistir ACK no SDL", control_request_id=ctrl_id, error=str(exc))
                correlation_id = causal_tracker.correlation_id(
                    info["meid"], info["ran_function_id"], req_id, inst_id
                )
                causal_tracker.record_ack(correlation_id, rtt_ms=rtt_ms)
                with self._lock:
                    self.req_key_to_id.pop(key, None)
                self.allocator.pop_correlation(info["meid"], info["ran_function_id"], req_id, inst_id)
                logger.info(f"Recebido RIC_CONTROL_ACK para req {ctrl_id} (ReqID {req_id}) - RTT: {rtt_ms:.2f} ms")
                return info
            else:
                logger.warning(f"RIC_CONTROL_ACK recebido para req não rastreado: {key}")
                return None
        except Exception as e:
            logger.error(f"Erro ao decodificar RIC_CONTROL_ACK: {e}")
            return None

    def handle_failure(self, payload: bytes, node_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Trata o RIC_CONTROL_FAILURE e aciona rollback seguro.
        """
        try:
            parsed = parse_ric_control_failure(payload)
            req_id = parsed["requestor_id"]
            inst_id = parsed["instance_id"]
            cause = parsed.get("cause", 1)
            match = self._find_request(parsed, node_id)
            if not match:
                logger.warning("CORRELATION_ERROR: RIC_CONTROL_FAILURE sem requisição pendente correspondente.")
                return None
            ctrl_id, key = match
            with self._lock:
                info = self.pending_requests.get(ctrl_id)
            if info is not None:
                info["status"] = "FAILED"
                info["cause"] = cause
                try:
                    self.sdl.update_control_result(ctrl_id, "FAILED")
                except Exception as exc:
                    logger.warning("Falha ao persistir falha de controle no SDL", control_request_id=ctrl_id, error=str(exc))
                correlation_id = causal_tracker.correlation_id(
                    info["meid"], info["ran_function_id"], req_id, inst_id
                )
                causal_tracker.record_failure(correlation_id, cause_code=cause)
                logger.error(f"Recebido RIC_CONTROL_FAILURE para req {ctrl_id} (ReqID {req_id}, Cause {cause})")
                with self._lock:
                    self.req_key_to_id.pop(key, None)
                self.allocator.pop_correlation(info["meid"], info["ran_function_id"], req_id, inst_id)
                self.trigger_rollback(ctrl_id)
                return info
            else:
                logger.warning(f"RIC_CONTROL_FAILURE recebido para req não rastreado: {key}")
                return None
        except Exception as e:
            logger.error(f"Erro ao decodificar RIC_CONTROL_FAILURE: {e}")
            return None

    def check_timeouts(self, now: Optional[float] = None) -> List[str]:
        """
        Varre requisições pendentes e dispara rollback seguro para requisições expiradas.
        """
        current_time = now if now is not None else time.time()
        timed_out_ids: List[str] = []
        
        for ctrl_id, info in list(self.pending_requests.items()):
            if info["status"] == "SENT" and current_time >= info["timeout_at"]:
                logger.warning(f"Timeout de controle E2 detectado para {ctrl_id} (ultrapassou {info['timeout_at']})")
                info["status"] = "TIMEOUT"
                timed_out_ids.append(ctrl_id)
                key = (info["meid"], info["ran_function_id"], info["requestor_id"], info["instance_id"])
                with self._lock:
                    self.req_key_to_id.pop(key, None)
                self.allocator.pop_correlation(info["meid"], info["ran_function_id"], info["requestor_id"], info["instance_id"])
                self.trigger_rollback(ctrl_id)
                
        return timed_out_ids

    def trigger_rollback(self, control_request_id: str):
        """
        Solicita rollback somente com valor anterior verificado.
        O envio não é considerado restauração confirmada sem um ACK próprio.
        """
        info = self.pending_requests.get(control_request_id)
        if not info:
            logger.warning(f"Tentativa de rollback para requisição desconhecida: {control_request_id}")
            return

        target_node = info["meid"]
        param = info["parameter"]
        safe_val = info.get("previous_safe_value")
        if safe_val is None:
            info["rollback_status"] = "UNAVAILABLE"
            info["rollback_error"] = "No verified pre-control value is available."
            self._persist_rollback_status(control_request_id, info)
            logger.error(
                "Rollback não enviado: estado anterior real da RAN não está disponível",
                control_request_id=control_request_id,
            )
            return False
        try:
            safe_val = float(safe_val)
        except (TypeError, ValueError):
            info["rollback_status"] = "UNAVAILABLE"
            info["rollback_error"] = "Pre-control value is not numeric."
            self._persist_rollback_status(control_request_id, info)
            logger.error("Rollback rejeitado: valor anterior inválido", control_request_id=control_request_id)
            return False
        if not isfinite(safe_val):
            info["rollback_status"] = "UNAVAILABLE"
            info["rollback_error"] = "Pre-control value is not finite."
            self._persist_rollback_status(control_request_id, info)
            logger.error("Rollback rejeitado: valor anterior não finito", control_request_id=control_request_id)
            return False
        
        logger.warning(
            f"Executando Rollback de Segurança para controle {control_request_id}: "
            f"Restaurando nó {target_node} parâmetro {param} -> {safe_val}"
        )
        
        # Codifica e envia comando de restauração segura
        try:
            ran_fn_id = info["ran_function_id"]
            encoded = self.encoder.encode_control_parts(
                node_id=target_node,
                parameter=param,
                value=safe_val,
                style_type=info["style_type"],
                action_id=info["control_action_id"],
                param_id=info["parameter_id"],
            )
            ctrl_ctx = build_ric_control_request(
                node_id=target_node,
                ran_function_id=ran_fn_id,
                header_bytes=encoded.header_aper,
                message_bytes=encoded.message_aper,
                requestor_id=info["requestor_id"],
                instance_id=info["instance_id"],
                ack_request=0 # Fallback não exige novo ACK para evitar loop de timeout
            )
            if not self.rmr.rmr_send(ctrl_ctx.pdu_aper, RIC_CONTROL_REQ, target_node):
                raise RuntimeError("RMR rejected the rollback request.")
        except Exception as e:
            logger.error(f"Erro ao emitir comando de rollback via RMR: {e}")
            info["rollback_status"] = "SEND_FAILED"
            info["rollback_error"] = str(e)
            self._persist_rollback_status(control_request_id, info)
            return False

        info["rollback_status"] = "SENT_UNCONFIRMED"
        info["rollback_sent_at"] = time.time()
        self._persist_rollback_status(control_request_id, info)
        self.rollback_history.append({
            "control_request_id": control_request_id,
            "node_id": target_node,
            "parameter": param,
            "requested_value": safe_val,
            "status": info["rollback_status"],
            "timestamp": info["rollback_sent_at"]
        })
        return True

    def _persist_rollback_status(self, control_request_id: str, info: Dict[str, Any]) -> None:
        try:
            self.sdl.record_rollback(
                control_request_id,
                status=info["rollback_status"],
                details={
                    "node_id": info.get("meid"),
                    "parameter": info.get("parameter"),
                    "requested_value": info.get("previous_safe_value"),
                    "error": info.get("rollback_error"),
                },
            )
        except Exception as exc:
            logger.error(
                "Falha ao persistir status do rollback",
                control_request_id=control_request_id,
                error=str(exc),
            )
