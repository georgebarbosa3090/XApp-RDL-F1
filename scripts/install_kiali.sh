#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}  Instalação Automatizada de Istio & Kiali Dashboard${NC}"
echo -e "${BLUE}====================================================${NC}"

# 1. Download do Istio (se ainda não existir)
if ! command -v istioctl &> /dev/null; then
    echo -e "\n${YELLOW}[1/5] Baixando istioctl...${NC}"
    curl -L https://istio.io/downloadIstio | sh -
    cp istio-*/bin/istioctl /usr/local/bin/ 2>/dev/null || cp istio-*/bin/istioctl ~/bin/ 2>/dev/null || true
    chmod +x /usr/local/bin/istioctl 2>/dev/null || true
fi

# 2. Instalação do Istio Service Mesh
echo -e "\n${YELLOW}[2/5] Instalando Istio Service Mesh (Profile Demo)...${NC}"
kubectl create namespace istio-system --dry-run=client -o yaml | kubectl apply -f -
istioctl install --set profile=demo -y

# 3. Instalação dos Addons (Prometheus e Kiali)
echo -e "\n${YELLOW}[3/5] Instalando Prometheus e Kiali Dashboard...${NC}"
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/addons/prometheus.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/addons/kiali.yaml

# 4. Habilitar injeção automática no namespace ricxapp
echo -e "\n${YELLOW}[4/5] Habilitando injeção de sidecar Istio no namespace ricxapp...${NC}"
kubectl label namespace ricxapp istio-injection=enabled --overwrite

# 5. Aguardar Rollout
echo -e "\n${YELLOW}[5/5] Aguardando inicialização do Kiali e Istio...${NC}"
kubectl rollout status deployment/istiod -n istio-system --timeout=120s
kubectl rollout status deployment/kiali -n istio-system --timeout=120s

# Reiniciar pods no namespace ricxapp para injetar proxy
kubectl delete pod -n ricxapp -l app=ricxapp-iqos-xapp-rdl 2>/dev/null || true

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}  Istio e Kiali instalados com SUCESSO!            ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "Para abrir o Kiali Dashboard, execute: ${YELLOW}make kiali-dashboard${NC}"
