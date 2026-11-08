#!/usr/bin/env bash
# =============================================================================
# Executor de cenário ns-3 / 5G-LENA (pilha nativa) com captura de proveniência.
# A saída do simulador aparece AO VIVO no terminal e é gravada em logs/.
# Para cenários E2 com NORI use o chart Helm deploy/helm/nori-ns3 (run.sh no pod).
#
# Roda UM cenário com UMA semente e grava, em experiments/runs/<run_id>/, somente
# o que a execução realmente produziu:
#   execution_manifest.json  campos exigidos por reproducibility/provenance_policy.yaml
#   logs/stdout.log, logs/stderr.log
#   raw/                     FlowMonitor XML e traços E2 (.raw/.pcap) encontrados
#   hashes.sha256            SHA-256 de todos os arquivos (integridade, não prova de execução)
#
# Versões são lidas dos checkouts (git), nunca do lock: divergências ficam visíveis
# para o certificador. Nada é inventado: se a simulação falhar, run_status=FAILED.
#
# Uso (dentro do WSL/Linux):
#   bash scripts/certification/run_ns3_certified.sh \
#        --scenario scenario_rdl_closed_loop_nori --seed 1001 --baseline B3 \
#        [--run-id S8_B3_seed1001] [--e2-trace-dir /caminho/traços] [-- <args do cenário>]
#
# Variáveis: NS3_DIR (padrão ~/ns3-oran-workspace/ns-3-oran)
# =============================================================================
set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-${HOME}/ns3-oran-workspace/ns-3-oran}"
SCENARIO="" SEED="" BASELINE="" RUN_ID="" E2_TRACE_DIR="" SCENARIO_ARGS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --scenario) SCENARIO="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --baseline) BASELINE="$2"; shift 2 ;;
    --run-id) RUN_ID="$2"; shift 2 ;;
    --e2-trace-dir) E2_TRACE_DIR="$2"; shift 2 ;;
    --) shift; SCENARIO_ARGS=("$@"); break ;;
    *) echo "Argumento desconhecido: $1" >&2; exit 64 ;;
  esac
done

[ -n "$SCENARIO" ] && [ -n "$SEED" ] || { echo "Obrigatório: --scenario e --seed" >&2; exit 64; }
[[ "$SEED" =~ ^[0-9]+$ ]] || { echo "--seed deve ser inteiro" >&2; exit 64; }
[ -x "${NS3_DIR}/ns3" ] || { echo "ns-3 não encontrado em NS3_DIR=${NS3_DIR} (rode scripts/setup_ns3.sh)" >&2; exit 69; }

RUN_ID="${RUN_ID:-${SCENARIO}_${BASELINE:-NA}_seed${SEED}}"
RUN_DIR="${REPO_DIR}/experiments/runs/${RUN_ID}"
[ -e "$RUN_DIR" ] && { echo "Execução já existe: ${RUN_DIR} (não sobrescrevo evidência)" >&2; exit 73; }
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/raw"

git_rev() { git -C "$1" rev-parse --short=7 HEAD 2>/dev/null || echo ""; }
git_desc() { git -C "$1" describe --tags --always 2>/dev/null || echo ""; }

NS3_VERSION="$(cat "${NS3_DIR}/VERSION" 2>/dev/null || git_desc "${NS3_DIR}" | sed 's/^ns-//')"
LENA_DIR="${NS3_DIR}/contrib/nr"
NORI_DIR=""
for d in "${NS3_DIR}/contrib/nori" "${NS3_DIR}/contrib/oran"; do [ -d "$d" ] && NORI_DIR="$d" && break; done
LENA_VERSION="$(git_desc "${LENA_DIR}")"
NORI_COMMIT="$([ -n "$NORI_DIR" ] && git_rev "$NORI_DIR" || echo "")"
# Sem módulo NORI a pilha é ns-3 + 5G-LENA pura: nunca rotular como NORI.
BACKEND=$([ -n "$NORI_DIR" ] && echo NORI_NS3 || echo NS3_5GLENA)
SCENARIO_SRC="${REPO_DIR}/simulations/ns3/${SCENARIO}.cc"
SCRATCH_SRC="${NS3_DIR}/scratch/${SCENARIO}.cc"
[ -f "$SCENARIO_SRC" ] && cp -f "$SCENARIO_SRC" "$SCRATCH_SRC"
[ -f "$SCRATCH_SRC" ] || { echo "Cenário ${SCENARIO}.cc não encontrado" >&2; rm -rf "$RUN_DIR"; exit 66; }

WORK_DIR="$(mktemp -d)"
STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
CMD=(./ns3 run "scratch/${SCENARIO} --RngRun=${SEED} ${SCENARIO_ARGS[*]:-}" --cwd "${WORK_DIR}")
echo "=== [${STARTED}] ${SCENARIO} seed=${SEED} backend=${BACKEND} (saída ao vivo) ==="
# Saída ao vivo no terminal e, ao mesmo tempo, gravada como evidência.
( cd "${NS3_DIR}" && "${CMD[@]}" )   > >(tee "${RUN_DIR}/logs/stdout.log")   2> >(tee "${RUN_DIR}/logs/stderr.log" >&2)
EXIT_CODE=$?
sleep 0.2  # deixa os tee terminarem de gravar
FINISHED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Coleta apenas o que a execução gerou
find "${WORK_DIR}" -maxdepth 2 -type f \( -name '*.xml' -o -name '*.raw' -o -name '*.pcap' -o -name '*.txt' -o -name '*.csv' \) \
     -exec cp -f {} "${RUN_DIR}/raw/" \;
if [ -n "$E2_TRACE_DIR" ] && [ -d "$E2_TRACE_DIR" ]; then
  find "$E2_TRACE_DIR" -type f -newermt "$STARTED" \( -name '*.raw' -o -name '*.pcap' -o -name '*.pcapng' \) \
       -exec cp -f {} "${RUN_DIR}/raw/" \;
fi
rm -rf "${WORK_DIR}"

SOURCES='[]'
ls "${RUN_DIR}/raw/"*.xml >/dev/null 2>&1 && SOURCES='["NS3_FLOWMONITOR"]'
if [ "$BACKEND" = "NORI_NS3" ] && { ls "${RUN_DIR}/raw/"*.raw >/dev/null 2>&1 || ls "${RUN_DIR}/raw/"*.pcap* >/dev/null 2>&1; }; then
  SOURCES='["NS3_FLOWMONITOR", "NORI_E2"]'
fi
RUN_STATUS=$([ "$EXIT_CODE" -eq 0 ] && echo SUCCESS || echo FAILED)

python3 - "$RUN_DIR" <<PY
import json, sys, platform, subprocess
def out(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout.strip().splitlines()[0]
    except Exception:
        return ""
manifest = {
    "run_id": "${RUN_ID}",
    "source": ${SOURCES},
    "backend": "${BACKEND}",
    "scenario": "${SCENARIO}",
    "baseline": "${BASELINE}" or None,
    "seed": int("${SEED}"),
    "command": "cd ${NS3_DIR} && ./ns3 run 'scratch/${SCENARIO} --RngRun=${SEED} ${SCENARIO_ARGS[*]:-}'",
    "run_status": "${RUN_STATUS}",
    "exit_code": int("${EXIT_CODE}"),
    "started_at_utc": "${STARTED}",
    "finished_at_utc": "${FINISHED}",
    "ns3_version": "${NS3_VERSION}",
    "fiveg_lena_version": "${LENA_VERSION}",
    "nori_commit": "${NORI_COMMIT}" or None,
    "repo_git_sha": out(["git", "-C", "${REPO_DIR}", "rev-parse", "--short=7", "HEAD"]),
    "scenario_sha256": out(["sha256sum", "${SCRATCH_SRC}"]).split(" ")[0],
    "environment": {
        "os": out(["lsb_release", "-ds"]) or platform.platform(),
        "kernel": platform.release(),
        "compiler": out(["g++", "--version"]),
        "cmake": out(["cmake", "--version"]),
    },
    "publication_eligible": "${RUN_STATUS}" == "SUCCESS" and ${SOURCES} != [],
}
with open(sys.argv[1] + "/execution_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
PY

( cd "${RUN_DIR}" && find . -type f ! -name hashes.sha256 -printf '%P\n' | sort | xargs -r sha256sum > hashes.sha256 )

echo "=== [${FINISHED}] fim: run_id=${RUN_ID} status=${RUN_STATUS} exit=${EXIT_CODE} dir=${RUN_DIR} ==="
exit "$EXIT_CODE"
