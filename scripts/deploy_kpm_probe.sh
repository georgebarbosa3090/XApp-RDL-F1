#!/usr/bin/env bash
# Implanta a xApp kpm-probe com o src/ do repositório num commit exato (codec E2 v3, ponte H-RDL e
# o próprio H-RDL). O pacote é o "git archive" desse commit, em base64 no ConfigMap; o commit vai
# para o evento start e para cada decisão registrada pela xApp.
# Recusa src/ com alterações não commitadas: o que roda no cluster tem de corresponder a um commit.
# Uso (Ubuntu do WSL): bash scripts/deploy_kpm_probe.sh [args extras do helm, ex.: -f valores.yaml]
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
cd "$REPO"
if [ -n "$(git status --porcelain -- src)" ]; then
  echo "src/ tem alterações não commitadas; faça o commit antes de implantar:" >&2
  git status --short -- src >&2
  exit 3
fi
COMMIT="$(git rev-parse HEAD)"
BUNDLE="$(mktemp)"
trap 'rm -f "$BUNDLE"' EXIT
git archive "$COMMIT" src | gzip -9 -n | base64 -w0 > "$BUNDLE"
echo "[$(date +%H:%M:%S)] kpm-probe com src/ do commit ${COMMIT} ($(wc -c < "$BUNDLE") B em base64)"
helm upgrade --install kpm-probe deploy/helm/xapp-kpm-probe -n ricxapp \
  --set-file srcBundle="$BUNDLE" --set srcCommit="$COMMIT" "$@"
kubectl -n ricxapp rollout status deploy/kpm-probe --timeout=600s
