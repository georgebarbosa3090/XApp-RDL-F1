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

import yaml

def load_provenance_policy() -> dict:
    policy_path = os.path.join(BASE_DIR, "reproducibility", "provenance_policy.yaml")
    if not os.path.exists(policy_path):
        raise FileNotFoundError(f"Arquivo de política não encontrado: {policy_path}")
    with open(policy_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def audit_datasets_provenance() -> Tuple[bool, bool]:
    """Verifica se os datasets contêm as tags de proveniência mandatárias conforme provenance_policy.yaml. Retorna (success, table_audited)"""
    policy = load_provenance_policy()
    eligible_sources = set(policy.get("publication_eligible_sources", []))
    non_eligible_sources = set(policy.get("non_publication_sources", []))
    
    paper_csv = os.path.join(RESULTS_DIR, "reproduced_audit_2026", "statistics", "paper_table.csv")
    if not os.path.exists(paper_csv):
        print(f"[!] Aviso: paper_table.csv não encontrado em {paper_csv}. Nenhuma tabela de publicação ativa para auditar.")
        print("  Status: NO_PUBLICATION_DATA_TO_VALIDATE")
        return True, False

    with open(paper_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "Fonte_Dados" not in reader.fieldnames:
            print("[!] Erro: Coluna 'Fonte_Dados' ausente em paper_table.csv!")
            return False, True

        count = 0
        non_pub_count = 0
        for row in reader:
            src = row.get("Fonte_Dados", "")
            base_src = src.split("+")[0].strip()
            if base_src in non_eligible_sources:
                non_pub_count += 1
            elif base_src not in eligible_sources:
                print(f"[!] Erro: Fonte de dados desconhecida ou não registrada no YAML: '{src}'")
                return False, True
            count += 1

    if non_pub_count > 0:
        print(f"[ERRO PROVENIÊNCIA CRÍTICO] paper_table.csv contém {non_pub_count} registros marcados como NON_PUBLICATION ({non_eligible_sources}).")
        print("  Conforme provenance_policy.yaml, dados NON_PUBLICATION NÃO PODEM estar presentes em tabelas destinadas a artigos/papers.")
        return False, True
    else:
        print(f"[OK] paper_table.csv validado com 100% de fontes elegíveis para publicação ({count} registros auditados).")
    return True, True


def main():
    print("=" * 80)
    print(" AUDITORIA DE PROVENIÊNCIA E INTEGRIDADE CIENTÍFICA (ZERO DADOS SINTÉTICOS)")
    print(" Diretriz Estrita: Proibido fabricar dados sintéticos. Apenas evidências elegíveis registradas.")
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
    success, table_audited = audit_datasets_provenance()
    if not success:
        print("[FALHA] Validação de proveniência de dados falhou.")
        sys.exit(1)

    print("\n" + "=" * 80)
    if table_audited:
        print(" [SUCESSO] REPOSITÓRIO 100% CONFORME COM A DIRETRIZ DE PROVENIÊNCIA CIENTÍFICA! [APROVADO]")
    else:
        print(" [OK] REPOSITÓRIO LIMPO: Nenhum gerador sintético encontrado. [NO_PUBLICATION_DATA_TO_VALIDATE]")
    print("=" * 80)
    sys.exit(0)

if __name__ == "__main__":
    main()
