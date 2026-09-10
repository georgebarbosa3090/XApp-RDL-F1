from typing import List, Optional
from pycrate_asn1rt.asnobj_basic import INT
from pycrate_asn1rt.asnobj_str import STR_UTF8
from pycrate_asn1rt.asnobj_construct import SEQ, SEQ_OF, ASN1Dict
from src.observability.logging import setup_logger

logger = setup_logger("KpmActionDefinition")

# ASN.1 Estrutural para E2SM-KPM Action Definition (Format 1)
class MeasurementInfoItem(SEQ):
    _cont = ASN1Dict([
        ('measType', STR_UTF8()),
        ('measID', INT(opt=True))
    ])
    _root_mand = ['measType']
    _root_opt = ['measID']
    _root = ['measType', 'measID']
    _ext = None

class MeasurementInfoList(SEQ_OF):
    _cont = MeasurementInfoItem()

class E2SM_KPM_ActionDefinition_Format1(SEQ):
    _cont = ASN1Dict([
        ('ric_Style_Type', INT()),
        ('measInfoList', MeasurementInfoList()),
        ('granulPeriod', INT())
    ])
    _root_mand = ['ric_Style_Type', 'measInfoList', 'granulPeriod']
    _root_opt = []
    _root = ['ric_Style_Type', 'measInfoList', 'granulPeriod']
    _ext = None

class E2SM_KPM_ActionDefinition(SEQ):
    _cont = ASN1Dict([
        ('actionDefinition_formats', E2SM_KPM_ActionDefinition_Format1())
    ])
    _root_mand = ['actionDefinition_formats']
    _root_opt = []
    _root = ['actionDefinition_formats']
    _ext = None

def build_kpm_action_definition(
    style_type: int = 1,
    granularity_period_ms: int = 200,
    metric_names: Optional[List[str]] = None
) -> bytes:
    """
    Constrói o buffer binário APER normativo para a Action Definition do E2SM-KPM.
    Especifica a lista de métricas 3GPP a serem coletadas da RAN (ex: DRB.UEThpDl, RRU.PrbUsedDl).
    """
    if metric_names is None:
        metric_names = [
            "DRB.UEThpDl",
            "DRB.UEThpUl",
            "DRB.RlcSduDelayDl",
            "RRU.PrbUsedDl",
            "RRU.PrbUsedUl"
        ]
        
    try:
        meas_list = [{'measType': name, 'measID': idx + 1} for idx, name in enumerate(metric_names)]
        action_def = E2SM_KPM_ActionDefinition()
        action_def.set_val({
            'actionDefinition_formats': {
                'ric_Style_Type': int(style_type),
                'measInfoList': meas_list,
                'granulPeriod': int(granularity_period_ms)
            }
        })
        aper_bytes = action_def.to_aper()
        logger.debug(f"E2SM-KPM Action Definition gerada ({len(aper_bytes)} bytes) com {len(metric_names)} metricas")
        return aper_bytes
    except Exception as e:
        logger.error(f"Falha ao gerar E2SM-KPM Action Definition via APER: {e}")
        raise
