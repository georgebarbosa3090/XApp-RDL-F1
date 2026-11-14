"""
Cadeia do Traffic Steering original (o-ran-sc/ric-app-ts, sem alteração) na malha fechada (docs/16, gate E3),
sem ns-3: o teste faz o papel do orquestrador e entrega janelas de KPM sintéticas ao adaptador, que emula o
AD (30003) e o QP (30002) por RMR e recebe o HandOff do TS por REST.

O teste de ponta a ponta requer o ts_xapp compilado por xapps-originais/ts/build.sh (Ubuntu/WSL) e é pulado
sem ele; os testes da predição e da conversão em proposta rodam em qualquer sistema.
"""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE = Path(os.environ.get("XAPPS_ORIGINAIS", os.path.expanduser("~/xapps-originais")))
BIN = BASE / "build-ts" / "src" / "ts_xapp" / "ts_xapp"
GNBS = [{"gnb": 0, "cell_id": 1}, {"gnb": 1, "cell_id": 2}]


def _ue(u, cell, thp, sinr, rsrp):
    return {"ue": u, "cell_id": cell, "gnb": cell - 1, "connected": True, "thp_mbps": thp, "delay_ms": 5.0,
            "sinr_db": sinr, "rsrp_dbm": rsrp}


# UE 0: vazão baixa e a célula 2 medida 10 dB melhor -> o TS deve pedir HandOff 1 -> 2
# UE 1: vazão baixa, mas a servidora é a melhor -> o TS mantém
# UE 2: vazão normal -> não é anômalo, o TS nem é consultado
UES = [_ue(0, 1, 0.05, 3.0, {"1": -100.0, "2": -90.0}),
       _ue(1, 1, 0.05, 10.0, {"1": -90.0, "2": -100.0}),
       _ue(2, 2, 5.0, 20.0, {"2": -80.0, "1": -105.0})]


def test_prediction_puts_serving_cell_first_and_scales_neighbors_by_shannon():
    from scripts.closed_loop.ts_driver import TsOriginalDriver

    drv = TsOriginalDriver(workdir=".")
    p0 = drv._prediction(UES[0])["0"]
    assert list(p0)[0] == "1" and p0["1"] == [50, 0]
    assert p0["2"][0] > p0["1"][0] * 1.05                     # vizinha melhor -> passa o limiar de 5 %
    p1 = drv._prediction(UES[1])["1"]
    assert p1["2"][0] < p1["1"][0]                            # vizinha pior -> o TS mantém


def test_handoff_post_becomes_ue_handover_proposal():
    from scripts.closed_loop.ts_driver import TsOriginalDriver

    drv = TsOriginalDriver(workdir=".")
    drv.gnb_of_cell = {1: 0, 2: 1}
    prop = drv._to_proposal({"command": "HandOff", "ue": "0", "fromCell": "1", "toCell": "2"}, 2.0)
    assert prop["parameter"] == "HANDOVER" and prop["gnb"] == 0 and prop["value"] == 1.0 and prop["ue"] == 0
    assert prop["xapp_id"] == "traffic_steering" and prop["xapp_impl"] == "original"
    assert drv._to_proposal({"ue": "0", "fromCell": "9", "toCell": "2"}, 2.0) is None   # célula desconhecida


def test_relative_anomaly_marks_only_degradation_of_the_ue_itself():
    from scripts.closed_loop.ts_driver import TsOriginalDriver

    drv = TsOriginalDriver(workdir=".", anomaly_mode="relativo", anomaly_drop=0.5)
    low = {"0": _ue(0, 1, 0.01, 3.0, {}), "1": _ue(1, 1, 0.01, 3.0, {})}   # tráfego leve, estável
    assert drv._anomalous(low) == []                                        # 1ª janela: só a média
    assert drv._anomalous(low) == []                                        # leve não é anomalia
    low["1"] = _ue(1, 1, 0.002, 3.0, {})                                    # UE 1 cai a 20 % da própria média
    assert drv._anomalous(low) == ["1"]
    assert TsOriginalDriver(workdir=".")._anomalous(low) == ["0", "1"]     # absoluto (0,2 Mbps): todos


@pytest.mark.skipif(os.name == "nt" or not BIN.exists(), reason="requer o ts_xapp compilado no Linux/WSL")
def test_ts_original_hands_off_only_the_ue_with_a_better_neighbor(tmp_path):
    from scripts.closed_loop.ts_driver import TsOriginalDriver

    drv = TsOriginalDriver(workdir=str(tmp_path), threshold_pct=5)
    drv.on_hello({"gnbs": GNBS, "window": 0.2})
    props = []
    try:
        for k in range(5, 10):                               # t = 1.0 ... 1.8 s (após a observação mínima)
            props += drv.on_kpm({"type": "kpm", "t": round(0.2 * k, 3), "window": 0.2, "cells": GNBS, "ues": UES})
    finally:
        drv.close()
    log = (tmp_path / "ts_stdout.log").read_text(errors="replace")
    assert "Setting Threshold for A1-P value: 5%" in log      # a política A1 20008 chegou ao TS
    assert "HandOff request is" in log                        # o TS decidiu e chamou o REST
    assert props and all(p["ue"] == 0 and p["gnb"] == 0 and p["value"] == 1.0 for p in props)
    assert 'The current serving cell "1" is the best one' in log    # UE 1 mantido pelo próprio TS
