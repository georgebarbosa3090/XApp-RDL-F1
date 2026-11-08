#!/usr/bin/env bash
# Aba Execução NORI: acompanha a saída da execução mais recente no pod do NORI (vazão por fatia,
# [RDL-UE], E2 Setup, Subscription e recebimento do Control). Troca sozinha para a próxima execução.
# Uso: bash scripts/observe/nori_live.sh [filtro-regex]     (padrão: linhas relevantes do cenário)
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
FILTER="${1:-Slice [01]|\[t = |\[RDL-UE\]|E2SimMod|RICcontrol|SETUP|ubscription|===}"
while true; do
  RUN=$(kubectl -n ricsim exec deploy/nori-ns3 -- sh -c 'ls -td /workspace/runs/*/ 2>/dev/null | head -1' | tr -d '\r')
  [ -n "$RUN" ] || { sleep 5; continue; }
  echo "===== acompanhando ${RUN} ====="
  kubectl -n ricsim exec deploy/nori-ns3 -- sh -c "
    tail -n +1 -F ${RUN}logs/stdout.log 2>/dev/null & T=\$!
    while [ \"\$(ls -td /workspace/runs/*/ | head -1)\" = '${RUN}' ]; do sleep 3; done; kill \$T" \
    | grep --line-buffered -a -E "$FILTER"
done
