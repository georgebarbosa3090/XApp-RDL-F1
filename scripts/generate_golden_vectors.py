"""
Gerador Canônico de Vetores Dourados ASN.1 APER para Validação Cruzada Independente (Specs / Golden Vectors)
Gera arquivos binários (.raw) e definições estruturadas (.json) para E2AP, E2SM-KPM e E2SM-RC.
"""

import os
import sys
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.e2.e2ap.control import (
    RICcontrolRequest,
    RICcontrolAcknowledge,
    RICcontrolFailure,
    build_ric_control_request
)
from src.e2.e2ap.pdu import (
    wrap_initiating_message,
    wrap_successful_outcome,
    wrap_unsuccessful_outcome
)
from src.e2.e2ap.constants import (
    PROC_RIC_CONTROL,
    PROC_RIC_SUBSCRIPTION,
    PROC_RIC_INDICATION,
    IE_RIC_REQUEST_ID,
    IE_RAN_FUNCTION_ID,
    IE_RIC_CONTROL_HEADER,
    IE_RIC_CONTROL_MESSAGE,
    IE_RIC_CONTROL_ACK_REQUEST,
    IE_CAUSE
)
from src.e2.kpm.event_trigger import build_kpm_event_trigger_definition
from src.e2.kpm_decoder import E2SM_KPM_IndicationMessage
from src.e2.rc_encoder import RCEncoder

def generate_golden_vectors(target_dir: str = "specs/golden_vectors"):
    os.makedirs(target_dir, exist_ok=True)
    encoder = RCEncoder()

    # 1. E2AP RIC Control Request
    ctrl_pdu = build_ric_control_request(
        node_id="gnb_01",
        ran_function_id=3,
        header_bytes=b"\x01\x01",
        message_bytes=b"\x02\x01\x41",
        requestor_id=1,
        instance_id=1,
        ack_request=1
    )
    with open(os.path.join(target_dir, "e2ap_ric_control_request.raw"), "wb") as f:
        f.write(ctrl_pdu.pdu_aper)
    with open(os.path.join(target_dir, "e2ap_ric_control_request.json"), "w", encoding="utf-8") as f:
        json.dump({
            "pdu_type": "initiatingMessage",
            "procedure_code": PROC_RIC_CONTROL,
            "requestor_id": 1,
            "instance_id": 1,
            "ran_function_id": 3,
            "hex": ctrl_pdu.pdu_aper.hex()
        }, f, indent=2)

    # 2. E2AP RIC Control ACK
    ack = RICcontrolAcknowledge()
    ack.set_val({
        'ricRequestID': {'ricRequestorID': 1, 'ricInstanceID': 1},
        'ranFunctionID': 3,
        'ricControlOutcome': b'\x06\x01\x00'
    })
    ack_bytes = ack.to_aper()
    ack_pdu = wrap_successful_outcome(PROC_RIC_CONTROL, ack_bytes)
    with open(os.path.join(target_dir, "e2ap_ric_control_ack.raw"), "wb") as f:
        f.write(ack_pdu)
    with open(os.path.join(target_dir, "e2ap_ric_control_ack.json"), "w", encoding="utf-8") as f:
        json.dump({
            "pdu_type": "successfulOutcome",
            "procedure_code": PROC_RIC_CONTROL,
            "requestor_id": 1,
            "instance_id": 1,
            "status": "ACKNOWLEDGED",
            "hex": ack_pdu.hex()
        }, f, indent=2)

    # 3. E2AP RIC Control Failure
    fail = RICcontrolFailure()
    fail.set_val({
        'ricRequestID': {'ricRequestorID': 1, 'ricInstanceID': 1},
        'ranFunctionID': 3,
        'cause': 1
    })
    fail_bytes = fail.to_aper()
    fail_pdu = wrap_unsuccessful_outcome(PROC_RIC_CONTROL, fail_bytes)
    with open(os.path.join(target_dir, "e2ap_ric_control_failure.raw"), "wb") as f:
        f.write(fail_pdu)
    with open(os.path.join(target_dir, "e2ap_ric_control_failure.json"), "w", encoding="utf-8") as f:
        json.dump({
            "pdu_type": "unsuccessfulOutcome",
            "procedure_code": PROC_RIC_CONTROL,
            "requestor_id": 1,
            "instance_id": 1,
            "cause": 1,
            "status": "FAILED",
            "hex": fail_pdu.hex()
        }, f, indent=2)

    # 4. E2SM-KPM Event Trigger
    trigger_bytes = build_kpm_event_trigger_definition(reporting_period_ms=200)
    with open(os.path.join(target_dir, "e2sm_kpm_event_trigger.raw"), "wb") as f:
        f.write(trigger_bytes)
    with open(os.path.join(target_dir, "e2sm_kpm_event_trigger.json"), "w", encoding="utf-8") as f:
        json.dump({
            "reporting_period_ms": 200,
            "hex": trigger_bytes.hex()
        }, f, indent=2)

    # 5. E2SM-KPM Indication Message
    kpm_msg = E2SM_KPM_IndicationMessage()
    kpm_msg.set_val({
        'measData': [
            {'metricName': 'DRB.UEThpDl', 'metricValue': 45000},
            {'metricName': 'DRB.RlcSduDelayDl', 'metricValue': 2800},
            {'metricName': 'RRU.PrbUsedDl', 'metricValue': 65}
        ],
        'nodeID': 'gnb_01',
        'ueID': 'ue_01'
    })
    kpm_bytes = kpm_msg.to_aper()
    with open(os.path.join(target_dir, "e2sm_kpm_indication.raw"), "wb") as f:
        f.write(kpm_bytes)
    with open(os.path.join(target_dir, "e2sm_kpm_indication.json"), "w", encoding="utf-8") as f:
        json.dump({
            "nodeID": "gnb_01",
            "ueID": "ue_01",
            "metrics": [
                {"name": "DRB.UEThpDl", "value": 45000},
                {"name": "DRB.RlcSduDelayDl", "value": 2800},
                {"name": "RRU.PrbUsedDl", "value": 65}
            ],
            "hex": kpm_bytes.hex()
        }, f, indent=2)

    # 6. E2SM-RC Control PDU (PRB_QUOTA = 65%)
    rc_parts = encoder.encode_control_parts("gnb_01", "PRB_QUOTA", 65.0, style_type=1, action_id=1)
    with open(os.path.join(target_dir, "e2sm_rc_control_prb.raw"), "wb") as f:
        f.write(rc_parts.pdu_aper)
    with open(os.path.join(target_dir, "e2sm_rc_control_prb.json"), "w", encoding="utf-8") as f:
        json.dump({
            "parameter": "PRB_QUOTA",
            "value": 65.0,
            "style_type": 1,
            "action_id": 1,
            "hex": rc_parts.pdu_aper.hex()
        }, f, indent=2)

if __name__ == "__main__":
    generate_golden_vectors()
