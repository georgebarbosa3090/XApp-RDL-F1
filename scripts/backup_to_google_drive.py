#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backup_to_google_drive.py
=========================
Script automatizado para empacotamento, cálculo de integridade SHA-256 e
envio de backup do repositório XApp-RDL-F2 para o Google Drive.

Pasta Destino no Google Drive:
- URL: https://drive.google.com/drive/folders/14ZHofqW5rT3UIXe248wb6JHiNX0WiGiM?usp=sharing
- Folder ID: 14ZHofqW5rT3UIXe248wb6JHiNX0WiGiM

Mecanismos de Envio Suportados:
1. Google Drive API v3 (OAuth 2.0 / Service Account JSON via google-api-python-client)
2. rclone CLI (se configurado no host / WSL)
3. Cópia Local para Google Drive for Desktop (se montado no sistema)
4. Empacotamento Autônomo com manifesto criptográfico local (Golden Archive)
"""

import os
import sys
import json
import time
import zipfile
import hashlib
import datetime
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

# --- CONFIGURAÇÃO GLOBAL DO BACKUP ---
GDRIVE_FOLDER_ID = "14ZHofqW5rT3UIXe248wb6JHiNX0WiGiM"
GDRIVE_SHARE_URL = "https://drive.google.com/drive/folders/14ZHofqW5rT3UIXe248wb6JHiNX0WiGiM?usp=sharing"

DEFAULT_PHASE2_DIR = Path(r"c:\Users\george.barbosa\.gemini\antigravity\scratch\iqos-xapp-rdl-phase2")
DEFAULT_PHASE1_DIR = Path(r"c:\Users\george.barbosa\.gemini\antigravity\scratch\iqos-xapp-rdl-phase1")

EXCLUDE_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".venv", "venv", ".idea", 
    ".vscode", "node_modules", "build", "dist", ".system_generated"
}
EXCLUDE_EXTENSIONS = {".pyc", ".pyo", ".pyd", ".tmp", ".log"}


def get_project_dir() -> Path:
    """Determina o diretório de origem (XApp-RDL-F2)."""
    if DEFAULT_PHASE2_DIR.exists():
        return DEFAULT_PHASE2_DIR
    cwd = Path.cwd()
    if (cwd / "docs").exists() and (cwd / "analysis").exists():
        return cwd
    return DEFAULT_PHASE1_DIR


def calculate_sha256(filepath: Path) -> str:
    """Calcula o checksum SHA-256 de um arquivo."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_git_commit_info(repo_dir: Path) -> Dict[str, str]:
    """Obtém informações do último commit Git."""
    info = {"commit_sha": "unknown", "branch": "main", "author": "George Barbosa"}
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir, capture_output=True, text=True, check=True
        )
        info["commit_sha"] = res.stdout.strip()
        
        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_dir, capture_output=True, text=True, check=True
        )
        info["branch"] = branch_res.stdout.strip()
    except Exception:
        pass
    return info


def create_backup_archive(source_dir: Path, output_dir: Path) -> Path:
    """
    Empacota o diretório XApp-RDL-F2 em um arquivo ZIP com carimbo temporal.
    Gera manifesto JSON e tabela de hashes SHA-256.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"backup_XApp-RDL-F2_{timestamp}.zip"
    archive_path = output_dir / archive_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[1/4] Empacotando diretório: {source_dir}")
    print(f"      Destino do arquivo ZIP: {archive_path}")

    files_to_zip = []
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            p = Path(root) / f
            if p.suffix.lower() not in EXCLUDE_EXTENSIONS and not p.name.startswith("."):
                files_to_zip.append(p)

    total_uncompressed_bytes = sum(p.stat().st_size for p in files_to_zip)
    print(f"      Total de arquivos selecionados: {len(files_to_zip)} ({total_uncompressed_bytes / (1024*1024):.2f} MB)")

    manifest_entries = []
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for idx, file_path in enumerate(files_to_zip, start=1):
            rel_path = file_path.relative_to(source_dir)
            zipf.write(file_path, arcname=str(rel_path))
            manifest_entries.append({
                "path": str(rel_path).replace("\\", "/"),
                "size_bytes": file_path.stat().st_size,
                "modified": datetime.datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })
            if idx % 100 == 0 or idx == len(files_to_zip):
                print(f"      Comprimindo... [{idx}/{len(files_to_zip)}]")

    archive_sha256 = calculate_sha256(archive_path)
    archive_size_mb = archive_path.stat().st_size / (1024 * 1024)

    git_info = get_git_commit_info(source_dir)
    manifest = {
        "project": "XApp-RDL-F2",
        "timestamp": datetime.datetime.now().isoformat(),
        "archive_name": archive_name,
        "archive_size_mb": round(archive_size_mb, 2),
        "archive_sha256": archive_sha256,
        "total_files": len(files_to_zip),
        "git": git_info,
        "gdrive_destination": {
            "folder_id": GDRIVE_FOLDER_ID,
            "share_url": GDRIVE_SHARE_URL
        },
        "files_sample": manifest_entries[:20]
    }

    manifest_path = output_dir / f"manifest_{timestamp}.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[OK] Arquivo gerado com sucesso!")
    print(f"     Tamanho comprimido: {archive_size_mb:.2f} MB")
    print(f"     SHA-256: {archive_sha256}")
    print(f"     Manifesto: {manifest_path}")

    return archive_path


def try_upload_google_drive_api(file_path: Path, folder_id: str) -> bool:
    """Tenta realizar upload usando a API oficial do Google Drive via Python SDK."""
    print(f"\n[2/4] Tentando upload via Google Drive API v3 (Folder ID: {folder_id})...")
    
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2 import service_account
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("      [AVISO] Bibliotecas 'google-api-python-client' ou 'google-auth-oauthlib' não importadas.")
        print("      Dica: Execute com 'uv run --with google-api-python-client --with google-auth-oauthlib ...'")
        return False

    service = None
    creds = None

    # 1. Verificar credencial de Service Account em variável de ambiente
    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if sa_path and Path(sa_path).exists():
        try:
            print(f"      Utilizando Service Account: {sa_path}")
            creds = service_account.Credentials.from_service_account_file(
                sa_path, scopes=["https://www.googleapis.com/auth/drive.file"]
            )
            service = build("drive", "v3", credentials=creds)
        except Exception as e:
            print(f"      [ERRO] Falha ao carregar Service Account: {e}")

    # 2. Verificar token OAuth 2.0 salvo em disco
    token_path = Path.home() / ".config" / "gdrive" / "token.json"
    client_secret_path = Path.home() / ".config" / "gdrive" / "credentials.json"
    
    if not service and token_path.exists():
        try:
            print(f"      Utilizando Token OAuth: {token_path}")
            creds = Credentials.from_authorized_user_file(str(token_path), ["https://www.googleapis.com/auth/drive.file"])
            service = build("drive", "v3", credentials=creds)
        except Exception as e:
            print(f"      [ERRO] Falha ao ler token OAuth: {e}")

    if not service:
        print("      [INFO] Nenhuma credencial automática do Google Drive detectada no ambiente.")
        print("      Para ativar upload direto via API:")
        print("      1. Crie um projeto no Google Cloud Console e ative a Google Drive API.")
        print(f"      2. Baixe 'credentials.json' para: {client_secret_path}")
        print("      3. Execute: python scripts/backup_to_google_drive.py --auth")
        return False

    try:
        file_metadata = {
            "name": file_path.name,
            "parents": [folder_id],
            "description": f"Backup automatizado XApp-RDL-F2 ({datetime.datetime.now().isoformat()})"
        }
        media = MediaFileUpload(str(file_path), mimetype="application/zip", resumable=True)
        print(f"      Iniciando streaming de upload para o Google Drive...")
        request = service.files().create(body=file_metadata, media_body=media, fields="id, name, webViewLink")
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"      Progresso de upload: {int(status.progress() * 100)}%")

        print(f"[OK] Upload concluído com sucesso no Google Drive!")
        print(f"     ID do Arquivo no Drive: {response.get('id')}")
        print(f"     Link de Acesso: {response.get('webViewLink')}")
        return True

    except Exception as e:
        print(f"      [ERRO] Falha durante o upload da API: {e}")
        return False


def try_upload_rclone(file_path: Path, folder_id: str) -> bool:
    """Tenta realizar upload usando o rclone CLI se disponível."""
    print(f"\n[3/4] Verificando integração via rclone CLI...")
    rclone_bin = shutil.which("rclone")
    if not rclone_bin:
        print("      rclone não encontrado no PATH do sistema.")
        return False

    try:
        res = subprocess.run([rclone_bin, "listremotes"], capture_output=True, text=True)
        remotes = [r.strip().rstrip(":") for r in res.stdout.splitlines() if r.strip()]
        if not remotes:
            print("      Nenhum controle remoto configurado no rclone.")
            return False

        remote = remotes[0]
        dest = f"{remote}:XApp-RDL-F2_Backups/"
        print(f"      Executando: rclone copy {file_path} {dest}")
        subprocess.run([rclone_bin, "copy", str(file_path), dest], check=True)
        print(f"[OK] Backup sincronizado via rclone com {dest}")
        return True
    except Exception as e:
        print(f"      [AVISO] Falha na sincronização via rclone: {e}")
        return False


def try_local_gdrive_sync(file_path: Path) -> bool:
    """Verifica se há pastas de sincronização do Google Drive for Desktop instaladas."""
    print(f"\n[4/4] Verificando Google Drive for Desktop montado localmente...")
    possible_roots = [
        Path(r"G:\Meu Drive"),
        Path(r"G:\My Drive"),
        Path(r"C:\Users\george.barbosa\Google Drive"),
        Path(r"C:\Users\george.barbosa\Meu Drive"),
    ]
    for root in possible_roots:
        if root.exists():
            dest_dir = root / "XApp-RDL-F2_Backups"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / file_path.name
            shutil.copy2(file_path, dest_file)
            print(f"[OK] Cópia local para Google Drive concluída: {dest_file}")
            print(f"     A sincronização em segundo plano cuidará do envio.")
            return True

    print("      Nenhum drive local 'G:\\' ou pasta sincronizada detectada no sistema.")
    return False


def main():
    print("=" * 80)
    print("      SISTEMA DE BACKUP AUTOMATIZADO XApp-RDL-F2 -> GOOGLE DRIVE")
    print(f"      Destino: {GDRIVE_SHARE_URL}")
    print(f"      Folder ID: {GDRIVE_FOLDER_ID}")
    print("=" * 80)

    repo_dir = get_project_dir()
    backup_dir = repo_dir / "backups"
    
    # 1. Gerar pacote ZIP e manifesto
    archive_path = create_backup_archive(repo_dir, backup_dir)

    # 2. Tentar upload via Google Drive API
    uploaded = try_upload_google_drive_api(archive_path, GDRIVE_FOLDER_ID)

    # 3. Tentar via rclone se API não configurada
    if not uploaded:
        uploaded = try_upload_rclone(archive_path, GDRIVE_FOLDER_ID)

    # 4. Tentar via Google Drive Desktop local
    if not uploaded:
        uploaded = try_local_gdrive_sync(archive_path)

    # 5. Resumo Final
    print("\n" + "=" * 80)
    print("RESUMO DO BACKUP DE GOVERNANÇA XApp-RDL-F2:")
    print(f"- Arquivo Compactado: {archive_path}")
    print(f"- Tamanho: {archive_path.stat().st_size / (1024*1024):.2f} MB")
    print(f"- Checksum SHA-256: {calculate_sha256(archive_path)}")
    print(f"- URL do Google Drive: {GDRIVE_SHARE_URL}")
    if uploaded:
        print("- Status de Transmissão: SINCRONIZADO COM SUCESSO!")
    else:
        print("- Status de Transmissão: ARQUIVO PRONTO LOCALMENTE PARA ENVIO.")
        print(f"  Você pode arrastar o arquivo '{archive_path.name}' diretamente para a pasta do link acima,")
        print("  ou configurar credenciais de API do Google Drive para envio totalmente transparente.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
