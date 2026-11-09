"""
Testes do disparo da decisão só com o par de KPM do período (src/closed_loop/kpm_pairing.py, achado 48).
"""

from src.closed_loop.kpm_pairing import DEFAULT_PAIR_WINDOW_S, pair_complete, pair_gap_s


def _entry(node_at=None, ues_at=None):
    e = {}
    if node_at is not None:
        e.update(node={"RRU.PrbUsedDl": 1}, node_sha256="n", node_at=node_at)
    if ues_at is not None:
        e.update(ues=[{"ue_id": 1}], ues_sha256="u", ues_at=ues_at)
    return e


def test_pair_of_the_same_period_triggers_in_either_order():
    assert pair_complete(_entry(node_at=100.0000, ues_at=100.0005))     # formato 1 e depois 3
    assert pair_complete(_entry(node_at=100.0005, ues_at=100.0000))     # entregues em ordem trocada
    assert pair_gap_s(_entry(node_at=100.0, ues_at=100.0005)) == 0.0005 or abs(
        pair_gap_s(_entry(node_at=100.0, ues_at=100.0005)) - 0.0005) < 1e-9


def test_first_message_of_a_new_period_does_not_trigger():
    # Semente 5012: formato 1 do período novo chega e os UEs ainda são do período anterior (~3,3 s antes)
    assert not pair_complete(_entry(node_at=103.32, ues_at=100.0))
    assert not pair_complete(_entry(node_at=100.0, ues_at=100.0 + DEFAULT_PAIR_WINDOW_S + 0.01))


def test_missing_half_does_not_trigger():
    assert not pair_complete(_entry(node_at=100.0))
    assert not pair_complete(_entry(ues_at=100.0))
    assert not pair_complete({})
    assert pair_gap_s({}) is None


def test_window_is_configurable():
    e = _entry(node_at=100.0, ues_at=100.8)
    assert not pair_complete(e) and pair_complete(e, window_s=1.0)
