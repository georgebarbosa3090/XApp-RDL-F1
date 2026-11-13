# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
xApps próprias para os papéis do catálogo sem original público (docs/16, decisão D2), guiadas por KPM:

- ``LoadBalancer``: se a carga de uma célula passa da vizinha menos carregada em ``lb_imbalance_pct``
  pontos, propõe o handover dela para essa vizinha; com desequilíbrio moderado, propõe abrir a cota de PRB
  da célula carregada.
- ``Beamformer``: se o SINR médio dos UEs da célula cai abaixo de ``bf_min_sinr_db``, propõe subir a
  potência em ``bf_step_db`` (até ``bf_max_tx_dbm``); com SINR folgado, propõe voltar à nominal.
- ``IsacRadar``: reserva recursos de sensoriamento: em intervalos de ``isac_period_s``, propõe a cota de
  PRB ``isac_sensing_cap_pct`` na célula de sensoriamento, exceto quando a carga passa de
  ``isac_max_load_pct`` (cede ao tráfego).
- ``EmbbThroughput``: se a vazão da fatia eMBB fica abaixo de ``embb_target_mbps``, propõe abrir a cota de
  PRB da célula para ``embb_cap_pct``.
"""

from typing import Any, Dict, List, Optional

from src.xapps.derivadas import _Kpm, _index


class LoadBalancer(_Kpm):
    XAPP_ID = "load_balancer"
    A1_TYPE = ""
    DEFAULTS: Dict[str, Any] = {"lb_imbalance_pct": 30.0, "lb_moderate_pct": 15.0, "lb_open_cap_pct": 90.0,
                                "lb_cooldown_s": 5.0, "lb_priority": 70}

    def __init__(self, *a, neighbors: Optional[Dict[str, List[str]]] = None, **k):
        super().__init__(*a, **k)
        self.neighbors = neighbors or {}
        self.last: Dict[str, float] = {}

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol, out = self.policy(), []
        loads = {c: s.load_pct for c, s in self.samples.items() if s.load_pct is not None}
        for cell, load in sorted(loads.items()):
            if now - self.last.get(cell, float("-inf")) < float(pol["lb_cooldown_s"]):
                continue
            neigh = [n for n in (self.neighbors.get(cell) or [c for c in loads if c != cell]) if n in loads]
            if not neigh:
                continue
            light = min(neigh, key=lambda n: loads[n])
            gap = load - loads[light]
            if gap >= float(pol["lb_imbalance_pct"]) and _index(light) is not None:
                self.last[cell] = now
                out.append(self._proposal(cell, "HANDOVER", _index(light), pol["lb_priority"]))
            elif gap >= float(pol["lb_moderate_pct"]):
                self.last[cell] = now
                out.append(self._proposal(cell, "PRB_QUOTA", pol["lb_open_cap_pct"], pol["lb_priority"]))
        return out


class Beamformer(_Kpm):
    XAPP_ID = "beamformer"
    A1_TYPE = ""
    DEFAULTS: Dict[str, Any] = {"bf_min_sinr_db": 10.0, "bf_ok_sinr_db": 20.0, "bf_step_db": 3.0,
                                "bf_nominal_tx_dbm": 43.0, "bf_max_tx_dbm": 43.0, "bf_priority": 70}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.tx: Dict[str, float] = {}

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol, out = self.policy(), []
        for cell, s in sorted(self.samples.items()):
            sinrs = [u.sinr_db for u in s.ues if u.sinr_db is not None]
            if not sinrs:
                continue
            mean = sum(sinrs) / len(sinrs)
            cur = self.tx.get(cell, float(pol["bf_nominal_tx_dbm"]))
            if mean < float(pol["bf_min_sinr_db"]) and cur < float(pol["bf_max_tx_dbm"]):
                new = min(cur + float(pol["bf_step_db"]), float(pol["bf_max_tx_dbm"]))
            elif mean > float(pol["bf_ok_sinr_db"]) and cur > float(pol["bf_nominal_tx_dbm"]):
                new = float(pol["bf_nominal_tx_dbm"])
            else:
                continue
            self.tx[cell] = new
            out.append(self._proposal(cell, "TX_POWER", new, pol["bf_priority"]))
        return out


class IsacRadar(_Kpm):
    XAPP_ID = "isac_radar"
    A1_TYPE = ""
    DEFAULTS: Dict[str, Any] = {"isac_period_s": 5.0, "isac_sensing_cap_pct": 40.0, "isac_max_load_pct": 80.0,
                                "isac_cells": None, "isac_priority": 85}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.next_t: Dict[str, float] = {}

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol, out = self.policy(), []
        cells = pol.get("isac_cells") or sorted(self.samples)
        for cell in cells:
            s = self.samples.get(cell)
            if s is None or now < self.next_t.get(cell, float("-inf")):
                continue
            self.next_t[cell] = now + float(pol["isac_period_s"])
            if (s.load_pct or 0.0) <= float(pol["isac_max_load_pct"]):
                out.append(self._proposal(cell, "PRB_QUOTA", pol["isac_sensing_cap_pct"], pol["isac_priority"]))
        return out


class EmbbThroughput(_Kpm):
    XAPP_ID = "embb_throughput"
    A1_TYPE = ""
    DEFAULTS: Dict[str, Any] = {"embb_sst": 1, "embb_target_mbps": 20.0, "embb_cap_pct": 80.0, "embb_priority": 60}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.open: Dict[str, bool] = {}

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol, out = self.policy(), []
        for cell, s in sorted(self.samples.items()):
            embb = s.slices.get(int(pol["embb_sst"]))
            if embb is None or embb.ues == 0:
                continue
            short = embb.thp_mbps < float(pol["embb_target_mbps"])
            if short and not self.open.get(cell):
                self.open[cell] = True
                out.append(self._proposal(cell, "PRB_QUOTA", pol["embb_cap_pct"], pol["embb_priority"]))
            elif not short:
                self.open[cell] = False
        return out
