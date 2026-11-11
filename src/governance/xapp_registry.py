"""
Registro de xApps sob a RDL (nível 1 da governança) e modo de supervisão de cada uma.

Arquivo JSON (``RDL_XAPP_REGISTRY``), por xApp:

- ``sources``: expressões regulares para a origem RMR da mensagem (``hostname:porta`` do remetente).
  No modo estrito (``O_RAN_INTEROP``) uma proposta só é aceita de xApp registrada cuja origem
  confere. A origem RMR pode ser declarada pelo próprio remetente (``RMR_SRC_ID``); por isso o
  registro vale junto com a ``NetworkPolicy`` que restringe quem alcança a porta RMR da RDL.
- ``mode``: ``MANAGED`` (padrão: janela de decisão), ``ON_DEMAND`` (supervisão sob demanda: a
  proposta é decidida na chegada, sozinha, e só entra na janela quando há disputa no mesmo nó ou
  em vizinho) ou ``QUARANTINED`` (toda proposta é recusada como ``UNAUTHORIZED``).
- ``max_priority``: teto de prioridade; a proposta é rebaixada a ele (impede furar a fila).
- ``intercept_requestor_ids`` e ``default_priority``: RICrequestorIDs de uma xApp de terceiros cujo
  RIC Control (12040) é roteado para a RDL (nível 2) e a prioridade dada a esses controles.

A política A1 20000 sobrepõe ``mode`` e ``max_priority`` por xApp (``xapp_modes`` e
``xapp_priority_caps``); removida a política, volta o arquivo.
"""

import json
import os
import re
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

MANAGED = "MANAGED"
ON_DEMAND = "ON_DEMAND"
QUARANTINED = "QUARANTINED"
MODES = (MANAGED, ON_DEMAND, QUARANTINED)


@dataclass
class XAppEntry:
    xapp_id: str
    sources: List[str] = field(default_factory=list)
    mode: str = MANAGED
    max_priority: int = 100
    intercept_requestor_ids: List[int] = field(default_factory=list)
    default_priority: int = 50

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"modo inválido para {self.xapp_id}: {self.mode}")
        if not 0 <= int(self.max_priority) <= 100 or not 0 <= int(self.default_priority) <= 100:
            raise ValueError(f"prioridade fora de [0, 100] para {self.xapp_id}")
        self._patterns = [re.compile(p) for p in self.sources]

    def source_matches(self, source: Optional[str]) -> bool:
        return bool(source) and any(p.match(str(source)) for p in self._patterns)

    def to_dict(self) -> Dict[str, Any]:
        return {"sources": list(self.sources), "mode": self.mode, "max_priority": self.max_priority,
                "intercept_requestor_ids": list(self.intercept_requestor_ids),
                "default_priority": self.default_priority}


def parse_pairs(items: Iterable[str]) -> Dict[str, str]:
    """``["es:ON_DEMAND", "rogue:QUARANTINED"]`` → ``{"es": "ON_DEMAND", "rogue": "QUARANTINED"}``."""
    out: Dict[str, str] = {}
    for item in items:
        xapp, sep, value = str(item).rpartition(":")
        if not sep or not xapp or not value:
            raise ValueError(f"item inválido (use xapp:VALOR): {item}")
        out[xapp] = value
    return out


class XAppRegistry:
    def __init__(self, entries: Optional[Iterable[XAppEntry]] = None):
        self._entries: Dict[str, XAppEntry] = {e.xapp_id: e for e in (entries or [])}
        self._by_requestor: Dict[int, XAppEntry] = {}
        for e in self._entries.values():
            for rid in e.intercept_requestor_ids:
                if rid in self._by_requestor:
                    raise ValueError(f"RICrequestorID {rid} atribuído a duas xApps")
                self._by_requestor[int(rid)] = e
        self._mode_override: Dict[str, str] = {}
        self._cap_override: Dict[str, int] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ carga
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "XAppRegistry":
        entries = []
        for xapp_id, spec in (data.get("xapps") or {}).items():
            entries.append(XAppEntry(
                xapp_id=xapp_id,
                sources=list(spec.get("sources", [])),
                mode=str(spec.get("mode", MANAGED)),
                max_priority=int(spec.get("max_priority", 100)),
                intercept_requestor_ids=[int(r) for r in spec.get("intercept_requestor_ids", [])],
                default_priority=int(spec.get("default_priority", 50)),
            ))
        return cls(entries)

    @classmethod
    def from_env(cls) -> "XAppRegistry":
        path = os.getenv("RDL_XAPP_REGISTRY", "")
        if not path:
            return cls()
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    # ------------------------------------------------------------------ consulta
    @property
    def configured(self) -> bool:
        return bool(self._entries)

    def entry(self, xapp_id: str) -> Optional[XAppEntry]:
        return self._entries.get(xapp_id)

    def by_requestor(self, requestor_id: int) -> Optional[XAppEntry]:
        return self._by_requestor.get(int(requestor_id))

    def mode(self, xapp_id: str) -> str:
        with self._lock:
            if xapp_id in self._mode_override:
                return self._mode_override[xapp_id]
        entry = self._entries.get(xapp_id)
        return entry.mode if entry else MANAGED

    def priority_cap(self, xapp_id: str) -> int:
        with self._lock:
            if xapp_id in self._cap_override:
                return self._cap_override[xapp_id]
        entry = self._entries.get(xapp_id)
        return entry.max_priority if entry else 100

    def authorize(self, xapp_id: str, source: Optional[str], strict: bool) -> Tuple[bool, str]:
        """Pode esta proposta entrar? (sim/não, motivo)."""
        if self.mode(xapp_id) == QUARANTINED:
            return False, f"xApp {xapp_id} em quarentena"
        entry = self._entries.get(xapp_id)
        if strict:
            if entry is None:
                return False, f"xApp {xapp_id} não registrada (modo estrito)"
            if not entry.source_matches(source):
                return False, f"origem RMR {source!r} não confere com o registro de {xapp_id}"
            return True, "registered"
        if entry is not None and entry.sources and source and not entry.source_matches(source):
            return False, f"origem RMR {source!r} não confere com o registro de {xapp_id}"
        return True, "registered" if entry else "unregistered (modo não estrito)"

    # ------------------------------------------------------------------ política A1
    def apply_policy(self, modes: Optional[Dict[str, str]] = None, caps: Optional[Dict[str, int]] = None) -> None:
        modes = dict(modes or {})
        for xapp, mode in modes.items():
            if mode not in MODES:
                raise ValueError(f"modo inválido para {xapp}: {mode}")
        caps = {k: int(v) for k, v in (caps or {}).items()}
        with self._lock:
            self._mode_override = modes
            self._cap_override = caps

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            modes, caps = dict(self._mode_override), dict(self._cap_override)
        xapps = {xid: {**e.to_dict(), "effective_mode": self.mode(xid), "effective_max_priority": self.priority_cap(xid)}
                 for xid, e in self._entries.items()}
        for xid in set(modes) | set(caps):
            xapps.setdefault(xid, {"registered": False, "effective_mode": self.mode(xid),
                                   "effective_max_priority": self.priority_cap(xid)})
        return {"xapps": xapps, "a1_overrides": {"modes": modes, "priority_caps": caps}}
