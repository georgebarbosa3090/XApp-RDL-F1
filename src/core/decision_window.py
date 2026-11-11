"""
Janela de decisão adaptativa e classes de urgência (doc 09 §2.2).

- ``CRITICAL``: prioridade ≥ ``critical_priority`` ou (xApp, parâmetro) marcado como crítico
  (por configuração ou política A1). Vai pelo caminho rápido: é decidida na hora, junto com as
  propostas pendentes para o mesmo nó ou para nós vizinhos (que saem do buffer para competir
  com ela). Passa pelo Safety Guard e pela arbitragem como qualquer outra; o intervalo mínimo
  entre controles no mesmo alvo é o da classe crítica (``critical_control_interval_ms`` no
  Refinement, 100 ms por padrão), não o de 1000 ms.
  Cota: cada xApp tem no máximo ``critical_max_per_s`` críticas por segundo; o excedente vira
  ``URGENT``, para que uma xApp não se declare crítica o tempo todo.
- ``URGENT``: prioridade ≥ ``urgent_priority``; encurta a janela para ``urgent_window_ms``.
- ``NORMAL``: janela adaptativa entre ``min_window_ms`` e ``max_window_ms``.

Validade: uma proposta não decidida em ``proposal_max_age_ms`` (desde a chegada à RDL) é
descartada como ``STALE``. Uma proposta com ``defer_ok`` pode pedir ``ttl_ms`` maior, até
``defer_max_ttl_ms``; sem ``ttl_ms`` vale ``defer_default_ttl_ms``. A idade é medida no relógio
monotônico da RDL, não no relógio de quem enviou.

Janela adaptativa: o tempo esperado para acumular ``target_proposals`` propostas, dada a taxa
de chegada recente (média móvel exponencial), limitado ao intervalo configurado. Com pouca
concorrência a janela encolhe (decide mais cedo); com muitas propostas cresce (agrupa os
conflitos). Sem chegadas recentes, usa ``base_window_ms``.
"""

import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Dict, Iterable, Optional, Set, Tuple


class Urgency(Enum):
    CRITICAL = "CRITICAL"
    URGENT = "URGENT"
    NORMAL = "NORMAL"


@dataclass
class WindowConfig:
    base_window_ms: float = 200.0
    min_window_ms: float = 50.0
    max_window_ms: float = 500.0
    urgent_window_ms: float = 20.0
    critical_priority: int = 95
    urgent_priority: int = 80
    target_proposals: float = 8.0
    rate_half_life_s: float = 1.0
    adaptive: bool = True
    critical_targets: Set[Tuple[str, str]] = field(default_factory=set)  # (xapp_id ou "*", parâmetro)
    critical_max_per_s: float = 5.0
    proposal_max_age_ms: float = 1000.0
    defer_default_ttl_ms: float = 2000.0
    defer_max_ttl_ms: float = 3000.0


def parse_critical_targets(spec: Iterable[str]) -> Set[Tuple[str, str]]:
    """``["xapp:PARAM", "*:CELL_STATE"]`` → ``{("xapp", "PARAM"), ("*", "CELL_STATE")}``."""
    targets: Set[Tuple[str, str]] = set()
    for item in spec:
        item = str(item).strip()
        if not item:
            continue
        xapp, sep, param = item.rpartition(":")
        if not sep or not xapp or not param:
            raise ValueError(f"alvo crítico inválido (use xapp:PARAMETRO ou *:PARAMETRO): {item}")
        targets.add((xapp, param))
    return targets


class AdaptiveDecisionWindow:
    def __init__(self, config: Optional[WindowConfig] = None, clock=time.monotonic):
        self.config = config or WindowConfig()
        self.clock = clock
        self._rate = 0.0           # propostas por segundo (EWMA)
        self._last_arrival: Optional[float] = None
        self._critical_times: Dict[str, Deque[float]] = {}
        self.downgraded_count = 0
        self.downgraded_by_xapp: Dict[str, int] = {}

    def classify(self, action) -> Urgency:
        cfg = self.config
        targets = cfg.critical_targets
        if action.priority >= cfg.critical_priority or (action.xapp_id, action.parameter) in targets \
                or ("*", action.parameter) in targets:
            return Urgency.CRITICAL
        if action.priority >= cfg.urgent_priority:
            return Urgency.URGENT
        return Urgency.NORMAL

    def classify_and_admit(self, action, now: Optional[float] = None) -> Urgency:
        """Classe de urgência com a cota de críticas por xApp aplicada (excedente vira URGENT)."""
        urgency = self.classify(action)
        if urgency != Urgency.CRITICAL:
            return urgency
        now = self.clock() if now is None else now
        times = self._critical_times.setdefault(action.xapp_id, deque())
        while times and now - times[0] >= 1.0:
            times.popleft()
        if len(times) >= self.config.critical_max_per_s:
            self.downgraded_count += 1
            self.downgraded_by_xapp[action.xapp_id] = self.downgraded_by_xapp.get(action.xapp_id, 0) + 1
            return Urgency.URGENT
        times.append(now)
        return Urgency.CRITICAL

    def ttl_ms(self, action) -> float:
        """Validade da proposta desde a chegada."""
        cfg = self.config
        if getattr(action, "defer_ok", False):
            requested = getattr(action, "ttl_ms", None)
            wanted = cfg.defer_default_ttl_ms if requested is None else float(requested)
            return max(cfg.proposal_max_age_ms, min(wanted, cfg.defer_max_ttl_ms))
        return cfg.proposal_max_age_ms

    def remaining_ms(self, action, now: Optional[float] = None) -> float:
        """Validade que resta (negativo = vencida). ``now`` no relógio de ``arrival_monotonic``."""
        now = time.perf_counter() if now is None else now
        return self.ttl_ms(action) - (now - action.arrival_monotonic) * 1000.0

    def observe_arrival(self, now: Optional[float] = None) -> None:
        now = self.clock() if now is None else now
        if self._last_arrival is None:
            self._rate = 1.0 / max(self.config.base_window_ms / 1000.0, 1e-3)
        else:
            dt = max(now - self._last_arrival, 1e-6)
            alpha = 1.0 - math.exp(-dt * math.log(2) / self.config.rate_half_life_s)
            self._rate = (1 - alpha) * self._rate + alpha * (1.0 / dt)
        self._last_arrival = now

    @property
    def arrival_rate(self) -> float:
        return self._rate

    def window_ms(self, now: Optional[float] = None) -> float:
        cfg = self.config
        if not cfg.adaptive:
            return cfg.base_window_ms
        now = self.clock() if now is None else now
        if self._last_arrival is None or now - self._last_arrival > cfg.max_window_ms / 1000.0 * 4:
            return cfg.base_window_ms
        if self._rate <= 0:
            return cfg.base_window_ms
        wanted = 1000.0 * cfg.target_proposals / self._rate
        return max(cfg.min_window_ms, min(cfg.max_window_ms, wanted))

    def deadline_ms(self, urgency: Urgency, now: Optional[float] = None) -> float:
        """Tempo máximo de espera, a partir da abertura da janela, para uma proposta dessa classe."""
        if urgency == Urgency.CRITICAL:
            return 0.0
        if urgency == Urgency.URGENT:
            return min(self.config.urgent_window_ms, self.window_ms(now))
        return self.window_ms(now)
