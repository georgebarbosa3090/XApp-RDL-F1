"""
Estrutura Canônica e Codec ASN.1 APER da E2AP-PDU (O-RAN.WG3.E2AP v02.03)
Implementação rigorosa da PDU de topo E2AP encapsulando InitiatingMessage, SuccessfulOutcome e UnsuccessfulOutcome.
"""

from typing import Dict, Any, Tuple, Optional
from pycrate_asn1rt.asnobj_basic import INT
from pycrate_asn1rt.asnobj_str import OCT_STR
from pycrate_asn1rt.asnobj_construct import SEQ, ASN1Dict
from src.e2.e2ap.constants import (
    PROC_RIC_CONTROL,
    PROC_RIC_SUBSCRIPTION,
    PROC_RIC_INDICATION,
    CRITICALITY_IGNORE,
    CRITICALITY_REJECT
)
from src.observability.logging import setup_logger

logger = setup_logger("E2AP_PDU")

class InitiatingMessage(SEQ):
    _cont = ASN1Dict([
        ('procedureCode', INT()),
        ('criticality', INT()),
        ('value', OCT_STR())
    ])
    _root_mand = ['procedureCode', 'criticality', 'value']
    _root_opt = []
    _root = ['procedureCode', 'criticality', 'value']
    _ext = None

class SuccessfulOutcome(SEQ):
    _cont = ASN1Dict([
        ('procedureCode', INT()),
        ('criticality', INT()),
        ('value', OCT_STR())
    ])
    _root_mand = ['procedureCode', 'criticality', 'value']
    _root_opt = []
    _root = ['procedureCode', 'criticality', 'value']
    _ext = None

class UnsuccessfulOutcome(SEQ):
    _cont = ASN1Dict([
        ('procedureCode', INT()),
        ('criticality', INT()),
        ('value', OCT_STR())
    ])
    _root_mand = ['procedureCode', 'criticality', 'value']
    _root_opt = []
    _root = ['procedureCode', 'criticality', 'value']
    _ext = None

class E2AP_PDU(SEQ):
    _cont = ASN1Dict([
        ('initiatingMessage', InitiatingMessage(opt=True)),
        ('successfulOutcome', SuccessfulOutcome(opt=True)),
        ('unsuccessfulOutcome', UnsuccessfulOutcome(opt=True))
    ])
    _root_mand = []
    _root_opt = ['initiatingMessage', 'successfulOutcome', 'unsuccessfulOutcome']
    _root = ['initiatingMessage', 'successfulOutcome', 'unsuccessfulOutcome']
    _ext = None

def wrap_initiating_message(procedure_code: int, value_bytes: bytes, criticality: int = CRITICALITY_IGNORE) -> bytes:
    """
    Encapsula uma carga útil (ex: RICcontrolRequest, RICsubscriptionRequest) em uma E2AP-PDU do tipo InitiatingMessage.
    """
    pdu = E2AP_PDU()
    pdu.set_val({
        'initiatingMessage': {
            'procedureCode': int(procedure_code),
            'criticality': int(criticality),
            'value': value_bytes
        }
    })
    return pdu.to_aper()

def wrap_successful_outcome(procedure_code: int, value_bytes: bytes, criticality: int = CRITICALITY_IGNORE) -> bytes:
    """
    Encapsula uma confirmação de procedimento (ex: RICcontrolAcknowledge, RICsubscriptionResponse) em uma E2AP-PDU.
    """
    pdu = E2AP_PDU()
    pdu.set_val({
        'successfulOutcome': {
            'procedureCode': int(procedure_code),
            'criticality': int(criticality),
            'value': value_bytes
        }
    })
    return pdu.to_aper()

def wrap_unsuccessful_outcome(procedure_code: int, value_bytes: bytes, criticality: int = CRITICALITY_REJECT) -> bytes:
    """
    Encapsula uma falha de procedimento (ex: RICcontrolFailure, RICsubscriptionFailure) em uma E2AP-PDU.
    """
    pdu = E2AP_PDU()
    pdu.set_val({
        'unsuccessfulOutcome': {
            'procedureCode': int(procedure_code),
            'criticality': int(criticality),
            'value': value_bytes
        }
    })
    return pdu.to_aper()

def unwrap_e2ap_pdu(payload_bytes: bytes) -> Tuple[str, int, int, bytes]:
    """
    Desempacota a E2AP-PDU retornando (pdu_type, procedure_code, criticality, inner_value_bytes).
    """
    pdu = E2AP_PDU()
    pdu.from_aper(payload_bytes)
    val = pdu()
    if val.get('initiatingMessage'):
        msg = val['initiatingMessage']
        return ('initiatingMessage', msg['procedureCode'], msg['criticality'], msg['value'])
    elif val.get('successfulOutcome'):
        msg = val['successfulOutcome']
        return ('successfulOutcome', msg['procedureCode'], msg['criticality'], msg['value'])
    elif val.get('unsuccessfulOutcome'):
        msg = val['unsuccessfulOutcome']
        return ('unsuccessfulOutcome', msg['procedureCode'], msg['criticality'], msg['value'])
    raise ValueError("E2AP-PDU recebida sem mensagem válida")
