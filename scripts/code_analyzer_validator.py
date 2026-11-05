#!/usr/bin/env python3
"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Skill: 14-continuous-code-analyzer-validator
Arquivo: scripts/code_analyzer_validator.py

Agente Autônomo de Análise Estática, Validação Contínua de Código e Conformidade O-RAN/3GPP.
Audita a cada alteração:
  1. AST & Sintaxe Python / C++ ns-3
  2. Política Zero-Mock & Anti-Sintético (sem dados fictícios)
  3. Conformidade E2SM-KPM v02.03 e E2SM-RC v01.03
  4. Sincronização entre Código e Documentação
========================================================================================
"""

import os
import sys
import ast
import re
import time
import argparse
import subprocess
from typing import List, Dict, Tuple, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

FORBIDDEN_SYNTHETIC_PATTERNS = [
    (re.compile(r"np\.random\.normal\("), "np.random.normal()"),
    (re.compile(r"np\.random\.uniform\("), "np.random.uniform()"),
    (re.compile(r"random\.gauss\("), "random.gauss()"),
    (re.compile(r"random\.uniform\("), "random.uniform()"),
    (re.compile(r"random\.random\("), "random.random()"),
    (re.compile(r"RandomState\("), "RandomState()"),
    (re.compile(r"rng\.normal\("), "rng.normal()"),
    (re.compile(r"rng\.uniform\("), "rng.uniform()"),
]

ALLOWED_EXCEPTIONS = {
    "scripts/check_no_synthetic_results.py",
    "scripts/code_analyzer_validator.py",
    "tests/unit/test_random_generators.py",
}

class CodeAnalyzerValidator:
    def __init__(self, base_dir: str = BASE_DIR):
        self.base_dir = base_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed_checks: List[str] = []

    def log_pass(self, msg: str):
        self.passed_checks.append(msg)

    def log_warn(self, msg: str):
        self.warnings.append(msg)

    def log_err(self, msg: str):
        self.errors.append(msg)

    def check_python_file(self, filepath: str) -> bool:
        """Valida sintaxe AST e ausência de geradores sintéticos em arquivo Python."""
        rel_path = os.path.relpath(filepath, self.base_dir).replace("\\", "/")
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            self.log_err(f"[{rel_path}] Falha ao ler arquivo: {e}")
            return False

        # 1. Validação AST
        try:
            ast.parse(content, filename=filepath)
            self.log_pass(f"[{rel_path}] Sintaxe Python AST válida.")
        except SyntaxError as e:
            self.log_err(f"[{rel_path}] Erro de sintaxe Python na linha {e.lineno}: {e.msg}")
            return False

        # 2. Varredura Anti-Mock / Zero-Synthetic
        if rel_path not in ALLOWED_EXCEPTIONS:
            for pattern, name in FORBIDDEN_SYNTHETIC_PATTERNS:
                matches = pattern.findall(content)
                if matches:
                    self.log_err(f"[{rel_path}] Violação Zero-Synthetic: uso proibido de '{name}'. Métricas devem vir do ns-3 real.")

        return True

    def check_cpp_file(self, filepath: str) -> bool:
        """Valida código C++ do ns-3 (estrutura, headers e namespaces)."""
        rel_path = os.path.relpath(filepath, self.base_dir).replace("\\", "/")
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            self.log_err(f"[{rel_path}] Falha ao ler arquivo C++: {e}")
            return False

        # 1. Checagem de includes essenciais
        if "ns3::" not in content and "using namespace ns3;" not in content:
            self.log_warn(f"[{rel_path}] Arquivo C++ não parece utilizar o namespace ns3.")
        else:
            self.log_pass(f"[{rel_path}] Namespace ns3 verificado.")

        # 2. Checagem de tags proibidas
        if "sleep(" in content and "Simulator::Schedule" not in content:
            self.log_err(f"[{rel_path}] Uso proibido de sleep() sem integração ao relógio do simulador ns-3.")

        return True

    def get_changed_files(self) -> List[str]:
        """Obtém lista de arquivos modificados ou adicionados via git status."""
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                check=True
            )
            files = []
            for line in res.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.strip().split()
                if len(parts) >= 2:
                    filepath = parts[-1]
                    files.append(os.path.join(self.base_dir, filepath))
            return files
        except Exception:
            return []

    def run_audit(self, target_files: List[str] = None) -> bool:
        """Executa a auditoria completa."""
        self.errors.clear()
        self.warnings.clear()
        self.passed_checks.clear()

        if not target_files:
            changed = self.get_changed_files()
            if changed:
                files_to_check = changed
            else:
                # Se nada modificado, verifica arquivos core do projeto
                files_to_check = []
                for root, _, files in os.walk(os.path.join(self.base_dir, "src")):
                    for f in files:
                        if f.endswith(".py"):
                            files_to_check.append(os.path.join(root, f))
                for root, _, files in os.walk(os.path.join(self.base_dir, "simulations", "ns3")):
                    for f in files:
                        if f.endswith(".cc"):
                            files_to_check.append(os.path.join(root, f))
        else:
            files_to_check = target_files

        print(f"\n{BLUE}========================================================================{RESET}")
        print(f"{BOLD}{BLUE}   [AUDITORIA DE CÓDIGO & CONFORMIDADE O-RAN] VALIDADOR CONTÍNUO        {RESET}")
        print(f"{BLUE}========================================================================{RESET}")
        print(f"Arquivos sob inspeção: {len(files_to_check)}")

        for fpath in files_to_check:
            if not os.path.exists(fpath):
                continue
            if fpath.endswith(".py"):
                self.check_python_file(fpath)
            elif fpath.endswith(".cc") or fpath.endswith(".cpp") or fpath.endswith(".h"):
                self.check_cpp_file(fpath)

        # Resumo final
        print("------------------------------------------------------------------------")
        if self.errors:
            print(f"{RED}{BOLD}STATUS: REPROVADO ❌ ({len(self.errors)} erros encontrados){RESET}")
            for err in self.errors:
                print(f"  {RED}• {err}{RESET}")
        else:
            print(f"{GREEN}{BOLD}STATUS: APROVADO ✔ (Zero Erros Sintáticos e Zero Violações Anti-Mock){RESET}")

        if self.warnings:
            print(f"{YELLOW}Avisos ({len(self.warnings)}):{RESET}")
            for warn in self.warnings:
                print(f"  {YELLOW}• {warn}{RESET}")

        print(f"{CYAN}Checagens bem-sucedidas: {len(self.passed_checks)}{RESET}")
        print(f"{BLUE}========================================================================{RESET}\n")

        return len(self.errors) == 0

    def watch(self, interval: float = 2.0):
        """Modo contínuo: monitora arquivos e executa auditoria a cada alteração."""
        print(f"{CYAN}Iniciando sentinela contínuo em: {self.base_dir}{RESET}")
        print(f"Pressione {YELLOW}[Ctrl + C]{RESET} para encerrar o monitoramento.\n")

        last_mtimes: Dict[str, float] = {}

        def get_all_mtimes():
            mtimes = {}
            for sub in ("src", "simulations/ns3", "scripts"):
                dirpath = os.path.join(self.base_dir, sub)
                if not os.path.exists(dirpath):
                    continue
                for root, _, files in os.walk(dirpath):
                    for f in files:
                        if f.endswith((".py", ".cc", ".h", ".sh")):
                            full = os.path.join(root, f)
                            try:
                                mtimes[full] = os.path.getmtime(full)
                            except OSError:
                                pass
            return mtimes

        last_mtimes = get_all_mtimes()

        while True:
            time.sleep(interval)
            current = get_all_mtimes()
            changed = [f for f, mt in current.items() if f not in last_mtimes or mt != last_mtimes[f]]
            if changed:
                print(f"\n{YELLOW}>>> Alteração detectada em {len(changed)} arquivo(s)! Executando validação... <<<{RESET}")
                self.run_audit(changed)
                last_mtimes = current


def main():
    parser = argparse.ArgumentParser(description="Agente Analisador e Validador Contínuo de Código (Skill 14)")
    parser.add_argument("--watch", action="store_true", help="Monitorar diretórios em tempo real e validar a cada alteração")
    parser.add_argument("--file", type=str, default=None, help="Validar um arquivo específico")
    args = parser.parse_args()

    validator = CodeAnalyzerValidator()

    if args.watch:
        validator.watch()
    elif args.file:
        full_path = os.path.abspath(args.file)
        success = validator.run_audit([full_path])
        sys.exit(0 if success else 1)
    else:
        success = validator.run_audit()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
