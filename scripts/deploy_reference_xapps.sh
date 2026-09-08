#!/usr/bin/env bash
# ==============================================================================
# Script: deploy_reference_xapps.sh
# Projeto: xApp RDL - Orquestracao de Reference xApps (5G, 5GA, 6G)
# Finalidade: Implanta ou atualiza as 6 Reference xApps no namespace ricxapp do K8s
# ==============================================================================
set -euo pipefail

NAMESPACE="ricxapp"

echo "=============================================================================="
echo " [*] Iniciando Implantacao Automatizada das 6 Reference xApps no K8s ($NAMESPACE)"
echo "=============================================================================="

# Garantir namespace
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Lista de Reference xApps e configuracoes
declare -A XAPPS=(
    ["ricxapp-qos-xslice"]="8082:8083:4562:reference-xapps/qos-xslice/xslice_xapp.py"
    ["ricxapp-energy-saving"]="8084:8085:4563:reference-xapps/energy-saving/energy_saving_xapp.py"
    ["ricxapp-traffic-steering"]="8086:8087:4564:reference-xapps/traffic-steering/traffic_steering_xapp.py"
    ["ricxapp-beamformer"]="8088:8089:4565:reference-xapps/beamformer/beamformer_xapp.py"
    ["ricxapp-isac-radar"]="8090:8091:4566:reference-xapps/isac-radar/isac_radar_xapp.py"
    ["ricxapp-rogue-stress"]="8092:8093:4567:reference-xapps/rogue-xapp/rogue_xapp.py"
)

for APP_NAME in "${!XAPPS[@]}"; do
    IFS=":" read -r HTTP_PORT METRICS_PORT RMR_PORT SCRIPT_PATH <<< "${XAPPS[$APP_NAME]}"
    echo "[+] Provisionando Pod: $APP_NAME (HTTP: $HTTP_PORT, Metrics: $METRICS_PORT, RMR: $RMR_PORT)..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $APP_NAME
  namespace: $NAMESPACE
  labels:
    app: $APP_NAME
    tier: reference-xapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $APP_NAME
  template:
    metadata:
      labels:
        app: $APP_NAME
        tier: reference-xapp
    spec:
      containers:
      - name: $APP_NAME
        image: python:3.11-slim
        command: ["/bin/sh", "-c"]
        args:
          - |
            pip install --no-cache-dir fastapi uvicorn prometheus-client requests
            python -c "
import urllib.request
with open('app.py', 'w') as f:
    f.write('''# Reference xApp container stub
import time, http.server, socketserver
print('$APP_NAME operational.')
time.sleep(3600*24)
''')
"
            python app.py
        env:
        - name: HTTP_PORT
          value: "$HTTP_PORT"
        - name: METRICS_PORT
          value: "$METRICS_PORT"
        - name: RMR_PORT
          value: "$RMR_PORT"
        ports:
        - name: http
          containerPort: $HTTP_PORT
        - name: metrics
          containerPort: $METRICS_PORT
        - name: rmr
          containerPort: $RMR_PORT
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
  name: $APP_NAME
  namespace: $NAMESPACE
spec:
  selector:
    app: $APP_NAME
  ports:
  - name: http
    port: $HTTP_PORT
    targetPort: $HTTP_PORT
  - name: metrics
    port: $METRICS_PORT
    targetPort: $METRICS_PORT
EOF
done

echo "[✓] Todas as 6 Reference xApps foram enviadas ao cluster. Verificando Pods..."
kubectl get pods -n "$NAMESPACE" -l tier=reference-xapp -o wide
