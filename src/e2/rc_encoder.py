from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional
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

# Dicionário Sistemático de Perfis de Parâmetros E2SM-RC (O-RAN.WG3.TS.E2SM-RC v01.00)
PARAM_PROFILES = {
    "PRB_QUOTA":          {"id": 1,  "scale": 1,    "unit": "PRB",         "min": 0,    "max": 100},
    "TX_POWER":           {"id": 2,  "scale": 10,   "unit": "dBm_x10",     "min": -100, "max": 430},
    "SCHEDULER_WEIGHT":   {"id": 3,  "scale": 1000, "unit": "milli_ratio", "min": 10,   "max": 10000},
    "A3_OFFSET":          {"id": 4,  "scale": 100,  "unit": "centi_dB",    "min": -1000,"max": 1000},
    "HANDOVER":           {"id": 5,  "scale": 1,    "unit": "cell_id",     "min": 0,    "max": 65535},
    "BEAM_DOWNTILT":      {"id": 10, "scale": 10,   "unit": "deg_x10",     "min": 0,    "max": 150},
    "ISAC_SENSING_RATIO": {"id": 11, "scale": 1000, "unit": "milli_ratio", "min": 0,    "max": 500},
    "CARRIER_AGG_RATIO":  {"id": 12, "scale": 1000, "unit": "milli_ratio", "min": 0,    "max": 1000}
}

RAN_PARAMETERS = PARAM_PROFILES

class RCEncoder:
    """
    Construtor de payloads APER para a subcamada E2SM-RC (RAN Control).
    """
    def __init__(self):
        self.profiles = PARAM_PROFILES

    def encode_control_parts(self, node_id: str, parameter: str, value: float, style_type: int = 1, action_id: int = 1) -> EncodedRCControl:
        header_aper, msg_aper = self.encode_control_pdu(node_id, parameter, value, style_type, action_id)
        
        profile = self.profiles[parameter]
        scale = profile["scale"]
        encoded_val = int(round(float(value) * scale))

        pdu = E2SM_RC_ControlPDU()
        pdu.set_val({
            'ricControlHeader': {'ricControlStyleType': style_type, 'ricControlActionID': action_id},
            'ricControlMessage': {'ricControlActionParameters': [
                {
                    'ranParameterID': profile["id"],
                    'ranParameterName': parameter,
                    'ranParameterValue': encoded_val
                }
            ]}
        })
        pdu_aper = pdu.to_aper()
        return EncodedRCControl(header_aper=header_aper, message_aper=msg_aper, pdu_aper=pdu_aper)

    def encode_control_pdu(self, node_id: str, parameter: str, value: float, style_type: int = 1, action_id: int = 1) -> Tuple[bytes, bytes]:
        if parameter not in self.profiles:
            raise ValueError(f"Parâmetro E2SM-RC não suportado ou desconhecido: '{parameter}'")
            
        profile = self.profiles[parameter]
        param_id = profile["id"]
        scale = profile["scale"]
        encoded_val = int(round(float(value) * scale))
        
        if encoded_val < profile["min"] or encoded_val > profile["max"]:
            raise ValueError(
                f"Valor fora dos limites para {parameter}: {value} (codificado: {encoded_val}, permitido: [{profile['min']}, {profile['max']}])"
            )

        header = E2SM_RC_ControlHeader()
        header.set_val({'ricControlStyleType': style_type, 'ricControlActionID': action_id})
        header_aper = header.to_aper()

        msg = E2SM_RC_ControlMessage()
        msg.set_val({'ricControlActionParameters': [
            {
                'ranParameterID': param_id,
                'ranParameterName': parameter,
                'ranParameterValue': encoded_val
            }
        ]})
        msg_aper = msg.to_aper()
        return header_aper, msg_aper

    def encode_control_request(self, node_id: str, parameter: str, value: float) -> bytes:
        _, msg_aper = self.encode_control_pdu(node_id, parameter, value)
        return msg_aper

    def decode_control_header(self, header_aper: bytes) -> Dict[str, Any]:
        header = E2SM_RC_ControlHeader()
        header.from_aper(header_aper)
        return header.get_val()

    def decode_control_message(self, msg_aper: bytes) -> Dict[str, Any]:
        msg = E2SM_RC_ControlMessage()
        msg.from_aper(msg_aper)
        return msg.get_val()

    def decode_control_request(self, msg_aper: bytes, parameter: str) -> float:
        val_dict = self.decode_control_message(msg_aper)
        raw_int = val_dict['ricControlActionParameters'][0]['ranParameterValue']
        profile = self.profiles.get(parameter, {"scale": 1})
        scale = profile["scale"]
        return float(raw_int) / float(scale)


