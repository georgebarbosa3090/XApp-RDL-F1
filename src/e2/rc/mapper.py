from typing import List, Optional
from src.conflict_types import XAppAction, RDLDecision
from src.e2.rc.control_parameter import validate_ran_parameter
from src.e2.rc_encoder import RCEncoder, EncodedRCControl
from src.e2.e2ap.control import build_ric_control_request, ControlContext
from src.observability.logging import setup_logger

logger = setup_logger("RCMapper")

class RCMapper:
    """
    Camada de Mapeamento Formal:
    RDL Decision / Action -> RC Control Action -> RAN Parameter ID -> E2SM-RC ASN.1 APER -> E2AP RICcontrolRequest
    """
    def __init__(self, ran_function_id: int = 3):
        self.ran_function_id = ran_function_id
        self.encoder = RCEncoder()

    def map_action_to_control_request(
        self,
        action: XAppAction,
        requestor_id: int = 1,
        instance_id: int = 1
    ) -> ControlContext:
        """
        Converte uma XAppAction individual aprovada pelo Safety Guard em uma PDU E2AP RICcontrolRequest completa.
        """
        is_valid, param_id, reason = validate_ran_parameter(action.parameter, action.value)
        if not is_valid:
            raise ValueError(f"Ação rejeitada no mapeamento E2SM-RC: {reason}")

        # Gera Header e Message APER
        encoded_rc = self.encoder.encode_control_parts(
            node_id=action.node_id,
            parameter=action.parameter,
            value=action.value,
            style_type=1,
            action_id=1
        )

        # Encapsula na PDU E2AP RICcontrolRequest
        control_ctx = build_ric_control_request(
            node_id=action.node_id,
            ran_function_id=self.ran_function_id,
            header_bytes=encoded_rc.header_aper,
            message_bytes=encoded_rc.message_aper,
            requestor_id=requestor_id,
            instance_id=instance_id,
            ack_request=1
        )
        return control_ctx

    def map_decision_to_control_requests(
        self,
        decision: RDLDecision,
        requestor_id: int = 1,
        instance_id: int = 1
    ) -> List[ControlContext]:
        """
        Converte todas as ações selecionadas de uma RDLDecision em mensagens E2AP de controle prontas para envio.
        """
        contexts: List[ControlContext] = []
        for act in decision.selected_actions:
            try:
                ctx = self.map_action_to_control_request(act, requestor_id, instance_id)
                contexts.append(ctx)
            except Exception as e:
                logger.error(f"Erro ao mapear ação {act.parameter} da decisão {decision.decision_id}: {e}")
        return contexts
