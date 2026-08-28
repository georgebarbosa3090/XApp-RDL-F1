#!/bin/bash
# ==============================================================================
# Script de Validação e Smoke Test das 3 Reference xApps (e RDL)
# ==============================================================================
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

NAMESPACE="ricxapp"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}   Validação e Smoke Test das xApps O-RAN no namespace '${NAMESPACE}'   ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. Checar Pods no namespace
echo -e "\n${YELLOW}[1/4] Listando Pods em execucao no namespace ${NAMESPACE}...${NC}"
kubectl get pods -n ${NAMESPACE} -o wide

# 2. Testar xSlice (QoS/Slicing) - Porta 8082 / 8083
echo -e "\n${YELLOW}[2/4] Validando 1. xSlice QoS xApp (peihaoY/xslice-oran)...${NC}"
if kubectl get deployment ricxapp-qos-xslice -n ${NAMESPACE} &>/dev/null; then
    kubectl port-forward -n ${NAMESPACE} svc/ricxapp-qos-xslice-http 18082:8082 18083:8083 >/dev/null 2>&1 &
    PF1_PID=$!
    sleep 2
    echo -n "  -> Healthcheck /health: "
    curl -s http://localhost:18082/health || echo "FAIL"
    echo -n "  -> Proposta Recente /proposals/latest: "
    curl -s http://localhost:18082/proposals/latest || echo "FAIL"
    echo -n "  -> Metricas Prometheus (xslice_): "
    curl -s http://localhost:18083/metrics | grep -E "xslice_" | head -n 2 || echo "Nenhuma metrica ainda"
    kill $PF1_PID 2>/dev/null || true
else
    echo -e "${RED}  -> ricxapp-qos-xslice nao encontrado no cluster.${NC}"
fi

# 3. Testar Energy Saving (Orange/FlexRIC) - Porta 8084 / 8085
echo -e "\n${YELLOW}[3/4] Validando 2. Energy Saving xApp (Orange-OpenSource/ns-O-RAN-flexric)...${NC}"
if kubectl get deployment ricxapp-energy-saving -n ${NAMESPACE} &>/dev/null; then
    kubectl port-forward -n ${NAMESPACE} svc/ricxapp-energy-saving-http 18084:8084 18085:8085 >/dev/null 2>&1 &
    PF2_PID=$!
    sleep 2
    echo -n "  -> Healthcheck /health: "
    curl -s http://localhost:18084/health || echo "FAIL"
    echo -n "  -> Proposta Recente /proposals/latest: "
    curl -s http://localhost:18084/proposals/latest || echo "FAIL"
    echo -n "  -> Metricas Prometheus (es_): "
    curl -s http://localhost:18085/metrics | grep -E "es_" | head -n 2 || echo "Nenhuma metrica ainda"
    kill $PF2_PID 2>/dev/null || true
else
    echo -e "${RED}  -> ricxapp-energy-saving nao encontrado no cluster.${NC}"
fi

# 4. Testar Traffic Steering (O-RAN SC) - Porta 8086 / 8087
echo -e "\n${YELLOW}[4/4] Validando 3. Traffic Steering xApp (o-ran-sc/ric-app-ts)...${NC}"
if kubectl get deployment ricxapp-traffic-steering -n ${NAMESPACE} &>/dev/null; then
    kubectl port-forward -n ${NAMESPACE} svc/ricxapp-traffic-steering-http 18086:8086 18087:8087 >/dev/null 2>&1 &
    PF3_PID=$!
    sleep 2
    echo -n "  -> Healthcheck /health: "
    curl -s http://localhost:18086/health || echo "FAIL"
    echo -n "  -> Proposta Recente /proposals/latest: "
    curl -s http://localhost:18086/proposals/latest || echo "FAIL"
    echo -n "  -> Metricas Prometheus (ts_): "
    curl -s http://localhost:18087/metrics | grep -E "ts_" | head -n 2 || echo "Nenhuma metrica ainda"
    kill $PF3_PID 2>/dev/null || true
else
    echo -e "${RED}  -> ricxapp-traffic-steering nao encontrado no cluster.${NC}"
fi

# 5. Opcional: Validar RDL se presente
if kubectl get deployment ricxapp-iqos-xapp-rdl -n ${NAMESPACE} &>/dev/null; then
    echo -e "\n${CYAN}[EXTRA] Validando 4. xApp RDL (Resource and Decision Layer - Fase 1)...${NC}"
    kubectl port-forward -n ${NAMESPACE} svc/ricxapp-iqos-xapp-rdl-http 18080:8080 18081:8081 >/dev/null 2>&1 &
    PF4_PID=$!
    sleep 2
    echo -n "  -> Healthcheck /health: "
    curl -s http://localhost:18080/health || echo "FAIL"
    echo -n "  -> Metricas Prometheus (rdl_): "
    curl -s http://localhost:18081/metrics | grep -E "rdl_" | head -n 2 || echo "Nenhuma metrica ainda"
    kill $PF4_PID 2>/dev/null || true
fi

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}   Verificação Concluída com SUCESSO!                                 ${NC}"
echo -e "${GREEN}======================================================================${NC}"
