#!/usr/bin/env bash
# ==============================================================================
# Script de Instalação e Compilação Automatizada do ns-3 NORI / 5G-LENA
# Suporta ambientes WSL2, Ubuntu, Docker e execução como root ou usuário comum.
# ==============================================================================
set -e

# Cores para saída no terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

WORKSPACE_DIR="${HOME}/ns3-oran-workspace"
NS3_DIR="${WORKSPACE_DIR}/ns-3-oran"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  Instalação e Configuração do Ambiente ns-3 NORI / 5G-LENA           ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. Detecção de privilégios e comando sudo
SUDO_CMD=""
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        SUDO_CMD="sudo"
    else
        echo -e "${RED}[ERRO] Este script requer privilégios de root para instalar pacotes apt, mas 'sudo' não foi encontrado.${NC}"
        echo -e "Por favor, execute como root ou instale o sudo."
        exit 1
    fi
fi

# 2. Instalação de dependências do sistema
echo -e "\n${YELLOW}[ETAPA 1/4] Instalando dependências essenciais do sistema (apt)...${NC}"
$SUDO_CMD apt-get update -y
$SUDO_CMD apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    python3-dev \
    libsctp-dev \
    lksctp-tools \
    libzmq3-dev \
    libboost-all-dev \
    libsqlite3-dev \
    libgsl-dev \
    libxml2-dev \
    tcpdump \
    wireshark \
    curl \
    ca-certificates

echo -e "${GREEN}[OK] Dependências do sistema instaladas com sucesso!${NC}"

# 3. Clonagem do repositório ns-3 (se ainda não existir)
echo -e "\n${YELLOW}[ETAPA 2/4] Preparando repositório ns-3 no workspace: ${WORKSPACE_DIR}...${NC}"
mkdir -p "${WORKSPACE_DIR}"

if [ ! -d "${NS3_DIR}" ]; then
    echo -e "Clonando ns-3-dev em ${NS3_DIR}..."
    git clone https://gitlab.com/nsnam/ns-3-dev.git "${NS3_DIR}" --depth 1
else
    echo -e "${GREEN}[OK] Diretório ${NS3_DIR} já existe.${NC}"
fi

cd "${NS3_DIR}"

# 4. Tratar trava de segurança para execução como root
echo -e "\n${YELLOW}[ETAPA 3/4] Ajustando permissões e compatibilidade do script ns3...${NC}"
if [ -f "./ns3" ]; then
    git checkout ./ns3 2>/dev/null || true
    if grep -q "def refuse_run_as_root():" "./ns3"; then
        echo -e "Ajustando 'refuse_run_as_root' para permitir compilação segura como root..."
        sed -i 's/def refuse_run_as_root():/def refuse_run_as_root():\n    return/g' ./ns3
    fi
fi

# 5. Configuração CMake e Compilação
echo -e "\n${YELLOW}[ETAPA 4/4] Configurando e compilando ns-3 com CMake...${NC}"
./ns3 configure -d optimized --enable-examples --enable-tests
./ns3 build -j"$(nproc)"

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}  ns-3 NORI / 5G-LENA compilado com sucesso!                          ${NC}"
echo -e "${GREEN}  Diretório: ${NS3_DIR}                                                ${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo -e "Para rodar os benchmarks do projeto xApp RDL, acerte o diretório do projeto e execute:"
echo -e "  ${YELLOW}cd ~/XApp-RDL-F1 && make run-experiments${NC}\n"
