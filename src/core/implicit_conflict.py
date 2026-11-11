"""
Detecção de conflito implícito (nível 3 da governança; doc 09 §2.6).

Um conflito implícito é uma mudança na RAN que nenhuma ação confirmada pela RDL explica: outra
xApp (ou um operador) agiu por fora. A RDL compara o KPM medido com o que a ação confirmada
(``Perception.get_committed_action``) implica:

| Ação confirmada | Expectativa | Violação |
| :-- | :-- | :-- |
| ``CELL_STATE = 0`` | célula sem tráfego | vazão DL > ``thp_tolerance_mbps`` ou PRBs em uso > 0 |
| ``PRB_QUOTA = q`` | fatia SST 1 com até q % dos PRBs | ``sst1_prb_share_pct`` > q + ``prb_tolerance_pct`` (só quando o KPM traz a fatia) |

``TX_POWER``, ``SCHEDULER_WEIGHT`` e ``HANDOVER`` não têm expectativa verificável pelo KPM disponível
(sem medida de potência ou de célula servidora por UE) e não são checados.

Para não confundir transitório com conflito: a verificação começa ``grace_s`` depois do ACK, e a
violação precisa persistir em ``persistence`` relatórios seguidos. Cada episódio gera um único
achado até o KPM voltar a ser coerente.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.conflict_types import ConflictEvent, ConflictSeverity, ConflictType, XAppAction


@dataclass
class ImplicitFinding:
    node_id: str
    parameter: str
    committed_value: float
    committed_xapp: str
    observed: Dict[str, float]
    detail: str
    t: float = field(default_factory=time.time)
    suspects: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"t": self.t, "node_id": self.node_id, "parameter": self.parameter,
                "committed_value": self.committed_value, "committed_xapp": self.committed_xapp,
                "observed": dict(self.observed), "detail": self.detail, "suspects": list(self.suspects)}

    def to_conflict(self, committed: XAppAction) -> ConflictEvent:
        return ConflictEvent(
            conflict_type=ConflictType.IMPLICIT,
            severity=ConflictSeverity.HIGH,
            involved_xapps=[committed],
            affected_kpis=sorted(self.observed),
            description=f"Implicit conflict on {self.node_id}/{self.parameter}: {self.detail}",
        )


class ImplicitConflictDetector:
    PARAMETERS = ("CELL_STATE", "PRB_QUOTA")

    def __init__(self, committed_lookup: Callable[[str, str], Optional[XAppAction]],
                 grace_s: float = 2.0, persistence: int = 3,
                 thp_tolerance_mbps: float = 0.5, prb_tolerance_pct: float = 10.0,
                 clock: Callable[[], float] = time.time):
        self.committed_lookup = committed_lookup
        self.grace_s = grace_s
        self.persistence = max(1, int(persistence))
        self.thp_tolerance_mbps = thp_tolerance_mbps
        self.prb_tolerance_pct = prb_tolerance_pct
        self.clock = clock
        self._streak: Dict[Tuple[str, str], int] = {}
        self._open: Dict[Tuple[str, str], bool] = {}

    def _violation(self, parameter: str, value: float, m: Dict[str, float]) -> Optional[str]:
        if parameter == "CELL_STATE" and value == 0:
            thp, prb = m.get("drb_thp_dl"), m.get("prb_used_dl")
            if thp is not None and thp > self.thp_tolerance_mbps:
                return f"célula desligada com vazão DL {thp:.2f} Mb/s"
            if prb is not None and prb > 0:
                return f"célula desligada com {prb:g} PRBs em uso"
        if parameter == "PRB_QUOTA":
            share = m.get("sst1_prb_share_pct")
            if share is not None and share > value + self.prb_tolerance_pct:
                return f"fatia SST 1 com {share:.1f} % dos PRBs acima do teto confirmado de {value:g} %"
        return None

    def observe(self, node_id: str, metrics: Dict[str, Optional[float]],
                now: Optional[float] = None) -> List[Tuple[ImplicitFinding, XAppAction]]:
        """Avalia um relatório KPM do nó; devolve os conflitos implícitos que acabaram de se confirmar."""
        now = self.clock() if now is None else now
        m = {k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))}
        found: List[Tuple[ImplicitFinding, XAppAction]] = []
        for parameter in self.PARAMETERS:
            key = (node_id, parameter)
            committed = self.committed_lookup(node_id, parameter)
            if committed is None or not committed.t_ack or now - committed.t_ack < self.grace_s:
                self._streak.pop(key, None)
                self._open.pop(key, None)
                continue
            detail = self._violation(parameter, float(committed.value), m)
            if detail is None:
                self._streak.pop(key, None)
                self._open.pop(key, None)
                continue
            self._streak[key] = self._streak.get(key, 0) + 1
            if self._streak[key] >= self.persistence and not self._open.get(key):
                self._open[key] = True
                found.append((ImplicitFinding(node_id=node_id, parameter=parameter,
                                              committed_value=float(committed.value),
                                              committed_xapp=committed.xapp_id, observed=m, detail=detail),
                              committed))
        return found
