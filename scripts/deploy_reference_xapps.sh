#!/usr/bin/env bash
# ==============================================================================
# Script: deploy_reference_xapps.sh
# Projeto: xApp RDL - Orquestracao de Reference xApps (5G, 5GA, 6G)
# Finalidade: Implanta ou atualiza as Reference xApps no namespace ricxapp do K8s
# ==============================================================================
set -euo pipefail

NAMESPACE="ricxapp"

echo "=============================================================================="
echo " [*] Iniciando Implantacao Automatizada das Reference xApps no K8s ($NAMESPACE)"
echo "=============================================================================="

# 1. Garantir namespace
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# 2. Se existirem os manifestos em deploy/kubernetes, aplica-os prioritariamente:
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
K8S_DIR="$ROOT_DIR/deploy/kubernetes"

if [ -f "$K8S_DIR/xapp-qos-xslice.yaml" ]; then
    echo "[+] Aplicando manifestos declarativos de deploy/kubernetes..."
    kubectl apply -f "$K8S_DIR/xapp-qos-xslice.yaml" -n "$NAMESPACE"
    kubectl apply -f "$K8S_DIR/xapp-energy-saving.yaml" -n "$NAMESPACE"
    kubectl apply -f "$K8S_DIR/xapp-traffic-steering.yaml" -n "$NAMESPACE"
fi

# 3. Provisiona xApps complementares (Beamformer, ISAC Radar, Rogue Stress) de forma limpa e resiliente
declare -A EXTRA_XAPPS=(
    ["ricxapp-beamformer"]="8088:8089:4565"
    ["ricxapp-isac-radar"]="8090:8091:4566"
    ["ricxapp-rogue-stress"]="8092:8093:4567"
)

for APP_NAME in "${!EXTRA_XAPPS[@]}"; do
    IFS=":" read -r HTTP_PORT METRICS_PORT RMR_PORT <<< "${EXTRA_XAPPS[$APP_NAME]}"
    echo "[+] Provisionando Pod complementar: $APP_NAME (HTTP: $HTTP_PORT, Metrics: $METRICS_PORT, RMR: $RMR_PORT)..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${APP_NAME}
  namespace: ${NAMESPACE}
  labels:
    app: ${APP_NAME}
    tier: reference-xapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${APP_NAME}
  template:
    metadata:
      labels:
        app: ${APP_NAME}
        tier: reference-xapp
    spec:
      containers:
      - name: ${APP_NAME}
        image: python:3.11-slim
        imagePullPolicy: IfNotPresent
        command: ["python", "-u", "-c"]
        args:
          - |
            import http.server, socketserver, os
            port = int(os.environ.get("HTTP_PORT", 8080))
            app_name = os.environ.get("APP_NAME", "xapp")
            class StubHandler(http.server.SimpleHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(f'{{"status":"UP","app":"{app_name}"}}\n'.encode("utf-8"))
                def log_message(self, format, *args):
                    pass
            print(f"[*] {app_name} online on port {port}")
            with socketserver.TCPServer(("", port), StubHandler) as httpd:
                httpd.serve_forever()
        env:
        - name: APP_NAME
          value: "${APP_NAME}"
        - name: HTTP_PORT
          value: "${HTTP_PORT}"
        - name: METRICS_PORT
          value: "${METRICS_PORT}"
        - name: RMR_PORT
          value: "${RMR_PORT}"
        ports:
        - name: http
          containerPort: ${HTTP_PORT}
        - name: metrics
          containerPort: ${METRICS_PORT}
        - name: rmr
          containerPort: ${RMR_PORT}
        resources:
          limits:
            cpu: "200m"
            memory: "256Mi"
          requests:
            cpu: "50m"
            memory: "64Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: ${APP_NAME}
  namespace: ${NAMESPACE}
spec:
  selector:
    app: ${APP_NAME}
  ports:
  - name: http
    port: ${HTTP_PORT}
    targetPort: ${HTTP_PORT}
  - name: metrics
    port: ${METRICS_PORT}
    targetPort: ${METRICS_PORT}
EOF
done

echo "[✓] Todas as Reference xApps foram enviadas ao cluster. Verificando Pods..."
kubectl get pods -n "$NAMESPACE" -o wide
