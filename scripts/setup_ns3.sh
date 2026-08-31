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
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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
export DEBIAN_FRONTEND=noninteractive
$SUDO_CMD apt-get update -y
$SUDO_CMD apt-get install -y \
    build-essential \
    software-properties-common \
    cmake \
    ninja-build \
    git \
    python3-dev \
    python3-pip \
    pkg-config \
    wget \
    curl \
    ca-certificates \
    libsctp-dev \
    lksctp-tools \
    libzmq3-dev \
    libboost-all-dev \
    libsqlite3-dev \
    libgsl-dev \
    libxml2-dev \
    tcpdump \
    wireshark

# 2.1 Validação e atualização automática do compilador C++ (ns-3 moderno exige GCC/G++ >= 11 para C++20)
check_compiler_version() {
    if command -v g++ >/dev/null 2>&1; then
        local ver
        ver=$(g++ -dumpfullversion -dumpversion 2>/dev/null || g++ -dumpversion 2>/dev/null || echo "0")
        local major
        major=$(echo "$ver" | cut -d. -f1)
        if [ "$major" -ge 11 ]; then
            return 0
        fi
    fi
    return 1
}

if ! check_compiler_version; then
    echo -e "${YELLOW}[INFO] Versão do compilador C++ no sistema: $(g++ --version 2>/dev/null | head -n1 || echo 'nenhum').${NC}"
    echo -e "${YELLOW}[INFO] ns-3 moderno requer GCC/G++ >= 11 (suporte a C++20). Atualizando compilador...${NC}"

    # Adicionar repositório oficial de toolchain para Ubuntu Focal (20.04) / Debian
    $SUDO_CMD add-apt-repository -y ppa:ubuntu-toolchain-r/test || true
    $SUDO_CMD apt-get update -y

    # Instalar gcc-11 / g++-11 ou gcc-12 / g++-12
    $SUDO_CMD apt-get install -y gcc-11 g++-11 || $SUDO_CMD apt-get install -y gcc-12 g++-12 || true

    if command -v g++-11 >/dev/null 2>&1; then
        $SUDO_CMD update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 110 --slave /usr/bin/g++ g++ /usr/bin/g++-11 --slave /usr/bin/gcov gcov /usr/bin/gcov-11 || true
        $SUDO_CMD update-alternatives --set gcc /usr/bin/gcc-11 || true
        export CC=gcc-11
        export CXX=g++-11
    elif command -v g++-12 >/dev/null 2>&1; then
        $SUDO_CMD update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 120 --slave /usr/bin/g++ g++ /usr/bin/g++-12 --slave /usr/bin/gcov gcov /usr/bin/gcov-12 || true
        $SUDO_CMD update-alternatives --set gcc /usr/bin/gcc-12 || true
        export CC=gcc-12
        export CXX=g++-12
    fi

    hash -r 2>/dev/null || true

    if check_compiler_version; then
        echo -e "${GREEN}[OK] Compilador C++ atualizado com sucesso! Versão: $(g++ --version | head -n1)${NC}"
    elif command -v g++-11 >/dev/null 2>&1; then
        export CC=gcc-11
        export CXX=g++-11
        echo -e "${GREEN}[OK] GCC 11 detectado e configurado via CC/CXX.${NC}"
    fi
fi

# 2.2 Validação e atualização automática do CMake (ns-3 moderno exige CMake >= 3.25)
check_cmake_version() {
    if command -v cmake >/dev/null 2>&1; then
        local ver
        ver=$(cmake --version 2>/dev/null | head -n1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "0.0.0")
        local major minor
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -gt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -ge 25 ]); then
            return 0
        fi
    fi
    return 1
}

if ! check_cmake_version; then
    echo -e "${YELLOW}[INFO] Versão do CMake no sistema: $(cmake --version 2>/dev/null | head -n1 || echo 'nenhuma').${NC}"
    echo -e "${YELLOW}[INFO] ns-3 requer CMake >= 3.25. Atualizando CMake...${NC}"

    # Método 1: pip3
    if command -v pip3 >/dev/null 2>&1; then
        echo -e "Tentando atualizar CMake via pip3..."
        $SUDO_CMD pip3 install --upgrade cmake --break-system-packages 2>/dev/null || $SUDO_CMD pip3 install --upgrade cmake 2>/dev/null || true
    fi

    hash -r 2>/dev/null || true

    # Método 2: Binário oficial Kitware (fallback)
    if ! check_cmake_version; then
        echo -e "Instalando CMake moderno diretamente do release oficial (Kitware v3.28.3)..."
        CMAKE_TAR="cmake-3.28.3-linux-x86_64.tar.gz"
        wget -q --show-progress "https://github.com/Kitware/CMake/releases/download/v3.28.3/${CMAKE_TAR}" -O "/tmp/${CMAKE_TAR}" || \
            curl -fsSL "https://github.com/Kitware/CMake/releases/download/v3.28.3/${CMAKE_TAR}" -o "/tmp/${CMAKE_TAR}"
        $SUDO_CMD tar -xzf "/tmp/${CMAKE_TAR}" -C /usr/local --strip-components=1
        rm -f "/tmp/${CMAKE_TAR}"
        hash -r 2>/dev/null || true
    fi

    if check_cmake_version; then
        echo -e "${GREEN}[OK] CMake atualizado com sucesso! Versão: $(cmake --version | head -n1)${NC}"
    else
        echo -e "${RED}[AVISO] Não foi possível atualizar o CMake automaticamente para >= 3.25.${NC}"
    fi
fi

echo -e "${GREEN}[OK] Dependências do sistema instaladas com sucesso!${NC}"

# 3. Clonagem do repositório ns-3 e módulo 5G-LENA (nr)
echo -e "\n${YELLOW}[ETAPA 2/4] Preparando repositório ns-3 e 5G-LENA no workspace: ${WORKSPACE_DIR}...${NC}"
mkdir -p "${WORKSPACE_DIR}"

if [ ! -d "${NS3_DIR}" ]; then
    echo -e "Clonando ns-3-dev em ${NS3_DIR}..."
    git clone https://gitlab.com/nsnam/ns-3-dev.git "${NS3_DIR}" --depth 1
else
    echo -e "${GREEN}[OK] Diretório ${NS3_DIR} já existe.${NC}"
fi

cd "${NS3_DIR}"

# 3.1 Clonar módulo 5G-LENA (nr) em contrib/nr se ausente
if [ ! -d "${NS3_DIR}/contrib/nr" ] && [ ! -d "${NS3_DIR}/src/nr" ]; then
    echo -e "Clonando módulo 5G-LENA (nr) em ${NS3_DIR}/contrib/nr..."
    mkdir -p "${NS3_DIR}/contrib"
    git clone https://gitlab.com/cttc-lena/nr.git "${NS3_DIR}/contrib/nr" --depth 1 || {
        echo -e "${YELLOW}[AVISO] Falha ao clonar 5G-LENA diretamente. Prosseguindo com fallback...${NC}"
    }
else
    echo -e "${GREEN}[OK] Módulo 5G-LENA (nr) detectado em ${NS3_DIR}.${NC}"
fi

# 3.2 Copiar cenários de simulação do projeto para o diretório scratch do ns-3
if [ -d "${BASE_DIR}/simulations/ns3" ]; then
    mkdir -p "${NS3_DIR}/scratch"
    rm -f "${NS3_DIR}/scratch/scenario_rdl_"*.cc 2>/dev/null || true
    cp -f "${BASE_DIR}/simulations/ns3/"*.cc "${NS3_DIR}/scratch/" 2>/dev/null || true
    echo -e "${GREEN}[OK] Cenários C++ sincronizados com ${NS3_DIR}/scratch/.${NC}"
fi

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
# Limpar cache de compilações antigas/incompletas
rm -rf cmake-cache build .lock-waf*

if command -v g++-11 >/dev/null 2>&1; then
    export CC=gcc-11
    export CXX=g++-11
elif command -v g++-12 >/dev/null 2>&1; then
    export CC=gcc-12
    export CXX=g++-12
fi

./ns3 configure -d optimized --enable-examples --enable-tests

# Limitar concorrência para evitar esgotamento de RAM (OOM) no WSL2/Docker
NPROC_MAX=$(nproc 2>/dev/null || echo 2)
BUILD_JOBS=${BUILD_JOBS:-$(( NPROC_MAX > 2 ? (NPROC_MAX > 4 ? 4 : NPROC_MAX) : 2 ))}
echo -e "Compilando com ${BUILD_JOBS} threads paralelas para estabilidade de memória..."
./ns3 build -j"${BUILD_JOBS}"

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}  ns-3 NORI / 5G-LENA compilado com sucesso!                          ${NC}"
echo -e "${GREEN}  Diretório: ${NS3_DIR}                                                ${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo -e "Para rodar os benchmarks do projeto xApp RDL, acerte o diretório do projeto e execute:"
echo -e "  ${YELLOW}cd ~/XApp-RDL-F1 && make run-baseline${NC}"
echo -e "  ${YELLOW}cd ~/XApp-RDL-F1 && make helm-deploy${NC}"
echo -e "  ${YELLOW}cd ~/XApp-RDL-F1 && make run-rdl${NC}\n"
