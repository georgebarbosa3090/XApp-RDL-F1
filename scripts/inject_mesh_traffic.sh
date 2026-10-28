#!/usr/bin/env bash
# ==============================================================================
# Script: inject_mesh_traffic.sh
# Finalidade: Injeta tráfego contínuo L7 (HTTP/Métricas) e L4 (TCP/RMR) em todas
#             as xApps no cluster K8s para visualização em tempo real no Kiali.
# ==============================================================================
set -e

NAMESPACE="ricxapp"
DURATION=${1:-300} # segundos (padrão 5 min)

echo "=============================================================================="
echo " [*] Iniciando Injeção de Tráfego Service Mesh (Istio / Kiali) - Duração: ${DURATION}s"
echo "=============================================================================="

# 1. Aplicar o Deployment do Gerador de Tráfego no Cluster se não existir
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
K8S_DIR="$ROOT_DIR/deploy/kubernetes"

if [ -f "$K8S_DIR/traffic-generator.yaml" ]; then
    echo "[+] Aplicando pod gerador de tráfego in-cluster..."
    kubectl apply -f "$K8S_DIR/traffic-generator.yaml" -n "$NAMESPACE"
fi

# 2. Injeção paralela via Port-Forward / kubectl exec local
echo "[+] Iniciando sondas diretas nas xApps..."
XAPP_PODS=$(kubectl get pods -n "$NAMESPACE" --no-headers -o custom-columns=":metadata.name" | grep -v "traffic-generator" || true)

if [ -z "$XAPP_PODS" ]; then
    echo "[!] Nenhum pod encontrado no namespace $NAMESPACE."
    exit 1
fi

echo "[[OK]] Pods ativos detectados: $(echo "$XAPP_PODS" | tr '\n' ' ')"

END_TIME=$((SECONDS + DURATION))
COUNT=0

while [ $SECONDS -lt $END_TIME ]; do
    for pod in $XAPP_PODS; do
        # Dispara requisições de probe HTTP para ativar telemetria Istio Envoy
        kubectl exec -n "$NAMESPACE" "$pod" -- python3 -c "
import urllib.request
for p in [8080, 8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088, 8089, 8090, 8091, 8092, 8093]:
    for path in ['/health', '/ready', '/metrics', '/']:
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{p}{path}', timeout=0.2)
        except Exception:
            pass
" 2>/dev/null || true
    done
    COUNT=$((COUNT + 1))
    if [ $((COUNT % 10)) -eq 0 ]; then
        echo " -> Ciclo de injeção $COUNT executado... (restam $((END_TIME - SECONDS))s)"
    fi
    sleep 1
done

echo "=============================================================================="
echo " [[OK]] Injeção de tráfego concluída. Verifique a aba 'Graph' no Kiali."
echo "=============================================================================="
