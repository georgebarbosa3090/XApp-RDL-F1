"""
Janela de decisão adaptativa e classes de urgência (doc 09 §2.2).

- ``CRITICAL``: prioridade ≥ ``critical_priority`` ou (xApp, parâmetro) marcado como crítico
  (por configuração ou política A1). Vai pelo caminho rápido: é decidida na hora, junto com as
  propostas pendentes para o mesmo nó ou para nós vizinhos (que saem do buffer para competir
  com ela). Passa pelo Safety Guard, pela histerese e pela arbitragem como qualquer outra.
- ``URGENT``: prioridade ≥ ``urgent_priority``; encurta a janela para ``urgent_window_ms``.
- ``NORMAL``: janela adaptativa entre ``min_window_ms`` e ``max_window_ms``.

Janela adaptativa: o tempo esperado para acumular ``target_proposals`` propostas, dada a taxa
de chegada recente (média móvel exponencial), limitado ao intervalo configurado. Com pouca
concorrência a janela encolhe (decide mais cedo); com muitas propostas cresce (agrupa os
conflitos). Sem chegadas recentes, usa ``base_window_ms``.
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set, Tuple


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


class AdaptiveDecisionWindow:
    def __init__(self, config: Optional[WindowConfig] = None, clock=time.monotonic):
        self.config = config or WindowConfig()
        self.clock = clock
        self._rate = 0.0           # propostas por segundo (EWMA)
        self._last_arrival: Optional[float] = None

    def classify(self, action) -> Urgency:
        cfg = self.config
        targets = cfg.critical_targets
        if action.priority >= cfg.critical_priority or (action.xapp_id, action.parameter) in targets \
                or ("*", action.parameter) in targets:
            return Urgency.CRITICAL
        if action.priority >= cfg.urgent_priority:
            return Urgency.URGENT
        return Urgency.NORMAL

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
