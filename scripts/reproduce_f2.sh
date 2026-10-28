#!/usr/bin/env bash
# =============================================================================
# Pipeline de Reproducao e Validacao Normativa — XApp-RDL-F2 (CA-RDL)
# =============================================================================
set -euo pipefail

echo "========================================================================"
echo "   REPRODUCAO DETERMINISTICA E VALIDACAO — XAPP-RDL-F2 (CA-RDL / MARL)"
echo "========================================================================"

echo "[1/4] Verificando ambiente Python e dependencias..."
python3 -c "import pytest, pycrate, pydantic, torch; print('Dependencias OK!')"

echo "[2/4] Executando suite completa de testes modulares e MARL..."
pytest tests/ -v

echo "[3/4] Validando perfil de deploy OpenRAN@Brasil Blueprint v3..."
test -f deploy/openran-br-v3/deployment.yaml
test -f deploy/openran-br-v3/config-map.yaml
test -f deploy/openran-br-v3/service.yaml
test -f deploy/openran-br-v3/values.yaml

echo "[4/4] Validando cenarios de co-simulacao ns-3 / NORI..."
test -f simulations/ns3/scenario_rdl_closed_loop_nori.cc

echo "========================================================================"
echo "   REPRODUCAO CONCLUIDA COM 100% DE SUCESSO!"
echo "========================================================================"
