import time
from typing import Dict, List, Optional, Tuple
from src.conflict_types import XAppAction, ConflictEvent, ConflictType, ConflictSeverity, KPMReport
from src.core.inter_cell import HANDOVER_INTO_REDUCED_CELL, InterCellRules
from src.core.knowledge_graph import KnowledgeGraph


class Perception:
    """
    Componente de Percepção da H-RDL (Núcleo / Core).
    Responsável pela ingestão de telemetria E2SM-KPM com verificação de TTL,
    manutenção do grafo de dependência de KPIs e detecção determinística de
    colisões e conflitos multi-xApp, inclusive entre células vizinhas.
    """
    def __init__(self, kpm_ttl_s: float = 1.0, inter_cell_rules: Optional[InterCellRules] = None,
                 knowledge_graph: Optional[KnowledgeGraph] = None):
        self.kpm_ttl_s = kpm_ttl_s
        # Regras e topologia (vizinhança entre células) para conflitos entre células
        self.inter_cell_rules = inter_cell_rules or InterCellRules()
        # Grafo de conhecimento: topologia, parâmetro -> KPIs e histórico de conflitos/decisões
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()
        # Grafo de dependências KPI modelando as relações lógicas da rede
        self.kpi_dependency_graph = {
            "PRB_QUOTA": ["DRB.UEThpDl", "RRU.PrbUsedDl"],
            "SCHEDULER_WEIGHT": ["DRB.UEThpDl", "DRB.RlcSduDelayDl"],
            "TX_POWER": ["L1M.DL-sinr", "DRB.UEThpDl"],
            "HANDOVER": ["DRB.UEThpDl", "RRU.PrbUsedDl"],
            "VERTICAL_DOWNTILT": ["L1M.DL-sinr", "DRB.UEThpDl"],
            "BEAM_WEIGHTS": ["L1M.DL-sinr", "DRB.UEThpDl"],
            "SENSING_RATIO": ["RRU.PrbUsedDl", "DRB.UEThpDl"],
            "LOAD_THRESHOLD": ["RRU.PrbUsedDl", "DRB.UEThpDl"],
            "PING_INTERVAL": ["DRB.RlcSduDelayDl"],
            "CELL_STATE": ["DRB.UEThpDl", "RRU.PrbUsedDl", "L1M.DL-sinr"],
        }
        for parameter, kpis in self.kpi_dependency_graph.items():
            self.knowledge_graph.add_parameter(parameter, kpis)
        for node, adjacent in self.inter_cell_rules.neighbors.items():
            for other in adjacent:
                self.knowledge_graph.add_neighbors(node, other)
        # Registro das últimas ações: node_id -> parameter -> XAppAction
        self._action_registry: Dict[str, Dict[str, XAppAction]] = {}
        self.latest_kpm: Optional[KPMReport] = None
        self._kpm_by_node: Dict[str, KPMReport] = {}
        self._kpm_timestamps: Dict[str, float] = {}

    def update_kpm_report(self, report: KPMReport):
        self.latest_kpm = report
        self._kpm_by_node[report.node_id] = report
        report_ts = getattr(report, "timestamp", None)
        self._kpm_timestamps[report.node_id] = float(report_ts) if isinstance(report_ts, (int, float)) and report_ts > 0 else time.time()

    def get_kpm_report_with_ttl(self, node_id: str) -> Tuple[Optional[KPMReport], bool]:
        """Retorna (report, is_valid) aplicando TTL de 1000 ms (kpm_ttl_s)."""
        report = self._kpm_by_node.get(node_id)
        if report is None:
            return None, False
        if self.kpm_ttl_s > 0:
            ts = self._kpm_timestamps.get(node_id, getattr(report, "timestamp", 0.0))
            if ts > 0 and (time.time() - ts) > self.kpm_ttl_s:
                return None, False
        return report, True

    def get_latest_kpm(self, node_id: str) -> Optional[KPMReport]:
        report, is_valid = self.get_kpm_report_with_ttl(node_id)
        return report if is_valid else None

    def get_active_xapps(self) -> Dict[str, List[XAppAction]]:
        active = {}
        for node, params in self._action_registry.items():
            for param, action in params.items():
                if action.xapp_id not in active:
                    active[action.xapp_id] = []
                active[action.xapp_id].append(action)
        return active

    def detect_action_group(self, actions: List[XAppAction]) -> List[ConflictEvent]:
        """
        Detecta conflitos da Decision Window sem tratar propostas não selecionadas como estado ativo.

        Os conflitos são agrupados por alvo, e não por par de ações, para que o custo
        cresça linearmente com o número de propostas (os conflitos entre células são
        detectados em ``_detect_inter_cell``):

        - propostas repetidas de uma mesma xApp para o mesmo (nó, parâmetro) são
          deduplicadas, valendo a mais recente;
        - DIRECT: um único evento por (nó, parâmetro) com todas as propostas concorrentes
          e, como incumbente, a última ação confirmada pela RAN (quando de outra xApp);
        - INDIRECT: um evento por par de parâmetros do mesmo nó que compartilham KPIs,
          com os candidatos de ambos os parâmetros.

        O número de eventos fica limitado por O(P²) por nó (P = parâmetros), independente
        do volume de propostas.
        """
        conflicts: List[ConflictEvent] = []

        latest: Dict[Tuple[str, str, str], XAppAction] = {}
        for action in actions:
            latest[(action.node_id, action.parameter, action.xapp_id)] = action

        proposals_by_node: Dict[str, Dict[str, List[XAppAction]]] = {}
        for (node_id, parameter, _), action in latest.items():
            proposals_by_node.setdefault(node_id, {}).setdefault(parameter, []).append(action)

        for node_id, proposals_by_param in proposals_by_node.items():
            committed = self._action_registry.get(node_id, {})

            candidates: Dict[str, List[XAppAction]] = {}
            for parameter, proposals in proposals_by_param.items():
                members = list(proposals)
                incumbent = committed.get(parameter)
                if incumbent is not None and all(p.xapp_id != incumbent.xapp_id for p in proposals):
                    members.insert(0, incumbent)
                candidates[parameter] = members

            for parameter, members in candidates.items():
                if len({m.xapp_id for m in members}) > 1 and len({m.value for m in members}) > 1:
                    conflicts.append(ConflictEvent(
                        conflict_type=ConflictType.DIRECT,
                        severity=ConflictSeverity.HIGH,
                        involved_xapps=members,
                        affected_kpis=list(self.kpi_dependency_graph.get(parameter, [])),
                        description=f"Direct conflict on parameter {parameter} ({len(members)} candidates)"
                    ))

            all_params = sorted(set(candidates) | set(committed))
            for i, param_a in enumerate(all_params):
                for param_b in all_params[i + 1:]:
                    if param_a not in proposals_by_param and param_b not in proposals_by_param:
                        continue
                    common_kpis = set(self.kpi_dependency_graph.get(param_a, [])).intersection(
                        self.kpi_dependency_graph.get(param_b, [])
                    )
                    if not common_kpis:
                        continue
                    members_a = candidates.get(param_a) or [committed[param_a]]
                    members_b = candidates.get(param_b) or [committed[param_b]]
                    if not any(a.xapp_id != b.xapp_id for a in members_a for b in members_b):
                        continue
                    conflicts.append(ConflictEvent(
                        conflict_type=ConflictType.INDIRECT,
                        severity=ConflictSeverity.MEDIUM,
                        involved_xapps=members_a + members_b,
                        affected_kpis=sorted(common_kpis),
                        description=f"Indirect conflict on KPIs {sorted(common_kpis)} via params {param_a} and {param_b}"
                    ))

        conflicts.extend(self._detect_inter_cell(proposals_by_node))
        return conflicts

    def _detect_inter_cell(self, proposals_by_node: Dict[str, Dict[str, List[XAppAction]]]) -> List[ConflictEvent]:
        """
        Conflitos entre células (regras em ``src/core/inter_cell.py``).

        Considera as propostas da janela e, para alvos sem proposta, a última ação
        confirmada pela RAN: estados persistentes (célula desligada, potência reduzida)
        sempre; handovers confirmados até serem substituídos (ou por ``handover_hold_s``),
        com o ping-pong limitado a ``pingpong_window_s`` entre os dois handovers. Só as ações
        relevantes (HANDOVER, CELL_STATE e TX_POWER abaixo do limiar) são indexadas,
        e um evento é gerado por (regra, par de nós).
        """
        rules = self.inter_cell_rules
        now = time.time()
        relevant: List[XAppAction] = []
        targets_with_proposal = set()
        for node_id, by_param in proposals_by_node.items():
            for parameter, proposals in by_param.items():
                targets_with_proposal.add((node_id, parameter))
                relevant.extend(p for p in proposals if p.parameter == "HANDOVER" or rules.reduces_cell(p))
        for node_id, by_param in self._action_registry.items():
            for parameter, committed in by_param.items():
                if (node_id, parameter) in targets_with_proposal:
                    continue
                if parameter == "HANDOVER":
                    if rules.handover_hold_s is None or now - float(committed.timestamp) <= rules.handover_hold_s:
                        relevant.append(committed)
                elif rules.reduces_cell(committed):
                    relevant.append(committed)
        if len(relevant) < 2:
            return []

        handovers_by_target: Dict[str, List[XAppAction]] = {}
        reducing_by_node: Dict[str, List[XAppAction]] = {}
        for act in relevant:
            if act.parameter == "HANDOVER":
                target = rules.handover_target(act)
                if target is not None:
                    handovers_by_target.setdefault(target, []).append(act)
            else:
                reducing_by_node.setdefault(act.node_id, []).append(act)

        events: Dict[Tuple[str, Tuple[str, str]], List[XAppAction]] = {}

        def add(reason: str, a: XAppAction, b: XAppAction) -> None:
            key = (reason, tuple(sorted((a.node_id, b.node_id))))
            members = events.setdefault(key, [])
            for act in (a, b):
                if all(m is not act for m in members):
                    members.append(act)

        for target, handovers in handovers_by_target.items():
            for ho in handovers:
                for reducer in reducing_by_node.get(target, []):
                    reason = rules.pair_conflict(ho, reducer)
                    if reason is not None:
                        add(reason, ho, reducer)
                for reverse in handovers_by_target.get(ho.node_id, []):
                    if reverse.node_id == target:
                        reason = rules.pair_conflict(ho, reverse, check_time=True)
                        if reason is not None:
                            add(reason, ho, reverse)
        for node_id, reducers in reducing_by_node.items():
            for neighbor in rules.neighbors.get(node_id, set()):
                if neighbor <= node_id:
                    continue
                for a in reducers:
                    for b in reducing_by_node.get(neighbor, []):
                        reason = rules.pair_conflict(a, b)
                        if reason is not None:
                            add(reason, a, b)

        conflicts: List[ConflictEvent] = []
        for (reason, nodes), members in sorted(events.items()):
            kpis = sorted({kpi for m in members for kpi in self.kpi_dependency_graph.get(m.parameter, [])})
            conflicts.append(ConflictEvent(
                conflict_type=ConflictType.INTER_CELL,
                severity=ConflictSeverity.HIGH if reason == HANDOVER_INTO_REDUCED_CELL else ConflictSeverity.MEDIUM,
                involved_xapps=members,
                affected_kpis=kpis,
                description=f"Inter-cell conflict {reason} between {nodes[0]} and {nodes[1]}",
            ))
        return conflicts

    def commit_actions(self, actions: List[XAppAction]) -> None:
        """Persist actions admitted by RDL until replaced or explicitly removed."""
        for action in actions:
            if action.node_id not in self._action_registry:
                self._action_registry[action.node_id] = {}
            self._action_registry[action.node_id][action.parameter] = action

    def get_committed_action(self, node_id: str, parameter: str) -> Optional[XAppAction]:
        """Return the last control acknowledged by the RAN, if known."""
        return self._action_registry.get(node_id, {}).get(parameter)

    def remove_action(self, node_id: str, parameter: str) -> bool:
        """Remove a persisted action when its owner or control state is withdrawn."""
        node_actions = self._action_registry.get(node_id)
        if not node_actions or parameter not in node_actions:
            return False
        del node_actions[parameter]
        if not node_actions:
            del self._action_registry[node_id]
        return True

    def register_action_group(self, actions: List[XAppAction]) -> List[ConflictEvent]:
        """Compatibility helper for callers that register an entire group as active."""
        conflicts = self.detect_action_group(actions)
        self.commit_actions(actions)
        return conflicts


# Alias de compatibilidade retroativa
PerceptionAgent = Perception
