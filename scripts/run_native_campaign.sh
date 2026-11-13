#!/usr/bin/env bash
# Campanha nativa (ns-3.48 + 5G-LENA v5.1, sem E2) ao vivo, seguida de análise, certificação e relatório.
# Mostra no terminal as linhas [RDL-ACT] (cada ação aplicada na RAN) e [RDL-KPI] (vazão e atraso por
# segundo simulado) de cada execução.
#
# Uso (Ubuntu do WSL):
#   bash scripts/run_native_campaign.sh                              # S0–S7 × B0–B3 × 1001–1005 (160 execuções)
#   bash scripts/run_native_campaign.sh --seeds 1001-1002 --jobs 1
#   bash scripts/run_native_campaign.sh --scenarios "G1" --baselines "B0 B3" --seeds 13001-13005 \
#     --sim-arg "--powerAllocation=used" --run-suffix U      # argumento extra do cenário; run_id nr_G1_B3U_seed...
# Pré-requisito: venv com as dependências (docs/04, seção 5.1) em ~/.venvs/xapp-rdl ou em $VENV.
# Retomável: execuções concluídas são puladas.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${VENV:-$HOME/.venvs/xapp-rdl}"
SEEDS="1001-1005"; JOBS=2; SCENARIOS="S0 S1 S2 S3 S4 S5 S6 S7"; BASELINES="B0 B1 B2 B3"
EXTRA=()
while [ $# -gt 0 ]; do
  case "$1" in
    --seeds) SEEDS="$2"; shift 2 ;;
    --jobs) JOBS="$2"; shift 2 ;;
    --scenarios) SCENARIOS="$2"; shift 2 ;;
    --baselines) BASELINES="$2"; shift 2 ;;
    --sim-arg) EXTRA+=("--sim-arg=$2"); shift 2 ;;
    --run-suffix) EXTRA+=("--run-suffix" "$2"); shift 2 ;;
    *) echo "opção desconhecida: $1" >&2; exit 64 ;;
  esac
done
# shellcheck disable=SC1091
source "$VENV/bin/activate" || { echo "venv não encontrado em $VENV (docs/04, seção 5.1)" >&2; exit 3; }
cd "$REPO"
say() { echo "[$(date +%H:%M:%S)] $*"; }
say "campanha nativa: cenários [$SCENARIOS] × baselines [$BASELINES] × sementes $SEEDS (jobs $JOBS) ${EXTRA[*]}"
# shellcheck disable=SC2086
python scripts/certification/run_conflict_campaign.py --scenarios $SCENARIOS --baselines $BASELINES \
  --seeds "$SEEDS" --jobs "$JOBS" "${EXTRA[@]}"
say "análise por cenário × baseline"
python scripts/certification/analyze_conflict_runs.py
say "certificação (G0 para a pilha nativa; G1–G4 vêm da bancada NORI)"
python scripts/certification/certify_chain.py | tail -9
say "relatório da campanha"
python scripts/certification/generate_campaign_report.py
