#!/bin/bash
# ==============================================================================
# Pipeline Completo de Execucao Experimental e Coleta de Metricas (Ponta a Ponta):
# Fase 1: Baseline Sem RDL -> Fase 2: Deploy RDL -> Fase 3: Com RDL -> Fase 4: Analise
# ==============================================================================
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "========================================================================"
echo "Iniciando Pipeline Experimental Completo (Baseline -> RDL -> Analise)"
echo "========================================================================"

# ETAPA 1: Executar Baseline
bash "$BASE_DIR/scripts/run_baseline_experiment.sh"

# ETAPA 2: Garantir Deploy da xApp RDL no Kubernetes
echo ""
echo "[PIPELINE] Garantindo deploy do orquestrador xApp RDL..."
bash "$BASE_DIR/scripts/deploy_helm.sh" --with-rdl || true

# ETAPA 3: Executar Cenarios com RDL e Analisar Resultados
bash "$BASE_DIR/scripts/run_rdl_experiment.sh"

# ETAPA 4: Sincronizacao Automatica com GitHub (opcional)
cd "$BASE_DIR"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git add experiments/results/
    COMMIT_MSG="chore(experiments): update simulation results and datasets ($(date '+%Y-%m-%d %H:%M:%S')) [skip ci]"
    if git commit -m "$COMMIT_MSG"; then
        echo "[INFO] Enviando resultados para a branch main no GitHub..."
        git push origin main || echo "[AVISO] Falha ao enviar para o GitHub. Verifique conexao/credenciais."
    else
        echo "[INFO] Nenhum dado novo alterado para commit."
    fi
fi
