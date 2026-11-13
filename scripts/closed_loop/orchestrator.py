#!/usr/bin/env python3
# Autor: George Barbosa
"""
Orquestrador da malha fechada (docs/16 §3): ns-3 (5G-LENA) ↔ xApps ↔ baseline, janela a janela.

Fluxo de uma execução:
  1. Abre um socket Unix e chama o executor certificado (scripts/certification/run_ns3_certified.sh)
     com RDL_CONTROL_SOCKET e RDL_DECISION_WINDOW; o cenário ns-3 conecta-se ao socket
     (RdlActuation, rdl-nr-common.h) e envia a topologia ("hello").
  2. A cada janela de decisão o ns-3 pausa e envia o KPM da janela. Os drivers de xApp
     (scripts/closed_loop/drivers.py) recebem o KPM e devolvem propostas.
  3. O baseline decide as propostas da janela (B0, B1, B2 ou o pipeline real da RDL-N1: B3, B3A, B3M)
     e as ações voltam ao ns-3, aplicadas no mesmo instante simulado.
  4. Cada janela (KPM, propostas, decisão, ações) é gravada em raw/closed_loop_log.jsonl da execução,
     antes de as ações voltarem ao ns-3: o arquivo está completo quando o executor calcula os hashes.

Diferença para a malha aberta: no B0, as propostas de uma janela são aplicadas no fechamento dela,
na ordem de chegada (no executor de cronograma, cada uma é aplicada no instante em que é emitida).

Uso (Ubuntu do WSL, com o venv do projeto):
  python scripts/closed_loop/orchestrator.py --scenario S8 --baseline B3 --seed 16001 --xapps replay
"""

from __future__ import annotations

import argparse
import json
import os
import select
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "scripts" / "certification"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import run_conflict_experiment as rce  # noqa: E402
from src.core import baselines as bl  # noqa: E402
from scripts.closed_loop.drivers import ReplayDriver, XAppDriver  # noqa: E402

RUNS = ROOT / "experiments" / "runs"
EEVS = {"B3": "additive", "B3A": "additive", "B3M": "mean"}


# --------------------------------------------------------------------------- baselines por janela
class WindowBaseline:
    """Decide as propostas de uma janela. B0/B1/B2 como no executor; B3* pelo pipeline real."""

    def __init__(self, baseline: str):
        self.baseline = baseline
        self.stream = None
        self._previous_eevs = os.environ.get("RDL_EEVS_AGGREGATION")
        if baseline in EEVS:
            os.environ["RDL_EEVS_AGGREGATION"] = EEVS[baseline]
            self.stream = rce.HrdlStream()

    def decide(self, group: List[Dict[str, Any]], t_close: float) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not group:
            return [], {"t_close": round(t_close, 6), "proposal_ids": [], "selected": [], "rule": "empty"}
        if self.stream is not None:
            ids, entry = self.stream.decide(group, t_close)
            by_id = {e["id"]: e for e in group}
            return [by_id[i] for i in ids if i in by_id], entry
        winners = bl.select(group, self.baseline, rce._target, rce._arrival, lambda e: e["priority"])
        rule = bl.B0_AT_WINDOW_CLOSE if self.baseline == "B0" else bl.RULES[self.baseline]
        return winners, {"t_close": round(t_close, 6), "proposal_ids": [e["id"] for e in group],
                         "selected": [w["id"] for w in winners], "rule": rule}

    def close(self) -> None:
        if self.stream is not None:
            self.stream.close()
        if self._previous_eevs is None:
            os.environ.pop("RDL_EEVS_AGGREGATION", None)
        else:
            os.environ["RDL_EEVS_AGGREGATION"] = self._previous_eevs


# --------------------------------------------------------------------------- socket com o ns-3
class Ns3Link:
    def __init__(self, conn: socket.socket):
        self.conn = conn
        self.buf = b""

    def read(self) -> Dict[str, Any] | None:
        while b"\n" not in self.buf:
            chunk = self.conn.recv(1 << 16)
            if not chunk:
                return None
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        return json.loads(line.decode("utf-8"))

    def send_actions(self, actions: List[Dict[str, Any]]) -> None:
        lines = [f"ACT {a['gnb']} {a['parameter']} {a['value']:g} {a['ue']} {a['xapp_id']} {a['id']}"
                 for a in actions]
        self.conn.sendall(("\n".join(lines + ["END"]) + "\n").encode("utf-8"))


SHIM_BUILD = os.environ.get("RDL_SHIM_BUILD", os.path.expanduser("~/xapps-originais/shim-build"))


def build_drivers(kind: str, spec: Dict[str, Any], window: float, run_id: str) -> List[XAppDriver]:
    if kind == "replay":
        return [ReplayDriver(rce.expand_proposals(spec), window)]
    if kind == "es-orange":
        # Gate E2: só o ES Orange original no laço (as demais xApps do cenário ficam de fora)
        from scripts.closed_loop.flexric_driver import FlexricXAppDriver
        work = os.path.join(tempfile.gettempdir(), f"rdl_xapp_es_{run_id}")
        return [FlexricXAppDriver("es-orange", "energy_saving", os.path.join(SHIM_BUILD, "xapp_es_with_cell_util_rdl"),
                                  "es", priority=60, workdir=work)]
    raise SystemExit(f"--xapps {kind}: ainda não implementado (docs/16, etapas E3–E4)")


def run(args) -> int:
    catalog = rce.load_catalog()
    spec = catalog["scenarios"][args.scenario]
    window = float(catalog.get("decision_window_s", 0.2))
    run_id = args.run_id or f"cl_{args.scenario}_{args.baseline}_{args.xapps}_seed{args.seed}"
    run_dir = RUNS / run_id

    topo_file = None
    if spec.get("topology"):
        fd, topo_file = tempfile.mkstemp(suffix=".json", prefix="rdl_topology_")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(spec["topology"], fh)
        os.environ["RDL_TOPOLOGY_FILE"] = topo_file

    sock_path = os.path.join(tempfile.gettempdir(), f"rdl_ctl_{os.getpid()}.sock")
    if os.path.exists(sock_path):
        os.remove(sock_path)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(sock_path)
    server.listen(1)

    env = dict(os.environ, RDL_CONTROL_SOCKET=sock_path, RDL_DECISION_WINDOW=f"{window}")
    cmd = ["bash", str(rce.RUNNER), "--scenario", spec["ns3"], "--seed", str(args.seed),
           "--baseline", args.baseline, "--run-id", run_id]
    if args.baseline in EEVS:
        cmd += ["--extra-source", "HRDL_RUNTIME"]
    if args.no_build:
        cmd += ["--no-build"]
    cmd += ["--", *spec.get("args", []), *args.sim_arg]
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.Popen(cmd, env=env)

    baseline = WindowBaseline(args.baseline)
    drivers = build_drivers(args.xapps, spec, window, run_id)
    log_fh = None
    n_windows = n_props = n_actions = 0
    try:
        conn = None
        while conn is None:
            if proc.poll() is not None:
                print(f"[RDL-CTL] o executor terminou ({proc.returncode}) antes de conectar", flush=True)
                return proc.returncode or 1
            ready, _, _ = select.select([server], [], [], 1.0)
            if ready:
                conn, _ = server.accept()
        link = Ns3Link(conn)
        hello = link.read()
        if not hello or hello.get("type") != "hello":
            raise RuntimeError(f"esperava hello do ns-3, recebi {hello!r}")
        for d in drivers:
            d.on_hello(hello)
        run_dir.joinpath("raw").mkdir(parents=True, exist_ok=True)
        log_fh = open(run_dir / "raw" / "closed_loop_log.jsonl", "w", encoding="utf-8")
        log_fh.write(json.dumps({"type": "header", "scenario": args.scenario, "baseline": args.baseline,
                                 "xapps": args.xapps, "drivers": [d.name for d in drivers], "seed": args.seed,
                                 "window_s": window, "hello": hello}, ensure_ascii=False) + "\n")
        while True:
            msg = link.read()
            if msg is None or msg.get("type") == "end":
                break
            t = float(msg["t"])
            proposals: List[Dict[str, Any]] = []
            notes: List[Dict[str, Any]] = []
            for d in drivers:
                proposals += d.on_kpm(msg)
                dlog = getattr(d, "log", None)
                if dlog:
                    notes += [dict(n, driver=d.name) for n in dlog]
                    dlog.clear()
            proposals.sort(key=lambda e: (e["t"], e["id"]))
            actions, entry = baseline.decide(proposals, t)
            log_fh.write(json.dumps({"type": "window", "t": t, "kpm": msg, "proposals": proposals,
                                     "xapp_controls": notes, "decision": entry, "actions": actions},
                                    ensure_ascii=False) + "\n")
            log_fh.flush()
            link.send_actions(actions)
            n_windows += 1
            n_props += len(proposals)
            n_actions += len(actions)
        log_fh.close()
        log_fh = None
        print(f"[RDL-CTL] {n_windows} janelas, {n_props} propostas, {n_actions} ações", flush=True)
        return proc.wait()
    finally:
        if log_fh is not None:
            log_fh.close()
        baseline.close()
        for d in drivers:
            d.close()
        server.close()
        if os.path.exists(sock_path):
            os.remove(sock_path)
        if topo_file and os.path.exists(topo_file):
            os.remove(topo_file)
        if proc.poll() is None:
            time.sleep(0.5)
            if proc.poll() is None:
                proc.terminate()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--baseline", required=True, choices=["B0", "B1", "B2", "B3", "B3A", "B3M"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--xapps", default="replay", help="replay (gate E1) | originais (docs/16, E2–E4)")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--sim-arg", action="append", default=[])
    args = ap.parse_args(argv)
    if os.name == "nt":
        raise SystemExit("rode no Ubuntu do WSL: o ns-3 e o socket Unix ficam no Linux")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
