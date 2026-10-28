#!/usr/bin/env bash
# ==============================================================================
# Orquestrador de 2 Terminais Abertos com 3 Janelas em Cada Um (Total 6 Janelas)
# Skill: 09-cognitive-conflict-orchestrator & 08-ns3-oran-simulation-specialist
#
# Terminal 1: Camada de Rede & Telemetria E2 (Janelas 1, 2, 3)
# Terminal 2: Camada Cognitiva & Ação em Malha Fechada (Janelas 4, 5, 6)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=============================================================================="
echo "  ☸️  INICIALIZANDO 2 TERMINAIS ABERTOS COM 3 JANELAS EM CADA UM"
echo "=============================================================================="
echo "  • Terminal 1: Rede & Telemetria (Janelas 1, 2, 3) [sessão: oran-terminal-1]"
echo "  • Terminal 2: Cognição & Ação (Janelas 4, 5, 6)   [sessão: oran-terminal-2]"
echo "=============================================================================="

# 1. Inicializa o Terminal 1 em background
bash "${BASE_DIR}/scripts/launch_terminal1_ran_telemetry.sh" >/dev/null 2>&1 || true

# 2. Inicializa o Terminal 2 em background
bash "${BASE_DIR}/scripts/launch_terminal2_cognitive_action.sh" >/dev/null 2>&1 || true

# 3. Se estiver no Windows/WSL, tenta abrir 2 janelas independentes no desktop
OPENED_DESKTOP=false

if command -v wt.exe &> /dev/null; then
    echo "[INFO] Abrindo 2 janelas separadas no Windows Terminal..."
    # Abre Terminal 1 (Janela Independente)
    wt.exe -w new --title "Terminal 1: Rede & Telemetria E2 (3 Janelas)" wsl.exe -d Ubuntu-20.04 -u root bash -c "launch_terminal1_ran_telemetry.sh" 2>/dev/null || true
    # Abre Terminal 2 (Janela Independente)
    wt.exe -w new --title "Terminal 2: Cognição & Ação E2SM-RC (3 Janelas)" wsl.exe -d Ubuntu-20.04 -u root bash -c "launch_terminal2_cognitive_action.sh" 2>/dev/null || true
    OPENED_DESKTOP=true
elif command -v cmd.exe &> /dev/null; then
    echo "[INFO] Abrindo 2 janelas separadas via console Windows..."
    cmd.exe /c start "Terminal 1: Rede & Telemetria" wsl.exe -d Ubuntu-20.04 -u root bash -c "launch_terminal1_ran_telemetry.sh" 2>/dev/null || true
    cmd.exe /c start "Terminal 2: Cognição & Ação" wsl.exe -d Ubuntu-20.04 -u root bash -c "launch_terminal2_cognitive_action.sh" 2>/dev/null || true
    OPENED_DESKTOP=true
fi

echo ""
echo "[OK] As 2 sessões tmux estão ativas com 3 janelas cada!"
echo ""
echo "COMANDOS PARA CONECTAR EM CADA TERMINAL:"
echo "------------------------------------------------------------------------------"
echo "  • No Terminal 1 execute:  tmux attach -t oran-terminal-1"
echo "  • No Terminal 2 execute:  tmux attach -t oran-terminal-2"
echo "------------------------------------------------------------------------------"
echo "Dica: Em cada terminal, use 'Ctrl+B' e as setas para navegar entre as 3 janelas."
echo "=============================================================================="
