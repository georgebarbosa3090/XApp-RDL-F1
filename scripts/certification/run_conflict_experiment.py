#!/usr/bin/env python3
"""
Experimento de conflito multi-xApp com atuação real na RAN simulada (ns-3.48 + 5G-LENA v5.1).

Fluxo:
  1. Lê as propostas das xApps do catálogo (simulations/ns3/conflicts/catalog.json).
  2. Aplica o baseline escolhido e produz o cronograma de ações que chega à RAN:
       B0  sem coordenação: cada proposta é aplicada no instante em que chega;
       B1  FIFO: por janela de decisão (200 ms) e alvo, vence a primeira proposta;
       B2  prioridade estática: por janela e alvo, vence a maior prioridade;
       B3  H-RDL: as propostas de cada janela passam pelo pipeline real da xApp RDL
           (RDLxApp._process_action_group: Perception, Reasoning TVS/EEVS, Refinement),
           com o relógio do Refinement substituído pelo relógio simulado.
  3. Executa o cenário ns-3 pelo executor certificado (saída ao vivo), que aplica o
     cronograma na RAN (rdl-nr-common.h) e grava a evidência em experiments/runs/<run_id>/.

O cronograma e o log de decisões viram anexos da execução (raw/), cobertos pelos hashes.
Esta é uma avaliação em malha aberta da decisão: não há E2 nem realimentação de KPM
(para isso, a pilha NORI). As ações decididas são aplicadas no fechamento da janela.

Uso:
  python scripts/certification/run_conflict_experiment.py --scenario S1 --baseline B3 --seed 1001
  python scripts/certification/run_conflict_experiment.py --scenario S1 --baseline B0 --seed 1001 --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import os
import subprocess
import sys
import tempfile
import time as _time
import types
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CATALOG = ROOT / "simulations" / "ns3" / "conflicts" / "catalog.json"
RUNNER = ROOT / "scripts" / "certification" / "run_ns3_certified.sh"
BASELINES = ("B0", "B1", "B2", "B3")
SCHEDULE_FIELDS = ["time_s", "gnb", "parameter", "value", "ue", "xapp_id", "action_id"]


def load_catalog(path: Path = CATALOG) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def expand_proposals(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Expande as propostas periódicas do catálogo em eventos ordenados no tempo."""
    events = []
    for p in spec["proposals"]:
        period = float(p.get("period", 0))
        t = float(p["start"])
        end = float(p["end"])
        while t < end - 1e-9:
            events.append({
                "t": round(t, 6),
                "xapp_id": p["xapp_id"],
                "gnb": int(p["gnb"]),
                "parameter": p["parameter"],
                "value": float(p["value"]),
                "priority": int(p["priority"]),
                "ue": int(p.get("ue", -1)),
                "id": f"{p['xapp_id']}-g{p['gnb']}-{p['parameter']}-{t:.3f}",
            })
            if period <= 0:
                break
            t += period
    events.sort(key=lambda e: (e["t"], e["id"]))
    return events


def _target(e: Dict[str, Any]) -> Tuple[int, str, int]:
    return (e["gnb"], e["parameter"], e["ue"])


def _windows(events: List[Dict[str, Any]], window: float) -> "OrderedDict[int, List[Dict[str, Any]]]":
    grouped: "OrderedDict[int, List[Dict[str, Any]]]" = OrderedDict()
    for e in events:
        grouped.setdefault(int(math.floor(e["t"] / window + 1e-9)), []).append(e)
    return grouped


def _entry(e: Dict[str, Any], at: float) -> Dict[str, Any]:
    return {"time_s": round(at, 6), "gnb": e["gnb"], "parameter": e["parameter"], "value": e["value"],
            "ue": e["ue"], "xapp_id": e["xapp_id"], "action_id": e["id"]}


def baseline_b0(events, window):
    """Sem coordenação: toda proposta chega à RAN no instante em que é emitida."""
    schedule = [_entry(e, e["t"]) for e in events]
    log = [{"t_close": e["t"], "proposal_ids": [e["id"]], "selected": [e["id"]], "rule": "apply-on-arrival"}
           for e in events]
    return schedule, log


def _per_window(events, window, choose, rule):
    schedule, log = [], []
    for k, group in _windows(events, window).items():
        t_close = (k + 1) * window
        by_target: "OrderedDict[Tuple, List]" = OrderedDict()
        for e in group:
            by_target.setdefault(_target(e), []).append(e)
        winners = [choose(cands) for cands in by_target.values()]
        schedule += [_entry(w, t_close) for w in winners]
        log.append({"t_close": round(t_close, 6), "proposal_ids": [e["id"] for e in group],
                    "selected": [w["id"] for w in winners], "rule": rule})
    return schedule, log


def baseline_b1(events, window):
    """FIFO: por janela e alvo, a primeira proposta a chegar."""
    return _per_window(events, window, lambda c: min(c, key=lambda e: (e["t"], e["id"])), "fifo-per-target")


def baseline_b2(events, window):
    """Prioridade estática: por janela e alvo, a maior prioridade (empate: a mais antiga)."""
    return _per_window(events, window, lambda c: min(c, key=lambda e: (-e["priority"], e["t"], e["id"])),
                       "static-priority-per-target")


class _SimClock:
    def __init__(self):
        self.now = 0.0

    def time(self) -> float:
        return self.now


def baseline_b3(events, window):
    """H-RDL: pipeline real da xApp RDL por janela de decisão, no relógio simulado."""
    os.environ.setdefault("RDL_MODE", "OFFLINE_SIMULATION")
    os.environ.setdefault("USE_FAKE_SDL", "True")
    os.environ.setdefault("RAN_BACKEND", "NORI_NS3")
    from src.conflict_types import XAppAction
    import src.core.refinement as refinement_module
    from src.rdl_xapp import RDLxApp

    clock = _SimClock()
    original_time = refinement_module.time
    refinement_module.time = types.SimpleNamespace(time=clock.time)
    logging.disable(logging.INFO)  # mantém a saída ao vivo legível; avisos continuam visíveis
    app = RDLxApp()
    by_id = {e["id"]: e for e in events}
    dispatched: List[str] = []
    resolutions: List[Dict[str, Any]] = []

    def capture_dispatch(decision, decision_latency_ms=None):
        action = decision.selected_actions[0]
        dispatched.append(action.action_id)
        app.perception.commit_actions([action])  # aplicada na RAN simulada (sem E2/ACK)
        return f"sim-{action.action_id}"

    original_resolve = app.reasoning.resolve

    def capture_resolve(conflict):
        resolution = original_resolve(conflict)
        resolutions.append({
            "conflict_type": conflict.conflict_type.name,
            "involved": [a.action_id for a in conflict.involved_xapps],
            "winners": [a.action_id for a in resolution.winning_actions],
            "strategy": resolution.strategy_used.name,
        })
        return resolution

    app.dispatcher.dispatch_control = capture_dispatch
    app.reasoning.resolve = capture_resolve
    schedule, log = [], []
    try:
        for k, group in _windows(events, window).items():
            t_close = (k + 1) * window
            clock.now = t_close
            actions = [XAppAction(xapp_id=e["xapp_id"], node_id=f"gnb_{e['gnb']}", parameter=e["parameter"],
                                  value=e["value"], priority=e["priority"], action_id=e["id"]) for e in group]
            before, res_before = len(dispatched), len(resolutions)
            started = _time.perf_counter()
            app._process_action_group(actions)
            latency_ms = (_time.perf_counter() - started) * 1000.0
            selected = dispatched[before:]
            schedule += [_entry(by_id[a], t_close) for a in selected if a in by_id]
            log.append({"t_close": round(t_close, 6), "proposal_ids": [e["id"] for e in group],
                        "selected": selected, "resolutions": resolutions[res_before:],
                        "decision_wall_ms": round(latency_ms, 3), "rule": "hrdl-pipeline"})
    finally:
        refinement_module.time = original_time
        logging.disable(logging.NOTSET)
        app.stop()
    return schedule, log


DECIDERS = {"B0": baseline_b0, "B1": baseline_b1, "B2": baseline_b2, "B3": baseline_b3}


def decide(scenario_id: str, baseline: str, catalog: Dict[str, Any]):
    spec = catalog["scenarios"][scenario_id]
    events = expand_proposals(spec)
    window = float(catalog.get("decision_window_s", 0.2))
    schedule, log = DECIDERS[baseline](events, window)
    schedule.sort(key=lambda r: (r["time_s"], r["action_id"]))
    return spec, events, schedule, log


def repo_git_sha() -> str:
    """Commit atual do repositório; usa o git do WSL se o do Windows não estiver disponível."""
    candidates = [["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"]]
    if os.name == "nt":
        candidates.append(["wsl", "-d", "Ubuntu", "--", "git", "-C", to_wsl(ROOT), "rev-parse", "--short", "HEAD"])
    for cmd in candidates:
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        sha = out.stdout.replace("\0", "").strip()
        if out.returncode == 0 and sha:
            return sha
    return "unknown"


def write_outputs(directory: Path, scenario_id, baseline, spec, events, schedule, log) -> Tuple[Path, Path]:
    schedule_path = directory / "action_schedule.csv"
    with open(schedule_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEDULE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(schedule)
    git_sha = repo_git_sha()
    decision = {
        "scenario": scenario_id, "baseline": baseline, "ns3_scenario": spec["ns3"],
        "summary": spec.get("summary"), "conflict_window_s": spec.get("conflict_window_s"),
        "engine": "src/rdl_xapp.py RDLxApp._process_action_group" if baseline == "B3" else DECIDERS[baseline].__doc__,
        "repo_git_sha": git_sha, "proposals": events, "windows": log, "schedule": schedule,
    }
    decision_path = directory / "decision_log.json"
    decision_path.write_text(json.dumps(decision, indent=2, ensure_ascii=False), encoding="utf-8")
    return schedule_path, decision_path


def to_wsl(path: Path) -> str:
    p = str(path.resolve()).replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        return f"/mnt/{p[0].lower()}{p[2:]}"
    return p


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", required=True, help="S0..S7")
    parser.add_argument("--baseline", required=True, choices=BASELINES)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--dry-run", action="store_true", help="só gera e mostra o cronograma")
    parser.add_argument("--sim-arg", action="append", default=[], help="argumento extra do cenário")
    parser.add_argument("--no-build", action="store_true",
                        help="não recompila o ns-3 (execuções paralelas; exige binário atualizado)")
    args = parser.parse_args(argv)

    catalog = load_catalog()
    if args.scenario not in catalog["scenarios"]:
        parser.error(f"cenário desconhecido: {args.scenario}")
    spec, events, schedule, log = decide(args.scenario, args.baseline, catalog)
    print(f"=== {args.scenario} ({spec['ns3']}) baseline {args.baseline}: "
          f"{len(events)} propostas -> {len(schedule)} ações na RAN ===")
    for row in schedule:
        print(f"  t={row['time_s']:7.3f}s gnb={row['gnb']} {row['parameter']}={row['value']:g} "
              f"[{row['xapp_id']}] {row['action_id']}")

    run_id = args.run_id or f"nr_{args.scenario}_{args.baseline}_seed{args.seed}"
    with tempfile.TemporaryDirectory() as tmp:
        schedule_path, decision_path = write_outputs(Path(tmp), args.scenario, args.baseline, spec, events, schedule, log)
        if args.dry_run:
            print(schedule_path.read_text(encoding="utf-8"))
            return 0
        cmd = ["bash", to_wsl(RUNNER), "--scenario", spec["ns3"], "--seed", str(args.seed),
               "--baseline", args.baseline, "--run-id", run_id,
               "--action-schedule", to_wsl(schedule_path), "--attach", to_wsl(decision_path)]
        if args.baseline == "B3":
            cmd += ["--extra-source", "HRDL_RUNTIME"]
        if args.no_build:
            cmd += ["--no-build"]
        cmd += ["--", *spec.get("args", []), *args.sim_arg]
        if os.name == "nt":
            cmd = ["wsl", "-d", "Ubuntu", "--", *cmd]
        print("$ " + " ".join(cmd), flush=True)
        return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
