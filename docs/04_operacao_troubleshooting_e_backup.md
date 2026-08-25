# Volume 04: Operação, Troubleshooting e Procedimentos de Backup

**Documento:** Volume Temático 04  
**Projeto:** xApp RDL (Resource and Decision Layer)  
**Escopo:** Procedimento Operacional Padrão (SOP), Diagnósticos de Falha, Soluções Offline e Backup/Restore WSL2  
**Data de Consolidação:** 25/08/2026  

---

## 1. Procedimento Operacional Padrão (SOP)

### 1.1. Sincronização e Reconstrução do Ambiente no Servidor
```bash
cd ~/XApp-RDL-F1

# 1. Atualização limpa com o repositório central
git fetch origin
git reset --hard origin/main

# 2. Reconstrução da imagem Docker com cache inteligente
docker build --file docker/Dockerfile --tag iqos-xapp-rdl:1.1.0 .

# 3. Importação nos nós do containerd (k3d)
for node in $(docker ps --format '{{.Names}}' | grep -E "k3d-.*-(server|agent)"); do
    echo "Carregando no nó: $node..."
    docker save iqos-xapp-rdl:1.1.0 | docker exec -i $node ctr images import -
done
```

---

## 2. Troubleshooting e Diagnósticos Comuns

### 2.1. Erro: `stat deploy/helm/iqos-xapp-rdl: no such file or directory`
* **Causa:** Tentativa de execução de comandos Helm antes de clonar ou sincronizar a pasta do Chart no servidor.
* **Solução:** Execute `make helm-deploy` ou recrie a estrutura de arquivos do Chart via script offline documentado no repositório.

### 2.2. Erro: `ErrImageNeverPull` ou `ImagePullBackOff`
* **Causa:** O Kubernetes tentou buscar a imagem `iqos-xapp-rdl:1.1.0` no Docker Hub público em vez de usar o containerd local do nó onde o Pod foi agendado.
* **Solução:**
  1. Carregue a imagem em todos os nós containerd com o laço `for node in $(docker ps --format '{{.Names}}' | grep -E "k3d-.*-(server|agent)"); do docker save ... | docker exec -i $node ctr images import -; done`.
  2. Garanta que o Helm aplique `--set image.pullPolicy=Never`.

### 2.3. Erro: `cattle-cluster-agent` em `CrashLoopBackOff` no Rancher
* **Causa:** O agente do Rancher tenta acessar `127.0.0.1:8443` (loopback interno do Pod) ou sofre rejeição TLS.
* **Solução:** Conecte o container do Rancher na rede do k3d (`docker network connect k3d-rancher-lab rancher-server`) e aponte a URL interna do agente para `https://rancher-server:443` com `CATTLE_SSL_NO_VERIFY=true`.

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
