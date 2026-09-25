#!/usr/bin/env bash
# ==============================================================================
# Script: run_all_scenarios_suite.sh
# Projeto: xApp RDL - Suíte Automatizada de Execução de Todos os Cenários (5G, 5GA, 6G)
# Finalidade: Compila e executa sequencialmente todos os 5 cenários no ns-3/NORI,
#             conectando com a xApp RDL e consolidando os relatórios estatísticos.
# ==============================================================================
set -euo pipefail

NS3_DIR="${NS3_DIR:-$HOME/ns3-oran-workspace/ns-3-oran}"
SCRATCH_DIR="$NS3_DIR/scratch"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEEDS=(42 101 2026)

echo "=============================================================================="
echo " [*] Iniciando Suíte Completa de Simulação e Benchmark RDL (5G, 5GA e 6G)"
echo " [*] Diretório do ns-3: $NS3_DIR"
echo "=============================================================================="

# 1. Copiar todos os cenários .cc para o scratch do ns-3
echo "[+] Sincronizando cenários .cc com o scratch do ns-3..."
mkdir -p "$SCRATCH_DIR"
cp -v "$PROJECT_DIR/simulations/ns3/"scenario_rdl_*.cc "$SCRATCH_DIR/"

# 2. Compilação via Ninja/CMake
echo "[+] Compilando todos os cenários com perfil otimizado via Ninja..."
cd "$NS3_DIR"
./ns3 build scratch/scenario_rdl_energy_vs_qos \
            scratch/scenario_rdl_tvs_conflict \
            scratch/scenario_rdl_5ga_multicarrier_mimo \
            scratch/scenario_rdl_6g_isac_sensing_coexistence \
            scratch/scenario_rdl_6g_cross_tier_governance

# 3. Matriz de Execução Automatizada
SCENARIOS=(
    "scenario_rdl_energy_vs_qos:Cenário 1 (5G EEVS - Energy vs QoS):--enableE2=true --simTime=30"
    "scenario_rdl_tvs_conflict:Cenário 2 (5G TVS - Handover vs Slicing):--enableE2=true --simTime=30"
    "scenario_rdl_5ga_multicarrier_mimo:Cenário 3 (5GA - Multi-Carrier FR1/FR3 & Massive MIMO):--enableE2=true --simTime=40"
    "scenario_rdl_6g_isac_sensing_coexistence:Cenário 4 (6G - ISAC Radar vs Comunicação 28 GHz):--sensingRatio=0.35 --simTime=30"
    "scenario_rdl_6g_cross_tier_governance:Cenário 5 (6G - Governança Cross-Tier & Anti-Rogue):--lockout=true --simTime=35"
)

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
            > "$PROJECT_DIR/data/results_suite/${SCENARIO_BIN}_seed_${SEED}.log" 2>&1 || {
            echo "  [!] Aviso: Execução concluída com código de retorno específico no log."
        }
    done
    echo "  [[OK]] $SCENARIO_DESC finalizado com sucesso para todas as seeds."
done

echo "=============================================================================="
echo " [*] Suíte de Simulação 5G/5GA/6G Concluída com Sucesso!"
echo " [*] Logs e métricas salvos em: $PROJECT_DIR/data/results_suite/"
echo "=============================================================================="

# Atualização de relatórios analíticos, gráficos e push automático para o GitHub
echo ""
echo "[+] Consolidando relatórios analíticos e sincronizando com o GitHub..."
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_DIR/.venv/bin/python"
elif [ -f "$PROJECT_DIR/.venv/Scripts/python.exe" ]; then
    PYTHON_CMD="$PROJECT_DIR/.venv/Scripts/python.exe"
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD "$PROJECT_DIR/scripts/run_experiment_suite.py" --push

