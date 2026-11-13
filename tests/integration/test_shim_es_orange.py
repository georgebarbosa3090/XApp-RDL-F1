"""
Cadeia do ES Orange original via libe42_shim (docs/16, gate E2), sem ns-3: o teste faz o papel do
orquestrador e entrega janelas de KPM sintéticas ao código original, sem alteração.

Documenta um defeito do original (docs/16, decisão de 2026-11-13): em ``add_UE`` (linha 177 de
xapp_es_with_cell_util.c), ``numOfConnectedUEs`` soma 1 a cada indicação, e não a cada UE novo. Com
relatórios periódicos, a célula com um único UE passa a contar 2 na segunda indicação, e o critério
"no máximo 1 UE" nunca é atendido na verificação, feita a cada 5 s. Por isso a xApp recebe e registra
o KPM (indicação chega pelo shim), mas não emite controle. O papel de energia nos cenários fica com a
EnergySaver-GreenRAN.

Requer o binário compilado por xapps-originais/shim/build.sh (Ubuntu/WSL); é pulado sem ele.
"""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BIN = Path(os.environ.get("RDL_SHIM_BUILD", os.path.expanduser("~/xapps-originais/shim-build"))) / \
    "xapp_es_with_cell_util_rdl"
pytestmark = pytest.mark.skipif(os.name == "nt" or not BIN.exists(), reason="requer o shim compilado no Linux/WSL")


def kpm(t, ues):
    return {"type": "kpm", "t": t, "window": 0.2,
            "cells": [{"gnb": 0, "cell_id": 1}, {"gnb": 1, "cell_id": 2}, {"gnb": 2, "cell_id": 3}], "ues": ues}


def test_es_orange_receives_kpm_but_never_acts_due_to_counter_defect(tmp_path):
    from scripts.closed_loop.flexric_driver import FlexricXAppDriver

    drv = FlexricXAppDriver("es-orange", "energy_saving", str(BIN), "es", priority=60, workdir=str(tmp_path))
    drv.on_hello({"gnbs": [{"gnb": 0, "cell_id": 1}, {"gnb": 1, "cell_id": 2}, {"gnb": 2, "cell_id": 3}], "window": 0.2})
    # célula 1 com 3 UEs; célula 2 com 1 UE, que mede a célula 3 melhor que a 1
    ues = [{"ue": u, "cell_id": 1, "gnb": 0, "connected": True, "thp_mbps": 1.0, "delay_ms": 5.0, "sinr_db": 15.0,
            "rsrp_dbm": {"1": -80.0, "2": -100.0, "3": -105.0}} for u in range(3)]
    ues.append({"ue": 3, "cell_id": 2, "gnb": 1, "connected": True, "thp_mbps": 1.0, "delay_ms": 5.0, "sinr_db": 12.0,
                "rsrp_dbm": {"2": -90.0, "3": -92.0, "1": -110.0}})
    props = []
    try:
        for k in range(1, 80):                       # 16 s simulados: o ES verifica a cada 5 s
            props += drv.on_kpm(kpm(round(0.2 * k, 3), ues))
    finally:
        drv.close()
    log = (tmp_path / "xapp_stdout.log").read_text(errors="replace")
    assert "Serving Cell 2 - UE 0: 12.00 dB" in log          # a indicação chegou ao código original
    assert "New neighbor cell 3 added for UE 0" in log        # e as vizinhas foram registradas
    assert props == [] and drv.log == []                      # mas nenhuma célula é marcada (defeito do contador)
