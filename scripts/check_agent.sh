#!/bin/bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

echo "=== PODS IN CATTLE-SYSTEM ==="
kubectl get pods -n cattle-system -o wide

echo -e "\n=== CRICTL CONTAINERS ==="
k3s crictl ps

echo -e "\n=== CATTLE AGENT LOGS ==="
AGENT_CONTAINER=$(k3s crictl ps --name cattle-cluster-agent -q | head -n 1)
if [ -n "$AGENT_CONTAINER" ]; then
    k3s crictl logs --tail=50 "$AGENT_CONTAINER"
else
    echo "No cattle-cluster-agent container found in crictl."
fi

echo -e "\n=== AGENT ENVIRONMENT ==="
kubectl get deployment cattle-cluster-agent -n cattle-system -o yaml | grep -A 15 "env:"
