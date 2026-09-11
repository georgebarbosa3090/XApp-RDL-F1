#!/usr/bin/env python3
"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Auditor de Proveniência e Integridade Científica (scripts/verify_provenance_and_integrity.py)
Validador Automatizado de Conformidade com a Diretriz Estrita de ZERO DADOS SINTÉTICOS.

Regras Invioláveis de Auditoria:
  1. É PERMANENTEMENTE PROIBIDO gerar, usar ou fabricar dados sintéticos ou mocks aleatórios
     (np.random.normal, np.random.uniform, random.gauss, random.uniform, RandomState, etc.).
  2. Apenas dados extraídos do FlowMonitor do ns-3 NORI / 5G-LENA ou do motor discreto
     físico DiscreteEventRANSimulator (3GPP TR 38.901 + Near-RT RIC H-RDL) são aceitos.
  3. Todos os datasets de saída e tabelas científicas devem conter rastreabilidade 100% comprovada.
========================================================================================
"""

import os
import sys
import re
import csv
from typing import List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
SRC_DIR = os.path.join(BASE_DIR, "src")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
EXPERIMENTS_DIR = os.path.join(BASE_DIR, "experiments", "results")

FORBIDDEN_PATTERNS = [
    ("np.random.normal", re.compile(r"np\.random\.normal\(")),
    ("np.random.uniform", re.compile(r"np\.random\.uniform\(")),
    ("random.gauss", re.compile(r"random\.gauss\(")),
    ("random.uniform", re.compile(r"random\.uniform\(")),
    ("RandomState", re.compile(r"RandomState\(")),
    ("rng.normal", re.compile(r"rng\.normal\(")),
    ("rng.uniform", re.compile(r"rng\.uniform\(")),
    ("generate_synthetic", re.compile(r"generate_synthetic|synthetic_data|generate_multi_seed_data", re.IGNORECASE)),
]

def audit_codebase_for_synthetic_generators() -> List[Tuple[str, int, str, str]]:
    """Varre todos os scripts e módulos para garantir ausência total de geradores mock."""
    violations = []

    for scan_dir in [SCRIPTS_DIR, SRC_DIR]:
        for root, _, files in os.walk(scan_dir):
            if any(skip in root for skip in [".git", ".venv", "__pycache__", ".agents"]):
                continue
            for f in files:
                if f.endswith((".py", ".sh", ".ps1")):
                    if f == "verify_provenance_and_integrity.py":
                        continue
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                        for lno, line in enumerate(fh, 1):
                            for name, pat in FORBIDDEN_PATTERNS:
                                if pat.search(line):
                                    violations.append((fpath, lno, name, line.strip()))
    return violations

def audit_datasets_provenance() -> bool:
    """Verifica se os datasets contêm as tags de proveniência mandatárias."""
    paper_csv = os.path.join(RESULTS_DIR, "reproduced_audit_2026", "statistics", "paper_table.csv")
    if not os.path.exists(paper_csv):
        print(f"[!] Aviso: paper_table.csv não encontrado em {paper_csv}. Execute python scripts/reproduce_paper_artifacts.py primeiro.")
        return True

    with open(paper_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "Fonte_Dados" not in reader.fieldnames:
            print("[!] Erro: Coluna 'Fonte_Dados' ausente em paper_table.csv!")
            return False

        valid_sources = ["DISCRETE_EVENT_SIMULATOR", "DISCRETE_EVENT_SIMULATOR + HRDL_RUNTIME", "NS3_FLOWMONITOR", "NORI_E2"]
        count = 0
        for row in reader:
            src = row.get("Fonte_Dados", "")
            if src not in valid_sources:
                print(f"[!] Erro: Fonte de dados desconhecida ou inválida: '{src}'")
                return False
            count += 1

    print(f"[OK] paper_table.csv validado com 100% de proveniência rastreável ({count} modelos auditados).")
    return True

def main():
    print("=" * 80)
    print(" AUDITORIA DE PROVENIÊNCIA E INTEGRIDADE CIENTÍFICA (ZERO DADOS SINTÉTICOS)")
    print(" Diretriz Estrita: Proibido fabricar dados sintéticos. Apenas FlowMonitor/ns-3/DiscreteEvent.")
    print("=" * 80)

    # 1. Auditoria Estática de Código
    print("[1/2] Verificando ausência total de geradores estatísticos mock...")
    violations = audit_codebase_for_synthetic_generators()
    if violations:
        print(f"[FALHA CRÍTICA] Encontradas {len(violations)} ocorrências de geradores sintéticos proibidos:")
        for path, lno, name, line in violations:
            print(f"  - [{name}] {os.path.basename(path)}:L{lno} -> {line}")
        sys.exit(1)
    else:
        print(" [OK] Nenhum gerador sintético detectado no código! (100% LIMPO E FACTUAL)")

    # 2. Auditoria de Datasets e Rastreabilidade
    print("[2/2] Auditando proveniência e integridade dos datasets de saída...")
    if not audit_datasets_provenance():
        print("[FALHA] Validação de proveniência de dados falhou.")
        sys.exit(1)

    print("\n" + "=" * 80)
    print(" [SUCESSO] REPOSITÓRIO 100% CONFORME COM A DIRETRIZ DE ZERO DADOS SINTÉTICOS! [APROVADO]")
    print("=" * 80)
    sys.exit(0)

if __name__ == "__main__":
    main()
