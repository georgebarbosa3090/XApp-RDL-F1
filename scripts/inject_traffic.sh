#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}   Injetor Contínuo de Tráfego O-RAN (xApp & RIC)   ${NC}"
echo -e "${BLUE}====================================================${NC}"

NAMESPACE="ricxapp"
SVC_NAME="ricxapp-iqos-xapp-rdl-http"

# 1. Iniciar Port-Forward em segundo plano
echo -e "${YELLOW}[1/2] Estabelecendo canal de comunicação com a xApp RDL...${NC}"
kubectl port-forward -n ${NAMESPACE} svc/${SVC_NAME} 8080:8080 8081:8081 >/dev/null 2>&1 &
PF_PID=$!

# Função de limpeza ao encerrar com Ctrl+C
cleanup() {
    echo -e "\n${YELLOW}Encerrando injeção de tráfego...${NC}"
    kill $PF_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Aguardar estabilização do port-forward
sleep 2

echo -e "${GREEN}[2/2] Injeção de tráfego ATIVA!${NC}"
echo -e "${CYAN}Abra o Kiali em http://localhost:20001/kiali para ver o fluxo animado.${NC}"
echo -e "Pressione ${YELLOW}[Ctrl + C]${NC} a qualquer momento para parar.\n"

COUNT=1
while true; do
    # Enviar requisições HTTP para endpoints de saúde e métricas
    HTTP_CODE1=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null || echo "000")
    HTTP_CODE2=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ready 2>/dev/null || echo "000")
    HTTP_CODE3=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/metrics 2>/dev/null || echo "000")

    echo -ne " [Lote #$COUNT] Pacotes O-RAN enviados -> /health ($HTTP_CODE1) | /ready ($HTTP_CODE2) | /metrics ($HTTP_CODE3)\r"
    COUNT=$((COUNT + 1))
    sleep 0.5
done
