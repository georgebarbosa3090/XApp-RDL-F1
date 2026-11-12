"""Perfis de backend do testbed UFPA: NORI (referência), srsRAN (GERCOM) e OAI (LACIS) — doc 12 §4."""
import pytest

from src.e2.backends import testbed_profiles as tp


def test_profiles_load_and_tb0_status():
    nori = tp.summary(tp.load_profile("NORI_NS3"))
    assert nori["tb0_ready"] and nori["verified"] and nori["rc_slice_param_ids"]["max"] == 4
    for name in ("SRSRAN_PROJECT", "OAI_FLEXRIC"):
        prof = tp.load_profile(name)
        s = tp.summary(prof)
        assert not s["tb0_ready"] and not s["verified"] and s["rc_slice_param_ids"] is None
        assert "e2.e2ap_version" in s["pending"] and "rc.prb_quota.param_ids" in s["pending"]
        assert "ue_sst" not in tp.kpm_metrics(prof) and tp.kpm_metrics(prof)["prb_used"] == "RRU.PrbUsedDl"
    with pytest.raises(ValueError):
        tp.load_profile("ERICSSON")


def test_unsupported_layout_and_custom_profile(tmp_path):
    custom = tmp_path / "lab.yaml"
    custom.write_text("backend: X\nrc:\n  prb_quota: {layout: aninhado_norma, param_ids: {list: 1}}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        tp.rc_slice_param_ids(tp.load_profile(str(custom)))
    custom.write_text("backend: X\nrc:\n  prb_quota: {layout: nori_flat, param_ids: {list: 1, sst: 8, max: 11, min: 10, dedicated: 12}}\n",
                      encoding="utf-8")
    assert tp.rc_slice_param_ids(tp.load_profile(str(custom))) == {"list": 1, "sst": 8, "max": 11, "min": 10, "dedicated": 12}
    bad = tmp_path / "bad.yaml"
    bad.write_text("- lista\n", encoding="utf-8")
    with pytest.raises(ValueError):
        tp.load_profile(str(bad))


def test_codec_uses_profile_param_ids():
    from src.governance import interception as icpt
    from src.e2.v3 import codec as v3
    codec = icpt._nori_codec()
    if codec is None:
        pytest.skip("ASN.1 do NORI fora do cache local")
    ids = {"list": 1, "sst": 8, "max": 11, "min": 10, "dedicated": 12}
    quotas = [v3.SlicePrbQuota(1, 70, 10, 5), v3.SlicePrbQuota(2, 30, 10, 5)]
    msg = codec.rc_slice_quota_message(quotas, param_ids=ids)
    assert codec.rc_decode_slice_quotas(msg, param_ids=ids) == quotas
    assert [q.max_prb_ratio for q in codec.rc_decode_slice_quotas(msg)] != [70, 30]      # IDs do NORI não leem
    assert codec.rc_decode_slice_quotas(codec.rc_slice_quota_message(quotas)) == quotas   # padrão continua o NORI
