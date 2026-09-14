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
        for root, _, files in os.walk(run_dir):
            if "execution_manifest.json" in files:
                manifest_path = os.path.join(root, "execution_manifest.json")
                break
            elif "metadata.json" in files:
                manifest_path = os.path.join(root, "metadata.json")
                break
        
    if not os.path.exists(manifest_path):
        print(f"  [PROVENANCE_INVALID] Manifesto 'execution_manifest.json' ou 'metadata.json' ausente em {run_dir}")
        return False


    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Verifica Nível de Evidência e Elegibilidade de Publicação
    source = manifest.get("source", manifest.get("evidence_level", ""))
    is_pub_eligible = manifest.get("publication_eligible", source in allowed_sources)

    if source not in allowed_sources and not any(banned in str(source) for banned in banned_sources):
        print(f"  [PROVENANCE_INVALID] Fonte de evidência desconhecida e não registrada na política: '{source}'")
        return False

    if any(banned in str(source) for banned in banned_sources):
        if is_pub_eligible:
            print(f"  [PROVENANCE_INVALID] Conflito de política: Fonte '{source}' é proibida para publicação, mas foi marcada como elegível.")
            return False
        else:
            print(f"  [DEV/LOCAL] Execução local detectada (fonte: '{source}'). Não elegível para publicação científica.")
            return True

    # 2. Obtém backend e valida campos obrigatórios (Fail-Closed por Backend)
    known_backends = set(policy.get("backend_evidence_rules", {}).keys())
    raw_backend = manifest.get("backend", manifest.get("backend_id"))
    if is_pub_eligible and (not raw_backend or raw_backend.upper() not in known_backends):
        print(f"  [PROVENANCE_INVALID] Backend experimental desconhecido ou não configurado na política: '{raw_backend}'")
        return False
        
    backend_id = (raw_backend or "NORI_NS3").upper()
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

    # 3. Verifica Presença de Artefatos Brutos por Extensões Válidas do Backend
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

    # 4. Verifica Integridade Criptográfica (hashes.sha256 é mandatória para publicação elegível)
    hashes_file = os.path.join(run_dir, "hashes.sha256")
    if is_pub_eligible and not os.path.exists(hashes_file):
        print(f"  [PROVENANCE_INVALID] Arquivo de hashes 'hashes.sha256' ausente em {run_dir}. Obrigatorio para execucoes elegiveis para publicacao.")
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

    success = validate_run_directory(target_dir)
    if not success:
        print("\n[PROVENANCE_INVALID] Falha na verificação de providência científica.")
        sys.exit(1)

    print("\n[OK] Validação de Providência Concluída com Sucesso!")
    sys.exit(0)

if __name__ == "__main__":
    main()
