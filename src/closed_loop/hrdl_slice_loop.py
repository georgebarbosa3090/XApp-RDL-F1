"""
Ponte da malha fechada (fase 4): KPM_t0 (E2SM-KPM v3) -> decisão RDL-N1 -> cotas de PRB (E2SM-RC v3).

1. ``slice_state``: estado da célula a partir do KPM decodificado (``src/e2/v3/codec.py``). Usa só o
   que o KPM do NORI mede de fato: PRB usados e disponíveis do nó (congestionamento) e a fatia de
   cada UE (``DRB.NetworkSlicing.SST``). A vazão por UE do KPM do NORI (``DRB.UEThpDl``) sai sempre 0
   e não é usada.
2. ``reference_proposals``: duas políticas de referência, fixadas antes das execuções, geram
   propostas conflitantes para o mesmo alvo (nó, ``PRB_QUOTA``) quando a célula está congestionada
   e há UEs nas fatias eMBB (SST 1) e URLLC (SST 2):

   - ``xapp-qos-xslice`` (prioridade 90): protege a URLLC, propõe teto de 25 % de PRB para a eMBB;
   - ``xapp-embb-throughput`` (prioridade 60): maximiza a vazão eMBB, propõe teto de 80 %.

   Valores da v2 (pré-registro docs/preregistros/01_fase4_v2.md). Na v1 (commit b48473d) a protetora
   propunha 40 %; o TVS a escolheu e o teto não restringiu (a eMBB usava ~40 % dos PRBs).

   ``PRB_QUOTA`` é o teto de PRB (%) da fatia eMBB; a URLLC recebe ``100 - PRB_QUOTA``.
3. ``HrdlDecider``: o pipeline real da xApp RDL (``RDLxApp.process_actions``: Safety Guard,
   Perception, Reasoning TVS/EEVS, Refinement), com o despacho capturado — o mesmo caminho do B3 na
   campanha. Uma instância nova por decisão, para que o histórico de uma execução não decida a outra.
4. ``decide_slice_quotas``: junta tudo e devolve o registro da decisão (estado, propostas,
   resoluções, ação selecionada, cotas) que a xApp grava ao lado dos bytes do Control.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional, Sequence

from src.e2.v3.codec import SlicePrbQuota

CONGESTION_RATIO = 0.95       # congestionada: PRB usados >= 95 % dos disponíveis (KPM do nó)
SST_EMBB, SST_URLLC = 1, 2
POLICIES = (
    # (xapp_id, prioridade, PRB_QUOTA proposto = teto % da fatia eMBB, justificativa)
    ("xapp-qos-xslice", 90, 25, "protege a URLLC sob congestionamento: teto de 25 % para a eMBB"),
    ("xapp-embb-throughput", 60, 80, "maximiza a vazão eMBB sob congestionamento: teto de 80 % para a eMBB"),
)
ENGINE = "src/rdl_xapp.py RDLxApp.process_actions"


def slice_state(node: Dict[str, Any], ues: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Estado da célula a partir do KPM_t0 (Format 1 do nó e Format 3 por UE)."""
    used, avail = node.get("RRU.PrbUsedDl"), node.get("RRU.PrbAvailDl")
    slices: Dict[int, List[Any]] = {}
    for ue in ues:
        sst = (ue.get("measurements") or {}).get("DRB.NetworkSlicing.SST")
        if sst is not None:
            slices.setdefault(int(sst), []).append(ue.get("ue_id"))
    congested = bool(avail) and used is not None and float(used) >= CONGESTION_RATIO * float(avail)
    return {"prb_used_dl": used, "prb_avail_dl": avail, "congested": congested,
            "congestion_ratio": CONGESTION_RATIO, "ues_by_sst": {str(k): v for k, v in sorted(slices.items())}}


def reference_proposals(state: Dict[str, Any], node_id: str) -> List[Any]:
    from src.conflict_types import XAppAction
    present = {int(k) for k in state["ues_by_sst"]}
    if not state["congested"] or not {SST_EMBB, SST_URLLC} <= present:
        return []
    return [XAppAction(xapp_id=xapp, node_id=node_id, parameter="PRB_QUOTA", value=float(value), priority=prio,
                       action_id=f"{xapp}-{node_id}-PRB_QUOTA")
            for xapp, prio, value, _ in POLICIES]


def quotas_for(prb_quota_embb: float) -> List[SlicePrbQuota]:
    embb = int(round(prb_quota_embb))
    return [SlicePrbQuota(SST_EMBB, embb, 0, 0), SlicePrbQuota(SST_URLLC, 100 - embb, 0, 0)]


class HrdlDecider:
    """Pipeline real do RDL-N1 fora do RIC, com o despacho de controle capturado."""

    def __init__(self) -> None:
        saved = {k: os.environ.pop(k, None) for k in ("SUBMGR_URL",)}   # sem subscrição própria do RDLxApp
        os.environ.setdefault("RDL_MODE", "OFFLINE_SIMULATION")
        os.environ.setdefault("USE_FAKE_SDL", "True")
        os.environ.setdefault("RAN_BACKEND", "NORI_NS3")
        try:
            from src.rdl_xapp import RDLxApp
            previous = logging.root.manager.disable
            logging.disable(logging.INFO)
            try:
                self.app = RDLxApp()
            finally:
                logging.disable(previous)
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v
        self.dispatched: List[Any] = []
        self.resolutions: List[Dict[str, Any]] = []
        original_resolve = self.app.reasoning.resolve

        def capture_dispatch(decision, decision_latency_ms=None):
            self.dispatched.append(decision.selected_actions[0])
            return f"closed-loop-{decision.selected_actions[0].action_id}"

        def capture_resolve(conflict):
            resolution = original_resolve(conflict)
            self.resolutions.append({
                "conflict_type": conflict.conflict_type.name,
                "involved": [a.action_id for a in conflict.involved_xapps],
                "winners": [a.action_id for a in resolution.winning_actions],
                "strategy": resolution.strategy_used.name,
                "confidence": resolution.confidence,
            })
            return resolution

        self.app.dispatcher.dispatch_control = capture_dispatch
        self.app.reasoning.resolve = capture_resolve

    def decide(self, actions: Sequence[Any]) -> Dict[str, Any]:
        started = time.perf_counter()
        self.app.process_actions(list(actions))
        return {"selected": list(self.dispatched), "resolutions": list(self.resolutions),
                "decision_wall_ms": round((time.perf_counter() - started) * 1000.0, 3)}

    def close(self) -> None:
        self.app.stop()


def decide_slice_quotas(node_id: str, node: Dict[str, Any], ues: Sequence[Dict[str, Any]],
                        decider: Optional[HrdlDecider] = None) -> Dict[str, Any]:
    """Decisão completa a partir do KPM_t0; ``quotas`` vazio quando o RDL-N1 não seleciona ação."""
    state = slice_state(node, ues)
    proposals = reference_proposals(state, node_id)
    record: Dict[str, Any] = {
        "decision_source": "H_RDL", "engine": ENGINE, "state": state,
        "policies": [{"xapp_id": x, "priority": p, "prb_quota_embb": v, "rationale": r} for x, p, v, r in POLICIES],
        "proposals": [{"action_id": a.action_id, "xapp_id": a.xapp_id, "parameter": a.parameter,
                       "value": a.value, "priority": a.priority} for a in proposals],
        "resolutions": [], "selected": None, "quotas": [], "decision_wall_ms": None,
    }
    if not proposals:
        record["reason"] = "sem propostas: célula não congestionada ou fatias ausentes no KPM_t0"
        return record
    own = decider is None
    decider = decider or HrdlDecider()
    try:
        out = decider.decide(proposals)
    finally:
        if own:
            decider.close()
    record["resolutions"] = out["resolutions"]
    record["decision_wall_ms"] = out["decision_wall_ms"]
    selected = [a for a in out["selected"] if a.parameter == "PRB_QUOTA"]
    if not selected:
        record["reason"] = "RDL-N1 não selecionou ação (bloqueada pelo Safety Guard ou sem vencedor)"
        return record
    winner = selected[0]
    record["selected"] = {"action_id": winner.action_id, "xapp_id": winner.xapp_id, "value": winner.value,
                          "priority": winner.priority}
    record["quotas"] = [q.__dict__ for q in quotas_for(winner.value)]
    record["reason"] = "ação selecionada pelo RDL-N1"
    return record
