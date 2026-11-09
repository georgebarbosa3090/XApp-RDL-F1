#!/usr/bin/env bash
# Campanha dos cenários de conflito na bancada NORI (E2 real), ao vivo, com certificação no fim:
#   implanta a xApp kpm-probe em modo catalog (src/ do commit atual), roda cada cenário × semente com
#   scripts/run_nori_scenario.sh e, ao final, roda o certificador e o resumo da campanha.
#
# Uso (Ubuntu do WSL):
#   bash scripts/run_nori_campaign.sh                                   # S0–S8 × 1001–1005 (45 execuções)
#   bash scripts/run_nori_campaign.sh --scenarios "S1 S7" --seeds "1001 1002"
#   bash scripts/run_nori_campaign.sh --no-deploy                       # reaproveita a xApp já implantada
#   bash scripts/run_nori_campaign.sh --tag _bw50 --args "--bandwidth=50e6"   # condição extra (run_id nori_<S>_B3_bw50_seed<N>)
# Execuções já existentes no repositório são puladas (retomável). Cada execução leva ~3 min.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
SCENARIOS="S0 S1 S2 S3 S4 S5 S6 S7 S8"; SEEDS="1001 1002 1003 1004 1005"; DEPLOY=1; TAG=""; ARGS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --scenarios) SCENARIOS="$2"; shift 2 ;;
    --seeds) SEEDS="$2"; shift 2 ;;
    --no-deploy) DEPLOY=0; shift ;;
    --tag) TAG="$2"; shift 2 ;;
    --args) ARGS="$2"; shift 2 ;;
    *) echo "opção desconhecida: $1" >&2; exit 64 ;;
  esac
done
say() { echo "[$(date +%H:%M:%S)] $*"; }
PY="${PYTHON:-$HOME/.venvs/xapp-rdl/bin/python}"; [ -x "$PY" ] || PY=python3

if [ "$DEPLOY" = 1 ]; then
  say "implantando a xApp kpm-probe em modo catalog"
  bash "$REPO/scripts/deploy_kpm_probe.sh" --set rc.decision=catalog --set rc.afterIndications=12 | tail -1 || exit 3
fi
total=0; for s in $SEEDS; do for c in $SCENARIOS; do total=$((total + 1)); done; done
n=0
for seed in $SEEDS; do                 # por semente: cada semente concluída forma um conjunto completo
  for sc in $SCENARIOS; do
    n=$((n + 1))
    say "################ [$n/$total] $sc semente $seed ################"
    RUN_TAG="$TAG" SCENARIO_ARGS="$ARGS" bash "$REPO/scripts/run_nori_scenario.sh" "$sc" "$seed" || say "falha em $sc/$seed (registrada; seguindo)"
  done
done
say "certificação e resumo da campanha NORI"
( cd "$REPO" && "$PY" scripts/certification/certify_chain.py | tail -9 )
( cd "$REPO" && "$PY" scripts/certification/nori_campaign_summary.py --seeds "$SEEDS" --tag "$TAG" )
