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


# ---------------------------------------------------------------------------
# Baselines B0–B2 na bancada NORI (campanha do G5): a mesma semântica da pilha nativa
# (scripts/certification/run_conflict_experiment.py), numa única janela de decisão por execução.
# ---------------------------------------------------------------------------

BASELINES = ("B0", "B1", "B2", "B3")
BASELINE_SOURCE = {"B0": "BASELINE_B0", "B1": "BASELINE_B1", "B2": "BASELINE_B2", "B3": "H_RDL"}
BASELINE_RULE = {"B0": "apply-on-arrival", "B1": "fifo-per-target", "B2": "static-priority-per-target"}


def arrival_order(catalog: Dict[str, Any], scenario: str, node_id: str) -> List[Any]:
    """Primeira ocorrência de cada (xApp, gNB, parâmetro), na ordem de chegada da pilha nativa:
    instante e, no empate, o identificador ``<xApp>-g<gNB>-<parâmetro>-<t>`` (``expand_proposals``)."""
    spec = catalog["scenarios"][scenario]
    by_key = {a.action_id: a for a in catalog_actions(catalog, scenario, node_id)}
    keyed = []
    seen = set()
    for p in spec["proposals"]:
        key = (p["xapp_id"], int(p["gnb"]), p["parameter"])
        if key in seen:
            continue
        seen.add(key)
        t = float(p["start"])
        native_id = f"{p['xapp_id']}-g{int(p['gnb'])}-{p['parameter']}-{t:.3f}"
        keyed.append(((round(t, 6), native_id), by_key[f"{scenario}-{p['xapp_id']}-g{int(p['gnb'])}-{p['parameter']}"]))
    return [a for _, a in sorted(keyed, key=lambda kv: kv[0])]


def decide_baseline(scenario: str, baseline: str, node_id: str, node: Dict[str, Any],
                    ues: Sequence[Dict[str, Any]], catalog: Dict[str, Any]) -> Dict[str, Any]:
    """Decisão de um baseline sem H-RDL. ``control_sequence``: cotas de cada RIC Control, na ordem de envio.

    - B0 (sem coordenação): toda proposta atuável vai à RAN na ordem de chegada; vale a última.
    - B1 (FIFO): por alvo (gNB, parâmetro), a primeira a chegar.
    - B2 (prioridade estática): por alvo, a de maior prioridade (empate: a primeira a chegar).
    """
    if baseline not in BASELINE_RULE:
        raise ValueError(f"baseline sem H-RDL desconhecido: {baseline} (B0, B1, B2)")
    order = arrival_order(catalog, scenario, node_id)
    if baseline == "B0":
        selected = list(order)
    else:
        by_target: Dict[Any, List[Any]] = {}
        for a in order:
            by_target.setdefault((a.node_id, a.parameter), []).append(a)
        if baseline == "B1":
            selected = [cands[0] for cands in by_target.values()]
        else:
            selected = [min(cands, key=lambda a: (-a.priority, order.index(a))) for cands in by_target.values()]
    actuable = [a for a in selected if actuation_of(a)["actuable"]]
    record: Dict[str, Any] = {
        "decision_source": BASELINE_SOURCE[baseline], "baseline": baseline, "rule": BASELINE_RULE[baseline],
        "mode": "catalog", "scenario": scenario, "scenario_summary": catalog["scenarios"][scenario].get("summary"),
        "state": slice_state(node, ues),
        "proposals": [{"action_id": a.action_id, "xapp_id": a.xapp_id, "target": a.node_id, "parameter": a.parameter,
                       "value": a.value, "priority": a.priority} for a in order],
        "resolutions": [],
        "selected": [{"action_id": a.action_id, "xapp_id": a.xapp_id, "target": a.node_id, "parameter": a.parameter,
                      "value": a.value, **actuation_of(a)} for a in selected],
        "not_selected": sorted({a.action_id for a in order} - {a.action_id for a in selected}),
        "actuated": None, "actuated_sequence": [], "control_sequence": [], "quotas": [],
    }
    record["not_actuated"] = [s for s in record["selected"] if not s["actuable"]]
    if actuable:
        record["actuated_sequence"] = [{"action_id": a.action_id, "xapp_id": a.xapp_id, "value": a.value} for a in actuable]
        record["control_sequence"] = [[q.__dict__ for q in quotas_for(a.value)] for a in actuable]
        last = actuable[-1]
        record["actuated"] = {"action_id": last.action_id, "xapp_id": last.xapp_id, "value": last.value}
        record["quotas"] = record["control_sequence"][-1]
        record["reason"] = f"{baseline} ({BASELINE_RULE[baseline]}): ação de PRB do gNB 0 atuada por E2SM-RC"
    else:
        record["reason"] = "nenhuma ação selecionada é atuável no NORI (sem RIC Control)"
    return record
