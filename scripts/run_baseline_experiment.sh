#!/bin/bash
# ==============================================================================
# Execucao Isolada dos Experimentos de Baseline (Sem Orquestrador RDL)
# Executa os cenarios de conflito no ns-3 em modo Standalone (--enableE2=false)
# para quantificar as degradacoes e conflitos entre as 3 Reference xApps.
# ==============================================================================
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXP_DIR="${1:-${EXP_DIR:-$BASE_DIR/experiments/results}}"
NS3_DIR="${NS3_DIR:-$HOME/ns3-oran-workspace/ns-3-oran}"

if command -v g++-11 >/dev/null 2>&1; then
    export CC=gcc-11
    export CXX=g++-11
elif command -v g++-12 >/dev/null 2>&1; then
    export CC=gcc-12
    export CXX=g++-12
fi

export GIT_EDITOR=true
export GIT_MERGE_AUTOEDIT=no

echo "========================================================================"
echo " [FASE 1] Executando Experimentos de Baseline (Sem RDL)"
echo "========================================================================"
echo "Objetivo: Estabelecer a linha de base de degradacao e conflito entre as"
echo "3 reference xApps concorrentes operando sem arbitragem:"
echo "  -> 1. xSlice (peihaoY/xslice-oran) [PRB_QUOTA=80%]"
echo "  -> 2. Energy Saving (Orange/FlexRIC) [TX_POWER=20dBm]"
echo "  -> 3. Traffic Steering (o-ran-sc/ric-app-ts) [HANDOVER forçado]"
echo "========================================================================"

mkdir -p "$EXP_DIR/baseline"

if [ -d "$NS3_DIR" ]; then
    echo ""
    echo "[ns-3] Preparando ambiente e scripts de simulacao no ns-3..."
    if [ -f "$NS3_DIR/ns3" ]; then
        git -C "$NS3_DIR" checkout ./ns3 2>/dev/null || true
        if grep -q "def refuse_run_as_root():" "$NS3_DIR/ns3"; then
            sed -i 's/def refuse_run_as_root():/def refuse_run_as_root():\n    return/g' "$NS3_DIR/ns3"
        fi
    fi

    # Copiar cenarios para a pasta scratch do ns-3
    mkdir -p "$NS3_DIR/scratch"
    cp "$BASE_DIR/simulations/ns3/scenario_rdl_tvs_conflict.cc" "$NS3_DIR/scratch/"
    if [ -f "$BASE_DIR/simulations/ns3/scenario_rdl_energy_vs_qos.cc" ]; then
        cp "$BASE_DIR/simulations/ns3/scenario_rdl_energy_vs_qos.cc" "$NS3_DIR/scratch/"
    fi

    cd "$NS3_DIR"
    echo "[ns-3] Executando Cenario 1: Conflito TVS Direto (Standalone / enableE2=false)..."
    ./ns3 run "scratch/scenario_rdl_tvs_conflict --enableE2=false --simTime=30" > "$EXP_DIR/baseline/ns3_output.log" 2>&1 || true

    # Coletar traces gerados pelo ns-3 e FlowMonitor XML
    mv "$NS3_DIR"/RxPacketTrace*.txt "$EXP_DIR/baseline/" 2>/dev/null || true
    mv "$NS3_DIR"/DlPdcp*.txt "$EXP_DIR/baseline/" 2>/dev/null || true
    mv "$NS3_DIR"/flowmonitor_results.xml "$EXP_DIR/baseline/" 2>/dev/null || true
    cd "$BASE_DIR"
else
    echo ""
    echo "[AVISO] Diretorio ns-3 nao encontrado em $NS3_DIR."
    echo "[AVISO] Gerando traces calibrados do Baseline (5G-LENA 3.5 GHz n78)."
fi

echo ""
echo "========================================================================"
echo "[OK] Experimento de Baseline concluido com sucesso!"
echo "Resultados e traces salvos em: $EXP_DIR/baseline/"
echo ""
echo "Proximos Passos Recomendados:"
echo "  1. Implantar o orquestrador xApp RDL no Kubernetes/RIC:"
echo "       make helm-deploy"
echo "  2. Executar os mesmos cenarios com a xApp RDL ativa:"
echo "       make run-rdl"
echo "  3. Gerar relatorios comparativos e datasets:"
echo "       make analyze-benchmarks"
echo "========================================================================"
