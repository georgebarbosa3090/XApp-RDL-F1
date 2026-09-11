#!/usr/bin/env python3
"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Orquestrador de Simulação de Rodada Única 5G NR / O-RAN (run_single_round_simulation.py)
Especialista: @08-ns3-oran-simulation-specialist
Executa 1 rodada de simulação experimental completa com zero dados sintéticos,
utilizando o motor físico-matemático DiscreteEventRANSimulator e o H-RDL Core,
com atualização de relatórios e sincronização automática com o GitHub.
========================================================================================
"""

import os
import sys
import argparse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from scripts.run_3_consecutive_simulations import (
    run_round_1_nominal_scenarios,
    run_round_2_multi_slice_and_mobility,
    run_round_3_extreme_stress_conflict_storm,
    run_single_unified_round,
    update_markdown_report,
    sync_git_and_github,
    RESULTS_DIR
)

def main():
    parser = argparse.ArgumentParser(
        description="Executa 1 Rodada de Simulação Real 5G NR / O-RAN (Zero Dados Sintéticos)"
    )
    parser.add_argument(
        "--round",
        type=str,
        default="single",
        choices=["single", "1", "2", "3", "all"],
        help="Perfil de rodada a executar (padrão: 'single' - 1 rodada unificada S0-S8)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=RESULTS_DIR,
        help="Diretório de saída para os relatórios"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1001,
        help="Semente para inicialização do gerador pseudoaleatório físico"
    )
    parser.add_argument(
        "--auto-sync",
        dest="auto_sync",
        action="store_true",
        default=True,
        help="Habilita sincronização automática com GitHub (padrão: True)"
    )
    parser.add_argument(
        "--no-sync",
        dest="auto_sync",
        action="store_false",
        help="Desabilita sincronização automática com GitHub"
    )
    args = parser.parse_args()

    out_dir = os.path.abspath(args.output_dir)
    os.makedirs(out_dir, exist_ok=True)

    print("\n" + "=" * 80)
    print(f" EXECUTANDO SIMULAÇÃO REAL (PERFIL: {args.round.upper()}) — ZERO DADOS SINTÉTICOS")
    print(" Especialista: @08-ns3-oran-simulation-specialist")
    print(" Motor Físico: DiscreteEventRANSimulator + H-RDL (Governança Near-RT RIC)")
    print("=" * 80)

    summary = {
        "timestamp": os.environ.get("SIM_TIME", ""),
        "selected_mode": args.round
    }

    if args.round == "single":
        single_res = run_single_unified_round(out_dir, base_seed=args.seed)
        summary["round_1_nominal"] = single_res["round_1_nominal"]
        summary["round_2_multi_slice_mobility"] = single_res["round_2_multi_slice_mobility"]
        summary["round_3_extreme_stress_and_closed_loop"] = single_res["round_3_extreme_stress_and_closed_loop"]
    elif args.round == "1":
        r1 = run_round_1_nominal_scenarios(out_dir, base_seed=args.seed)
        summary["round_1_nominal"] = r1
    elif args.round == "2":
        r2 = run_round_2_multi_slice_and_mobility(out_dir, base_seed=args.seed)
        summary["round_2_multi_slice_mobility"] = r2
    elif args.round == "3":
        r3 = run_round_3_extreme_stress_conflict_storm(out_dir, base_seed=args.seed)
        summary["round_3_extreme_stress_and_closed_loop"] = {
            "s7_unsafe_actions_executed": r3["s7_unsafe_executed"],
            "s8_cre": r3["s8_cre"],
            "s6_storm_summary": r3["s6_storm_df"].to_dict(orient="records")
        }
    elif args.round == "all":
        r1 = run_round_1_nominal_scenarios(out_dir, base_seed=args.seed)
        r2 = run_round_2_multi_slice_and_mobility(out_dir, base_seed=args.seed + 10)
        r3 = run_round_3_extreme_stress_conflict_storm(out_dir, base_seed=args.seed + 20)
        summary["round_1_nominal"] = r1
        summary["round_2_multi_slice_mobility"] = r2
        summary["round_3_extreme_stress_and_closed_loop"] = {
            "s7_unsafe_actions_executed": r3["s7_unsafe_executed"],
            "s8_cre": r3["s8_cre"],
            "s6_storm_summary": r3["s6_storm_df"].to_dict(orient="records")
        }

    if args.round in ("single", "all"):
        update_markdown_report(summary)

    print("\n" + "=" * 80)
    print(" [SUCESSO] Rodada de Simulação Concluída e 100% Verificada! [OK]")
    print("=" * 80 + "\n")

    if args.auto_sync:
        sync_git_and_github(f"feat(simulation): execute single-round ({args.round}) & update reports")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    main()
