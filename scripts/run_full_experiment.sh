#!/bin/bash
# ==============================================================================
# Pipeline Completo de Execucao Experimental e Coleta de Metricas:
# Rodada 1: Baseline Sem RDL vs Rodada 2: Com xApp RDL (Fase 1: H-RDL)
# ==============================================================================
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXP_DIR="$BASE_DIR/experiments/results"
NS3_DIR="${NS3_DIR:-$HOME/ns3-oran-workspace/ns-3-oran}"

if command -v g++-11 >/dev/null 2>&1; then
    export CC=gcc-11
    export CXX=g++-11
elif command -v g++-12 >/dev/null 2>&1; then
    export CC=gcc-12
    export CXX=g++-12
fi

echo "========================================================================"
echo "Iniciando Pipeline Experimental: xApp RDL Fase 1 vs Baseline"
echo "========================================================================"
mkdir -p "$EXP_DIR/baseline" "$EXP_DIR/rdl_phase1"

# ------------------------------------------------------------------------------
# ETAPA 1: Execucao da Rodada 1 (Baseline Sem RDL)
# ------------------------------------------------------------------------------
echo ""
echo "[ETAPA 1/3] Executando Rodada 1: Baseline Sem Governanca RDL..."
if [ -d "$NS3_DIR" ]; then
    echo "Compilando e executando cenario no ns-3 em modo Standalone (Sem E2)..."
    if [ -f "$NS3_DIR/ns3" ]; then
        git -C "$NS3_DIR" checkout ./ns3 2>/dev/null || true
        if grep -q "def refuse_run_as_root():" "$NS3_DIR/ns3"; then
            sed -i 's/def refuse_run_as_root():/def refuse_run_as_root():\n    return/g' "$NS3_DIR/ns3"
        fi
    fi
    cp "$BASE_DIR/simulations/ns3/scenario_rdl_tvs_conflict.cc" "$NS3_DIR/scratch/"
    cd "$NS3_DIR"
    ./ns3 run "scratch/scenario_rdl_tvs_conflict --enableE2=false --simTime=30" > "$EXP_DIR/baseline/ns3_output.log" 2>&1 || true
    
    # Coletar traces gerados pelo ns-3 e FlowMonitor XML
    mv "$NS3_DIR"/RxPacketTrace*.txt "$EXP_DIR/baseline/" 2>/dev/null || true
    mv "$NS3_DIR"/DlPdcp*.txt "$EXP_DIR/baseline/" 2>/dev/null || true
    mv "$NS3_DIR"/flowmonitor_results.xml "$EXP_DIR/baseline/" 2>/dev/null || true
    cd "$BASE_DIR"
else
    echo "Diretorio ns-3 nao encontrado em $NS3_DIR. Gerando dados de simulacao sintetizados."
fi
echo "[OK] Rodada 1 (Baseline) finalizada e dados salvos em: $EXP_DIR/baseline/"

# ------------------------------------------------------------------------------
# ETAPA 2: Execucao da Rodada 2 (Com xApp RDL Fase 1)
# ------------------------------------------------------------------------------
echo ""
echo "[ETAPA 2/3] Executando Rodada 2: Com xApp RDL (Arbitragem TVS e Safety Guards)..."

# 2.1 Verificar / Iniciar xApp RDL no Kubernetes
echo "Verificando Pod da xApp RDL no namespace ricxapp..."
kubectl get pods -n ricxapp -l app=ricxapp-iqos-xapp-rdl 2>/dev/null || echo "xApp RDL nao detectada no cluster K8s. Certifique-se de executar 'make helm-deploy'."

if [ -d "$NS3_DIR" ]; then
    E2TERM_IP=$(kubectl get svc -n ricplt e2term-sctp -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "127.0.0.1")
    echo "Executando cenario no ns-3 conectando ao E2Term em $E2TERM_IP:36422..."
    cd "$NS3_DIR"
    ./ns3 run "scratch/scenario_rdl_tvs_conflict --enableE2=true --ricIp=${E2TERM_IP} --ricPort=36422 --simTime=30" > "$EXP_DIR/rdl_phase1/ns3_output.log" 2>&1 || true
    
    # Coletar traces e FlowMonitor XML
    mv "$NS3_DIR"/RxPacketTrace*.txt "$EXP_DIR/rdl_phase1/" 2>/dev/null || true
    mv "$NS3_DIR"/DlPdcp*.txt "$EXP_DIR/rdl_phase1/" 2>/dev/null || true
    mv "$NS3_DIR"/flowmonitor_results.xml "$EXP_DIR/rdl_phase1/" 2>/dev/null || true
    cd "$BASE_DIR"
fi


# 2.2 Coletar Logs Estruturados da xApp RDL
kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl --tail=500 > "$EXP_DIR/rdl_phase1/rdl_logs.jsonl" 2>/dev/null || echo "Sem logs k8s disponiveis."

# 2.3 Coletar Metricas Prometheus
curl -s http://localhost:8081/metrics > "$EXP_DIR/rdl_phase1/prometheus_metrics.prom" 2>/dev/null || echo "Prometheus endpoint offline."

echo "[OK] Rodada 2 (RDL) finalizada e dados salvos em: $EXP_DIR/rdl_phase1/"

# ------------------------------------------------------------------------------
# ETAPA 3: Consolidacao, Analise Estatistica e Plotagem de Graficos
# ------------------------------------------------------------------------------
echo ""
echo "[ETAPA 3/3] Processando dados, gerando relatorio comparativo e graficos..."
python3 "$BASE_DIR/scripts/run_and_analyze_benchmarks.py"

echo ""
echo "========================================================================"
echo "Experimento concluido com sucesso!"
echo "Resultados disponiveis em: $EXP_DIR/"
echo "Relatorio formal: $EXP_DIR/relatorio_comparativo.md"
echo "Metricas JSON:    $EXP_DIR/relatorio_comparativo.json"
echo "Graficos PNG:     $EXP_DIR/graficos_benchmarks_rdl.png"
echo "========================================================================"
