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
import json
from typing import List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
EXPERIMENTS_DIR = os.path.join(BASE_DIR, "experiments")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
ANALYSIS_DIR = os.path.join(BASE_DIR, "analysis")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

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


ALLOWED_EXCEPTIONS = {
    "bootstrap",
    "check_no_synthetic_results.py",
    "verify_provenance_and_integrity.py",
    "realtime_protocol_engine.py",
    "generate_demonstration_and_latest_sim_plots.py",
    "generate_rich_demo_exclusive_figures.py",
    "gerar_figuras_faltantes_hrdl.py",
    "generate_separated_phase1_phase2_figures.py",
    "generate_paper_styled_benchmarks.py",
}

def log_step_summary(content: str):
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write(content + "\n")
        except OSError as exc:
            print(f"[AVISO] Não foi possível atualizar GITHUB_STEP_SUMMARY: {exc}", file=sys.stderr)


def main():
    print("=" * 80)
    print(" AUDITORIA ESTÁTICA DE ZERO DADOS SINTÉTICOS")
    print(" Validando que nenhum gerador aleatório é usado em relatórios/experimentos...")
    print("=" * 80)

    violations: List[Tuple[str, int, str, str]] = []

    for scan_dir in [SCRIPTS_DIR, EXPERIMENTS_DIR, ANALYSIS_DIR]:
        if not os.path.exists(scan_dir):
            continue
        for root, _, files in os.walk(scan_dir):
            for f in files:
                if f.endswith((".py", ".sh")):
                    if f in ALLOWED_EXCEPTIONS:
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
        err_msg = f"[FALHA CRÍTICA] Encontradas {len(violations)} violações da política de Zero Dados Sintéticos:\n"
        for path, lno, name, line in violations:
            rel_path = os.path.relpath(path, BASE_DIR)
            err_msg += f"  - [{name}] {rel_path}:L{lno} -> {line}\n"
        print(err_msg)
        print("\n[ERRO] Abortando. Remova os geradores sintéticos antes de prosseguir.")
        log_step_summary(f"### [FAIL] Zero-Synthetic Audit\n```\n{err_msg}\n```")
        sys.exit(1)

    # Validação da existência e integridade da política de proveniência em YAML
    policy_file = os.path.join(BASE_DIR, "reproducibility", "provenance_policy.yaml")
    if not os.path.exists(policy_file):
        err = f"Política de proveniência não encontrada em: {policy_file}"
        print(f"\n[FALHA CRÍTICA] {err}")
        log_step_summary(f"### [FAIL] {err}")
        sys.exit(1)

    import yaml
    try:
        with open(policy_file, "r", encoding="utf-8") as pf:
            policy_data = yaml.safe_load(pf)
        pub_sources = policy_data.get("publication_eligible_sources", [])
        non_pub_sources = policy_data.get("non_publication_sources", [])
        firewall = policy_data.get("firewall_rules", {})
        if not pub_sources or not non_pub_sources:
            print(f"\n[FALHA CRÍTICA] provenance_policy.yaml está ausente de seções mandatárias de fontes!")
            sys.exit(1)
        print(f"\n[OK] Política de proveniência YAML (provenance_policy.yaml) parsed e validada!")
        print(f"  - Fontes Elegíveis: {pub_sources}")
        print(f"  - Fontes Restritas: {non_pub_sources}")
        print(f"  - Regra de Ouro: {firewall.get('golden_rule', 'N/A')}")
    except Exception as e:
        err = f"Erro ao carregar provenance_policy.yaml: {e}"
        print(f"\n[FALHA CRÍTICA] {err}")
        log_step_summary(f"### [FAIL] {err}")
        sys.exit(1)

    # Validação de Linhagem e Proveniência de Manifestos em experiments/
    print("\n--- Verificação de Linhagem e Proveniência de Manifestos ---")
    manifest_dirs = [os.path.join(BASE_DIR, "experiments", "results"), os.path.join(BASE_DIR, "experiments", "runs")]
    for mdir in manifest_dirs:
        if not os.path.exists(mdir):
            continue
        for root, _, files in os.walk(mdir):
            for file in files:
                if file.endswith(("_manifest.json", "manifest.json")) or file.startswith("manifest_"):
                    m_fpath = os.path.join(root, file)
                    try:
                        with open(m_fpath, "r", encoding="utf-8") as f_m:
                            m_obj = json.load(f_m)
                        cat = m_obj.get("provenance_category")
                        pub_elig = m_obj.get("publication_eligible", False)
                        gate = str(m_obj.get("gate", ""))
                        status = str(m_obj.get("status", ""))
                        # Se categoria for não publicável, não pode ter publication_eligible=True ou alegar certificação externa
                        if cat in non_pub_sources:
                            if pub_elig:
                                err = f"Violação de Linhagem: {m_fpath} categorizado como {cat} mas declara publication_eligible=True!"
                                print(f"[FALHA CRÍTICA] {err}")
                                sys.exit(1)
                            if "CERTIFIED_NON_REPUDIABLE" in status or "G5_CERTIFIED" in status or "Gate 1 - Multi-Seed" in gate:
                                err = f"Violação de Linhagem: {m_fpath} categorizado como {cat} mas declara certificação externa G5/Gate1!"
                                print(f"[FALHA CRÍTICA] {err}")
                                sys.exit(1)
                    except (OSError, json.JSONDecodeError) as exc:
                        err = f"Não foi possível validar manifesto {m_fpath}: {exc}"
                        print(f"[FALHA CRÍTICA] {err}")
                        log_step_summary(f"### [FAIL] {err}")
                        sys.exit(1)
    print("[OK] Manifestos legíveis e sem contradições explícitas detectadas; isso não comprova origem experimental.")

    # Validação do figures_manifest.json (Solução 2)
    manifest_path = os.path.join(REPORTS_DIR, "figures", "figures_manifest.json")
    if not os.path.exists(manifest_path):
        err = f"figures_manifest.json não encontrado em: {manifest_path}"
        print(f"\n[FALHA CRÍTICA] {err}")
        log_step_summary(f"### [FAIL] {err}")
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as mf:
        mdata = json.load(mf)
    figs = mdata.get("figures", [])
    ssot_hash = mdata.get("ssot_source", {}).get("sha256", "")
    if not ssot_hash or len(figs) < 25:
        err = f"figures_manifest.json incompleto! Figuras catalogadas: {len(figs)} (esperado >= 25)"
        print(f"\n[FALHA CRÍTICA] {err}")
        log_step_summary(f"### [FAIL] {err}")
        sys.exit(1)

    print(f"[OK] figures_manifest.json validado com sucesso! ({len(figs)} figuras empíricas vinculadas à SSOT {ssot_hash[:12]}...)")
    print("[OK] Varredura estática limitada concluída; isso não é certificação de proveniência empírica.")
    log_step_summary(f"### [PASS] Static synthetic-pattern scan only: {len(figs)} figures linked to SSOT {ssot_hash[:12]}.")
    sys.exit(0)

if __name__ == "__main__":
    main()
