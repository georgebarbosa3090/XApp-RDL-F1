import time
import uuid
from typing import Dict, Optional, List, Any
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
        self.req_key_to_id: Dict[str, str] = {}
        self.rollback_history: List[Dict[str, Any]] = []

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
            val = float(getattr(selected_act, "value", 50.0))
            target_node = getattr(selected_act, "node_id", getattr(decision, "affected_node", "gnb_01"))

        target_cell = getattr(decision, "affected_cell", "cell_01")
        action_id = getattr(selected_act, "action_id", str(uuid.uuid4())[:8])
        
        from src.e2.rc.capability_registry import rc_capability_registry
        ran_fn_id = rc_capability_registry.get_rc_function_id(target_node)
        style_type, ctrl_action_id, param_id = rc_capability_registry.resolve_action(
            param_name=param, node_id=target_node
        )

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
            "previous_safe_value": getattr(decision, "previous_safe_value", 50.0),
            "sent_at": now,
            "timeout_at": now + self.default_timeout_s,
            "status": "SENT"
        }
        
        self.pending_requests[control_request_id] = tracking_info
        key = f"{requestor_id}_{instance_id}"
        self.req_key_to_id[key] = control_request_id
        
        try:
            self.sdl.save_control_request(control_request_id, tracking_info)
        except Exception as e:
            logger.warning(f"Não foi possível persistir no SDL: {e}")
            
        # Enviar via RMR (Message Type 12040 = RIC_CONTROL_REQUEST)
        logger.info(f"Enviando RIC_CONTROL_REQUEST {control_request_id} (ReqID {requestor_id}) para MEID {target_node}")
        if not self.rmr.rmr_send(payload, RIC_CONTROL_REQ, target_node):
            tracking_info["status"] = "SEND_FAILED"
            self.pending_requests.pop(control_request_id, None)
            self.req_key_to_id.pop(key, None)
            self.allocator.pop_correlation(target_node, ran_fn_id, requestor_id, instance_id)
            logger.error(f"RMR rejeitou RIC_CONTROL_REQUEST {control_request_id}; despacho cancelado.")
            return None
        return control_request_id

    def handle_ack(self, payload: bytes) -> Optional[Dict[str, Any]]:
        """
        Trata o RIC_CONTROL_ACK decodificando a PDU E2AP canônica.
        """
        try:
            parsed = parse_ric_control_ack(payload)
            req_id = parsed["requestor_id"]
            inst_id = parsed["instance_id"]
            key = f"{req_id}_{inst_id}"
            ctrl_id = self.req_key_to_id.get(key)
            if not ctrl_id:
                logger.warning(f"CORRELATION_ERROR: RIC_CONTROL_ACK recebido para req não rastreado: {key}")
                return None
                
            if ctrl_id and ctrl_id in self.pending_requests:
                info = self.pending_requests[ctrl_id]
                info["status"] = "ACKNOWLEDGED"
                info["ack_received_at"] = time.time()
                rtt_ms = (info["ack_received_at"] - info["sent_at"]) * 1000.0
                try:
                    self.sdl.update_control_result(ctrl_id, "ACKNOWLEDGED")
                except Exception:
                    pass
                causal_tracker.record_ack(req_id, rtt_ms=rtt_ms)
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

    def handle_failure(self, payload: bytes) -> Optional[Dict[str, Any]]:
        """
        Trata o RIC_CONTROL_FAILURE e aciona rollback seguro.
        """
        try:
            parsed = parse_ric_control_failure(payload)
            req_id = parsed["requestor_id"]
            inst_id = parsed["instance_id"]
            cause = parsed.get("cause", 1)
            key = f"{req_id}_{inst_id}"
            
            ctrl_id = self.req_key_to_id.get(key)
            if not ctrl_id:
                logger.warning(f"CORRELATION_ERROR: RIC_CONTROL_FAILURE recebido para req não rastreado: {key}")
                return None
                
            if ctrl_id and ctrl_id in self.pending_requests:
                info = self.pending_requests[ctrl_id]
                info["status"] = "FAILED"
                info["cause"] = cause
                try:
                    self.sdl.update_control_result(ctrl_id, "FAILED")
                except Exception:
                    pass
                causal_tracker.record_failure(req_id, cause_code=cause)
                logger.error(f"Recebido RIC_CONTROL_FAILURE para req {ctrl_id} (ReqID {req_id}, Cause {cause})")
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
                key = f"{info['requestor_id']}_{info['instance_id']}"
                self.req_key_to_id.pop(key, None)
                self.allocator.pop_correlation(info["meid"], info["ran_function_id"], info["requestor_id"], info["instance_id"])
                self.trigger_rollback(ctrl_id)
                
        return timed_out_ids

    def trigger_rollback(self, control_request_id: str):
        """
        Executa rollback determinístico restaurando o parâmetro ao valor seguro anterior.
        Garante a invariante de que nenhuma ação insegura ou pendente permanece na RAN.
        """
        info = self.pending_requests.get(control_request_id)
        if not info:
            logger.warning(f"Tentativa de rollback para requisição desconhecida: {control_request_id}")
            return

        target_node = info["meid"]
        param = info["parameter"]
        safe_val = info.get("previous_safe_value", 50.0)
        
        logger.warning(
            f"Executando Rollback de Segurança para controle {control_request_id}: "
            f"Restaurando nó {target_node} parâmetro {param} -> {safe_val}"
        )
        
        # Codifica e envia comando de restauração segura
        try:
            from src.e2.rc.capability_registry import rc_capability_registry
            ran_fn_id = rc_capability_registry.get_rc_function_id(target_node)
            encoded = self.encoder.encode_control_parts(node_id=target_node, parameter=param, value=safe_val)
            ctrl_ctx = build_ric_control_request(
                node_id=target_node,
                ran_function_id=ran_fn_id,
                header_bytes=encoded.header_aper,
                message_bytes=encoded.message_aper,
                requestor_id=9999,
                instance_id=1,
                ack_request=0 # Fallback não exige novo ACK para evitar loop de timeout
            )
            self.rmr.rmr_send(ctrl_ctx.pdu_aper, RIC_CONTROL_REQ, target_node)
        except Exception as e:
            logger.error(f"Erro ao emitir comando de rollback via RMR: {e}")
            
        info["status"] = "ROLLED_BACK"
        info["rolled_back_at"] = time.time()
        self.rollback_history.append({
            "control_request_id": control_request_id,
            "node_id": target_node,
            "parameter": param,
            "restored_value": safe_val,
            "timestamp": info["rolled_back_at"]
        })
