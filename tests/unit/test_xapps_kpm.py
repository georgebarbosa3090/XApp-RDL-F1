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
from src.xapps.derivadas import EnergySavingDerivada, RogueDerivada, TrafficSteeringDerivada  # noqa: E402
from src.xapps.proprias import (Beamformer, CoverageCapacityOptimizer, EmbbThroughput, IsacRadar,  # noqa: E402
                                LoadBalancer, UeFairnessScheduler, UrllcSliceGuard)


class _T:
    on_result = None

    def send(self, p):
        return True


ALL = [UrllcSliceGuard, EnergySavingDerivada, TrafficSteeringDerivada, RogueDerivada, LoadBalancer, Beamformer,
       IsacRadar, EmbbThroughput, CoverageCapacityOptimizer, UeFairnessScheduler]


@pytest.mark.parametrize("cls", ALL)
def test_no_kpm_no_proposal(cls):
    assert cls(transport=_T()).decide(10.0) == []


def test_urllc_slice_guard_protects_urllc_and_relaxes():
    x = UrllcSliceGuard(transport=_T())
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
    from src.xapps.proprias import UrllcSliceGuard as Core

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
    assert lb.decide(1.0) == []                               # tempo de disparo (A3, 640 ms) começa
    out = lb.decide(1.8)
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
    assert lb.decide(1.0) == []
    assert [p["ue"] for p in lb.decide(1.8)] == [7]


def test_load_balancer_without_ue_that_hears_the_neighbor_does_not_move():
    lb = LoadBalancer(transport=_T(), neighbors={"gnb_0": ["gnb_1"], "gnb_1": ["gnb_0"]})
    s0 = CellSample("gnb_0", 0, load_pct=100)
    s0.ues = [UeKpi(str(i), "gnb_0", 5.0, {"gnb_0": -80.0, "gnb_1": -110.0}) for i in range(5)]
    lb.observe(s0)
    lb.observe(CellSample("gnb_1", 0, load_pct=0))
    assert lb.decide(1.0) == []


def _urllc(x, cell, delay):
    x.observe(CellSample(cell, 0, load_pct=50, slices={2: SliceKpi(ues=3, delay_ms=delay), 1: SliceKpi(ues=5)}))


def test_urllc_slice_guard_does_not_relax_while_delay_stays_near_the_limit():
    """S2, semente 16908 (comparativo das xApps, seção 3.2): protegido, o atraso da URLLC ficava em ~9 ms com limite
    de 10 ms; relaxar o levava acima do limite e o teto oscilava 25 -> 80 -> 25 % a cada ~1,4 s. Com a histerese
    (relaxar só abaixo de 0,7 × limite), a xApp mantém a proteção."""
    x = UrllcSliceGuard(transport=_T())
    _urllc(x, "gnb_0", 14.2)
    assert [p["value"] for p in x.decide(3.4)] == [25.0]
    for k in range(40):
        _urllc(x, "gnb_0", 9.0)
        assert x.decide(3.6 + 0.2 * k) == []


def test_urllc_slice_guard_doubles_relax_windows_when_relaxing_recreates_the_risk():
    x = UrllcSliceGuard(transport=_T())
    _urllc(x, "gnb_0", 20.0)
    x.decide(0.2)
    for k in range(5):
        _urllc(x, "gnb_0", 4.0)
        out = x.decide(0.4 + 0.2 * k)
    assert [p["value"] for p in out] == [80.0]
    _urllc(x, "gnb_0", 30.0)                                   # relaxar recriou o risco
    assert [p["value"] for p in x.decide(1.6)] == [25.0]
    got = []
    for k in range(10):
        _urllc(x, "gnb_0", 4.0)
        got.append([p["value"] for p in x.decide(1.8 + 0.2 * k)])
    assert got == [[]] * 9 + [[80.0]]                         # agora exige 10 janelas calmas


def test_urllc_slice_guard_proposes_again_after_refusal():
    """S2/B3, semente 16908: a proposta de 25 % recusada (histerese da RDL) deixava a célula marcada como protegida e
    a xApp parava de propor. Com a recusa tratada, ela volta a propor na janela seguinte."""
    x = UrllcSliceGuard(transport=_T())
    _urllc(x, "gnb_0", 37.0)
    assert [p["value"] for p in x.decide(4.8)] == [25.0]
    x.on_result({"node_id": "gnb_0", "parameter": "PRB_QUOTA", "reason": "NOT_SELECTED"})
    _urllc(x, "gnb_0", 98.0)
    assert [p["value"] for p in x.decide(5.0)] == [25.0]
    _urllc(x, "gnb_0", 98.0)
    assert x.decide(5.2) == []                                # aplicada: não repete


def test_slice_of_each_ue_comes_from_the_kpm():
    """Desde 2026-11-21 o ns-3 reporta a fatia de cada UE (campo sst); o mapa do closed_loop.json só vale para
    registros antigos."""
    from src.greenran.common import samples_from_closed_loop
    kpm = {"t": 1.0, "cells": [{"gnb": 0, "cell_id": 1, "prb_util": 0.5}],
           "ues": [{"ue": 0, "gnb": 0, "connected": True, "sst": 2, "thp_mbps": 1.0, "delay_ms": 12.0},
                   {"ue": 1, "gnb": 0, "connected": True, "sst": 1, "thp_mbps": 9.0, "delay_ms": 3.0}]}
    s = samples_from_closed_loop(kpm, {0: 1, 1: 1})["gnb_0"]  # o mapa diz o contrário: vale o KPM
    assert s.slices[2].ues == 1 and s.slices[2].delay_ms == 12.0 and s.slices[1].ues == 1
    old = {"t": 1.0, "cells": kpm["cells"], "ues": [{k: v for k, v in u.items() if k != "sst"} for u in kpm["ues"]]}
    assert sorted(samples_from_closed_loop(old, {0: 2, 1: 1})["gnb_0"].slices) == [1, 2]
    assert samples_from_closed_loop(old)["gnb_0"].slices == {}


def test_load_balancer_waits_time_to_trigger_and_restarts_it_when_the_condition_drops():
    lb = LoadBalancer(transport=_T(), neighbors={"gnb_0": ["gnb_1"], "gnb_1": ["gnb_0"]})
    near = [UeKpi("1", "gnb_0", 5.0, {"gnb_0": -90.0, "gnb_1": -91.0})]
    far = [UeKpi("1", "gnb_0", 5.0, {"gnb_0": -90.0, "gnb_1": -99.0})]
    lb.observe(CellSample("gnb_1", 0, load_pct=0))
    for t, ues in ((1.0, near), (1.4, far), (1.6, near), (2.0, near)):
        s0 = CellSample("gnb_0", t, load_pct=100)
        s0.ues = ues
        lb.observe(s0)
        assert lb.decide(t) == [], t                          # a condição caiu em 1,4 s: o TTT recomeçou em 1,6 s
    s0 = CellSample("gnb_0", 2.4, load_pct=100)
    s0.ues = near
    lb.observe(s0)
    assert [p["ue"] for p in lb.decide(2.4)] == [1]


def test_load_balancer_prb_branch_is_off_by_default():
    lb = LoadBalancer(transport=_T(), neighbors={"gnb_0": ["gnb_1"], "gnb_1": ["gnb_0"]})
    lb.observe(CellSample("gnb_0", 0, load_pct=40))
    lb.observe(CellSample("gnb_1", 0, load_pct=20))
    assert lb.decide(1.0) == []
    lb.DEFAULTS = {**LoadBalancer.DEFAULTS, "lb_open_cap_enabled": True}
    assert [(p["parameter"], p["value"]) for p in lb.decide(2.0)] == [("PRB_QUOTA", 90.0)]


def test_beamformer_uses_the_power_measured_in_the_kpm():
    """docs/16 §10.16: nos cenários do ns-3 a gNB transmite com 4 dBm (padrão do 5G-LENA). Com SINR baixo, o
    Beamformer sobe a partir da potência medida, até a nominal mais 6 dB; com nominal e máximo iguais (antes), nunca
    propunha."""
    bf = Beamformer(transport=_T())
    s = CellSample("gnb_0", 0, tx_power_dbm=4.0)
    s.ues = [UeKpi("1", "gnb_0", 2.0, {})]
    bf.observe(s)
    assert [p["value"] for p in bf.decide(1)] == [7.0]
    s2 = CellSample("gnb_0", 1, tx_power_dbm=9.0)
    s2.ues = [UeKpi("1", "gnb_0", 2.0, {})]
    bf.observe(s2)
    assert [p["value"] for p in bf.decide(2)] == [10.0]       # nominal 4 + 6 dB
    s3 = CellSample("gnb_0", 2, tx_power_dbm=10.0)
    s3.ues = [UeKpi("1", "gnb_0", 25.0, {})]
    bf.observe(s3)
    assert [p["value"] for p in bf.decide(3)] == [4.0]        # SINR folgado: volta à nominal


def test_energysaver_never_raises_power_when_it_reduces():
    """docs/16 §10.16: com a gNB a 4 dBm, a "redução" fixa para 30 dBm era um aumento de 26 dB. Com a potência no
    KPM, o alvo fica ao menos 3 dB abaixo dela; uma recusa desfaz a marcação e a xApp volta a propor."""
    from src.greenran.energysaver_greenran import EnergySaver
    es = EnergySaver(transport=_T(), neighbors={}, hour_of=lambda t: 12)
    es.observe(CellSample("gnb_0", 0.0, load_pct=20.0, tx_power_dbm=4.0))
    es.observe(CellSample("gnb_0", 10.0, load_pct=20.0, tx_power_dbm=4.0))
    (p,) = [q for q in es.decide(10.0) if q["parameter"] == "TX_POWER"]
    assert p["value"] == 1.0
    es.on_result({"node_id": "gnb_0", "parameter": "TX_POWER", "reason": "NOT_SELECTED"})
    assert [q["value"] for q in es.decide(11.0) if q["parameter"] == "TX_POWER"] == [1.0]
    es.observe(CellSample("gnb_0", 12.0, load_pct=40.0, tx_power_dbm=1.0))
    assert [q["value"] for q in es.decide(12.0) if q["parameter"] == "TX_POWER"] == [4.0]   # restaura a medida


def test_ranslicer_treats_zero_throughput_with_prb_in_use_as_missing_measure():
    """NORI S8 (docs/16 §10.6): o KPM traz vazão por UE sempre 0, e a RANSlicer se via sempre em risco e pedia o
    máximo. Vazão 0 com PRB em uso é medida ausente: a célula não é decidida."""
    from src.greenran.ranslicer_greenran import RanSlicer
    rs = RanSlicer(transport=_T())
    rs.observe(CellSample("gnb_0", 0, load_pct=60.0, slices={1: SliceKpi(thp_mbps=0.0, prb_used=30.0, ues=4)}))
    assert rs.decide(1.0) == []
    rs.observe(CellSample("gnb_0", 1, load_pct=60.0, slices={1: SliceKpi(thp_mbps=20.0, prb_used=30.0, ues=4)}))
    assert [p["parameter"] for p in rs.decide(2.0)] == ["PRB_QUOTA"]


def _cell(cell, t, tx, sinrs, load=50.0, sst=None, thps=None):
    s = CellSample(cell, t, load_pct=load, tx_power_dbm=tx)
    s.ues = [UeKpi(str(i), cell, v, {cell: -100.0}, (thps or [1.0] * len(sinrs))[i], sst)
             for i, v in enumerate(sinrs)]
    return s


def test_cco_raises_power_on_coverage_hole_and_returns_toward_nominal():
    """docs/16 §10.17: CCO (TS 28.313) contra a EnergySaver em TX_POWER, como no par CCO × ES de Wadud et al."""
    x = CoverageCapacityOptimizer(transport=_T())
    x.observe(_cell("gnb_0", 0, 4.0, [-3.0, -2.0, 5.0, 8.0]))          # 50 % dos UEs na borda
    assert [p["value"] for p in x.decide(1.0)] == [7.0]
    x.observe(_cell("gnb_0", 1, 7.0, [-3.0, -2.0, 5.0, 8.0]))
    assert x.decide(2.0) == []                                          # 2 s entre propostas da célula
    assert [p["value"] for p in x.decide(3.0)] == [10.0]                # até a nominal + 6 dB
    x.observe(_cell("gnb_0", 4, 10.0, [15.0, 16.0, 18.0, 20.0]))       # cobertura folgada
    assert [p["value"] for p in x.decide(5.0)] == [7.0]
    x.observe(_cell("gnb_0", 6, 4.0, [15.0, 16.0, 18.0, 20.0]))
    assert x.decide(7.0) == []                                          # já na nominal


def test_ue_scheduler_switches_between_fairness_and_efficiency():
    x = UeFairnessScheduler(transport=_T())
    x.observe(_cell("gnb_0", 0, 4.0, [5.0] * 4, load=90.0, sst=1, thps=[20.0, 0.5, 0.4, 0.3]))
    (p,) = x.decide(1.0)
    assert (p["parameter"], p["value"]) == ("SCHEDULER_WEIGHT", 20.0)  # Jain baixo: mais justiça
    x.observe(_cell("gnb_0", 2, 4.0, [5.0] * 4, load=90.0, sst=1, thps=[5.0, 5.1, 4.9, 5.0]))
    assert [q["value"] for q in x.decide(3.0)] == [100.0]               # justo e carregado: PF clássico
    assert x.decide(6.0) == []                                          # mesmo modo: não repete
    x.on_result({"node_id": "gnb_0", "parameter": "SCHEDULER_WEIGHT", "reason": "NOT_SELECTED"})
    assert [q["value"] for q in x.decide(9.0)] == [100.0]               # recusa: volta a propor


def test_ue_scheduler_ignores_other_slices():
    x = UeFairnessScheduler(transport=_T())
    x.observe(_cell("gnb_0", 0, 4.0, [5.0] * 3, load=90.0, sst=2, thps=[20.0, 0.1, 0.1]))
    assert x.decide(1.0) == []
