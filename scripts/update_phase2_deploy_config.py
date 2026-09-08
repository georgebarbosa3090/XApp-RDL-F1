#!/usr/bin/env python3
"""
Atualiza o pipeline de deploy Helm dedicado para a Fase 2 (CA-RDL / MARL):
- Cria/copia scripts/deploy_rdl_phase2.sh
- Configura o release name exclusivo: ricxapp-iqos-xapp-rdl-f2
- Atualiza Makefile da Fase 2 e Fase 1
- Atualiza docs/03_guia_deploy_helm_e_k8s.md e README.md da Fase 2
"""

import os
import shutil

P1_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
P2_DIR = os.path.abspath(os.path.join(P1_DIR, "..", "iqos-xapp-rdl-phase2"))

def update_deploy_config():
    print(f"Atualizando configuracao de deploy Helm isolado para a Fase 2 em: {P2_DIR}")

    # 1. Copiar scripts/deploy_rdl_phase2.sh para Fase 2
    src_sh = os.path.join(P1_DIR, "scripts", "deploy_rdl_phase2.sh")
    dst_sh = os.path.join(P2_DIR, "scripts", "deploy_rdl_phase2.sh")
    shutil.copy2(src_sh, dst_sh)
    print(f"[OK] scripts/deploy_rdl_phase2.sh sincronizado.")

    # 2. Atualizar Makefile da Fase 2
    makefile_p2 = """.PHONY: build build-no-cache test validate package onboard install status status-f2 logs logs-f2 smoke-test uninstall helm-deploy-f2 helm-upgrade-f2 helm-uninstall-f2 helm-test-f2 test-f2 test-3xapps cluster-create cluster-delete cluster-recreate setup-ns3 run-baseline run-rdl run-experiments run-suite analyze-benchmarks view-results push-results sync auto-sync rollback rollback-push rollback-clean rollback-list

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 2.0.0
CHART_DIR ?= deploy/helm/iqos-xapp-rdl
NAMESPACE_RIC ?= ricplt
NAMESPACE ?= ricxapp
RELEASE_NAME_F2 ?= ricxapp-iqos-xapp-rdl-f2
CLUSTER_NAME ?= rancher-lab

# -------------------------------------------------------------
# Build e Testes Locais da xApp RDL Fase 2
# -------------------------------------------------------------
build:
	docker build --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

build-no-cache:
	docker build --no-cache --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

test:
	PYTHONPATH=. pytest tests/ -v

# -------------------------------------------------------------
# Deploy Helm Exclusivo para RDL Fase 2 (CA-RDL / MARL)
# Premissa: Near-RT RIC e as 3 Reference xApps ja estao rodando!
# -------------------------------------------------------------
helm-deploy-f2:
	@echo "Implantando/Atualizando exclusivamente a xApp RDL Fase 2 ($(RELEASE_NAME_F2))..."
	bash scripts/deploy_rdl_phase2.sh

helm-upgrade-f2:
	@echo "Executando Helm Upgrade da release $(RELEASE_NAME_F2)..."
	helm upgrade --install $(RELEASE_NAME_F2) $(CHART_DIR) \\
	  --namespace $(NAMESPACE) \\
	  --set image.repository=$(IMAGE_NAME) \\
	  --set image.tag=$(IMAGE_TAG) \\
	  --set image.pullPolicy=Never \\
	  --set fullnameOverride=$(RELEASE_NAME_F2) \\
	  --set env.useFakeSdl="false" \\
	  --set env.rmrWaitForReady="false" \\
	  --set env.enableTorch="true"

helm-uninstall-f2:
	@echo "Removendo exclusivamente a xApp RDL Fase 2 ($(RELEASE_NAME_F2))..."
	helm uninstall $(RELEASE_NAME_F2) -n $(NAMESPACE) || echo "Release $(RELEASE_NAME_F2) nao encontrada."

status-f2:
	@echo "=== Status das xApps no Namespace $(NAMESPACE) ==="
	@kubectl get pods -n $(NAMESPACE) -o wide
	@echo "\n=== Pod da xApp RDL Fase 2 ==="
	@kubectl get pods -n $(NAMESPACE) -l app=$(RELEASE_NAME_F2) -o wide

logs-f2:
	kubectl logs -l app=$(RELEASE_NAME_F2) -n $(NAMESPACE) -f

test-f2:
	@echo "Testando endpoints da xApp RDL Fase 2 (CA-RDL / MARL)..."
	@curl -i http://localhost:8080/health || true
	@echo "\nMétricas Prometheus:"
	@curl -s http://localhost:8081/metrics | grep -E "rdl_|marl_" || true

test-3xapps:
	@echo "Testando integridade das 3 Reference xApps no cluster..."
	bash scripts/verify_3_xapps.sh

# -------------------------------------------------------------
# Gestão do Cluster k3d (se necessário)
# -------------------------------------------------------------
cluster-create:
	@echo "Criando cluster k3d $(CLUSTER_NAME)..."
	k3d cluster create $(CLUSTER_NAME) --servers 1 --agents 0 --port "36422:36422/SCTP@server:0" --port "8080:8080@server:0" --port "8081:8081@server:0" --port "4560:4560@server:0" --port "4561:4561@server:0"
	mkdir -p ~/.kube
	k3d kubeconfig get $(CLUSTER_NAME) > ~/.kube/config

cluster-delete:
	k3d cluster delete $(CLUSTER_NAME)

# -------------------------------------------------------------
# Simulações ns-3 e Pipelines Experimentais
# -------------------------------------------------------------
setup-ns3:
	bash scripts/setup_ns3.sh

run-baseline:
	bash scripts/run_baseline_experiment.sh

run-rdl:
	bash scripts/run_rdl_experiment.sh

run-experiments:
	bash scripts/run_full_experiment.sh

run-suite:
	python3 scripts/run_experiment_suite.py

analyze-benchmarks:
	python3 scripts/run_experiment_suite.py

view-results:
	@cat experiments/results/relatorio_comparativo.md

push-results:
	@echo "Sincronizando resultados com o GitHub..."
	git add experiments/results/ docs/ scripts/
	git commit -m "chore(experiments): upload latest ns-3 MARL benchmark results [skip ci]" || echo "Nenhum dado novo."
	git push origin main || echo "Aviso no push."

sync:
	@bash scripts/git_sync.sh "$(MSG)"

auto-sync:
	@bash scripts/git_auto_sync.sh $(INTERVAL)
"""
    with open(os.path.join(P2_DIR, "Makefile"), "w", encoding="utf-8") as f:
        f.write(makefile_p2)
    print("[OK] Makefile da Fase 2 atualizado com 'make helm-deploy-f2'.")

    # 3. Atualizar docs/03_guia_deploy_helm_e_k8s.md da Fase 2
    doc_deploy_f2 = """# Volume 03: Guia de Implantação e Automação de Deploy (Helm & K8s Nativo)

**Documento:** Volume Temático 03  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Procedimentos de Implantação do Zero (Greenfield) e Deploy Isolado (Brownfield) no Cluster Kubernetes  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  
**Versão da Release:** `ricxapp-iqos-xapp-rdl-f2` | **Imagem:** `iqos-xapp-rdl:2.0.0`  

---

## 1. Visão Geral e Matriz de Cenários de Deploy

O ciclo de vida da **xApp RDL Fase 2 (CA-RDL / MARL)** suporta dois modos de implantação no cluster Kubernetes (k3d / K8s puro):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MATRIZ DE DEPLOY DA FASE 2                                │
├───────────────────────────────────┬────────────────────────────────────────────────────┤
│ Cenário A: Greenfield (Do Zero)   │ Cluster novo ou limpo:                             │
│                                   │ 1. Cria cluster k3d com portas O-RAN expostas      │
│                                   │ 2. Cria namespaces 'ricplt' e 'ricxapp'            │
│                                   │ 3. Instala Near-RT RIC (DBAAS Redis, RMR)          │
│                                   │ 4. Instala Reference xApps (QoS, Energy, TS, ...)  │
│                                   │ 5. Instala xApp RDL Fase 2 (CA-RDL / MARL)         │
├───────────────────────────────────┼────────────────────────────────────────────────────┤
│ Cenário B: Brownfield (Isolado)   │ Infraestrutura já ativa:                           │
│                                   │ 1. Mantém Near-RT RIC e Reference xApps operando   │
│                                   │ 2. Instala/Atualiza apenas a release               │
│                                   │    'ricxapp-iqos-xapp-rdl-f2' (v2.0.0)             │
└───────────────────────────────────┴────────────────────────────────────────────────────┘
```

---

## 2. Cenário A: Implantação Completa do Zero (Greenfield — Sem RIC, Sem xApps, Sem RDL)

Este cenário é o recomendado quando você está iniciando em uma máquina nova ou após recriar o ambiente. **Nenhum componente O-RAN precisa estar previamente instalado.**

### 2.1. Passo 1: Criar o Cluster Kubernetes (k3d) com Portas O-RAN Expostas
```bash
# Cria o cluster k3d com as portas O-RAN (SCTP 36422, HTTP 8080/8081, RMR 4560/4561):
make cluster-create

# Ou comando equivalente direto:
k3d cluster create rancher-lab \\
  --servers 1 --agents 0 \\
  --port "36422:36422/SCTP@server:0" \\
  --port "8080:8080@server:0" \\
  --port "8081:8081@server:0" \\
  --port "4560:4560@server:0" \\
  --port "4561:4561@server:0"
mkdir -p ~/.kube && k3d kubeconfig get rancher-lab > ~/.kube/config
```

### 2.2. Passo 2: Criar os Namespaces O-RAN
```bash
kubectl create namespace ricplt --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ricxapp --dry-run=client -o yaml | kubectl apply -f -
```

### 2.3. Passo 3: Implantar a Plataforma Near-RT RIC (`ricplt`)
Implanta o DBAAS Redis (Shared Data Layer - SDL) e serviços da plataforma:
```bash
# Aplica o manifesto do Near-RT RIC:
kubectl apply -f deploy/kubernetes/near-rt-ric.yaml -n ricplt

# Aguarda a prontidão do Redis DBAAS:
kubectl rollout status deployment/deployment-ricplt-dbaas-redis -n ricplt --timeout=90s
```

### 2.4. Passo 4: Implantar as Reference xApps (`ricxapp`)
Implanta as Reference xApps que fornecerão métricas e atuarão nas decisões de rede:
```bash
# Opção A: Script automatizado das 6 Reference xApps
bash scripts/deploy_reference_xapps.sh

# Opção B: Via Kustomize / Kubectl direto:
kubectl apply -f deploy/kubernetes/xapp-qos-xslice.yaml -n ricxapp
kubectl apply -f deploy/kubernetes/xapp-energy-saving.yaml -n ricxapp
kubectl apply -f deploy/kubernetes/xapp-traffic-steering.yaml -n ricxapp

# Valida o status dos pods das xApps:
kubectl get pods -n ricxapp -o wide
```

### 2.5. Passo 5: Compilar e Implantar a xApp RDL Fase 2 (CA-RDL / MARL)
```bash
# 1. Build da imagem Docker da Fase 2 (v2.0.0 com PyTorch / MARL):
make build

# 2. Deploy Helm da release dedicada:
make helm-deploy-f2
```

### 2.6. Pipeline Automatizado de Deploy Completo (Tudo em 1 Comando)
Você também pode executar a suíte completa de ponta a ponta:
```bash
# Executa a criação dos namespaces, deploy do RIC, deploy das 3 xApps e deploy da RDL:
bash scripts/deploy_k8s.sh --with-rdl
```

---

## 3. Cenário B: Implantação Incremental / Isolada (Brownfield — RIC e xApps já Ativos)

Utilize este cenário quando o Near-RT RIC e as Reference xApps já estiverem rodando no cluster e você deseja implantar ou atualizar **apenas** a xApp RDL Fase 2:

### 3.1. Implantar/Atualizar Exclusivamente a Release da Fase 2:
```bash
make helm-deploy-f2
```
*Premissa:* Não reinstala nem interrompe os componentes do `ricplt` nem as Reference xApps existentes.

### 3.2. Atualização Declarativa (Helm Upgrade):
```bash
make helm-upgrade-f2
```

---

## 4. Validação, Healthcheck e Monitoramento

### 4.1. Visualizar Status dos Pods em Todos os Namespaces:
```bash
# Namespace da Plataforma RIC:
kubectl get pods -n ricplt -o wide

# Namespace das xApps e RDL Fase 2:
kubectl get pods -n ricxapp -o wide
# ou: make status-f2
```

### 4.2. Inspecionar Logs da xApp RDL Fase 2 em Tempo Real:
```bash
make logs-f2
# ou: kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 -f
```

### 4.3. Testar Endpoints HTTP e Telemetria Prometheus:
```bash
# Teste automatizado dos endpoints da Fase 2:
make test-f2

# Teste manual de Liveness / Readiness:
curl -i http://localhost:8080/health

# Métricas cognitivas do motor MAPPO / MARL:
curl -s http://localhost:8081/metrics | grep -E "rdl_|marl_"

# Teste de integridade das Reference xApps:
make test-3xapps
```

---

## 5. Limpeza e Reset do Ambiente (Tear Down)

### 5.1. Desinstalar Apenas a xApp RDL Fase 2:
```bash
make helm-uninstall-f2
```

### 5.2. Desinstalar Todas as xApps (RDL Fase 1 e Fase 2):
```bash
make uninstall-all-rdl
```

### 5.3. Limpeza Completa (Destruir Cluster e Recursos):
```bash
# Remove o cluster k3d e todos os contêineres/volumes associados:
make cluster-delete
```

---

## 6. Mapeamento de Portas e Serviços O-RAN

| Serviço / Componente | Namespace | Tipo | Porta do Contêiner | Porta Mapeada no Host | Finalidade |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **xApp RDL F2 (HTTP)** | `ricxapp` | ClusterIP / NodePort | `8080` | `8080` | Sondas de Liveness/Readiness e API REST |
| **xApp RDL F2 (Metrics)** | `ricxapp` | ClusterIP / NodePort | `8081` | `8081` | Telemetria Prometheus e Métricas MARL |
| **xApp RDL F2 (RMR)** | `ricxapp` | ClusterIP | `4560` | `4560` | Barramento de Mensagens RMR O-RAN |
| **DBAAS (Redis SDL)** | `ricplt` | ClusterIP | `6379` | `6379` | Shared Data Layer (Estado e Contexto) |
| **E2Term / Mock** | `ricplt` | ClusterIP | `36422` | `36422/SCTP` | Terminação E2 / Conexão com simulador ns-3 |
| **QoS xSlice xApp** | `ricxapp` | ClusterIP | `8082` / `4562` | `8082` | Fatiamento de Rede e Controle de Banda |
| **Energy Saving xApp** | `ricxapp` | ClusterIP | `8084` / `4563` | `8084` | Desligamento de Células / Economia de Energia |
| **Traffic Steering xApp** | `ricxapp` | ClusterIP | `8086` / `4564` | `8086` | Handover e Redirecionamento de Tráfego |

---

## 7. Resumo dos Targets do Makefile

| Comando Makefile | Ação Executada | Escopo de Impacto |
| :--- | :--- | :--- |
| **`make cluster-create`** | Provisiona cluster k3d com portas O-RAN | Infraestrutura K8s |
| **`make cluster-delete`** | Destrói cluster k3d e limpa recursos | Infraestrutura K8s |
| **`make build`** | Compila a imagem Docker `iqos-xapp-rdl:2.0.0` | Imagem Local |
| **`make test`** | Executa os testes unitários (pytest) | Local |
| **`make helm-deploy-f2`** | Deploy exclusivo da release `ricxapp-iqos-xapp-rdl-f2` | Namespace `ricxapp` |
| **`make helm-upgrade-f2`** | Upgrade da release `ricxapp-iqos-xapp-rdl-f2` | Namespace `ricxapp` |
| **`make helm-uninstall-f2`** | Remove a release `ricxapp-iqos-xapp-rdl-f2` | Namespace `ricxapp` |
| **`make status-f2`** | Exibe status detalhado dos pods no namespace `ricxapp` | Diagnóstico |
| **`make logs-f2`** | Streaming de logs da xApp RDL Fase 2 | Diagnóstico |
| **`make test-f2`** | Testa endpoints `/health` e `/metrics` da Fase 2 | Diagnóstico |
| **`make test-3xapps`** | Verifica saúde das 3 Reference xApps | Diagnóstico |
"""
    with open(os.path.join(P2_DIR, "docs", "03_guia_deploy_helm_e_k8s.md"), "w", encoding="utf-8") as f:
        f.write(doc_deploy_f2)
    print("[OK] docs/03_guia_deploy_helm_e_k8s.md atualizado com as diretrizes completas (Greenfield e Brownfield) da Fase 2.")

    # 4. Atualizar README.md da Fase 2
    with open(os.path.join(P2_DIR, "README.md"), "r", encoding="utf-8") as f:
        readme = f.read()

    readme_updated = readme.replace("make helm-deploy", "make helm-deploy-f2")
    with open(os.path.join(P2_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_updated)
    print("[OK] README.md da Fase 2 atualizado para referenciar 'make helm-deploy-f2'.")

if __name__ == "__main__":
    update_deploy_config()
