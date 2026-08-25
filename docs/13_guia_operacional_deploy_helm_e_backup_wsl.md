# Guia Operacional: Clone, Deploy Helm e Backup do Ambiente WSL Ubuntu 20.04

**Documento:** Procedimento Operacional Padrão (SOP)  
**Projeto:** xApp RDL (Resource and Decision Layer)  
**Ambiente Alvo:** Servidor de Produção / Cluster Near-RT RIC (`SAC-10806` / WSL Ubuntu 20.04)  
**Data:** 25/08/2026  

---

## 1. Clonagem e Sincronização do Repositório Fase 1

No terminal do seu servidor Ubuntu (`SAC-10806` ou WSL):

```bash
# Se o repositório já existir no servidor:
cd ~/XApp-RDL-F1
git pull origin main

# OU se for uma nova instalação limpa do zero:
cd ~
git clone https://github.com/georgebarbosa3090/XApp-RDL-F1.git
cd XApp-RDL-F1
```

---

## 2. Construção da Imagem Docker e Smoke Test de Validação

Antes de aplicar os manifestos no Kubernetes, valide a integridade do container em modo standalone:

```bash
# 1. Reconstruir a imagem Docker otimizada (multi-stage com wheels)
docker build --file docker/Dockerfile --tag iqos-xapp-rdl:1.1.0 .

# 2. Executar o container de validação com Fake SDL ativado
docker rm -f xapp-rdl-test 2>/dev/null || true
docker run -d --name xapp-rdl-test -p 8090:8080 -p 8091:8081 -e USE_FAKE_SDL=true iqos-xapp-rdl:1.1.0

# 3. Aguardar estabilização dos serviços HTTP e Prometheus
sleep 3

# 4. Validar o endpoint de saúde (deve retornar HTTP 200 OK e JSON {"status":"UP"})
curl -i http://localhost:8090/health

# 5. Validar a exportação de métricas do Prometheus
curl http://localhost:8091/metrics | grep -E "rdl_|dl_"

# 6. Inspecionar logs estruturados e remover o container de teste
docker logs xapp-rdl-test
docker rm -f xapp-rdl-test
```

---

## 3. Empacotamento Helm e Deploy no Cluster Near-RT RIC

```bash
# 1. Validar a sintaxe dos templates Helm (Lint)
helm lint deploy/helm/iqos-xapp-rdl

# 2. Empacotar o Chart em um arquivo binário comprimido (.tgz)
helm package deploy/helm/iqos-xapp-rdl

# 3. Instalar / Atualizar a release no namespace ricxapp do Kubernetes
helm upgrade --install ricxapp-iqos-xapp-rdl ./iqos-xapp-rdl-1.1.0.tgz \
  --namespace ricxapp \
  --create-namespace

# 4. Acompanhar a inicialização dos Pods em tempo real
kubectl get pods -n ricxapp -l app=ricxapp-iqos-xapp-rdl -w
```

---

## 4. Procedimento de Backup Completo do WSL Ubuntu 20.04

Para garantir a preservação de todo o estado do cluster, dependências compiladas, módulos SCTP e configurações do Near-RT RIC, utilize o método de exportação de imagem do WSL.

### 4.1. Backup Snapshot Completo da Máquina Virtual (via PowerShell do Windows)

Abra o **PowerShell do Windows como Administrador**:

```powershell
# 1. Identificar o nome exato da distribuição instalada
wsl --list --verbose

# 2. Criar o diretório de destino dos backups no Windows
New-Item -ItemType Directory -Force -Path "C:\BackupsWSL"

# 3. Desligar o WSL para garantir consistência total do disco
wsl --shutdown

# 4. Exportar a imagem completa do sistema de arquivos para arquivo .tar
wsl --export Ubuntu-20.04 "C:\BackupsWSL\ubuntu-20.04-backup-$(Get-Date -Format 'yyyyMMdd').tar"
```

---

### 4.2. Como Restaurar o Backup do WSL (se necessário no futuro)

```powershell
# Criar diretório onde a imagem restaurada residirá
New-Item -ItemType Directory -Force -Path "C:\WSL\Ubuntu20"

# Importar o snapshot
wsl --import Ubuntu-20.04-Restaurado "C:\WSL\Ubuntu20" "C:\BackupsWSL\ubuntu-20.04-backup-YYYYMMDD.tar"

# Iniciar a distribuição restaurada
wsl -d Ubuntu-20.04-Restaurado
```

---

### 4.3. Alternativa: Backup Rápido de Códigos e Configurações Kube (sem desligar o WSL)

No terminal do próprio Ubuntu / WSL:

```bash
mkdir -p /mnt/c/BackupsWSL
tar -czvf /mnt/c/BackupsWSL/backup-configs-$(date +%Y%m%d).tar.gz \
  ~/XApp-RDL-F1 \
  ~/XApp-RDL-F2 \
  ~/.kube \
  ~/.config \
  /etc/hosts
```

---

## 5. Comandos de Diagnóstico e Monitoramento Pós-Deploy

```bash
# Inspecionar logs da xApp em execução no Kubernetes
kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl -f

# Checar serviços expostos (RMR e HTTP)
kubectl get svc -n ricxapp

# Verificar consumo de recursos da xApp
kubectl top pod -n ricxapp -l app=ricxapp-iqos-xapp-rdl
```
