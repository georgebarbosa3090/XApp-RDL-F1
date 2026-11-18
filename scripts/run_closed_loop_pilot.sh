#!/usr/bin/env bash
# Autor: George Barbosa
# Piloto da malha fechada (docs/16, etapa E7): todas as xApps do cenário lendo KPM, rApp com A1 no laço e
# a RDL (B3) ou nenhuma coordenação (B0), por cenário, em primeiro plano. Exploratório: serve para fixar o
# pré-registro 11, não para conclusões. Retomável: pula execuções já concluídas com SUCCESS.
#
# Uso (Ubuntu do WSL): bash scripts/run_closed_loop_pilot.sh [--scenarios "S9 G2"] [--baselines "B0 B3"] [--seed 16901]
#   [--repeat 2]: roda cada execução N vezes com a mesma semente (teste de determinismo do pré-registro 11, item 5);
#   a k-ésima repetição (k >= 2) ganha o sufixo _rep<k> no run_id. Compare com scripts/closed_loop/comparar_determinismo.py.
#   [--prefix cl_s0s7]: prefixo do run_id e do painel (padrão cl_piloto). Antes da primeira execução, compila em
#   sequência o programa ns-3 de cada cenário (S0–S7 usam programas diferentes; G* e S9–S15, o multicell);
#   depois, todas as execuções usam --no-build.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${VENV:-$HOME/.venvs/xapp-rdl}"
SCENARIOS="G2 G1 S9 S15 S11 S14 S10 S13 S12"; BASELINES="B0 B3"; SEED=16901; REPEAT=1; PREFIX=cl_piloto
while [ $# -gt 0 ]; do
  case "$1" in
    --scenarios) SCENARIOS="$2"; shift 2 ;;
    --baselines) BASELINES="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --repeat) REPEAT="$2"; shift 2 ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    *) echo "opção desconhecida: $1" >&2; exit 64 ;;
  esac
done
# shellcheck disable=SC1091
source "$VENV/bin/activate" || { echo "venv não encontrado em $VENV" >&2; exit 3; }
cd "$REPO"
say() { echo "[$(date +%H:%M:%S)] $*"; }
say "malha fechada ($PREFIX): cenários [$SCENARIOS] × baselines [$BASELINES], semente $SEED, $REPEAT repetição(ões)"
# compila uma vez, em sequência (memória do WSL), o programa ns-3 de cada cenário
NS3_DIR="${NS3_DIR:-$HOME/ns3-oran-workspace/ns-3-oran}"
progs=$(python -c "import json,sys; c=json.load(open('simulations/ns3/conflicts/catalog.json',encoding='utf-8'))['scenarios']; print(' '.join(sorted({c[s]['ns3'] for s in sys.argv[1:]})))" $SCENARIOS) || exit 3
cp -f simulations/ns3/*.h "$NS3_DIR/scratch/"
for prog in $progs; do
  cp -f "simulations/ns3/${prog}.cc" "$NS3_DIR/scratch/"
  say "compila $prog"
  (cd "$NS3_DIR" && ./ns3 build "scratch/${prog}" 2>&1 | tail -2) || { say "falha ao compilar $prog"; exit 70; }
done
for k in $(seq 1 "$REPEAT"); do
for sc in $SCENARIOS; do
  for bl in $BASELINES; do
    tag=""; [ "$k" -ge 2 ] && tag="_rep${k}"
    rid="${PREFIX}_${sc}_${bl}_completo${tag}_seed${SEED}"
    man="experiments/runs/${rid}/execution_manifest.json"
    if [ -f "$man" ] && grep -q '"run_status": "SUCCESS"' "$man"; then say "pula $rid (concluída)"; continue; fi
    rm -rf "experiments/runs/${rid}"
    extra=(--no-build)
    say "INÍCIO $rid"
    python scripts/closed_loop/orchestrator.py --scenario "$sc" --baseline "$bl" --seed "$SEED" --xapps completo \
      --run-id "$rid" "${extra[@]}" 2>&1 | grep --line-buffered -E 'RDL-ACT|RDL-CTL|fim:|Traceback|Error' | grep --line-buffered -v Prometheus
    say "FIM $rid"
  done
done
done
say "rodada concluída ($PREFIX)"
# painel de fim de campanha (docs/16 §10.4): conflitos, oscilações, cadeia E2, rede, mensagens, controle e regras
python scripts/closed_loop/resumo_campanha.py --prefix "${PREFIX}_" --seed "$SEED"
