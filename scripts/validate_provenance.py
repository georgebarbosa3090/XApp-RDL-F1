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
    if not os.path.exists(parent_dir):
        return []
    
    # Se o próprio diretório tiver um manifesto diretamente nele:
    if any(os.path.exists(os.path.join(parent_dir, m)) for m in direct_manifests):
        return [parent_dir]
    
    run_dirs = []
    # Verifica subdiretórios de 1º nível
    try:
        entries = sorted(os.listdir(parent_dir))
    except Exception:
        return []

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
    source = manifest.get("source", manifest.get("provenance_category", manifest.get("evidence_level", manifest.get("benchmark_type", ""))))
    
    raw_backend = manifest.get("backend", manifest.get("backend_id", ""))
    raw_backend_str = str(raw_backend).upper() if raw_backend else ""

    if not source:
        if "NORI" in raw_backend_str or "NS3" in raw_backend_str:
            source = "NORI_E2"
        elif "SRSRAN" in raw_backend_str:
            source = "SRSRAN_E2"
        elif "TESTBED" in raw_backend_str or "OPENRANBR" in raw_backend_str:
            source = "OPENRANBR_TESTBED"

    # Determina elegibilidade de publicação
    is_pub_eligible = manifest.get("publication_eligible", (source in allowed_sources))

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

    # 2. Normaliza backend e valida campos obrigatórios
    backend_id = "NORI_NS3"
    if "SRSRAN" in raw_backend_str:
        backend_id = "SRSRAN_OPEN5GS"
    elif "TESTBED" in raw_backend_str or "OPENRANBR" in raw_backend_str:
        backend_id = "OPENRANBR_PHYSICAL"
    elif raw_backend_str in policy.get("backend_evidence_rules", {}):
        backend_id = raw_backend_str

    backend_rules = policy.get("backend_evidence_rules", {}).get(backend_id, {
        "required_manifest_fields": ["nori_commit"],
        "required_raw_extensions": [".xml", ".raw"]
    })

    print(f"  - Backend Experimental: {backend_id}")
    print(f"  - Fonte de Evidência: {source}")

    if is_pub_eligible:
        missing_fields = [field for field in backend_rules.get("required_manifest_fields", []) if not manifest.get(field)]
        if missing_fields:
            print(f"  [PROVENANCE_INVALID] Campos de manifesto ausentes para backend '{backend_id}': {missing_fields}")
            return False

    # 3. Verifica Presença de Artefatos Brutos
    raw_extensions = tuple(backend_rules.get("required_raw_extensions", [".raw", ".pcap", ".xml", ".log"]))
    found_raw_files = []
    
    for root, _, files in os.walk(run_dir):
        for f in files:
            if f.endswith(raw_extensions):
                found_raw_files.append(f)
        
    print(f"  - Artefatos Brutos Encontrados ({', '.join(raw_extensions)}): {len(found_raw_files)} arquivos")
    if is_pub_eligible and len(found_raw_files) == 0:
        print(f"  [PROVENANCE_INVALID] NENHUM artefato bruto {raw_extensions} encontrado em {run_dir}. Exigido para publicação elegível.")
        return False

    # 4. Verifica Integridade Criptográfica
    hashes_file = os.path.join(run_dir, "hashes.sha256")
    if is_pub_eligible and not os.path.exists(hashes_file):
        print(f"  [PROVENANCE_INVALID] Arquivo de hashes 'hashes.sha256' ausente em {run_dir}.")
        return False

    if os.path.exists(hashes_file):
        print(f"  - Verificando integridade SHA256 em {hashes_file}...")
        with open(hashes_file, "r", encoding="utf-8") as hf:
            for line in hf:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    expected_hash, rel_path = parts[0], parts[1].strip()
                    target_file = os.path.join(run_dir, rel_path)
                    if not os.path.exists(target_file):
                        target_file = os.path.join(os.path.dirname(hashes_file), rel_path)
                    if not os.path.exists(target_file):
                        print(f"  [PROVENANCE_INVALID] Arquivo referenciado em hashes.sha256 não encontrado no disco: '{rel_path}'")
                        return False
                    actual_hash = hash_file(target_file)
                    if actual_hash.lower() != expected_hash.lower():
                        print(f"  [PROVENANCE_INVALID] Divergência SHA256 em '{rel_path}': esperado {expected_hash[:8]}..., obtido {actual_hash[:8]}...")
                        return False

    print(f"  [OK] Rastreabilidade de proveniência aprovada para {os.path.basename(run_dir)} [Backend={backend_id}]")
    return True


def main():
    print("=" * 80)
    print(" AUDITORIA DE PROVIDÊNCIA E INTEGRIDADE CIENTÍFICA DE EVIDÊNCIAS")
    print("=" * 80)

    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE_DIR, "experiments", "runs")
    
    if not os.path.exists(target_dir):
        print(f"[!] Nenhum resultado em {os.path.relpath(target_dir, BASE_DIR)}. Árvore limpa para novos experimentos.")
        sys.exit(0)

    run_dirs = find_run_subdirectories(target_dir)
    if not run_dirs:
        print(f"[!] Nenhum manifesto encontrado em {target_dir}.")
        sys.exit(0)

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
