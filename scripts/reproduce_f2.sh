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
# S0–S7: binários da pilha nativa; S8: closed loop só na bancada NORI (scripts/run_nori_scenario.sh)
python3 -c 'import json, pathlib; c = json.load(open("simulations/ns3/conflicts/catalog.json"))["scenarios"]; assert c["S8"]["backend"] == "NORI_NS3"; assert all(pathlib.Path("simulations/ns3/" + c["S%d" % i]["ns3"] + ".cc").exists() for i in range(8))'
test -f scripts/run_nori_scenario.sh

echo "========================================================================"
echo "   REPRODUCAO CONCLUIDA COM 100% DE SUCESSO!"
echo "========================================================================"
