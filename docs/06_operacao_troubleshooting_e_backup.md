# Volume 06: Operação, Troubleshooting e Procedimentos de Backup Bare-Metal

> **Navegação Sequencial:** [Vol 01: Arquitetura Core](01_arquitetura_e_modelagem_matematica.md) -> [Vol 02: Infraestrutura & Rancher](02_infraestrutura_cluster_k3d_e_rancher.md) -> [Vol 03: Deploy & Observabilidade Kiali](03_guia_deploy_helm_e_k8s.md) -> [Vol 04: Testes, ns-3 & Benchmarks](04_testes_simulacao_ns3_e_benchmarks.md) -> [Vol 05: Conformidade O-RAN](05_relatorios_conformidade_e_governanca.md) -> **[Vol 06: Operação & Troubleshooting]**

**Documento:** Volume Temático 06  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL Determinística)  
**Escopo:** Procedimento Operacional Padrão (SOP), Diagnósticos de Falha, Troubleshooting Exaustivo e Backup/Restore WSL2  
**Data de Consolidação:** 27/08/2026  

---

## 1. Procedimento Operacional Padrão (SOP)

### 1.1. Sincronização e Reconstrução Limpa do Ambiente no Servidor
```bash
cd ~/XApp-RDL-F1

# 1. Atualização com o repositório central
git fetch origin
git reset --hard origin/main

# 2. Reconstrução da imagem Docker
docker build --file docker/Dockerfile --tag iqos-xapp-rdl:1.1.0 .

# 3. Importação nos nós do containerd (k3d)
for node in $(docker ps --format '{{.Names}}' | grep -E "k3d-.*-(server|agent)"); do
    echo "Carregando no nó: $node..."
    docker save iqos-xapp-rdl:1.1.0 | docker exec -i $node ctr images import -
done
```

---

## 2. Guia de Troubleshooting e Diagnóstico de Falhas

### 2.1. Erro: Falha de Importação / DNS no Rancher (`Could not resolve host: rancher-server` ou `no objects passed to apply`)
* **Sintomas:**
  - `curl: (6) Could not resolve host: rancher-server`
  - `error: no objects passed to apply`
  - `Unable to connect to the server: dial tcp: lookup rancher-server on 10.255.255.254:53: i/o timeout`
* **Causa:**
  1. O host WSL2 tenta resolver o nome `rancher-server` no servidor DNS do Windows (`10.255.255.254:53`), que não conhece esse hostname Docker.
  2. O Rancher expõe a porta `8443` no host Windows/WSL2, enquanto internamente no container e na rede Docker a porta padrão é `443`.
* **Solução Automatizada (Recomendada):**
  ```bash
  # Execute o comando make informando a URL/Token real de importação:
  make rancher-connect URL="https://localhost:8443/v3/import/c-m-abcdef_c-m-abcdef.yaml"

  # Ou execute diretamente o script com auto-descoberta de token:
  bash scripts/register_rancher.sh
  ```

---

### 2.2. Erro: `-bash: token: No such file or directory` e `Error from server (NotFound): namespaces "cattle-system" not found`
* **Sintomas:**
  - `-bash: token: No such file or directory`
  - `error: no objects passed to apply`
  - `Error from server (NotFound): namespaces "cattle-system" not found`
* **Causa:**
  - Digitar literalmente `<token>` no terminal Bash faz com que o shell interprete os caracteres `<` e `>` como operadores de redirecionamento de entrada (`stdin`), procurando por um arquivo inexistente chamado `token`.
  - Como o manifesto de registro não é baixado nem aplicado, o namespace `cattle-system` e o deployment `cattle-cluster-agent` não são criados no cluster k3d.
* **Solução:**
  1. Obtenha o comando de registro real na UI do Rancher (**Cluster Management** > **Clusters** > Seu cluster).
  2. Substitua `TOKEN_REAL.yaml` pelo nome exato do arquivo (ex: `c-m-abcdef123_c-m-abcdef123.yaml`):
     ```bash
     # Conectar container à rede do cluster
     docker network connect k3d-rancher-lab rancher-server 2>/dev/null || true

     # Baixar manifesto usando o token real
     docker exec rancher-server curl --insecure -sfL https://localhost:443/v3/import/TOKEN_REAL.yaml | kubectl apply -f -

     # Configurar o agente e reiniciar
     kubectl wait --for=condition=available --timeout=60s deployment/cattle-cluster-agent -n cattle-system 2>/dev/null || true
     kubectl set env deployment/cattle-cluster-agent -n cattle-system \
       CATTLE_SERVER="https://rancher-server:443" \
       CATTLE_SSL_NO_VERIFY="true"
     kubectl rollout restart deployment/cattle-cluster-agent -n cattle-system
     ```
  3. Ou execute `bash scripts/register_rancher.sh` para detecção e correção automática.

---

### 2.2. Erro: `cattle-cluster-agent` em `CrashLoopBackOff` ou `Connection Refused`
* **Causa:** O agente tenta acessar `127.0.0.1:8443` (loopback interno do Pod) ou sofre rejeição de certificado TLS autoassinado.
* **Solução:**
  ```bash
  docker network connect k3d-rancher-lab rancher-server 2>/dev/null || true
  kubectl set env deployment/cattle-cluster-agent -n cattle-system \
    CATTLE_SERVER="https://rancher-server:443" \
    CATTLE_SSL_NO_VERIFY="true"
  kubectl rollout restart deployment/cattle-cluster-agent -n cattle-system
  ```

---

### 2.3. Erro: `ErrImageNeverPull` ou `ImagePullBackOff`
* **Causa:** O Kubernetes tentou buscar a imagem `iqos-xapp-rdl:1.1.0` no Docker Hub público em vez de usar o containerd local do nó onde o Pod foi agendado.
* **Solução:**
  1. Carregue a imagem em todos os nós containerd com:
     ```bash
     for node in $(docker ps --format '{{.Names}}' | grep -E "k3d-.*-(server|agent)"); do
         docker save iqos-xapp-rdl:1.1.0 | docker exec -i $node ctr images import -
     done
     ```
  2. Garanta que o Helm aplique `--set image.pullPolicy=Never`.

---

### 2.4. Erro: `stat deploy/helm/iqos-xapp-rdl: no such file or directory`
* **Causa:** Execução de comandos a partir de um diretório incorreto ou ausência do chart local.
* **Solução:** Certifique-se de estar na raiz do repositório (`cd ~/XApp-RDL-F1`) e execute `make helm-deploy`.

---

### 2.5. Erro: `/bin/sh: 1: pytest: not found (Error 127)`
* **Causa:** O binário do `pytest` não está instalado no ambiente global do host ou o ambiente virtual (`.venv`) não foi ativado antes de executar `make test`.
* **Solução:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt -r requirements-dev.txt
  make test
  ```

---

### 2.6. Erro: `Could not find a version that satisfies the requirement networkx==3.2.1`
* **Causa:** Versões estritas de pacotes que exigem Python $\ge 3.9$ sendo instaladas em distros com Python 3.8 (ex: Ubuntu 20.04 LTS).
* **Solução:** Utilize operadores flexíveis (`>=`) ou execute os testes diretamente via contêiner:
  ```bash
  docker run --rm -v $(pwd):/app -w /app -u 0 iqos-xapp-rdl:1.1.0 sh -c "pip install -r requirements-dev.txt && pytest tests/ -v"
  ```

---

### 2.7. Erro: `Command 'sudo' not found`
* **Sintomas:**
  - `bash: sudo: command not found`
  - `Command 'sudo' not found, but can be installed with: apt install sudo`
* **Causa:** O terminal está executando diretamente como usuário `root` (comum em instâncias WSL2 ou contêineres Docker mínimos). Como o usuário já possui os privilégios mais altos do sistema, o utilitário `sudo` não vem instalado e não é necessário para gerenciar pacotes.
* **Solução:**
  1. Execute comandos administrativos (como `apt-get`) diretamente, sem prefixar `sudo`:
     ```bash
     apt-get update && apt-get install -y build-essential cmake git
     ```
  2. Caso deseje disponibilizar o comando `sudo` para compatibilidade com scripts de terceiros:
     ```bash
     apt-get update && apt-get install -y sudo
     ```

---

### 2.8. Erro no ns-3: `Exception: Refusing to run as root. --enable-sudo will request your password when needed`
* **Sintomas:**
  - `./ns3 configure` ou `./ns3 build` falha com `Exception: Refusing to run as root`.
* **Causa:** O front-end em Python do simulador ns-3 (`./ns3`) contém uma validação intencional (`refuse_run_as_root()`) que impede a compilação como superusuário (`UID 0`) para evitar modificações acidentais em arquivos do sistema.
* **Solução:**
  1. **Opção Recomendada (Bypass de verificação no WSL2/Docker):** Restaure o arquivo e insira o retorno imediato na função:
     ```bash
     cd ~/ns3-oran-workspace/ns-3-oran
     git checkout ./ns3
     sed -i 's/def refuse_run_as_root():/def refuse_run_as_root():\n    return/g' ./ns3
     ./ns3 configure -d optimized --enable-examples --enable-tests
     ./ns3 build -j$(nproc)
     ```
  2. **Opção Alternativa:** Utilize o script automatizado do projeto a partir de `~/XApp-RDL-F1`:
     ```bash
     make setup-ns3
     ```
  3. **Opção por Usuário sem privilégios:** Crie um usuário padrão Linux e execute a compilação:
     ```bash
     useradd -m -s /bin/bash oran
     chown -R oran:oran ~/ns3-oran-workspace ~/XApp-RDL-F1
     su - oran
     cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 configure -d optimized && ./ns3 build -j$(nproc)
     ```

---

### 2.9. Erro: `make: *** No rule to make target 'run-experiments'. Stop.`
* **Sintomas:**
  - `make: *** No rule to make target 'run-experiments'. Stop.`
  - `make: *** No rule to make target 'analyze-benchmarks'. Stop.`
* **Causa:** O comando `make` foi invocado dentro do diretório do simulador (`~/ns3-oran-workspace/ns-3-oran`) em vez de no diretório raiz do repositório da xApp RDL. O `Makefile` que declara os alvos de orquestração experimental reside em `~/XApp-RDL-F1`.
* **Solução:** Navegue de volta ao diretório raiz do projeto antes de invocar os alvos do `make`:
  ```bash
  cd ~/XApp-RDL-F1
  make run-experiments
  # ou
  make analyze-benchmarks
  ```

---

### 2.10. Erro no Git: `fatal: detected dubious ownership in repository at '/root/XApp-RDL-F1'`
* **Sintomas:**
  - `fatal: detected dubious ownership in repository at '/root/XApp-RDL-F1'`
  - Comandos como `git pull`, `git fetch` ou `git reset` são bloqueados pelo Git.
* **Causa:** Medida de segurança introduzida a partir do Git 2.35.2 (CVE-2022-24765) que impede a execução de operações Git quando o dono do diretório no sistema de arquivos é diferente do usuário que está executando o comando (muito comum ao alternar entre usuário comum e `root` no WSL2 ou contêineres).
* **Solução:**
  1. **Para este repositório específico:**
     ```bash
     git config --global --add safe.directory /root/XApp-RDL-F1
     ```
  2. **Para todos os repositórios (Recomendado para ambientes de laboratório/WSL2):**
     ```bash
     git config --global --add safe.directory '*'
     ```
  3. Após configurar, execute normalmente:
     ```bash
     git fetch origin
     git reset --hard origin/main
     ```

---

### 2.11. Erro no ns-3: `CMake Error: CMake 3.25..3.25 or higher is required. You are running version 3.16.3`
* **Sintomas:**
  - `CMake Error at CMakeLists.txt:4 (cmake_minimum_required): CMake 3.25..3.25 or higher is required. You are running version 3.16.3`
  - Falha durante a etapa 4 de `./ns3 configure` ou `make setup-ns3`.
* **Causa:** O repositório de pacotes padrão do Ubuntu 20.04 (Focal) fornece a versão 3.16.3 do CMake. As versões recentes do ns-3 (ns-3-dev / 5G-LENA) utilizam recursos modernos de compilação que exigem CMake $\ge 3.25$.
* **Solução Rápida:**
  1. Instale/atualize o CMake via `pip3`:
     ```bash
     apt-get update && apt-get install -y python3-pip
     pip3 install --upgrade cmake
     hash -r
     ```
  2. Ou limpe os diretórios de cache e reexecute o script automatizado:
     ```bash
     cd ~/XApp-RDL-F1
     git fetch origin && git reset --hard origin/main
     make setup-ns3
     ```
  3. Se compilar manualmente no diretório do ns-3:
     ```bash
     cd ~/ns3-oran-workspace/ns-3-oran
     rm -rf cmake-cache build
     ./ns3 configure -d optimized --enable-examples --enable-tests
     ./ns3 build -j$(nproc)
     ```

---

## 3. Procedimento de Backup e Restauração do WSL Ubuntu 20.04

Para garantir recuperação instantânea contra desastres ou corrupção do disco virtual do WSL:

### 3.1. Backup Snapshot Completo (via PowerShell do Windows)
Abra o **PowerShell como Administrador**:

```powershell
# 1. Listar distribuições ativas
wsl --list --verbose

# 2. Criar diretório de destino no Windows
New-Item -ItemType Directory -Force -Path "C:\BackupsWSL"

# 3. Desligar o WSL para garantir integridade do disco
wsl --shutdown

# 4. Exportar a imagem completa do sistema para arquivo .tar
wsl --export Ubuntu-20.04 "C:\BackupsWSL\ubuntu-20.04-backup-$(Get-Date -Format 'yyyyMMdd').tar"
```

### 3.2. Restauração do Backup do WSL
```powershell
# Criar diretório da nova instância
New-Item -ItemType Directory -Force -Path "C:\WSL\Ubuntu20"

# Importar o snapshot .tar
wsl --import Ubuntu-20.04-Restaurado "C:\WSL\Ubuntu20" "C:\BackupsWSL\ubuntu-20.04-backup-YYYYMMDD.tar"

# Iniciar o sistema restaurado
wsl -d Ubuntu-20.04-Restaurado
```

### 3.3. Backup Rápido de Códigos e Configurações (sem desligar o WSL)
No terminal do próprio Ubuntu / WSL:
```bash
mkdir -p /mnt/c/BackupsWSL
tar -czvf /mnt/c/BackupsWSL/backup-configs-$(date +%Y%m%d).tar.gz \
  ~/XApp-RDL-F1 \
  ~/XApp-RDL-F2 \
  ~/.kube \
  ~/.config
```

---

## 4. Retorno ao Índice Geral

Voltar para a página inicial e índice temático da documentação:

🏠 **[Voltar ao Portal de Documentação (docs/README.md)](README.md)** | **[Página Inicial do Repositório (README.md)](../README.md)**
