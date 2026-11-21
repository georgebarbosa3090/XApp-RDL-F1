#!/usr/bin/env bash
# Rodada exploratória da proposta P3 do S5 em malha fechada (docs/16 §10.15: UEs em movimento entre as
# células). Para cada baseline, roda o S5 com as xApps completas, sobrepondo ao closed_loop.json a
# mobilidade pelo --sim-arg do orquestrador, e avalia a execução com avaliar_pingpong.py (voltas em até
# 5 s, ações justificadas, perdas depois de handover) e avaliar_mobilidade.py (perdas e reconexões por grupo).
# Uso (Ubuntu do WSL): bash scripts/closed_loop/rodar_s5_p3.sh [--baselines "B0 B3 N12"] [--seed 16907]
#                       [--speed 5] [--fraction 0.5] [--prefix cl_p3v5]
set -u
BLS="B0 B3"; SEED=16907; SPEED=5; FRAC=0.5; PREFIX=""
while [ $# -gt 0 ]; do
  case "$1" in
    --baselines) BLS="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --speed) SPEED="$2"; shift 2 ;;
    --fraction) FRAC="$2"; shift 2 ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    *) echo "opção desconhecida: $1" >&2; exit 2 ;;
  esac
done
PREFIX="${PREFIX:-cl_p3v${SPEED}}"
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
for bl in $BLS; do
  rid="${PREFIX}_S5_${bl}_completo_seed${SEED}"
  man="experiments/runs/${rid}/execution_manifest.json"
  if [ -f "$man" ] && grep -q '"run_status": "SUCCESS"' "$man"; then say "pula $rid (concluída)"; continue; fi
  rm -rf "experiments/runs/${rid}"
  say "INÍCIO $rid (ueSpeed=${SPEED} m/s, fração ${FRAC})"
  python scripts/closed_loop/orchestrator.py --scenario S5 --baseline "$bl" --seed "$SEED" --xapps completo \
    --run-id "$rid" --no-build --sim-arg="--ueSpeed=${SPEED}" --sim-arg="--ueMovingFraction=${FRAC}" 2>&1 \
    | grep --line-buffered -E 'RDL-ACT|RDL-CTL|RDL-MOB|fim:|Traceback|Error' | grep --line-buffered -v Prometheus
  say "FIM $rid"
  python scripts/closed_loop/avaliar_pingpong.py "experiments/runs/${rid}"
  python scripts/closed_loop/avaliar_mobilidade.py "experiments/runs/${rid}"
  # N12 (RDL-N1 + RDL-N2): roteamento por nível e reserva, pelo script da Fase 2 (RDL_F2_ROOT, padrão ao lado)
  F2="${RDL_F2_ROOT:-$REPO/../XApp-RDL-F2}"
  if [ "$bl" = "N12" ] && [ -f "$F2/experiments/closed_loop/resumo_n12.py" ]; then
    python "$F2/experiments/closed_loop/resumo_n12.py" "experiments/runs/${rid}"
  fi
done
say "rodada P3 concluída"
