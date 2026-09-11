#!/usr/bin/env bash
# ==============================================================================
# Monitor Interativo Live do Cluster K8s & Near-RT RIC
# Skill: 07-k8s-oran-cluster-operator
# ==============================================================================

export KUBECONFIG="/etc/rancher/k3s/k3s.yaml"

# Ativar cores
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo -e "${CYAN}================================================================================${NC}"
echo -e "${GREEN} ☸️ MONITOR LIVE: O-RAN NEAR-RT RIC & H-RDL CLUSTER (WSL2 / k3s)${NC}"
echo -e "${CYAN}================================================================================${NC}"

while true; do
    echo -e "\n${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] Estado dos Nós Kubernetes:${NC}"
    kubectl get nodes -o wide 2>/dev/null || echo "Aguardando nós do cluster..."
    
    echo -e "\n${BLUE}[Namespace: ricplt (Near-RT RIC Platform)]${NC}"
    kubectl get pods -n ricplt -o wide 2>/dev/null || echo "Nenhum pod em ricplt."
    
    echo -e "\n${GREEN}[Namespace: ricxapp (H-RDL & Reference xApps)]${NC}"
    kubectl get pods -n ricxapp -o wide 2>/dev/null || echo "Nenhum pod em ricxapp."
    
    echo -e "\n${CYAN}--------------------------------------------------------------------------------${NC}"
    echo -e "Últimos eventos do cluster (Event Watch):"
    kubectl get events -n ricxapp --sort-by='.lastTimestamp' 2>/dev/null | tail -n 6 || true
    echo -e "${CYAN}================================================================================${NC}"
    echo -e "Pressione Ctrl+C para encerrar o monitor."
    sleep 5
    clear
done
