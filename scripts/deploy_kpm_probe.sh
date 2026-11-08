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
# core.autocrlf=true: no checkout do Windows a cópia de trabalho tem CRLF e o índice LF; sem isso,
# o git do WSL veria todos os arquivos como modificados. O pacote sai do commit (LF).
if [ -n "$(git -c core.autocrlf=true status --porcelain -- src simulations/ns3/conflicts/catalog.json)" ]; then
  echo "src/ ou o catálogo têm alterações não commitadas; faça o commit antes de implantar:" >&2
  git -c core.autocrlf=true status --short -- src simulations/ns3/conflicts/catalog.json >&2
  exit 3
fi
COMMIT="$(git rev-parse HEAD)"
BUNDLE="$(mktemp)"
trap 'rm -f "$BUNDLE"' EXIT
git archive "$COMMIT" src simulations/ns3/conflicts/catalog.json | gzip -9 -n | base64 -w0 > "$BUNDLE"
echo "[$(date +%H:%M:%S)] kpm-probe com src/ do commit ${COMMIT} ($(wc -c < "$BUNDLE") B em base64)"
helm upgrade --install kpm-probe deploy/helm/xapp-kpm-probe -n ricxapp \
  --set-file srcBundle="$BUNDLE" --set srcCommit="$COMMIT" "$@"
kubectl -n ricxapp rollout status deploy/kpm-probe --timeout=600s
