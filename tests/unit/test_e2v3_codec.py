"""
Testes do codec E2AP v03.01 / E2SM v3 (src/e2/v3/codec.py).

A camada E2AP é conferida contra o dissecador de PCAP do certificador, implementação separada.
A camada E2SM usa o ASN.1 do NORI baixado no commit fixado (sha256 conferido); sem rede e sem
cache, esses testes são pulados com o motivo explícito.
"""

import importlib.util
import struct
import sys
from pathlib import Path

import pytest

from src.e2.v3 import codec as c

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("e2_pcap_dissect_v3", ROOT / "scripts" / "certification" / "e2_pcap_dissect.py")
dis = importlib.util.module_from_spec(_spec)
sys.modules["e2_pcap_dissect_v3"] = dis
_spec.loader.exec_module(dis)


@pytest.fixture(scope="module")
def e2sm():
    try:
        return c.E2smCodec()
    except Exception as exc:  # noqa: BLE001 - sem ASN.1 (rede/cache) não há como testar o E2SM
        pytest.skip(f"ASN.1 do NORI indisponível: {exc}")


# ---------------------------------------------------------------------------
# APER e E2AP
# ---------------------------------------------------------------------------

def test_aper_writer_matches_reader_for_constrained_and_lengths():
    w = c.AperWriter().bits(1, 1).constrained(4095, 0, 4095).constrained(200, 0, 255).length(300).octets(b"x" * 300)
    r = c.AperReader(w.to_bytes())
    assert r.bits(1) == 1
    assert r.constrained(0, 4095) == 4095
    assert r.constrained(0, 255) == 200
    assert r.length() == 300 and r.octets(300) == b"x" * 300
    with pytest.raises(c.CodecError):
        c.AperWriter().constrained(4096, 0, 4095)


def test_control_request_is_read_identically_by_the_pcap_dissector():
    pdu = c.encode_ric_control_request(1003, 7, 300, b"\x10\x20", b"\x30" * 200, ack_request=True)
    mine = c.decode_e2ap_pdu(pdu)
    assert mine["pdu_type"] == "initiatingMessage" and mine["procedure_code"] == 4
    assert (mine["ric_requestor_id"], mine["ric_instance_id"], mine["ran_function_id"]) == (1003, 7, 300)
    assert mine["control_header"] == b"\x10\x20" and len(mine["control_message"]) == 200
    assert mine["ack_request"] is True
    assert mine["ie_ids"] == [5, 21, 22, 23, 29]
    theirs = dis.decode_e2ap_header(pdu)
    assert theirs["role"] == "control_request"
    assert dis.ie_value(theirs, dis.IE_RIC_REQUEST_ID) == {"requestor": 1003, "instance": 7}
    assert dis.ie_value(theirs, dis.IE_RAN_FUNCTION_ID) == 300
    assert dis.ie_value(theirs, dis.IE_RIC_CONTROL_MESSAGE)["len"] == 200


def test_ie_order_follows_the_asn1_definition():
    pdu = c.encode_ric_control_request(1, 2, 300, b"h", b"m", ack_request=False, call_process_id=b"\x01")
    r = c.AperReader(pdu)
    r.bits(3); r.constrained(0, 255); r.bits(2)
    body = c.AperReader(r.open_type())
    body.bits(1)
    order = []
    for _ in range(body.constrained(0, 65535)):
        order.append(body.constrained(0, 65535)); body.bits(2); body.open_type()
    # RICrequestID, RANfunctionID, RICcallProcessID, Header, Message, AckRequest
    assert order == [29, 5, 20, 22, 23, 21]
    assert c.decode_e2ap_pdu(pdu)["ack_request"] is False


def test_parse_control_ack_and_failure():
    ack = c.encode_e2ap_pdu(c.PDU_SUCCESSFUL, c.PROC_RIC_CONTROL, c.CRIT_REJECT, [
        (c.IE_RIC_REQUEST_ID, c.CRIT_REJECT, c._ric_request_id(1003, 7)),
        (c.IE_RAN_FUNCTION_ID, c.CRIT_REJECT, struct.pack("!H", 300))])
    out = c.parse_ric_control_outcome(ack)
    assert out["outcome"] == "ACK" and (out["ric_requestor_id"], out["ric_instance_id"], out["ran_function_id"]) == (1003, 7, 300)
    assert dis.decode_e2ap_header(ack)["role"] == "control_ack"
    fail = c.encode_e2ap_pdu(c.PDU_UNSUCCESSFUL, c.PROC_RIC_CONTROL, c.CRIT_REJECT, [
        (c.IE_RIC_REQUEST_ID, c.CRIT_REJECT, c._ric_request_id(1003, 7)),
        (c.IE_RAN_FUNCTION_ID, c.CRIT_REJECT, struct.pack("!H", 300)),
        (c.IE_CAUSE, c.CRIT_IGNORE, b"\x00\x00")])
    assert c.parse_ric_control_outcome(fail)["outcome"] == "FAILURE"
    with pytest.raises(c.CodecError):
        c.parse_ric_control_outcome(c.encode_ric_control_request(1, 1, 300, b"h", b"m"))


def test_trailing_bytes_are_rejected():
    with pytest.raises(c.CodecError):
        c.decode_e2ap_pdu(c.encode_ric_control_request(1, 1, 300, b"h", b"m") + b"\x00")


# ---------------------------------------------------------------------------
# E2SM-KPM / E2SM-RC (ASN.1 do NORI)
# ---------------------------------------------------------------------------

def test_kpm_event_trigger_known_vector(e2sm):
    # reportingPeriod INTEGER (1..4294967295) = 1000 -> 999 em 2 octetos
    assert e2sm.kpm_event_trigger(1000).hex() == "0803e7"


def test_rc_slice_quota_roundtrip_as_nori_reads_it(e2sm):
    quotas = [c.SlicePrbQuota(1, 70, 10, 5), c.SlicePrbQuota(2, 30, 10, 5)]
    assert e2sm.rc_decode_slice_quotas(e2sm.rc_slice_quota_message(quotas)) == quotas
    fmt, header = e2sm.rc_decode_header(e2sm.rc_slice_quota_header(bytes.fromhex("623814")))["ric-controlHeader-formats"]
    assert fmt == "controlHeader-Format1"
    assert header["ric-Style-Type"] == 2 and header["ric-ControlAction-ID"] == 6
    assert header["ueID"][1]["guami"]["pLMNIdentity"] == bytes.fromhex("623814")


def test_rc_quota_validation(e2sm):
    with pytest.raises(c.CodecError):
        e2sm.rc_slice_quota_message([c.SlicePrbQuota(1, 120)])
    with pytest.raises(c.CodecError):
        e2sm.rc_slice_quota_message([c.SlicePrbQuota(1, 20, min_prb_ratio=30)])
    with pytest.raises(c.CodecError):
        e2sm.rc_slice_quota_message([])


def test_full_control_request_carries_decodable_e2sm(e2sm):
    pdu = c.build_slice_quota_control(e2sm, 1003, 1, 300, [c.SlicePrbQuota(1, 70, 10, 5)])
    d = c.decode_e2ap_pdu(pdu)
    assert e2sm.rc_decode_slice_quotas(d["control_message"]) == [c.SlicePrbQuota(1, 70, 10, 5)]
    assert d["ack_request"] is True
