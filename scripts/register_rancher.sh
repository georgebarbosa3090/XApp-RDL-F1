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

# 3. Descobrir ou validar URL/Token do manifesto
if [ -z "$IMPORT_URL" ] || [[ "$IMPORT_URL" == *"<token>"* ]]; then
    echo -e "${CYAN} -> Tentando autodescobrir token de importação diretamente do ${RANCHER_CONTAINER}...${NC}"
    DISCOVERED_PATH=$(docker exec ${RANCHER_CONTAINER} curl -s -k https://localhost:443/v3/clusterRegistrationTokens 2>/dev/null | grep -o '/v3/import/[^"]*\.yaml' | head -n 1 || true)
    if [ -n "$DISCOVERED_PATH" ]; then
        IMPORT_URL="https://localhost:443${DISCOVERED_PATH}"
        echo -e "${GREEN} -> Token descoberto automaticamente:${NC} ${DISCOVERED_PATH}"
    elif [ -z "$IMPORT_URL" ] || [[ "$IMPORT_URL" == *"<token>"* ]]; then
        echo -e "${RED}[ERRO] Token do Rancher não fornecido e não foi possível autodescobrir.${NC}"
        echo -e "${YELLOW}Uso: bash scripts/register_rancher.sh <URL_OU_TOKEN>${NC}"
        echo -e "Exemplo: bash scripts/register_rancher.sh https://localhost:8443/v3/import/c-m-abcdef_c-m-abcdef.yaml"
        echo -e "         ou: make rancher-connect URL=\"https://.../v3/import/c-m-abcdef_c-m-abcdef.yaml\""
        exit 1
    fi
fi

# Se foi passado apenas o token ou nome do arquivo .yaml, monta a URL interna
if [[ "$IMPORT_URL" != http* ]]; then
    if [[ "$IMPORT_URL" == *.yaml ]]; then
        IMPORT_URL="https://localhost:443/v3/import/${IMPORT_URL}"
    else
        IMPORT_URL="https://localhost:443/v3/import/${IMPORT_URL}.yaml"
    fi
fi

# 4. Baixar e aplicar manifesto do Rancher
echo -e "\n${YELLOW}[2/4] Baixando e aplicando manifesto do Rancher...${NC}"
IMPORT_PATH=$(echo "$IMPORT_URL" | sed -E 's|https?://[^/]+||')

if docker exec ${RANCHER_CONTAINER} curl --insecure -sfL "https://localhost:443${IMPORT_PATH}" > /tmp/rancher-import.yaml 2>/dev/null && [ -s /tmp/rancher-import.yaml ]; then
    echo " -> Manifesto obtido com sucesso via container interno (${IMPORT_PATH})!"
    kubectl apply -f /tmp/rancher-import.yaml
elif curl --insecure -sfL "https://127.0.0.1:${RANCHER_PORT}${IMPORT_PATH}" > /tmp/rancher-import.yaml 2>/dev/null && [ -s /tmp/rancher-import.yaml ]; then
    echo " -> Manifesto obtido via host (porta ${RANCHER_PORT})!"
    kubectl apply -f /tmp/rancher-import.yaml
else
    echo " -> Tentando aplicar via URL direta com curl..."
    curl --insecure -sfL "$IMPORT_URL" | kubectl apply -f - || true
fi

# 5. Ajustar variáveis de ambiente do agente para comunicação interna direta
echo -e "\n${YELLOW}[3/4] Configurando Deployment do cattle-cluster-agent...${NC}"
echo " -> Aguardando namespace cattle-system e deployment cattle-cluster-agent..."
for i in {1..12}; do
    if kubectl get deployment cattle-cluster-agent -n cattle-system >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

kubectl set env deployment/cattle-cluster-agent -n cattle-system \
  CATTLE_SERVER="https://rancher-server:443" \
  CATTLE_SSL_NO_VERIFY="true" 2>/dev/null || true

# 6. Reiniciar o pod do agente
echo -e "\n${YELLOW}[4/4] Reiniciando Pod do Agente no namespace cattle-system...${NC}"
kubectl rollout restart deployment/cattle-cluster-agent -n cattle-system 2>/dev/null || true

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}   Agente Configurado! Verificando status dos Pods:  ${NC}"
echo -e "${GREEN}====================================================${NC}"
kubectl get pods -n cattle-system -o wide 2>/dev/null || echo "Aguardando criação dos pods em cattle-system..."
