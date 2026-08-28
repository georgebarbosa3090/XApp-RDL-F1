#!/usr/bin/env bash
# ==============================================================================
# Script de Atualização Automática Contínua (Watcher / Auto-Sync)
# Monitora qualquer modificação no repositório e sincroniza com o GitHub
# Projeto: xApp RDL (Resource and Decision Layer) - Fase 1
# ==============================================================================

INTERVAL="${1:-5}" # Intervalo de verificação em segundos
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

echo "============================================================"
echo "  xApp RDL: Monitor de Atualização Automática do GitHub"
echo "  Intervalo de varredura: ${INTERVAL} segundos"
echo "  Diretório monitorado: ${REPO_ROOT}"
echo "  Pressione Ctrl+C para interromper a qualquer momento."
echo "============================================================"

# Função de limpeza ao receber SIGINT/SIGTERM
cleanup() {
    echo ""
    echo "[!] Monitor de sincronização automática finalizado pelo usuário."
    exit 0
}
trap cleanup SIGINT SIGTERM

while true; do
    # Verificar se existem alterações no repositório
    CHANGES=$(git status --porcelain 2>/dev/null || true)
    
    if [ -n "${CHANGES}" ]; then
        TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
        echo ""
        echo "[*] [${TIMESTAMP}] Alterações detectadas:"
        git status -s
        
        # Debounce de 3 segundos para aguardar salvar múltiplos arquivos juntos
        sleep 3
        
        echo "[*] Disparando sincronização automática..."
        bash "${REPO_ROOT}/scripts/git_sync.sh" "auto(sync): auto-update changes on ${TIMESTAMP}" || {
            echo "[!] Falha temporária na sincronização automática. Tentando novamente no próximo ciclo..."
        }
        echo "[*] Aguardando novas alterações..."
    fi
    
    sleep "${INTERVAL}"
done
