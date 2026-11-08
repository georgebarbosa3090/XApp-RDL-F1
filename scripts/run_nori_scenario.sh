#!/usr/bin/env bash
# Executa UM cenário de conflito do catálogo (S0–S8) na bancada NORI, ao vivo, com a cadeia E2 real:
#   1. escreve o cenário no volume da xApp kpm-probe (modo catalog) e espera ela ficar pronta;
#   2. roda nori-rc-slicing-flowmon no pod do NORI, com a saída do cenário no terminal
#      (vazão por fatia, [RDL-UE], E2 Setup, Subscription e recebimento do Control);
#   3. traz a evidência, recorta os eventos da xApp, disseca o E2 (tshark) e mede o efeito na RAN.
#
# Uso (Ubuntu do WSL, a partir da raiz do repositório ou de qualquer lugar):
#   bash scripts/run_nori_scenario.sh S1 1001
# Pré-requisitos: RIC Release I, bancada NORI e xApp kpm-probe em modo catalog
#   (bash scripts/deploy_kpm_probe.sh --set rc.decision=catalog).
# Variáveis: SIM_TIME (40), TRAFFIC_RATE (300Mb/s), E2_PERIOD (1), KUBECONFIG.
set -uo pipefail
[ $# -eq 2 ] || { echo "Uso: $0 <S0..S8> <semente>" >&2; exit 64; }
SCENARIO="$1"; SEED="$2"
[[ "$SCENARIO" =~ ^S[0-8]$ ]] || { echo "cenário inválido: $SCENARIO (S0..S8)" >&2; exit 64; }
[[ "$SEED" =~ ^[0-9]+$ ]] || { echo "semente inválida: $SEED" >&2; exit 64; }
REPO="$(cd "$(dirname "$0")/.." && pwd)"
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
RUN_ID="nori_${SCENARIO}_B3_seed${SEED}"
COMMIT="$(cd "$REPO" && git rev-parse HEAD)"
say() { echo "[$(date +%H:%M:%S)] $*"; }

# xApp pronta = um único pod 1/1 Running e, no arquivo de eventos persistente (o kubectl logs é
# rotacionado), o último "start" em modo catalog seguido de "rmr_ready".
ready() {
  local pods ev
  pods=$(kubectl -n ricxapp get pods -l app.kubernetes.io/name=kpm-probe --no-headers 2>/dev/null)
  [ "$(echo "$pods" | grep -c .)" = 1 ] && echo "$pods" | grep -q " 1/1 .*Running" || return 1
  ev=$(kubectl -n ricxapp exec deploy/kpm-probe -- sh -c 'grep -E "event\": \"(start|rmr_ready)\"" /data/logs/kpm_probe_events.jsonl | tail -2' 2>/dev/null)
  echo "$ev" | head -1 | grep -q '"rc_decision": "catalog"' && echo "$ev" | tail -1 | grep -q '"event": "rmr_ready"'
}

if [ -e "$REPO/experiments/runs/$RUN_ID" ]; then
  say "$RUN_ID já existe no repositório: pulando (não sobrescrevo evidência)"; exit 0
fi
for i in $(seq 1 120); do ready && break; sleep 5; done
ready || { say "xApp kpm-probe não está pronta em modo catalog (pod único)"; exit 3; }
kubectl -n ricxapp exec deploy/kpm-probe -- sh -c "echo $SCENARIO > /data/rdl_scenario"
say "cenário $SCENARIO gravado na xApp; xApp com src/ de $(kubectl -n ricxapp exec deploy/kpm-probe -- sh -c 'grep "event\": \"start\"" /data/logs/kpm_probe_events.jsonl | tail -1' | grep -o '"src_commit": "[0-9a-f]\{7\}' | cut -d'"' -f4) (repositório em ${COMMIT:0:7})"
say "=== $RUN_ID: $SCENARIO na bancada NORI, semente $SEED (saída ao vivo) ==="
kubectl -n ricsim exec -it deploy/nori-ns3 -- env RDL_SCENARIO="$SCENARIO" RDL_BASELINE=B3 \
  bash /scripts/run.sh nori-rc-slicing-flowmon "$RUN_ID" --seed "$SEED" -- \
  --simTime="${SIM_TIME:-40}" --ns3::E2Interface::E2Periodicity="${E2_PERIOD:-1}" --trafficRate="${TRAFFIC_RATE:-300Mb/s}" \
  | grep --line-buffered -E "Slice [01]|\[t = |\[RDL-UE\]|E2Term|SETUP|Subscription|subscription|RICcontrol|===|E2SimMod"
bash "$REPO/scripts/collect_nori_run.sh" "$RUN_ID" 2>&1 | grep -E "hashes|Cadeia|tshark \(|xApp:|Control:|Efeito|SST|ERRO"
sleep 15   # o E2Mgr marca o nó como desconectado e a xApp apaga a subscrição antes da próxima execução
