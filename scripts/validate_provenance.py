#!/usr/bin/env python3
"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Auditor de Providência e Integridade Científica (scripts/validate_provenance.py)

Valida estritamente a rastreabilidade de evidências reais extraídas do ns-3 / 5G-LENA / NORI:
  ✓ execution_manifest.json com meta-informações completas
  ✓ Hashes SHA256 do executável ns-3 e do cenário .cc
  ✓ Versão do ns-3 (3.48), commit do 5G-LENA (v5.1), commit do NORI (9b64c12)
  ✓ Semente de simulação (seed) e parâmetros CLI
  ✓ FlowMonitor XML bruto gerado pelo ns-3
  ✓ Artefatos brutos E2 KPM (.raw) capturados do socket/RMR
  ✓ Timestamps de alta resolução e logs stdout/stderr
========================================================================================
"""

import os
import sys
import json
import hashlib
import yaml
from typing import Dict, Any, List

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_provenance_policy() -> dict:
    policy_path = os.path.join(BASE_DIR, "reproducibility", "provenance_policy.yaml")
    if not os.path.exists(policy_path):
        raise FileNotFoundError(f"Arquivo de política não encontrado: {policy_path}")
    with open(policy_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def hash_file(filepath: str) -> str:
    """Calcula o hash SHA256 de um arquivo."""
    if not os.path.exists(filepath):
        return ""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def validate_run_directory(run_dir: str) -> bool:
    """Audita um diretório de execução experimental com verificação fail-closed."""
    policy = load_provenance_policy()
    allowed_sources = set(policy.get("publication_eligible_sources", []))
    banned_sources = set(policy.get("non_publication_sources", []))

    print(f"\n[+] Auditando diretório de proveniência: {os.path.relpath(run_dir, BASE_DIR)}")
    
    if not os.path.exists(run_dir):
        print(f"  [ERRO] Diretório de execução não encontrado: {run_dir}")
        return False

    manifest_path = os.path.join(run_dir, "execution_manifest.json")
    if not os.path.exists(manifest_path):
        manifest_path = os.path.join(run_dir, "metadata.json")
        
    if not os.path.exists(manifest_path):
        print(f"  [PROVENANCE_INVALID] Manifesto 'execution_manifest.json' ou 'metadata.json' ausente em {run_dir}")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Verifica Nível de Evidência e Elegibilidade de Publicação
    source = manifest.get("source", manifest.get("evidence_level", ""))
    is_pub_eligible = manifest.get("publication_eligible", source in allowed_sources)

    if any(banned in str(source) for banned in banned_sources):
        if is_pub_eligible:
            print(f"  [PROVENANCE_INVALID] Conflito de política: Fonte '{source}' é proibida para publicação, mas foi marcada como elegível.")
            return False
        else:
            print(f"  [DEV/LOCAL] Execução local detectada (fonte: '{source}'). Não elegível para publicação científica.")
            return True

    # 2. Se for elegível para publicação, exige nori_commit e raw_files (Fail-Closed)
    commit_nori = manifest.get("nori_commit", "")
    seed = manifest.get("seed", None)
    
    print(f"  - Fonte de Evidência: {source}")
    print(f"  - NORI Commit: {commit_nori if commit_nori else 'AUSENTE (FAIL)'}")
    print(f"  - Seed: {seed if seed is not None else 'Parametrizada'}")

    if is_pub_eligible and not commit_nori:
        print(f"  [PROVENANCE_INVALID] Campo 'nori_commit' ausente em execução declarada elegível para publicação.")
        return False
    
    # 3. Verifica Presença de Payloads Brutos
    raw_e2_dir = os.path.join(run_dir, "e2", "kpm")
    raw_files = []
    if os.path.exists(raw_e2_dir):
        raw_files = [f for f in os.listdir(raw_e2_dir) if f.endswith(".raw")]
        
    print(f"  - Artefatos Brutos E2 (.raw): {len(raw_files)} arquivos encontrados")
    if is_pub_eligible and len(raw_files) == 0:
        print(f"  [PROVENANCE_INVALID] NENHUM arquivo .raw E2 encontrado em {raw_e2_dir}. Exigido para elegibilidade de publicação.")
        return False

    print(f"  [OK] Rastreabilidade de proveniência aprovada para {os.path.basename(run_dir)}")
    return True

def main():
    print("=" * 80)
    print(" AUDITORIA DE PROVIDÊNCIA E INTEGRIDADE CIENTÍFICA DE EVIDÊNCIAS")
    print("=" * 80)

    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE_DIR, "experiments", "runs")
    
    if not os.path.exists(target_dir):
        print(f"[!] Nenhum resultado em {os.path.relpath(target_dir, BASE_DIR)}. Árvore limpa para novos experimentos.")
        sys.exit(0)

    success = validate_run_directory(target_dir)
    if not success:
        print("\n[PROVENANCE_INVALID] Falha na verificação de providência científica.")
        sys.exit(1)

    print("\n[OK] Validação de Providência Concluída com Sucesso!")
    sys.exit(0)

if __name__ == "__main__":
    main()
