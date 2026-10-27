import pytest
from src.e2.rc_encoder import RCEncoder, PARAM_PROFILES
from src.e2.rc.control_parameter import RAN_PARAMETERS
from src.e2.rc.capability_registry import rc_capability_registry
from src.e2.rc.mapper import RCMapper
from src.conflict_types import XAppAction

def test_canonical_param_ids_consistency():
    for param_name in ["PRB_QUOTA", "SCHEDULER_WEIGHT", "TX_POWER", "HANDOVER"]:
        canonical_def = RAN_PARAMETERS[param_name]
        profile_def = PARAM_PROFILES[param_name]
        registry_cap = rc_capability_registry.get_action_capability(param_name, "gnb_01", strict_mode=False)

        assert profile_def["id"] == canonical_def.param_id, f"Profile ID mismatch for {param_name}"
        assert registry_cap.param_id == canonical_def.param_id, f"Registry ID mismatch for {param_name}"

def test_encode_control_parts_param_id_override():
    encoder = RCEncoder()
    encoded = encoder.encode_control_parts(
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=50.0,
        style_type=1,
        action_id=1,
        param_id=99
    )
    decoded_id = encoder.decode_param_id(encoded.message_aper)
    assert decoded_id == 99

def test_encode_control_parts_default_id():
    encoder = RCEncoder()
    for param_name, defn in RAN_PARAMETERS.items():
        val = 10.0 if param_name != "TX_POWER" else 20.0
        encoded = encoder.encode_control_parts(
            node_id="gnb_01",
            parameter=param_name,
            value=val,
            style_type=1,
            action_id=1
        )
        decoded_id = encoder.decode_param_id(encoded.message_aper)
        assert decoded_id == defn.param_id

def test_mapper_passes_resolved_param_id():
    mapper = RCMapper(ran_function_id=3)
    action = XAppAction(
        xapp_id="test_xapp",
        node_id="gnb_01",
        parameter="TX_POWER",
        value=35.0,
        priority=10
    )
    ctx = mapper.map_action_to_control_request(action)
    encoder = RCEncoder()
    decoded_id = encoder.decode_param_id(ctx.message_bytes)
    assert decoded_id == 3
