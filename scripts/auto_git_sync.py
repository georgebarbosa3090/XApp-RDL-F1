#!/usr/bin/env python3
"""
Auto Git Sync Daemon - XApp-RDL-F1
Sincroniza automaticamente qualquer alteração local no repositório para o GitHub.

Monitora o workspace em intervalos configuráveis, realiza git add, commit e push
para arquivos rastreados. Novos arquivos exigem staging explícito para evitar
a publicação acidental de credenciais ou arquivos locais.
"""

import os
import subprocess
import sys
import time
from datetime import datetime

CHECK_INTERVAL_SECONDS = 15
DEBOUNCE_SECONDS = 5
REMOTE_NAME = "origin"
BRANCH_NAME = "main"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_git(args: list[str], check: bool = False) -> subprocess.CompletedProcess:
    """Executa comando git no diretório raiz do repositório."""
    return subprocess.run(
        ["git"] + args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


def has_local_changes() -> bool:
    """Verifica alterações staged/unstaged em arquivos rastreados."""
    result = run_git(["status", "--porcelain", "--untracked-files=no"])
    return bool(result.stdout.strip())


def get_changed_files_summary() -> str:
    """Retorna lista resumida de arquivos alterados."""
    result = run_git(["status", "--short", "--untracked-files=no"])
    lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    if not lines:
        return "modificações gerais"
    if len(lines) <= 3:
        return ", ".join(line.split()[-1] for line in lines)
    return f"{len(lines)} arquivos alterados ({lines[0].split()[-1]}, ...)"


def sync_cycle() -> bool:
    """Executa um ciclo de verificação, commit e push se houver alterações."""
    if not has_local_changes():
        return False

    # Debounce para permitir que múltiplos arquivos de uma edição sejam gravados juntos
    time.sleep(DEBOUNCE_SECONDS)

    if not has_local_changes():
        return False

    summary = get_changed_files_summary()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"chore(auto-sync): {summary} [{now_str}]"

    print(f"[{now_str}] Alterações detectadas: {summary}")
    print(" -> Staging somente arquivos já rastreados ('git add -u')...")
    add_res = run_git(["add", "-u"])
    if add_res.returncode != 0:
        print(f" [ERRO] Falha no git add: {add_res.stderr.strip()}", file=sys.stderr)
        return False

    # Confirma se ainda há mudanças para commit
    status_staged = run_git(["diff", "--cached", "--name-only"])
    if not status_staged.stdout.strip():
        print(" -> Nenhuma alteração staged para commit.")
        return False

    print(f" -> Criando commit: '{commit_msg}'...")
    commit_res = run_git(["commit", "-m", commit_msg])
    if commit_res.returncode != 0:
        print(f" [ERRO] Falha no git commit: {commit_res.stderr.strip()}", file=sys.stderr)
        return False

    print(f" -> Enviando para {REMOTE_NAME}/{BRANCH_NAME}...")
    push_res = run_git(["push", REMOTE_NAME, BRANCH_NAME])
    if push_res.returncode == 0:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [OK] Sincronização com GitHub concluída com sucesso!")
        return True
    else:
        print(f" [AVISO] Falha ao enviar para GitHub: {push_res.stderr.strip()}", file=sys.stderr)
        return False


def main():
    print("=" * 70)
    print(" Auto Git Sync Daemon Iniciado")
    print(f" Repositório: {REPO_ROOT}")
    print(f" Destino: {REMOTE_NAME}/{BRANCH_NAME}")
    print(f" Intervalo de checagem: {CHECK_INTERVAL_SECONDS}s")
    print("=" * 70)

    # Primeira checagem imediata
    try:
        sync_cycle()
    except Exception as exc:
        print(f" [ERRO] Exceção durante sincronização inicial: {exc}", file=sys.stderr)

    if "--once" in sys.argv:
        print("[INFO] Modo de execução única (--once) finalizado.")
        return

    while True:
        try:
            time.sleep(CHECK_INTERVAL_SECONDS)
            sync_cycle()
        except KeyboardInterrupt:
            print("\nAuto Git Sync finalizado pelo usuário.")
            break
        except Exception as exc:
            print(f" [ERRO] Exceção no ciclo de sincronização: {exc}", file=sys.stderr)
            time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
