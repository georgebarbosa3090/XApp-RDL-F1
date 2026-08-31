#!/bin/bash
# ==============================================================================
# Pipeline de Deploy Helm Dedicado: xApp RDL Fase 2 (CA-RDL / MARL)
# Release Exclusiva: ricxapp-iqos-xapp-rdl-f2 (v2.0.0)
# ==============================================================================
# Premissa: O Near-RT RIC (ricplt) e as 3 Reference xApps (ricxapp) ja estao
#           implantados e operando. Este script instala/atualiza APENAS a Fase 2.
# ==============================================================================
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

IMAGE_NAME="iqos-xapp-rdl"
IMAGE_TAG="2.0.0"
RELEASE_NAME="ricxapp-iqos-xapp-rdl-f2"
CHART_DIR="deploy/helm/iqos-xapp-rdl"
NAMESPACE_RIC="ricplt"
NAMESPACE_XAPP="ricxapp"
CLUSTER_NAME="rancher-lab"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${CYAN}   Deploy Helm Isolado: xApp RDL Fase 2 (CA-RDL / MARL)               ${NC}"
echo -e "${BLUE}   Release Name: ${RELEASE_NAME} | Versão: ${IMAGE_TAG}               ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. Configurar KUBECONFIG para o cluster existente
export KUBECONFIG=~/.kube/config
if command -v k3d &> /dev/null; then
    k3d kubeconfig merge ${CLUSTER_NAME} --kubeconfig-switch-context -d 2>/dev/null || true
    k3d kubeconfig get ${CLUSTER_NAME} > ~/.kube/config 2>/dev/null || true
fi

# 2. Build da Imagem Docker da Fase 2 (v2.0.0)
echo -e "\n${YELLOW}[1/4] Construindo imagem Docker da Fase 2 (${IMAGE_NAME}:${IMAGE_TAG})...${NC}"
docker build --file docker/Dockerfile --tag ${IMAGE_NAME}:${IMAGE_TAG} .

# 3. Importação da Imagem para os nós do k3d
echo -e "\n${YELLOW}[2/4] Importando imagem ${IMAGE_NAME}:${IMAGE_TAG} para o cluster k3d...${NC}"
K3D_NODES=$(docker ps --format '{{.Names}}' | grep -E "k3d-.*-(server-[0-9]|agent-[0-9])" || true)
if [ -n "$K3D_NODES" ]; then
    for node in $K3D_NODES; do
        echo " -> Importando no containerd do nó: $node"
        docker save ${IMAGE_NAME}:${IMAGE_TAG} | docker exec -i $node ctr images import - || true
    done
else
    if command -v k3d &> /dev/null; then
        k3d image import ${IMAGE_NAME}:${IMAGE_TAG} -c ${CLUSTER_NAME} || true
    fi
fi

# 4. Deploy/Upgrade Helm Exclusivo da Fase 2
echo -e "\n${YELLOW}[3/4] Executando Helm Upgrade/Install da release '${RELEASE_NAME}'...${NC}"
helm upgrade --install ${RELEASE_NAME} ${CHART_DIR} \
  --namespace ${NAMESPACE_XAPP} \
  --set image.repository=${IMAGE_NAME} \
  --set image.tag=${IMAGE_TAG} \
  --set image.pullPolicy=Never \
  --set fullnameOverride=${RELEASE_NAME} \
  --set env.useFakeSdl="false" \
  --set env.rmrWaitForReady="false" \
  --set env.enableTorch="true"

# 5. Validação de Rollout e Status
echo -e "\n${YELLOW}[4/4] Aguardando inicialização e prontidão do Pod da Fase 2...${NC}"
kubectl rollout status deployment/${RELEASE_NAME} -n ${NAMESPACE_XAPP} --timeout=60s

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}   Deploy da xApp RDL Fase 2 concluído com SUCESSO!                  ${NC}"
echo -e "${GREEN}======================================================================${NC}"

echo -e "\n--- Status das xApps no namespace ${NAMESPACE_XAPP} ---"
kubectl get pods -n ${NAMESPACE_XAPP} -o wide

echo -e "\n--- Endpoints de Teste da Fase 2 ---"
echo -e " Healthcheck: curl -i http://localhost:8080/health"
echo -e " Métricas:    curl -s http://localhost:8081/metrics | grep -E 'rdl_|marl_'"
echo -e " Logs:        kubectl logs -n ${NAMESPACE_XAPP} -l app=${RELEASE_NAME} -f\n"
