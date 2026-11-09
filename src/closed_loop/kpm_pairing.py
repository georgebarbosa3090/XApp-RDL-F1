"""
Disparo da decisão só com o relatório KPM completo do período (achado 48 de docs/07).

O NORI envia o KPM de cada período em par: formato 1 (nó) e formato 3 (UEs), com menos de 1 ms entre si, e o
E2Term pode entregá-los à xApp em qualquer ordem. Uma decisão rápida (os baselines decidem em ~1 ms) disparada
pela primeira mensagem do par usava os UEs do período anterior, e o último KPM antes do Control no fio (o
KPM_t0) não entrava na decisão.

Regra: a decisão só dispara quando a mensagem que acabou de chegar completa o par, ou seja, quando há KPM de nó
e de UEs recebidos a no máximo ``window_s`` um do outro. Os pares chegam com < 1 ms de diferença e os períodos
ficam a segundos de distância, então a janela padrão de 0,5 s separa os períodos com folga. O cabeçalho KPM do
NORI (``colletStartTime``) não distingue os períodos, por isso o casamento é pela chegada.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

DEFAULT_PAIR_WINDOW_S = 0.5


def pair_gap_s(entry: Dict[str, Any]) -> Optional[float]:
    """Intervalo (s) entre a chegada do último KPM de nó e do último KPM de UEs; None se faltar um deles."""
    node_at, ues_at = entry.get("node_at"), entry.get("ues_at")
    if node_at is None or ues_at is None or "node" not in entry or "ues" not in entry:
        return None
    return abs(float(node_at) - float(ues_at))


def pair_complete(entry: Dict[str, Any], window_s: float = DEFAULT_PAIR_WINDOW_S) -> bool:
    """True se o KPM de nó e o de UEs mais recentes são do mesmo período (chegaram dentro da janela)."""
    gap = pair_gap_s(entry)
    return gap is not None and gap <= window_s
