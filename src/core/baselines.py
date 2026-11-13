# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
Baselines B0–B2: a regra de escolha única, usada pelo executor nativo
(``scripts/certification/run_conflict_experiment.py``), pelo orquestrador da malha fechada
(``scripts/closed_loop/orchestrator.py``) e pela bancada NORI (``src/closed_loop/catalog_loop.py``).

- **B0 (sem coordenação):** toda proposta vai à RAN. O instante depende do executor e fica explícito
  na regra registrada: ``apply-on-arrival`` (malha aberta e bancada: cada proposta no instante em que é
  emitida) ou ``apply-all-at-window-close`` (malha fechada: todas no fechamento da janela, por ordem de
  chegada).
- **B1 (FIFO):** por alvo, a primeira proposta a chegar.
- **B2 (prioridade estática):** por alvo, a de maior prioridade; no empate, a primeira a chegar.

As funções não conhecem o formato das propostas: quem chama passa como obter o alvo, a ordem de chegada
e a prioridade. Assim, um dicionário do catálogo e uma ``XAppAction`` seguem a mesma regra.
"""

from collections import OrderedDict
from typing import Any, Callable, Hashable, Iterable, List, Sequence

B0_ON_ARRIVAL = "apply-on-arrival"
B0_AT_WINDOW_CLOSE = "apply-all-at-window-close"
RULES = {"B1": "fifo-per-target", "B2": "static-priority-per-target"}
NON_HRDL_BASELINES = ("B0", "B1", "B2")


def group_by_target(items: Iterable[Any], target: Callable[[Any], Hashable]) -> "OrderedDict[Hashable, List[Any]]":
    """Propostas agrupadas por alvo, na ordem em que cada alvo aparece pela primeira vez."""
    grouped: "OrderedDict[Hashable, List[Any]]" = OrderedDict()
    for item in items:
        grouped.setdefault(target(item), []).append(item)
    return grouped


def choose(candidates: Sequence[Any], baseline: str, arrival: Callable[[Any], Any],
           priority: Callable[[Any], float]) -> Any:
    """Vencedora de um alvo: B1 pela chegada; B2 pela maior prioridade e, no empate, pela chegada."""
    if baseline == "B1":
        return min(candidates, key=arrival)
    if baseline == "B2":
        return min(candidates, key=lambda c: (-priority(c), arrival(c)))
    raise ValueError(f"baseline por alvo desconhecido: {baseline} (B1, B2)")


def select_per_target(items: Iterable[Any], baseline: str, target: Callable[[Any], Hashable],
                      arrival: Callable[[Any], Any], priority: Callable[[Any], float]) -> List[Any]:
    """B1/B2: uma vencedora por alvo, na ordem de primeira aparição de cada alvo."""
    return [choose(cands, baseline, arrival, priority) for cands in group_by_target(items, target).values()]


def select(items: Sequence[Any], baseline: str, target: Callable[[Any], Hashable],
           arrival: Callable[[Any], Any], priority: Callable[[Any], float]) -> List[Any]:
    """B0: todas, por ordem de chegada; B1/B2: ``select_per_target``."""
    if baseline == "B0":
        return sorted(items, key=arrival)
    return select_per_target(items, baseline, target, arrival, priority)
