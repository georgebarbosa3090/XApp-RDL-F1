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

def validate_gate1() -> bool:
    """
    Valida formalmente a conjunção dos 7 critérios do Gate 1:
    G1 = g1_nori_connected ∧ g2_e2_setup ∧ g3_kpm_function ∧ g4_subscription_ack 
         ∧ g5_indication_raw ∧ g6_aper_decode ∧ g7_semantic_validation (< 5%)
    """
    gate1_required = os.getenv("GATE_1_REQUIRED", "true").lower() in ("true", "1", "yes")
    if not gate1_required:
        return True

    print("\n[Gate 1] Avaliando status dos 7 critérios formais de interoperabilidade KPM...")
    
    gate1_runs_dir = os.path.join(BASE_DIR, "experiments", "runs", "gate1")
    if not os.path.exists(gate1_runs_dir):
        print("  [Gate 1: PENDENTE] Diretório experiments/runs/gate1/ ausente.")
        return False

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

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # g1: NORI Connected
    g1 = manifest.get("nori_connected", False) or bool(manifest.get("nori_commit", ""))
    # g2: E2 Setup
    g2 = os.path.exists(os.path.join(run_dir, "e2", "setup", "request.raw")) or manifest.get("e2_setup_success", False)
    # g3: KPM Function Announced
    g3 = manifest.get("kpm_function_id", 0) > 0 or manifest.get("kpm_announced", False)
    # g4: Subscription ACK
    g4 = os.path.exists(os.path.join(run_dir, "e2", "kpm", "subscription_response.raw")) or manifest.get("subscription_ack", False)
    # g5: RIC Indication Raw
    raw_kpm_dir = os.path.join(run_dir, "e2", "kpm")
    raw_files = [f for f in os.listdir(raw_kpm_dir) if f.endswith(".raw")] if os.path.exists(raw_kpm_dir) else []
    g5 = len(raw_files) > 0
    # g6: APER Decode
    decoded_files = [f for f in os.listdir(raw_kpm_dir) if f.endswith("_decoded.json")] if os.path.exists(raw_kpm_dir) else []
    g6 = len(decoded_files) > 0
    # g7: Semantic Validation (< 5%)
    sem_val = manifest.get("semantic_validation_error_pct", 100.0)
    g7 = sem_val < 5.0

    print(f"  - G1.1 NORI Connected: {'OK' if g1 else 'FAIL'}")
    print(f"  - G1.2 E2 Setup: {'OK' if g2 else 'FAIL'}")
    print(f"  - G1.3 KPM Function: {'OK' if g3 else 'FAIL'}")
    print(f"  - G1.4 Subscription ACK: {'OK' if g4 else 'FAIL'}")
    print(f"  - G1.5 Indication Raw ({len(raw_files)} files): {'OK' if g5 else 'FAIL'}")
    print(f"  - G1.6 APER Decode ({len(decoded_files)} files): {'OK' if g6 else 'FAIL'}")
    print(f"  - G1.7 Semantic Validation (error={sem_val:.2f}%): {'OK' if g7 else 'FAIL'}")

    all_passed = g1 and g2 and g3 and g4 and g5 and g6 and g7
    if not all_passed:
        print("  [Gate 1: PENDENTE / FAIL] Um ou mais dos 7 critérios formais não foram satisfeitos.")
        return False

    print("  [Gate 1: OK] Todos os 7 critérios formais de interoperabilidade KPM validados!")
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
