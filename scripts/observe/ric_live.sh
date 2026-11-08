#!/usr/bin/env bash
# Aba RIC: logs filtrados do E2Term, E2Mgr, SubMgr e RtMgr (mensageria RMR, rotas, subscrições),
# cada linha com o componente de origem.
# Uso: bash scripts/observe/ric_live.sh [componente...]    (padrão: e2term e2mgr submgr rtmgr)
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
declare -A DEPLOY=([e2term]=deployment-ricplt-e2term-alpha [e2mgr]=deployment-ricplt-e2mgr
                   [submgr]=deployment-ricplt-submgr [rtmgr]=deployment-ricplt-rtmgr [appmgr]=deployment-ricplt-appmgr)
declare -A FILTER=(
  [e2term]='E2_SETUP|SETUP|RIC_INDICATION|RIC_CONTROL|RIC_SUB|RAN name|sctp|SCTP|Connected|disconnect'
  [e2mgr]='E2SetupRequest|E2_SETUP|SETUP|CONNECTED|DISCONNECTED|nodeb|E2 node|setup'
  [submgr]='SubReq|SubResp|SubDel|RIC_SUB|Subscription|subscription|REST|E2T'
  [rtmgr]='Update Routes|Push policy|subscription|xapp|Endpoint|endpoint|ERROR')
COMPS=("${@:-e2term e2mgr submgr rtmgr}"); [ $# -gt 0 ] || COMPS=(e2term e2mgr submgr rtmgr)
for c in "${COMPS[@]}"; do
  ( while true; do
      kubectl -n ricplt logs -f "deploy/${DEPLOY[$c]}" --since=5s 2>/dev/null \
        | grep --line-buffered -a -v -E "Client -> E2 Manager|E2 Manager -> Client|fileReadAll" \
        | grep --line-buffered -a -E "${FILTER[$c]}" | cut -c1-220 | sed -u "s/^/[$c] /"
      sleep 3
    done ) &
done
trap 'kill $(jobs -p) 2>/dev/null' EXIT INT TERM
wait
