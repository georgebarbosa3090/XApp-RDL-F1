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
from typing import Any, Dict, List, Optional


class XAppDriver:
    """Interface: on_hello(topologia) uma vez; on_kpm(kpm) a cada janela; close() no fim."""

    name = "driver"

    def on_hello(self, hello: Dict[str, Any]) -> None:
        pass

    def on_kpm(self, kpm: Dict[str, Any]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def on_decision(self, selected_ids) -> None:
        """Ids selecionados pelo baseline na janela (para devolver recusas à xApp)."""

    def close(self) -> None:
        pass


class _NullTransport:
    """Transporte em memória: na malha fechada a proposta vai ao orquestrador, não ao RMR."""

    def __init__(self):
        self.on_result = None

    def send(self, proposal):
        return True

    def start(self):
        return "none"

    def stop(self):
        pass

    def stats(self):
        return {}


class PythonXAppDriver(XAppDriver):
    """
    Uma xApp do projeto (núcleo ``GreenRanXApp``: GreenRAN, derivadas, próprias) na malha fechada.

    A cada janela recebe o KPM do ns-3 como amostras por célula (``samples_from_closed_loop``), decide pelo
    próprio ``decide(t)`` e devolve as propostas no formato do executor. As propostas não selecionadas
    voltam à xApp como recusa (``on_result``), como faria o RMR 30001.
    """

    def __init__(self, name: str, app, ue_sst: Optional[Dict[int, int]] = None, xapp_impl: str = "propria"):
        self.name = name
        self.app = app
        self.ue_sst = ue_sst
        self.xapp_impl = xapp_impl
        self._mine: Dict[str, Dict[str, Any]] = {}
        self._seq = 0

    def on_kpm(self, kpm: Dict[str, Any]) -> List[Dict[str, Any]]:
        from src.greenran.common import samples_from_closed_loop
        t = float(kpm["t"])
        for s in samples_from_closed_loop(kpm, self.ue_sst).values():
            self.app.observe(s)
        out = []
        for p in self.app.decide(t):
            node = str(p["node_id"])
            gnb = int(node.rsplit("_", 1)[-1])
            self._seq += 1
            pid = f"{p['xapp_id']}-g{gnb}-{p['parameter']}-{t:.3f}-{self._seq}"
            prop = {"t": t, "xapp_id": p["xapp_id"], "gnb": gnb, "parameter": p["parameter"],
                    "value": float(p["value"]), "priority": int(p["priority"]), "ue": int(p.get("ue", -1)),
                    "id": pid, "xapp_impl": self.xapp_impl}
            self._mine[pid] = prop
            out.append(prop)
        return out

    def on_decision(self, selected_ids) -> None:
        for pid, p in list(self._mine.items()):
            if pid not in selected_ids:
                self.app.on_result({"node_id": f"gnb_{p['gnb']}", "parameter": p["parameter"],
                                    "reason": "NOT_SELECTED"})
        self._mine.clear()


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
