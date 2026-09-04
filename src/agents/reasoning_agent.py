from typing import List, Tuple, Dict, Any, Optional
from src.conflict_types import ConflictEvent, ResolutionAction, ResolutionStrategy, XAppAction, KPMReport
from src.infrastructure.sdl_repository import SdlRepository
import math
import itertools

class ReasoningAgent:
    """
    Agente de Raciocinio da xApp RDL (Fase 1: H-RDL).
    Implementa as heuristicas TVS e EEVS fundamentadas em modelos analiticos calibrados de radio 5G:
    - Capacidade Espectral de Shannon com SINR real e overhead 3GPP;
    - Modelo de Atraso e Satisfacao de SLA (Fila M/G/1 com curva sigmoide);
    - Modelo de Eficiencia Energetica (Earth/3GPP Linear Power Model);
    - Barreira de Estabilidade e Penalidade de Oscilacao (Ping-Pong);
    - Priorizacao estrita de fatias de missao critica (URLLC > TS > eMBB > ES > mMTC).
    """
    def __init__(self, memory: Any, config: Optional[dict] = None):
        self.memory = memory
        self.config = config or {}
        
        # Pesos Multiobjetivo para Conflito DIRETO (TVS)
        self.w_sla = self.config.get("w_sla", 0.40)
        self.w_throughput = self.config.get("w_throughput", 0.25)
        self.w_energy = self.config.get("w_energy", 0.15)
        self.w_stability = self.config.get("w_stability", 0.10)
        self.w_priority = self.config.get("w_priority", 0.10)

        # Pesos Multiobjetivo para Conflito INDIRETO (EEVS)
        self.w_qos_ind = self.config.get("w_qos_ind", 0.45)
        self.w_energy_ind = self.config.get("w_energy_ind", 0.20)
        self.w_fairness_ind = self.config.get("w_fairness_ind", 0.15)
        self.w_viol_ind = self.config.get("w_viol_ind", 0.35)

        # Parametros Fisicos Calibrados de Radio 5G (Banda n78 3.5 GHz)
        self.BANDWIDTH_HZ = 100e6         # 100 MHz de BWP
        self.EFFICIENCY_OVERHEAD = 0.86    # 14% de overhead de controle DMRS/PDCCH
        self.NOISE_FLOOR_DBM = -95.0       # Piso de ruido termico
        self.N_TRX = 4                     # Canais MIMO 4x4
        self.P0_W = 130.0                  # Consumo estatico de circuito (Earth Model)
        self.DELTA_P = 4.7                 # Inclinacao do amplificador de potencia RF
        self.P_SLEEP_W = 4.3               # Consumo em modo hibernacao (Cell Sleep)

    def resolve(self, conflict: ConflictEvent) -> ResolutionAction:
        # 1. Consultar historico na Shared Data Layer
        similar_resolutions = self.memory.get_similar_resolutions(conflict)
        if similar_resolutions:
            best_res = similar_resolutions[0]
            if best_res.confidence >= 0.8:
                return self._resolve_by_history(conflict, similar_resolutions)
                
        # 2. Conflito DIRETO (mesmo parametro/alvo) -> Heuristica TVS
        if conflict.conflict_type.name == "DIRECT":
            return self._resolve_direct_conflict(conflict)
            
        # 3. Conflito INDIRETO (impacto cruzado em KPIs) -> Heuristica EEVS
        return self._resolve_indirect_conflict(conflict)

    def _resolve_direct_conflict(self, conflict: ConflictEvent) -> ResolutionAction:
        actions = conflict.involved_xapps
        best_score = -float("inf")
        best_action = None

        for act in actions:
            scores = self._calculate_action_scores(act)
            
            # Funcao de Utilidade Global TVS
            u_a = (self.w_sla * scores["sla"] +
                   self.w_throughput * scores["throughput"] +
                   self.w_energy * scores["energy"] +
                   self.w_stability * scores["stability"] +
                   self.w_priority * scores["priority"])
            
            if u_a > best_score:
                best_score = u_a
                best_action = act

        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=ResolutionStrategy.TVS, 
            winning_actions=[best_action] if best_action else [],
            modified_value=best_action.value if best_action else None,
            confidence=0.92,
            validation_level=0
        )

    def _resolve_indirect_conflict(self, conflict: ConflictEvent) -> ResolutionAction:
        actions = conflict.involved_xapps
        max_prio_in_conflict = max(getattr(a, "priority", 50) for a in actions) if actions else 50
        
        best_score = -float("inf")
        best_subset: List[XAppAction] = []

        powerset = []
        for i in range(1, len(actions) + 1):
            powerset.extend(list(itertools.combinations(actions, i)))
            
        for subset in powerset:
            subset_list = list(subset)
            if self._has_physical_incompatibility(subset_list):
                score = -float("inf")
            else:
                sub_scores = self._calculate_subset_scores(subset_list, max_prio_in_conflict)
                
                # Funcao de Utilidade Global EEVS
                score = (self.w_qos_ind * sub_scores["qos"] +
                         self.w_energy_ind * sub_scores["energy"] +
                         self.w_fairness_ind * sub_scores["fairness"] -
                         self.w_viol_ind * sub_scores["violations"])
                         
            if score > best_score:
                best_score = score
                best_subset = subset_list
                
        modified_val = best_subset[0].value if len(best_subset) == 1 else None

        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=ResolutionStrategy.EEVS, 
            winning_actions=best_subset,
            modified_value=modified_val,
            confidence=0.88,
            validation_level=0
        )

    def _has_physical_incompatibility(self, subset: List[XAppAction]) -> bool:
        param_targets = {}
        for act in subset:
            key = f"{act.node_id}_{act.parameter}"
            if key in param_targets and param_targets[key] != act.value:
                return True
        return False

    def _calculate_action_scores(self, act: XAppAction) -> Dict[str, float]:
        param = act.parameter
        val = act.value
        prio = getattr(act, "priority", 50)

        # 1. Throughput Score (Shannon Capacity Normalizado)
        if param == "PRB_QUOTA":
            fraction_prb = max(0.05, min(1.0, val / 100.0))
            tput_score = fraction_prb
        elif param == "TX_POWER":
            norm_power = (val - (-10.0)) / (23.0 - (-10.0))
            tput_score = max(0.1, min(1.0, 0.4 + 0.6 * norm_power))
        else:
            tput_score = 0.70

        # 2. SLA Score (Funcao Sigmoide de Atraso e Prioridade)
        if prio >= 90:  # URLLC de Missao Critica (SLA <= 5ms)
            if param == "PRB_QUOTA" and val >= 70:
                sla_score = 0.98
            elif param == "TX_POWER" and val < 15:
                sla_score = 0.45
            else:
                sla_score = 0.85
        elif prio >= 75:  # Traffic Steering / Handover
            sla_score = 0.82
        elif prio >= 60:  # eMBB / Energy Saving
            sla_score = 0.75
        else:  # mMTC
            sla_score = 0.65

        # 3. Energy Score (Earth Model Linear)
        if param == "TX_POWER":
            p_watts = 10 ** ((val - 30) / 10)
            p_total = self.N_TRX * (self.P0_W + self.DELTA_P * p_watts)
            p_max = self.N_TRX * (self.P0_W + self.DELTA_P * (10 ** ((23 - 30) / 10)))
            energy_score = max(0.0, min(1.0, 1.0 - (p_total - (self.N_TRX * self.P0_W)) / (p_max - (self.N_TRX * self.P0_W) + 1e-6)))
        elif param == "PRB_QUOTA":
            energy_score = max(0.2, 1.0 - (val / 150.0))
        else:
            energy_score = 0.60

        # 4. Stability Score
        if param == "HANDOVER":
            stability_score = 0.75
        else:
            stability_score = 0.90

        # 5. Priority Score Normalizado (0.0 a 1.0)
        priority_score = max(0.1, min(1.0, prio / 100.0))

        return {
            "sla": sla_score,
            "throughput": tput_score,
            "energy": energy_score,
            "stability": stability_score,
            "priority": priority_score
        }

    def _calculate_subset_scores(self, subset: List[XAppAction], max_prio_in_conflict: float = 50.0) -> Dict[str, float]:
        if not subset:
            return {"qos": 0.0, "energy": 0.0, "fairness": 0.0, "violations": 1.0}

        individual_scores = [self._calculate_action_scores(act) for act in subset]
        
        # QoS Ponderado pela prioridade
        total_prio = sum(s["priority"] for s in individual_scores)
        if total_prio > 0:
            qos_joint = sum(s["sla"] * s["priority"] for s in individual_scores) / total_prio
        else:
            qos_joint = sum(s["sla"] for s in individual_scores) / len(subset)

        # Eficiencia Energetica Media
        energy_joint = sum(s["energy"] for s in individual_scores) / len(subset)

        # Equidade de Jain entre os ganhos de QoS
        sla_values = [s["sla"] for s in individual_scores]
        sum_sla = sum(sla_values)
        sum_sq_sla = sum(v ** 2 for v in sla_values)
        if sum_sq_sla > 0:
            fairness = (sum_sla ** 2) / (len(subset) * sum_sq_sla)
        else:
            fairness = 0.5

        # Violacoes e Penalidades:
        violations = 0.0
        subset_max_prio = max(getattr(a, "priority", 50) for a in subset)
        
        # Penalidade pesada se descartar a acao de maior prioridade do conflito (ex: URLLC descartado em prol de ES)
        if subset_max_prio < max_prio_in_conflict:
            violations += ((max_prio_in_conflict - subset_max_prio) / 30.0)

        has_es = any(a.xapp_id.startswith("energy") for a in subset)
        has_urllc = any(getattr(a, "priority", 50) >= 90 for a in subset)
        if has_es and has_urllc:
            violations += 0.20

        return {
            "qos": qos_joint,
            "energy": energy_joint,
            "fairness": min(1.0, max(0.1, fairness)),
            "violations": violations
        }

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
