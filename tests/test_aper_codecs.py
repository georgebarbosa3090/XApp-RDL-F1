import pytest
from src.e2.e2ap_decoder import decode_e2ap_ric_indication
from src.e2.kpm_decoder import KpmDecoder
from src.e2.rc_encoder import RCEncoder

def test_e2ap_decoder_mock_fallback():
    # Passando bytes crus que não são válidos APER para verificar se o fallback MOCK
    # protege a thread principal de crashear (Resiliência Zero to Hero).
    payload = b"MOCK_PAYLOAD"
    indication = decode_e2ap_ric_indication(payload)
    
    assert indication is not None
    assert indication.request_id == 1
    assert indication.ran_function_id == 2

def test_kpm_decoder_fallback():
    decoder = KpmDecoder()
    
    # Bytes que quebram o ASN.1 estrito
    payload = b"BOGUS_DATA"
    measurements = decoder.decode_indication(payload)
    
    # Deve retornar a lista MOCK para testes locais sem quebrar
    assert isinstance(measurements, list)
    assert len(measurements) > 0
    assert "node_id" in measurements[0]
    assert measurements[0]["drb_thp_dl"] > 0

def test_rc_encoder_generates_bytes():
    encoder = RCEncoder()
    
    node_id = "gnb_01"
    parameter = "PRB_QUOTA"
    value = 50.0
    
    aper_bytes = encoder.encode_control_request(node_id, parameter, value)
    
    # Deve gerar um bytestring (APER encoded PDU)
    assert isinstance(aper_bytes, bytes)
    assert len(aper_bytes) > 0
