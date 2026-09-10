import pytest
from src.e2.kpm.event_trigger import build_kpm_event_trigger, E2SM_KPM_EventTriggerDefinition
from src.e2.kpm.action_definition import build_kpm_action_definition, E2SM_KPM_ActionDefinition
from src.e2.kpm_decoder import KpmDecoder, E2SM_KPM_IndicationMessage

def test_kpm_event_trigger_roundtrip():
    """Valida serialização e desserialização APER do KPM Event Trigger Definition."""
    period_ms = 200
    aper_bytes = build_kpm_event_trigger(report_period_ms=period_ms)
    
    assert isinstance(aper_bytes, bytes)
    assert len(aper_bytes) > 0
    
    # Desserializa
    trigger = E2SM_KPM_EventTriggerDefinition()
    trigger.from_aper(aper_bytes)
    val = trigger()
    assert val['eventDefinition_formats']['reportingPeriodMs'] == period_ms

def test_kpm_action_definition_roundtrip():
    """Valida serialização e desserialização APER do KPM Action Definition."""
    metric_names = ["DRB.UEThpDl", "RRU.PrbUsedDl"]
    aper_bytes = build_kpm_action_definition(style_type=1, granularity_period_ms=200, metric_names=metric_names)
    
    assert isinstance(aper_bytes, bytes)
    assert len(aper_bytes) > 0
    
    # Desserializa
    action_def = E2SM_KPM_ActionDefinition()
    action_def.from_aper(aper_bytes)
    val = action_def()
    meas_list = val['actionDefinition_formats']['measInfoList']
    assert len(meas_list) == 2
    assert meas_list[0]['measType'] == "DRB.UEThpDl"

def test_kpm_indication_message_strict_decoding():
    """Valida decodificação APER estrita da Indication Message E2SM-KPM."""
    msg = E2SM_KPM_IndicationMessage()
    msg.set_val({
        'nodeID': "gnb_01",
        'ueID': "ue_42",
        'measData': [
            {'metricName': "DRB.UEThpDl", 'metricValue': 28500},
            {'metricName': "RRU.PrbUsedDl", 'metricValue': 65}
        ]
    })
    aper_bytes = msg.to_aper()
    
    decoder = KpmDecoder()
    measurements = decoder.decode(indication_header=b'', indication_message=aper_bytes)
    
    assert len(measurements) == 2
    assert measurements[0].ue_id == "ue_42"
    assert measurements[0].metric_name == "DRB.UEThpDl"
    assert measurements[0].value == 28500.0
