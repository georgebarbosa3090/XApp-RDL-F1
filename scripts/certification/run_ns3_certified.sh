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
#        --scenario scenario_rdl_direct_prb_conflict --seed 1001 --baseline B3 \
#        [--run-id nr_S1_B3_seed1001] [--action-schedule cronograma.csv] \
#        [--attach decision_log.json] [--extra-source HRDL_RUNTIME] \
#        [--e2-trace-dir /caminho/traços] [-- <args do cenário>]
#
# --action-schedule: cronograma de ações de controle (gerado pelo baseline) aplicado na
#   RAN pelo cenário via rdl-nr-common.h; é copiado para raw/ e entra nos hashes.
# --attach: arquivo adicional da execução (ex.: log de decisões do baseline) copiado para raw/.
# --extra-source: origem adicional declarada no manifesto (validada contra a política).
#
# Variáveis: NS3_DIR (padrão ~/ns3-oran-workspace/ns-3-oran)
# =============================================================================
set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-${HOME}/ns3-oran-workspace/ns-3-oran}"
SCENARIO="" SEED="" BASELINE="" RUN_ID="" E2_TRACE_DIR="" ACTION_SCHEDULE="" SCENARIO_ARGS=()
ATTACHMENTS=() EXTRA_SOURCES=() NO_BUILD=0

while [ $# -gt 0 ]; do
  case "$1" in
    --scenario) SCENARIO="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --baseline) BASELINE="$2"; shift 2 ;;
    --run-id) RUN_ID="$2"; shift 2 ;;
    --e2-trace-dir) E2_TRACE_DIR="$2"; shift 2 ;;
    --action-schedule) ACTION_SCHEDULE="$2"; shift 2 ;;
    --attach) ATTACHMENTS+=("$2"); shift 2 ;;
    --extra-source) EXTRA_SOURCES+=("$2"); shift 2 ;;
    --no-build) NO_BUILD=1; shift ;;
    --) shift; SCENARIO_ARGS=("$@"); break ;;
    *) echo "Argumento desconhecido: $1" >&2; exit 64 ;;
  esac
done

[ -n "$SCENARIO" ] && [ -n "$SEED" ] || { echo "Obrigatório: --scenario e --seed" >&2; exit 64; }
[[ "$SEED" =~ ^[0-9]+$ ]] || { echo "--seed deve ser inteiro" >&2; exit 64; }
[ -x "${NS3_DIR}/ns3" ] || { echo "ns-3 não encontrado em NS3_DIR=${NS3_DIR} (rode scripts/setup_ns3.sh)" >&2; exit 69; }
[ -z "$ACTION_SCHEDULE" ] || [ -f "$ACTION_SCHEDULE" ] || { echo "Cronograma não encontrado: $ACTION_SCHEDULE" >&2; exit 66; }
for f in "${ATTACHMENTS[@]}"; do [ -f "$f" ] || { echo "Anexo não encontrado: $f" >&2; exit 66; }; done
for src in "${EXTRA_SOURCES[@]}"; do
  awk '{sub(/\r$/, "")} /^publication_eligible_sources:/{f=1;next} /^[^ #]/{f=0} f' "${REPO_DIR}/reproducibility/provenance_policy.yaml" \
    | grep -qE "^  - ${src}\$" \
    || { echo "Origem não elegível na política: ${src}" >&2; exit 64; }
done

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
NS3_COMMIT="$(git -C "${NS3_DIR}" rev-parse HEAD 2>/dev/null || echo "")"
LENA_COMMIT="$(git -C "${LENA_DIR}" rev-parse HEAD 2>/dev/null || echo "")"
# Sem módulo NORI a pilha é ns-3 + 5G-LENA pura: nunca rotular como NORI.
BACKEND=$([ -n "$NORI_DIR" ] && echo NORI_NS3 || echo NS3_5GLENA)
SCENARIO_SRC="${REPO_DIR}/simulations/ns3/${SCENARIO}.cc"
SCRATCH_SRC="${NS3_DIR}/scratch/${SCENARIO}.cc"
# --no-build (campanhas paralelas): não recompila nem altera scratch/; exige que a fonte
# em scratch/ seja idêntica à do repositório e que o binário seja mais novo que ela.
if [ "$NO_BUILD" = 1 ]; then
  for f in "$SCENARIO_SRC" "${REPO_DIR}/simulations/ns3/"*.h; do
    [ -f "$f" ] || continue
    cmp -s "$f" "${NS3_DIR}/scratch/$(basename "$f")" \
      || { echo "scratch/ desatualizado para $(basename "$f"): recompile antes de usar --no-build" >&2; rm -rf "$RUN_DIR"; exit 65; }
  done
  BIN="$(ls "${NS3_DIR}"/build/scratch/ns3*-"${SCENARIO}"-* 2>/dev/null | head -1)"
  { [ -n "$BIN" ] && [ "$BIN" -nt "$SCRATCH_SRC" ]; } \
    || { echo "binário de ${SCENARIO} ausente ou mais antigo que a fonte: recompile" >&2; rm -rf "$RUN_DIR"; exit 65; }
fi
# Copia só o que mudou, para não invalidar binários de outras execuções em andamento
[ -f "$SCENARIO_SRC" ] && { cmp -s "$SCENARIO_SRC" "$SCRATCH_SRC" || cp -f "$SCENARIO_SRC" "$SCRATCH_SRC"; }
# Cabeçalhos comuns dos cenários (rede NR, atuação e KPIs)
for h in "${REPO_DIR}/simulations/ns3/"*.h; do
  [ -f "$h" ] && { cmp -s "$h" "${NS3_DIR}/scratch/$(basename "$h")" || cp -f "$h" "${NS3_DIR}/scratch/"; }
done
[ -f "$SCRATCH_SRC" ] || { echo "Cenário ${SCENARIO}.cc não encontrado" >&2; rm -rf "$RUN_DIR"; exit 66; }

# Espaço livre mínimo (MB) no disco das evidências e no temporário do simulador
MIN_FREE_MB="${MIN_FREE_MB:-1024}"
for target in "${RUN_DIR}" "${TMPDIR:-/tmp}"; do
  free_mb=$(df -Pm "$target" | awk 'NR==2 {print $4}')
  if [ "${free_mb:-0}" -lt "$MIN_FREE_MB" ]; then
    echo "Espaço insuficiente em ${target}: ${free_mb} MB livres (mínimo ${MIN_FREE_MB} MB)" >&2
    rm -rf "$RUN_DIR"; exit 75
  fi
done
WORK_DIR="$(mktemp -d)"
STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
# Os cenários do projeto chamam SeedManager::SetSeed/SetRun com os próprios argumentos
# (--seed/--run) depois de ler a linha de comando, o que anula --RngRun. Quando o cenário
# expõe --seed, a semente é passada por ele; caso contrário, por --RngRun.
if grep -qE 'AddValue *\( *"seed"' "$SCRATCH_SRC"; then
  RNG_ARGS="--seed=${SEED}"
else
  RNG_ARGS="--RngRun=${SEED}"
fi
SCHEDULE_ARG=""
SCHEDULE_SHA=""
if [ -n "$ACTION_SCHEDULE" ]; then
  cp -f "$ACTION_SCHEDULE" "${RUN_DIR}/raw/action_schedule.csv"
  SCHEDULE_ARG="--actionSchedule=${RUN_DIR}/raw/action_schedule.csv"
  SCHEDULE_SHA="$(sha256sum "${RUN_DIR}/raw/action_schedule.csv" | cut -d' ' -f1)"
fi
for f in "${ATTACHMENTS[@]}"; do cp -f "$f" "${RUN_DIR}/raw/"; done
SIM_ARGS="${RNG_ARGS} ${SCHEDULE_ARG} ${SCENARIO_ARGS[*]:-}"
CMD=(./ns3 run "scratch/${SCENARIO} ${SIM_ARGS}" --cwd "${WORK_DIR}")
[ "$NO_BUILD" = 1 ] && CMD+=(--no-build)
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
if [ "${#EXTRA_SOURCES[@]}" -gt 0 ] && [ "$SOURCES" != '[]' ]; then
  SOURCES="$(python3 -c 'import json,sys; s=json.loads(sys.argv[1]); s+= [x for x in sys.argv[2:] if x not in s]; print(json.dumps(s))' "$SOURCES" "${EXTRA_SOURCES[@]}")"
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
    "command": "cd ${NS3_DIR} && ./ns3 run 'scratch/${SCENARIO} ${SIM_ARGS}'",
    "rng_args": "${RNG_ARGS}",
    "action_schedule_sha256": "${SCHEDULE_SHA}" or None,
    "run_status": "${RUN_STATUS}",
    "exit_code": int("${EXIT_CODE}"),
    "started_at_utc": "${STARTED}",
    "finished_at_utc": "${FINISHED}",
    "ns3_version": "${NS3_VERSION}",
    "ns3_commit": "${NS3_COMMIT}" or None,
    "fiveg_lena_version": "${LENA_VERSION}",
    "nr_commit": "${LENA_COMMIT}" or None,
    "nori_commit": "${NORI_COMMIT}" or None,
    "repo_git_sha": out(["git", "-C", "${REPO_DIR}", "rev-parse", "--short=7", "HEAD"]),
    "scenario_sha256": out(["sha256sum", "${SCRATCH_SRC}"]).split(" ")[0],
    "support_files_sha256": {
        __import__("os").path.basename(h): out(["sha256sum", h]).split(" ")[0]
        for h in sorted(__import__("glob").glob("${NS3_DIR}/scratch/*.h"))
    },
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
