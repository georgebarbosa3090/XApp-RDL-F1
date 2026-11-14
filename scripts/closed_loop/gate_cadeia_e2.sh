#!/usr/bin/env bash
# Autor: George Barbosa
# Gate do ciclo NORI S8 na malha fechada (docs/16 §10.1): roda cenário:baseline com a cadeia E2 ligada e
# verifica cada execução. Uso (Ubuntu do WSL): bash scripts/closed_loop/gate_cadeia_e2.sh 16903 G2:B3 S15:B0
set -uo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "${VENV:-$HOME/.venvs/xapp-rdl}/bin/activate"
cd "$REPO"
SEED="$1"; shift
runs=()
for sb in "$@"; do
  s="${sb%:*}"; b="${sb#*:}"; rid="cl_e2chain_${s}_${b}_seed${SEED}"
  echo "[$(date +%H:%M:%S)] INÍCIO $rid"
  python scripts/closed_loop/orchestrator.py --scenario "$s" --baseline "$b" --seed "$SEED" --xapps completo \
    --run-id "$rid" 2>&1 | grep --line-buffered -E 'RDL-E2|RDL-CTL|fim:|Traceback|Error' | grep --line-buffered -v Prometheus
  runs+=("experiments/runs/$rid")
done
python scripts/closed_loop/verificar_cadeia.py "${runs[@]}"
python scripts/closed_loop/resumo_campanha.py --runs "${runs[@]}" --title "Gate da cadeia E2 (semente $SEED)" \
  --out "reports/avaliacao/gate_cadeia_e2_seed${SEED}"
