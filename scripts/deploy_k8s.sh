#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

IMAGE_NAME="iqos-xapp-rdl"
IMAGE_TAG="1.1.0"
K8S_DIR="deploy/kubernetes"
NAMESPACE="ricxapp"
DEPLOYMENT_NAME="ricxapp-iqos-xapp-rdl"

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}   Pipeline de Deploy Kubernetes (K8s Puro / Kustomize)  ${NC}"
echo -e "${BLUE}====================================================${NC}"

# 1. Build da Imagem Docker
echo -e "\n${YELLOW}[1/4] Construindo imagem Docker (${IMAGE_NAME}:${IMAGE_TAG})...${NC}"
docker build --file docker/Dockerfile --tag ${IMAGE_NAME}:${IMAGE_TAG} .

# 2. Auto-Importação para nós k3d (se aplicável)
echo -e "\n${YELLOW}[2/4] Verificando nós do cluster para importação da imagem...${NC}"
K3D_NODES=$(docker ps --format '{{.Names}}' | grep -E "k3d-.*-(server|agent)" || true)
if [ -n "$K3D_NODES" ]; then
    for node in $K3D_NODES; do
        echo " -> Carregando imagem no nó containerd: $node"
        docker save ${IMAGE_NAME}:${IMAGE_TAG} | docker exec -i $node ctr images import - || true
    done
fi

# 3. Aplicar os manifestos via Kustomize / Kubectl
echo -e "\n${YELLOW}[3/4] Aplicando manifestos no Kubernetes (${K8S_DIR})...${NC}"
kubectl apply -k ${K8S_DIR}

# 4. Aguardar o Pod estar 1/1 Running
echo -e "\n${YELLOW}[4/4] Aguardando Pod atingir estado Ready...${NC}"
kubectl rollout status deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE} --timeout=60s

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}   Deploy K8s Concluído com SUCESSO! Pod 1/1 Running ${NC}"
echo -e "${GREEN}====================================================${NC}"

kubectl get pods -n ${NAMESPACE} -l app=${DEPLOYMENT_NAME} -o wide
