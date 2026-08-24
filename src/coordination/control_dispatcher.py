import time
import uuid
from typing import Dict, Optional, Any
from src.e2.rc_encoder import RCEncoder
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
            
            # Enviar via RMR (Message Type 12010 = RIC_CONTROL_REQUEST)
            logger.info(f"Enviando RIC_CONTROL_REQUEST {control_request_id} para MEID {action.node_id}")
            if hasattr(self.rmr, "rmr_send"):
                self.rmr.rmr_send(payload, 12010)
    def handle_ack(self, payload: bytes):
        """
        Trata o RIC_CONTROL_ACK (12011)
        Na prática, extraímos o request_id do payload.
        """
        # Mock de decodificação extraindo ID (usando um estático para exemplo)
        req_id = "simulated_req_id"
        logger.info(f"Recebido RIC_CONTROL_ACK para req {req_id}")
        # Update SDL
        self.sdl.update_control_result(req_id, "ACKNOWLEDGED")

    def handle_failure(self, payload: bytes):
        """
        Trata o RIC_CONTROL_FAILURE (12012)
        """
        req_id = "simulated_req_id"
        logger.error(f"Recebido RIC_CONTROL_FAILURE para req {req_id}")
        self.sdl.update_control_result(req_id, "FAILED")
        self.trigger_rollback(req_id)
        
    def trigger_rollback(self, control_request_id: str):
        logger.warning(f"Executando Rollback para controle {control_request_id}")
        # Lógica de reverter a decisão
