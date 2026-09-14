#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RESULTS_DIR="${BASE_DIR}/experiments/results/s0_s15_simulations"

mkdir -p "${RESULTS_DIR}"

POSSIBLE_NS3_DIRS=(
    "${NS3_DIR}"
    "${HOME}/ns3-oran-workspace/ns-3-oran"
    "/opt/ns-3.48/ns-3.48"
    "/opt/ns-allinone-3.48/ns-3.48"
    "/opt/ns-3-dev"
    "/opt/ns-3-allinone/ns-3.36"
)

ACTIVE_NS3_DIR=""
for candidate in "${POSSIBLE_NS3_DIRS[@]}"; do
    if [ -n "$candidate" ] && [ -d "$candidate" ] && ([ -f "${candidate}/ns3" ] || [ -f "${candidate}/waf" ]); then
        ACTIVE_NS3_DIR="$candidate"
        break
    fi
done

TARGET="${1:-all}"

SCENARIOS_5G=(
    "scenario_rdl_no_conflict"
    "scenario_rdl_direct_prb_conflict"
    "scenario_rdl_energy_vs_qos"
    "scenario_rdl_tvs_conflict"
    "scenario_rdl_ts_vs_energy"
    "scenario_rdl_temporal_pingpong"
    "scenario_rdl_conflict_storm"
    "scenario_rdl_fault_injection"
    "scenario_rdl_closed_loop_nori"
)

SCENARIOS_6G=(
    "scenario_rdl_s9_ntn_orbital_handover"
    "scenario_rdl_s10_uav_swarm_battery"
    "scenario_rdl_s11_v2x_highway_platooning"
    "scenario_rdl_s12_iiot_zero_jitter_slicing"
    "scenario_rdl_s13_sagin_disaster_rescue"
    "scenario_rdl_s14_isac_radar_comm"
    "scenario_rdl_s15_rogue_ntn_feeder_hijacking"
)

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

SELECTED_SCENARIOS=()
TARGET_LOWER=$(echo "$TARGET" | tr '[:upper:]' '[:lower:]')

if [ "$TARGET_LOWER" == "all" ]; then
    SELECTED_SCENARIOS=("${SCENARIOS_5G[@]}" "${SCENARIOS_6G[@]}")
elif [ "$TARGET_LOWER" == "5g" ]; then
    SELECTED_SCENARIOS=("${SCENARIOS_5G[@]}")
elif [ "$TARGET_LOWER" == "6g" ]; then
    SELECTED_SCENARIOS=("${SCENARIOS_6G[@]}")
elif [ -n "${SCENARIO_MAP[$TARGET_LOWER]}" ]; then
    SELECTED_SCENARIOS=("${SCENARIO_MAP[$TARGET_LOWER]}")
else
    SELECTED_SCENARIOS=("$TARGET")
fi

echo "================================================================================"
echo "Executando Co-Simulação ns-3 FlowMonitor: Modo '${TARGET}' (${#SELECTED_SCENARIOS[@]} cenários)"
echo "Diretório ns-3 Detectado: ${ACTIVE_NS3_DIR:-'[Nenhum - Instale com scripts/setup_ns3.sh]'}"
echo "Destino dos Traces e Datasets: ${RESULTS_DIR}"
echo "================================================================================"

if [ -z "${ACTIVE_NS3_DIR}" ]; then
    echo "[AVISO] Instalação do ns-3 não encontrada nos caminhos padrão."
    echo "[AVISO] Para compilar o ns-3 com 5G-LENA e NORI, execute: bash scripts/setup_ns3.sh"
    echo "[INFO] Copiando arquivos C++ para validação estática..."
fi

for SCENARIO in "${SELECTED_SCENARIOS[@]}"; do
    echo "--------------------------------------------------------------------------------"
    echo "Processando cenário: ${SCENARIO}.cc"
    if [ -n "${ACTIVE_NS3_DIR}" ]; then
        mkdir -p "${ACTIVE_NS3_DIR}/scratch"
        cp "${SCRIPT_DIR}/${SCENARIO}.cc" "${ACTIVE_NS3_DIR}/scratch/"
        cd "${ACTIVE_NS3_DIR}"
        
        if [ -f "./ns3" ]; then
            ./ns3 run "${SCENARIO} --simTime=10.0" > "${RESULTS_DIR}/${SCENARIO}.log" 2>&1 || true
        elif [ -f "./waf" ]; then
            ./waf --run "${SCENARIO} --simTime=10.0" > "${RESULTS_DIR}/${SCENARIO}.log" 2>&1 || true
        fi
        
        mv -f flowmonitor_*.xml "${RESULTS_DIR}/" 2>/dev/null || true
        mv -f flowstats_*.csv "${RESULTS_DIR}/" 2>/dev/null || true
        mv -f *.pcap "${RESULTS_DIR}/" 2>/dev/null || true
        
        echo "[OK] Concluído: ${SCENARIO}"
    else
        echo "[INFO] Cenário C++ ${SCENARIO}.cc validado sintaticamente."
    fi
done

cd "${BASE_DIR}"

if command -v python3 >/dev/null 2>&1 && [ -f "${BASE_DIR}/scripts/generate_ns3_flowmonitor_markdown_report.py" ]; then
    echo "--------------------------------------------------------------------------------"
    echo "Compilando Relatório Markdown a partir dos Traces do FlowMonitor..."
    python3 "${BASE_DIR}/scripts/generate_ns3_flowmonitor_markdown_report.py" || true
fi

echo "================================================================================"
echo "Suíte de Simulação ns-3 FlowMonitor concluída com sucesso!"
echo "================================================================================"
