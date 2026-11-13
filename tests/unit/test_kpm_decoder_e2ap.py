import os
import json
import pytest
from src.e2.kpm_decoder import KpmDecoder, E2SM_KPM_IndicationMessage
from src.e2.e2ap_decoder import RICindication
from src.e2.e2ap.pdu import wrap_initiating_message
from src.e2.e2ap.constants import PROC_RIC_INDICATION
from src.e2.kpm_raw_collector import KpmRawCollector

@pytest.fixture
def sample_kpm_payload():
    msg = E2SM_KPM_IndicationMessage()
    msg.set_val({
        'nodeID': 'gnb_01',
        'ueID': 'ue_01',
        'measData': [
            {'metricName': 'DRB.UEThpDl', 'metricValue': 55000},
            {'metricName': 'DRB.UEThpUl', 'metricValue': 15000},
            {'metricName': 'DRB.RlcSduDelayDl', 'metricValue': 12},
            {'metricName': 'RRU.PrbUsedDl', 'metricValue': 70}
        ]
    })
    msg_bytes = msg.to_aper()

    ind = RICindication()
    ind.set_val({
        'ricRequestID': {'ricRequestorID': 101, 'ricInstanceID': 1},
        'ranFunctionID': 2,
        'ricActionID': 1,
        'ricIndicationSN': 5,
        'ricIndicationType': 0,
        'ricIndicationHeader': b'\x01\x02\x03',
        'ricIndicationMessage': msg_bytes
    })
    ind_bytes = ind.to_aper()
    pdu_bytes = wrap_initiating_message(PROC_RIC_INDICATION, ind_bytes)

    return {
        "raw_kpm": msg_bytes,
        "ric_indication": ind_bytes,
        "e2ap_pdu": pdu_bytes
    }

def test_decode_e2ap_pdu_path(sample_kpm_payload):
    decoder = KpmDecoder()
    reports = decoder.decode_indication(sample_kpm_payload["e2ap_pdu"])
    assert len(reports) == 1
    assert decoder.last_decode_path == "e2ap_pdu"
    rep = reports[0]
    assert rep["node_id"] == "gnb_01"
    assert rep["ue_id"] == "ue_01"
    assert rep["drb_thp_dl"] == 55000.0
    assert rep["drb_delay_dl"] == 12.0
    assert rep["prb_used_dl"] == 70

def test_decode_ric_indication_path(sample_kpm_payload):
    decoder = KpmDecoder()
    reports = decoder.decode_indication(sample_kpm_payload["ric_indication"])
    assert len(reports) == 1
    assert decoder.last_decode_path == "ric_indication"
    assert reports[0]["drb_thp_dl"] == 55000.0

def test_decode_raw_kpm_fallback_path(sample_kpm_payload):
    decoder = KpmDecoder()
    reports = decoder.decode_indication(sample_kpm_payload["raw_kpm"])
    assert len(reports) == 1
    assert decoder.last_decode_path == "raw_kpm"
    assert reports[0]["drb_thp_dl"] == 55000.0


def test_aggregation_does_not_replace_unreported_metrics_with_zero():
    msg = E2SM_KPM_IndicationMessage()
    msg.set_val({
        "nodeID": "gnb_01",
        "ueID": "ue_01",
        "measData": [{"metricName": "DRB.UEThpDl", "metricValue": 100}],
    })

    report = KpmDecoder().decode_indication(msg.to_aper())[0]

    assert report["drb_thp_dl"] == 100.0
    assert "drb_delay_dl" not in report
    assert "prb_used_dl" not in report

def test_kpm_raw_collector_with_e2ap(tmp_path, sample_kpm_payload):
    collector = KpmRawCollector(base_exp_dir=str(tmp_path))
    kpm_dir = collector.create_run_session("run-0001")
    raw_path, json_path = collector.save_indication(kpm_dir, 1, sample_kpm_payload["e2ap_pdu"])

    assert os.path.exists(raw_path)
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["decode_ok"] is True
    assert data["reports_count"] == 1
    assert len(data["reports"]) == 1
    assert data["reports"][0]["drb_thp_dl"] == 55000.0
