from typing import List, Tuple
from src.conflict_types import ConflictEvent, ResolutionAction, ResolutionStrategy, XAppAction
from src.infrastructure.sdl_repository import SdlRepository
import math
import itertools

class ReasoningAgent:
    def __init__(self, memory: SdlRepository, config: dict):
        self.memory = memory
        self.config = config
        
        # Pesos para conflito DIRETO
        self.w_sla = self.config.get("w_sla", 0.35)
        self.w_throughput = self.config.get("w_throughput", 0.25)
        self.w_energy = self.config.get("w_energy", 0.20)
        self.w_stability = self.config.get("w_stability", 0.10)
        self.w_priority = self.config.get("w_priority", 0.10)

        # Pesos para conflito INDIRETO
        self.w_qos_ind = self.config.get("w_qos_ind", 0.30)
        self.w_energy_ind = self.config.get("w_energy_ind", 0.20)
        self.w_fairness_ind = self.config.get("w_fairness_ind", 0.20)
        self.w_viol_ind = self.config.get("w_viol_ind", 0.30)

    def resolve(self, conflict: ConflictEvent) -> ResolutionAction:
        # 4.1 Consultar histórico
        similar_resolutions = self.memory.get_similar_resolutions(conflict)
        if similar_resolutions:
            best_res = similar_resolutions[0]
            if best_res.confidence >= 0.8:  # theta threshold
                return self._resolve_by_history(conflict, similar_resolutions)
                
        # 4.2 Se conflito DIRETO
        if conflict.conflict_type.name == "DIRECT":
            return self._resolve_direct_conflict(conflict)
            
        # 4.3 Se conflito INDIRETO
        return self._resolve_indirect_conflict(conflict)

    def _resolve_direct_conflict(self, conflict: ConflictEvent) -> ResolutionAction:
        actions = conflict.involved_xapps
        best_score = -float("inf")
        best_action = None

        for act in actions:
            sla_score = self._mock_score(act, "SLA")
            tput_score = self._mock_score(act, "Throughput")
            nrg_score = self._mock_score(act, "Energy")
            stab_score = self._mock_score(act, "Stability")
            prio_score = self._mock_score(act, "Priority")

            u_a = (self.w_sla * sla_score +
                   self.w_throughput * tput_score +
                   self.w_energy * nrg_score +
                   self.w_stability * stab_score +
                   self.w_priority * prio_score)
            
            if u_a > best_score:
                best_score = u_a
                best_action = act

        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=ResolutionStrategy.TVS, 
            winning_actions=[best_action] if best_action else [],
            modified_value=best_action.value if best_action else None,
            confidence=0.9,
            validation_level=0
        )

    def _resolve_indirect_conflict(self, conflict: ConflictEvent) -> ResolutionAction:
        actions = conflict.involved_xapps
        best_score = -float("inf")
        best_subset = []

        powerset = []
        for i in range(1, len(actions) + 1):
            powerset.extend(list(itertools.combinations(actions, i)))
            
        for subset in powerset:
            if self._has_physical_incompatibility(list(subset)):
                score = -float("inf")
            else:
                qos = self._mock_subset_score(list(subset), "QoS")
                energy = self._mock_subset_score(list(subset), "Energy")
                fairness = self._mock_subset_score(list(subset), "Fairness")
                violations = self._mock_subset_score(list(subset), "Violations")

                score = (self.w_qos_ind * qos +
                         self.w_energy_ind * energy +
                         self.w_fairness_ind * fairness -
                         self.w_viol_ind * violations)
                         
            if score > best_score:
                best_score = score
                best_subset = list(subset)
                
        modified_val = best_subset[0].value if len(best_subset) == 1 else None

        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=ResolutionStrategy.EEVS, 
            winning_actions=best_subset,
            modified_value=modified_val,
            confidence=0.8,
            validation_level=0
        )

    def _has_physical_incompatibility(self, subset: List[XAppAction]) -> bool:
        param_targets = {}
        for act in subset:
            key = f"{act.node_id}_{act.parameter}"
            if key in param_targets and param_targets[key] != act.value:
                return True
        return False

    def _mock_score(self, act: XAppAction, metric: str) -> float:
        val = act.value
        if metric == "SLA":
            return 0.95 if val > 50 else 0.60
        elif metric == "Throughput":
            return 0.90 if val > 50 else 0.55
        elif metric == "Energy":
            return 0.40 if val > 50 else 0.85
        elif metric == "Stability":
            return 0.80
        elif metric == "Priority":
            return 0.80 if act.xapp_id == "qos_xapp" else 0.60
        return 0.5

    def _mock_subset_score(self, subset: List[XAppAction], metric: str) -> float:
        total_val = sum(a.value for a in subset)
        if metric == "QoS":
            return min(1.0, total_val / 100.0)
        elif metric == "Energy":
            return max(0.0, 1.0 - (total_val / 150.0))
        elif metric == "Fairness":
            return 0.8
        elif metric == "Violations":
            return total_val / 200.0
        return 0.5

    def _resolve_by_history(self, conflict: ConflictEvent, similar: List[ResolutionAction]) -> ResolutionAction:
        best_past_res = similar[0]
        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=best_past_res.strategy_used,
            winning_actions=best_past_res.winning_actions,
            modified_value=best_past_res.modified_value,
            confidence=best_past_res.confidence,
            validation_level=0
        )

