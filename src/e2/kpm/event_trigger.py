from pycrate_asn1rt.asnobj_basic import INT
from pycrate_asn1rt.asnobj_construct import SEQ, ASN1Dict
from src.observability.logging import setup_logger

logger = setup_logger("KpmEventTrigger")

# ASN.1 Estrutural para E2SM-KPM Event Trigger Definition (Format 1 - Periodic Reporting)
class E2SM_KPM_EventTriggerDefinition_Format1(SEQ):
    _cont = ASN1Dict([
        ('reportingPeriodMs', INT())
    ])
    _root_mand = ['reportingPeriodMs']
    _root_opt = []
    _root = ['reportingPeriodMs']
    _ext = None

class E2SM_KPM_EventTriggerDefinition(SEQ):
    _cont = ASN1Dict([
        ('eventDefinition_formats', E2SM_KPM_EventTriggerDefinition_Format1())
    ])
    _root_mand = ['eventDefinition_formats']
    _root_opt = []
    _root = ['eventDefinition_formats']
    _ext = None

def build_kpm_event_trigger(report_period_ms: int = 200) -> bytes:
    """
    Constrói o buffer binário APER normativo para o Event Trigger Definition do E2SM-KPM.
    Define o intervalo periódico de envio de telemetria pelo nó E2 / simulador 5G-LENA.
    """
    try:
        trigger = E2SM_KPM_EventTriggerDefinition()
        trigger.set_val({
            'eventDefinition_formats': {
                'reportingPeriodMs': int(report_period_ms)
            }
        })
        aper_bytes = trigger.to_aper()
        logger.debug(f"E2SM-KPM Event Trigger gerado ({len(aper_bytes)} bytes) para período {report_period_ms}ms")
        return aper_bytes
    except Exception as e:
        logger.error(f"Falha ao gerar E2SM-KPM Event Trigger via APER: {e}")
        raise
