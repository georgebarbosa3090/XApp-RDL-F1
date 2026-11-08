#!/usr/bin/env bash
# Aba xApp: subscrição, KPM decodificado por UE (fatia, PRBs), decisão do H-RDL, RIC Control e ACK.
# Uso: bash scripts/observe/xapp_live.sh [--indications]
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
while true; do   # reconecta se o pod da xApp for trocado
  kubectl -n ricxapp logs -f deploy/kpm-probe --since=2s 2>/dev/null | python3 -u "$REPO/scripts/observe/format_xapp_events.py" "$@"
  sleep 3
done
