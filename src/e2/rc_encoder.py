from dataclasses import dataclass
from typing import Dict, Any, Tuple
from src.observability.logging import setup_logger
from pycrate_asn1rt.asnobj_basic import INT
from pycrate_asn1rt.asnobj_construct import SEQ, SEQ_OF, ASN1Dict
from pycrate_asn1rt.asnobj_str import STR_UTF8, OCT_STR

logger = setup_logger("RCEncoder")

# Definição Estrutural Nativa ASN.1 (E2SM-RC v1 - Formato de Controle)
class E2SM_RC_ControlHeader(SEQ):
    _cont = ASN1Dict([
        ('ricControlStyleType', INT()),
        ('ricControlActionID', INT())
    ])
    _root_mand = ['ricControlStyleType', 'ricControlActionID']
    _root_opt = []
    _root = ['ricControlStyleType', 'ricControlActionID']
    _ext = None

class E2SM_RC_ControlMessageItem(SEQ):
    _cont = ASN1Dict([
        ('ranParameterID', INT()),
        ('ranParameterName', STR_UTF8()),
        ('ranParameterValue', INT())
    ])
    _root_mand = ['ranParameterID', 'ranParameterName', 'ranParameterValue']
    _root_opt = []
    _root = ['ranParameterID', 'ranParameterName', 'ranParameterValue']
    _ext = None

class ParamList(SEQ_OF):
    _cont = E2SM_RC_ControlMessageItem()

class E2SM_RC_ControlMessage(SEQ):
    _cont = ASN1Dict([
        ('ricControlActionParameters', ParamList())
    ])
    _root_mand = ['ricControlActionParameters']
    _root_opt = []
    _root = ['ricControlActionParameters']
    _ext = None

class E2SM_RC_ControlPDU(SEQ):
    """Encapsulamento integrado de Header e Message para transmissao E2AP."""
    _cont = ASN1Dict([
        ('ricControlHeader', E2SM_RC_ControlHeader()),
        ('ricControlMessage', E2SM_RC_ControlMessage())
    ])
    _root_mand = ['ricControlHeader', 'ricControlMessage']
    _root_opt = []
    _root = ['ricControlHeader', 'ricControlMessage']
    _ext = None

@dataclass
class EncodedRCControl:
    header_aper: bytes
    message_aper: bytes
    pdu_aper: bytes

class RCEncoder:
    """
    Construtor de payloads APER para a subcamada E2SM-RC (RAN Control).
    Gera o encapsulamento completo do Header e da Mensagem para envio ao E2 Node / NORI.
    Requisito RF-17.
    """
    def __init__(self):
        # Mapeia nomes logicos para IDs da RAN 3GPP/O-RAN
        self.param_map = {
            "PRB_QUOTA": 1,
            "SCHEDULER_WEIGHT": 2,
            "TX_POWER": 3,
            "HANDOVER": 4
        }

    def encode_control_parts(self, node_id: str, parameter: str, value: float, style_type: int = 1, action_id: int = 1) -> EncodedRCControl:
        """
        Gera as partes separadas (Header e Message) e a PDU unificada encodada em APER.
        """
        param_id = self.param_map.get(parameter, 99)
        
        # 1. Header
        header = E2SM_RC_ControlHeader()
        header.set_val({'ricControlStyleType': style_type, 'ricControlActionID': action_id})
        header_aper = header.to_aper()

        # 2. Message
        msg = E2SM_RC_ControlMessage()
        msg.set_val({'ricControlActionParameters': [
            {
                'ranParameterID': param_id,
                'ranParameterName': parameter,
                'ranParameterValue': int(value)
            }
        ]})
        msg_aper = msg.to_aper()

        # 3. PDU Integrada (Header + Message)
        pdu = E2SM_RC_ControlPDU()
        pdu.set_val({
            'ricControlHeader': {'ricControlStyleType': style_type, 'ricControlActionID': action_id},
            'ricControlMessage': {'ricControlActionParameters': [
                {
                    'ranParameterID': param_id,
                    'ranParameterName': parameter,
                    'ranParameterValue': int(value)
                }
            ]}
        })
        pdu_aper = pdu.to_aper()

        logger.debug(
            f"RC Control Encoded - Header: {len(header_aper)}B, "
            f"Msg: {len(msg_aper)}B, PDU: {len(pdu_aper)}B"
        )
        return EncodedRCControl(header_aper=header_aper, message_aper=msg_aper, pdu_aper=pdu_aper)

    def encode_control_request(self, node_id: str, parameter: str, value: float) -> bytes:
        """
        Gera o payload binario APER completo da PDU de controle para envio via E2 / RMR.
        """
        try:
            encoded = self.encode_control_parts(node_id, parameter, value)
            return encoded.pdu_aper
        except Exception as e:
            logger.error(f"Erro Critico ao encodar E2SM-RC via APER: {e}")
            raise

