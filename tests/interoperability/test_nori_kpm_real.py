"""
Testes de Interoperabilidade E2SM-KPM / NORI
Valida a recepção, decodificação e agregação de telemetria multicélula transmitida pelo E2 Node/NORI.
"""

import pytest
from src.e2.kpm_decoder import KpmDecoder, E2SM_KPM_IndicationMessage
from src.e2.kpm.event_trigger import build_kpm_event_trigger
from src.e2.kpm.action_definition import build_kpm_action_definition

def test_nori_kpm_event_trigger_subscription_pipeline():
    """
    Testa a geração de Event Trigger para subscrição periódica (200ms) no NORI.
    """
    event_trigger_bytes = build_kpm_event_trigger(reporting_period_ms=200)
    assert len(event_trigger_bytes) > 0
    assert isinstance(event_trigger_bytes, bytes)

def test_nori_kpm_action_definition_3gpp_metrics():
    """
    Testa a geração de Action Definition contendo as métricas canônicas 3GPP 28.552 requisitadas pelo NORI.
    """
    metrics = ["DRB.UEThpDl", "RRU.PrbUsedDl", "DRB.RlcSduDelayDl"]
    action_def_bytes = build_kpm_action_definition(
        style_type=1,
        granularity_period_ms=200,
        metric_names=metrics
    )
    assert len(action_def_bytes) > 0
    assert isinstance(action_def_bytes, bytes)

def test_nori_kpm_indication_decoding_pipeline():
    """
    Testa a decodificação estrita de uma mensagem de telemetria recebida de um nó gNodeB.
    """
    msg = E2SM_KPM_IndicationMessage()
    msg.set_val({
        'nodeID': 'gnb_01',
        'ueID': 'ue_10',
        'measData': [
            {'metricName': 'DRB.UEThpDl', 'metricValue': 100},
            {'metricName': 'RRU.PrbUsedDl', 'metricValue': 40}
        ]
    })
    raw_payload = msg.to_aper()

    decoder = KpmDecoder()
    measurements = decoder.decode(raw_payload, raw_payload)
    
    assert len(measurements) == 2
    assert measurements[0].node_id == "gnb_01"
    assert measurements[0].metric_name == "DRB.UEThpDl"
    assert measurements[0].value == 100.0
