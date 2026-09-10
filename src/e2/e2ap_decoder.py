import os
from dataclasses import dataclass
from typing import Optional
from src.observability.logging import setup_logger
from pycrate_asn1rt.asnobj_basic import INT, ENUM
from pycrate_asn1rt.asnobj_str import OCT_STR
from pycrate_asn1rt.asnobj_construct import SEQ, ASN1Dict

logger = setup_logger("E2APDecoder")

@dataclass
class RicIndication:
    request_id: int
    instance_id: int
    ran_function_id: int
    action_id: int
    sn: int
    indication_type: int
    indication_header: bytes
    indication_message: bytes

# Definição estrutural nativa ASN.1 (E2AP - RIC Indication simplificado)
class RICrequestID(SEQ):
    _cont = ASN1Dict([
        ('ricRequestorID', INT()),
        ('ricInstanceID', INT())
    ])
    _root_mand = ['ricRequestorID', 'ricInstanceID']
    _root_opt = []
    _root = ['ricRequestorID', 'ricInstanceID']
    _ext = None

class RICindication(SEQ):
    _cont = ASN1Dict([
        ('ricRequestID', RICrequestID()),
        ('ranFunctionID', INT()),
        ('ricActionID', INT()),
        ('ricIndicationSN', INT()),
        ('ricIndicationType', ENUM(val={0: 'report', 1: 'insert'})),
        ('ricIndicationHeader', OCT_STR()),
        ('ricIndicationMessage', OCT_STR()),
        ('ricCallProcessID', OCT_STR(opt=True))
    ])
    _root_mand = ['ricRequestID', 'ranFunctionID', 'ricActionID', 'ricIndicationSN', 'ricIndicationType', 'ricIndicationHeader', 'ricIndicationMessage']
    _root_opt = ['ricCallProcessID']
    _root = ['ricRequestID', 'ranFunctionID', 'ricActionID', 'ricIndicationSN', 'ricIndicationType', 'ricIndicationHeader', 'ricIndicationMessage', 'ricCallProcessID']
    _ext = None

def decode_e2ap_ric_indication(payload: bytes) -> RicIndication:
    """
    Decodifica estritamente o envelope E2AP (RIC Indication) via APER.
    Lanca excecao em caso de buffer invalido ou corrompido.
    """
    if not payload:
        raise ValueError("Payload E2AP vazio. Esperado buffer binario APER.")
         
    try:
        indication = RICindication()
        indication.from_aper(payload)
        val = indication()
        
        return RicIndication(
            request_id=val['ricRequestID']['ricRequestorID'],
            instance_id=val['ricRequestID']['ricInstanceID'],
            ran_function_id=val['ranFunctionID'],
            action_id=val['ricActionID'],
            sn=val['ricIndicationSN'],
            indication_type=val['ricIndicationType'],
            indication_header=val['ricIndicationHeader'],
            indication_message=val['ricIndicationMessage']
        )
    except Exception as pycrate_err:
        logger.error(f"Falha estrita ao decodificar E2AP RIC Indication via APER: {pycrate_err}")
        raise pycrate_err


