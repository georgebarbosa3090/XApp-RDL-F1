# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
xApp2-EnergySaver (GreenRAN, atividade A1.6): desligamento de RUs em baixa demanda com padrão sazonal.

Por célula, um perfil de carga por hora do dia (``SeasonalProfile``) aprende os padrões sazonais. A cada
período, dentro da janela de economia da política A1 21001 (``GreenRAN_EnergySaver_Policy``):

1. **Religar primeiro:** uma célula desligada volta (``CELL_STATE = 1``, prioridade 85) se a janela
   acabou, se uma vizinha passou de ``es_wake_threshold_pct`` ou se a carga esperada para a próxima
   hora passa do limiar.
2. **Desligar com segurança (borda entre duas RUs):** a célula ativa menos carregada é candidata se a
   carga atual e a esperada para a próxima hora estão abaixo de ``es_sleep_threshold_pct``, se restam mais
   que ``es_min_active_cells`` células ativas e se uma vizinha ativa absorve a carga sem passar de
   ``es_wake_threshold_pct``. Em dois passos:
   - com UEs na célula: ``HANDOVER`` para a vizinha (evacuação, prioridade 65);
   - sem UEs (ou já evacuada): ``CELL_STATE = 0`` (prioridade 65).
   Uma célula por período.
3. **Potência:** com carga moderada (entre o limiar e o dobro), propõe reduzir ``TX_POWER`` para
   ``es_reduced_tx_power_dbm``, se a política permitir.

Se a RDL recusar o desligamento (por exemplo, pela regra ``HANDOVER_INTO_REDUCED_CELL`` ou pela política
A1), a célula volta a ``ACTIVE``.
"""

import re
import time
from typing import Any, Dict, List, Optional

from src.greenran.common import CellSample, GreenRanXApp, SeasonalProfile, load_neighbors

ACTIVE, EVACUATING, SLEEP = "ACTIVE", "EVACUATING", "SLEEP"


def _index(cell_id: str) -> Optional[int]:
    m = re.search(r"(\d+)$", cell_id)
    return int(m.group(1)) if m else None


class EnergySaver(GreenRanXApp):
    XAPP_ID = "xapp2_energysaver"
    A1_TYPE = "21001"
    DEFAULTS: Dict[str, Any] = {
        "es_sleep_threshold_pct": 15.0,
        "es_wake_threshold_pct": 60.0,
        "es_min_active_cells": 1,
        "es_sleep_start_hour": 22,
        "es_sleep_end_hour": 6,
        "es_tx_power_reduction": True,
        "es_reduced_tx_power_dbm": 30.0,
    }

    def __init__(self, *args, neighbors: Optional[Dict[str, List[str]]] = None, hour_of=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.neighbors = neighbors if neighbors is not None else load_neighbors()
        self.profile = SeasonalProfile()
        self.state: Dict[str, str] = {}
        self.hour_of = hour_of or (lambda t: time.localtime(t).tm_hour)

    def observe(self, sample: CellSample) -> None:
        super().observe(sample)
        self.state.setdefault(sample.cell_id, ACTIVE)
        if sample.load_pct is not None and self.state[sample.cell_id] == ACTIVE:
            self.profile.update(sample.cell_id, self.hour_of(sample.t), sample.load_pct)

    def _in_window(self, hour: int, pol: Dict[str, Any]) -> bool:
        start, end = int(pol["es_sleep_start_hour"]), int(pol["es_sleep_end_hour"])
        return (start <= hour or hour < end) if start > end else (start <= hour < end)

    def _load(self, cell: str) -> float:
        s = self.samples.get(cell)
        return float(s.load_pct) if s and s.load_pct is not None else 0.0

    def on_result(self, result: Dict[str, Any]) -> None:
        super().on_result(result)
        cell = result.get("node_id")
        if result.get("parameter") in ("CELL_STATE", "HANDOVER") and cell in self.state:
            self.state[cell] = ACTIVE                       # recusado pela RDL: volta a ativo

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol = self.policy()
        hour = self.hour_of(now)
        nxt = (hour + 1) % 24
        sleep_thr, wake_thr = float(pol["es_sleep_threshold_pct"]), float(pol["es_wake_threshold_pct"])
        in_window = self._in_window(hour, pol)
        out: List[Dict[str, Any]] = []
        cells = sorted(set(self.samples) | set(self.state))
        active = [c for c in cells if self.state.get(c, ACTIVE) != SLEEP]

        # 1. religar
        for cell in [c for c in cells if self.state.get(c) == SLEEP]:
            neigh_hot = any(self._load(n) > wake_thr for n in self.neighbors.get(cell, []))
            expected = self.profile.expected(cell, nxt, default=0.0) or 0.0
            if not in_window or neigh_hot or expected > sleep_thr:
                self.state[cell] = ACTIVE
                out.append(self._proposal(cell, "CELL_STATE", 1, 85))
        if out:
            return out

        # 2. desligar (uma célula por período) ou terminar a evacuação
        if in_window and len(active) > int(pol["es_min_active_cells"]):
            for cell in sorted(active, key=self._load):
                load = self._load(cell)
                expected = self.profile.expected(cell, nxt, default=load) or 0.0
                if load >= sleep_thr or expected >= sleep_thr:
                    continue
                hosts = [n for n in self.neighbors.get(cell, []) if self.state.get(n, ACTIVE) == ACTIVE
                         and self._load(n) + load < wake_thr and _index(n) is not None]
                if not hosts:
                    continue
                sample = self.samples.get(cell)
                ues = sample.total_ues if sample else 0
                if self.state.get(cell) == ACTIVE and ues > 0:
                    host = min(hosts, key=self._load)
                    self.state[cell] = EVACUATING
                    return [self._proposal(cell, "HANDOVER", _index(host), 65)]
                self.state[cell] = SLEEP
                return [self._proposal(cell, "CELL_STATE", 0, 65)]

        # 3. potência com carga moderada
        if pol.get("es_tx_power_reduction"):
            for cell in active:
                if self.state.get(cell) == ACTIVE and sleep_thr <= self._load(cell) < 2 * sleep_thr:
                    out.append(self._proposal(cell, "TX_POWER", float(pol["es_reduced_tx_power_dbm"]), 60))
        return out

    def _proposal(self, cell: str, parameter: str, value: Any, priority: int) -> Dict[str, Any]:
        return {"xapp_id": self.XAPP_ID, "node_id": cell, "parameter": parameter, "value": float(value),
                "priority": priority, "defer_ok": parameter != "HANDOVER", "ttl_ms": 2000}


def main() -> int:  # pragma: no cover - execução no RIC
    import os
    app = EnergySaver(rmr_port=int(os.getenv("RMR_PORT", "4560")))
    app.start()
    while app.running:
        time.sleep(1)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
