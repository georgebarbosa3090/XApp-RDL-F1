"""
Testes de Decodificação Cruzada de Vetores Dourados Normativos (Golden Vectors APER Oracle)
Valida a compatibilidade de desempacotamento de E2AP, E2SM-KPM e E2SM-RC a partir de artefatos pré-compilados (.raw).
"""

import os
import json
import pytest
from src.e2.e2ap.pdu import unwrap_e2ap_pdu
from src.e2.e2ap.control import parse_ric_control_ack, parse_ric_control_failure
from src.e2.e2ap.constants import PROC_RIC_CONTROL
from src.e2.kpm_decoder import KpmDecoder, E2SM_KPM_IndicationMessage
from src.e2.rc_encoder import RCEncoder

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "specs", "golden_vectors")

def test_golden_vector_ric_control_request():
    raw_path = os.path.join(GOLDEN_DIR, "e2ap_ric_control_request.raw")
    json_path = os.path.join(GOLDEN_DIR, "e2ap_ric_control_request.json")
    assert os.path.exists(raw_path) and os.path.exists(json_path)

    with open(raw_path, "rb") as f:
        raw_bytes = f.read()
    with open(json_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    pdu_type, proc_code, crit, inner = unwrap_e2ap_pdu(raw_bytes)
    assert pdu_type == spec["pdu_type"]
    assert proc_code == spec["procedure_code"] == PROC_RIC_CONTROL
    assert len(inner) > 0

def test_golden_vector_ric_control_ack():
    raw_path = os.path.join(GOLDEN_DIR, "e2ap_ric_control_ack.raw")
    json_path = os.path.join(GOLDEN_DIR, "e2ap_ric_control_ack.json")
    with open(raw_path, "rb") as f:
        raw_bytes = f.read()

    pdu_type, proc_code, crit, inner = unwrap_e2ap_pdu(raw_bytes)
    assert pdu_type == "successfulOutcome"
    assert proc_code == PROC_RIC_CONTROL

    ack_data = parse_ric_control_ack(raw_bytes)
    assert ack_data["status"] == "ACKNOWLEDGED"
    assert ack_data["requestor_id"] == 1

def test_golden_vector_ric_control_failure():
    raw_path = os.path.join(GOLDEN_DIR, "e2ap_ric_control_failure.raw")
    json_path = os.path.join(GOLDEN_DIR, "e2ap_ric_control_failure.json")
    with open(raw_path, "rb") as f:
        raw_bytes = f.read()

    pdu_type, proc_code, crit, inner = unwrap_e2ap_pdu(raw_bytes)
    assert pdu_type == "unsuccessfulOutcome"
    assert proc_code == PROC_RIC_CONTROL

    fail_data = parse_ric_control_failure(raw_bytes)
    assert fail_data["status"] == "FAILED"
    assert fail_data["cause"] == 1

def test_golden_vector_e2sm_kpm_indication():
    raw_path = os.path.join(GOLDEN_DIR, "e2sm_kpm_indication.raw")
    with open(raw_path, "rb") as f:
        raw_bytes = f.read()

    decoder = KpmDecoder()
    measurements = decoder.decode(raw_bytes, raw_bytes)
    assert len(measurements) == 3

    metrics_dict = {m.metric_name: m.value for m in measurements}
    assert metrics_dict["DRB.UEThpDl"] == 45000.0
    assert metrics_dict["DRB.RlcSduDelayDl"] == 2800.0
    assert metrics_dict["RRU.PrbUsedDl"] == 65.0

def test_golden_vector_e2sm_rc_control_prb():
    raw_path = os.path.join(GOLDEN_DIR, "e2sm_rc_control_prb.raw")
    with open(raw_path, "rb") as f:
        raw_bytes = f.read()

    encoder = RCEncoder()
    val = encoder.decode_control_request(raw_bytes, "PRB_QUOTA")
    assert val == pytest.approx(65.0, 0.01)
