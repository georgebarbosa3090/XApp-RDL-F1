#!/usr/bin/env bash
# ==============================================================================
# Orquestrador tmux no WSL Ubuntu — 6 Janelas na Mesma Tela (100% Dados Reais)
# Skill: 09-cognitive-conflict-orchestrator & 08-ns3-oran-simulation-specialist
#
# Divide a tela do terminal WSL em uma grade 2x3 (6 janelas/painéis sincronizados):
#   [Painel 0: Reg. UEs/gNBs] [Painel 1: Sinalização E2] [Painel 2: Percepção]
#   [Painel 3: Grafo Conhec.] [Painel 4: Refinamento]    [Painel 5: Ação E2SM-RC]
# ==============================================================================

set -euo pipefail

SESSION_NAME="oran-closed-loop-6panes"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Verifica se o tmux está instalado no WSL
if ! command -v tmux &> /dev/null; then
    echo "[ERRO] tmux não encontrado no WSL Ubuntu. Instale com: sudo apt-get update && sudo apt-get install -y tmux"
    exit 1
fi

# Mata sessão prévia se existir
tmux kill-session -t "${SESSION_NAME}" 2>/dev/null || true

echo "[INFO] Inicializando sessão tmux '${SESSION_NAME}' no layout 2x3 com 6 janelas na mesma tela..."

# Cria nova sessão em background com resolução confortável (160x50)
tmux new-session -d -s "${SESSION_NAME}" -x 160 -y 50

# 1. Divide horizontalmente em 2 linhas (Linha Superior e Linha Inferior)
tmux split-window -v -t "${SESSION_NAME}:0.0"

# 2. Divide a Linha Superior (Painel 0) em 3 colunas
#    Primeiro split na metade (Painel 0 vira 0 e 1)
tmux split-window -h -t "${SESSION_NAME}:0.0"
#    Segundo split no primeiro terço (Painel 0 vira 0 e 2)
tmux split-window -h -t "${SESSION_NAME}:0.0"

# 3. Divide a Linha Inferior (antigo Painel 1, agora Painel 3) em 3 colunas
tmux split-window -h -t "${SESSION_NAME}:0.3"
tmux split-window -h -t "${SESSION_NAME}:0.3"

# Equaliza os painéis para uma grade 2x3 simétrica perfeita
tmux select-layout -t "${SESSION_NAME}:0" tiled

# Configura títulos dos painéis
tmux set-option -t "${SESSION_NAME}" -g pane-border-status top
tmux set-option -t "${SESSION_NAME}" -g pane-border-format " #{pane_index}: #{pane_title} "
tmux set-option -t "${SESSION_NAME}" -g pane-border-style fg=colour240
tmux set-option -t "${SESSION_NAME}" -g pane-active-border-style fg=colour51

# Executa cada monitor dedicado em seu respectivo painel
tmux select-pane -t "${SESSION_NAME}:0.0" -T "1. REGISTRO UE & GNBS (ns-3)"
tmux send-keys -t "${SESSION_NAME}:0.0" "cd '${BASE_DIR}' && python3 -u scripts/wsl_pane_monitors.py pane1" C-m

tmux select-pane -t "${SESSION_NAME}:0.1" -T "2. SINALIZAÇÃO E2 (PCAP/APER)"
tmux send-keys -t "${SESSION_NAME}:0.1" "cd '${BASE_DIR}' && python3 -u scripts/wsl_pane_monitors.py pane2" C-m

tmux select-pane -t "${SESSION_NAME}:0.2" -T "3. PERCEPÇÃO & CONFLITOS"
tmux send-keys -t "${SESSION_NAME}:0.2" "cd '${BASE_DIR}' && python3 -u scripts/wsl_pane_monitors.py pane3" C-m

tmux select-pane -t "${SESSION_NAME}:0.3" -T "4. GRAFO DE CONHECIMENTO"
tmux send-keys -t "${SESSION_NAME}:0.3" "cd '${BASE_DIR}' && python3 -u scripts/wsl_pane_monitors.py pane4" C-m

tmux select-pane -t "${SESSION_NAME}:0.4" -T "5. REFINAMENTO & SAFETY (H-RDL)"
tmux send-keys -t "${SESSION_NAME}:0.4" "cd '${BASE_DIR}' && python3 -u scripts/wsl_pane_monitors.py pane5" C-m

tmux select-pane -t "${SESSION_NAME}:0.5" -T "6. AÇÃO E2SM-RC & MALHA FECHADA"
tmux send-keys -t "${SESSION_NAME}:0.5" "cd '${BASE_DIR}' && python3 -u scripts/wsl_pane_monitors.py pane6" C-m

# Seleciona o primeiro painel e anexa
tmux select-pane -t "${SESSION_NAME}:0.0"

echo "[OK] Sessão tmux configurada com 6 painéis!"
echo "Para anexar agora execute no terminal WSL: tmux attach -t ${SESSION_NAME}"

# Se estiver em terminal interativo, anexa automaticamente
if [ -t 0 ] || [ -t 1 ]; then
    tmux attach-session -t "${SESSION_NAME}"
fi
