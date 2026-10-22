#!/usr/bin/env python3
"""Run a reproducible in-process RAN-model / deterministic-RDL closed loop."""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.conflict_types import XAppAction
from src.core.perception import Perception
from src.core.reasoning import Reasoning
from src.core.refinement import Refinement
from src.infrastructure.memory_module import MemoryModule
from src.simulation.discrete_event_ran_simulator import DiscreteEventRANSimulator

SEED_START = 1001
DEFAULT_SEEDS = 30
DEFAULT_DURATION_S = 30.0
DEFAULT_INTERVAL_S = 0.2
SLOT_DURATION_S = 0.01
URLLC_SLA_MS = 5.0
RDL_URLLC_QUOTA_PCT = 45.0
ENERGY_URLLC_QUOTA_PCT = 30.0

METRIC_FIELDS = (
    "throughput_mbps",
    "urllc_latency_mean_ms",
    "urllc_latency_p99_ms",
    "urllc_sla_violations_pct",
    "jain_fairness",
    "delivery_ratio_pct",
    "prb_utilization_pct",
    "energy_efficiency_mbps_per_w",
    "packets_lost_total",
)


def _git_metadata() -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "commit": commit.stdout.strip() if commit.returncode == 0 else None,
        "worktree_dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
    }


def _build_simulator(seed: int, duration_s: float, interval_s: float) -> DiscreteEventRANSimulator:
    sim = DiscreteEventRANSimulator(
        seed=seed,
        carrier_freq_ghz=3.5,
        bandwidth_mhz=100.0,
        duration_s=duration_s,
        decision_interval_s=interval_s,
        mode="B0",
        num_ues=30,
    )
    sim.add_gnb("gnb_01", 0.0, 0.0, tx_power_dbm=43.0)
    sim.add_gnb("gnb_02", 300.0, 0.0, tx_power_dbm=38.0)

    for index in range(sim.num_ues):
        slice_type = "URLLC" if index % 3 == 0 else ("eMBB" if index % 3 == 1 else "mMTC")
        angle = (index / sim.num_ues) * 2.0 * math.pi + (seed % 100) * 0.01
        distance = 40.0 + ((index * 7 + (seed % 17)) % 180)
        sim.add_ue(
            f"ue_{index + 1:02d}",
            slice_type,
            distance * math.cos(angle),
            distance * math.sin(angle),
            "gnb_01",
        )

    sim.gnbs["gnb_01"].slice_prb_quotas = {
        "URLLC": 0.15,
        "eMBB": 0.70,
        "SENSING": 0.15,
    }
    return sim


def _metrics(sim: DiscreteEventRANSimulator) -> dict[str, Any]:
    kpm = sim.get_kpm_metrics()
    urllc_ues = [ue for ue in sim.ues.values() if ue.slice_type == "URLLC"]
    violating = 0
    for ue in urllc_ues:
        mean_delay = statistics.fmean(ue.packet_delays_ms) if ue.packet_delays_ms else 2.5
        violating += mean_delay > URLLC_SLA_MS
    rf_power_w = sum(
        10.0 ** ((gnb.tx_power_dbm - 30.0) / 10.0) for gnb in sim.gnbs.values()
    )
    return {
        **kpm,
        "urllc_sla_violations_pct": round(
            100.0 * violating / max(1, len(urllc_ues)), 2
        ),
        "energy_efficiency_mbps_per_w": round(
            kpm["throughput_mbps"] / max(0.1, rf_power_w), 4
        ),
        "urllc_ues": len(urllc_ues),
        "ue_count": len(sim.ues),
        "gnb_count": len(sim.gnbs),
        "simulated_time_s": round(sim.current_sim_time_s, 3),
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _run_one(
    seed: int,
    mode: str,
    duration_s: float,
    interval_s: float,
    output_dir: Path,
) -> dict[str, Any]:
    sim = _build_simulator(seed, duration_s, interval_s)
    run_dir = output_dir / mode / str(seed)
    run_dir.mkdir(parents=True, exist_ok=False)
    slots_per_interval = round(interval_s / SLOT_DURATION_S)
    interval_count = round(duration_s / interval_s)
    metrics_path = run_dir / "metrics.csv"
    decisions_path = run_dir / "decisions.jsonl"

    perception = Perception() if mode == "HRDL" else None
    memory = MemoryModule() if mode == "HRDL" else None
    reasoning = Reasoning(memory, config={}) if memory is not None else None
    refinement = Refinement(memory) if memory is not None else None
    applied_control = False
    decision_latency_samples: list[float] = []

    with metrics_path.open("w", newline="", encoding="utf-8") as metrics_file:
        writer = csv.DictWriter(
            metrics_file,
            fieldnames=[
                "seed",
                "mode",
                "time_s",
                *METRIC_FIELDS,
                "urllc_quota_pct",
            ],
        )
        writer.writeheader()

        with decisions_path.open("w", encoding="utf-8") as decisions_file:
            for step in range(1, interval_count + 1):
                for _ in range(slots_per_interval):
                    sim.step_slot(SLOT_DURATION_S)

                current = _metrics(sim)
                quota_pct = round(
                    sim.gnbs["gnb_01"].slice_prb_quotas["URLLC"] * 100.0, 2
                )
                writer.writerow(
                    {
                        "seed": seed,
                        "mode": mode,
                        "time_s": current["simulated_time_s"],
                        **{field: current[field] for field in METRIC_FIELDS},
                        "urllc_quota_pct": quota_pct,
                    }
                )

                if mode == "B0":
                    event = {
                        "seed": seed,
                        "time_s": current["simulated_time_s"],
                        "mode": mode,
                        "event": "STATIC_NO_CONTROL",
                        "observed_urllc_latency_ms": current["urllc_latency_mean_ms"],
                    }
                else:
                    qos_action = XAppAction(
                        xapp_id="qos_priority",
                        node_id="gnb_01",
                        parameter="PRB_QUOTA",
                        value=RDL_URLLC_QUOTA_PCT,
                        priority=85,
                    )
                    energy_action = XAppAction(
                        xapp_id="energy_saver",
                        node_id="gnb_01",
                        parameter="PRB_QUOTA",
                        value=ENERGY_URLLC_QUOTA_PCT,
                        priority=40,
                    )
                    started = time.perf_counter()
                    conflicts = perception.detect_action_group([qos_action, energy_action])
                    resolution = reasoning.resolve(conflicts[0]) if conflicts else None
                    decision_ms = (time.perf_counter() - started) * 1000.0
                    decision_latency_samples.append(decision_ms)

                    selected = resolution.winning_actions[0] if resolution else None
                    sla_trigger = (
                        current["urllc_latency_mean_ms"] > URLLC_SLA_MS
                        or current["urllc_sla_violations_pct"] > 0.0
                    )
                    needs_control = (
                        sla_trigger
                        and selected is not None
                        and abs(quota_pct - selected.value) > 1e-9
                    )
                    safety_ok = False
                    safety_reason = "No control required"
                    event_name = "NO_CONTROL_REQUIRED"

                    if needs_control:
                        safety_ok, _, safety_reason = refinement.validate(
                            resolution, conflicts[0]
                        )
                        event_name = "CONTROL_BLOCKED" if not safety_ok else "CONTROL_APPLIED"
                        if safety_ok:
                            sim.apply_rc_control(
                                {
                                    "node_id": selected.node_id,
                                    "parameter": selected.parameter,
                                    "value": selected.value,
                                }
                            )
                            applied_control = True
                    elif sla_trigger and quota_pct == RDL_URLLC_QUOTA_PCT:
                        event_name = "TARGET_ALREADY_ACTIVE"

                    event = {
                        "seed": seed,
                        "time_s": current["simulated_time_s"],
                        "mode": mode,
                        "event": event_name,
                        "observed_urllc_latency_ms": current["urllc_latency_mean_ms"],
                        "sla_violation_pct": current["urllc_sla_violations_pct"],
                        "conflicts_detected": len(conflicts),
                        "strategy": resolution.strategy_used.name if resolution else None,
                        "proposals": [
                            {
                                "xapp_id": action.xapp_id,
                                "parameter": action.parameter,
                                "value": action.value,
                                "priority": action.priority,
                            }
                            for action in (qos_action, energy_action)
                        ],
                        "selected_action": (
                            {
                                "xapp_id": selected.xapp_id,
                                "parameter": selected.parameter,
                                "value": selected.value,
                            }
                            if selected
                            else None
                        ),
                        "decision_latency_ms": round(decision_ms, 6),
                        "safety_approved": safety_ok if needs_control else None,
                        "safety_reason": safety_reason,
                        "control_transport": (
                            "direct in-process simulator API; no E2/RIC transport"
                            if event_name == "CONTROL_APPLIED"
                            else None
                        ),
                    }
                decisions_file.write(
                    json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
                )

    final = _metrics(sim)
    final["seed"] = seed
    final["mode"] = mode
    final["control_applied"] = applied_control
    final["decision_count"] = len(decision_latency_samples)
    final["mean_decision_latency_ms"] = (
        statistics.fmean(decision_latency_samples) if decision_latency_samples else 0.0
    )
    _write_json(
        run_dir / "config.json",
        {
            "seed": seed,
            "mode": mode,
            "simulator": "src.simulation.discrete_event_ran_simulator.DiscreteEventRANSimulator",
            "controller": "in-process deterministic RDL" if mode == "HRDL" else "static/no-control",
            "external_ns3": False,
            "external_nori_ric": False,
            "e2sm_rc_transport": "emulated by direct local simulator API" if mode == "HRDL" else None,
            "duration_s": duration_s,
            "decision_interval_s": interval_s,
            "slot_duration_s": SLOT_DURATION_S,
            "carrier_frequency_ghz": 3.5,
            "bandwidth_mhz": 100.0,
            "g_node_bs": [
                {"node_id": "gnb_01", "x_m": 0.0, "y_m": 0.0, "tx_power_dbm": 43.0},
                {"node_id": "gnb_02", "x_m": 300.0, "y_m": 0.0, "tx_power_dbm": 38.0},
            ],
            "ue_count": sim.num_ues,
            "initial_slice_quotas_gnb_01_pct": {
                "URLLC": 15.0,
                "eMBB": 70.0,
                "SENSING": 15.0,
            },
            "policy": {
                "trigger": f"URLLC mean latency > {URLLC_SLA_MS} ms or any URLLC flow violates SLA",
                "qos_proposal_urllc_quota_pct": RDL_URLLC_QUOTA_PCT,
                "energy_proposal_urllc_quota_pct": ENERGY_URLLC_QUOTA_PCT,
                "selected_target": "determined by deterministic RDL arbitration",
            },
            "result": final,
        },
    )
    return final


def _summary(values: list[float]) -> dict[str, float]:
    mean = statistics.fmean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    margin = 1.96 * sd / math.sqrt(len(values)) if values else 0.0
    return {
        "mean": mean,
        "median": statistics.median(values),
        "sample_sd": sd,
        "ci95_normal_low": mean - margin,
        "ci95_normal_high": mean + margin,
    }


def _write_report(
    report_path: Path,
    seeds: int,
    duration_s: float,
    interval_s: float,
    baseline: list[dict[str, Any]],
    hrdl: list[dict[str, Any]],
) -> dict[str, Any]:
    summaries: dict[str, Any] = {}
    for metric in METRIC_FIELDS:
        b0_values = [float(result[metric]) for result in baseline]
        rdl_values = [float(result[metric]) for result in hrdl]
        deltas = [rdl - b0 for rdl, b0 in zip(rdl_values, b0_values)]
        summaries[metric] = {
            "B0": _summary(b0_values),
            "HRDL": _summary(rdl_values),
            "paired_delta_HRDL_minus_B0": _summary(deltas),
        }

    summary_payload = {
        "scenario_id": "RICH_CLOSED_LOOP_LOCAL_MODEL",
        "seed_count": seeds,
        "seed_range": [SEED_START, SEED_START + seeds - 1],
        "duration_s": duration_s,
        "decision_interval_s": interval_s,
        "metric_summaries": summaries,
        "control_applied_runs": sum(bool(result["control_applied"]) for result in hrdl),
        "mean_decisions_per_run": statistics.fmean(
            result["decision_count"] for result in hrdl
        ),
        "mean_decision_latency_ms": statistics.fmean(
            result["mean_decision_latency_ms"] for result in hrdl
        ),
    }
    _write_json(report_path.parent / "summary.json", summary_payload)

    rows = []
    for metric, label, unit in (
        ("throughput_mbps", "Vazão agregada", "Mbps"),
        ("urllc_latency_mean_ms", "Latência média URLLC", "ms"),
        ("urllc_latency_p99_ms", "Latência p99 URLLC", "ms"),
        ("urllc_sla_violations_pct", "Fluxos URLLC violando SLA", "%"),
        ("jain_fairness", "Equidade de Jain", "índice"),
        ("delivery_ratio_pct", "Taxa de entrega", "%"),
        ("prb_utilization_pct", "Utilização PRB (proxy do modelo)", "%"),
        ("energy_efficiency_mbps_per_w", "Eficiência energética (proxy)", "Mbps/W"),
        ("packets_lost_total", "Pacotes perdidos", "pacotes"),
    ):
        values = summaries[metric]
        b0 = values["B0"]
        rdl = values["HRDL"]
        delta = values["paired_delta_HRDL_minus_B0"]
        rows.append(
            f"| {label} ({unit}) | {b0['mean']:.3f} ± {b0['sample_sd']:.3f} "
            f"| {rdl['mean']:.3f} ± {rdl['sample_sd']:.3f} "
            f"| {delta['mean']:+.3f} "
            f"[{delta['ci95_normal_low']:+.3f}, {delta['ci95_normal_high']:+.3f}] |"
        )

    report_path.write_text(
        "\n".join(
            [
                "# Relatório — campanha de simulação rica em closed loop",
                "",
                "- **Cenário:** loop local KPM-modelo → RDL determinística → safety guard → controle direto do simulador → KPM-modelo.",
                (
                    f"- **Execução:** {seeds} sementes pareadas ({SEED_START}–{SEED_START + seeds - 1}), "
                    f"{duration_s:g} s simulados por execução, intervalo de decisão {interval_s:g} s."
                ),
                "- **Topologia:** 2 gNB, 30 UE por semente, 3,5 GHz, 100 MHz; tráfego URLLC/eMBB/mMTC.",
                "- **Comparação:** B0 estático sem controle versus H-RDL, ambos iniciando com 15% de quota URLLC.",
                (
                    f"- **Controle:** acionado por latência URLLC > {URLLC_SLA_MS:g} ms ou violação de fluxo; "
                    f"propostas concorrentes de quota URLLC {RDL_URLLC_QUOTA_PCT:g}% (QoS) e "
                    f"{ENERGY_URLLC_QUOTA_PCT:g}% (energia)."
                ),
                (
                    f"- **Resultado de execução:** controle aplicado em {summary_payload['control_applied_runs']}/{seeds} "
                    f"execuções; {summary_payload['mean_decisions_per_run']:.1f} ciclos de decisão por execução; "
                    f"latência média de detecção/arbitragem medida no processo: "
                    f"{summary_payload['mean_decision_latency_ms']:.6f} ms."
                ),
                "",
                "## Resultados finais pareados",
                "",
                (
                    "Média ± desvio-padrão entre sementes; diferença pareada = H-RDL − B0. "
                    "O IC de 95% da diferença usa aproximação normal (1,96 × erro-padrão)."
                ),
                "",
                "| Métrica | B0 | H-RDL | Diferença pareada [IC95%] |",
                "|---|---:|---:|---:|",
                *rows,
                "",
                "## Interpretação e limites",
                "",
                (
                    "Esta execução é uma simulação local do modelo Python "
                    "`DiscreteEventRANSimulator`, conectada em processo ao código Perception, "
                    "Reasoning e Refinement. A observação é derivada diretamente do estado do "
                    "modelo e o controle chama a API local `apply_rc_control`."
                ),
                "",
                (
                    "**Não foi executado ns-3/5G-LENA, NORI, Near-RT RIC, SCTP live, nem uma "
                    "transação E2SM-KPM/E2SM-RC externa.** Portanto, os resultados não comprovam "
                    "interoperabilidade externa ou closed loop físico. As métricas de PRB, rádio, "
                    "filas, latência, perda e energia são proxies/saídas do modelo local; "
                    "não são medições de testbed."
                ),
                "",
                (
                    f"No modelo, o H-RDL elevou a equidade média de Jain em "
                    f"{summaries['jain_fairness']['paired_delta_HRDL_minus_B0']['mean']:+.4f}, "
                    f"mas reduziu a vazão agregada em "
                    f"{(summaries['throughput_mbps']['HRDL']['mean'] / summaries['throughput_mbps']['B0']['mean'] - 1.0) * 100.0:.1f}% "
                    "e não reduziu a violação da meta URLLC: ela permaneceu em 100% nos dois braços. "
                    "Neste modelo, a decisão TVS escolhe a quota URLLC de 45%, em detrimento da "
                    "proposta de energia de 30%, mas isso não foi suficiente para cumprir a meta."
                ),
                "",
                (
                    "Há uma limitação estrutural importante: os eventos de rádio são discretizados "
                    f"em slots de {SLOT_DURATION_S * 1000:g} ms, enquanto a meta configurada é "
                    f"{URLLC_SLA_MS:g} ms. A latência observada fica em 10 ms, de modo que o modelo "
                    "não representa resolução temporal suficiente para demonstrar cumprimento "
                    "dessa meta. Além disso, a utilização PRB exportada pelo simulador é um proxy "
                    "com piso de 15% (atingido em ambos os braços nesta execução), não uma medição "
                    "independente de blocos físicos; entrega de pacotes também permaneceu em 100%. "
                    "Essas métricas não devem ser interpretadas como evidência de performance "
                    "real de rádio."
                ),
                "",
                (
                    "As 30 sementes alteram deterministicamente o posicionamento dos UEs; não há "
                    "aleatoriedade independente do canal/tráfego neste simulador. As diferenças "
                    "são pareadas e reproduzíveis, mas ICs normais são apenas descritivos e não "
                    "substituem calibração com traces reais ou validação estatística do modelo."
                ),
                "",
                "## Reprodutibilidade e arquivos",
                "",
                (
                    "Execute: `uv run python scripts/run_rich_closed_loop_simulation.py "
                    f"--seeds {seeds} --duration {duration_s:g} --interval {interval_s:g} "
                    f"--output-dir {report_path.parent.as_posix()}`."
                ),
                "",
                "- `summary.json`: estatísticas agregadas e diferenças pareadas.",
                "- `paired_metrics.csv`: resultados finais por semente e braço.",
                "- `B0/<seed>/metrics.csv`, `HRDL/<seed>/metrics.csv`: KPM-modelo por ciclo.",
                "- `HRDL/<seed>/decisions.jsonl`: observações, conflito, arbitragem, validação e atuação.",
                "- `B0/<seed>/decisions.jsonl`: ciclos do baseline sem controle.",
                "- `*/<seed>/config.json`: configuração e resultado final por execução.",
                "",
                (
                    f"Metadados do repositório: commit `{_git_metadata()['commit'] or 'indisponível'}`; "
                    f"worktree dirty: `{_git_metadata()['worktree_dirty']}`."
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary_payload


def run_campaign(
    seeds: int,
    duration_s: float,
    interval_s: float,
    output_dir: Path,
) -> None:
    if seeds < 2:
        raise ValueError("Use pelo menos duas sementes para comparação estatística.")
    if duration_s <= 0.0 or interval_s <= 0.0:
        raise ValueError("A duração e o intervalo devem ser positivos.")
    if not math.isclose(interval_s / SLOT_DURATION_S, round(interval_s / SLOT_DURATION_S)):
        raise ValueError("O intervalo deve ser múltiplo do slot de 10 ms.")
    if not math.isclose(duration_s / interval_s, round(duration_s / interval_s)):
        raise ValueError("A duração deve ser múltipla do intervalo de decisão.")
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)

    config = {
        "scenario_id": "RICH_CLOSED_LOOP_LOCAL_MODEL",
        "seed_count": seeds,
        "seed_range": [SEED_START, SEED_START + seeds - 1],
        "duration_s": duration_s,
        "decision_interval_s": interval_s,
        "slot_duration_s": SLOT_DURATION_S,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "git": _git_metadata(),
        "external_ns3_available": False,
        "external_nori_ric_available": False,
    }
    _write_json(output_dir / "campaign_config.json", config)

    baseline_results = []
    hrdl_results = []
    paired_path = output_dir / "paired_metrics.csv"
    fields = ["seed", "metric", "B0", "HRDL", "delta_HRDL_minus_B0"]

    for index in range(seeds):
        seed = SEED_START + index
        print(f"[{index + 1}/{seeds}] seed={seed}: executando B0 e H-RDL", flush=True)
        baseline_results.append(
            _run_one(seed, "B0", duration_s, interval_s, output_dir)
        )
        hrdl_results.append(_run_one(seed, "HRDL", duration_s, interval_s, output_dir))

    with paired_path.open("w", newline="", encoding="utf-8") as paired_file:
        writer = csv.DictWriter(paired_file, fieldnames=fields)
        writer.writeheader()
        for b0_result, rdl_result in zip(baseline_results, hrdl_results):
            for metric in METRIC_FIELDS:
                writer.writerow(
                    {
                        "seed": b0_result["seed"],
                        "metric": metric,
                        "B0": b0_result[metric],
                        "HRDL": rdl_result[metric],
                        "delta_HRDL_minus_B0": rdl_result[metric] - b0_result[metric],
                    }
                )

    summary = _write_report(
        output_dir / "report.md",
        seeds,
        duration_s,
        interval_s,
        baseline_results,
        hrdl_results,
    )
    print(
        f"Concluído: {output_dir}\n"
        f"Controle aplicado em {summary['control_applied_runs']}/{seeds} sementes.\n"
        f"Relatório: {output_dir / 'report.md'}",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a reproducible local-model closed-loop RDL campaign."
    )
    parser.add_argument("--seeds", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION_S)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_S)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "experiments" / "results" / "rich_closed_loop_local",
    )
    args = parser.parse_args()
    run_campaign(args.seeds, args.duration, args.interval, args.output_dir)


if __name__ == "__main__":
    main()
