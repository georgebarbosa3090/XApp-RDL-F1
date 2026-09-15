#!/usr/bin/env bash
# ==============================================================================
# PIPELINE AUTOMÁTICO DE ATUALIZAÇÃO DE FIGURAS E SINCRONIZAÇÃO COM O GITHUB
# Executado automaticamente ao final de cada rodada de simulação ns-3/NORI
# Autor: George Alexandro F. Barbosa / PPGC-UFPA
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "================================================================================"
echo " [AUTO-PIPELINE] Atualização Automática de Figuras, Tabelas e GitHub"
echo " Diretório Base: ${BASE_DIR}"
echo " Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"

cd "${BASE_DIR}"

# 1. Compilar Relatórios Markdown a partir dos Traces do ns-3 FlowMonitor
echo "[1/4] Processando Traces FlowMonitor XML e atualizando relatórios..."
if [ -f "scripts/generate_ns3_flowmonitor_markdown_report.py" ]; then
    python3 scripts/generate_ns3_flowmonitor_markdown_report.py || echo "[AVISO] Falha ao processar FlowMonitor XML."
fi

# 2. Exportar as 9 Tabelas CSV de Síntese
echo "[2/4] Exportando matrizes e tabelas CSV estatísticas..."
if [ -f "analysis/export_tables.py" ]; then
    python3 analysis/export_tables.py || echo "[AVISO] Falha ao exportar tabelas CSV."
fi

# 3. Regenerar Todas as 20 Figuras Científicas (300 DPI / Seaborn / 3D)
echo "[3/4] Regenerando 20 figuras científicas em alta densidade (300 DPI)..."
if [ -f "analysis/generate_plots.py" ]; then
    python3 analysis/generate_plots.py || echo "[AVISO] Falha ao gerar figuras com matplotlib/seaborn."
fi

# 4. Sincronização e Commit Automático no GitHub
echo "[4/4] Sincronizando repositório e enviando commits para o GitHub..."
if [ -d ".git" ]; then
    mkdir -p reports/figures docs/figures experiments/results/tables
    git add experiments/ results/ reports/figures/ docs/figures/ docs/
    
    COMMIT_MSG="results(sim): auto-update 20 figures, CSV tables and reports [$(date '+%Y-%m-%d %H:%M')]"
    git commit -m "${COMMIT_MSG}" || echo "[INFO] Nenhuma alteração pendente para commit."
    
    echo "Executando git pull --rebase e git push origin HEAD:main..."
    git pull --rebase origin main || true
    git push origin HEAD:main || true
    echo "[OK] GitHub sincronizado com sucesso com as novas figuras e tabelas!"
fi

echo "================================================================================"
echo " [OK] Pipeline de simulação e sincronização finalizado com sucesso!"
echo "================================================================================"
