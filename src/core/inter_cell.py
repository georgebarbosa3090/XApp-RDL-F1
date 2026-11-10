"""
Regras de conflito entre células (H-RDL).

A percepção original agrupa conflitos por gNB e não enxerga interações entre
células vizinhas (achado 11, cenários S4 e S5). Este módulo define as regras que a
percepção usa para detectar esses conflitos e que o raciocínio usa para recusar
subconjuntos fisicamente incompatíveis na arbitragem (EEVS):

- HANDOVER_INTO_REDUCED_CELL: uma xApp move UEs para uma célula enquanto outra
  desliga essa célula (``CELL_STATE = 0``) ou reduz sua potência abaixo de um limiar.
  O handover é um evento, mas seu efeito (UEs servidos pela célula de destino) persiste:
  um handover confirmado continua valendo até ser substituído por outro do mesmo nó de
  origem, ou por ``handover_hold_s`` segundos quando configurado.
- HANDOVER_PING_PONG: handovers em sentidos opostos entre o mesmo par de células,
  vindos de xApps diferentes, dentro de uma janela de tempo.
- NEIGHBOR_SLEEP: duas células vizinhas desligadas por xApps diferentes na mesma
  decisão (risco de buraco de cobertura), quando a topologia é conhecida.

O valor de ``HANDOVER`` é o índice da célula de destino (como no catálogo de
cenários). O nó de destino é obtido trocando o índice final do ``node_id`` de origem
(``gnb_0`` -> ``gnb_1``; ``nori#g0`` -> ``nori#g1``), ou por um resolvedor injetado.
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Set

from src.conflict_types import XAppAction

HANDOVER_INTO_REDUCED_CELL = "HANDOVER_INTO_REDUCED_CELL"
HANDOVER_PING_PONG = "HANDOVER_PING_PONG"
NEIGHBOR_SLEEP = "NEIGHBOR_SLEEP"

_TRAILING_INDEX = re.compile(r"^(.*?)(\d+)$")


def default_handover_target(action: XAppAction) -> Optional[str]:
    """Nó de destino de um HANDOVER: troca o índice final do nó de origem pelo valor."""
    try:
        value = float(action.value)
    except (TypeError, ValueError):
        return None
    if not value.is_integer() or value < 0:
        return None
    match = _TRAILING_INDEX.match(str(action.node_id))
    if not match:
        return None
    return f"{match.group(1)}{int(value)}"


def load_inter_cell_config(path: Optional[str] = None) -> dict:
    """Lê a topologia e os parâmetros das regras de um JSON (``RDL_TOPOLOGY_FILE``).

    Formato: ``{"neighbors": {"gnb_0": ["gnb_1"]}, "low_power_threshold_dbm": 10,
    "pingpong_window_s": 5, "allow_neighbor_sleep": false}``. Sem arquivo, as regras
    de handover continuam ativas e a de vizinhas dormindo fica inativa (sem topologia).
    """
    path = path or os.getenv("RDL_TOPOLOGY_FILE")
    if not path:
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@dataclass
class InterCellRules:
    """Parâmetros e topologia das regras entre células."""

    neighbors: Dict[str, Set[str]] = field(default_factory=dict)
    low_power_threshold_dbm: float = 10.0
    pingpong_window_s: float = 5.0
    # None: um handover confirmado protege a célula de destino até ser substituído
    handover_hold_s: Optional[float] = None
    allow_neighbor_sleep: bool = False
    handover_target: Callable[[XAppAction], Optional[str]] = default_handover_target

    @classmethod
    def from_config(cls, config: Optional[dict]) -> "InterCellRules":
        config = config or {}
        neighbors: Dict[str, Set[str]] = {}
        for node, adjacent in (config.get("neighbors") or {}).items():
            for other in adjacent:
                neighbors.setdefault(str(node), set()).add(str(other))
                neighbors.setdefault(str(other), set()).add(str(node))
        return cls(
            neighbors=neighbors,
            low_power_threshold_dbm=float(config.get("low_power_threshold_dbm", 10.0)),
            pingpong_window_s=float(config.get("pingpong_window_s", 5.0)),
            handover_hold_s=(float(config["handover_hold_s"]) if config.get("handover_hold_s") is not None else None),
            allow_neighbor_sleep=bool(config.get("allow_neighbor_sleep", False)),
        )

    def are_neighbors(self, node_a: str, node_b: str) -> bool:
        return node_b in self.neighbors.get(node_a, set())

    def reduces_cell(self, action: XAppAction) -> bool:
        """A ação desliga a célula ou reduz sua potência abaixo do limiar."""
        try:
            value = float(action.value)
        except (TypeError, ValueError):
            return False
        if action.parameter == "CELL_STATE":
            return value == 0.0
        if action.parameter == "TX_POWER":
            return value <= self.low_power_threshold_dbm
        return False

    def is_sleep(self, action: XAppAction) -> bool:
        return action.parameter == "CELL_STATE" and self.reduces_cell(action)

    def pair_conflict(self, a: XAppAction, b: XAppAction, check_time: bool = False) -> Optional[str]:
        """Motivo do conflito entre duas ações de nós diferentes e xApps diferentes, ou None."""
        if a.node_id == b.node_id or a.xapp_id == b.xapp_id:
            return None
        for first, second in ((a, b), (b, a)):
            if first.parameter == "HANDOVER" and self.reduces_cell(second):
                if self.handover_target(first) == second.node_id:
                    return HANDOVER_INTO_REDUCED_CELL
        if a.parameter == "HANDOVER" and b.parameter == "HANDOVER":
            if self.handover_target(a) == b.node_id and self.handover_target(b) == a.node_id:
                if not check_time or abs(float(a.timestamp) - float(b.timestamp)) <= self.pingpong_window_s:
                    return HANDOVER_PING_PONG
        if (
            not self.allow_neighbor_sleep
            and self.is_sleep(a)
            and self.is_sleep(b)
            and self.are_neighbors(a.node_id, b.node_id)
        ):
            return NEIGHBOR_SLEEP
        return None

    def subset_is_compatible(self, subset: Iterable[XAppAction]) -> bool:
        """Nenhum par do subconjunto viola uma regra entre células."""
        items: List[XAppAction] = list(subset)
        for i, a in enumerate(items):
            for b in items[i + 1:]:
                if self.pair_conflict(a, b) is not None:
                    return False
        return True
