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

def find_run_subdirectories(parent_dir: str) -> List[str]:
    """Encontra subdiretórios contendo manifestos de execução."""
    direct_manifests = [
        "execution_manifest.json",
        "metadata.json",
        "chain_manifest.json",
        "manifest_gate1_n30.json"
    ]
    if not os.path.isdir(parent_dir):
        return []
    
    # Se o próprio diretório tiver um manifesto diretamente nele:
    if any(os.path.exists(os.path.join(parent_dir, m)) for m in direct_manifests):
        return [parent_dir]
    
    run_dirs = []
    # Verifica subdiretórios de 1º nível
    entries = sorted(os.listdir(parent_dir))

    for entry in entries:
        sub_path = os.path.join(parent_dir, entry)
        if os.path.isdir(sub_path):
            if any(os.path.exists(os.path.join(sub_path, m)) for m in direct_manifests):
                run_dirs.append(sub_path)
    
    # Se ainda não encontrou, busca recursivamente diretórios com manifesto
    if not run_dirs:
        for root, _, files in os.walk(parent_dir):
            if any(m in files for m in direct_manifests):
                run_dirs.append(root)
                
    return run_dirs


def validate_run_directory(run_dir: str) -> bool:
    """Audita um diretório de execução experimental com verificação fail-closed."""
    policy = load_provenance_policy()
    allowed_sources = set(policy.get("publication_eligible_sources", []))
    banned_sources = set(policy.get("non_publication_sources", []))

    print(f"\n[+] Auditando diretório de proveniência: {os.path.relpath(run_dir, BASE_DIR)}")
    
    if not os.path.exists(run_dir):
        print(f"  [ERRO] Diretório de execução não encontrado: {run_dir}")
        return False

    manifest_names = [
        "execution_manifest.json",
        "metadata.json",
        "chain_manifest.json",
        "manifest_gate1_n30.json"
    ]
    manifest_path = None
    for m_name in manifest_names:
        p = os.path.join(run_dir, m_name)
        if os.path.exists(p):
            manifest_path = p
            break

    if not manifest_path:
        print(f"  [PROVENANCE_INVALID] Manifesto ausente em {run_dir}")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Determina a Fonte de Evidência e Nível
    source = manifest.get("source", manifest.get("provenance_category", ""))
    raw_backend = manifest.get("backend", manifest.get("backend_id", ""))
    raw_backend_str = str(raw_backend).upper() if raw_backend else ""
    if not isinstance(source, str) or not source:
        print("  [PROVENANCE_INVALID] Campo 'source'/'provenance_category' explícito ausente.")
        return False

    is_pub_eligible = manifest.get("publication_eligible")
    if not isinstance(is_pub_eligible, bool):
        print("  [PROVENANCE_INVALID] Campo booleano 'publication_eligible' explícito ausente.")
        return False

    # Se a fonte for restrita a desenvolvimento/testes
    if source in banned_sources or any(banned in str(source) for banned in banned_sources):
        if is_pub_eligible:
            print(f"  [PROVENANCE_INVALID] Conflito de política: Fonte '{source}' é proibida para publicação, mas foi marcada como elegível.")
            return False
        else:
            print(f"  [DEV/LOCAL] Execução/fixture local detectada (fonte: '{source}'). Não elegível para publicação científica.")
            return True

    if source not in allowed_sources:
        print(f"  [PROVENANCE_INVALID] Fonte de evidência desconhecida e não registrada na política: '{source}'")
        return False

    if not is_pub_eligible:
        print(f"  [DEV/LOCAL] Fonte elegível '{source}' explicitamente marcada como não publicável.")
        return True

    # 2. Resolve only declared backend identifiers; never infer from free-form text.
    if raw_backend_str in ("NORI_NS3", "NORI_NS3_5GLENA"):
        backend_id = "NORI_NS3"
    elif raw_backend_str in ("SRSRAN_OPEN5GS",):
        backend_id = "SRSRAN_OPEN5GS"
    elif raw_backend_str in ("OPENRANBR_PHYSICAL",):
        backend_id = "OPENRANBR_PHYSICAL"
    else:
        print(f"  [PROVENANCE_INVALID] Backend explícito ausente ou desconhecido: '{raw_backend}'")
        return False

    backend_rules = policy.get("backend_evidence_rules", {}).get(backend_id)
    if not backend_rules:
        print(f"  [PROVENANCE_INVALID] Regras de evidência ausentes para backend '{backend_id}'.")
        return False

    print(f"  - Backend Experimental: {backend_id}")
    print(f"  - Fonte de Evidência: {source}")

    # 3. Require an explicit successful execution record.
    requirements = policy.get("publication_manifest_requirements", {})
    required_fields = backend_rules.get("required_manifest_fields", [])
    missing_fields = [field for field in required_fields if manifest.get(field) is None or manifest.get(field) == ""]
    if missing_fields:
        print(f"  [PROVENANCE_INVALID] Campos de manifesto ausentes para backend '{backend_id}': {missing_fields}")
        return False
    if manifest.get("run_status") != requirements.get("successful_run_status", "SUCCESS"):
        print(f"  [PROVENANCE_INVALID] run_status não confirma execução bem-sucedida: {manifest.get('run_status')!r}")
        return False
    if manifest.get("exit_code") != requirements.get("successful_exit_code", 0):
        print(f"  [PROVENANCE_INVALID] exit_code não confirma execução bem-sucedida: {manifest.get('exit_code')!r}")
        return False

    # 4. Require every evidence class specified by policy (not merely one matching extension).
    required_groups = backend_rules.get("required_raw_groups", [])
    found_raw_files = []
    for root, _, files in os.walk(run_dir):
        found_raw_files.extend(os.path.join(root, name) for name in files)
    missing_groups = [
        group for group in required_groups
        if not any(path.lower().endswith(tuple(ext.lower() for ext in group)) for path in found_raw_files)
    ]
    print(f"  - Artefatos brutos encontrados: {len(found_raw_files)} arquivos")
    if missing_groups:
        print(f"  [PROVENANCE_INVALID] Classes de evidência bruta ausentes: {missing_groups}")
        return False

    # 5. Verify complete, nonempty hash coverage and reject paths outside this run.
    hashes_file = os.path.join(run_dir, "hashes.sha256")
    if not os.path.exists(hashes_file):
        print(f"  [PROVENANCE_INVALID] Arquivo de hashes 'hashes.sha256' ausente em {run_dir}.")
        return False

    hashed_paths = set()
    with open(hashes_file, "r", encoding="utf-8") as hf:
        hash_lines = [line.strip() for line in hf if line.strip() and not line.lstrip().startswith("#")]
    if not hash_lines:
        print("  [PROVENANCE_INVALID] hashes.sha256 está vazio.")
        return False
    run_root = os.path.realpath(run_dir)
    for line in hash_lines:
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            print(f"  [PROVENANCE_INVALID] Linha de hash malformada: {line!r}")
            return False
        expected_hash, rel_path = parts[0], parts[1].lstrip("* ")
        target_file = os.path.realpath(os.path.join(run_dir, rel_path))
        if os.path.commonpath((run_root, target_file)) != run_root:
            print(f"  [PROVENANCE_INVALID] Caminho de hash escapa do diretório da execução: '{rel_path}'")
            return False
        if not os.path.isfile(target_file):
            print(f"  [PROVENANCE_INVALID] Arquivo referenciado em hashes.sha256 não encontrado: '{rel_path}'")
            return False
        actual_hash = hash_file(target_file)
        if actual_hash.lower() != expected_hash.lower():
            print(f"  [PROVENANCE_INVALID] Divergência SHA256 em '{rel_path}'.")
            return False
        hashed_paths.add(os.path.normcase(target_file))
    if requirements.get("require_all_evidence_hashed", True):
        untracked_evidence = [
            os.path.normcase(os.path.realpath(path)) for path in found_raw_files
            if os.path.normcase(os.path.realpath(path)) not in hashed_paths
        ]
        if untracked_evidence:
            print(f"  [PROVENANCE_INVALID] Evidências brutas sem hash: {untracked_evidence}")
            return False

    print(f"  [OK] Rastreabilidade de proveniência aprovada para {os.path.basename(run_dir)} [Backend={backend_id}]")
    return True


def main():
    print("=" * 80)
    print(" AUDITORIA DE PROVIDÊNCIA E INTEGRIDADE CIENTÍFICA DE EVIDÊNCIAS")
    print("=" * 80)

    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE_DIR, "experiments", "runs")
    
    if not os.path.exists(target_dir):
        print(f"[PROVENANCE_INVALID] Diretório obrigatório de resultados ausente: {os.path.relpath(target_dir, BASE_DIR)}")
        sys.exit(1)

    run_dirs = find_run_subdirectories(target_dir)
    if not run_dirs:
        print(f"[PROVENANCE_INVALID] Nenhum manifesto de execução encontrado em {target_dir}.")
        sys.exit(1)

    print(f"[i] Total de diretórios experimentais a auditar: {len(run_dirs)}")
    all_ok = True
    for r_dir in run_dirs:
        if not validate_run_directory(r_dir):
            all_ok = False

    if not all_ok:
        print("\n[PROVENANCE_INVALID] Falha na verificação de providência científica.")
        sys.exit(1)

    print("\n[OK] Validação de Providência Concluída com Sucesso!")
    sys.exit(0)

if __name__ == "__main__":
    main()
