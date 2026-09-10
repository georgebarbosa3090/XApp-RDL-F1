import pytest
from src.e2.rc_encoder import RCEncoder, E2SM_RC_ControlPDU
from src.e2.rc.control_parameter import validate_ran_parameter

def test_rc_encoder_pdu_roundtrip():
    """Valida serialização e desserialização APER unificada de Header e Message no E2SM-RC."""
    encoder = RCEncoder()
    encoded = encoder.encode_control_parts(
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=75.0,
        style_type=1,
        action_id=1
    )
    
    assert len(encoded.header_aper) > 0
    assert len(encoded.message_aper) > 0
    assert len(encoded.pdu_aper) > 0
    
    # Desserializa a PDU
    pdu = E2SM_RC_ControlPDU()
    pdu.from_aper(encoded.pdu_aper)
    val = pdu()
    
    assert val['ricControlHeader']['ricControlStyleType'] == 1
    params = val['ricControlMessage']['ricControlActionParameters']
    assert len(params) == 1
    assert params[0]['ranParameterID'] == 1
    assert params[0]['ranParameterName'] == "PRB_QUOTA"
    assert params[0]['ranParameterValue'] == 75

def test_rc_parameter_validation():
    """Valida limites estritos de parâmetros E2SM-RC."""
    is_valid, param_id, reason = validate_ran_parameter("PRB_QUOTA", 80.0)
    assert is_valid is True
    assert param_id == 1
    
    is_valid_pow, param_id_pow, _ = validate_ran_parameter("TX_POWER", 20.0)
    assert is_valid_pow is True
    assert param_id_pow == 3
    
    # Inválido (fora de faixa)
    is_inv, _, reason_inv = validate_ran_parameter("TX_POWER", 50.0)
    assert is_inv is False
