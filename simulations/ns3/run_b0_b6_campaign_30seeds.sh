#!/usr/bin/env bash
# ==============================================================================
# Script: run_b0_b6_campaign_30seeds.sh
# Finalidade: Executa a Campanha Científica de 30 Sementes dos 7 Baselines (B0 a B6)
# Projeto: xApp-RDL Fase 1 & 2 (UFPA / PPGCOMP / O-RAN Alliance)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SEEDS="${1:-30}"
BASE_SEED="${2:-1001}"

echo "======================================================================"
echo "   Campanha Científica de Baselines B0 a B6 (N=${SEEDS} Sementes)"
echo "   Sementes: ${BASE_SEED} a $((BASE_SEED + SEEDS - 1)) | Total: $((7 * SEEDS)) Execuções"
echo "======================================================================"

cd "${BASE_DIR}"

if command -v python3 >/dev/null 2>&1; then
    echo "[1/3] Executando orquestrador estocástico de 30 sementes..."
    python3 scripts/run_b0_b6_campaign_30seeds.py --seeds "${SEEDS}" --base-seed "${BASE_SEED}"

    echo -e "\n[2/3] Atualizando inferência estatística pareada (N=${SEEDS})..."
    python3 scripts/compute_inferential_statistics_b0_b3.py

    echo -e "\n[3/3] Exportando tabelas científicas CSV consolidadas..."
    if command -v uv >/dev/null 2>&1; then
        uv run --with pandas --with scipy python analysis/export_tables.py
        uv run --with pandas --with matplotlib --with seaborn --with scipy python analysis/generate_plots.py
    else
        python3 analysis/export_tables.py
        python3 analysis/generate_plots.py
    fi
else
    echo "[ERRO] python3 não encontrado no ambiente." >&2
    exit 1
fi

echo -e "\n======================================================================"
echo "   Campanha B0–B6 com N=${SEEDS} Sementes Finalizada com SUCESSO!"
echo "   - Matriz SSOT: experiments/results/canonical_simulation_master.csv"
echo "   - 16 Tabelas CSV: experiments/results/tables/"
echo "   - 25 Figuras 300 DPI: reports/figures/"
echo "======================================================================"
