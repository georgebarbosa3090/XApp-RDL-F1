#!/usr/bin/env bash
# ==============================================================================
# Script: deploy_dual_rdl_6xapps.sh
# Finalidade: Implanta o ecossistema O-RAN completo de coexistência:
#             - Near-RT RIC (ricplt: DBAAS Redis, E2Term, SubMgr)
#             - H-RDL Fase 1 (ricxapp-iqos-xapp-rdl-f1: v1.1.0)
#             - CA-RDL Fase 2 (ricxapp-iqos-xapp-rdl-f2: v2.0.0)
#             - 6 Reference xApps (xSlice, Energy, TrafficSteering, Beamformer, ISAC, Rogue)
#             - Injetor Contínuo de Tráfego Service Mesh
# ==============================================================================
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

NAMESPACE_RIC="ricplt"
NAMESPACE_XAPP="ricxapp"
CLUSTER_NAME="rancher-lab"
CHART_DIR="deploy/helm/iqos-xapp-rdl"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${CYAN}   Deploy Coexistencia O-RAN: H-RDL (F1) + CA-RDL (F2) + 6 xApps      ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. Garantir Namespaces com Injeção Istio
echo -e "\n${YELLOW}[1/6] Configurando namespaces ricplt e ricxapp com injeção Istio...${NC}"
kubectl create namespace "$NAMESPACE_RIC" --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace "$NAMESPACE_XAPP" --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace "$NAMESPACE_RIC" istio-injection=enabled --overwrite 2>/dev/null || true
kubectl label namespace "$NAMESPACE_XAPP" istio-injection=enabled --overwrite 2>/dev/null || true

# 2. Sincronizar Imagens Docker nos Nós k3d
echo -e "\n${YELLOW}[2/6] Sincronizando imagens Docker (1.1.0 e 2.0.0)...${NC}"
if docker image inspect iqos-xapp-rdl:2.0.0 >/dev/null 2>&1 && ! docker image inspect iqos-xapp-rdl:1.1.0 >/dev/null 2>&1; then
    docker tag iqos-xapp-rdl:2.0.0 iqos-xapp-rdl:1.1.0
elif docker image inspect iqos-xapp-rdl:1.1.0 >/dev/null 2>&1 && ! docker image inspect iqos-xapp-rdl:2.0.0 >/dev/null 2>&1; then
    docker tag iqos-xapp-rdl:1.1.0 iqos-xapp-rdl:2.0.0
fi

if command -v k3d &> /dev/null; then
    k3d image import iqos-xapp-rdl:1.1.0 iqos-xapp-rdl:2.0.0 -c ${CLUSTER_NAME} 2>/dev/null || true
else
    for node in $(docker ps --format '{{.Names}}' | grep -E "k3d-.*-(server|agent)" 2>/dev/null || true); do
        docker save iqos-xapp-rdl:1.1.0 | docker exec -i "$node" ctr images import - 2>/dev/null || true
        docker save iqos-xapp-rdl:2.0.0 | docker exec -i "$node" ctr images import - 2>/dev/null || true
    done
fi

# 3. Implantar Near-RT RIC (ricplt)
echo -e "\n${YELLOW}[3/6] Implantando Near-RT RIC (DBAAS Redis, E2Term, SubMgr)...${NC}"
kubectl apply -f deploy/kubernetes/near-rt-ric.yaml -n "$NAMESPACE_RIC"
kubectl rollout status deployment/deployment-ricplt-dbaas-redis -n "$NAMESPACE_RIC" --timeout=60s

# 4. Implantar as 6 Reference xApps
echo -e "\n${YELLOW}[4/6] Implantando as 6 Reference xApps (xSlice, Energy, TS, Beamformer, ISAC, Rogue)...${NC}"
SKIP_IMAGE_IMPORT=true bash scripts/deploy_reference_xapps.sh

# 5. Implantar H-RDL Fase 1 e CA-RDL Fase 2 Concorrentes via Helm
echo -e "\n${YELLOW}[5/6] Implantando H-RDL (Fase 1) e CA-RDL (Fase 2) concorrentes...${NC}"

# 5.1 Release Fase 1 (H-RDL Determinística)
helm upgrade --install ricxapp-iqos-xapp-rdl-f1 ${CHART_DIR} \
  --namespace ${NAMESPACE_XAPP} \
  --set image.repository="iqos-xapp-rdl" \
  --set image.tag="1.1.0" \
  --set image.pullPolicy=Never \
  --set fullnameOverride="ricxapp-iqos-xapp-rdl-f1" \
  --set env.useFakeSdl="false" \
  --set env.rmrWaitForReady="false" \
  --set env.enableTorch="false"

# 5.2 Release Fase 2 (CA-RDL / MARL MAPPO)
helm upgrade --install ricxapp-iqos-xapp-rdl-f2 ${CHART_DIR} \
  --namespace ${NAMESPACE_XAPP} \
  --set image.repository="iqos-xapp-rdl" \
  --set image.tag="2.0.0" \
  --set image.pullPolicy=Never \
  --set fullnameOverride="ricxapp-iqos-xapp-rdl-f2" \
  --set env.useFakeSdl="false" \
  --set env.rmrWaitForReady="false" \
  --set env.enableTorch="true"

# 6. Validar Rollout e Subir Gerador de Carga
echo -e "\n${YELLOW}[6/6] Validando prontidão de todos os Pods e ativando injeção de tráfego...${NC}"
kubectl rollout status deployment/ricxapp-iqos-xapp-rdl-f1 -n ${NAMESPACE_XAPP} --timeout=120s
kubectl rollout status deployment/ricxapp-iqos-xapp-rdl-f2 -n ${NAMESPACE_XAPP} --timeout=120s
kubectl apply -f deploy/kubernetes/traffic-generator.yaml -n ${NAMESPACE_XAPP}

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}   Deploy Completo de Coexistência Concluído com SUCESSO!            ${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo -e "\n--- Pods Near-RT RIC (ricplt) ---"
kubectl get pods -n ${NAMESPACE_RIC} -o wide
echo -e "\n--- Workloads Ativos no Mesh (ricxapp) ---"
kubectl get pods -n ${NAMESPACE_XAPP} -o wide
