import time
import uuid
from typing import Dict, Optional, Any
from src.e2.rc_encoder import RCEncoder
from src.e2.e2ap.constants import RIC_CONTROL_REQ, RIC_CONTROL_ACK, RIC_CONTROL_FAILURE
from src.e2.e2ap.control import parse_ric_control_ack, parse_ric_control_failure
from src.infrastructure.sdl_repository import SdlRepository
from src.conflict_types import ResolutionAction, XAppAction
from src.observability.logging import setup_logger

logger = setup_logger("ControlDispatcher")

class ControlDispatcher:
    def __init__(self, rmr_client: Any, sdl_repo: SdlRepository):
        self.rmr = rmr_client
        self.sdl = sdl_repo
        self.encoder = RCEncoder()
        
    def dispatch_control(self, resolution: ResolutionAction, target_node: str = "gnb_01"):
        if not resolution.winning_actions:
            logger.warning(f"Resolução {resolution.conflict_id} ignorada por ausência de ações.")
            return

        for action in resolution.winning_actions:
            payload = self.encoder.encode_control_request(action.node_id, action.parameter, action.value)
            control_request_id = str(uuid.uuid4())
            
            # RF-18: Armazenar tracking
            tracking_info = {
                "control_request_id": control_request_id,
                "request_id": 1,
                "instance_id": 1,
                "ran_function_id": 3, # RC
                "meid": action.node_id,
                "conflict_id": resolution.conflict_id,
                "sent_at": time.time(),
                "timeout_at": time.time() + 5.0, # Timeout 5s
                "status": "SENT"
            }
            self.sdl.save_control_request(control_request_id, tracking_info)
            
            # Enviar via RMR (Message Type 12040 = RIC_CONTROL_REQ)
            logger.info(f"Enviando RIC_CONTROL_REQ (mtype={RIC_CONTROL_REQ}) {control_request_id} para MEID {action.node_id}")
            if hasattr(self.rmr, "rmr_send"):
                self.rmr.rmr_send(payload, RIC_CONTROL_REQ)

    def handle_ack(self, payload: bytes):
        """
        Trata o RIC_CONTROL_ACK (12041) extraindo o control_request_id real do payload (JSON ou APER).
        """
        req_id = ""
        if payload:
            try:
                parsed = parse_ric_control_ack(payload)
                req_id = str(parsed.get("requestor_id", ""))
            except Exception:
                pass
            if not req_id:
                try:
                    import json
                    data = json.loads(payload.decode('utf-8'))
                    req_id = data.get("transaction_id") or data.get("control_request_id", "")
                except Exception:
                    req_id = payload.hex()[:8]
        if req_id:
            logger.info(f"Recebido RIC_CONTROL_ACK (12041) para req {req_id}")
            self.sdl.update_control_result(req_id, "ACKNOWLEDGED")

    def handle_failure(self, payload: bytes):
        """
        Trata o RIC_CONTROL_FAILURE (12042) extraindo o control_request_id e causa do erro.
        """
        req_id = ""
        cause = 1
        if payload:
            try:
                parsed = parse_ric_control_failure(payload)
                req_id = str(parsed.get("requestor_id", ""))
                cause = parsed.get("cause", 1)
            except Exception:
                pass
            if not req_id:
                try:
                    import json
                    data = json.loads(payload.decode('utf-8'))
                    req_id = data.get("transaction_id") or data.get("control_request_id", "")
                    cause = data.get("cause", 1)
                except Exception:
                    req_id = payload.hex()[:8]
        if req_id:
            logger.error(f"Recebido RIC_CONTROL_FAILURE (12042) para req {req_id} (Cause: {cause})")
            self.sdl.update_control_result(req_id, "FAILED")
            self.trigger_rollback(req_id)

    def trigger_rollback(self, control_request_id: str):
        logger.warning(f"Executando Rollback/Compensação para controle {control_request_id}")
        # Lógica de reverter a decisão ou restabelecer ponto de operação seguro
        if hasattr(self.sdl, "record_rollback"):
            self.sdl.record_rollback(control_request_id)

