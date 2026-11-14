"""
Grafo de conhecimento da RDL (Fases 1 e 2).

Grafo de propriedades em memória, sem dependências externas, que reúne o que a RDL sabe sobre
a rede e sobre as próprias decisões:

Nós (``kind``)                       Arestas (``relation``)
- ``cell``: nó E2 / célula           - ``NEIGHBOR_OF``: cell — cell (simétrica)
- ``parameter``: parâmetro de RC     - ``AFFECTS``: parameter → kpi
- ``kpi``: métrica E2SM-KPM          - ``PROPOSED``: xapp → action
- ``xapp``                           - ``TARGETS``: action → cell (atributo ``parameter``)
- ``action``: proposta               - ``INVOLVES``: conflict → action
- ``conflict``                       - ``RESOLVED_BY``: conflict → decision
- ``decision``                       - ``SELECTED``: decision → action
- ``policy``: política A1            - ``GOVERNS``: policy → decision (política efetiva no momento)

Usos:
- **Fase 1:** fonte da vizinhança entre células e das dependências parâmetro → KPI usadas pela
  Percepção; registro auditável de propostas, conflitos e decisões (exportável em JSON).
- **Fase 2:** contexto para o MAPPO (histórico de conflitos e decisões por alvo, grau de
  vizinhança), via ``context_features``.

Os eventos (ações, conflitos, decisões) têm retenção limitada (``max_events``): os mais antigos
saem com suas arestas, para o grafo não crescer sem limite.
"""

import json
import threading
import time
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, Iterable, List, Optional, Set, Tuple

EVENT_KINDS = {"action", "conflict", "decision"}


@dataclass
class Node:
    id: str
    kind: str
    attrs: Dict[str, Any] = field(default_factory=dict)


_QUERIES = ("has_node", "node", "successors", "predecessors", "edge", "nodes", "neighbors", "neighbor_map",
            "affected_kpis", "shared_kpis", "conflicts_on", "context_features")
_WRITES = ("add_node", "add_edge", "add_cell", "add_neighbors", "add_parameter", "record_action", "record_conflict",
           "record_decision")


def _counted(kind: str, fn):
    """Conta a chamada pública (consulta ou escrita); chamadas internas aninhadas não contam de novo."""
    import functools

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        depth = getattr(self._tls, "depth", 0)
        if depth == 0:
            self.op_counts[kind] = self.op_counts.get(kind, 0) + 1
        self._tls.depth = depth + 1
        try:
            return fn(self, *args, **kwargs)
        finally:
            self._tls.depth = depth
    return wrapper


class KnowledgeGraph:
    def __init__(self, max_events: int = 5000):
        self.op_counts: Dict[str, int] = {"queries": 0, "writes": 0}   # painel de campanha (docs/16 §10.4)
        self._tls = threading.local()
        self.max_events = int(max_events)
        self._nodes: Dict[str, Node] = {}
        # relation -> origem -> {destino: atributos}
        self._out: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = {}
        self._in: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = {}
        self._events: Deque[str] = deque()
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ básico
    def add_node(self, node_id: str, kind: str, **attrs: Any) -> Node:
        with self._lock:
            node = self._nodes.get(node_id)
            if node is None:
                node = Node(node_id, kind, dict(attrs))
                self._nodes[node_id] = node
                if kind in EVENT_KINDS:
                    self._events.append(node_id)
                    self._evict()
            else:
                node.attrs.update(attrs)
            return node

    def add_edge(self, src: str, relation: str, dst: str, **attrs: Any) -> None:
        with self._lock:
            if src not in self._nodes or dst not in self._nodes:
                raise KeyError(f"aresta {src} -{relation}-> {dst}: nó inexistente")
            self._out.setdefault(relation, {}).setdefault(src, {})[dst] = dict(attrs)
            self._in.setdefault(relation, {}).setdefault(dst, {})[src] = dict(attrs)

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def node(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def successors(self, node_id: str, relation: str) -> List[str]:
        return sorted(self._out.get(relation, {}).get(node_id, {}))

    def predecessors(self, node_id: str, relation: str) -> List[str]:
        return sorted(self._in.get(relation, {}).get(node_id, {}))

    def edge(self, src: str, relation: str, dst: str) -> Optional[Dict[str, Any]]:
        return self._out.get(relation, {}).get(src, {}).get(dst)

    def nodes(self, kind: Optional[str] = None) -> List[Node]:
        return [n for n in self._nodes.values() if kind is None or n.kind == kind]

    def _remove_node(self, node_id: str) -> None:
        for index, reverse in ((self._out, self._in), (self._in, self._out)):
            for relation, adjacency in index.items():
                for other in list(adjacency.pop(node_id, {})):
                    reverse.get(relation, {}).get(other, {}).pop(node_id, None)
        self._nodes.pop(node_id, None)

    def _evict(self) -> None:
        while len(self._events) > self.max_events:
            self._remove_node(self._events.popleft())

    # ------------------------------------------------------------------ topologia
    def add_cell(self, cell_id: str, **attrs: Any) -> None:
        self.add_node(cell_id, "cell", **attrs)

    def add_neighbors(self, a: str, b: str) -> None:
        self.add_cell(a)
        self.add_cell(b)
        self.add_edge(a, "NEIGHBOR_OF", b)
        self.add_edge(b, "NEIGHBOR_OF", a)

    def neighbors(self, cell_id: str) -> Set[str]:
        return set(self.successors(cell_id, "NEIGHBOR_OF"))

    def neighbor_map(self) -> Dict[str, Set[str]]:
        return {n.id: self.neighbors(n.id) for n in self.nodes("cell") if self.neighbors(n.id)}

    def add_parameter(self, parameter: str, kpis: Iterable[str]) -> None:
        self.add_node(f"param:{parameter}", "parameter", name=parameter)
        for kpi in kpis:
            self.add_node(f"kpi:{kpi}", "kpi", name=kpi)
            self.add_edge(f"param:{parameter}", "AFFECTS", f"kpi:{kpi}")

    def affected_kpis(self, parameter: str) -> List[str]:
        return [k.split(":", 1)[1] for k in self.successors(f"param:{parameter}", "AFFECTS")]

    def shared_kpis(self, param_a: str, param_b: str) -> Set[str]:
        return set(self.affected_kpis(param_a)) & set(self.affected_kpis(param_b))

    # ------------------------------------------------------------------ eventos
    def record_action(self, action) -> str:
        aid = f"action:{action.action_id}"
        self.add_node(aid, "action", xapp_id=action.xapp_id, parameter=action.parameter,
                      value=float(action.value), priority=int(action.priority), timestamp=float(action.timestamp))
        self.add_node(f"xapp:{action.xapp_id}", "xapp")
        self.add_cell(action.node_id)
        self.add_edge(f"xapp:{action.xapp_id}", "PROPOSED", aid)
        self.add_edge(aid, "TARGETS", action.node_id, parameter=action.parameter)
        return aid

    def record_conflict(self, conflict) -> str:
        cid = f"conflict:{conflict.conflict_id}"
        self.add_node(cid, "conflict", type=conflict.conflict_type.name, severity=conflict.severity.name,
                      description=conflict.description, detected_at=float(conflict.detected_at))
        for action in conflict.involved_xapps:
            self.add_edge(cid, "INVOLVES", self.record_action(action))
        return cid

    def record_decision(self, decision_id: str, strategy: str, selected: Iterable, conflict_ids: Iterable[str] = (),
                        policy: Optional[Dict[str, Any]] = None, source: str = "H_RDL") -> str:
        did = f"decision:{decision_id}"
        self.add_node(did, "decision", strategy=strategy, source=source, timestamp=time.time())
        for action in selected:
            self.add_edge(did, "SELECTED", self.record_action(action))
        for conflict_id in conflict_ids:
            cid = f"conflict:{conflict_id}"
            if self.has_node(cid):
                self.add_edge(cid, "RESOLVED_BY", did)
        if policy:
            pid = "policy:" + json.dumps(policy, sort_keys=True)
            self.add_node(pid, "policy", **{k: v for k, v in policy.items()})
            self.add_edge(pid, "GOVERNS", did)
        return did

    # ------------------------------------------------------------------ consultas de contexto
    def conflicts_on(self, cell_id: str, parameter: Optional[str] = None, since: float = 0.0) -> List[str]:
        """Conflitos recentes que envolveram ações sobre a célula (e parâmetro)."""
        found: Set[str] = set()
        for aid in self.predecessors(cell_id, "TARGETS"):
            if parameter is not None and self.edge(aid, "TARGETS", cell_id).get("parameter") != parameter:
                continue
            for cid in self.predecessors(aid, "INVOLVES"):
                if self._nodes[cid].attrs.get("detected_at", 0.0) >= since:
                    found.add(cid)
        return sorted(found)

    def context_features(self, cell_id: str, parameter: str, since: float = 0.0) -> Dict[str, float]:
        """Atributos numéricos para o raciocínio (usados pela RDL-N2 da Fase 2)."""
        conflicts = self.conflicts_on(cell_id, parameter, since)
        inter_cell = sum(1 for c in conflicts if self._nodes[c].attrs.get("type") == "INTER_CELL")
        decisions = {d for c in conflicts for d in self.successors(c, "RESOLVED_BY")}
        xapps = {self.predecessors(a, "PROPOSED")[0] for a in self.predecessors(cell_id, "TARGETS")
                 if self.predecessors(a, "PROPOSED")}
        return {
            "neighbor_count": float(len(self.neighbors(cell_id))),
            "recent_conflicts": float(len(conflicts)),
            "recent_inter_cell_conflicts": float(inter_cell),
            "recent_decisions": float(len(decisions)),
            "distinct_xapps_on_cell": float(len(xapps)),
        }

    # ------------------------------------------------------------------ exportação
    def stats(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for n in self._nodes.values():
            counts[n.kind] = counts.get(n.kind, 0) + 1
        counts["edges"] = sum(len(d) for adj in self._out.values() for d in adj.values())
        return counts

    def op_totals(self) -> Dict[str, int]:
        """Consultas e escritas públicas acumuladas (o painel usa a diferença por decisão)."""
        return dict(self.op_counts)

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "schema": "xapp-rdl/knowledge-graph/v1",
                "nodes": [{"id": n.id, "kind": n.kind, **n.attrs} for n in self._nodes.values()],
                "edges": [{"src": s, "relation": r, "dst": d, **a}
                          for r, adj in self._out.items() for s, dsts in adj.items() for d, a in dsts.items()],
            }

    def to_json(self, path: Optional[str] = None) -> str:
        text = json.dumps(self.to_dict(), ensure_ascii=False, indent=1, default=str)
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
        return text


for _name in _QUERIES:
    setattr(KnowledgeGraph, _name, _counted("queries", getattr(KnowledgeGraph, _name)))
for _name in _WRITES:
    setattr(KnowledgeGraph, _name, _counted("writes", getattr(KnowledgeGraph, _name)))
