#!/usr/bin/env bash
# Implanta InfluxDB 2 e Grafana (Helm, versões fixadas) no namespace monitoring, com o dashboard das simulações.
# Uso (Ubuntu do WSL): bash scripts/observe/deploy_observability.sh
#   Depois: bash scripts/observe/influx_live.sh   (alimentador: NORI, xApp e campanhas -> InfluxDB)
#           bash scripts/observe/grafana.sh       (Grafana em http://localhost:3000, leitura anônima)
#   Remover: helm -n monitoring uninstall grafana influxdb2
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
NS=monitoring
INFLUX_CHART_VERSION=2.1.2     # InfluxDB 2.7.4
GRAFANA_CHART_VERSION=10.5.15  # Grafana 12.3.1
V="$REPO/deploy/helm/observability"
say() { echo "[$(date +%H:%M:%S)] $*"; }

helm repo add influxdata https://helm.influxdata.com/ >/dev/null 2>&1 || true
helm repo add grafana https://grafana.github.io/helm-charts >/dev/null 2>&1 || true
helm repo update influxdata grafana >/dev/null
kubectl create namespace "$NS" --dry-run=client -o yaml | kubectl apply -f - >/dev/null

# Os charts são baixados uma vez para um cache local, com novas tentativas (o do InfluxDB vem de um release no
# GitHub, que às vezes estoura o tempo), e instalados a partir do .tgz.
CACHE="${HOME}/.cache/xapp-rdl/charts"; mkdir -p "$CACHE"
fetch() {   # fetch <repo/chart> <versão> -> caminho do .tgz
  local ref="$1" ver="$2" tgz="$CACHE/$(basename "$1")-$2.tgz"
  for i in 1 2 3 4 5; do
    [ -s "$tgz" ] && { echo "$tgz"; return 0; }
    helm pull "$ref" --version "$ver" -d "$CACHE" >/dev/null 2>&1 || { echo "  download de $ref $ver falhou (tentativa $i); repetindo" >&2; sleep 5; }
  done
  [ -s "$tgz" ] && echo "$tgz" || { echo "não consegui baixar $ref $ver" >&2; return 1; }
}

say "InfluxDB 2 (chart influxdata/influxdb2 $INFLUX_CHART_VERSION)"
helm upgrade --install influxdb2 "$(fetch influxdata/influxdb2 "$INFLUX_CHART_VERSION")" -n "$NS" -f "$V/values-influxdb2.yaml"
kubectl -n "$NS" rollout status statefulset/influxdb2 --timeout=300s

say "dashboard das simulações (ConfigMap grafana-dash-rdl)"
kubectl -n "$NS" create configmap grafana-dash-rdl --from-file="$V/dashboards/rdl_simulacoes.json" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null

say "Grafana (chart grafana/grafana $GRAFANA_CHART_VERSION)"
helm upgrade --install grafana "$(fetch grafana/grafana "$GRAFANA_CHART_VERSION")" -n "$NS" -f "$V/values-grafana.yaml"
kubectl -n "$NS" rollout restart deploy/grafana >/dev/null   # relê o dashboard se o ConfigMap mudou
kubectl -n "$NS" rollout status deploy/grafana --timeout=300s
kubectl -n "$NS" get pods
say "pronto: bash scripts/observe/influx_live.sh  e  bash scripts/observe/grafana.sh"
