from dataclasses import dataclass, field
import uuid
import time
from typing import Optional, Dict, Any
from pycrate_asn1rt.asnobj_basic import INT, ENUM
from pycrate_asn1rt.asnobj_str import OCT_STR
from pycrate_asn1rt.asnobj_construct import SEQ, ASN1Dict
from src.observability.logging import setup_logger

logger = setup_logger("E2APControl")

# Estrutura ASN.1 E2AP RIC Control Request
class RICrequestID(SEQ):
    _cont = ASN1Dict([
        ('ricRequestorID', INT()),
        ('ricInstanceID', INT())
    ])
    _root_mand = ['ricRequestorID', 'ricInstanceID']
    _root_opt = []
    _root = ['ricRequestorID', 'ricInstanceID']
    _ext = None

class RICcontrolRequest(SEQ):
    _cont = ASN1Dict([
        ('ricRequestID', RICrequestID()),
        ('ranFunctionID', INT()),
        ('ricControlHeader', OCT_STR()),
        ('ricControlMessage', OCT_STR()),
        ('ricControlAckRequest', INT())
    ])
    _root_mand = ['ricRequestID', 'ranFunctionID', 'ricControlHeader', 'ricControlMessage', 'ricControlAckRequest']
    _root_opt = []
    _root = ['ricRequestID', 'ranFunctionID', 'ricControlHeader', 'ricControlMessage', 'ricControlAckRequest']
    _ext = None

class RICcontrolAcknowledge(SEQ):
    _cont = ASN1Dict([
        ('ricRequestID', RICrequestID()),
        ('ranFunctionID', INT())
    ])
    _root_mand = ['ricRequestID', 'ranFunctionID']
    _root_opt = []
    _root = ['ricRequestID', 'ranFunctionID']
    _ext = None

class RICcontrolFailure(SEQ):
    _cont = ASN1Dict([
        ('ricRequestID', RICrequestID()),
        ('ranFunctionID', INT()),
        ('cause', INT())
    ])
    _root_mand = ['ricRequestID', 'ranFunctionID', 'cause']
    _root_opt = []
    _root = ['ricRequestID', 'ranFunctionID', 'cause']
    _ext = None


@dataclass
class ControlContext:
    control_id: str
    requestor_id: int
    instance_id: int
    ran_function_id: int
    node_id: str
    header_bytes: bytes
    message_bytes: bytes
    pdu_aper: bytes
    sent_at: float = field(default_factory=time.time)

def build_ric_control_request(
    node_id: str,
    ran_function_id: int,
    header_bytes: bytes,
    message_bytes: bytes,
    requestor_id: int = 1,
    instance_id: int = 1,
    ack_request: int = 1 # 1 = ack obrigatório
) -> ControlContext:
    """
    Constrói a PDU E2AP normativo RICcontrolRequest contendo o Header e Message do E2SM-RC.
    """
    try:
        ctrl = RICcontrolRequest()
        ctrl.set_val({
            'ricRequestID': {'ricRequestorID': requestor_id, 'ricInstanceID': instance_id},
            'ranFunctionID': int(ran_function_id),
            'ricControlHeader': header_bytes,
            'ricControlMessage': message_bytes,
            'ricControlAckRequest': int(ack_request)
        })



        pdu_aper = ctrl.to_aper()
        ctrl_id = str(uuid.uuid4())[:8]
        
        logger.debug(
            f"E2AP RICcontrolRequest montado (ID {ctrl_id}, {len(pdu_aper)} bytes APER) para {node_id}"
        )
        return ControlContext(
            control_id=ctrl_id,
            requestor_id=requestor_id,
            instance_id=instance_id,
            ran_function_id=ran_function_id,
            node_id=node_id,
            header_bytes=header_bytes,
            message_bytes=message_bytes,
            pdu_aper=pdu_aper
        )
    except Exception as e:
        logger.error(f"Falha ao gerar E2AP RICcontrolRequest: {e}")
        raise

def parse_ric_control_ack(payload: bytes) -> Dict[str, Any]:
    """
    Decodifica resposta de confirmação E2AP RICcontrolAcknowledge recebida via RMR.
    """
    ack = RICcontrolAcknowledge()
    ack.from_aper(payload)
    val = ack()
    return {
        "requestor_id": val['ricRequestID']['ricRequestorID'],
        "instance_id": val['ricRequestID']['ricInstanceID'],
        "ran_function_id": val['ranFunctionID'],
        "status": "ACKNOWLEDGED"
    }

def parse_ric_control_failure(payload: bytes) -> Dict[str, Any]:
    """
    Decodifica resposta de falha E2AP RICcontrolFailure recebida via RMR.
    """
    fail = RICcontrolFailure()
    fail.from_aper(payload)
    val = fail()
    return {
        "requestor_id": val['ricRequestID']['ricRequestorID'],
        "instance_id": val['ricRequestID']['ricInstanceID'],
        "ran_function_id": val['ranFunctionID'],
        "cause": val['cause'],
        "status": "FAILED"
    }
