#!/usr/bin/env bash
# Traz uma execução NORI do pod para o repositório e prepara a certificação E2:
#   1. copia /workspace/runs/<run_id> para experiments/runs/<run_id> e confere hashes.sha256;
#   2. recorta os eventos da xApp kpm-probe no intervalo da execução para
#      experiments/xapp_logs/<run_id>/kpm_probe_events.jsonl (com hashes.sha256);
#   3. disseca o PCAP E2 (dissecador do projeto + tshark) em experiments/e2_dissection/<run_id>.
# Executar no Ubuntu do WSL, na raiz do repositório ou de qualquer lugar:
#   bash scripts/collect_nori_run.sh nori_kpm_flowmon_seed1_p1s
# Variáveis: TSHARK (executável; padrão: tshark do PATH ou ~/.local/tshark-4.2.2), KUBECONFIG.
set -euo pipefail
[ $# -eq 1 ] || { echo "Uso: $0 <run_id>" >&2; exit 64; }
RUN_ID="$1"
[[ "$RUN_ID" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "run_id inválido" >&2; exit 64; }
REPO="$(cd "$(dirname "$0")/.." && pwd)"
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
DEST="$REPO/experiments/runs/$RUN_ID"
XLOG="$REPO/experiments/xapp_logs/$RUN_ID"
say() { echo "[$(date +%H:%M:%S)] $*"; }

POD="$(kubectl -n ricsim get pod -l app.kubernetes.io/name=nori-ns3 -o jsonpath='{.items[0].metadata.name}')"
if [ -e "$DEST" ]; then
  say "experiments/runs/$RUN_ID já existe: não sobrescrevo (só refaço o recorte da xApp e a dissecação)"
else
  say "copiando $POD:/workspace/runs/$RUN_ID"
  kubectl -n ricsim cp "$POD:/workspace/runs/$RUN_ID" "$DEST" >/dev/null
fi
( cd "$DEST" && sha256sum --quiet -c hashes.sha256 ) && say "hashes.sha256 conferido ($(wc -l < "$DEST/hashes.sha256") arquivos)"

if kubectl -n ricxapp get deploy kpm-probe >/dev/null 2>&1; then
  mkdir -p "$XLOG"
  kubectl -n ricxapp exec deploy/kpm-probe -- cat /data/logs/kpm_probe_events.jsonl \
    | python3 -c '
import json, sys
from datetime import datetime, timedelta
m = json.load(open(sys.argv[1]))
parse = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
start, end = parse(m["started_at_utc"]), parse(m["finished_at_utc"]) + timedelta(seconds=5)
n = 0
for line in sys.stdin:
    try:
        ev = json.loads(line)
    except ValueError:
        continue
    if start <= parse(ev["t_utc"]) <= end:
        sys.stdout.write(line); n += 1
print("%d eventos da xApp em [%s, %s + 5 s]" % (n, m["started_at_utc"], m["finished_at_utc"]), file=sys.stderr)
' "$DEST/execution_manifest.json" > "$XLOG/kpm_probe_events.jsonl"
  ( cd "$XLOG" && sha256sum kpm_probe_events.jsonl > hashes.sha256 )
else
  say "xApp kpm-probe não implantada: sem recorte de eventos"
fi

TSHARK="${TSHARK:-$(command -v tshark || echo "$HOME/.local/tshark-4.2.2/root/usr/bin/tshark")}"
[ -x "$TSHARK" ] || { say "tshark não encontrado ($TSHARK): a dissecação fica sem confirmação independente"; TSHARK=""; }
if [ -n "$TSHARK" ]; then TS_ARGS=(--tshark "$TSHARK"); else TS_ARGS=(--no-tshark); fi
python3 "$REPO/scripts/certification/e2_pcap_dissect.py" --run "$RUN_ID" "${TS_ARGS[@]}" || true

# Efeito do Control na RAN (série do FlowMonitor por fatia); requer asn1tools (codec E2SM v3)
if [ -f "$DEST/raw/slice_series.csv" ]; then
  PY="${PYTHON:-$HOME/.venvs/xapp-rdl/bin/python}"
  [ -x "$PY" ] || PY=python3
  # Regra calibrada (pré-registros docs/07_*): usa a calibração, exceto nas próprias execuções de calibração
  CAL="${CALIBRATION:-$REPO/experiments/calibration/slice_capacity_v3.json}"   # desenho v3 (docs/07_preregistro_fase4_v3.md)
  CURVE="${CURVE:-$REPO/experiments/calibration/slice_cap_curve_v5.json}"   # desenho v5 (docs/07_preregistro_fase4_v5.md)
  CAL_ARGS=()
  if [[ "$RUN_ID" == nori_cal* || "$RUN_ID" == nori_curve* ]]; then
    :   # execuções de calibração/curva: sem previsão
  elif [ -f "$CURVE" ]; then
    CAL_ARGS=(--curve "$CURVE")
  elif [ -f "$CAL" ]; then
    CAL_ARGS=(--calibration "$CAL")
  fi
  ( cd "$REPO" && "$PY" scripts/certification/slice_effect.py --run "$RUN_ID" "${CAL_ARGS[@]}" ) || true
fi
