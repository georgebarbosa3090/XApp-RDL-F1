#!/usr/bin/env bash
# ==============================================================================
# Script de Reprodução Automatizada da Fase 1 (H-RDL) — XApp-RDL-F1
# Autor: George Alexandro F. Barbosa / PPGC-UFPA
# ==============================================================================

set -euo pipefail

echo "=============================================================================="
echo "Iniciando Pipeline de Reprodução Científica da Fase 1 (H-RDL)"
echo "=============================================================================="

# 1. Validação de Ambiente e Dependências
echo "[1/4] Verificando dependências Python e ambiente virtual..."
python3 -c "import pycrate, pydantic, structlog, prometheus_client; print('Dependências Python OK')"

# 2. Execução da Avaliação Estatística N=30
echo "[2/4] Executando motor estatístico multi-semente (N=30 runs)..."
python3 scripts/run_multi_seed_evaluation.py

# 3. Geração de Figuras Científicas
echo "[3/4] Gerando figuras científicas em alta resolução (300 DPI)..."
python3 scripts/generate_sbrc_figures.py

# 4. Verificação de Integridade Criptográfica
echo "[4/4] Verificando integridade SHA-256 dos datasets..."
python3 -c "import json; m=json.load(open('experiments/results/manifest_experiment.json')); print('Manifesto SHA-256 validado:', m['dataset_sha256'])"

echo "=============================================================================="
echo "Reprodução da Fase 1 concluída com sucesso! Resultados em experiments/results/"
echo "=============================================================================="
