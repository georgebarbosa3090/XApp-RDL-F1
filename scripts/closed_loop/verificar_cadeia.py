#!/usr/bin/env python3
# Autor: George Barbosa
"""
Verificador da cadeia E2 da malha fechada (docs/16 §10.1): o encerramento do ciclo NORI S8 aplicado às
execuções ``cl_*`` que gravam ``raw/e2_chain.jsonl``.

Critérios (fail-closed: ausência de evidência reprova):
- ``e2_setup`` para cada gNB anunciado no E2SetupRequest;
- ``subscription`` para cada xApp × nó;
- uma Indication (``kpm_t0``) por nó em cada janela do ``closed_loop_log.jsonl``;
- todo ``control_request`` com exatamente um desfecho: ``control_ack``, ``control_failure`` ou ``control_timeout``;
- todo ACK de controle aplicado (``status = APPLIED``) com um ``kpm_t1``;
- ``chain_summary`` no fim e hashes conferidos (``hashes.sha256``), quando existirem.

Uso: python scripts/closed_loop/verificar_cadeia.py experiments/runs/<execução> [...] [--json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def _hashes_ok(run: Path) -> Any:
    hf = run / "hashes.sha256"
    if not hf.exists():
        return None
    bad = []
    for line in hf.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        p = run / name.strip().lstrip("*")
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            bad.append(name.strip())
    return bad == [] or bad


def verify(run: Path) -> Dict[str, Any]:
    chain_file = run / "raw" / "e2_chain.jsonl"
    reasons: List[str] = []
    if not chain_file.exists():
        return {"run": run.name, "verdict": "SEM_CADEIA", "reasons": ["raw/e2_chain.jsonl ausente"]}
    recs = [json.loads(line) for line in chain_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_role = Counter(r["role"] for r in recs)
    nodes = {r["node"] for r in recs if r["role"] == "e2_setup_request"}
    setup = {r["node"] for r in recs if r["role"] == "e2_setup"}
    if not nodes or nodes != setup:
        reasons.append(f"e2_setup incompleto: anunciados {sorted(nodes)}, aceitos {sorted(setup)}")
    subs_req = {(r["xapp"], r["node"]) for r in recs if r["role"] == "subscription_request"}
    subs_ok = {(r["xapp"], r["node"]) for r in recs if r["role"] == "subscription"}
    if subs_req != subs_ok or not subs_ok:
        reasons.append(f"subscrições sem resposta: {sorted(subs_req - subs_ok)}")
    windows = 0
    log = run / "raw" / "closed_loop_log.jsonl"
    if log.exists():
        windows = sum(1 for line in log.read_text(encoding="utf-8").splitlines() if '"type": "window"' in line)
    per_node = Counter(r["node"] for r in recs if r["role"] == "kpm_t0")
    for n in nodes:
        if windows and per_node.get(n, 0) != windows:
            reasons.append(f"{n}: {per_node.get(n, 0)} Indications para {windows} janelas")
    requested = [r["action_id"] for r in recs if r["role"] == "control_request"]
    outcome = Counter(r["action_id"] for r in recs
                      if r["role"] in ("control_ack", "control_timeout")
                      or (r["role"] == "control_failure" and r.get("dispatched", True)))
    no_outcome = [a for a in requested if outcome.get(a, 0) == 0]
    multi = [a for a in requested if outcome.get(a, 0) > 1]
    if no_outcome:
        reasons.append(f"{len(no_outcome)} controle(s) sem ACK/Failure/timeout")
    if multi:
        reasons.append(f"{len(multi)} controle(s) com mais de um desfecho")
    applied = {r["action_id"] for r in recs if r["role"] == "control_ack" and r.get("status") == "APPLIED"}
    t1 = {r["action_id"]: r for r in recs if r["role"] == "kpm_t1"}
    if applied - set(t1):
        reasons.append(f"{len(applied - set(t1))} ACK(s) aplicados sem kpm_t1")
    if "chain_summary" not in by_role:
        reasons.append("sem chain_summary (execução não encerrou a cadeia)")
    hashes = _hashes_ok(run)
    if hashes not in (None, True):
        reasons.append(f"hashes divergentes: {hashes}")
    effect = [r.get("effect_ok") for a, r in t1.items() if a in applied]
    return {
        "run": run.name, "verdict": "CADEIA_COMPLETA" if not reasons else "CADEIA_INCOMPLETA", "reasons": reasons,
        "counts": {k: by_role.get(k, 0) for k in ("e2_setup", "subscription", "kpm_t0", "decision", "control_request",
                                                    "control_ack", "control_failure", "control_timeout", "kpm_t1")},
        "janelas": windows, "efeito_confirmado": sum(1 for e in effect if e), "efeito_nao_observado":
        sum(1 for e in effect if not e), "hashes": "sem arquivo" if hashes is None else ("ok" if hashes is True else "divergentes"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    results = [verify(Path(r)) for r in a.runs]
    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            c = r.get("counts", {})
            print(f"{r['run']}: {r['verdict']} | " + " ".join(f"{k}={v}" for k, v in c.items())
                  + (f" | efeito {r['efeito_confirmado']} ok / {r['efeito_nao_observado']} não observado" if c else ""))
            for why in r["reasons"]:
                print(f"  - {why}")
    return 0 if all(r["verdict"] == "CADEIA_COMPLETA" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
