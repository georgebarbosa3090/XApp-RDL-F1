#!/usr/bin/env bash
# ==============================================================================
# Script de Reprodução Automatizada da Fase 1 (H-RDL) — XApp-RDL-F1
# Autor: George Alexandro F. Barbosa / PPGC-UFPA
# Zero Dados Sintéticos: Execução Factual via FlowMonitor / DiscreteEventRANSimulator
# ==============================================================================

set -euo pipefail

echo "=============================================================================="
echo "Iniciando Pipeline de Reprodução Científica da Fase 1 (H-RDL)"
echo "=============================================================================="

# 1. Validação de Ambiente e Dependências
echo "[1/4] Verificando dependências Python e ambiente virtual..."
python3 -c "import pycrate, pydantic, structlog, prometheus_client; print('Dependências Python OK')"

# 2. Execução da Bateria Experimental e Validação de Proveniência
echo "[2/4] Executando simulação discreta pareada e reprodução de artefatos..."
python3 scripts/reproduce_paper_artifacts.py

# 3. Geração de Figuras Científicas
echo "[3/4] Gerando figuras científicas em alta resolução (300 DPI)..."
python3 scripts/generate_sbrc_figures.py

# 4. Auditoria de Proveniência e Integridade
echo "[4/4] Auditando integridade e conformidade de zero dados sintéticos..."
python3 scripts/verify_provenance_and_integrity.py

echo "=============================================================================="
echo "Reprodução da Fase 1 concluída com sucesso! Resultados em results/ e experiments/results/"
echo "=============================================================================="
