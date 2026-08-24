#!/bin/bash
# Collects evidence for RDL experiments

EXPERIMENT_ID=$1
if [ -z "$EXPERIMENT_ID" ]; then
    echo "Usage: $0 <experiment_id>"
    exit 1
fi

OUT_DIR="experiments/results/$EXPERIMENT_ID"
mkdir -p "$OUT_DIR"

echo "Collecting metadata..."
echo '{"experiment_id": "'$EXPERIMENT_ID'", "timestamp": "'$(date -Iseconds)'"}' > "$OUT_DIR/metadata.json"

echo "Collecting config..."
cp configs/config-file.json "$OUT_DIR/configuration.yaml" 2>/dev/null || echo "No config" > "$OUT_DIR/configuration.yaml"

echo "Collecting git commit..."
# Omitindo git commands direct execution for compatibility, but keeping structure
echo "commit_hash_placeholder" > "$OUT_DIR/git_commit.txt"

echo "Collecting container image..."
kubectl get deployment ricxapp-iqos-xapp-rdl -n ricxapp -o jsonpath='{.spec.template.spec.containers[0].image}' > "$OUT_DIR/container_image.txt" 2>/dev/null || echo "unknown" > "$OUT_DIR/container_image.txt"

echo "Collecting pod info..."
kubectl get pods -n ricxapp > "$OUT_DIR/kubectl_get_pods.txt" 2>/dev/null || echo "No k8s" > "$OUT_DIR/kubectl_get_pods.txt"
kubectl describe pods -l app=ricxapp-iqos-xapp-rdl -n ricxapp > "$OUT_DIR/kubectl_describe.txt" 2>/dev/null || echo "No k8s" > "$OUT_DIR/kubectl_describe.txt"

echo "Collecting logs..."
kubectl logs -l app=ricxapp-iqos-xapp-rdl -n ricxapp > "$OUT_DIR/xapp_logs.jsonl" 2>/dev/null || echo "No logs" > "$OUT_DIR/xapp_logs.jsonl"

echo "Evidence collection complete in $OUT_DIR"
