import time
import uuid
from typing import Dict, Optional
from src.e2.rc_encoder import E2SMRCEncoder, ControlAction
from src.infrastructure.sdl_repository import SdlRepository
from src.conflict_types import RDLDecision as Decision
from src.observability.logging import setup_logger

logger = setup_logger("ControlDispatcher")

class ControlDispatcher:
    def __init__(self, rmr_client, sdl_repo: SdlRepository):
        self.rmr = rmr_client
        self.sdl = sdl_repo
        self.encoder = E2SMRCEncoder()
        
    def dispatch_control(self, decision: Decision):
        if not getattr(decision, "safety_validation", False) or not getattr(decision, "selected_action", None):
            logger.warning(f"Decisão {decision.decision_id} ignorada por falha de safety guard.")
            return

        action_data = decision.selected_action.action
        target_node = getattr(decision, "affected_node", "gnb_01")
        target_cell = getattr(decision, "affected_cell", "cell_01")
        param = action_data.get("parameter", "PRB_QUOTA")
        val = action_data.get("value", 50.0)
        
        encoded = self.encoder.encode_control_parts(node_id=target_node, parameter=param, value=val)
        payload = encoded.pdu_aper
        
        control_request_id = str(uuid.uuid4())
        
        # RF-18: Armazenar tracking
        tracking_info = {
            "control_request_id": control_request_id,
            "request_id": 1,
            "instance_id": 1,
            "ran_function_id": 3, # RC
            "meid": target_node,
            "decision_id": decision.decision_id,
            "sent_at": time.time(),
            "timeout_at": time.time() + 5.0, # Timeout 5s
            "status": "SENT"
        }
        self.sdl.save_control_request(control_request_id, tracking_info)
        
        # Enviar via RMR (Message Type 12010 = RIC_CONTROL_REQUEST)
        logger.info(f"Enviando RIC_CONTROL_REQUEST {control_request_id} para MEID {target_node}")
        self.rmr.rmr_send(payload, 12010, target_node)

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
