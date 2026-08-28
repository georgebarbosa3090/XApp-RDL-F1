#!/usr/bin/env bash
# ==============================================================================
# Script de Sincronização Rápida e Segura com o GitHub
# Projeto: xApp RDL (Resource and Decision Layer) - Fase 1
# ==============================================================================

set -e

BRANCH="${GIT_BRANCH:-main}"
REMOTE="${GIT_REMOTE:-origin}"
CUSTOM_MSG="$1"

# Identificar raiz do repositório
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

echo "============================================================"
echo "  Sincronização do Repositório xApp RDL -> GitHub (${BRANCH})"
echo "============================================================"

# 1. Verificar estado atual do git
git fetch "${REMOTE}" "${BRANCH}" --quiet 2>/dev/null || true

# Verificar alterações locais (staged, unstaged, untracked)
CHANGES=$(git status --porcelain)

if [ -n "${CHANGES}" ]; then
    echo "[+] Detectadas alterações locais no repositório:"
    git status -s
    
    # Criar ponto de restauração de segurança antes do sync
    CURRENT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "initial")
    TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
    git tag -f "backup/pre-sync-latest" HEAD 2>/dev/null || true

    # Definir mensagem do commit
    if [ -z "${CUSTOM_MSG}" ]; then
        CHANGED_SUMMARY=$(git status -s | head -n 3 | awk '{print $2}' | tr '\n' ' ' | sed 's/ $//')
        MSG="chore(sync): update repository (${CHANGED_SUMMARY}) [${TIMESTAMP}]"
    else
        MSG="${CUSTOM_MSG}"
    fi

    echo "[+] Adicionando arquivos e gerando commit: \"${MSG}\""
    git add -A
    git commit -m "${MSG}"
else
    echo "[i] Nenhuma alteração de arquivo pendente no diretório de trabalho."
fi

# 2. Atualizar com a branch remota com rebase para manter histórico limpo
echo "[+] Sincronizando com ${REMOTE}/${BRANCH} (pull --rebase)..."
git pull --rebase "${REMOTE}" "${BRANCH}" || {
    echo "[!] Aviso: Conflito durante pull --rebase. Resolva os conflitos ou execute 'git rebase --abort'."
    exit 1
}

# 3. Enviar para o GitHub
echo "[+] Enviando commits para o GitHub (${REMOTE} ${BRANCH})..."
if git push "${REMOTE}" "${BRANCH}"; then
    LATEST_HASH=$(git rev-parse --short HEAD)
    echo "============================================================"
    echo " [OK] Repositório sincronizado com sucesso no GitHub!"
    echo "      Commit atual: ${LATEST_HASH}"
    echo "      Branch: ${BRANCH}"
    echo "============================================================"
else
    echo "[X] Erro ao enviar para o GitHub. Verifique permissões/chaves SSH."
    exit 1
fi
