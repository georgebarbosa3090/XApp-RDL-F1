"""
Porte dos cenários de conflito S0–S8 para a bancada NORI (E2 real): catálogo -> H-RDL -> RIC Control.

A pilha nativa (ns-3.48) reproduz a topologia de cada cenário mas não tem E2. No NORI, a carga de
conflito de cada cenário é a mesma do catálogo (``simulations/ns3/conflicts/catalog.json``): as
propostas das xApps vão ao pipeline real da xApp RDL (``RDLxApp._process_action_group``) e a ação
vencedora sai como RIC Control E2SM-RC pela cadeia E2 real.

Mapeamento para o NORI (um gNB, duas fatias: eMBB SST 1 e URLLC SST 2):

- Cada proposta mantém o gNB de origem no alvo (``<nó>#g<gNB>``): o H-RDL vê os mesmos conflitos
  (diretos e indiretos) da pilha nativa.
- Só ``PRB_QUOTA`` no gNB 0 (a célula portada) é atuável: vira cotas de PRB por fatia, com
  ``PRB_QUOTA`` = teto % da fatia eMBB e a URLLC com o complemento (``quotas_for``).
- ``TX_POWER`` não existe no E2SM-RC do NORI, ``HANDOVER`` é só registrado em log pelo NORI (e o
  cenário tem um único gNB), e ações em gNB ≥ 1 não têm célula correspondente: são decididas pelo
  H-RDL e registradas como não atuáveis, sem Control.
- Uma decisão por execução: as propostas do cenário (primeira ocorrência de cada xApp/gNB/parâmetro)
  formam uma única janela de decisão, disparada pelo KPM_t0.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from src.closed_loop.hrdl_slice_loop import ENGINE, HrdlDecider, quotas_for, slice_state

ACTUABLE_PARAMETER = "PRB_QUOTA"
ACTUABLE_GNB = 0
NOT_ACTUABLE_REASON = {
    "TX_POWER": "potência de transmissão não existe no E2SM-RC do NORI",
    "HANDOVER": "handover é só registrado em log pelo NORI (cenário com um único gNB)",
}


def load_catalog(path: Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def catalog_actions(catalog: Dict[str, Any], scenario: str, node_id: str) -> List[Any]:
    """Propostas do cenário como XAppAction, primeira ocorrência por (xApp, gNB, parâmetro)."""
    from src.conflict_types import XAppAction
    spec = catalog["scenarios"][scenario]
    seen, actions = set(), []
    for p in sorted(spec["proposals"], key=lambda p: (float(p["start"]), p["xapp_id"])):
        key = (p["xapp_id"], int(p["gnb"]), p["parameter"])
        if key in seen:
            continue
        seen.add(key)
        actions.append(XAppAction(xapp_id=p["xapp_id"], node_id=f"{node_id}#g{int(p['gnb'])}",
                                  parameter=p["parameter"], value=float(p["value"]), priority=int(p["priority"]),
                                  action_id=f"{scenario}-{p['xapp_id']}-g{int(p['gnb'])}-{p['parameter']}"))
    return actions


def actuation_of(action: Any) -> Dict[str, Any]:
    gnb = int(str(action.node_id).rsplit("#g", 1)[-1]) if "#g" in str(action.node_id) else 0
    if action.parameter == ACTUABLE_PARAMETER and gnb == ACTUABLE_GNB:
        return {"actuable": True}
    if gnb != ACTUABLE_GNB:
        return {"actuable": False, "reason": f"gNB {gnb} não existe na bancada NORI (só a célula do gNB 0 foi portada)"}
    return {"actuable": False, "reason": NOT_ACTUABLE_REASON.get(action.parameter, "parâmetro sem atuação no NORI")}


def decide_catalog(scenario: str, node_id: str, node: Dict[str, Any], ues: Sequence[Dict[str, Any]],
                   catalog: Dict[str, Any], decider: Optional[HrdlDecider] = None) -> Dict[str, Any]:
    """Decisão do H-RDL sobre as propostas do cenário; ``quotas`` vazio se nada for atuável."""
    proposals = catalog_actions(catalog, scenario, node_id)
    record: Dict[str, Any] = {
        "decision_source": "H_RDL", "engine": ENGINE, "mode": "catalog", "scenario": scenario,
        "scenario_summary": catalog["scenarios"][scenario].get("summary"),
        "state": slice_state(node, ues),
        "proposals": [{"action_id": a.action_id, "xapp_id": a.xapp_id, "target": a.node_id,
                       "parameter": a.parameter, "value": a.value, "priority": a.priority} for a in proposals],
        "resolutions": [], "selected": [], "actuated": None, "not_actuated": [], "quotas": [],
        "decision_wall_ms": None,
    }
    own = decider is None
    decider = decider or HrdlDecider()
    try:
        out = decider.decide(proposals)
    finally:
        if own:
            decider.close()
    record["resolutions"] = out["resolutions"]
    record["decision_wall_ms"] = out["decision_wall_ms"]
    selected = list(out["selected"])
    record["selected"] = [{"action_id": a.action_id, "xapp_id": a.xapp_id, "target": a.node_id,
                           "parameter": a.parameter, "value": a.value, **actuation_of(a)} for a in selected]
    blocked = {a.action_id for a in proposals} - {a.action_id for a in selected}
    record["not_selected"] = sorted(blocked)
    actuable = [a for a in selected if actuation_of(a)["actuable"]]
    record["not_actuated"] = [s for s in record["selected"] if not s["actuable"]]
    if actuable:
        winner = actuable[0]
        record["actuated"] = {"action_id": winner.action_id, "xapp_id": winner.xapp_id, "value": winner.value}
        record["quotas"] = [q.__dict__ for q in quotas_for(winner.value)]
        record["reason"] = "ação de PRB do gNB 0 selecionada pelo H-RDL e atuada por E2SM-RC"
    else:
        record["reason"] = "nenhuma ação selecionada é atuável no NORI (sem RIC Control)"
    return record
