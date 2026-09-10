"""
Estrutura Canônica e Codec ASN.1 APER do E2AP RIC Control (O-RAN.WG3.E2AP v02.03)
Implementação com ProtocolIE-Container (SEQUENCE OF ProtocolIE-Field) e ProtocolIE-IDs normativos.
"""

from dataclasses import dataclass, field
import uuid
import time
from typing import Optional, Dict, Any, List, Union

from src.e2.e2ap.canonical_asn import E2AP_Canonical_Module
from src.e2.e2ap.constants import (
    PROC_RIC_CONTROL,
    CRITICALITY_REJECT,
    CRITICALITY_IGNORE,
    IE_RIC_REQUEST_ID,
    IE_RAN_FUNCTION_ID,
    IE_RIC_CONTROL_HEADER,
    IE_RIC_CONTROL_MESSAGE,
    IE_RIC_CONTROL_ACK_REQUEST,
    IE_RIC_CONTROL_OUTCOME,
    IE_CAUSE
)
from src.e2.e2ap.pdu import wrap_initiating_message, wrap_successful_outcome, wrap_unsuccessful_outcome, unwrap_e2ap_pdu
from src.observability.logging import setup_logger

logger = setup_logger("E2APControl")

class RICrequestID:
    def __init__(self):
        self._obj = E2AP_Canonical_Module.RICrequestID
    def set_val(self, val: Dict[str, Any]):
        self._obj.set_val(val)
    def to_aper(self) -> bytes:
        return self._obj.to_aper()
    def from_aper(self, char: bytes):
        self._obj.from_aper(char)
    def __call__(self) -> Dict[str, Any]:
        return self._obj()

class RICcontrolRequest:
    def __init__(self):
        self._obj = E2AP_Canonical_Module.RICcontrolRequest

    def set_val(self, val: Dict[str, Any]):
        # Se for passado no formato simplificado (compatibilidade), encapsula no ProtocolIE-Container
        if 'protocolIEs' in val:
            self._obj.set_val(val)
        else:
            req_id = E2AP_Canonical_Module.RICrequestID
            req_id_val = val.get('ricRequestID', {'ricRequestorID': 1, 'ricInstanceID': 1})
            req_id.set_val(req_id_val)
            req_id_bytes = req_id.to_aper()

            func_id = E2AP_Canonical_Module.RANfunctionID
            func_id.set_val(int(val.get('ranFunctionID', 1)))
            func_id_bytes = func_id.to_aper()

            ack_req = E2AP_Canonical_Module.RICcontrolAckRequest
            ack_val = val.get('ricControlAckRequest', 1)
            ack_enum = 'ack' if ack_val == 1 else ('nAck' if ack_val == 2 else 'noAck')
            ack_req.set_val(ack_enum)
            ack_bytes = ack_req.to_aper()

            header_bytes = val.get('ricControlHeader', b'')
            message_bytes = val.get('ricControlMessage', b'')

            self._obj.set_val({
                'protocolIEs': [
                    {'id': IE_RIC_REQUEST_ID, 'criticality': 'reject', 'value': req_id_bytes},
                    {'id': IE_RAN_FUNCTION_ID, 'criticality': 'reject', 'value': func_id_bytes},
                    {'id': IE_RIC_CONTROL_HEADER, 'criticality': 'reject', 'value': header_bytes},
                    {'id': IE_RIC_CONTROL_MESSAGE, 'criticality': 'reject', 'value': message_bytes},
                    {'id': IE_RIC_CONTROL_ACK_REQUEST, 'criticality': 'reject', 'value': ack_bytes}
                ]
            })

    def to_aper(self) -> bytes:
        return self._obj.to_aper()

    def from_aper(self, char: bytes):
        self._obj.from_aper(char)

    def __call__(self) -> Dict[str, Any]:
        val = self._obj()
        # Converte ProtocolIEs para visão canônica estruturada
        res = {
            'protocolIEs': val.get('protocolIEs', []),
            'ricRequestID': {'ricRequestorID': 1, 'ricInstanceID': 1},
            'ranFunctionID': 1,
            'ricControlHeader': b'',
            'ricControlMessage': b'',
            'ricControlAckRequest': 1
        }
        for ie in val.get('protocolIEs', []):
            ie_id = ie['id']
            ie_bytes = ie['value']
            if ie_id == IE_RIC_REQUEST_ID:
                r = E2AP_Canonical_Module.RICrequestID
                r.from_aper(ie_bytes)
                res['ricRequestID'] = r()
            elif ie_id == IE_RAN_FUNCTION_ID:
                f = E2AP_Canonical_Module.RANfunctionID
                f.from_aper(ie_bytes)
                res['ranFunctionID'] = f()
            elif ie_id == IE_RIC_CONTROL_HEADER:
                res['ricControlHeader'] = ie_bytes
            elif ie_id == IE_RIC_CONTROL_MESSAGE:
                res['ricControlMessage'] = ie_bytes
            elif ie_id == IE_RIC_CONTROL_ACK_REQUEST:
                a = E2AP_Canonical_Module.RICcontrolAckRequest
                a.from_aper(ie_bytes)
                ack_name = a()
                res['ricControlAckRequest'] = 1 if ack_name == 'ack' else (2 if ack_name == 'nAck' else 0)
        return res

class RICcontrolAcknowledge:
    def __init__(self):
        self._obj = E2AP_Canonical_Module.RICcontrolAcknowledge

    def set_val(self, val: Dict[str, Any]):
        if 'protocolIEs' in val:
            self._obj.set_val(val)
        else:
            req_id = E2AP_Canonical_Module.RICrequestID
            req_id_val = val.get('ricRequestID', {'ricRequestorID': 1, 'ricInstanceID': 1})
            req_id.set_val(req_id_val)
            req_id_bytes = req_id.to_aper()

            func_id = E2AP_Canonical_Module.RANfunctionID
            func_id.set_val(int(val.get('ranFunctionID', 1)))
            func_id_bytes = func_id.to_aper()

            outcome_bytes = val.get('ricControlOutcome', b'')

            ies = [
                {'id': IE_RIC_REQUEST_ID, 'criticality': 'reject', 'value': req_id_bytes},
                {'id': IE_RAN_FUNCTION_ID, 'criticality': 'reject', 'value': func_id_bytes}
            ]
            if outcome_bytes:
                ies.append({'id': IE_RIC_CONTROL_OUTCOME, 'criticality': 'ignore', 'value': outcome_bytes})

            self._obj.set_val({'protocolIEs': ies})

    def to_aper(self) -> bytes:
        return self._obj.to_aper()

    def from_aper(self, char: bytes):
        self._obj.from_aper(char)

    def __call__(self) -> Dict[str, Any]:
        val = self._obj()
        res = {
            'protocolIEs': val.get('protocolIEs', []),
            'ricRequestID': {'ricRequestorID': 1, 'ricInstanceID': 1},
            'ranFunctionID': 1,
            'ricControlOutcome': b''
        }
        for ie in val.get('protocolIEs', []):
            ie_id = ie['id']
            ie_bytes = ie['value']
            if ie_id == IE_RIC_REQUEST_ID:
                r = E2AP_Canonical_Module.RICrequestID
                r.from_aper(ie_bytes)
                res['ricRequestID'] = r()
            elif ie_id == IE_RAN_FUNCTION_ID:
                f = E2AP_Canonical_Module.RANfunctionID
                f.from_aper(ie_bytes)
                res['ranFunctionID'] = f()
            elif ie_id == IE_RIC_CONTROL_OUTCOME:
                res['ricControlOutcome'] = ie_bytes
        return res

class RICcontrolFailure:
    def __init__(self):
        self._obj = E2AP_Canonical_Module.RICcontrolFailure

    def set_val(self, val: Dict[str, Any]):
        if 'protocolIEs' in val:
            self._obj.set_val(val)
        else:
            req_id = E2AP_Canonical_Module.RICrequestID
            req_id_val = val.get('ricRequestID', {'ricRequestorID': 1, 'ricInstanceID': 1})
            req_id.set_val(req_id_val)
            req_id_bytes = req_id.to_aper()

            func_id = E2AP_Canonical_Module.RANfunctionID
            func_id.set_val(int(val.get('ranFunctionID', 1)))
            func_id_bytes = func_id.to_aper()

            cause_val = val.get('cause', 1)

            ies = [
                {'id': IE_RIC_REQUEST_ID, 'criticality': 'reject', 'value': req_id_bytes},
                {'id': IE_RAN_FUNCTION_ID, 'criticality': 'reject', 'value': func_id_bytes}
            ]
            self._obj.set_val({'protocolIEs': ies, 'cause': cause_val})

    def to_aper(self) -> bytes:
        return self._obj.to_aper()

    def from_aper(self, char: bytes):
        self._obj.from_aper(char)

    def __call__(self) -> Dict[str, Any]:
        val = self._obj()
        res = {
            'protocolIEs': val.get('protocolIEs', []),
            'ricRequestID': {'ricRequestorID': 1, 'ricInstanceID': 1},
            'ranFunctionID': 1,
            'cause': val.get('cause', 1)
        }
        for ie in val.get('protocolIEs', []):
            ie_id = ie['id']
            ie_bytes = ie['value']
            if ie_id == IE_RIC_REQUEST_ID:
                r = E2AP_Canonical_Module.RICrequestID
                r.from_aper(ie_bytes)
                res['ricRequestID'] = r()
            elif ie_id == IE_RAN_FUNCTION_ID:
                f = E2AP_Canonical_Module.RANfunctionID
                f.from_aper(ie_bytes)
                res['ranFunctionID'] = f()
        return res

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
    Constrói a PDU E2AP normativa completa com ProtocolIE-Container:
    E2AP-PDU -> InitiatingMessage (id-RICcontrol = 4) -> RICcontrolRequest -> protocolIEs
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

        ctrl_bytes = ctrl.to_aper()
        # Encapsula na E2AP-PDU canônica InitiatingMessage com procedureCode = id-RICcontrol (4)
        pdu_aper = wrap_initiating_message(PROC_RIC_CONTROL, ctrl_bytes, criticality=CRITICALITY_IGNORE)
        ctrl_id = str(uuid.uuid4())[:8]
        
        logger.debug(
            f"E2AP-PDU RICcontrolRequest montada com ProtocolIE-Container (ID {ctrl_id}, {len(pdu_aper)} bytes APER) para {node_id}"
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
        logger.error(f"Falha ao gerar E2AP RICcontrolRequest canônica: {e}")
        raise

def parse_ric_control_ack(payload: bytes) -> Dict[str, Any]:
    """
    Decodifica resposta de confirmação E2AP RICcontrolAcknowledge contendo ProtocolIE-Container.
    """
    target_bytes = payload
    try:
        pdu_type, proc_code, crit, inner = unwrap_e2ap_pdu(payload)
        target_bytes = inner
    except Exception:
        target_bytes = payload

    ack = RICcontrolAcknowledge()
    ack.from_aper(target_bytes)
    val = ack()
    
    return {
        "requestor_id": val['ricRequestID']['ricRequestorID'],
        "instance_id": val['ricRequestID']['ricInstanceID'],
        "ran_function_id": val['ranFunctionID'],
        "outcome": val.get('ricControlOutcome', b''),
        "status": "ACKNOWLEDGED"
    }

def parse_ric_control_failure(payload: bytes) -> Dict[str, Any]:
    """
    Decodifica resposta de falha E2AP RICcontrolFailure contendo ProtocolIE-Container.
    """
    target_bytes = payload
    try:
        pdu_type, proc_code, crit, inner = unwrap_e2ap_pdu(payload)
        target_bytes = inner
    except Exception:
        target_bytes = payload

    fail = RICcontrolFailure()
    fail.from_aper(target_bytes)
    val = fail()
    
    return {
        "requestor_id": val['ricRequestID']['ricRequestorID'],
        "instance_id": val['ricRequestID']['ricInstanceID'],
        "ran_function_id": val['ranFunctionID'],
        "cause": val.get('cause', 1),
        "status": "FAILED"
    }
