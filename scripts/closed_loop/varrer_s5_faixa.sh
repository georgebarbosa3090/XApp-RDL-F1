#!/usr/bin/env bash
# Varredura exploratória da faixa dos UEs no S5 em malha fechada (docs/16 §10.14, proposta P1: duas células
# carregadas). Para cada limite superior de x, roda o S5 com as xApps completas e um baseline, sobrepondo
# --ueBoxXmax ao closed_loop.json pelo --sim-arg do orquestrador (o último valor vale no CommandLine do ns-3),
# e gera um painel por faixa (prefixo cl_p1x<xmax>).
# Uso (Ubuntu do WSL): bash scripts/closed_loop/varrer_s5_faixa.sh [--xmax "70 75 80 85"] [--baseline B0] [--seed 16907]
#   [--prefix cl_p1x]  (o run id fica <prefixo><xmax>_S5_<baseline>_completo_seed<semente>)
set -u
XMAX="70 75 80 85"; BL="B0"; SEED=16907; PREFIX="cl_p1x"
while [ $# -gt 0 ]; do
  case "$1" in
    --xmax) XMAX="$2"; shift 2 ;;
    --baseline) BL="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    *) echo "opção desconhecida: $1" >&2; exit 2 ;;
  esac
done
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
VENV="${VENV:-$HOME/.venvs/xapp-rdl}"
# shellcheck disable=SC1091
source "$VENV/bin/activate" || { echo "venv não encontrado em $VENV" >&2; exit 3; }
cd "$REPO"
say() { echo "[$(date +%H:%M:%S)] $*"; }
NS3_DIR="${NS3_DIR:-$HOME/ns3-oran-workspace/ns-3-oran}"
cp -f simulations/ns3/*.h "$NS3_DIR/scratch/"
cp -f simulations/ns3/scenario_rdl_temporal_pingpong.cc "$NS3_DIR/scratch/"
say "compila scenario_rdl_temporal_pingpong"
(cd "$NS3_DIR" && ./ns3 build scratch/scenario_rdl_temporal_pingpong 2>&1 | tail -2) || { say "falha ao compilar"; exit 70; }
for x in $XMAX; do
  pre="${PREFIX}${x}"
  rid="${pre}_S5_${BL}_completo_seed${SEED}"
  man="experiments/runs/${rid}/execution_manifest.json"
  if [ -f "$man" ] && grep -q '"run_status": "SUCCESS"' "$man"; then say "pula $rid (concluída)"; continue; fi
  rm -rf "experiments/runs/${rid}"
  say "INÍCIO $rid (ueBoxXmax=$x)"
  python scripts/closed_loop/orchestrator.py --scenario S5 --baseline "$BL" --seed "$SEED" --xapps completo \
    --run-id "$rid" --no-build --sim-arg="--ueBoxXmax=${x}" 2>&1 \
    | grep --line-buffered -E 'RDL-ACT|RDL-CTL|fim:|Traceback|Error|recompile|desatualizado' | grep --line-buffered -v Prometheus
  say "FIM $rid"
  python scripts/closed_loop/resumo_campanha.py --prefix "${pre}_" --seed "$SEED" | tail -4
done
say "varredura concluída"
