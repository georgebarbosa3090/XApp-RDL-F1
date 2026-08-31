#!/bin/bash
# ==============================================================================
# Pipeline Completo de Execucao Experimental e Coleta de Metricas (Ponta a Ponta):
# Fase 1: Baseline Sem RDL -> Fase 2: Deploy RDL -> Fase 3: Com RDL -> Fase 4: Analise & ML -> Fase 5: GitHub
# ==============================================================================
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TODAY=$(date '+%Y-%m-%d')
RUN_ID="run_$(date '+%H%M%S')"
EXP_RUN_DIR="$BASE_DIR/experiments/results/$TODAY/$RUN_ID"

echo "========================================================================"
echo "Iniciando Pipeline Experimental Completo (Baseline -> RDL -> ML -> GitHub)"
echo "Data: $TODAY | Execucao: $RUN_ID"
echo "Diretorio: $EXP_RUN_DIR"
echo "========================================================================"

mkdir -p "$EXP_RUN_DIR"

# ETAPA 1: Executar Baseline salvando no diretorio isolado
bash "$BASE_DIR/scripts/run_baseline_experiment.sh" "$EXP_RUN_DIR"

# ETAPA 2: Garantir Deploy da xApp RDL no Kubernetes
echo ""
echo "[PIPELINE] Garantindo deploy do orquestrador xApp RDL..."
bash "$BASE_DIR/scripts/deploy_helm.sh" --with-rdl || true

# ETAPA 3: Executar Cenarios com RDL e Analisar Resultados
bash "$BASE_DIR/scripts/run_rdl_experiment.sh" "$EXP_RUN_DIR"

# ETAPA 4: Treinamento e Avaliacao de Machine Learning
echo ""
echo "[ML] Executando benchmark de Machine Learning e Relatorio Detalhado..."
if [ -f "$BASE_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$BASE_DIR/.venv/bin/python"
elif [ -f "$BASE_DIR/.venv/Scripts/python.exe" ]; then
    PYTHON_CMD="$BASE_DIR/.venv/Scripts/python.exe"
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD "$BASE_DIR/scripts/evaluate_and_improve_algorithms.py" --input-dir "$EXP_RUN_DIR" --output-dir "$EXP_RUN_DIR"

# ETAPA 5: Espelhar para experiments/results/ e experiments/results/latest/
echo ""
echo "[ESPELHO] Sincronizando espelho retrocompativel..."
mkdir -p "$BASE_DIR/experiments/results/latest"
cp -r "$EXP_RUN_DIR"/* "$BASE_DIR/experiments/results/" 2>/dev/null || true
cp -r "$EXP_RUN_DIR"/* "$BASE_DIR/experiments/results/latest/" 2>/dev/null || true

# ETAPA 6: Sincronizacao Automatica com GitHub
cd "$BASE_DIR"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo ""
    echo "[GITHUB] Enviando relatorios e resultados para o GitHub..."
    git add experiments/results/ scripts/ docs/
    COMMIT_MSG="chore(experiments): save run $TODAY/$RUN_ID and update reports [skip ci]"
    if git commit -m "$COMMIT_MSG"; then
        git push origin main || echo "[AVISO] Falha no push. Verifique credenciais de rede/SSH."
    else
        echo "[INFO] Nenhum dado novo para commit."
    fi
fi

echo "========================================================================"
echo "[OK] Pipeline Completo Finalizado com Sucesso!"
echo "Resultados em: $EXP_RUN_DIR"
echo "========================================================================"

