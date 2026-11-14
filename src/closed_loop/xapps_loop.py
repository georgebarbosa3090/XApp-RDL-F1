# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
Malha fechada na bancada NORI com xApps reais (docs/16 §10.2, opção C do híbrido).

No modo ``RC_DECISION=xapps`` da kpm-probe, as propostas não vêm do catálogo: chegam pelo RMR 30000
(``RDL_ACTION_PROPOSAL``) das xApps que rodam no Near-RT RIC e leem o KPM real do gNB do NORI (RANSlicer-GreenRAN,
derivada do xSlice e ``embb_throughput``). A cada Indication KPM completa (par nó + UEs), a kpm-probe decide sobre
as propostas recebidas desde a decisão anterior e envia o RIC Control E2SM-RC; o ACK e o KPM_t1 fecham o ciclo,
como no NORI S8.

- ``ProposalWindow``: recebe e valida as propostas (JSON do ``RdlTransport``) e entrega as da janela, na ordem de
  chegada, com a última de cada (xApp, nó, parâmetro).
- ``decide_xapps``: B3 = pipeline real da RDL-N1 (``HrdlDecider``, o mesmo do modo catalog); B0/B1/B2 =
  ``src.core.baselines`` (sem coordenação, FIFO, prioridade estática). Só ``PRB_QUOTA`` do gNB do NORI é atuável
  (``catalog_loop.actuation_of``); o resto é decidido e registrado como não atuável.
"""

from __future__ import annotations

import json
import threading
from typing import Any, Dict, List, Optional, Sequence

from src.core import baselines as bl
from src.closed_loop.catalog_loop import BASELINE_RULE, BASELINE_SOURCE, actuation_of
from src.closed_loop.hrdl_slice_loop import ENGINE, HrdlDecider, quotas_for, slice_state

REQUIRED = ("xapp_id", "parameter", "value")


class ProposalWindow:
    """Propostas recebidas pelo RMR 30000 entre duas decisões (seguro entre threads)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._items: List[Dict[str, Any]] = []
        self._seq = 0
        self.rejected = 0

    def add(self, payload: bytes, received_at: float, meid: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            p = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            p = None
        if not isinstance(p, dict) or any(k not in p for k in REQUIRED):
            with self._lock:
                self.rejected += 1
            return None
        with self._lock:
            self._seq += 1
            item = dict(p, _seq=self._seq, _received_at=received_at, _meid=meid)
            self._items.append(item)
        return item

    def drain(self) -> List[Dict[str, Any]]:
        """As propostas da janela, na ordem de chegada; fica a última de cada (xApp, nó, parâmetro)."""
        with self._lock:
            items, self._items = self._items, []
        last: Dict[tuple, Dict[str, Any]] = {}
        for p in items:
            last[(p["xapp_id"], str(p.get("node_id", "")), p["parameter"])] = p
        return sorted(last.values(), key=lambda p: p["_seq"])


def to_actions(proposals: Sequence[Dict[str, Any]], meid: str) -> List[Any]:
    """Propostas como XAppAction no alvo ``<meid>#g<gNB>``: a célula do NORI é o gNB 0; um ``node_id`` que não é o
    nó do NORI fica num gNB inexistente e é decidido como não atuável."""
    from src.conflict_types import XAppAction
    out = []
    for p in proposals:
        node = str(p.get("node_id") or meid)
        gnb = 0 if node in (meid, "gnb_0", "") else 1
        out.append(XAppAction(xapp_id=str(p["xapp_id"]), node_id=f"{meid}#g{gnb}", parameter=str(p["parameter"]),
                              value=float(p["value"]), priority=int(p.get("priority", 50)),
                              action_id=f"{p['xapp_id']}-{p['parameter']}-{p['_seq']}"))
    return out


def decide_xapps(baseline: str, meid: str, node: Dict[str, Any], ues: Sequence[Dict[str, Any]],
                 proposals: Sequence[Dict[str, Any]], decider: Optional[HrdlDecider] = None,
                 a1_policies: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Decisão sobre as propostas da janela. ``control_sequence``: cotas de cada RIC Control, na ordem de envio."""
    if baseline not in BASELINE_SOURCE:
        raise ValueError(f"baseline desconhecido: {baseline} (B0, B1, B2, B3)")
    actions = to_actions(proposals, meid)
    record: Dict[str, Any] = {
        "decision_source": BASELINE_SOURCE[baseline], "baseline": baseline, "mode": "xapps", "engine": ENGINE,
        "state": slice_state(node, ues),
        "proposals": [{"action_id": a.action_id, "xapp_id": a.xapp_id, "target": a.node_id, "parameter": a.parameter,
                       "value": a.value, "priority": a.priority} for a in actions],
        "resolutions": [], "selected": [], "not_selected": [], "not_actuated": [], "actuated": None,
        "actuated_sequence": [], "control_sequence": [], "quotas": [],
    }
    if not actions:
        record["reason"] = "nenhuma proposta das xApps na janela"
        return record
    if baseline == "B3":
        own = decider is None
        decider = decider or HrdlDecider()
        try:
            if a1_policies:
                manager = decider.app.a1_policies
                for key, body in a1_policies.items():
                    type_id, _, instance_id = key.partition(":")
                    manager.put_policy(type_id, instance_id, body)
                record["a1_policy"] = manager.effective_policy()
            out = decider.decide(actions)
        finally:
            if own:
                decider.close()
        record["resolutions"] = out["resolutions"]
        record["decision_wall_ms"] = out["decision_wall_ms"]
        selected = list(out["selected"])
    else:
        rank = {id(a): i for i, a in enumerate(actions)}
        selected = bl.select(actions, baseline, lambda a: (a.node_id, a.parameter), lambda a: rank[id(a)],
                             lambda a: a.priority)
        record["rule"] = BASELINE_RULE[baseline]
    record["selected"] = [{"action_id": a.action_id, "xapp_id": a.xapp_id, "target": a.node_id,
                           "parameter": a.parameter, "value": a.value, **actuation_of(a)} for a in selected]
    record["not_selected"] = sorted({a.action_id for a in actions} - {a.action_id for a in selected})
    record["not_actuated"] = [s for s in record["selected"] if not s["actuable"]]
    actuable = [a for a in selected if actuation_of(a)["actuable"]]
    if not actuable:
        record["reason"] = "nenhuma ação selecionada é atuável no NORI (sem RIC Control)"
        return record
    seq = actuable if baseline == "B0" else actuable[:1]       # B0: toda ação vai à RAN, na ordem; vale a última
    record["actuated_sequence"] = [{"action_id": a.action_id, "xapp_id": a.xapp_id, "value": a.value} for a in seq]
    record["control_sequence"] = [[q.__dict__ for q in quotas_for(a.value)] for a in seq]
    last = seq[-1]
    record["actuated"] = {"action_id": last.action_id, "xapp_id": last.xapp_id, "value": last.value}
    record["quotas"] = record["control_sequence"][-1]
    record["reason"] = f"{baseline}: ação de PRB do gNB do NORI atuada por E2SM-RC"
    return record
