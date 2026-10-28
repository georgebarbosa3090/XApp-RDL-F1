#!/usr/bin/env bash
# ==============================================================================
# Script de Diagnóstico e Estado Completo do Cluster O-RAN K8s
# ==============================================================================
set -euo pipefail

export KUBECONFIG="/etc/rancher/k3s/k3s.yaml"

echo "================================================================================"
echo " ☸️ DIAGNÓSTICO INTEGRAL DO CLUSTER O-RAN K8S (k3s / Near-RT RIC / H-RDL)"
echo "================================================================================"

echo -e "\n[1] NÓS DO CLUSTER:"
kubectl get nodes -o wide

echo -e "\n[2] PODS DA PLATAFORMA (ricplt):"
kubectl get pods -n ricplt -o wide

echo -e "\n[3] PODS DAS XAPPS E H-RDL (ricxapp):"
kubectl get pods -n ricxapp -o wide

echo -e "\n[4] SERVIÇOS E ROTAS (ricplt / ricxapp):"
kubectl get svc -n ricplt
kubectl get svc -n ricxapp

echo -e "\n[5] LOGS DA XAPP H-RDL (Últimas 20 linhas):"
POD_RDL=$(kubectl get pods -n ricxapp -l app=ricxapp-iqos-xapp-rdl -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$POD_RDL" ]; then
    kubectl logs -n ricxapp "$POD_RDL" | tail -n 20 || true
else
    echo "[AVISO] Pod da xApp H-RDL não encontrado."
fi

echo -e "\n================================================================================"
echo " DIAGNÓSTICO CONCLUÍDO COM SUCESSO! [OK]"
echo "================================================================================"
