"""
Melhorias da EnergySaver-GreenRAN (2026-11-13; docs/12 §3 e docs/16, comparação com o ES Orange):
destino da evacuação pela cobertura dos UEs, confirmação da evacuação, permanência mínima, histerese de
potência, hora em UTC com deslocamento da política e amostras a partir do KPM da malha fechada.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.greenran.common import CellSample, SliceKpi, UeKpi, samples_from_closed_loop  # noqa: E402
from src.greenran.energysaver_greenran import ACTIVE, EVACUATING, SLEEP, EnergySaver  # noqa: E402

NEIGH = {"gnb_0": ["gnb_1", "gnb_2"], "gnb_1": ["gnb_0", "gnb_2"], "gnb_2": ["gnb_0", "gnb_1"]}


class _Transport:
    def __init__(self):
        self.on_result = None
        self.sent = []

    def send(self, p):
        self.sent.append(p)
        return True

    def start(self):
        return "none"

    def stop(self):
        pass

    def stats(self):
        return {}


def saver(**pol):
    x = EnergySaver(transport=_Transport(), neighbors=NEIGH, hour_of=lambda t: 2)
    x.DEFAULTS = {**EnergySaver.DEFAULTS, **pol}
    return x


def cell(cid, load, ues=0, t=0.0, signal=None):
    s = CellSample(cid, t, load_pct=load)
    if signal is not None:
        s.ues = [UeKpi(f"{cid}-u{i}", cid, 10.0, rsrp) for i, rsrp in enumerate(signal)]
    elif ues:
        s.slices = {1: SliceKpi(ues=ues)}
    return s


def test_host_chosen_by_coverage_of_all_ues():
    x = saver()
    x.observe(cell("gnb_0", 30))
    x.observe(cell("gnb_2", 20))
    # gnb_1 tem 2 UEs: gnb_0 é menos carregada, mas não cobre o segundo UE; gnb_2 cobre os dois
    x.observe(cell("gnb_1", 5, signal=[{"gnb_1": -80, "gnb_0": -95, "gnb_2": -100},
                                       {"gnb_1": -82, "gnb_0": -118, "gnb_2": -104}]))
    (p,) = x.step(now=100)
    assert (p["node_id"], p["parameter"], p["value"]) == ("gnb_1", "HANDOVER", 2.0)
    assert x.state["gnb_1"] == EVACUATING
    assert x.decisions[-1]["decision"] == "host-by-coverage"


def test_no_evacuation_when_no_neighbor_covers_every_ue():
    x = saver()
    x.observe(cell("gnb_0", 30))
    x.observe(cell("gnb_2", 20))
    x.observe(cell("gnb_1", 5, signal=[{"gnb_1": -80, "gnb_0": -120, "gnb_2": -100},
                                       {"gnb_1": -82, "gnb_0": -95, "gnb_2": -125}]))
    assert all(p["parameter"] != "HANDOVER" for p in x.step(now=100))
    assert x.state["gnb_1"] == ACTIVE
    assert any(d["decision"] == "keep" for d in x.decisions)


def test_sleep_only_after_cell_is_empty_and_abort_after_timeout():
    x = saver(es_evacuation_timeout_s=5.0, es_min_dwell_s=0.0)
    x.observe(cell("gnb_0", 30))
    x.observe(cell("gnb_2", 25))
    x.observe(cell("gnb_1", 5, ues=3))
    (p,) = x.step(now=0)
    assert p["parameter"] == "HANDOVER"
    x.observe(cell("gnb_1", 5, ues=1))                 # ainda há UE: não desliga
    assert x.step(now=2) == [] and x.state["gnb_1"] == EVACUATING
    x.observe(cell("gnb_1", 5, ues=1))
    assert x.step(now=6) == []                         # prazo vencido: aborta, sem nova tentativa no período
    assert x.state["gnb_1"] == ACTIVE and x.decisions[-1]["decision"] == "abort"
    assert all(p["parameter"] != "HANDOVER" for p in x.step(now=8))    # espera de 5 s depois do aborto
    assert [p["parameter"] for p in x.step(now=11)] == ["HANDOVER"]    # nova tentativa


def test_sleep_confirmed_when_empty():
    x = saver(es_min_dwell_s=0.0)
    x.observe(cell("gnb_0", 30))
    x.observe(cell("gnb_2", 25))
    x.observe(cell("gnb_1", 5, ues=3))
    x.step(now=0)
    x.observe(cell("gnb_1", 0, ues=0))
    (p,) = x.step(now=1)
    assert (p["parameter"], p["value"]) == ("CELL_STATE", 0.0) and x.state["gnb_1"] == SLEEP


def test_min_dwell_blocks_planned_wake_but_not_capacity_wake():
    x = saver(es_min_dwell_s=60.0, es_sleep_end_hour=6)
    x.observe(cell("gnb_0", 30))
    x.observe(cell("gnb_2", 25))
    x.observe(cell("gnb_1", 0))
    (p,) = x.step(now=0)
    assert p["parameter"] == "CELL_STATE" and x.state["gnb_1"] == SLEEP
    x.hour_of = lambda t: 7                           # fim da janela, mas dentro da permanência
    assert all(q["parameter"] != "CELL_STATE" for q in x.step(now=10))
    x.observe(cell("gnb_0", 80))                      # vizinha quente: religa já
    (q,) = x.step(now=11)
    assert (q["node_id"], q["parameter"], q["value"]) == ("gnb_1", "CELL_STATE", 1.0)


def test_tx_power_proposed_once_and_restored_with_hysteresis():
    x = saver(es_nominal_tx_power_dbm=43.0)
    x.hour_of = lambda t: 14                          # fora da janela de sono
    x.observe(cell("gnb_0", 20))
    assert [p["value"] for p in x.step(now=0)] == [30.0]
    assert x.step(now=1) == []                        # não repete
    x.observe(cell("gnb_0", 33))                      # 2*15 = 30, mais 5 de histerese = 35: ainda reduzida
    assert x.step(now=2) == []
    x.observe(cell("gnb_0", 36))
    assert [p["value"] for p in x.step(now=3)] == [43.0]


def test_hour_uses_utc_with_policy_offset():
    x = EnergySaver(transport=_Transport(), neighbors=NEIGH)
    assert x.hour_of(0) == 21                         # 00h UTC com deslocamento -3
    x.DEFAULTS = {**EnergySaver.DEFAULTS, "es_utc_offset_h": 0}
    assert x.hour_of(3600 * 5) == 5


def test_samples_from_closed_loop_kpm():
    kpm = {"t": 15.8, "cells": [{"gnb": 0, "cell_id": 1, "prb_util": 0.02}, {"gnb": 1, "cell_id": 2, "prb_util": 0.5}],
           "ues": [{"ue": 0, "cell_id": 2, "gnb": 1, "connected": True, "thp_mbps": 0.016, "sinr_db": 14.6,
                    "rsrp_dbm": {"1": -112.07, "2": -109.77}},
                   {"ue": 1, "cell_id": 1, "gnb": 0, "connected": False, "rsrp_dbm": {}}]}
    s = samples_from_closed_loop(kpm)
    assert s["gnb_1"].load_pct == 50.0 and s["gnb_0"].load_pct == 2.0
    assert s["gnb_1"].total_ues == 1 and s["gnb_0"].total_ues == 0
    assert s["gnb_1"].ues[0].rsrp_dbm == {"gnb_0": -112.07, "gnb_1": -109.77} and s["gnb_1"].has_ue_signal
