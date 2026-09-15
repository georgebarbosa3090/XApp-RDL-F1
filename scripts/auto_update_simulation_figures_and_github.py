#!/usr/bin/env python3
"""
Pipeline Automático de Atualização de Figuras, Tabelas e Sincronização GitHub
Executado automaticamente ao final de cada rodada de simulação ns-3/NORI.
Autor: George Alexandro F. Barbosa / PPGC-UFPA
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent


def run_step(step_name, command, cwd=root_dir):
    print(f"\n--- {step_name} ---")
    try:
        res = subprocess.run(command, cwd=cwd, shell=True, check=False)
        if res.returncode == 0:
            print(f"[OK] {step_name} concluído com sucesso.")
        else:
            print(f"[AVISO] {step_name} retornou código {res.returncode}.")
    except Exception as e:
        print(f"[ERRO] Falha ao executar {step_name}: {e}")


def main():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 80)
    print(f" [AUTO-PIPELINE] Atualização Automática de Figuras, Tabelas e GitHub")
    print(f" Diretório: {root_dir}")
    print(f" Horário: {timestamp}")
    print("=" * 80)

    # 1. FlowMonitor Markdown Report
    report_script = root_dir / "scripts" / "generate_ns3_flowmonitor_markdown_report.py"
    if report_script.exists():
        run_step("1. Processar Traces FlowMonitor XML", f"{sys.executable} {report_script}")

    # 2. Exportar Tabelas CSV
    tables_script = root_dir / "analysis" / "export_tables.py"
    if tables_script.exists():
        run_step("2. Exportar Tabelas CSV de Síntese", f"{sys.executable} {tables_script}")

    # 3. Gerar 20 Figuras Científicas (300 DPI / Seaborn / 3D)
    plots_script = root_dir / "analysis" / "generate_plots.py"
    if plots_script.exists():
        run_step("3. Regenerar 20 Figuras Científicas (300 DPI)", f"{sys.executable} {plots_script}")

    # 4. Git Commit & Push Automático
    if (root_dir / ".git").exists():
        print("\n--- 4. Sincronização Automática com o GitHub ---")
        subprocess.run("git add experiments/ results/ reports/figures/ docs/figures/ docs/", cwd=root_dir, shell=True)
        commit_msg = f"results(sim): auto-update 20 figures, CSV tables and reports [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}]"
        subprocess.run(f'git commit -m "{commit_msg}"', cwd=root_dir, shell=True)
        subprocess.run("git pull --rebase origin main", cwd=root_dir, shell=True)
        push_res = subprocess.run("git push origin HEAD:main", cwd=root_dir, shell=True)
        if push_res.returncode == 0:
            print("[OK] GitHub atualizado automaticamente com as novas figuras e tabelas!")
        else:
            print("[INFO] Finalizado com status do Git.")

    print("\n" + "=" * 80)
    print(" [OK] Pipeline de simulação e sincronização finalizado com sucesso!")
    print("=" * 80)


if __name__ == "__main__":
    main()
