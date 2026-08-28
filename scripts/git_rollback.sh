#!/usr/bin/env bash
# ==============================================================================
# Script de Rollback Seguro de Commits e Alterações
# Permite desfazer alterações com criação automática de ponto de restauração
# Projeto: xApp RDL (Resource and Decision Layer) - Fase 1
# ==============================================================================

set -e

BRANCH="${GIT_BRANCH:-main}"
REMOTE="${GIT_REMOTE:-origin}"
TARGET_COMMIT=""
DO_PUSH=false
DO_CLEAN=false
DO_LIST=false
STEPS=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# Processar argumentos
while [[ $# -gt 0 ]]; do
    case "$1" in
        --commit|-c)
            TARGET_COMMIT="$2"
            shift 2
            ;;
        --steps|-s)
            STEPS="$2"
            shift 2
            ;;
        --push|-p)
            DO_PUSH=true
            shift
            ;;
        --clean)
            DO_CLEAN=true
            shift
            ;;
        --list|-l)
            DO_LIST=true
            shift
            ;;
        --help|-h)
            echo "Uso: $0 [OPÇÕES]"
            echo ""
            echo "Opções:"
            echo "  --list, -l          Lista o histórico recente de commits e pontos de restauração"
            echo "  --steps, -s <N>     Volta N commits atrás (padrão: 1)"
            echo "  --commit, -c <HASH> Volta para um commit específico"
            echo "  --clean             Descarta todas as alterações não commitadas locais"
            echo "  --push, -p          Propaga o rollback para o GitHub remoto (force-with-lease)"
            echo "  --help, -h          Exibe esta ajuda"
            exit 0
            ;;
        *)
            if [ -z "${TARGET_COMMIT}" ] && [[ "$1" =~ ^[0-9a-fA-F]{6,40}$ ]]; then
                TARGET_COMMIT="$1"
            fi
            shift
            ;;
    esac
done

echo "============================================================"
echo "  xApp RDL: Ferramenta de Rollback e Restauração Segura"
echo "============================================================"

# Listar histórico se solicitado
if [ "${DO_LIST}" = true ]; then
    echo "[i] Histórico dos últimos 10 commits:"
    git log -n 10 --graph --pretty=format:'%C(yellow)%h%Creset -%C(auto)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset'
    echo ""
    echo "[i] Pontos de restauração e tags de backup disponíveis:"
    git tag -l "backup/*" | tail -n 10
    exit 0
fi

# Descartar alterações de trabalho não commitadas se solicitado
if [ "${DO_CLEAN}" = true ]; then
    echo "[!] Descartando todas as alterações não commitadas locais..."
    git restore . 2>/dev/null || git checkout -- .
    git clean -fd
    echo "[OK] Diretório de trabalho limpo com sucesso."
    exit 0
fi

# Obter estado atual
CURRENT_HASH=$(git rev-parse HEAD)
CURRENT_SHORT=$(git rev-parse --short HEAD)
TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
BACKUP_TAG="backup/rollback_${TIMESTAMP}_${CURRENT_SHORT}"

# Criar ponto de restauração de segurança obrigatório
echo "[+] Criando ponto de restauração de segurança: ${BACKUP_TAG}..."
git tag "${BACKUP_TAG}" HEAD

# Determinar commit de destino
if [ -n "${TARGET_COMMIT}" ]; then
    DEST_COMMIT="${TARGET_COMMIT}"
else
    DEST_COMMIT="HEAD~${STEPS}"
fi

echo "[+] Executando rollback para: ${DEST_COMMIT}..."
git reset --hard "${DEST_COMMIT}"

NEW_SHORT=$(git rev-parse --short HEAD)
echo "[OK] Rollback local concluído com sucesso!"
echo "     Commit anterior: ${CURRENT_SHORT}"
echo "     Commit atual:    ${NEW_SHORT}"
echo "     Tag de segurança criada: ${BACKUP_TAG} (permite desfazer o rollback a qualquer momento)"

# Se solicitado envio para o GitHub
if [ "${DO_PUSH}" = true ]; then
    echo "[!] Propagando rollback para o repositório remoto GitHub (${REMOTE}/${BRANCH})..."
    git push --force-with-lease "${REMOTE}" "${BRANCH}"
    echo "[OK] Rollback sincronizado com sucesso no GitHub!"
else
    echo ""
    echo "[Dica] Para sincronizar esse rollback com o GitHub remoto, execute:"
    echo "       make rollback-push"
    echo "       ou: git push --force-with-lease origin main"
fi
