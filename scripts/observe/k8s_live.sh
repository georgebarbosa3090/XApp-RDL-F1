#!/usr/bin/env bash
# Aba Kubernetes: deployments, statefulsets e pods de ricplt, ricxapp e ricsim, ao vivo (a cada 2 s).
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
exec watch -t -n 2 'for ns in ricplt ricxapp ricsim; do echo "== $ns"; kubectl -n $ns get deploy,statefulset,pods -o wide 2>/dev/null | cut -c1-170; echo; done; free -m | head -2'
