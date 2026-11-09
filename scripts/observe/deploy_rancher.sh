#!/usr/bin/env bash
# Rancher (opcional) no k3s da bancada, via Helm: cert-manager v1.14.7 + Rancher 2.8.5 (o chart 2.8.x aceita
# Kubernetes < 1.29; a bancada roda k3s v1.26). Uma réplica, com limite de memória. Só prossegue se o WSL tiver
# memória livre suficiente, porque a bancada (RIC + NORI) divide os 5 GB do WSL.
# Uso (Ubuntu do WSL):
#   bash scripts/observe/deploy_rancher.sh              # instala/atualiza
#   bash scripts/observe/deploy_rancher.sh --uninstall  # remove Rancher e cert-manager
# Acesso: kubectl -n cattle-system port-forward svc/rancher 8443:443   ->  https://localhost:8443
#   senha inicial: kubectl -n cattle-system get secret bootstrap-secret -o jsonpath='{.data.bootstrapPassword}' | base64 -d
set -euo pipefail
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
CM_VERSION=v1.14.7
RANCHER_VERSION=2.8.5
# Em 2026-11-09, com 2,9 GB livres, a máquina virtual do WSL reiniciou durante o download e a descompactação da
# imagem do Rancher (~1,4 GB) e derrubou a bancada (docs/05, achado 50). O padrão exige 4,5 GB livres, o que um WSL
# de 5 GB com RIC e NORI não tem: rode o Rancher fora dele (outra máquina ou WSL com >= 8 GB) e importe o cluster.
MIN_FREE_MB="${MIN_FREE_MB:-4500}"
say() { echo "[$(date +%H:%M:%S)] $*"; }
avail() { awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo; }

if [ "${1:-}" = "--uninstall" ]; then
  helm -n cattle-system uninstall rancher 2>/dev/null || true
  helm -n cert-manager uninstall cert-manager 2>/dev/null || true
  say "Rancher e cert-manager removidos (namespaces cattle-* podem levar alguns minutos para sumir); livre: $(avail) MB"
  exit 0
fi

[ "$(avail)" -ge "$MIN_FREE_MB" ] || { say "só $(avail) MB livres (< $MIN_FREE_MB MB): Rancher não instalado para não afetar a bancada"; exit 3; }
say "memória livre antes: $(avail) MB"
helm repo add jetstack https://charts.jetstack.io >/dev/null 2>&1 || true
helm repo add rancher-stable https://releases.rancher.com/server-charts/stable >/dev/null 2>&1 || true
helm repo update jetstack rancher-stable >/dev/null

say "cert-manager $CM_VERSION"
helm upgrade --install cert-manager jetstack/cert-manager -n cert-manager --create-namespace --version "$CM_VERSION" \
  --set installCRDs=true --set resources.limits.memory=128Mi --set webhook.resources.limits.memory=64Mi \
  --set cainjector.resources.limits.memory=128Mi --wait --timeout 10m

say "Rancher $RANCHER_VERSION (uma réplica)"
kubectl create namespace cattle-system --dry-run=client -o yaml | kubectl apply -f - >/dev/null
if ! kubectl -n cattle-system get secret bootstrap-secret >/dev/null 2>&1; then
  BOOT="$(head -c 18 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 20)"
else
  BOOT="$(kubectl -n cattle-system get secret bootstrap-secret -o jsonpath='{.data.bootstrapPassword}' | base64 -d)"
fi
helm upgrade --install rancher rancher-stable/rancher -n cattle-system --version "$RANCHER_VERSION" \
  --set hostname=rancher.localhost --set replicas=1 --set bootstrapPassword="$BOOT" \
  --set resources.requests.memory=512Mi --set resources.limits.memory=1280Mi \
  --set global.cattle.psp.enabled=false --set ingress.tls.source=rancher --wait --timeout 20m
kubectl -n cattle-system rollout status deploy/rancher --timeout=15m
say "Rancher pronto; memória livre agora: $(avail) MB"
say "acesso: kubectl -n cattle-system port-forward svc/rancher 8443:443  ->  https://localhost:8443 (certificado autoassinado)"
say "senha inicial: kubectl -n cattle-system get secret bootstrap-secret -o jsonpath='{.data.bootstrapPassword}' | base64 -d"
