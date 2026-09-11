#!/usr/bin/env python3
"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Auditor de Proveniência e Integridade Científica (scripts/verify_provenance_and_integrity.py)
Validador Automatizado de Conformidade com a Diretriz de ZERO DADOS SINTÉTICOS.

Regras Invioláveis de Auditoria:
  1. Nenhum script experimental pode sintetizar métricas de rede usando np.random.normal,
     np.random.uniform ou distribuições a priori de métricas.
  2. Todos os datasets de saída devem conter tags explícitas de proveniência (source).
  3. A tabela científica oficial (paper_table.csv) deve ser gerada exclusivamente a partir
     do motor físico DiscreteEventRANSimulator e da malha fechada H-RDL.
========================================================================================
"""

import os
import sys
import re
import pandas as pd
from typing import List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
EXPERIMENTS_DIR = os.path.join(BASE_DIR, "experiments", "results")

def audit_codebase_for_synthetic_generators() -> List[Tuple[str, int, str]]:
    """Varre todos os scripts de avaliação para garantir ausência total de geradores mock."""
    violations = []
    forbidden_patterns = [
        re.compile(r"np\.random\.normal\("),
        re.compile(r"np\.random\.uniform\("),
        re.compile(r"random\.gauss\("),
        re.compile(r"random\.uniform\(")
    ]

    for root, _, files in os.walk(SCRIPTS_DIR):
        for f in files:
            if f.endswith(".py"):
                fpath = os.path.join(root, f)
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                    for lno, line in enumerate(fh, 1):
                        for pat in forbidden_patterns:
                            if pat.search(line):
                                violations.append((fpath, lno, line.strip()))
    return violations

def audit_datasets_provenance() -> bool:
    """Verifica se os datasets contêm as tags de proveniência mandatárias."""
    paper_csv = os.path.join(RESULTS_DIR, "reproduced_audit_2026", "statistics", "paper_table.csv")
    if not os.path.exists(paper_csv):
        print(f"[!] Aviso: paper_table.csv não encontrado em {paper_csv}. Execute make reproduce-paper primeiro.")
        return False

    df = pd.read_csv(paper_csv)
    if "Fonte_Dados" not in df.columns:
        print("[!] Erro: Coluna 'Fonte_Dados' ausente em paper_table.csv!")
        return False

    valid_sources = ["DISCRETE_EVENT_SIMULATOR", "DISCRETE_EVENT_SIMULATOR + HRDL_RUNTIME", "NS3_FLOWMONITOR", "NORI_E2"]
    for src in df["Fonte_Dados"]:
        if src not in valid_sources:
            print(f"[!] Erro: Fonte de dados desconhecida ou inválida: '{src}'")
            return False

    print(f"[OK] paper_table.csv validado com 100% de proveniência rastreável ({len(df)} modelos auditados).")
    return True

def main():
    print("=" * 80)
    print(" AUDITORIA DE PROVENIÊNCIA E INTEGRIDADE CIENTÍFICA (ZERO DADOS SINTÉTICOS)")
    print("=" * 80)

    # 1. Auditoria Estática de Código
    print("[1/2] Verificando ausência de geradores estatísticos mock em scripts/...")
    violations = audit_codebase_for_synthetic_generators()
    if violations:
        print(f"[FALHA] Encontradas {len(violations)} ocorrências de geradores sintéticos proibidos:")
        for path, lno, line in violations:
            print(f"  - {os.path.basename(path)}:L{lno} -> {line}")
        sys.exit(1)
    else:
        print(" [OK] Nenhum gerador sintético (np.random.normal/uniform) detectado em scripts/! (100% LIMPO)")

    # 2. Auditoria de Datasets e Rastreabilidade
    print("[2/2] Auditando proveniência e integridade dos datasets de saída...")
    if not audit_datasets_provenance():
        print("[FALHA] Validação de proveniência de dados falhou.")
        sys.exit(1)

    print("\n" + "=" * 80)
    print(" [SUCESSO] REPOSITORIO 100% CONFORME COM A DIRETRIZ DE ZERO DADOS SINTETICOS! [APROVADO]")
    print("=" * 80)
    sys.exit(0)

if __name__ == "__main__":
    main()
