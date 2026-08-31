# Volume 05: Operação, Troubleshooting e Procedimentos de Backup Bare-Metal

> **Navegação Sequencial:** [Vol 01: Arquitetura Core](01_arquitetura_e_modelagem_matematica.md) -> [Vol 02: Infraestrutura & Rancher](02_infraestrutura_cluster_k3d_e_rancher.md) -> [Vol 03: Deploy, Testes & Simulações ns-3](03_guia_deploy_testes_e_simulacoes_ns3.md) -> [Vol 04: Conformidade O-RAN](04_relatorios_conformidade_e_governanca.md) -> **[Vol 05: Operação & Troubleshooting]**

**Documento:** Volume Temático 05  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL Determinística)  
**Escopo:** Procedimento Operacional Padrão (SOP), Diagnósticos de Falha, Troubleshooting Exaustivo e Backup/Restore WSL2  
**Data de Consolidação:** 28/08/2026  

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

### 1.2. Sincronização Contínua e Atualização Automática para o GitHub
Para agilizar o desenvolvimento, o projeto disponibiliza scripts de sincronização instantânea e monitoramento contínuo de alterações:

```bash
# Sincronização pontual com mensagem automática ou personalizada:
make sync
# ou especificando mensagem: make sync MSG="feat(rdl): add new safety clamp logic"

# Atualização automática contínua (monitora alterações em arquivos e envia ao salvar):
make auto-sync
# ou com intervalo customizado em segundos: make auto-sync INTERVAL=10
```

### 1.3. Procedimento de Rollback Seguro (Desfazer Alterações com Backup Tag)
Caso precise reverter commits ou descartar alterações de trabalho com segurança:

```bash
# 1. Listar histórico de commits e tags de backup disponíveis:
make rollback-list

# 2. Rollback do último commit local (cria tag backup/rollback_* antes de reverter):
make rollback

# 3. Rollback de múltiplos commits ou para um commit específico:
make rollback STEPS=2
# ou: make rollback COMMIT=399173a

# 4. Rollback sincronizado diretamente com o GitHub (force-with-lease):
make rollback-push
# ou: make rollback-push COMMIT=399173a

# 5. Descartar apenas alterações de trabalho não commitadas locais (clean):
make rollback-clean
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

### 2.3. Erro: `cattle-cluster-agent` em `CrashLoopBackOff` ou `Connection Refused`
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

### 2.4. Erro: `ErrImageNeverPull` ou `ImagePullBackOff`
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

### 2.5. Erro: `stat deploy/helm/iqos-xapp-rdl: no such file or directory`
* **Causa:** Execução de comandos a partir de um diretório incorreto ou ausência do chart local.
* **Solução:** Certifique-se de estar na raiz do repositório (`cd ~/XApp-RDL-F1`) e execute `make helm-deploy`.

---

### 2.6. Erro: `/bin/sh: 1: pytest: not found (Error 127)`
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

### 2.7. Erro: `Could not find a version that satisfies the requirement networkx==3.2.1`
* **Causa:** Versões estritas de pacotes que exigem Python $\ge 3.9$ sendo instaladas em distros com Python 3.8 (ex: Ubuntu 20.04 LTS).
* **Solução:** Utilize operadores flexíveis (`>=`) ou execute os testes diretamente via contêiner:
  ```bash
  docker run --rm -v $(pwd):/app -w /app -u 0 iqos-xapp-rdl:1.1.0 sh -c "pip install -r requirements-dev.txt && pytest tests/ -v"
  ```

---

### 2.8. Erro: `Command 'sudo' not found`
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

### 2.9. Erro no ns-3: `Exception: Refusing to run as root. --enable-sudo will request your password when needed`
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

### 2.10. Erro: `make: *** No rule to make target 'run-experiments'. Stop.`
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

### 2.11. Erro no Git: `fatal: detected dubious ownership in repository at '/root/XApp-RDL-F1'`
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

### 2.12. Erro no ns-3: `CMake Error: CMake 3.25..3.25 or higher is required. You are running version 3.16.3`
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
  3. Se compilar manualmente no diretório do ns-3 (recomenda-se `-j 2` para evitar OOM no WSL2):
     ```bash
     cd ~/ns3-oran-workspace/ns-3-oran
     rm -rf cmake-cache build
     ./ns3 configure -d optimized --enable-examples --enable-tests
     ./ns3 build -j 2
     ```

---

### 2.13. Erro no ns-3: `fatal error: ns3/nr-module.h: No such file or directory`
* **Sintomas:**
  - `scratch/scenario_rdl_tvs_conflict.cc:16:10: fatal error: ns3/nr-module.h: No such file or directory`
* **Causa:** O repositório `ns-3-dev` padrão não inclui o módulo **5G-LENA (`nr`)**. O módulo deve ser clonado dentro de `contrib/nr` para que o CMake gere os headers 5G NR.
* **Solução:**
  1. Execute a clonagem e compilação do 5G-LENA:
     ```bash
     cd ~/ns3-oran-workspace/ns-3-oran
     git clone https://gitlab.com/cttc-lena/nr.git contrib/nr --depth 1
     rm -rf cmake-cache build
     ./ns3 configure -d optimized --enable-examples --enable-tests
     ./ns3 build -j 2
     ```
  2. Ou execute o script automatizado atualizado:
     ```bash
     cd ~/XApp-RDL-F1 && make setup-ns3
     ```

---

### 2.14. Erro / Travamento: WSL2 Congelado e Rancher Inacessível após Build do ns-3 5G-LENA (OOM Lockup & Roteamento de Rede)
* **Sintomas:**
  - A interface web do **Rancher** (`https://localhost:8443` ou `http://localhost:8088`) para de responder com erro de *Timeout* ou *Connection Refused*.
  - Comandos no terminal WSL2 (`wsl.exe`, `bash`, `docker ps`, `kubectl`) congelam ou demoram minutos para responder.
  - O processo `vmmemWSL` no Gerenciador de Tarefas do Windows consome mais de 7.5 GB de RAM, deixando o host sem memória livre.
  - O pod `cattle-cluster-agent` no namespace `cattle-system` entra em `CrashLoopBackOff` ou `Error` com mensagens:
    - `ERROR: https://rancher-server:443/ping is not accessible (Could not connect to server)`
    - `proxy error from 127.0.0.1:6443 while dialing 172.18.0.4:10250, code 502: 502 Bad Gateway`
    - `100% packet loss` no ping entre os containers na rede Docker bridge.

* **Causa Raiz:**
  1. **Esgotamento de Memória (OOM) no WSL2:** A compilação C++ do ns-3 / 5G-LENA via Ninja/CMake sem limitar jobs (`-j`) dispara compilação paralela em todos os núcleos da CPU (ex.: 12 threads). Cada unidade de compilação consome 1.5 GB a 2.5 GB de RAM, ultrapassando os 8 GB padrão do WSL2 e travando o kernel Linux por *memory starvation / swap thrashing*.
  2. **Bloqueio de Roteamento na Bridge Docker:** Após reiniciar o Docker ou recriar containers no WSL2, as tabelas de iptables/nftables podem resetar a política de encaminhamento (`FORWARD`) para `DROP`, bloqueando a comunicação inter-container entre o nó `k3d-rancher-lab-server-0` e o container `rancher-server`.
  3. **Resolução de Hostname vs CoreDNS:** Dentro do pod `cattle-cluster-agent`, o nome `rancher-server` não é resolvido pelo CoreDNS interno do Kubernetes (`10.43.0.10`), exigindo o IP direto do container ou roteamento interno.

* **Procedimento de Recuperação Passo a Passo:**

#### Passo 1: Desbloquear o WSL2 e liberar a memória no PowerShell do Windows
Abra o **PowerShell como Administrador** no Windows:
```powershell
# 1. Finalizar processos travados do cliente WSL
Stop-Process -Name wsl, wslhost, wslrelay -Force -ErrorAction SilentlyContinue

# 2. Reiniciar o serviço do WSL
Restart-Service -Name WSLService -Force

# 3. Desligar o subsistema WSL2 para liberar a RAM
wsl --shutdown
```

#### Passo 2: Configuração Preventiva Definitiva (`~/.wslconfig`)
Para evitar novos travamentos durante futuras compilações do ns-3, crie ou edite o arquivo `C:\Users\<SEU_USUARIO>\.wslconfig` (no PowerShell do Windows):
```powershell
Set-Content -Path "$env:USERPROFILE\.wslconfig" -Value "[wsl2]`nmemory=10GB`nswap=8GB`nprocessors=4" -Encoding UTF8
```
* **`memory=10GB`:** Reserva teto estável de RAM para o WSL2.
* **`swap=8GB`:** Garante espaço de troca seguro para evitar panic no kernel.
* **`processors=4`:** Evita que comandos de build saturem a CPU e disparem 12+ compilações simultâneas.

#### Passo 3: Limpar Travas Órfãs (index.lock / reset-flag) e Restabelecer Roteamento de Rede
Após paradas não planejadas, o Rancher pode entrar em crash loop devido a locks de git ou flags de reset corrompidas. Execute no Ubuntu / WSL2:
```bash
# 1. Limpar travas órfãs do Git e flags de reset nos volumes do Docker
find /var/lib/docker/volumes -name 'index.lock' -delete 2>/dev/null || true
find /var/lib/docker/volumes -name 'reset-flag' -delete 2>/dev/null || true

# 2. Habilitar encaminhamento IPv4 e regras de iptables
sysctl -w net.ipv4.ip_forward=1
iptables -I FORWARD 1 -j ACCEPT
iptables -P FORWARD ACCEPT

# 3. Reiniciar o container do Rancher
docker restart rancher-server
```

#### Passo 4: Reiniciar o Cluster k3d e Ressincronizar o Agente do Rancher
```bash
# 1. Reiniciar os containers do cluster k3d
k3d cluster stop rancher-lab && k3d cluster start rancher-lab

# 2. Obter o IP interno do container rancher-server na rede k3d-rancher-lab
RANCHER_IP=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{if eq $k "k3d-rancher-lab"}}{{$v.IPAddress}}{{end}}{{end}}' rancher-server)
echo "IP do Rancher Server: $RANCHER_IP"

# 3. Atualizar as variáveis de ambiente do cattle-cluster-agent com o IP direto e bypass TLS
docker exec k3d-rancher-lab-server-0 kubectl set env deployment/cattle-cluster-agent -n cattle-system \
  CATTLE_SERVER="https://${RANCHER_IP}:443" \
  CATTLE_SSL_NO_VERIFY="true"

# 4. Reiniciar o rollout do agente
docker exec k3d-rancher-lab-server-0 kubectl rollout restart deployment/cattle-cluster-agent -n cattle-system

# 5. Validar que todos os pods voltaram ao status 1/1 Running
docker exec k3d-rancher-lab-server-0 kubectl get pods -A
```

#### Passo 5: Boas Práticas para Compilação do ns-3 5G-LENA
Sempre que for recompilar o ns-3 ou seus cenários C++, utilize explicitamente a flag `-j 2` ou `-j 3`:
```bash
cd ~/ns3-oran-workspace/ns-3-oran
./ns3 build -j 2
# ou
ninja -j 2
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

 **[Voltar ao Portal de Documentação (docs/README.md)](README.md)** | **[Página Inicial do Repositório (README.md)](../README.md)**
