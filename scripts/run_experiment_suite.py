#!/usr/bin/env python3
"""
Orquestrador Geral da Suíte de Experimentos xApp RDL - Fase 1
Organiza os resultados em diretórios por data (YYYY-MM-DD/run_HHMMSS),
assegura que nenhuma execução do mesmo dia seja sobrescrita,
espelha a versão mais recente em experiments/results/ (e experiments/results/latest/),
e envia automaticamente os artefatos gerados para o GitHub.
"""

import os
import sys
import shutil
import datetime
import subprocess
import argparse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPERIMENTS_DIR = os.path.join(BASE_DIR, "experiments", "results")

def archive_historical_data_if_needed():
    """Garante que a execução anterior de 27 de agosto fique preservada em seu próprio diretório diário."""
    aug27_dir = os.path.join(EXPERIMENTS_DIR, "2026-08-27", "run_132651")
    if not os.path.exists(aug27_dir):
        os.makedirs(aug27_dir, exist_ok=True)
        # Se os arquivos raiz forem da execução antiga de 27/08, preserva cópia em 2026-08-27
        for item in [
            "relatorio_comparativo.md", "relatorio_comparativo.json",
            "relatorio_comparativo_detalhado.md", "avaliacao_completa_metricas.json",
            "dataset_flow_metrics.csv", "dataset_rdl_decisions_ml.csv",
            "graficos_benchmarks_rdl.png", "comparativo_completo_cenarios_rdl.png",
            "avaliacao_modelos_ml_rdl.png"
        ]:
            src = os.path.join(EXPERIMENTS_DIR, item)
            dst = os.path.join(aug27_dir, item)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)
        
        # Preserva traces de baseline e rdl_phase1 se existirem
        for sub in ["baseline", "rdl_phase1"]:
            src_sub = os.path.join(EXPERIMENTS_DIR, sub)
            dst_sub = os.path.join(aug27_dir, sub)
            if os.path.exists(src_sub) and not os.path.exists(dst_sub):
                shutil.copytree(src_sub, dst_sub, dirs_exist_ok=True)
        print(f"[OK] Histórico da execução de 27/08 preservado em: {aug27_dir}")

def get_python_cmd():
    """Identifica o interpretador Python adequado."""
    venv_py_win = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")
    venv_py_linux = os.path.join(BASE_DIR, ".venv", "bin", "python")
    if os.path.exists(venv_py_win):
        return venv_py_win
    elif os.path.exists(venv_py_linux):
        return venv_py_linux
    return sys.executable

def run_suite(push_git=True, custom_date=None):
    now = datetime.datetime.now()
    date_str = custom_date or now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    run_id = f"run_{now.strftime('%H%M%S')}"

    months_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    date_formatted_pt = f"{now.day} de {months_pt.get(now.month, 'Agosto')} de {now.year}"

    # Diretório específico do dia e execução: experiments/results/YYYY-MM-DD/run_HHMMSS
    day_dir = os.path.join(EXPERIMENTS_DIR, date_str)
    run_dir = os.path.join(day_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)

    # Diretório latest
    latest_dir = os.path.join(EXPERIMENTS_DIR, "latest")
    os.makedirs(latest_dir, exist_ok=True)

    print("========================================================================")
    print(f" Execução da Suíte de Experimentos xApp RDL - Fase 1")
    print(f" Data: {date_formatted_pt} ({date_str}) | Execução: {run_id}")
    print(f" Destino: {run_dir}")
    print("========================================================================")

    # 1. Preservar histórico se necessário
    archive_historical_data_if_needed()

    # 2. Copiar traces brutos existentes de baseline / rdl se existirem
    for sub in ["baseline", "rdl_phase1"]:
        src_sub = os.path.join(EXPERIMENTS_DIR, sub)
        dst_sub = os.path.join(run_dir, sub)
        if os.path.exists(src_sub):
            shutil.copytree(src_sub, dst_sub, dirs_exist_ok=True)

    py_exe = get_python_cmd()

    # 3. Executar run_and_analyze_benchmarks.py
    print("\n[Passo 1/3] Executando Análise e Processamento de Benchmarks...")
    cmd_bench = [
        py_exe,
        os.path.join(BASE_DIR, "scripts", "run_and_analyze_benchmarks.py"),
        "--output-dir", run_dir,
        "--timestamp-str", timestamp_str
    ]
    subprocess.check_call(cmd_bench, cwd=BASE_DIR)

    # 4. Executar evaluate_and_improve_algorithms.py
    print("\n[Passo 2/3] Executando Benchmark e Treinamento de Modelos de ML...")
    cmd_ml = [
        py_exe,
        os.path.join(BASE_DIR, "scripts", "evaluate_and_improve_algorithms.py"),
        "--input-dir", run_dir,
        "--output-dir", run_dir,
        "--date-str", date_formatted_pt,
        "--timestamp-str", timestamp_str
    ]
    subprocess.check_call(cmd_ml, cwd=BASE_DIR)

    # 5. Espelhar artefatos para experiments/results/ e experiments/results/latest/
    print("\n[Passo 3/3] Atualizando espelhos de compatibilidade (latest e root)...")
    for root_mirror in [EXPERIMENTS_DIR, latest_dir]:
        for item in os.listdir(run_dir):
            src = os.path.join(run_dir, item)
            dst = os.path.join(root_mirror, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
    print("[OK] Espelhamento concluído.")

    # 6. Sincronização automática com o GitHub
    if push_git:
        print("\n========================================================================")
        print(" Sincronizando Resultados Automaticamente com o GitHub (origin main)...")
        print("========================================================================")
        try:
            subprocess.run(["git", "add", "experiments/results/", "scripts/", "docs/"], cwd=BASE_DIR, check=True)
            commit_msg = f"chore(experiments): add results for {date_str} ({run_id}) [skip ci]"
            commit_res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, capture_output=True, text=True)
            if commit_res.returncode == 0:
                print(f"[OK] Commit criado: {commit_msg}")
            else:
                print("[INFO] " + commit_res.stdout.strip())

            push_res = subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, capture_output=True, text=True)
            if push_res.returncode == 0:
                print("[OK] Resultados enviados com sucesso para o GitHub (main)!")
            else:
                print(f"[AVISO] Não foi possível fazer push automático: {push_res.stderr.strip()}")
        except Exception as e:
            print(f"[AVISO] Falha na sincronização git: {e}")

    print("\n========================================================================")
    print(f" [SUCESSO] Suíte de experimentos concluída com sucesso!")
    print(f"  Diretório da Execução: {run_dir}")
    print(f"  Relatório Markdown:    {os.path.join(run_dir, 'relatorio_comparativo.md')}")
    print(f"  Relatório Detalhado:   {os.path.join(run_dir, 'relatorio_comparativo_detalhado.md')}")
    print(f"  Métricas JSON:         {os.path.join(run_dir, 'avaliacao_completa_metricas.json')}")
    print("========================================================================\n")
    return run_dir

def main():
    parser = argparse.ArgumentParser(description="Orquestrador da Suíte de Experimentos xApp RDL")
    parser.add_argument("--push", action="store_true", default=True, help="Envia automaticamente as alterações para o GitHub")
    parser.add_argument("--no-push", dest="push", action="store_false", help="Não faz push automático para o GitHub")
    parser.add_argument("--date", default=None, help="Força uma data YYYY-MM-DD específica")
    args = parser.parse_args()

    run_suite(push_git=args.push, custom_date=args.date)

if __name__ == "__main__":
    main()
