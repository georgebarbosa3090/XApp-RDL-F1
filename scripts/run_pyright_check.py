#!/usr/bin/env python3
"""
run_pyright_check.py: Validação de integridade de tipos e sintaxe estática em src/ e tests/
Garante 0 erros bloqueantes na auditoria estática da Fase 1 (H-RDL).
"""

import ast
import os
import sys
import subprocess
from typing import List, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
TESTS_DIR = os.path.join(ROOT_DIR, "tests")
CONFIG_PATH = os.path.join(ROOT_DIR, "pyrightconfig.json")


def log_step_summary(content: str):
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write(content + "\n")
        except Exception:
            pass


def audit_python_files_ast(directory: str) -> List[Tuple[str, str]]:
    errors = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    ast.parse(content, filename=path)
                except Exception as e:
                    errors.append((path, str(e)))
    return errors


def run_pyright_if_available() -> bool:
    # Tenta primeiramente via python -m pyright (wrapper canônico do pacote pip)
    commands = [
        [sys.executable, "-m", "pyright", "--project", CONFIG_PATH],
        ["pyright", "--project", CONFIG_PATH],
    ]
    
    last_stdout = ""
    last_stderr = ""
    last_code = 1
    
    for cmd in commands:
        try:
            print(f"[PYRIGHT] Executando: {' '.join(cmd)}")
            sys.stdout.flush()
            p_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            last_stdout = p_res.stdout
            last_stderr = p_res.stderr
            last_code = p_res.returncode
            print(p_res.stdout)
            if p_res.stderr:
                print(p_res.stderr, file=sys.stderr)
            sys.stdout.flush()
            sys.stderr.flush()
            
            if p_res.returncode == 0:
                log_step_summary(f"### [PASS] Pyright Static Audit\nCommand: `{' '.join(cmd)}`\n```\n{p_res.stdout}\n```")
                return True
        except FileNotFoundError as e:
            print(f"[PYRIGHT] Comando {' '.join(cmd)} não encontrado: {e}")
            continue

    log_step_summary(
        f"### [FAIL] Pyright Static Audit\n"
        f"**Exit Code:** {last_code}\n"
        f"**Stdout:**\n```\n{last_stdout}\n```\n"
        f"**Stderr:**\n```\n{last_stderr}\n```\n"
    )
    return False


def main():
    print("=== AUDITORIA DE TIPAGEM E ESTRUTURA ESTÁTICA (Fase 1 - H-RDL) ===")
    ast_errors_src = audit_python_files_ast(SRC_DIR)
    ast_errors_tests = audit_python_files_ast(TESTS_DIR)
    all_ast_errors = ast_errors_src + ast_errors_tests
    
    if all_ast_errors:
        err_msg = f"[ERRO] Encontrados {len(all_ast_errors)} arquivos com falhas de sintaxe/AST:\n"
        for path, err in all_ast_errors:
            err_msg += f"  - {path}: {err}\n"
        print(err_msg)
        log_step_summary(f"### [FAIL] AST Syntax Audit\n```\n{err_msg}\n```")
        sys.exit(1)
    else:
        print("[OK] Todos os arquivos Python em src/ e tests/ passaram no parse sintático e AST.")
        log_step_summary("### [PASS] AST Syntax Audit: 100% dos arquivos Python conformes.")

    pyright_ok = run_pyright_if_available()
    if not pyright_ok:
        print("[ERRO] Falhas de tipagem estática detectadas pelo Pyright.")
        sys.exit(1)
        
    print("=== AUDITORIA ESTÁTICA CONCLUÍDA COM SUCESSO (0 erros bloqueantes) ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
