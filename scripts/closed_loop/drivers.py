#!/usr/bin/env python3
"""
Drivers de xApp da malha fechada (docs/16 §3 e §4).

Cada driver recebe o KPM de uma janela (dicionário vindo do ns-3, rdl-nr-common.h) e devolve as
propostas que a xApp emitiu ao ver esse KPM, no formato do executor:
    {"t", "xapp_id", "gnb", "parameter", "value", "priority", "ue", "id"}

- ReplayDriver: reproduz as propostas fixas do catálogo (malha aberta dentro da malha fechada).
  Serve ao gate E1: com os mesmos instantes, o ns-3 em passo travado tem de dar o mesmo resultado
  do modo de cronograma. Não é xApp: as campanhas com xApps reais não usam este driver.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List


class XAppDriver:
    """Interface: on_hello(topologia) uma vez; on_kpm(kpm) a cada janela; close() no fim."""

    name = "driver"

    def on_hello(self, hello: Dict[str, Any]) -> None:
        pass

    def on_kpm(self, kpm: Dict[str, Any]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def close(self) -> None:
        pass


class ReplayDriver(XAppDriver):
    """Propostas fixas do catálogo, entregues na janela em que foram emitidas."""

    name = "replay"

    def __init__(self, events: List[Dict[str, Any]], window: float):
        self.window = window
        self.by_window: Dict[int, List[Dict[str, Any]]] = {}
        for e in events:
            self.by_window.setdefault(int(math.floor(e["t"] / window + 1e-9)), []).append(e)

    def on_kpm(self, kpm: Dict[str, Any]) -> List[Dict[str, Any]]:
        # KPM em t fecha a janela k-1 = [t - w, t): entrega as propostas emitidas nela.
        k = int(round(float(kpm["t"]) / self.window)) - 1
        return list(self.by_window.get(k, []))
