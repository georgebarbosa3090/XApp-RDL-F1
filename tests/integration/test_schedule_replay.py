# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
Regressão de decisão: refaz o cronograma de ações de cada execução nativa registrada
(``experiments/runs/nr_*``) com o código atual e confere o sha256 gravado no manifesto
(``action_schedule_sha256``). Uma mudança nos baselines ou no pipeline que altere uma decisão já
medida falha aqui.

- B0, B1 e B2: todas as execuções.
- B3 e B3A: o B3 das execuções registradas usou o EEVS por média (B3M hoje); o B3A, o aditivo.
- Exceção documentada: S4 e S5 da campanha C1 (2026-11-08) são anteriores às regras entre células
  (achado 52 de docs/07: "as campanhas anteriores não refletem isso").
- Exceção documentada (docs/16 §10.10 e §10.16): os B3 do S15 são anteriores à regra de que um handover já
  confirmado não forma conflito indireto com propostas posteriores do mesmo nó (commit 69e241b). Antes, o EEVS
  descartava as cotas de PRB do Energy Saving que vinham depois do handover do TS; hoje elas passam. Para essas
  execuções, o teste confere que o cronograma atual contém o registrado e que as ações a mais são só cotas de PRB
  de xApps que não pediram o handover.
"""

import csv
import glob
import hashlib
import io
import json
import logging
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "certification"))

import run_conflict_experiment as rce  # noqa: E402

# Execuções anteriores às regras entre células (achado 52)
PRE_INTER_CELL = {f"nr_{s}_B3_seed{seed}" for s in ("S4", "S5") for seed in range(1001, 1006)}
DECIDER = {"B0": "B0", "B1": "B1", "B2": "B2", "B3": "B3M", "B3A": "B3A"}
# Execuções anteriores à regra do handover confirmado (docs/16 §10.10; commit 69e241b)
PRE_CONFIRMED_HO = {f"nr_S15_B3_seed{seed}" for seed in (9101, *range(11001, 11006), *range(12001, 12006))}


def _runs():
    for f in sorted(glob.glob(str(ROOT / "experiments" / "runs" / "nr_*_seed*" / "execution_manifest.json"))):
        run = Path(f).parent.name
        manifest = json.loads(Path(f).read_text(encoding="utf-8"))
        if manifest.get("baseline") in DECIDER and run not in PRE_INTER_CELL:
            yield run, manifest


def _schedule_sha(schedule):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rce.SCHEDULE_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(schedule)
    return hashlib.sha256(buf.getvalue().encode("utf-8")).hexdigest()


def _only_prb_added_after_confirmed_handover(run, schedule):
    """O cronograma atual contém o registrado, e o que sobra são cotas de PRB de xApps que não pediram handover."""
    path = ROOT / "experiments" / "runs" / run / "raw" / "action_schedule.csv"
    with open(path, newline="", encoding="utf-8") as fh:
        registered = {(round(float(r["time_s"]), 6), r["action_id"]) for r in csv.DictReader(fh)}
    current = {(round(float(r["time_s"]), 6), r["action_id"]): r for r in schedule}
    if not registered <= set(current):
        return False
    movers = {r["xapp_id"] for r in schedule if r["parameter"] == "HANDOVER"}
    extra = [current[k] for k in set(current) - registered]
    return bool(extra) and all(r["parameter"] == "PRB_QUOTA" and r["xapp_id"] not in movers for r in extra)


def test_registered_native_schedules_are_reproduced():
    runs = list(_runs())
    if not runs:
        pytest.skip("sem execuções nativas no repositório")
    os.environ.setdefault("RDL_SERVE_HTTP", "false")
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    catalog = rce.load_catalog()
    mismatched = []
    try:
        for run, manifest in runs:
            scenario = run.split("_")[1]
            if scenario not in catalog["scenarios"]:
                continue
            _, _, schedule, _ = rce.decide(scenario, DECIDER[manifest["baseline"]], catalog)
            if run in PRE_CONFIRMED_HO:
                if not _only_prb_added_after_confirmed_handover(run, schedule):
                    mismatched.append(run)
            elif _schedule_sha(schedule) != manifest.get("action_schedule_sha256"):
                mismatched.append(run)
    finally:
        logging.disable(previous)
    assert not mismatched, f"cronogramas que mudaram em relação ao registrado: {mismatched}"
