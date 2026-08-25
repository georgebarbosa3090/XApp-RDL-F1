#!/bin/bash
set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

IMAGE_NAME="iqos-xapp-rdl"
IMAGE_TAG="1.1.0"
CHART_DIR="deploy/helm/iqos-xapp-rdl"
NAMESPACE="ricxapp"
RELEASE_NAME="ricxapp-iqos-xapp-rdl"

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}   Pipeline Automatizado de Deploy Helm - xApp RDL  ${NC}"
echo -e "${BLUE}====================================================${NC}"

# 1. Build da Imagem Docker
echo -e "\n${YELLOW}[1/6] Construindo imagem Docker (${IMAGE_NAME}:${IMAGE_TAG})...${NC}"
docker build --file docker/Dockerfile --tag ${IMAGE_NAME}:${IMAGE_TAG} .

# 2. Importação Automática para os nós do k3d
echo -e "\n${YELLOW}[2/6] Importando imagem para os nós do k3d...${NC}"
K3D_NODES=$(docker ps --format '{{.Names}}' | grep k3d || true)
if [ -n "$K3D_NODES" ]; then
    for node in $K3D_NODES; do
        echo " -> Carregando no nó containerd: $node"
        docker save ${IMAGE_NAME}:${IMAGE_TAG} | docker exec -i $node ctr images import -
    done
else
    echo " -> Nenhum nó k3d detectado. Utilizando daemon local/containerd padrão."
fi

# 3. Criação de Namespaces
echo -e "\n${YELLOW}[3/6] Garantindo namespaces ricplt e ricxapp...${NC}"
kubectl create namespace ricplt --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# 4. Validação e Empacotamento Helm
echo -e "\n${YELLOW}[4/6] Validando e empacotando Helm Chart...${NC}"
helm lint ${CHART_DIR}
helm package ${CHART_DIR}

# 5. Instalação / Upgrade no Kubernetes
echo -e "\n${YELLOW}[5/6] Executando Helm Upgrade/Install no namespace ${NAMESPACE}...${NC}"
helm upgrade --install ${RELEASE_NAME} ./${IMAGE_NAME}-${IMAGE_TAG}.tgz \
  --namespace ${NAMESPACE} \
  --create-namespace \
  --set image.pullPolicy=Never \
  --set env.useFakeSdl="true" \
  --set env.rmrWaitForReady="false"

# 6. Aguardar Pod estar 1/1 Running e Pronto
echo -e "\n${YELLOW}[6/6] Aguardando Pod atingir estado Ready...${NC}"
kubectl rollout status deployment/${RELEASE_NAME} -n ${NAMESPACE} --timeout=60s

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}   Deploy Concluído com SUCESSO! Pod 1/1 Running    ${NC}"
echo -e "${GREEN}====================================================${NC}"

kubectl get pods -n ${NAMESPACE} -l app=${RELEASE_NAME} -o wide
