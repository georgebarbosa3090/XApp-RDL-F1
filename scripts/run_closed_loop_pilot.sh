#!/usr/bin/env bash
# Autor: George Barbosa
# Piloto da malha fechada (docs/16, etapa E7): todas as xApps do cenário lendo KPM, rApp com A1 no laço e
# a RDL (B3) ou nenhuma coordenação (B0), por cenário, em primeiro plano. Exploratório: serve para fixar o
# pré-registro 11, não para conclusões. Retomável: pula execuções já concluídas com SUCCESS.
#
# Uso (Ubuntu do WSL): bash scripts/run_closed_loop_pilot.sh [--scenarios "S9 G2"] [--baselines "B0 B3"] [--seed 16901]
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${VENV:-$HOME/.venvs/xapp-rdl}"
SCENARIOS="G2 G1 S9 S15 S11 S14 S10 S13 S12"; BASELINES="B0 B3"; SEED=16901
while [ $# -gt 0 ]; do
  case "$1" in
    --scenarios) SCENARIOS="$2"; shift 2 ;;
    --baselines) BASELINES="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    *) echo "opção desconhecida: $1" >&2; exit 64 ;;
  esac
done
# shellcheck disable=SC1091
source "$VENV/bin/activate" || { echo "venv não encontrado em $VENV" >&2; exit 3; }
cd "$REPO"
say() { echo "[$(date +%H:%M:%S)] $*"; }
say "piloto da malha fechada: cenários [$SCENARIOS] × baselines [$BASELINES], semente $SEED"
first=1
for sc in $SCENARIOS; do
  for bl in $BASELINES; do
    rid="cl_piloto_${sc}_${bl}_completo_seed${SEED}"
    man="experiments/runs/${rid}/execution_manifest.json"
    if [ -f "$man" ] && grep -q '"run_status": "SUCCESS"' "$man"; then say "pula $rid (concluída)"; continue; fi
    rm -rf "experiments/runs/${rid}"
    extra=(); [ "$first" = 0 ] && extra=(--no-build)
    say "INÍCIO $rid"
    python scripts/closed_loop/orchestrator.py --scenario "$sc" --baseline "$bl" --seed "$SEED" --xapps completo \
      --run-id "$rid" "${extra[@]}" 2>&1 | grep --line-buffered -E 'RDL-ACT|RDL-CTL|fim:|Traceback|Error' | grep --line-buffered -v Prometheus
    say "FIM $rid"
    first=0
  done
done
say "piloto concluído"
# painel de fim de campanha (docs/16 §10.4): conflitos, oscilações, cadeia E2, rede, mensagens, controle e regras
python scripts/closed_loop/resumo_campanha.py --prefix cl_piloto_ --seed "$SEED"
