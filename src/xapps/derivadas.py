# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
Núcleos guiados por KPM das xApps derivadas (reimplementações próprias, inspiradas em xApps publicadas;
os originais estão em third_party/xapps/ e rodam na malha fechada pelo libe42_shim ou pelo adaptador).

Cada núcleo decide só a partir do KPM observado (``self.samples``), nunca de valores fixos. Os papéis:

O papel do xSlice (``peihaoY/xslice-oran``) na malha fechada é feito desde 2026-11-21 por uma xApp própria,
``src.xapps.proprias.UrllcSliceGuard`` (até então, ``XSliceDerivada`` neste módulo, com ``xapp_id`` ``xslice``).

- ``EnergySavingDerivada`` (papel de Energy Saving): com a carga da célula abaixo do limiar, propõe reduzir
  a potência de transmissão; com carga alta, propõe restaurar. Uma proposta por mudança de estado.
- ``TrafficSteeringDerivada`` (papel de ``o-ran-sc/ric-app-ts``): quando uma fração dos UEs de uma célula
  mede uma vizinha com RSRP acima da servidora mais ``ts_threshold_db``, propõe o handover da célula para
  essa vizinha (a RDL aplica o handover à célula inteira), com tempo mínimo entre propostas.
- ``RogueDerivada`` (teste de segurança): ao observar tráfego, alterna propostas fora dos limites físicos
  (potência de 45 dBm e 5 dBm, cota de PRB de 150 %) para exercitar o Safety Guard.
"""

from typing import Any, Dict, List, Optional

from src.greenran.common import GreenRanXApp


def _index(cell: str) -> Optional[int]:
    tail = cell.rsplit("_", 1)[-1]
    return int(tail) if tail.isdigit() else None


class _Kpm(GreenRanXApp):
    """Base: proposta no formato da RDL e utilitários de leitura do KPM."""

    def _proposal(self, cell: str, parameter: str, value: float, priority: int, **extra) -> Dict[str, Any]:
        return {"xapp_id": self.XAPP_ID, "node_id": cell, "parameter": parameter, "value": float(value),
                "priority": int(priority), **extra}


class EnergySavingDerivada(_Kpm):
    XAPP_ID = "energy_saving"
    A1_TYPE = ""  # sem tipo A1 próprio: usa os padrões
    DEFAULTS: Dict[str, Any] = {"esd_low_load_pct": 10.0, "esd_high_load_pct": 40.0, "esd_reduced_tx_dbm": 30.0,
                                "esd_nominal_tx_dbm": 43.0, "esd_priority": 65}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.reduced: Dict[str, bool] = {}

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol, out = self.policy(), []
        for cell, s in sorted(self.samples.items()):
            if s.load_pct is None:
                continue
            if not self.reduced.get(cell) and s.load_pct < float(pol["esd_low_load_pct"]):
                self.reduced[cell] = True
                out.append(self._proposal(cell, "TX_POWER", pol["esd_reduced_tx_dbm"], pol["esd_priority"]))
            elif self.reduced.get(cell) and s.load_pct > float(pol["esd_high_load_pct"]):
                self.reduced[cell] = False
                out.append(self._proposal(cell, "TX_POWER", pol["esd_nominal_tx_dbm"], pol["esd_priority"]))
        return out


class TrafficSteeringDerivada(_Kpm):
    XAPP_ID = "traffic_steering"
    A1_TYPE = "20008"  # mesmo tipo de política do ric-app-ts (limiar)
    DEFAULTS: Dict[str, Any] = {"ts_threshold_db": 3.0, "ts_min_fraction": 0.5, "ts_cooldown_s": 5.0,
                                "ts_priority": 80}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.last: Dict[str, float] = {}

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol, out = self.policy(), []
        thr = float(pol["ts_threshold_db"])
        for cell, s in sorted(self.samples.items()):
            if not s.ues or now - self.last.get(cell, float("-inf")) < float(pol["ts_cooldown_s"]):
                continue
            votes: Dict[str, int] = {}
            for u in s.ues:
                serv = u.rsrp_dbm.get(cell)
                if serv is None:
                    continue
                best = max(((c, r) for c, r in u.rsrp_dbm.items() if c != cell), key=lambda x: x[1], default=None)
                if best and best[1] > serv + thr:
                    votes[best[0]] = votes.get(best[0], 0) + 1
            if not votes:
                continue
            target, n = max(votes.items(), key=lambda x: x[1])
            if n >= max(1, float(pol["ts_min_fraction"]) * len(s.ues)) and _index(target) is not None:
                self.last[cell] = now
                out.append(self._proposal(cell, "HANDOVER", _index(target), pol["ts_priority"]))
        return out


class RogueDerivada(_Kpm):
    XAPP_ID = "rogue_xapp"
    A1_TYPE = ""  # sem tipo A1 próprio: usa os padrões
    DEFAULTS: Dict[str, Any] = {"rogue_period_s": 2.0, "rogue_priority": 95}
    VALUES = (("TX_POWER", 45.0), ("TX_POWER", 5.0), ("PRB_QUOTA", 150.0))

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.next_t: Optional[float] = None
        self.k = 0

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol = self.policy()
        busy = [c for c, s in sorted(self.samples.items()) if (s.load_pct or 0) > 0 or s.ues]
        if not busy:
            return []
        if self.next_t is not None and now < self.next_t:
            return []
        self.next_t = now + float(pol["rogue_period_s"])
        param, value = self.VALUES[self.k % len(self.VALUES)]
        self.k += 1
        return [self._proposal(busy[0], param, value, pol["rogue_priority"])]
