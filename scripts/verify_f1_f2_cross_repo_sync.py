#!/usr/bin/env python3
"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer)
Verificador de Sincronização Cross-Repository (F1 H-RDL <-> F2 CA-RDL)

Valida estritamente a paridade de esquema entre repositórios:
  ✓ src/conflict_types.py (Esquema de dados compartilhados)
  ✓ docs/compliance/* (Contratos normativos e de evidência)

Modo Gate (`--strict` / `--check-gate`):
  - Retorna EXIT 1 se houver qualquer divergência de esquema/documento.
  - Retorna EXIT 1 se o repositório peer não for localizado.
========================================================================================
"""

import sys
import os
import argparse
import hashlib
from pathlib import Path

def hash_file(filepath: Path) -> str:
    if not filepath.exists():
        return ""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Verificador de Sincronização F1/F2 Cross-Repo")
    parser.add_argument("--peer-dir", type=str, default=None, help="Caminho explícito para o repositório peer (F1 ou F2)")
    parser.add_argument("--strict", "--check-gate", action="store_true", help="Executa em modo fail-closed para CI/Gate (exit 1 em divergência ou peer ausente)")
    args = parser.parse_args()

    print("=" * 80)
    print(" AUDITORIA DE SINCRONIZAÇÃO CROSS-REPOSITORY (F1 H-RDL <-> F2 CA-RDL)")
    print("=" * 80)

    current_dir = Path(__file__).resolve().parent.parent
    repo_name = current_dir.name

    if repo_name == "XApp-RDL-F1":
        f1_dir = current_dir
        f2_dir = Path(args.peer_dir).resolve() if args.peer_dir else current_dir.parent / "XApp-RDL-F2"
    elif repo_name == "XApp-RDL-F2":
        f2_dir = current_dir
        f1_dir = Path(args.peer_dir).resolve() if args.peer_dir else current_dir.parent / "XApp-RDL-F1"
    else:
        # Fallback genérico por argumento ou diretório pai
        f1_dir = Path(args.peer_dir).resolve() if args.peer_dir else current_dir.parent / "XApp-RDL-F1"
        f2_dir = current_dir if current_dir.name.endswith("F2") else current_dir.parent / "XApp-RDL-F2"

    print(f"[*] Repositório Atual: {current_dir} ({repo_name})")
    print(f"[*] Repositório F1 Target: {f1_dir}")
    print(f"[*] Repositório F2 Target: {f2_dir}")

    peer_missing = False
    if not f1_dir.exists():
        print(f"[!] ERRO: Repositório F1 não localizado em {f1_dir}.")
        peer_missing = True
    if not f2_dir.exists():
        print(f"[!] ERRO: Repositório F2 não localizado em {f2_dir}.")
        peer_missing = True

    if peer_missing:
        if args.strict:
            print("\n[FALHA GATE] Repositório peer ausente em modo estrito --strict. Cancelando aprovação.")
            sys.exit(1)
        else:
            print("\n[AVISO] Validação mantida em escopo local por falta do repositório peer. Use --strict para impor gate.")
            sys.exit(0)

    all_synced = True

    # 1. Comparação do Esquema Core conflict_types.py
    f1_conflict_types = f1_dir / "src" / "conflict_types.py"
    f2_conflict_types = f2_dir / "src" / "conflict_types.py"

    h1 = hash_file(f1_conflict_types)
    h2 = hash_file(f2_conflict_types)

    if h1 and h1 == h2:
        print("[OK] Esquema conflict_types.py 100% idêntico entre F1 e F2.")
    else:
        print("[!] DIVERGÊNCIA CRÍTICA detectada em conflict_types.py!")
        print(f"  - F1 SHA256: {h1}")
        print(f"  - F2 SHA256: {h2}")
        all_synced = False

    # 2. Comparação dos Perfis de Compatibilidade Normativa em docs/compliance/
    comp_docs = [
        "CARDL_F2_COMPATIBILITY_PROFILE.md",
        "PHASE1_PHASE2_SYNC_CONTRACT.md",
        "HRDL_F1_COMPATIBILITY_PROFILE.md",
        "EXPERIMENTAL_EVIDENCE_POLICY.md"
    ]

    for doc in comp_docs:
        p1 = f1_dir / "docs" / "compliance" / doc
        p2 = f2_dir / "docs" / "compliance" / doc
        if p1.exists() and p2.exists() and hash_file(p1) == hash_file(p2):
            print(f"[OK] Documento {doc} sincronizado.")
        else:
            print(f"[!] Documento {doc} desalinhado ou ausente entre F1 e F2.")
            all_synced = False

    print("=" * 80)
    if all_synced:
        print(" [SUCESSO] SINCRONIZAÇÃO CROSS-REPOSITORY F1 <-> F2 VERIFICADA E APROVADA!")
        print("=" * 80)
        sys.exit(0)
    else:
        print(" [FALHA] DIVERGÊNCIA DE SINCRONIZAÇÃO DETECTADA ENTRE F1 E F2.")
        print("=" * 80)
        sys.exit(1 if args.strict else 0)

if __name__ == "__main__":
    main()
