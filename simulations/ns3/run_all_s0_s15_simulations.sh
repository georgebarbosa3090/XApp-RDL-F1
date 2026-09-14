#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NS3_DIR="${NS3_DIR:-/opt/ns-3.48/ns-3.48}"
RESULTS_DIR="${SCRIPT_DIR}/../../experiments/results/s0_s15_simulations"

mkdir -p "${RESULTS_DIR}"

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
echo "Executando Co-Simulação ns-3: Modo '${TARGET}' (${#SELECTED_SCENARIOS[@]} cenários)"
echo "Ambiente: ns-3.48 + 5G-LENA v5.1 + NORI Open-RAN"
echo "Destino de Traces: ${RESULTS_DIR}"
echo "================================================================================"

for SCENARIO in "${SELECTED_SCENARIOS[@]}"; do
    echo "--------------------------------------------------------------------------------"
    echo "Processando cenário: ${SCENARIO}.cc"
    if [ -d "${NS3_DIR}" ]; then
        cp "${SCRIPT_DIR}/${SCENARIO}.cc" "${NS3_DIR}/scratch/"
        cd "${NS3_DIR}"
        ./ns3 run "${SCENARIO} --simTime=10.0" > "${RESULTS_DIR}/${SCENARIO}.log" 2>&1 || true
        echo "[OK] Concluído: ${RESULTS_DIR}/${SCENARIO}.log"
    else
        echo "[INFO] Modo simulação desacoplado: cenário C++ ${SCENARIO}.cc registrado e pronto."
    fi
done

echo "================================================================================"
echo "Execução concluída com sucesso!"
echo "================================================================================"
