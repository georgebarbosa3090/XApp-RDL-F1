"""
Testes da regra v6 do efeito do Control (scripts/certification/slice_effect.py, pré-registro
docs/preregistros/05_fase4_v6.md): previsão relativa à vazão antes do Control, com a razão r(teto) da curva
interpolada só entre níveis que restringem.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("slice_effect_v6", ROOT / "scripts" / "certification" / "slice_effect.py")
se = importlib.util.module_from_spec(SPEC)
sys.modules["slice_effect_v6"] = se
SPEC.loader.exec_module(se)

BASE = 151.488
# Mesma forma da curva v5: 10/15/20/30 % restringem; 70 % já não restringe
CURVE_PTS = [
    {"cap_max_prb_pct": 10.0, "throughput_before_mbps": BASE, "throughput_after_mbps": 37.458, "binding": True},
    {"cap_max_prb_pct": 15.0, "throughput_before_mbps": BASE, "throughput_after_mbps": 56.25, "binding": True},
    {"cap_max_prb_pct": 20.0, "throughput_before_mbps": BASE, "throughput_after_mbps": 76.446, "binding": True},
    {"cap_max_prb_pct": 30.0, "throughput_before_mbps": BASE, "throughput_after_mbps": 113.984, "binding": True},
    {"cap_max_prb_pct": 70.0, "throughput_before_mbps": BASE, "throughput_after_mbps": BASE, "binding": False},
]
CURVE = {"1": CURVE_PTS, "2": CURVE_PTS}


@pytest.mark.parametrize("cap,kind,ratio", [
    (20.0, "ratio", 76.446 / BASE),                                   # nível medido: a própria razão
    (25.0, "ratio", (76.446 / BASE + 113.984 / BASE) / 2),            # entre 20 e 30 (70 não entra)
    (30.0, "ratio", 113.984 / BASE),                                  # achado 41: sem interpolar até 70 %
    (70.0, "no_decrease", None),
    (85.0, "no_decrease", None),
    (40.0, "not_testable", None),                                     # joelho entre 30 e 70: desconhecido
    (5.0, "not_testable", None),
])
def test_predict_ratio(cap, kind, ratio):
    p = se.predict_ratio(CURVE_PTS, cap)
    assert p["kind"] == kind
    if ratio is not None:
        assert p["ratio"] == pytest.approx(ratio)


def _series(before, after_by_sst, t_apply=16.0):
    """Série sintética por fatia: vazão constante antes de t_apply e outra depois (amostras a 0,5 s)."""
    out = {}
    for sst in (1, 2):
        b, a = before[sst], after_by_sst[sst]
        rows, acc, t = [], 0.0, 0.0
        while t <= 40.0 + 1e-9:
            rows.append((t, 1000.0 + 3.6 * t, acc))
            rate = b if t < t_apply else a
            acc += rate * 1e6 / 8 * 0.5
            t += 0.5
        out[sst] = rows
    return out


QUOTAS_80_20 = [{"sst": 1, "max_prb_ratio": 80}, {"sst": 2, "max_prb_ratio": 20}]


def test_prediction_scales_with_the_base_rate():
    # Achado 42: vazão de base pela metade, mesma razão -> CONSISTENT na v6
    half = BASE / 2
    s = _series({1: half, 2: half}, {1: half, 2: half * 76.446 / BASE})
    r = se.evaluate_ratio(s, 16.0, QUOTAS_80_20, CURVE)
    assert r["verdict"] == "CONSISTENT"
    assert r["slices"]["2"]["predicted_after_mbps"] == pytest.approx(half * 76.446 / BASE, rel=1e-3)
    assert r["slices"]["1"]["expectation"] == "no_decrease"


def test_wrong_effect_is_inconsistent():
    s = _series({1: BASE, 2: BASE}, {1: BASE, 2: BASE * 0.8})     # caiu bem menos que r(20 %) = 0,505
    assert se.evaluate_ratio(s, 16.0, QUOTAS_80_20, CURVE)["verdict"] == "INCONSISTENT"
    s = _series({1: BASE, 2: BASE}, {1: BASE * 0.7, 2: BASE * 0.505})  # eMBB perdeu vazão acima do nível livre
    assert se.evaluate_ratio(s, 16.0, QUOTAS_80_20, CURVE)["verdict"] == "INCONSISTENT"


def test_tolerance_is_ten_percent():
    pred = BASE * 76.446 / BASE
    ok = se.evaluate_ratio(_series({1: BASE, 2: BASE}, {1: BASE, 2: pred * 1.09}), 16.0, QUOTAS_80_20, CURVE)
    bad = se.evaluate_ratio(_series({1: BASE, 2: BASE}, {1: BASE, 2: pred * 1.12}), 16.0, QUOTAS_80_20, CURVE)
    assert ok["verdict"] == "CONSISTENT" and bad["verdict"] == "INCONSISTENT"


def test_cap_in_the_unknown_knee_is_not_testable():
    s = _series({1: BASE, 2: BASE}, {1: BASE, 2: BASE})
    r = se.evaluate_ratio(s, 16.0, [{"sst": 1, "max_prb_ratio": 60}, {"sst": 2, "max_prb_ratio": 40}], CURVE)
    assert r["verdict"] == "NOT_TESTABLE"


def test_v6_requires_the_curve():
    with pytest.raises(ValueError):
        se.analyze("x", rule="v6")
