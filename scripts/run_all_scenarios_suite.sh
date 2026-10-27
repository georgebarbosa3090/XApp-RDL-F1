#!/usr/bin/env bash
# ==============================================================================
# Script: run_all_scenarios_suite.sh
# Executa somente os cenários ns-3 que exigem o módulo 5G-LENA NR.
# ==============================================================================
set -euo pipefail

NS3_DIR="${NS3_DIR:-$HOME/ns3-oran-workspace/ns-3-oran}"
SCRATCH_DIR="$NS3_DIR/scratch"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEEDS=(42 101 2026)

echo "=============================================================================="
echo " [*] Iniciando suíte ns-3 + 5G-LENA (cenários S2)"
echo " [*] Diretório do ns-3: $NS3_DIR"
echo "=============================================================================="

# Sincroniza somente cenários Phase 1 e nunca sobrescreve arquivos locais diferentes.
mkdir -p "$SCRATCH_DIR"
SCENARIOS=(
    "scenario_rdl_energy_vs_qos:Cenário 1 (5G EEVS - Energy vs QoS):--enableE2=true --simTime=30"
    "scenario_rdl_tvs_conflict:Cenário 2 (5G TVS - Handover vs Slicing):--enableE2=true --simTime=30"
)

for ENTRY in "${SCENARIOS[@]}"; do
    IFS=":" read -r SCENARIO_BIN SCENARIO_DESC SCENARIO_FLAGS <<< "$ENTRY"
    SOURCE="$PROJECT_DIR/simulations/ns3/$SCENARIO_BIN.cc"
    DESTINATION="$SCRATCH_DIR/$SCENARIO_BIN.cc"
    if [[ -e "$DESTINATION" ]]; then
        if ! cmp -s "$SOURCE" "$DESTINATION"; then
            echo "[ERROR] $DESTINATION existe e difere da fonte; não será sobrescrito." >&2
            exit 1
        fi
    else
        cp "$SOURCE" "$DESTINATION"
    fi
done

# Compile fails at source level if the 5G-LENA module is absent.
echo "[+] Compilando cenários ns-3 + 5G-LENA..."
cd "$NS3_DIR"
./ns3 build scratch/scenario_rdl_energy_vs_qos scratch/scenario_rdl_tvs_conflict

# Stop immediately on any failed scenario/seed; never create success-shaped reports.
mkdir -p "$PROJECT_DIR/data/results_suite"

for ENTRY in "${SCENARIOS[@]}"; do
    IFS=":" read -r SCENARIO_BIN SCENARIO_DESC SCENARIO_FLAGS <<< "$ENTRY"
    echo "------------------------------------------------------------------------------"
    echo " [*] Executando: $SCENARIO_DESC"
    echo " [*] Binário: $SCENARIO_BIN | Flags: $SCENARIO_FLAGS"
    echo "------------------------------------------------------------------------------"

    for SEED in "${SEEDS[@]}"; do
        echo "  [>] Executando com RNG Seed=$SEED..."
        ./ns3 run "scratch/$SCENARIO_BIN $SCENARIO_FLAGS --seed=$SEED" \
            > "$PROJECT_DIR/data/results_suite/${SCENARIO_BIN}_seed_${SEED}.log" 2>&1
    done
    echo "  [OK] $SCENARIO_DESC finalizado para todas as seeds."
done

echo "=============================================================================="
echo " [*] Suíte ns-3 + 5G-LENA concluída com sucesso."
echo " [*] Logs e métricas salvos em: $PROJECT_DIR/data/results_suite/"
echo "=============================================================================="
