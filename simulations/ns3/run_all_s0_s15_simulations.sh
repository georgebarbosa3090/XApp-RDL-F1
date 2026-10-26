#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RESULTS_DIR="${BASE_DIR}/experiments/results/ns3_runs"

declare -A SCENARIO_MAP=(
    ["s0"]="scenario_rdl_no_conflict"
    ["s1"]="scenario_rdl_direct_prb_conflict"
    ["s2"]="scenario_rdl_energy_vs_qos"
    ["s3"]="scenario_rdl_tvs_conflict"
    ["s4"]="scenario_rdl_ts_vs_energy"
    ["s5"]="scenario_rdl_temporal_pingpong"
    ["s6"]="scenario_rdl_conflict_storm"
    ["s7"]="scenario_rdl_fault_injection"
    ["s8"]="scenario_rdl_closed_loop_nori"
    ["s9"]="scenario_rdl_s9_ntn_orbital_handover"
    ["s10"]="scenario_rdl_s10_uav_swarm_battery"
    ["s11"]="scenario_rdl_s11_v2x_highway_platooning"
    ["s12"]="scenario_rdl_s12_iiot_zero_jitter_slicing"
    ["s13"]="scenario_rdl_s13_sagin_disaster_rescue"
    ["s14"]="scenario_rdl_s14_isac_radar_comm"
    ["s15"]="scenario_rdl_s15_rogue_ntn_feeder_hijacking"
)

FORCE="${FORCE:-false}"
ARGS=()
for arg in "$@"; do
    if [[ "$arg" == "--force" || "$arg" == "-f" ]]; then
        FORCE=true
    else
        ARGS+=("$arg")
    fi
done

TARGET="${ARGS[0]:-all}"
TARGET_LOWER="$(echo "${TARGET}" | tr '[:upper:]' '[:lower:]')"
SCENARIOS=()

case "${TARGET_LOWER}" in
    all)
        for scenario in "${SCENARIO_MAP[@]}"; do SCENARIOS+=("${scenario}"); done
        ;;
    5g)
        for id in s0 s1 s2 s3 s4 s5 s6 s7 s8; do SCENARIOS+=("${SCENARIO_MAP[$id]}"); done
        ;;
    6g)
        for id in s9 s10 s11 s12 s13 s14 s15; do SCENARIOS+=("${SCENARIO_MAP[$id]}"); done
        ;;
    s[0-9]|s1[0-5])
        if [[ -z "${SCENARIO_MAP[$TARGET_LOWER]:-}" ]]; then
            echo "[ERROR] Cenário desconhecido: ${TARGET}" >&2
            exit 2
        fi
        SCENARIOS+=("${SCENARIO_MAP[$TARGET_LOWER]}")
        ;;
    *)
        SCENARIOS+=("${TARGET}")
        ;;
esac

for scenario in "${SCENARIOS[@]}"; do
    if [[ "${scenario}" == "scenario_rdl_closed_loop_nori" ]]; then
        echo "[ERROR] S8 não implementa o controle E2SM-RC causal; não pode ser executado/rotulado como closed loop." >&2
        exit 2
    fi
done

POSSIBLE_NS3_DIRS=(
    "${NS3_DIR:-}"
    "${HOME:-}/ns3-oran-workspace/ns-3-oran"
    "/opt/ns-3.48/ns-3.48"
    "/opt/ns-allinone-3.48/ns-3.48"
)
ACTIVE_NS3_DIR=""
for candidate in "${POSSIBLE_NS3_DIRS[@]}"; do
    if [[ -n "${candidate}" && -f "${candidate}/ns3" ]]; then
        ACTIVE_NS3_DIR="${candidate}"
        break
    fi
done

if [[ -z "${ACTIVE_NS3_DIR}" ]]; then
    echo "[ERROR] ns-3 não encontrado. Defina NS3_DIR para um checkout ns-3 configurado com 5G-LENA." >&2
    exit 2
fi

if ! "${ACTIVE_NS3_DIR}/ns3" show config 2>&1 | grep -qi 'nr'; then
    echo "[ERROR] O checkout encontrado não declara o módulo NR/5G-LENA na configuração ns-3." >&2
    exit 2
fi

mkdir -p "${RESULTS_DIR}"
for scenario in "${SCENARIOS[@]}"; do
    source_file="${SCRIPT_DIR}/${scenario}.cc"
    if [[ ! -f "${source_file}" ]]; then
        echo "[ERROR] Arquivo de cenário ausente: ${source_file}" >&2
        exit 2
    fi

    run_id="$(date -u +%Y%m%dT%H%M%SZ)_${scenario}_$$"
    run_dir="${RESULTS_DIR}/${run_id}"
    if ! mkdir "${run_dir}"; then
        echo "[ERROR] Diretório de execução já existe: ${run_dir}" >&2
        exit 1
    fi

    scratch_file="${ACTIVE_NS3_DIR}/scratch/${scenario}.cc"
    if [[ -e "${scratch_file}" ]]; then
        if [[ "${FORCE}" == "true" || "${OVERWRITE_SCRATCH:-false}" == "true" ]]; then
            echo "[WARN] Sobrescrevendo arquivo scratch preexistente: ${scratch_file}"
        else
            echo "[ERROR] Arquivo scratch preexistente não será sobrescrito: ${scratch_file} (use --force ou FORCE=true)" >&2
            exit 2
        fi
    fi
    cp "${source_file}" "${scratch_file}"
    trap 'rm -f -- "${scratch_file}"' EXIT

    flowmonitor_file="${ACTIVE_NS3_DIR}/flowmonitor_closed_loop_results.xml"
    if [[ -e "${flowmonitor_file}" ]]; then
        if [[ "${FORCE}" == "true" || "${OVERWRITE_SCRATCH:-false}" == "true" ]]; then
            rm -f "${flowmonitor_file}"
        else
            echo "[ERROR] FlowMonitor preexistente não será sobrescrito: ${flowmonitor_file} (use --force ou FORCE=true)" >&2
            exit 2
        fi
    fi

    echo "[INFO] Compilando e executando ${scenario} com ns-3/5G-LENA; resultados em ${run_dir}"
    (
        cd "${ACTIVE_NS3_DIR}"
        ./ns3 build "${scenario}"
        ./ns3 run "${scenario} --simTime=10.0"
    ) >"${run_dir}/execution.log" 2>&1 || {
        echo "[ERROR] Build/execução de ${scenario} falhou. Consulte ${run_dir}/execution.log." >&2
        exit 1
    }
    rm -f -- "${scratch_file}"
    trap - EXIT

    if [[ ! -s "${flowmonitor_file}" ]]; then
        echo "[ERROR] Execução terminou sem FlowMonitor XML não vazio: ${flowmonitor_file}" >&2
        exit 1
    fi
    mv "${flowmonitor_file}" "${run_dir}/flowmonitor.xml"
    echo "[PASS] Execução ns-3 concluída e FlowMonitor preservado; proveniência científica ainda exige manifesto válido e auditoria."
done
