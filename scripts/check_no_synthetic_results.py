#!/usr/bin/env python3
"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Auditor Estático de Dados Sintéticos (scripts/check_no_synthetic_results.py)

Garante que NENHUM script de processamento de experimentos ou geração de figuras
utilize geradores aleatórios sintéticos (np.random, random.gauss, etc.).
========================================================================================
"""

import os
import sys
import re
from typing import List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
EXPERIMENTS_DIR = os.path.join(BASE_DIR, "experiments")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

FORBIDDEN_PATTERNS = [
    ("np.random.normal", re.compile(r"np\.random\.normal\(")),
    ("np.random.uniform", re.compile(r"np\.random\.uniform\(")),
    ("random.gauss", re.compile(r"random\.gauss\(")),
    ("random.uniform", re.compile(r"random\.uniform\(")),
    ("random.random", re.compile(r"random\.random\(")),
    ("RandomState", re.compile(r"RandomState\(")),
    ("rng.normal", re.compile(r"rng\.normal\(")),
    ("rng.uniform", re.compile(r"rng\.uniform\(")),
    ("generate_flowmonitor_xml", re.compile(r"generate_flowmonitor_xml", re.IGNORECASE)),
    ("synthetic_metric_generator", re.compile(r"synthetic_metric_generator", re.IGNORECASE)),
    ("synthetic_tradeoff_figure", re.compile(r"cenario_2_tradeoff_energy_vs_qos\.png", re.IGNORECASE)),
]


ALLOWED_EXCEPTIONS = [
    "bootstrap",
    "check_no_synthetic_results.py"
]

def main():
    print("=" * 80)
    print(" AUDITORIA ESTÁTICA DE ZERO DADOS SINTÉTICOS")
    print(" Validando que nenhum gerador aleatório é usado em relatórios/experimentos...")
    print("=" * 80)

    violations: List[Tuple[str, int, str, str]] = []

    for scan_dir in [SCRIPTS_DIR, EXPERIMENTS_DIR]:
        if not os.path.exists(scan_dir):
            continue
        for root, _, files in os.walk(scan_dir):
            for f in files:
                if f.endswith((".py", ".sh")):
                    if any(exc in f for exc in ALLOWED_EXCEPTIONS):
                        continue
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                        for lno, line in enumerate(fh, 1):
                            line_strip = line.strip()
                            if line_strip.startswith("#") or line_strip.startswith("//"):
                                continue
                            for name, pat in FORBIDDEN_PATTERNS:
                                if pat.search(line):
                                    violations.append((fpath, lno, name, line_strip))

    if violations:
        print(f"\n[FALHA CRÍTICA] Encontradas {len(violations)} violações da política de Zero Dados Sintéticos:")
        for path, lno, name, line in violations:
            rel_path = os.path.relpath(path, BASE_DIR)
            print(f"  - [{name}] {rel_path}:L{lno} -> {line}")
        print("\n[ERRO] Abortando. Remova os geradores sintéticos antes de prosseguir.")
        sys.exit(1)

    print("\n[OK] Nenhum gerador sintético detectado no pipeline científico! (100% CONFORME)")
    sys.exit(0)

if __name__ == "__main__":
    main()
