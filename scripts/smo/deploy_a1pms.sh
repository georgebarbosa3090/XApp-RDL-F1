#!/usr/bin/env bash
# Implanta o Non-RT RIC leve da bancada (A1-PMS do O-RAN SC) e registra os tipos de política
# da RDL no A1 Mediator do Near-RT RIC (doc 10 §3). Uso, no Ubuntu do WSL:
#   bash scripts/smo/deploy_a1pms.sh            # instala/atualiza e verifica
#   bash scripts/smo/deploy_a1pms.sh --uninstall
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
NS=nonrtric
RELEASE=a1pms
say() { echo "[$(date +%H:%M:%S)] $*"; }

if [ "${1:-}" = "--uninstall" ]; then
  helm uninstall "$RELEASE" -n "$NS" || true
  exit 0
fi

avail_mb=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
if [ "$avail_mb" -lt 900 ]; then
  echo "memória disponível ${avail_mb} MB < 900 MB: libere memória antes (achados 50–51)" >&2
  exit 3
fi
kubectl -n ricplt get svc service-ricplt-a1mediator-http >/dev/null \
  || { echo "A1 Mediator não encontrado no namespace ricplt (docs/04 §7)" >&2; exit 4; }

say "instalando o A1-PMS (namespace $NS)"
kubectl create namespace "$NS" --dry-run=client -o yaml | kubectl apply -f - >/dev/null
helm upgrade --install "$RELEASE" "$REPO/deploy/helm/a1pms" -n "$NS" --wait --timeout 10m

say "registrando os tipos de política no A1 Mediator (port-forward temporário)"
kubectl -n ricplt port-forward svc/service-ricplt-a1mediator-http 10000:10000 >/tmp/a1med-pf.log 2>&1 &
PF1=$!
kubectl -n "$NS" port-forward svc/"$RELEASE" 8081:8081 >/tmp/a1pms-pf.log 2>&1 &
PF2=$!
trap 'kill $PF1 $PF2 2>/dev/null || true' EXIT
sleep 3
PY="${VENV:-$HOME/.venvs/xapp-rdl}/bin/python"; [ -x "$PY" ] || PY=python3
"$PY" "$REPO/scripts/a1/register_policy_types.py" --a1-url http://127.0.0.1:10000

say "A1-PMS: RICs e tipos de política vistos (a sincronização com o RIC leva até ~30 s)"
for _ in $(seq 1 12); do
  types=$(curl -s http://127.0.0.1:8081/a1-policy/v2/policy-types || true)
  echo "$types" | grep -q 20001 && break
  sleep 5
done
curl -s http://127.0.0.1:8081/a1-policy/v2/rics; echo
echo "$types"; echo
