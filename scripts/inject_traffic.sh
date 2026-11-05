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

# 1. Limpar port-forwards anteriores que possam ter ficado orfaos
pkill -f "kubectl port-forward -n ${NAMESPACE}" 2>/dev/null || true
sleep 1

# Garantir que os manifests das reference xApps estejam aplicados no cluster
kubectl apply -f deploy/kubernetes/xapp-qos-xslice.yaml \
              -f deploy/kubernetes/xapp-energy-saving.yaml \
              -f deploy/kubernetes/xapp-traffic-steering.yaml >/dev/null 2>&1 || true

# 2. Iniciar Port-Forwards em segundo plano para as xApps
echo -e "${YELLOW}[1/2] Estabelecendo canais de comunicação com as xApps O-RAN...${NC}"
kubectl port-forward -n ${NAMESPACE} svc/ricxapp-qos-xslice-http 8082:8082 >/dev/null 2>&1 &
PF_PID1=$!
kubectl port-forward -n ${NAMESPACE} svc/ricxapp-energy-saving-http 8084:8084 >/dev/null 2>&1 &
PF_PID2=$!
kubectl port-forward -n ${NAMESPACE} svc/ricxapp-traffic-steering-http 8086:8086 >/dev/null 2>&1 &
PF_PID3=$!
kubectl port-forward -n ${NAMESPACE} svc/ricxapp-iqos-xapp-rdl-http 8080:8080 >/dev/null 2>&1 &
PF_PID4=$!

# Função de limpeza ao encerrar com Ctrl+C
cleanup() {
    echo -e "\n${YELLOW}Encerrando injeção de tráfego...${NC}"
    kill $PF_PID1 $PF_PID2 $PF_PID3 $PF_PID4 2>/dev/null || true
    pkill -f "kubectl port-forward -n ${NAMESPACE}" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Aguardar estabilização do port-forward
sleep 2

echo -e "${GREEN}[2/2] Injeção de tráfego ATIVA no Service Mesh!${NC}"
echo -e "${CYAN}Abra o Kiali em http://localhost:20001/kiali para ver o grafo animado.${NC}"
echo -e "Pressione ${YELLOW}[Ctrl + C]${NC} a qualquer momento para parar.\n"

query_status() {
    local url="$1"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 0.5 "$url" 2>/dev/null) || true
    if [ -z "$code" ] || [ "$code" = "000" ]; then
        echo "---"
    else
        echo "$code"
    fi
}

COUNT=1
while true; do
    CODE_QOS=$(query_status "http://localhost:8082/health")
    CODE_ES=$(query_status "http://localhost:8084/health")
    CODE_TS=$(query_status "http://localhost:8086/health")
    CODE_RDL=$(query_status "http://localhost:8080/health")

    # Metrics
    curl -s --connect-timeout 0.3 http://localhost:8082/metrics >/dev/null 2>&1 || true
    curl -s --connect-timeout 0.3 http://localhost:8084/metrics >/dev/null 2>&1 || true
    curl -s --connect-timeout 0.3 http://localhost:8086/metrics >/dev/null 2>&1 || true

    echo -ne " [Lote #$COUNT] Pacotes -> QoS ($CODE_QOS) | Energy ($CODE_ES) | Traffic ($CODE_TS) | RDL ($CODE_RDL)\r"
    COUNT=$((COUNT + 1))
    sleep 0.2
done
