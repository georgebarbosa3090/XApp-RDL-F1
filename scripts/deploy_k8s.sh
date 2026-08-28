#!/bin/bash
# ==============================================================================
# Pipeline de Deploy Kubernetes (K8s Puro / Kustomize): Near-RT RIC + 3 Reference xApps
# ==============================================================================
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

IMAGE_NAME="iqos-xapp-rdl"
IMAGE_TAG="1.1.0"
NAMESPACE_RIC="ricplt"
NAMESPACE_XAPP="ricxapp"

DEPLOY_RDL=true
for arg in "$@"; do
    case $arg in
        --baseline|--no-rdl)
            DEPLOY_RDL=false
            shift
            ;;
        --with-rdl)
            DEPLOY_RDL=true
            shift
            ;;
    esac
done

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}   Pipeline de Deploy K8s Puro: Near-RT RIC + 3 Reference xApps       ${NC}"
if [ "$DEPLOY_RDL" = true ]; then
    echo -e "${CYAN}   [Modo Governança: Near-RT RIC + 3 Reference xApps + xApp RDL]      ${NC}"
else
    echo -e "${YELLOW}   [Modo Baseline: Near-RT RIC + 3 Reference xApps (SEM RDL)]         ${NC}"
fi
echo -e "${BLUE}======================================================================${NC}"

# 1. Build da Imagem Docker Unificada
echo -e "\n${YELLOW}[1/5] Construindo imagem Docker (${IMAGE_NAME}:${IMAGE_TAG})...${NC}"
docker build --file docker/Dockerfile --tag ${IMAGE_NAME}:${IMAGE_TAG} .

# 2. Auto-Importação para nós k3d (se aplicável)
echo -e "\n${YELLOW}[2/5] Verificando nós do cluster para importação da imagem...${NC}"
K3D_NODES=$(docker ps --format '{{.Names}}' | grep -E "k3d-.*-(server-[0-9]|agent-[0-9])" || true)
if [ -n "$K3D_NODES" ]; then
    for node in $K3D_NODES; do
        echo " -> Carregando imagem no nó containerd: $node"
        docker save ${IMAGE_NAME}:${IMAGE_TAG} | docker exec -i $node ctr images import - || true
    done
fi

# 3. Aplicar Namespaces e Plataforma Near-RT RIC (ricplt)
echo -e "\n${YELLOW}[3/5] Aplicando plataforma Near-RT RIC (Redis DBAAS, E2Term, SubMgr)...${NC}"
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f deploy/kubernetes/near-rt-ric.yaml
kubectl rollout status deployment/deployment-ricplt-dbaas-redis -n ${NAMESPACE_RIC} --timeout=60s

# 4. Aplicar as 3 Reference xApps (ricxapp)
echo -e "\n${YELLOW}[4/5] Aplicando manifestos das 3 Reference xApps no namespace ${NAMESPACE_XAPP}...${NC}"
kubectl apply -f deploy/kubernetes/xapp-qos-xslice.yaml
kubectl apply -f deploy/kubernetes/xapp-energy-saving.yaml
kubectl apply -f deploy/kubernetes/xapp-traffic-steering.yaml

# 5. Aplicar RDL se modo governança
if [ "$DEPLOY_RDL" = true ]; then
    echo -e "\n${YELLOW}[5/5] Aplicando xApp RDL (Resource and Decision Layer)...${NC}"
    kubectl apply -f deploy/kubernetes/configmap.yaml
    kubectl apply -f deploy/kubernetes/deployment.yaml
    kubectl apply -f deploy/kubernetes/service-http.yaml
    kubectl apply -f deploy/kubernetes/service-rmr.yaml
    kubectl rollout status deployment/ricxapp-iqos-xapp-rdl -n ${NAMESPACE_XAPP} --timeout=60s
else
    echo -e "\n${YELLOW}[5/5] Modo Baseline ativo: removendo xApp RDL caso exista...${NC}"
    kubectl delete -f deploy/kubernetes/deployment.yaml --ignore-not-found=true
fi

# Aguardar prontidão das Reference xApps
kubectl rollout status deployment/ricxapp-qos-xslice -n ${NAMESPACE_XAPP} --timeout=60s
kubectl rollout status deployment/ricxapp-energy-saving -n ${NAMESPACE_XAPP} --timeout=60s
kubectl rollout status deployment/ricxapp-traffic-steering -n ${NAMESPACE_XAPP} --timeout=60s

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}   Deploy K8s Concluído com SUCESSO!                                  ${NC}"
echo -e "${GREEN}======================================================================${NC}"

kubectl get pods -n ${NAMESPACE_RIC} -o wide
kubectl get pods -n ${NAMESPACE_XAPP} -o wide
