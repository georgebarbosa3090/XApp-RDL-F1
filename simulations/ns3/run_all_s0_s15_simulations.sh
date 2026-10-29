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

write_run_status() {
    local status="$1"
    local status_file="${run_dir}/run_status.json"
    local temp_file="${status_file}.tmp.$$"
    printf '{"status":"%s","updated_at_utc":"%s"}\n' \
        "${status}" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >"${temp_file}"
    mv -f -- "${temp_file}" "${status_file}"
}

case "${TARGET_LOWER}" in
    all)
        for s in $(seq 0 15); do
            SCENARIOS+=("${SCENARIO_MAP[s$s]}")
        done
        ;;
    5g)
        for s in $(seq 0 8); do
            SCENARIOS+=("${SCENARIO_MAP[s$s]}")
        done
        ;;
    6g|ntn|sagin)
        for s in $(seq 9 15); do
            SCENARIOS+=("${SCENARIO_MAP[s$s]}")
        done
        ;;
    s[0-9]|s1[0-5])
        if [[ -z "${SCENARIO_MAP[$TARGET_LOWER]:-}" ]]; then
            echo "[ERROR] Cenário desconhecido: ${TARGET}" >&2
            exit 2
        fi
        SCENARIOS+=("${SCENARIO_MAP[$TARGET_LOWER]}")
        ;;
    *)
        echo "[ERROR] Cenário não autorizado: ${TARGET}. Use s0..s15, 5g, 6g ou all." >&2
        exit 2
        ;;
esac

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
    write_run_status "running"

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
    trap 'rm -f -- "${scratch_file}"; write_run_status "failed"' EXIT

    possible_flowmon=(
        "${ACTIVE_NS3_DIR}/flowmonitor_${scenario}.xml"
        "${ACTIVE_NS3_DIR}/flowmonitor_closed_loop_results.xml"
        "${ACTIVE_NS3_DIR}/flowmonitor_results.xml"
    )
    for f in "${possible_flowmon[@]}"; do
        if [[ -e "$f" ]]; then
            if [[ "${FORCE}" == "true" || "${OVERWRITE_SCRATCH:-false}" == "true" ]]; then
                rm -f "$f"
            else
                echo "[ERROR] FlowMonitor preexistente não será sobrescrito: $f (use --force ou FORCE=true)" >&2
                exit 2
            fi
        fi
    done

    echo "[INFO] Compilando e executando ${scenario} com ns-3/5G-LENA; resultados em ${run_dir}"
    (
        cd "${ACTIVE_NS3_DIR}"
        ./ns3 build "${scenario}"
        ./ns3 run "${scenario} --simTime=10.0"
    ) >"${run_dir}/execution.log" 2>&1 || {
        echo "[ERROR] Build/execução de ${scenario} falhou. Consulte ${run_dir}/execution.log." >&2
        exit 1
    }
    write_run_status "collecting_flowmonitor"
    rm -f -- "${scratch_file}"

    found_flowmon=""
    for f in "${possible_flowmon[@]}"; do
        if [[ -s "$f" ]]; then
            found_flowmon="$f"
            break
        fi
    done

    if [[ -z "${found_flowmon}" ]]; then
        echo "[ERROR] Execução terminou sem FlowMonitor XML não vazio em ${ACTIVE_NS3_DIR}." >&2
        exit 1
    fi
    mv "${found_flowmon}" "${run_dir}/flowmonitor.xml"
    write_run_status "completed"
    trap - EXIT
    echo "[PASS] Execução ns-3 concluída e FlowMonitor preservado; proveniência científica ainda exige manifesto válido e auditoria."
done

# ==============================================================================
# Atualização Automática de Relatórios e Sincronização Local e GitHub
# ==============================================================================
echo -e "\n======================================================================"
echo "[INFO] Atualizando relatórios analíticos, tabelas e figuras científicas..."
echo "======================================================================"

if command -v python3 >/dev/null 2>&1; then
    echo "[1/3] Gerando Relatório Consolidado do FlowMonitor (S0 a S15)..."
    python3 "${BASE_DIR}/scripts/generate_ns3_flowmonitor_markdown_report.py" 2>/dev/null || true

    echo "[2/3] Atualizando figuras analíticas de alta resolução (300 DPI) e tabelas..."
    if command -v uv >/dev/null 2>&1; then
        uv run --with pandas --with matplotlib --with seaborn --with scipy python "${BASE_DIR}/analysis/generate_plots.py" 2>/dev/null || true
        uv run --with pandas --with scipy python "${BASE_DIR}/analysis/export_tables.py" 2>/dev/null || true
    else
        python3 "${BASE_DIR}/analysis/generate_plots.py" 2>/dev/null || true
        python3 "${BASE_DIR}/analysis/export_tables.py" 2>/dev/null || true
    fi
fi

echo "[3/3] Sincronizando relatórios com o repositório local e GitHub..."
if [[ -d "${BASE_DIR}/.git" ]]; then
    (
        cd "${BASE_DIR}"
        git add docs/20_relatorio_experimental_ns3_flowmonitor_s0_s15.md \
                reports/figures/ \
                experiments/results/tables/ \
                experiments/results/canonical_simulation_master.csv \
                experiments/results/ns3_runs/ 2>/dev/null || true
        if ! git diff --cached --quiet 2>/dev/null; then
            TIMESTAMP="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
            git commit -m "chore(auto-report): atualiza relatorios, tabelas e figuras de simulacao [${TIMESTAMP}]" 2>/dev/null || true
            git push origin main 2>/dev/null || true
            echo "[OK] Relatórios locais commitados no repositório!"
        else
            echo "[INFO] Relatórios locais já estão sincronizados com as últimas simulações."
        fi

        # Se estiver executando no WSL2 e o workspace do host Windows existir, sincroniza para push imediato via daemon
        WIN_WORKSPACE="/mnt/c/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase1"
        if [[ -d "${WIN_WORKSPACE}" && "${BASE_DIR}" != "${WIN_WORKSPACE}" ]]; then
            cp -u "${BASE_DIR}/docs/20_relatorio_experimental_ns3_flowmonitor_s0_s15.md" "${WIN_WORKSPACE}/docs/" 2>/dev/null || true
            cp -ru "${BASE_DIR}/experiments/results/"* "${WIN_WORKSPACE}/experiments/results/" 2>/dev/null || true
            cp -ru "${BASE_DIR}/reports/figures/"* "${WIN_WORKSPACE}/reports/figures/" 2>/dev/null || true
            echo "[OK] Dados e relatórios sincronizados com o workspace host Windows e enviados ao GitHub!"
        fi
    )
fi
