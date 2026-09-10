"""
Estrutura Canônica e Codec ASN.1 APER da E2AP-PDU (O-RAN.WG3.E2AP v02.03)
Implementação rigorosa da PDU de topo E2AP encapsulando InitiatingMessage, SuccessfulOutcome e UnsuccessfulOutcome como ASN.1 CHOICE oficial.
"""

from typing import Dict, Any, Tuple, Optional
from src.e2.e2ap.canonical_asn import E2AP_Canonical_Module
from src.e2.e2ap.constants import (
    PROC_RIC_CONTROL,
    PROC_RIC_SUBSCRIPTION,
    PROC_RIC_INDICATION,
    CRITICALITY_IGNORE,
    CRITICALITY_REJECT,
    CRITICALITY_NOTIFY
)
from src.observability.logging import setup_logger

logger = setup_logger("E2AP_PDU")

# Aliases diretos para as classes canônicas do módulo compilado
InitiatingMessage = E2AP_Canonical_Module.InitiatingMessage
SuccessfulOutcome = E2AP_Canonical_Module.SuccessfulOutcome
UnsuccessfulOutcome = E2AP_Canonical_Module.UnsuccessfulOutcome
E2AP_PDU = E2AP_Canonical_Module.E2AP_PDU

_CRIT_MAP = {
    0: 'reject',
    1: 'ignore',
    2: 'notify',
    'reject': 'reject',
    'ignore': 'ignore',
    'notify': 'notify'
}

_REV_CRIT_MAP = {
    'reject': 0,
    'ignore': 1,
    'notify': 2
}

def wrap_initiating_message(procedure_code: int, value_bytes: bytes, criticality: int = CRITICALITY_IGNORE) -> bytes:
    """
    Encapsula uma carga útil (ex: RICcontrolRequest, RICsubscriptionRequest) em uma E2AP-PDU do tipo InitiatingMessage (CHOICE).
    """
    crit_str = _CRIT_MAP.get(criticality, 'ignore')
    pdu = E2AP_PDU
    pdu.set_val(('initiatingMessage', {
        'procedureCode': int(procedure_code),
        'criticality': crit_str,
        'value': value_bytes
    }))
    return pdu.to_aper()

def wrap_successful_outcome(procedure_code: int, value_bytes: bytes, criticality: int = CRITICALITY_IGNORE) -> bytes:
    """
    Encapsula uma confirmação de procedimento (ex: RICcontrolAcknowledge, RICsubscriptionResponse) em uma E2AP-PDU (CHOICE).
    """
    crit_str = _CRIT_MAP.get(criticality, 'ignore')
    pdu = E2AP_PDU
    pdu.set_val(('successfulOutcome', {
        'procedureCode': int(procedure_code),
        'criticality': crit_str,
        'value': value_bytes
    }))
    return pdu.to_aper()

def wrap_unsuccessful_outcome(procedure_code: int, value_bytes: bytes, criticality: int = CRITICALITY_REJECT) -> bytes:
    """
    Encapsula uma falha de procedimento (ex: RICcontrolFailure, RICsubscriptionFailure) em uma E2AP-PDU (CHOICE).
    """
    crit_str = _CRIT_MAP.get(criticality, 'reject')
    pdu = E2AP_PDU
    pdu.set_val(('unsuccessfulOutcome', {
        'procedureCode': int(procedure_code),
        'criticality': crit_str,
        'value': value_bytes
    }))
    return pdu.to_aper()

def unwrap_e2ap_pdu(payload_bytes: bytes) -> Tuple[str, int, int, bytes]:
    """
    Desempacota a E2AP-PDU retornando (pdu_type, procedure_code, criticality, inner_value_bytes).
    """
    pdu = E2AP_PDU
    pdu.from_aper(payload_bytes)
    val = pdu()
    
    if isinstance(val, tuple) and len(val) == 2:
        msg_type, msg_val = val
        crit_num = _REV_CRIT_MAP.get(msg_val['criticality'], 1)
        return (msg_type, int(msg_val['procedureCode']), crit_num, msg_val['value'])
    elif isinstance(val, dict):
        for msg_type in ['initiatingMessage', 'successfulOutcome', 'unsuccessfulOutcome']:
            if msg_type in val and val[msg_type]:
                msg_val = val[msg_type]
                crit_num = _REV_CRIT_MAP.get(msg_val.get('criticality', 'ignore'), 1)
                return (msg_type, int(msg_val['procedureCode']), crit_num, msg_val['value'])

    raise ValueError(f"E2AP-PDU inválida ou vazia: {val}")
