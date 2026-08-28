#!/bin/bash
# ==============================================================================
# Pipeline Automatizado de Deploy Helm: Near-RT RIC + 3 Reference xApps (+ RDL)
# ==============================================================================
set -e

# Cores para output
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
CLUSTER_NAME="rancher-lab"

# Flag para deploy do RDL (padrão: true; use --baseline para subir apenas as 3 xApps concorrentes sem RDL)
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
echo -e "${BLUE}   Pipeline de Deploy Helm: Near-RT RIC + 3 Reference xApps           ${NC}"
if [ "$DEPLOY_RDL" = true ]; then
    echo -e "${CYAN}   [Modo Governança: Near-RT RIC + 3 Reference xApps + xApp RDL]      ${NC}"
else
    echo -e "${YELLOW}   [Modo Baseline: Near-RT RIC + 3 Reference xApps (SEM RDL)]         ${NC}"
fi
echo -e "${BLUE}======================================================================${NC}"

# 0. Verificar se o cluster k3d existe; se não existir, criar automaticamente
if ! k3d cluster list ${CLUSTER_NAME} 2>/dev/null | grep -q "${CLUSTER_NAME}"; then
    echo -e "\n${YELLOW}[0/6] Cluster '${CLUSTER_NAME}' não encontrado. Criando cluster k3d automaticamente...${NC}"
    docker network disconnect -f k3d-${CLUSTER_NAME} rancher-server 2>/dev/null || true
    k3d cluster create ${CLUSTER_NAME} \
      --servers 1 \
      --agents 0 \
      --port "36422:36422/SCTP@server:0" \
      --port "8080:8080@server:0" \
      --port "8081:8081@server:0" \
      --port "8082:8082@server:0" \
      --port "8083:8083@server:0" \
      --port "8084:8084@server:0" \
      --port "8085:8085@server:0" \
      --port "8086:8086@server:0" \
      --port "8087:8087@server:0" \
      --port "4560:4560@server:0" \
      --port "4561:4561@server:0"
    mkdir -p ~/.kube
    k3d kubeconfig get ${CLUSTER_NAME} > ~/.kube/config
    chmod 600 ~/.kube/config
else
    k3d kubeconfig merge ${CLUSTER_NAME} --kubeconfig-switch-context -d 2>/dev/null || true
    k3d kubeconfig get ${CLUSTER_NAME} > ~/.kube/config 2>/dev/null || true
fi
export KUBECONFIG=~/.kube/config

# 1. Build da Imagem Docker Unificada
echo -e "\n${YELLOW}[1/6] Construindo imagem Docker unificada (${IMAGE_NAME}:${IMAGE_TAG})...${NC}"
docker build --file docker/Dockerfile --tag ${IMAGE_NAME}:${IMAGE_TAG} .

# 2. Importação Automática para os nós do k3d
echo -e "\n${YELLOW}[2/6] Importando imagem para os nós do k3d...${NC}"
K3D_NODES=$(docker ps --format '{{.Names}}' | grep -E "k3d-.*-(server-[0-9]|agent-[0-9])" || true)
if [ -n "$K3D_NODES" ]; then
    for node in $K3D_NODES; do
        echo " -> Carregando no nó containerd: $node"
        docker save ${IMAGE_NAME}:${IMAGE_TAG} | docker exec -i $node ctr images import - || true
    done
else
    if command -v k3d &> /dev/null; then
        echo " -> Importando via CLI nativa do k3d..."
        k3d image import ${IMAGE_NAME}:${IMAGE_TAG} -c ${CLUSTER_NAME} || true
    fi
fi

# 3. Criação de Namespaces e Near-RT RIC Plataforma (ricplt)
echo -e "\n${YELLOW}[3/6] Provisionando plataforma Near-RT RIC (namespace ${NAMESPACE_RIC})...${NC}"
kubectl create namespace ${NAMESPACE_RIC} --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ${NAMESPACE_XAPP} --dry-run=client -o yaml | kubectl apply -f -

# Subir Redis DBAAS, E2Term e SubMgr no ricplt
echo " -> Aplicando manifestos do Near-RT RIC (Redis DBAAS, E2Term, SubMgr)..."
kubectl apply -f deploy/kubernetes/near-rt-ric.yaml

# Aguardar Redis DBAAS estar Running
echo " -> Aguardando Redis DBAAS atingir estado Ready no ricplt..."
kubectl rollout status deployment/deployment-ricplt-dbaas-redis -n ${NAMESPACE_RIC} --timeout=60s

# 4. Deploy das 3 Reference xApps via Helm (ricxapp)
echo -e "\n${YELLOW}[4/6] Realizando deploy das 3 Reference xApps via Helm no namespace ${NAMESPACE_XAPP}...${NC}"

echo " -> 4.1 Instalando 1. xSlice QoS xApp (peihaoY/xslice-oran)..."
helm upgrade --install ricxapp-qos-xslice deploy/helm/xapp-qos-xslice \
  --namespace ${NAMESPACE_XAPP} \
  --create-namespace \
  --set image.pullPolicy=Never

echo " -> 4.2 Instalando 2. Energy Saving xApp (Orange-OpenSource/ns-O-RAN-flexric)..."
helm upgrade --install ricxapp-energy-saving deploy/helm/xapp-energy-saving \
  --namespace ${NAMESPACE_XAPP} \
  --create-namespace \
  --set image.pullPolicy=Never

echo " -> 4.3 Instalando 3. Traffic Steering xApp (o-ran-sc/ric-app-ts)..."
helm upgrade --install ricxapp-traffic-steering deploy/helm/xapp-traffic-steering \
  --namespace ${NAMESPACE_XAPP} \
  --create-namespace \
  --set image.pullPolicy=Never

# 5. Deploy do RDL (se habilitado)
if [ "$DEPLOY_RDL" = true ]; then
    echo -e "\n${YELLOW}[5/6] Instalando 4. xApp RDL (Resource and Decision Layer - Fase 1)...${NC}"
    helm upgrade --install ricxapp-iqos-xapp-rdl deploy/helm/iqos-xapp-rdl \
      --namespace ${NAMESPACE_XAPP} \
      --create-namespace \
      --set image.pullPolicy=Never \
      --set env.useFakeSdl="false" \
      --set env.rmrWaitForReady="false"
else
    echo -e "\n${YELLOW}[5/6] Modo Baseline ativo: xApp RDL NAO será implantada neste momento.${NC}"
    helm uninstall ricxapp-iqos-xapp-rdl -n ${NAMESPACE_XAPP} 2>/dev/null || true
fi

# 6. Validação de Rollout e Status
echo -e "\n${YELLOW}[6/6] Validando rollout dos Pods no namespace ${NAMESPACE_XAPP}...${NC}"
kubectl rollout status deployment/ricxapp-qos-xslice -n ${NAMESPACE_XAPP} --timeout=60s
kubectl rollout status deployment/ricxapp-energy-saving -n ${NAMESPACE_XAPP} --timeout=60s
kubectl rollout status deployment/ricxapp-traffic-steering -n ${NAMESPACE_XAPP} --timeout=60s

if [ "$DEPLOY_RDL" = true ]; then
    kubectl rollout status deployment/ricxapp-iqos-xapp-rdl -n ${NAMESPACE_XAPP} --timeout=60s
fi

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}   Deploy Concluído com SUCESSO!                                      ${NC}"
echo -e "${GREEN}======================================================================${NC}"

echo -e "\n--- Pods Near-RT RIC (ricplt) ---"
kubectl get pods -n ${NAMESPACE_RIC} -o wide

echo -e "\n--- xApps Ativas (ricxapp) ---"
kubectl get pods -n ${NAMESPACE_XAPP} -o wide
