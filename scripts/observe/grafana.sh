#!/usr/bin/env bash
# Aba Grafana: port-forward do Grafana (namespace monitoring) para http://localhost:3000 (leitura anônima).
# O WSL2 encaminha o localhost para o Windows: abra http://localhost:3000 no navegador.
# Uso (Ubuntu do WSL): bash scripts/observe/grafana.sh     (admin: senha no Secret grafana, chave admin-password)
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
PORT="${GRAFANA_LOCAL_PORT:-3000}"
echo "Grafana em http://localhost:$PORT (dashboard 'xApp RDL — simulações'); Ctrl-C encerra"
while true; do
  kubectl -n monitoring port-forward svc/grafana "$PORT:80" --address 127.0.0.1
  sleep 2
done
