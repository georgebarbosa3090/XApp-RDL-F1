"""
Núcleos das xApps derivadas e próprias (src/xapps): toda proposta vem do KPM (decisão de 2026-11-13).
Sem amostra, nenhuma xApp propõe; com o KPM descrito, cada uma propõe o controle do seu papel.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "reference-xapps" / "common"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.greenran.common import CellSample, SliceKpi, UeKpi  # noqa: E402
from src.xapps.derivadas import (EnergySavingDerivada, RogueDerivada, TrafficSteeringDerivada,  # noqa: E402
                                 XSliceDerivada)
from src.xapps.proprias import Beamformer, EmbbThroughput, IsacRadar, LoadBalancer  # noqa: E402


class _T:
    on_result = None

    def send(self, p):
        return True


ALL = [XSliceDerivada, EnergySavingDerivada, TrafficSteeringDerivada, RogueDerivada, LoadBalancer, Beamformer,
       IsacRadar, EmbbThroughput]


@pytest.mark.parametrize("cls", ALL)
def test_no_kpm_no_proposal(cls):
    assert cls(transport=_T()).decide(10.0) == []


def test_xslice_protects_urllc_and_relaxes():
    x = XSliceDerivada(transport=_T())
    x.observe(CellSample("gnb_0", 0, load_pct=50, slices={2: SliceKpi(ues=3, delay_ms=25.0), 1: SliceKpi(ues=5)}))
    (p,) = x.decide(1.0)
    assert (p["parameter"], p["value"], p["priority"]) == ("PRB_QUOTA", 25.0, 90)
    assert x.decide(1.2) == []                                # não repete
    for k in range(5):
        x.observe(CellSample("gnb_0", 0, load_pct=50, slices={2: SliceKpi(ues=3, delay_ms=4.0)}))
        out = x.decide(2.0 + k)
    assert [q["value"] for q in out] == [80.0]


def test_energy_saving_derivada_reduces_and_restores_power():
    x = EnergySavingDerivada(transport=_T())
    x.observe(CellSample("gnb_1", 0, load_pct=5))
    assert [p["value"] for p in x.decide(1)] == [30.0]
    x.observe(CellSample("gnb_1", 0, load_pct=60))
    assert [p["value"] for p in x.decide(2)] == [43.0]


def test_traffic_steering_derivada_moves_cell_to_better_neighbor():
    x = TrafficSteeringDerivada(transport=_T())
    s = CellSample("gnb_0", 0, load_pct=40)
    s.ues = [UeKpi(str(i), "gnb_0", 5.0, {"gnb_0": -100.0, "gnb_1": -90.0}) for i in range(4)]
    x.observe(s)
    (p,) = x.decide(10.0)
    assert (p["node_id"], p["parameter"], p["value"]) == ("gnb_0", "HANDOVER", 1.0)
    assert x.decide(11.0) == []                               # tempo mínimo entre propostas


def test_rogue_alternates_out_of_bounds_values_when_traffic_exists():
    x = RogueDerivada(transport=_T())
    x.observe(CellSample("gnb_0", 0, load_pct=10))
    vals = [x.decide(t)[0]["value"] for t in (0.0, 2.0, 4.0)]
    assert vals == [45.0, 5.0, 150.0]


def test_load_balancer_beamformer_isac_embb():
    lb = LoadBalancer(transport=_T(), neighbors={"gnb_0": ["gnb_1"], "gnb_1": ["gnb_0"]})
    lb.observe(CellSample("gnb_0", 0, load_pct=80))
    lb.observe(CellSample("gnb_1", 0, load_pct=20))
    assert [(p["node_id"], p["parameter"], p["value"]) for p in lb.decide(1)] == [("gnb_0", "HANDOVER", 1.0)]

    bf = Beamformer(transport=_T(), )
    bf.DEFAULTS = {**Beamformer.DEFAULTS, "bf_nominal_tx_dbm": 37.0}
    s = CellSample("gnb_0", 0)
    s.ues = [UeKpi("1", "gnb_0", 4.0, {})]
    bf.observe(s)
    assert [p["value"] for p in bf.decide(1)] == [40.0]

    isac = IsacRadar(transport=_T())
    isac.observe(CellSample("gnb_0", 0, load_pct=30))
    assert [p["value"] for p in isac.decide(0)] == [40.0] and isac.decide(1) == []

    em = EmbbThroughput(transport=_T())
    em.observe(CellSample("gnb_0", 0, slices={1: SliceKpi(ues=4, thp_mbps=5.0)}))
    assert [p["value"] for p in em.decide(1)] == [80.0]


def test_reference_runtime_loop_uses_kpm_core():
    import kpm_runtime
    from src.xapps.derivadas import XSliceDerivada as Core

    class Owner:
        running = False
        transport = _T()

    core = kpm_runtime.make_core(Core, Owner.transport)
    kpm_runtime.run_kpm_loop(Owner, core, 0.0)            # sem SUBMGR_URL e sem KPM: sai sem propor
    assert core.decide(0.0) == []


def test_load_balancer_moves_part_of_the_ues_with_best_neighbor_signal():
    """docs/16 §10.11 e §10.13: com RSRP por UE, o Load Balancer transfere só parte dos UEs (os de menor diferença
    de RSRP, com a vizinha no máximo 3 dB pior), um pedido por UE, e não a célula inteira."""
    lb = LoadBalancer(transport=_T(), neighbors={"gnb_0": ["gnb_1"], "gnb_1": ["gnb_0"]})
    s0 = CellSample("gnb_0", 0, load_pct=100)
    # diferença de RSRP servidora - vizinha: UE i tem i - 2 dB (UEs 0 e 1 ouvem a vizinha melhor); os UEs 6..9
    # (4 a 7 dB) não ouvem a vizinha o bastante
    s0.ues = [UeKpi(str(i), "gnb_0", 5.0, {"gnb_0": -90.0, "gnb_1": -90.0 - (i - 2)}) for i in range(10)]
    lb.observe(s0)
    lb.observe(CellSample("gnb_1", 0, load_pct=10))
    out = lb.decide(1.0)
    # metade da diferença (90 pontos) sobre 100 % de carga: 45 % de 10 UEs -> 5, limitado a lb_max_ues = 4
    assert [(p["node_id"], p["parameter"], p["value"], p["ue"]) for p in out] == [
        ("gnb_0", "HANDOVER", 1.0, ue) for ue in (0, 1, 2, 3)]
    assert lb.decide(2.0) == []                               # espera de 5 s por célula


def test_load_balancer_does_not_move_ue_to_a_much_weaker_neighbor():
    """docs/16 §10.12 e §10.13: no S5 (semente 16907), o UE 2 ouvia a vizinha 6,5 dB pior e o UE 14, 3,3 dB pior;
    transferidos, perdiam a conexão lá. Com a vizinha mais de 3 dB pior, o Load Balancer não transfere."""
    lb = LoadBalancer(transport=_T(), neighbors={"gnb_0": ["gnb_1"], "gnb_1": ["gnb_0"]})
    s0 = CellSample("gnb_0", 0, load_pct=100)
    s0.ues = [UeKpi("2", "gnb_0", 5.0, {"gnb_0": -122.6, "gnb_1": -129.1}),
              UeKpi("14", "gnb_0", 5.0, {"gnb_0": -130.0, "gnb_1": -133.3}),
              UeKpi("7", "gnb_0", 5.0, {"gnb_0": -120.0, "gnb_1": -122.7})]
    lb.observe(s0)
    lb.observe(CellSample("gnb_1", 0, load_pct=0))
    assert [p["ue"] for p in lb.decide(1.0)] == [7]


def test_load_balancer_without_ue_that_hears_the_neighbor_does_not_move():
    lb = LoadBalancer(transport=_T(), neighbors={"gnb_0": ["gnb_1"], "gnb_1": ["gnb_0"]})
    s0 = CellSample("gnb_0", 0, load_pct=100)
    s0.ues = [UeKpi(str(i), "gnb_0", 5.0, {"gnb_0": -80.0, "gnb_1": -110.0}) for i in range(5)]
    lb.observe(s0)
    lb.observe(CellSample("gnb_1", 0, load_pct=0))
    assert lb.decide(1.0) == []
