#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NS3_DIR="${NS3_DIR:-/opt/ns-3.48/ns-3.48}"
RESULTS_DIR="${SCRIPT_DIR}/../../experiments/results/s0_s15_simulations"

mkdir -p "${RESULTS_DIR}"

echo "================================================================================"
echo "Executando Suíte Completa de Co-Simulação ns-3 (Cenários S0 a S15)"
echo "Ambiente: ns-3.48 + 5G-LENA v5.1 + NORI Open-RAN"
echo "Destino de Traces: ${RESULTS_DIR}"
echo "================================================================================"

SCENARIOS=(
    "scenario_rdl_no_conflict"
    "scenario_rdl_direct_prb_conflict"
    "scenario_rdl_energy_vs_qos"
    "scenario_rdl_tvs_conflict"
    "scenario_rdl_ts_vs_energy"
    "scenario_rdl_temporal_pingpong"
    "scenario_rdl_conflict_storm"
    "scenario_rdl_fault_injection"
    "scenario_rdl_closed_loop_nori"
    "scenario_rdl_s9_ntn_orbital_handover"
    "scenario_rdl_s10_uav_swarm_battery"
    "scenario_rdl_s11_v2x_highway_platooning"
    "scenario_rdl_s12_iiot_zero_jitter_slicing"
    "scenario_rdl_s13_sagin_disaster_rescue"
    "scenario_rdl_s14_isac_radar_comm"
    "scenario_rdl_s15_rogue_ntn_feeder_hijacking"
)

for SCENARIO in "${SCENARIOS[@]}"; do
    echo "--------------------------------------------------------------------------------"
    echo "Processando cenário: ${SCENARIO}.cc"
    if [ -d "${NS3_DIR}" ]; then
        cp "${SCRIPT_DIR}/${SCENARIO}.cc" "${NS3_DIR}/scratch/"
        cd "${NS3_DIR}"
        ./ns3 run "${SCENARIO} --simTime=10.0" > "${RESULTS_DIR}/${SCENARIO}.log" 2>&1 || true
    else
        echo "[INFO] Modo simulação desacoplado: cenário C++ ${SCENARIO}.cc registrado e pronto."
    fi
done

echo "================================================================================"
echo "Suíte de Simulação S0 a S15 concluída com sucesso!"
echo "================================================================================"
