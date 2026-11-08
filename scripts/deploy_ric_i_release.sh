#!/usr/bin/env bash
# =============================================================================
# Implanta o Near-RT RIC O-RAN SC Release I (componentes da cadeia E2) no k3s via Helm.
# Roda no terminal do WSL/Ubuntu, em primeiro plano, sem sudo.
#
#   bash scripts/deploy_ric_i_release.sh            # implanta/atualiza
#   bash scripts/deploy_ric_i_release.sh --status   # só mostra o estado
#
# Passos:
#   1. ric-dep (gerrit.o-ran-sc.org, branch i-release) em ~/oran/ric-dep, no commit fixado;
#   2. repositório Helm "local" com o chart ric-common, servido por HTTP em 127.0.0.1:8879
#      (python3 -m http.server; dispensa o chartmuseum/servecm do instalador oficial, que exige sudo);
#   3. helm upgrade --install de dbaas, appmgr, rtmgr, e2mgr, e2term e submgr no namespace ricplt,
#      com deploy/ric/recipe_ric_i_release_e2.yaml e o plugin pós-renderizador do Helm 4
#      deploy/ric/helm-postrenderer (RBAC v1beta1 -> v1; remove Ingress v1beta1, usados só com o Kong,
#      que não é implantado);
#   4. espera os pods ficarem prontos e lista os serviços (E2Term SCTP: service-ricplt-e2term-sctp-alpha).
#
# Variáveis: KUBECONFIG (padrão /etc/rancher/k3s/k3s.yaml), ORAN_DIR (padrão ~/oran)
# =============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RECIPE="$REPO_DIR/deploy/ric/recipe_ric_i_release_e2.yaml"
# Os charts da Release I usam APIs removidas no Kubernetes 1.22 (RBAC e Ingress v1beta1):
# plugin pós-renderizador do Helm 4 em deploy/ric/helm-postrenderer.
POST_RENDERER_DIR="$REPO_DIR/deploy/ric/helm-postrenderer"
POST_RENDERER="ric-k8s122"
ORAN_DIR="${ORAN_DIR:-$HOME/oran}"
RIC_DEP="$ORAN_DIR/ric-dep"
RIC_DEP_COMMIT="0a6f18efda7b20b9d3d9d6bf80a9e0feedddd8e7"   # i-release, "Updating release images for I release"
CHART_REPO="$ORAN_DIR/chartrepo"
PORT=8879
NS=ricplt
COMPONENTS=(dbaas appmgr rtmgr e2mgr e2term submgr)
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"

say() { echo "[$(date +%H:%M:%S)] $*"; }

status() {
  kubectl get pods -n "$NS" -o wide
  kubectl get svc -n "$NS"
  helm list -n "$NS"
}

if [ "${1:-}" = "--status" ]; then status; exit 0; fi

say "Cluster:"; kubectl get nodes

# 1. ric-dep no commit fixado
if [ ! -d "$RIC_DEP/.git" ]; then
  say "Clonando ric-dep (i-release)..."
  mkdir -p "$ORAN_DIR"
  git clone -q -b i-release https://gerrit.o-ran-sc.org/r/ric-plt/ric-dep "$RIC_DEP"
fi
HEAD_COMMIT="$(git -C "$RIC_DEP" rev-parse HEAD)"
if [ "$HEAD_COMMIT" != "$RIC_DEP_COMMIT" ]; then
  say "ERRO: ric-dep em $HEAD_COMMIT, esperado $RIC_DEP_COMMIT"; exit 1
fi
say "ric-dep em $HEAD_COMMIT"

# 2. repositório Helm local com ric-common
mkdir -p "$CHART_REPO/charts"
helm package -d "$CHART_REPO/charts" "$RIC_DEP/ric-common/Common-Template/helm/ric-common" >/dev/null
helm repo index "$CHART_REPO/charts" --url "http://127.0.0.1:$PORT/charts"
if ! curl -fs "http://127.0.0.1:$PORT/charts/index.yaml" >/dev/null; then
  say "Servindo o repositório Helm local em 127.0.0.1:$PORT (log: $CHART_REPO/http.log)"
  nohup python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$CHART_REPO" >"$CHART_REPO/http.log" 2>&1 &
  for _ in $(seq 1 20); do curl -fs "http://127.0.0.1:$PORT/charts/index.yaml" >/dev/null && break; sleep 0.5; done
fi
helm repo add local "http://127.0.0.1:$PORT/charts" --force-update >/dev/null
helm repo update local >/dev/null
helm search repo local/ric-common

# 3. componentes
if ! helm plugin list | awk '{print $1}' | grep -qx "$POST_RENDERER"; then
  say "Instalando o plugin pós-renderizador $POST_RENDERER"
  helm plugin install "$POST_RENDERER_DIR"
fi
kubectl get ns "$NS" >/dev/null 2>&1 || kubectl create ns "$NS"
kubectl get ns ricxapp >/dev/null 2>&1 || kubectl create ns ricxapp
kubectl create configmap -n "$NS" ricplt-recipe --from-file=recipe="$RECIPE" --dry-run=client -o yaml | kubectl apply -f - >/dev/null
for c in "${COMPONENTS[@]}"; do
  say "== $c"
  helm dep up "$RIC_DEP/helm/$c" >/dev/null
  helm upgrade --install "r4-$c" "$RIC_DEP/helm/$c" -n "$NS" -f "$RECIPE" --post-renderer "$POST_RENDERER"
done

# 4. espera
say "Aguardando os pods de $NS ficarem prontos (até 15 min; a primeira vez baixa as imagens)..."
if ! kubectl wait --for=condition=Ready pod --all -n "$NS" --timeout=900s; then
  say "AVISO: nem todos os pods ficaram prontos; estado atual:"
fi
status
grep -E "MemTotal|MemAvailable" /proc/meminfo
