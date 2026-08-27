#!/bin/bash
set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

CLUSTER_NAME="rancher-lab"
RANCHER_CONTAINER="rancher-server"
RANCHER_PORT="8443"

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}   Vinculação e Correção do Agente Rancher (k3d)    ${NC}"
echo -e "${BLUE}====================================================${NC}"

# 1. Obter URL do manifesto de importação como argumento ou interativo
IMPORT_URL="$1"

# 2. Conectar o container do Rancher à rede do k3d
echo -e "\n${YELLOW}[1/4] Conectando container ${RANCHER_CONTAINER} à rede k3d-${CLUSTER_NAME}...${NC}"
docker network connect k3d-${CLUSTER_NAME} ${RANCHER_CONTAINER} 2>/dev/null || true

# 3. Baixar e aplicar manifesto do Rancher
if [ -n "$IMPORT_URL" ]; then
    echo -e "\n${YELLOW}[2/4] Baixando e aplicando manifesto do Rancher...${NC}"
    # Tenta via docker exec direto do container para evitar conflitos de porta/DNS no host
    IMPORT_PATH=$(echo "$IMPORT_URL" | sed -E 's|https?://[^/]+||')
    if docker exec ${RANCHER_CONTAINER} curl --insecure -sfL "https://localhost:443${IMPORT_PATH}" > /tmp/rancher-import.yaml 2>/dev/null && [ -s /tmp/rancher-import.yaml ]; then
        echo " -> Manifesto obtido com sucesso via container interno!"
        kubectl apply -f /tmp/rancher-import.yaml
    elif curl --insecure -sfL "https://127.0.0.1:${RANCHER_PORT}${IMPORT_PATH}" > /tmp/rancher-import.yaml 2>/dev/null && [ -s /tmp/rancher-import.yaml ]; then
        echo " -> Manifesto obtido via host (porta ${RANCHER_PORT})!"
        kubectl apply -f /tmp/rancher-import.yaml
    else
        echo " -> Tentando aplicar URL direta..."
        curl --insecure -sfL "$IMPORT_URL" | kubectl apply -f - || true
    fi
fi

# 4. Ajustar variáveis de ambiente do agente para comunicação interna direta
echo -e "\n${YELLOW}[3/4] Configurando Deployment do cattle-cluster-agent...${NC}"
kubectl wait --for=condition=available --timeout=60s deployment/cattle-cluster-agent -n cattle-system 2>/dev/null || true

kubectl set env deployment/cattle-cluster-agent -n cattle-system \
  CATTLE_SERVER="https://rancher-server:443" \
  CATTLE_SSL_NO_VERIFY="true" 2>/dev/null || true

# 5. Reiniciar o pod do agente
echo -e "\n${YELLOW}[4/4] Reiniciando Pod do Agente no namespace cattle-system...${NC}"
kubectl rollout restart deployment/cattle-cluster-agent -n cattle-system 2>/dev/null || true

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}   Agente Configurado! Verificando status dos Pods:  ${NC}"
echo -e "${GREEN}====================================================${NC}"
kubectl get pods -n cattle-system -o wide
