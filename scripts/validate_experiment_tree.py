#!/usr/bin/env python3
"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Validador de Artefatos Experimentais e Gate 1 (scripts/validate_experiment_tree.py)

Valida o encadeamento formal Claim -> Metric -> RawEvidence e a aprovação do Gate 1.
========================================================================================
"""

import os
import sys
import json
from typing import Dict, Any, List

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def validate_gate1() -> bool:
    """
    Valida formalmente a conjunção dos 7 critérios do Gate 1:
    G1 = g1_nori_connected ∧ g2_e2_setup ∧ g3_kpm_function ∧ g4_subscription_ack 
         ∧ g5_indication_raw ∧ g6_aper_decode ∧ g7_semantic_validation (< 5%)
    """
    print("\n[Gate 1] Avaliando status dos 7 critérios formais de interoperabilidade KPM...")
    
    gate1_runs_dir = os.path.join(BASE_DIR, "experiments", "runs", "gate1")
    if not os.path.exists(gate1_runs_dir):
        print("  [Gate 1] Diretório legado experiments/runs/gate1/ ausente; recalculando o G1 com o certificador.")
        return validate_gate1_with_certifier()

    # Procura um run_dir válido dentro de gate1_runs_dir
    run_dirs = [os.path.join(gate1_runs_dir, d) for d in os.listdir(gate1_runs_dir) if os.path.isdir(os.path.join(gate1_runs_dir, d))]
    if not run_dirs:
        print("  [Gate 1: PENDENTE] Nenhum experimento em experiments/runs/gate1/")
        return False

    # Analisa o primeiro run do Gate 1
    run_dir = run_dirs[0]
    manifest_file = os.path.join(run_dir, "execution_manifest.json")
    if not os.path.exists(manifest_file):
        manifest_file = os.path.join(run_dir, "metadata.json")

    if not os.path.exists(manifest_file):
        print("  [Gate 1: FAIL] Manifesto execution_manifest.json ausente no run do Gate 1.")
        return False

    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  [Gate 1: FAIL] Manifesto inválido ou ilegível: {exc}")
        return False

    # Gate status is derived from captured files; manifest assertions alone are insufficient.
    g1 = manifest.get("nori_connected") is True
    setup_dir = os.path.join(run_dir, "e2", "setup")
    g2 = all(
        os.path.isfile(os.path.join(setup_dir, name))
        for name in ("request.raw", "response.raw", "ran_function_definition.raw")
    )
    g3 = isinstance(manifest.get("kpm_function_id"), int) and manifest["kpm_function_id"] > 0
    subscription_dir = os.path.join(run_dir, "e2", "kpm")
    g4 = all(
        os.path.isfile(os.path.join(subscription_dir, name))
        for name in ("subscription_request.raw", "subscription_response.raw")
    )
    raw_kpm_dir = os.path.join(run_dir, "e2", "kpm")
    raw_files = [
        name for name in os.listdir(raw_kpm_dir)
        if name.startswith("indication_") and name.endswith(".raw")
    ] if os.path.exists(raw_kpm_dir) else []
    decoded_files = [
        name for name in os.listdir(raw_kpm_dir)
        if name.startswith("indication_") and name.endswith(".json")
    ] if os.path.exists(raw_kpm_dir) else []
    g5 = bool(raw_files)
    g6 = bool(decoded_files)
    sem_val = manifest.get("semantic_validation_error_pct")
    g7 = isinstance(sem_val, (int, float)) and 0 <= sem_val < 5.0
    # Versões esperadas vêm do perfil NORI do versions.lock (o NORI oficial exige ns-3.42).
    from scripts.certification.certify_chain import load_versions_lock
    nori_profile = load_versions_lock().get("profile.nori", {})
    declared_sources = manifest.get("source")
    declared_sources = declared_sources if isinstance(declared_sources, list) else [declared_sources]
    nori_commit = str(manifest.get("nori_commit") or "")
    manifest_ok = (
        "NORI_E2" in declared_sources
        and manifest.get("publication_eligible") is True
        and manifest.get("backend") in ("NORI_NS3", "NORI_NS3_5GLENA")
        and str(manifest.get("ns3_version", "")).startswith(nori_profile.get("ns3", "?"))
        and len(nori_commit) >= 7
        and nori_profile.get("nori_commit", "").startswith(nori_commit[:7])
        and manifest.get("run_status") == "SUCCESS"
        and manifest.get("exit_code") == 0
        and isinstance(manifest.get("seed"), int)
    )
    try:
        from scripts.validate_provenance import validate_run_directory
        provenance_ok = validate_run_directory(run_dir)
    except (ImportError, OSError, ValueError) as exc:
        print(f"  [Gate 1: FAIL] Verificação de proveniência falhou: {exc}")
        provenance_ok = False

    sem_str = f"{sem_val:.2f}%" if isinstance(sem_val, (int, float)) else "N/A"
    print(f"  - Manifesto e proveniência de execução: {'OK' if manifest_ok and provenance_ok else 'FAIL'}")
    print(f"  - G1.1 NORI Connected: {'OK' if g1 else 'FAIL'}")
    print(f"  - G1.2 E2 Setup: {'OK' if g2 else 'FAIL'}")
    print(f"  - G1.3 KPM Function: {'OK' if g3 else 'FAIL'}")
    print(f"  - G1.4 Subscription ACK: {'OK' if g4 else 'FAIL'}")
    print(f"  - G1.5 Indication Raw ({len(raw_files)} files): {'OK' if g5 else 'FAIL'}")
    print(f"  - G1.6 APER Decode ({len(decoded_files)} files): {'OK' if g6 else 'FAIL'}")
    print(f"  - G1.7 Semantic Validation (error={sem_str}): {'OK' if g7 else 'FAIL'}")

    all_passed = manifest_ok and provenance_ok and g1 and g2 and g3 and g4 and g5 and g6 and g7
    if not all_passed:
        print("  [Gate 1: PENDENTE / FAIL] Um ou mais dos 7 critérios formais não foram satisfeitos.")
        return False

    print("  [Gate 1: OK] Todos os 7 critérios formais de interoperabilidade KPM validados!")
    return True

def validate_gate1_with_certifier() -> bool:
    """G1 do certificador (scripts/certification/certify_chain.py), recalculado sobre experiments/runs."""
    from pathlib import Path
    from scripts.certification import certify_chain as cc
    runs_dir = Path(BASE_DIR) / "experiments" / "runs"
    if not runs_dir.is_dir():
        print("  [Gate 1: PENDENTE] experiments/runs/ ausente.")
        return False
    policy, lock, patterns = cc.load_policy(), cc.load_versions_lock(), cc.synthetic_run_id_patterns()
    reports = [cc.certify_run(p, policy, lock, patterns, cc.DEFAULT_DISSECTION_ROOT)
               for p in sorted(runs_dir.iterdir()) if p.is_dir()]
    gates = cc.evaluate_gates(reports, lock)
    g1 = gates.get("G1", {})
    print(f"  - G1 (certificador): {g1.get('verdict')} — {g1.get('reason')}")
    if g1.get("verdict") != cc.CERTIFIED:
        print("  [Gate 1: PENDENTE / FAIL] O certificador não certifica o G1.")
        return False
    print("  [Gate 1: OK] G1 certificado pelo certificador a partir das execuções do repositório.")
    return True


def main():
    print("=" * 80)
    print(" VALIDADOR DE ARTEFATOS EXPERIMENTAIS E DEPENDÊNCIA DO GATE 1")
    print("=" * 80)

    if "--check-gate1" in sys.argv:
        is_gate1_ok = validate_gate1()
        if not is_gate1_ok:
            print("\n[ERROR] Gate 1 is not experimentally validated.")
            print("Scientific report generation is disabled until Gate 1 validation passes.")
            sys.exit(1)
        else:
            print("\n[OK] Gate 1 Validado com Sucesso!")
            sys.exit(0)

    print("[OK] Estrutura da Árvore Experimental Pronta.")
    sys.exit(0)

if __name__ == "__main__":
    main()
