#!/usr/bin/env bash
# ==============================================================================
# Terminal 2: Artefatos de decisão e controle observados (3 painéis no WSL)
# Skill: 09-cognitive-conflict-orchestrator & 08-ns3-oran-simulation-specialist
#
# Janelas / Painéis deste Terminal:
#   [Painel 0: Topo]         Janela 4: Endpoints IP observados no FlowMonitor
#   [Painel 1: Inferior Esq] Janela 5: Artefato de decisão RDL por execução
#   [Painel 2: Inferior Dir] Janela 6: Request/ACK E2SM-RC por execução
# ==============================================================================

set -euo pipefail

SESSION_NAME="oran-terminal-2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if ! command -v tmux &> /dev/null; then
    echo "[ERRO] tmux não encontrado. Instale com: sudo apt-get update && sudo apt-get install -y tmux"
    exit 1
fi

tmux kill-session -t "${SESSION_NAME}" 2>/dev/null || true

echo "[INFO] Inicializando Terminal 2 (artefatos RDL/E2) com 3 painéis..."

# Cria sessão em background (resolução confortável 160x45)
tmux new-session -d -s "${SESSION_NAME}" -x 160 -y 45

# Divide verticalmente em 2 partes (Topo e Base)
tmux split-window -v -t "${SESSION_NAME}:0.0"

# Divide a parte inferior horizontalmente em 2 colunas
tmux split-window -h -t "${SESSION_NAME}:0.1"

# Configura títulos dos painéis
tmux set-option -t "${SESSION_NAME}" -g pane-border-status top
tmux set-option -t "${SESSION_NAME}" -g pane-border-format " #{pane_index}: #{pane_title} "
tmux set-option -t "${SESSION_NAME}" -g pane-border-style fg=colour240
tmux set-option -t "${SESSION_NAME}" -g pane-active-border-style fg=colour206

# Executa os 3 monitores em cada painel
tmux select-pane -t "${SESSION_NAME}:0.0" -T "JANELA 4: ENDPOINTS IP"
tmux send-keys -t "${SESSION_NAME}:0.0" "cd '${BASE_DIR}' && python3 -u scripts/wsl_pane_monitors.py pane4" C-m

tmux select-pane -t "${SESSION_NAME}:0.1" -T "JANELA 5: DECISÃO RDL"
tmux send-keys -t "${SESSION_NAME}:0.1" "cd '${BASE_DIR}' && python3 -u scripts/wsl_pane_monitors.py pane5" C-m

tmux select-pane -t "${SESSION_NAME}:0.2" -T "JANELA 6: CONTROLE E2SM-RC"
tmux send-keys -t "${SESSION_NAME}:0.2" "cd '${BASE_DIR}' && python3 -u scripts/wsl_pane_monitors.py pane6" C-m

tmux select-pane -t "${SESSION_NAME}:0.0"

echo "[OK] Terminal 2 pronto com 3 janelas!"
echo "Para anexar execute: tmux attach -t ${SESSION_NAME}"

if [ -t 0 ] && [ -t 1 ]; then
    tmux attach-session -t "${SESSION_NAME}"
fi
