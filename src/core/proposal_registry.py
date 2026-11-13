"""
Registro de propostas não atendidas (doc 09 §2.4).

Toda proposta que entra na RDL e não vira RIC Control fica registrada com o motivo, para consulta
posterior (``GET /rejections``), para o aviso à xApp (RMR ``RDL_ACTION_RESULT``) e para o retorno
ao Non-RT RIC (resumo por motivo e por xApp, também exposto em métricas Prometheus).

Motivos:

- ``SAFETY``: barrada pelo Safety Guard (limites físicos, política A1, topologia).
- ``HYSTERESIS``: o alvo recebeu controle há menos que o intervalo mínimo; vem com ``retry_after_ms``.
- ``LOST_ARBITRATION``: perdeu para outra proposta ou para a ação já confirmada (``winner_*``).
- ``SLA_PROTECTION``: inelegível pela guarda de SLA (doc 18 §4.4): a previsão do modelo de efeito leva uma
  fatia com SLA abaixo do requisito, e outra candidata não leva (``winner_*``). Fica fora de
  ``LOST_ARBITRATION`` para não alimentar regras do Non-RT RIC sobre derrotas na arbitragem.
- ``STALE``: ficou mais tempo que a validade (``RDL_PROPOSAL_MAX_AGE_MS`` ou ``ttl_ms``) antes de ser decidida.
- ``OVERFLOW``: fila cheia na chegada.
- ``DISPATCH_FAILED``: admitida, mas o envio do RIC Control falhou.
- ``UNAUTHORIZED``: xApp não registrada (modo estrito), origem RMR que não confere ou em quarentena.

O registro é limitado (``max_entries``) e, se a memória da RDL souber guardar recusas
(``save_rejection``: SDL na implantação), cada entrada também é persistida lá.
"""

import threading
import time
from collections import Counter, deque
from typing import Any, Deque, Dict, List, Optional

SAFETY = "SAFETY"
HYSTERESIS = "HYSTERESIS"
LOST_ARBITRATION = "LOST_ARBITRATION"
SLA_PROTECTION = "SLA_PROTECTION"
STALE = "STALE"
OVERFLOW = "OVERFLOW"
DISPATCH_FAILED = "DISPATCH_FAILED"
UNAUTHORIZED = "UNAUTHORIZED"
REASONS = (SAFETY, HYSTERESIS, LOST_ARBITRATION, SLA_PROTECTION, STALE, OVERFLOW, DISPATCH_FAILED, UNAUTHORIZED)

_HYSTERESIS_MARK = "Control frequency exceeded"


def classify_guard_reason(text: str) -> str:
    """Motivo de recusa a partir do texto devolvido pelo Refinement."""
    return HYSTERESIS if text and _HYSTERESIS_MARK in text else SAFETY


class ProposalRegistry:
    def __init__(self, max_entries: int = 5000, store: Any = None, clock=time.time):
        self._entries: Deque[Dict[str, Any]] = deque(maxlen=max(1, int(max_entries)))
        self._totals: Counter = Counter()
        self._lock = threading.Lock()
        self.store = store
        self.clock = clock

    def record(self, action, reason: str, detail: str = "", decision_id: Optional[str] = None,
               winner=None, retry_after_ms: Optional[float] = None, deferred: bool = False) -> Dict[str, Any]:
        if reason not in REASONS:
            raise ValueError(f"motivo de recusa desconhecido: {reason}")
        entry = {
            "t": self.clock(),
            "action_id": action.action_id,
            "xapp_id": action.xapp_id,
            "node_id": action.node_id,
            "parameter": action.parameter,
            "value": action.value,
            "priority": action.priority,
            "urgency": getattr(action, "urgency", "NORMAL"),
            "reason": reason,
            "detail": detail or "",
            "decision_id": decision_id,
            "winner_action_id": getattr(winner, "action_id", None),
            "winner_xapp_id": getattr(winner, "xapp_id", None),
            "retry_after_ms": None if retry_after_ms is None else round(float(retry_after_ms), 1),
            "deferred": bool(deferred),
        }
        with self._lock:
            self._entries.append(entry)
            self._totals[(reason, action.xapp_id)] += 1
        saver = getattr(self.store, "save_rejection", None)
        if callable(saver):
            try:
                saver(action.action_id, entry)
            except Exception:  # a persistência nunca bloqueia a decisão
                pass
        return entry

    def query(self, xapp_id: Optional[str] = None, node_id: Optional[str] = None, reason: Optional[str] = None,
              since: float = 0.0, limit: int = 100) -> List[Dict[str, Any]]:
        """Entradas mais recentes primeiro, filtradas."""
        with self._lock:
            entries = list(self._entries)
        out = []
        for e in reversed(entries):
            if e["t"] < since:
                break
            if (xapp_id and e["xapp_id"] != xapp_id) or (node_id and e["node_id"] != node_id) \
                    or (reason and e["reason"] != reason):
                continue
            out.append(dict(e))
            if len(out) >= max(1, int(limit)):
                break
        return out

    def summary(self) -> Dict[str, Any]:
        """Totais desde o início (não só o que cabe no registro), por motivo e por xApp."""
        with self._lock:
            totals = dict(self._totals)
            retained = len(self._entries)
        by_reason: Counter = Counter()
        by_xapp: Dict[str, Dict[str, int]] = {}
        for (reason, xapp), n in totals.items():
            by_reason[reason] += n
            by_xapp.setdefault(xapp, {})[reason] = n
        return {"total": sum(by_reason.values()), "retained": retained,
                "by_reason": dict(by_reason), "by_xapp": by_xapp}
