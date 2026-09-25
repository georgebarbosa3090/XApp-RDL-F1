#!/usr/bin/env bash
# ==============================================================================
# Script: cleanup_all.sh
# Finalidade: Remove completamente todos os componentes O-RAN (xApps, Near-RT RIC,
#             releases Helm, gerador de tráfego e namespaces ricxapp/ricplt).
# ==============================================================================
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}======================================================================${NC}"
echo -e "${RED}   [!] Iniciando Limpeza e Remocao Completa do Ambiente O-RAN / K8s   ${NC}"
echo -e "${RED}======================================================================${NC}"

# 1. Remover releases Helm se existirem
echo -e "\n${YELLOW}[1/4] Removendo releases Helm...${NC}"
for release in $(helm list -A -q 2>/dev/null || true); do
    echo " -> Removendo Helm release: $release"
    helm uninstall "$release" -n ricxapp 2>/dev/null || true
    helm uninstall "$release" -n ricplt 2>/dev/null || true
done

# 2. Deletar todos os recursos nos namespaces ricxapp e ricplt
echo -e "\n${YELLOW}[2/4] Deletando recursos nos namespaces ricxapp e ricplt...${NC}"
kubectl delete all,configmap,secret,ingress,service --all -n ricxapp --timeout=30s --grace-period=0 --force 2>/dev/null || true
kubectl delete all,configmap,secret,ingress,service --all -n ricplt --timeout=30s --grace-period=0 --force 2>/dev/null || true

# 3. Remover os namespaces
echo -e "\n${YELLOW}[3/4] Removendo namespaces ricxapp e ricplt...${NC}"
kubectl delete namespace ricxapp --timeout=30s 2>/dev/null || true
kubectl delete namespace ricplt --timeout=30s 2>/dev/null || true

# 4. Status Final
echo -e "\n${GREEN}[4/4] Verificando se restou algum pod...${NC}"
kubectl get pods -A | grep -E "ricxapp|ricplt" || echo -e "${GREEN}[[OK]] Nenhum recurso O-RAN restante no cluster.${NC}"

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}   [[OK]] Limpeza concluida com SUCESSO! O cluster esta limpo.           ${NC}"
echo -e "${GREEN}======================================================================${NC}"
