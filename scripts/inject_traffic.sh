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

# 1. Iniciar Port-Forwards em segundo plano para as 3 Reference xApps
echo -e "${YELLOW}[1/2] Estabelecendo canais de comunicação com as xApps O-RAN...${NC}"
kubectl port-forward -n ${NAMESPACE} svc/ricxapp-qos-xslice-http 8082:8082 >/dev/null 2>&1 &
PF_PID1=$!
kubectl port-forward -n ${NAMESPACE} svc/ricxapp-energy-saving-http 8084:8084 >/dev/null 2>&1 &
PF_PID2=$!
kubectl port-forward -n ${NAMESPACE} svc/ricxapp-traffic-steering-http 8086:8086 >/dev/null 2>&1 &
PF_PID3=$!
kubectl port-forward -n ${NAMESPACE} svc/ricxapp-iqos-xapp-rdl-http 8080:8080 8081:8081 >/dev/null 2>&1 &
PF_PID4=$!

# Função de limpeza ao encerrar com Ctrl+C
cleanup() {
    echo -e "\n${YELLOW}Encerrando injeção de tráfego...${NC}"
    kill $PF_PID1 $PF_PID2 $PF_PID3 $PF_PID4 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Aguardar estabilização do port-forward
sleep 2

echo -e "${GREEN}[2/2] Injeção de tráfego ATIVA no Service Mesh!${NC}"
echo -e "${CYAN}Abra o Kiali em http://localhost:20001/kiali para ver o grafo animado.${NC}"
echo -e "Pressione ${YELLOW}[Ctrl + C]${NC} a qualquer momento para parar.\n"

COUNT=1
while true; do
    # Enviar requisições HTTP para as 3 reference xApps
    CODE_QOS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/health 2>/dev/null || echo "000")
    CODE_ES=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8084/health 2>/dev/null || echo "000")
    CODE_TS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8086/health 2>/dev/null || echo "000")
    CODE_RDL=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null || echo "---")

    # Metrics
    curl -s http://localhost:8082/metrics >/dev/null 2>&1 || true
    curl -s http://localhost:8084/metrics >/dev/null 2>&1 || true
    curl -s http://localhost:8086/metrics >/dev/null 2>&1 || true

    echo -ne " [Lote #$COUNT] Pacotes -> QoS ($CODE_QOS) | Energy ($CODE_ES) | Traffic ($CODE_TS) | RDL ($CODE_RDL)\r"
    COUNT=$((COUNT + 1))
    sleep 0.2
done
