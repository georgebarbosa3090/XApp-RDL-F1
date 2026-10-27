"""
Módulo de Rastreamento Causal e Métricas Científicas de Governança O-RAN (Gate 4)
Implementa a formalização matemática e causal entre Telemetria (t0) -> Conflito -> Decisão H-RDL -> E2SM-RC -> ACK -> Telemetria (t1).
Calcula a métrica Conflict Resolution Effectiveness (CRE) e indicadores de alta autoridade científica.
"""

import time
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from src.observability.logging import setup_logger

logger = setup_logger("CausalTracker")

@dataclass
class CausalRecord:
    action_id: str
    decision_id: str
    ric_request_id: Union[int, str]
    conflict_id: Optional[str]
    timestamp: float
    node_id: str
    parameter: str
    old_value: Optional[float]
    new_value: float
    kpm_before: Dict[str, float]
    kpm_after: Optional[Dict[str, float]] = None
    ack_status: str = "PENDING"  # PENDING, ACKNOWLEDGED, FAILED, TIMEOUT
    cause_code: Optional[int] = None
    kpi_improved: Optional[bool] = None
    resolution_strategy: str = "SHANNON_OPTIMAL"
    control_to_effect_latency_ms: float = 0.0

    @property
    def rtt_ms(self) -> float:
        return self.control_to_effect_latency_ms

    @rtt_ms.setter
    def rtt_ms(self, val: float):
        self.control_to_effect_latency_ms = val

@dataclass
class ScientificSummary:
    total_conflicts_detected: int
    total_conflicts_resolved: int
    total_actions_dispatched: int
    total_acks_received: int
    total_failures_received: int
    conflict_resolution_rate: float            # CRR (%)
    conflict_resolution_effectiveness: float   # CRE (%)
    sla_violation_rate_before: float           # (%)
    sla_violation_rate_after: float            # (%)
    sla_violation_reduction_pct: float         # (%)
    latency_mean_before_ms: float
    latency_mean_after_ms: float
    latency_reduction_pct: float
    latency_p95_ms: float
    latency_p99_ms: float
    jain_fairness_before: float
    jain_fairness_after: float
    ping_pong_rate_before_epm: float           # events per minute
    ping_pong_rate_after_epm: float
    safety_intervention_rate: float            # (%)
    unsafe_action_rate: float                  # (%) -> Deve ser 0.0%
    mean_decision_latency_ms: float
    mean_control_to_effect_latency_ms: float
    energy_efficiency_gain_pct: float

class RecordList(List[CausalRecord]):
    def __getitem__(self, item):
        if isinstance(item, str):
            for r in reversed(self):
                if getattr(r, "action_id", None) == item or getattr(r, "decision_id", None) == item:
                    return r
            raise KeyError(item)
        return super().__getitem__(item)

class CausalTracker:
    """
    Rastreador Causal e Gerador de Evidências Experimentais O-RAN.
    Garante rastreabilidade estrita entre intervenção de controle e melhoria objetiva de KPIs.
    """
    def __init__(self):
        self.records: RecordList = RecordList()
        self._conflict_ids: set[str] = set()
        self._resolved_conflict_ids: set[str] = set()
        self._proposal_ids: set[str] = set()
        self._pending_responses: Dict[Union[int, str], Tuple[str, float, Optional[int]]] = {}
        self.conflicts_detected_count: int = 0
        self.conflicts_resolved_count: int = 0
        self.safety_interventions_count: int = 0
        self.safety_validations_count: int = 0
        self.unsafe_actions_count: int = 0
        self.total_proposals_count: int = 0
        self.decision_latencies_ms: List[float] = []
        self.ack_latency_ms: List[float] = []
        self.sla_violations: List[Any] = []

    def reset(self):
        self.records.clear()
        self._conflict_ids.clear()
        self._resolved_conflict_ids.clear()
        self._proposal_ids.clear()
        self._pending_responses.clear()
        self.conflicts_detected_count = 0
        self.conflicts_resolved_count = 0
        self.safety_interventions_count = 0
        self.safety_validations_count = 0
        self.unsafe_actions_count = 0
        self.total_proposals_count = 0
        self.decision_latencies_ms.clear()
        self.ack_latency_ms.clear()
        self.sla_violations.clear()

    def register_conflict_event(
        self,
        conflict_id: str,
        conflict_type: str,
        num_actions: int,
        action_ids: Optional[List[str]] = None,
    ):
        if conflict_id not in self._conflict_ids:
            self._conflict_ids.add(conflict_id)
            self.conflicts_detected_count = len(self._conflict_ids)
        if action_ids is None:
            self.total_proposals_count += max(0, num_actions)
        else:
            self._proposal_ids.update(action_ids)
            self.total_proposals_count = len(self._proposal_ids)

    def record_conflict_resolution(self, conflict_id: str) -> bool:
        if conflict_id not in self._conflict_ids or conflict_id in self._resolved_conflict_ids:
            return False
        self._resolved_conflict_ids.add(conflict_id)
        self.conflicts_resolved_count = len(self._resolved_conflict_ids)
        return True

    def record_safety_validation(
        self,
        *,
        intervention: bool = False,
        unsafe_action: bool = False,
    ) -> None:
        self.safety_validations_count += 1
        if intervention:
            self.safety_interventions_count += 1
        if unsafe_action:
            self.unsafe_actions_count += 1

    def record_decision(
        self,
        action_id: str,
        decision_id: str,
        ric_request_id: Union[int, str],
        node_id: str,
        parameter: str,
        old_val: Optional[float],
        new_val: float,
        kpm_before: Optional[Dict[str, float]] = None,
        strategy: str = "SHANNON_OPTIMAL",
        decision_latency_ms: Optional[float] = None,
        conflict_id: Optional[str] = None,
    ) -> CausalRecord:
        if decision_latency_ms is not None:
            self.decision_latencies_ms.append(float(decision_latency_ms))
        rec = CausalRecord(
            action_id=action_id,
            decision_id=decision_id,
            ric_request_id=ric_request_id,
            conflict_id=conflict_id,
            timestamp=time.time(),
            node_id=node_id,
            parameter=parameter,
            old_value=old_val,
            new_value=new_val,
            kpm_before=dict(kpm_before) if kpm_before else {},
            resolution_strategy=strategy
        )
        pending = self._pending_responses.pop(ric_request_id, None)
        if pending is not None:
            rec.ack_status, rtt_ms, cause_code = pending
            rec.control_to_effect_latency_ms = rtt_ms
            rec.cause_code = cause_code
            if rec.ack_status == "ACKNOWLEDGED":
                self.ack_latency_ms.append(rtt_ms)
        self.records.append(rec)
        return rec

    @staticmethod
    def correlation_id(node_id: str, ran_function_id: int, requestor_id: int, instance_id: int) -> str:
        return f"{node_id}:{ran_function_id}:{requestor_id}:{instance_id}"

    def record_ack(self, ric_request_id: Union[int, str], rtt_ms: float = 0.0) -> bool:
        matches = [record for record in self.records if record.ric_request_id == ric_request_id]
        if len(matches) != 1:
            if matches or ric_request_id in self._pending_responses:
                return False
            self._pending_responses[ric_request_id] = ("ACKNOWLEDGED", rtt_ms, None)
            return True
        if matches[0].ack_status != "PENDING":
            return False
        matches[0].ack_status = "ACKNOWLEDGED"
        matches[0].control_to_effect_latency_ms = rtt_ms
        self.ack_latency_ms.append(rtt_ms)
        return True

    def record_failure(self, ric_request_id: Union[int, str], cause_code: int = 1) -> bool:
        matches = [record for record in self.records if record.ric_request_id == ric_request_id]
        if len(matches) != 1:
            if matches or ric_request_id in self._pending_responses:
                return False
            self._pending_responses[ric_request_id] = ("FAILED", 0.0, cause_code)
            return True
        if matches[0].ack_status != "PENDING":
            return False
        matches[0].ack_status = "FAILED"
        matches[0].cause_code = cause_code
        return True

    def record_timeout(self, ric_request_id: Union[int, str]) -> bool:
        matches = [record for record in self.records if record.ric_request_id == ric_request_id]
        if len(matches) != 1 or matches[0].ack_status != "PENDING":
            return False
        matches[0].ack_status = "TIMEOUT"
        return True

    def record_send_failure(self, ric_request_id: Union[int, str]) -> bool:
        matches = [record for record in self.records if record.ric_request_id == ric_request_id]
        if len(matches) != 1 or matches[0].ack_status != "PENDING":
            return False
        matches[0].ack_status = "SEND_FAILED"
        return True

    def record_telemetry_effect(
        self,
        action_id: str,
        kpm_after: Dict[str, float]
    ) -> bool:
        """
        Associa a telemetria pós-ação (t1) à ação executada e avalia a causalidade de melhoria de KPI.
        Sem fallback sintético: caso os dados sejam ausentes, a melhoria causal não é confirmada (Fail-Closed).
        """
        for r in reversed(self.records):
            if r.action_id == action_id:
                r.kpm_after = dict(kpm_after)
                
                improved: Optional[bool] = False
                lat_before = r.kpm_before.get("latency_ms")
                lat_after = kpm_after.get("latency_ms")
                thp_before = r.kpm_before.get("throughput_mbps")
                thp_after = kpm_after.get("throughput_mbps")
                pdr_before = r.kpm_before.get("pdr_percent")
                pdr_after = kpm_after.get("pdr_percent")

                if r.parameter in ("PRB_QUOTA", "SCHEDULER_WEIGHT"):
                    # Espera-se redução de latência ou aumento de PDR/Vazão
                    if (lat_before is not None and lat_after is not None and lat_after < lat_before) or \
                       (pdr_before is not None and pdr_after is not None and pdr_after > pdr_before) or \
                       (thp_before is not None and thp_after is not None and thp_after > thp_before):
                        improved = True
                elif r.parameter == "TX_POWER":
                    # Espera-se preservação de SLA com redução de consumo/interferência
                    if lat_before is not None and lat_after is not None and pdr_after is not None:
                        if lat_after <= lat_before * 1.05 and pdr_after >= 99.0:
                            improved = True
                elif r.parameter == "HANDOVER":
                    # Mitigação de ping-pong e sobrecarga de célula
                    if (lat_before is not None and lat_after is not None and lat_after < lat_before) or \
                       (pdr_before is not None and pdr_after is not None and pdr_after >= pdr_before):
                        improved = True
                else:
                    if (lat_before is not None and lat_after is not None and lat_after < lat_before) or \
                       (thp_before is not None and thp_after is not None and thp_after > thp_before):
                        improved = True

                r.kpi_improved = (
                    improved
                    if r.ack_status == "ACKNOWLEDGED"
                    else None
                )
                return True
        return False

    def _calculate_jain_fairness(self, values: List[float]) -> float:
        """Calcula o índice de equidade de Jain J = (sum(x))^2 / (n * sum(x^2))."""
        clean_vals = [max(0.0, float(v)) for v in values if v is not None and not np.isnan(v)]
        if not clean_vals or len(clean_vals) == 0:
            return float("nan")
        sum_v = sum(clean_vals)
        sum_sq = sum(v * v for v in clean_vals)
        if sum_sq <= 1e-9:
            return float("nan")
        return float((sum_v * sum_v) / (len(clean_vals) * sum_sq))

    def compute_metrics(self) -> ScientificSummary:
        total_conflicts = self.conflicts_detected_count
        resolved_conflicts = self.conflicts_resolved_count
        crr = (
            (resolved_conflicts / total_conflicts) * 100.0
            if total_conflicts
            else float("nan")
        )

        # Conflitos com melhoria comprovada e ACK recebido
        improved_conflicts = {
            r.conflict_id
            for r in self.records
            if r.conflict_id is not None
            and r.kpi_improved is True
            and r.ack_status == "ACKNOWLEDGED"
        }
        cre = (
            (len(improved_conflicts) / total_conflicts) * 100.0
            if total_conflicts
            else float("nan")
        )

        # Estatísticas de latência agregada puramente empíricas
        lat_before_list = [float(r.kpm_before["latency_ms"]) for r in self.records if "latency_ms" in r.kpm_before]
        lat_after_list = [float(r.kpm_after["latency_ms"]) for r in self.records if r.kpm_after and "latency_ms" in r.kpm_after]

        lat_mean_before = float(np.mean(lat_before_list)) if lat_before_list else float("nan")
        lat_mean_after = float(np.mean(lat_after_list)) if lat_after_list else float("nan")
        lat_reduction = ((lat_mean_before - lat_mean_after) / max(0.001, lat_mean_before)) * 100.0 if (not np.isnan(lat_mean_before) and not np.isnan(lat_mean_after) and lat_mean_before > 0) else float("nan")

        p95 = float(np.percentile(lat_after_list, 95)) if lat_after_list else float("nan")
        p99 = float(np.percentile(lat_after_list, 99)) if lat_after_list else float("nan")

        # Violações de SLA (latência > 5ms para fatias críticas)
        sla_before_viol = (sum(1 for l in lat_before_list if l > 5.0) / len(lat_before_list)) * 100.0 if lat_before_list else float("nan")
        sla_after_viol = (sum(1 for l in lat_after_list if l > 5.0) / len(lat_after_list)) * 100.0 if lat_after_list else float("nan")
        sla_reduction = (
            ((sla_before_viol - sla_after_viol) / sla_before_viol) * 100.0
            if not np.isnan(sla_before_viol)
            and not np.isnan(sla_after_viol)
            and sla_before_viol > 0
            else float("nan")
        )

        acks = sum(1 for r in self.records if r.ack_status == "ACKNOWLEDGED")
        fails = sum(1 for r in self.records if r.ack_status == "FAILED")
        
        # Vazão para equidade de Jain
        thp_before = [float(r.kpm_before["throughput_mbps"]) for r in self.records if "throughput_mbps" in r.kpm_before]
        thp_after = [float(r.kpm_after["throughput_mbps"]) for r in self.records if r.kpm_after and "throughput_mbps" in r.kpm_after]
        
        jain_before = self._calculate_jain_fairness(thp_before) if thp_before else float("nan")
        jain_after = self._calculate_jain_fairness(thp_after) if thp_after else float("nan")
        
        # RTT e latência de malha
        rtt_list = [r.control_to_effect_latency_ms for r in self.records if r.control_to_effect_latency_ms > 0]
        mean_control_to_effect = float(np.mean(rtt_list)) if rtt_list else float("nan")
        
        # Taxa de intervenção de segurança
        safety_rate = (
            (self.safety_interventions_count / self.total_proposals_count) * 100.0
            if self.total_proposals_count
            else float("nan")
        )
        unsafe_rate = (
            (self.unsafe_actions_count / self.safety_validations_count) * 100.0
            if self.safety_validations_count
            else float("nan")
        )

        # Latência média de decisão a partir de medições reais registradas
        mean_decision_latency = float(np.mean(self.decision_latencies_ms)) if self.decision_latencies_ms else float("nan")

        # Ganho de eficiência energética calculado a partir de reduções de TX_POWER reais
        tx_power_reductions = []
        for r in self.records:
            if r.parameter == "TX_POWER" and r.old_value is not None and r.old_value > 0 and r.new_value < r.old_value:
                tx_power_reductions.append((r.old_value - r.new_value) / r.old_value * 100.0)
        energy_gain = float(np.mean(tx_power_reductions)) if tx_power_reductions else float("nan")

        return ScientificSummary(
            total_conflicts_detected=self.conflicts_detected_count,
            total_conflicts_resolved=self.conflicts_resolved_count,
            total_actions_dispatched=len(self.records),
            total_acks_received=acks,
            total_failures_received=fails,
            conflict_resolution_rate=crr,
            conflict_resolution_effectiveness=cre,
            sla_violation_rate_before=sla_before_viol,
            sla_violation_rate_after=sla_after_viol,
            sla_violation_reduction_pct=sla_reduction,
            latency_mean_before_ms=lat_mean_before,
            latency_mean_after_ms=lat_mean_after,
            latency_reduction_pct=lat_reduction,
            latency_p95_ms=p95,
            latency_p99_ms=p99,
            jain_fairness_before=jain_before,
            jain_fairness_after=jain_after,
            ping_pong_rate_before_epm=float("nan"),
            ping_pong_rate_after_epm=float("nan"),
            safety_intervention_rate=safety_rate,
            unsafe_action_rate=unsafe_rate,
            mean_decision_latency_ms=mean_decision_latency,
            mean_control_to_effect_latency_ms=mean_control_to_effect,
            energy_efficiency_gain_pct=energy_gain
        )

    def export_causal_log_json(self) -> str:
        return json.dumps([asdict(r) for r in self.records], indent=2)

# Instância Singleton
causal_tracker = CausalTracker()
