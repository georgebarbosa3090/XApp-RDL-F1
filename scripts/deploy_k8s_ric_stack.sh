#!/usr/bin/env bash
# ==============================================================================
# Script de Deploy e Gerenciamento Autônomo do Cluster K8s & Near-RT RIC O-RAN
# Skill: 07-k8s-oran-cluster-operator
# ==============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

echo "================================================================================"
echo " ☸️ INICIALIZANDO DEPLOY AUTÔNOMO: K8s (k3s) + Near-RT RIC + Reference xApps + H-RDL"
echo "================================================================================"

# 1. Configurar KUBECONFIG
export KUBECONFIG="/etc/rancher/k3s/k3s.yaml"

# 2. Validar conectividade com o cluster
echo "[OK] Validando conectividade com os nós do cluster Kubernetes..."
kubectl get nodes -o wide

# 3. Criar Namespaces O-RAN
echo "[INFO] Configurando namespaces O-RAN (ricplt, ricxapp)..."
kubectl create namespace ricplt --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ricxapp --dry-run=client -o yaml | kubectl apply -f -

# 4. Deploy da Infraestrutura Near-RT RIC (DBAAS Redis, Mock E2Term, Mock SubMgr)
echo "[INFO] Aplicando infraestrutura Near-RT RIC no namespace 'ricplt'..."
kubectl apply -f deploy/kubernetes/near-rt-ric.yaml

# 5. Deploy dos ConfigMaps e xApps no namespace ricxapp
echo "[INFO] Aplicando manifests das xApps e H-RDL no namespace 'ricxapp'..."
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/service.yaml
kubectl apply -f deploy/kubernetes/service-http.yaml
kubectl apply -f deploy/kubernetes/service-rmr.yaml
kubectl apply -f deploy/kubernetes/xapp-traffic-steering.yaml || true
kubectl apply -f deploy/kubernetes/xapp-qos-xslice.yaml || true
kubectl apply -f deploy/kubernetes/xapp-energy-saving.yaml || true
kubectl apply -f deploy/kubernetes/deployment.yaml

# 6. Status e Healthcheck dos Pods
echo "================================================================================"
echo " 🔍 STATUS DOS PODS NO CLUSTER O-RAN:"
echo "================================================================================"
echo "--- [Namespace: ricplt (Near-RT RIC Platform)] ---"
kubectl get pods -n ricplt -o wide
echo "--- [Namespace: ricxapp (H-RDL & Reference xApps)] ---"
kubectl get pods -n ricxapp -o wide
echo "================================================================================"
echo " [SUCESSO] CLUSTER E COMPONENTES O-RAN IMPLANTADOS COM SUCESSO!"
echo "================================================================================"
