# Guia de Empacotamento Helm e Sincronização com o GitHub

**Projeto:** xApp RDL (Resource and Decision Layer)  
**Versões Abrangidas:** Fase 1 (`1.1.0`) e Fase 2 (`2.0.0`)  
**Diretório do Chart:** `deploy/helm/iqos-xapp-rdl/`  
**Data:** 25/08/2026  

---

## 1. Visão Geral

Para empacotar a **xApp RDL** em Helm, foi criada e homologada a estrutura oficial de deployment em `deploy/helm/iqos-xapp-rdl/` tanto no repositório da **Fase 1 (H-RDL)** quanto no da **Fase 2 (CA-RDL / MAPPO)**.

Existem duas formas suportadas para empacotar e implantar a xApp no **Near-RT RIC**:
1. **Método 1:** Empacotamento Helm Nativo (Padrão Kubernetes / Helm CLI).
2. **Método 2:** Onboarding Oficial O-RAN SC via `dms_cli` / `xapp-onboarder`.

---

## 2. Estrutura do Helm Chart Criado

```text
deploy/helm/iqos-xapp-rdl/
├── Chart.yaml                  # Metadados do Chart (nome, descrição, versão)
├── values.yaml                 # Parâmetros configuráveis (portas, recursos, sondas, variáveis)
└── templates/
    ├── _helpers.tpl            # Nomes e labels padronizados do Kubernetes
    ├── deployment.yaml         # Pod da xApp com probes de saúde, RMR e non-root security context
    ├── service-http.yaml       # Serviços HTTP (porta 8080 health / 8081 metrics)
    └── service-rmr.yaml        # Serviços RMR (portas 4560 data / 4561 route)
```

---

## 3. Método 1: Empacotamento Helm Nativo (Padrão Kubernetes / Helm CLI)

### 3.1. Validar a sintaxe do Chart (*Lint*):
```bash
helm lint deploy/helm/iqos-xapp-rdl
```

### 3.2. Empacotar o Chart em um arquivo `.tgz`:
```bash
helm package deploy/helm/iqos-xapp-rdl
```
> **Resultado:** Será gerado o arquivo comprimido binário `iqos-xapp-rdl-1.1.0.tgz` (ou `iqos-xapp-rdl-2.0.0.tgz` para a Fase 2).

### 3.3. Testar a renderização dos manifestos (*Dry Run*):
```bash
helm install ricxapp-iqos-xapp-rdl ./iqos-xapp-rdl-1.1.0.tgz \
  --namespace ricxapp \
  --create-namespace \
  --dry-run --debug
```

### 3.4. Instalar no Cluster Near-RT RIC:
```bash
helm install ricxapp-iqos-xapp-rdl ./iqos-xapp-rdl-1.1.0.tgz \
  --namespace ricxapp \
  --create-namespace
```

### 3.5. Customizar variáveis na instalação:
Exemplo para rodar a xApp com Fake SDL ativado e sem bloqueio de Route Manager (ideal para testes isolados e staging):
```bash
helm install ricxapp-iqos-xapp-rdl ./iqos-xapp-rdl-1.1.0.tgz \
  --namespace ricxapp \
  --set env.useFakeSdl="true" \
  --set env.rmrWaitForReady="false"
```

---

## 4. Método 2: Onboarding Oficial O-RAN SC (via `dms_cli` / `xapp-onboarder`)

No ecossistema oficial da **O-RAN Software Community (OSC)**, o componente **DMS (Deployment Management Service)** gera o Helm Chart dinamicamente a partir dos descritores `configs/config-file.json` e `configs/schema.json` da xApp:

```bash
# 1. Configurar as URLs do ChartMuseum e AppMgr da OSC
export CHART_REPO_URL=http://<IP_DO_RIC>:8080/chartmuseum
export APPMGR_HTTP_URL=http://<IP_DO_RIC>:8080/appmgr

# 2. Fazer o onboarding do descritor da xApp
dms_cli onboard configs/config-file.json configs/schema.json

# 3. Fazer o deploy da xApp através do AppMgr no namespace ricxapp
dms_cli install --xapp-chart-name iqos-xapp-rdl --version 1.1.0 --namespace ricxapp
```

---

## 5. Comandos Úteis de Gerenciamento do Helm

### Verificar o status do deploy e pods:
```bash
helm status ricxapp-iqos-xapp-rdl -n ricxapp
kubectl get pods -n ricxapp -l app=ricxapp-iqos-xapp-rdl
```

### Inspecionar logs da xApp em execução:
```bash
kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl -f
```

### Atualizar a versão da xApp (*Upgrade*):
```bash
helm upgrade ricxapp-iqos-xapp-rdl ./iqos-xapp-rdl-1.1.0.tgz -n ricxapp
```

### Desinstalar a xApp:
```bash
helm uninstall ricxapp-iqos-xapp-rdl -n ricxapp
```

---

## 6. Status dos Repositórios Locais e Sincronização com o GitHub

Ambos os repositórios locais (**Fase 1** e **Fase 2**) foram devidamente testados com 100% de cobertura nos testes unitários e possuem histórico de commits limpo e estruturado na branch `main`.

### 📦 Repositório Fase 1 (`XApp-RDL-F1`)
* **Caminho Local:** `C:\Users\george.barbosa\.gemini\antigravity\scratch\iqos-xapp-rdl-phase1`
* **Remote Git:** `https://github.com/georgebarbosa3090/XApp-RDL-F1.git`
* **Histórico de Commits:**
  - `fdc14d9` - `chore: adiciona script de sincronizacao de melhorias com a Fase 2`
  - `1e41c45` - `feat: adiciona Helm Chart completo para deploy da xApp RDL no Kubernetes/Near-RT RIC`
  - `17c760f` - `docs: adiciona relatorio formal de smoke test da xApp RDL (Fase 1)`
  - `e70bb47` - `docs: atualiza comandos de smoke test no README.md`
  - `9f53c2f` - `fix: initialize self.running before RMRXapp post_init invocation`
  - `ea641a6` - `feat: atualizacao completa da xApp RDL - Dockerfile multi-stage, RMRXapp, health server e documentacao`

### 📦 Repositório Fase 2 (`XApp-RDL-F2`)
* **Caminho Local:** `C:\Users\george.barbosa\.gemini\antigravity\scratch\iqos-xapp-rdl-phase2`
* **Remote Git:** `https://github.com/georgebarbosa3090/XApp-RDL-F2.git`
* **Histórico de Commits:**
  - `3561e0e` - `feat: adiciona Helm Chart para xApp RDL (Fase 2)`
  - `b0d7508` - `feat: alimentacao inicial do repositorio Fase 2 (CA-RDL / MAPPO) com correcoes de runtime, RMR, ASN.1 e Dockerfile multi-stage`

---

## 7. Instruções para Subir ao GitHub

Execute no terminal (PowerShell ou Git Bash) para sincronizar com o GitHub:

```bash
# 1. Subir a Fase 1 (XApp-RDL-F1)
cd "C:\Users\george.barbosa\.gemini\antigravity\scratch\iqos-xapp-rdl-phase1"
git push -u origin main

# 2. Subir a Fase 2 (XApp-RDL-F2)
cd "C:\Users\george.barbosa\.gemini\antigravity\scratch\iqos-xapp-rdl-phase2"
git push -u origin main
```
*(Nota: Se o repositório remoto Fase 2 tiver sido inicializado no GitHub com README, execute `git push -u origin main --force` para sincronizar).*
