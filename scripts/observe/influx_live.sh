#!/usr/bin/env bash
# Aba InfluxDB: alimenta o InfluxDB (namespace monitoring) com a execução NORI corrente, os eventos da xApp e os
# vereditos das campanhas, para o Grafana. Abre um port-forward local para o InfluxDB e lê o token do Secret.
# Uso (Ubuntu do WSL): bash scripts/observe/influx_live.sh [--once] [--no-campaign]
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
PORT="${INFLUX_LOCAL_PORT:-18086}"
kubectl -n monitoring port-forward svc/influxdb2 "$PORT:80" >/dev/null 2>&1 &
PF=$!
trap 'kill $PF 2>/dev/null' EXIT INT TERM
for i in $(seq 1 30); do (echo > /dev/tcp/127.0.0.1/"$PORT") 2>/dev/null && break; sleep 1; done
export INFLUX_URL="http://127.0.0.1:$PORT"
export INFLUX_TOKEN="$(kubectl -n monitoring get secret influxdb2-auth -o jsonpath='{.data.admin-token}' | base64 -d)"
python3 -u "$REPO/scripts/observe/influx_feeder.py" "$@"
