from src.observability.logging import setup_logger
from pycrate_asn1rt.asnobj_basic import INT
from pycrate_asn1rt.asnobj_construct import SEQ, SEQ_OF, ASN1Dict
from pycrate_asn1rt.asnobj_str import STR_UTF8, OCT_STR

logger = setup_logger("RCEncoder")

# Definição Estrutural Nativa ASN.1 (E2SM-RC v1)
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

class RCEncoder:
    """
    Construtor de payloads APER para a subcamada E2SM-RC (RAN Control).
    Requisito RF-17.
    """
    def __init__(self):
        # Mapeia nomes lógicos para IDs da RAN
        self.param_map = {
            "PRB_QUOTA": 1,
            "SCHEDULER_WEIGHT": 2,
            "TX_POWER": 3
        }

    def encode_control_request(self, node_id: str, parameter: str, value: float) -> bytes:
        """
        Gera a string de bytes APER pura que o E2 Node espera.
        """
        try:
            param_id = self.param_map.get(parameter, 99)
            
            # Constrói o Header
            header = E2SM_RC_ControlHeader()
            header.set_val({'ricControlStyleType': 1, 'ricControlActionID': 1})
            header_aper = header.to_aper()

            # Constrói a Message
            msg = E2SM_RC_ControlMessage()
            msg.set_val({'ricControlActionParameters': [
                {
                    'ranParameterID': param_id,
                    'ranParameterName': parameter,
                    'ranParameterValue': int(value)
                }
            ]})
            msg_aper = msg.to_aper()
            
            # Retornamos as partes concatenadas ou como estrutura.
            # RMR mtype 12010 espera JSON empacotado para o E2 Term, 
            # ou o byte puro se a xApp fala APER nativo. 
            # A RDLxApp no nosso framework envia JSON, mas com o header/msg encodados.
            logger.debug(f"RC Control Encoded APER size: {len(msg_aper)} bytes")
            return msg_aper

        except Exception as e:
            logger.error(f"Erro Crítico ao encodar E2SM-RC via APER: {e}")
            raise
