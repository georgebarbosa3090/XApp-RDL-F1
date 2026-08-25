#!/bin/bash
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
CHART_DIR="deploy/helm/iqos-xapp-rdl"
NAMESPACE="ricxapp"
RELEASE_NAME="ricxapp-iqos-xapp-rdl"

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}   Pipeline Automatizado de Deploy Helm - xApp RDL  ${NC}"
echo -e "${BLUE}====================================================${NC}"

# 0. Sincronizar Kubeconfig
if command -v k3d &> /dev/null; then
    k3d kubeconfig merge rancher-lab --kubeconfig-switch-context -d 2>/dev/null || true
fi
export KUBECONFIG=~/.kube/config

# 1. Build da Imagem Docker
echo -e "\n${YELLOW}[1/6] Construindo imagem Docker (${IMAGE_NAME}:${IMAGE_TAG})...${NC}"
docker build --file docker/Dockerfile --tag ${IMAGE_NAME}:${IMAGE_TAG} .

# 2. Importação Automática para os nós do k3d
echo -e "\n${YELLOW}[2/6] Importando imagem para os nós do k3d...${NC}"
K3D_NODES=$(docker ps --format '{{.Names}}' | grep -E "k3d-.*-(server|agent)" || true)
if [ -n "$K3D_NODES" ]; then
    for node in $K3D_NODES; do
        echo " -> Carregando no nó containerd: $node"
        docker save ${IMAGE_NAME}:${IMAGE_TAG} | docker exec -i $node ctr images import - || true
    done
else
    if command -v k3d &> /dev/null; then
        echo " -> Importando via CLI nativa do k3d..."
        k3d image import ${IMAGE_NAME}:${IMAGE_TAG} -c rancher-lab || true
    fi
fi

# 3. Criação de Namespaces e Near-RT RIC DBAAS
echo -e "\n${YELLOW}[3/6] Garantindo namespaces e plataforma Near-RT RIC (ricplt)...${NC}"
kubectl create namespace ricplt --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Subir Redis DBAAS no ricplt se não existir
if ! kubectl get deployment deployment-ricplt-dbaas-redis -n ricplt &>/dev/null; then
    echo " -> Provisionando Redis DBAAS (Shared Data Layer) no ricplt..."
    kubectl apply -n ricplt -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deployment-ricplt-dbaas-redis
  namespace: ricplt
  labels:
    app: ricplt-dbaas
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ricplt-dbaas
  template:
    metadata:
      labels:
        app: ricplt-dbaas
    spec:
      containers:
      - name: redis
        image: redis:6.2-alpine
        ports:
        - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: service-ricplt-dbaas-tcp
  namespace: ricplt
  labels:
    app: ricplt-dbaas
spec:
  selector:
    app: ricplt-dbaas
  ports:
  - port: 6379
    targetPort: 6379
EOF
fi

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
echo -e "${GREEN}   Deploy Helm Concluído com SUCESSO!               ${NC}"
echo -e "${GREEN}====================================================${NC}"

kubectl get pods -n ${NAMESPACE} -l app=${RELEASE_NAME} -o wide
