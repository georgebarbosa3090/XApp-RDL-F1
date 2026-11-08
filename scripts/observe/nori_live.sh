#!/usr/bin/env bash
# Aba Execução NORI: acompanha a execução NORI em andamento no pod (vazão por fatia, [RDL-UE],
# E2 Setup, Subscription e recebimento do Control) e passa sozinha para a próxima execução.
# Uso: bash scripts/observe/nori_live.sh [filtro-regex]     (padrão: linhas relevantes do cenário)
#      FOLLOW_LAST=1 bash scripts/observe/nori_live.sh      (mostra também a última execução já encerrada)
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
FILTER="${1:-Slice [01]|\[t = |\[RDL-UE\]|E2SimMod|RICcontrol|SETUP|ubscription|^=== \[}"
latest() { kubectl -n ricsim exec deploy/nori-ns3 -- sh -c 'ls -td /workspace/runs/*/ 2>/dev/null | head -1' | tr -d '\r'; }
SKIP=""
if [ -z "${FOLLOW_LAST:-}" ]; then
  SKIP="$(latest)"
  if [ -n "$SKIP" ] && ! kubectl -n ricsim exec deploy/nori-ns3 -- test -f "${SKIP}hashes.sha256" 2>/dev/null; then
    SKIP=""   # a última execução ainda está em andamento: acompanha ela
  fi
fi
[ -n "$SKIP" ] && echo "aguardando a próxima execução NORI (a última, ${SKIP}, já terminou)..."
while true; do
  RUN="$(latest)"
  if [ -z "$RUN" ] || [ "$RUN" = "$SKIP" ]; then sleep 3; continue; fi
  SKIP=""
  echo "===== acompanhando ${RUN} ====="
  kubectl -n ricsim exec deploy/nori-ns3 -- sh -c "
    tail -n +1 -F ${RUN}logs/stdout.log 2>/dev/null & T=\$!
    while [ \"\$(ls -td /workspace/runs/*/ | head -1)\" = '${RUN}' ] && [ ! -f '${RUN}hashes.sha256' ]; do sleep 2; done
    sleep 2; kill \$T" | grep --line-buffered -a -E "$FILTER"
  SKIP="$RUN"
  echo "===== ${RUN} encerrada; aguardando a próxima ====="
done
