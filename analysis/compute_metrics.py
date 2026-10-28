#!/usr/bin/env python3
"""
Módulo de Cálculo e Consolidação de Métricas em 6 Camadas (F1 H-RDL x F2 CA-RDL)
Implementa as formulações matemáticas exatas de SLA Drift, Fairness de Jain,
decomposição de latência de malha fechada, severidade de conflito e eficiência de rádio.
"""

import math
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent


def compute_jain_fairness(values: List[float]) -> float:
    """Calcula o índice de equidade de Jain: J = (sum x_i)^2 / (n * sum x_i^2)."""
    clean_vals = [float(v) for v in values if not math.isnan(v) and v > 0]
    n = len(clean_vals)
    if n == 0:
        return 1.0
    sum_x = sum(clean_vals)
    sum_sq = sum(v * v for v in clean_vals)
    if sum_sq == 0:
        return 1.0
    return (sum_x ** 2) / (n * sum_sq)


def compute_sla_drift_throughput(t_obs: float, t_req: float) -> float:
    """Calcula o SLA drift em throughput: SLAD_T = max(0, (T_req - T_obs) / T_req)."""
    if t_req <= 0:
        return 0.0
    return max(0.0, (t_req - t_obs) / t_req)


def compute_sla_drift_delay(d_obs: float, d_max: float) -> float:
    """Calcula o SLA drift em latência: SLAD_D = max(0, (D_obs - D_max) / D_max)."""
    if d_max <= 0:
        return 0.0
    return max(0.0, (d_obs - d_max) / d_max)


def compute_conflict_severity(
    delta_t_norm: float,
    delta_l_norm: float,
    sla_viol: float,
    delta_fairness: float,
    weights: tuple = (0.3, 0.3, 0.25, 0.15)
) -> float:
    """Calcula o índice normalizado de severidade do conflito CS."""
    w1, w2, w3, w4 = weights
    cs = (w1 * delta_t_norm) + (w2 * delta_l_norm) + (w3 * (sla_viol / 100.0)) + (w4 * (1.0 - delta_fairness))
    return round(float(np.clip(cs, 0.0, 1.0)), 4)


def compute_closed_loop_breakdown(
    t_detect_ms: float = 2.0,
    t_decision_ms: float = 0.12,
    t_encode_ms: float = 0.15,
    t_dispatch_ms: float = 0.20,
    t_e2_rtt_ms: float = 1.82,
    t_apply_ms: float = 0.50,
    t_observe_ms: float = 195.21
) -> Dict[str, float]:
    """Retorna decomposição da latência do ciclo fechado T_loop."""
    t_loop = t_detect_ms + t_decision_ms + t_encode_ms + t_dispatch_ms + t_e2_rtt_ms + t_apply_ms + t_observe_ms
    return {
        "t_detect_ms": t_detect_ms,
        "t_decision_ms": t_decision_ms,
        "t_encode_ms": t_encode_ms,
        "t_dispatch_ms": t_dispatch_ms,
        "t_e2_rtt_ms": t_e2_rtt_ms,
        "t_apply_ms": t_apply_ms,
        "t_observe_ms": t_observe_ms,
        "t_total_loop_ms": round(t_loop, 2)
    }


def compute_scenario_comprehensive_metrics(df_flows: pd.DataFrame) -> pd.DataFrame:
    """Calcula agregações por cenário a partir do FlowMonitor."""
    if df_flows.empty:
        return pd.DataFrame()

    records = []
    for scenario, group in df_flows.groupby("scenario_name"):
        throughputs = group["throughput_mbps"].values
        delays = group["mean_delay_ms"].values
        losses = group["loss_ratio_pct"].values

        mean_tp = float(np.mean(throughputs)) if len(throughputs) > 0 else 0.0
        p95_delay = float(np.percentile(delays, 95)) if len(delays) > 0 else 0.0
        p99_delay = float(np.percentile(delays, 99)) if len(delays) > 0 else 0.0
        mean_delay = float(np.mean(delays)) if len(delays) > 0 else 0.0
        mean_loss = float(np.mean(losses)) if len(losses) > 0 else 0.0
        jain_tp = compute_jain_fairness(throughputs)

        # Metas de SLA por cenário (heurística normativa)
        target_tp = 30.0 if "urllc" in scenario.lower() or "direct_prb" in scenario.lower() else 50.0
        max_delay = 10.0 if "urllc" in scenario.lower() or "zero_jitter" in scenario.lower() else 25.0

        slad_t = compute_sla_drift_throughput(mean_tp, target_tp)
        slad_d = compute_sla_drift_delay(p95_delay, max_delay)
        sla_violations = 0.0 if slad_t == 0.0 and slad_d == 0.0 else round((slad_t + slad_d) * 25.0, 2)

        records.append({
            "scenario": scenario,
            "total_flows": len(group),
            "throughput_mean_mbps": round(mean_tp, 2),
            "throughput_median_mbps": round(float(np.median(throughputs)), 2),
            "latency_mean_ms": round(mean_delay, 2),
            "latency_p95_ms": round(p95_delay, 2),
            "latency_p99_ms": round(p99_delay, 2),
            "packet_loss_pct": round(mean_loss, 2),
            "jain_fairness": round(jain_tp, 4),
            "slad_throughput": round(slad_t, 4),
            "slad_latency": round(slad_d, 4),
            "sla_violation_pct": min(100.0, sla_violations),
            "spectral_efficiency_bps_hz": round(mean_tp / 100.0, 3)
        })

    return pd.DataFrame(records)


if __name__ == "__main__":
    from load_data import load_all_flowmonitor_datasets
    df_f = load_all_flowmonitor_datasets()
    df_scen = compute_scenario_comprehensive_metrics(df_f)
    print(f"[OK] Métricas consolidadas para {len(df_scen)} cenários:")
    print(df_scen[["scenario", "throughput_mean_mbps", "latency_p95_ms", "jain_fairness", "sla_violation_pct"]])
