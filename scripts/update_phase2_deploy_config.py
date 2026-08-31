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
    doc_deploy_f2 = """# Volume 03: Guia de Implantação Helm Exclusivo para RDL Fase 2 (CA-RDL / MARL)

**Documento:** Volume Temático 03  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Procedimento de Deploy Helm Isolado da Release `ricxapp-iqos-xapp-rdl-f2` no Near-RT RIC Existente  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  
**Versão da Release:** `ricxapp-iqos-xapp-rdl-f2` | **Imagem:** `iqos-xapp-rdl:2.0.0`  

---

## 1. Premissas de Implantação da Fase 2

Na infraestrutura operacional de testes e produção:
1. O **Near-RT RIC Platform (`ricplt`)** já está provisionado e ativo (DBAAS Redis na porta `6379`, E2Term na porta `36422/SCTP`, E2Mgr e Route Generator na porta `4561`).
2. As **3 Reference xApps (`ricxapp`)** já estão implantadas e em execução:
   - `ricxapp-qos-xslice` (porta HTTP `8082`, RMR `4562`)
   - `ricxapp-energy-saving` (porta HTTP `8084`, RMR `4563`)
   - `ricxapp-traffic-steering` (porta HTTP `8086`, RMR `4564`)
3. A **xApp RDL Fase 2 (CA-RDL)** deve ser implantada de forma **isolada e independente**, com identificação exclusiva de release:
   - **Helm Release Name:** `ricxapp-iqos-xapp-rdl-f2`
   - **Deployment Name:** `ricxapp-iqos-xapp-rdl-f2`
   - **Tag da Imagem:** `2.0.0`
   - **Target de Execução:** `make helm-deploy-f2`

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        Cluster Kubernetes: Namespace ricxapp                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [ricxapp-qos-xslice]          (Existente - Já em Execução)                           │
│   [ricxapp-energy-saving]       (Existente - Já em Execução)                           │
│   [ricxapp-traffic-steering]    (Existente - Já em Execução)                           │
│                                                                                        │
│   ─────────────────────────── [Deploy Isolado Fase 2] ────────────────────────────     │
│   [ricxapp-iqos-xapp-rdl-f2]    (v2.0.0 - CA-RDL / MARL - Release Dedicada)           │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Comandos Operacionais de Deploy da Fase 2

### 2.1. Implantar Exclusivamente a xApp RDL Fase 2:
```bash
# Executa o build da imagem 2.0.0, importação no k3d e deploy da release 'ricxapp-iqos-xapp-rdl-f2'
make helm-deploy-f2
```
*Esse comando não reinstala o Near-RT RIC nem interfere nas 3 Reference xApps existentes.*

### 2.2. Verificar o Status da xApp RDL Fase 2:
```bash
make status-f2
# ou: kubectl get pods -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 -o wide
```

### 2.3. Inspecionar Logs do Motor MARL/MAPPO em Tempo Real:
```bash
make logs-f2
# ou: kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 -f
```

### 2.4. Validar Endpoints HTTP e Telemetria Prometheus:
```bash
# Testa o healthcheck e métricas cognitivas da Fase 2
make test-f2

# Chamadas manuais via cURL:
curl -i http://localhost:8080/health
curl -s http://localhost:8081/metrics | grep -E "rdl_|marl_"
```

### 2.5. Remover Apenas a xApp RDL Fase 2:
```bash
# Desinstala somente a release 'ricxapp-iqos-xapp-rdl-f2' mantendo o restante da infraestrutura intacta
make helm-uninstall-f2
```

---

## 3. Resumo dos Targets do Makefile para a Fase 2

| Comando Makefile | Ação Executada | Escopo de Impacto |
| :--- | :--- | :--- |
| **`make test`** | Executa os 18 testes unitários (pytest) | Local |
| **`make helm-deploy-f2`** | Instala/Atualiza a release `ricxapp-iqos-xapp-rdl-f2` (v2.0.0) | Namespace `ricxapp` (apenas RDL F2) |
| **`make helm-uninstall-f2`** | Desinstala a release `ricxapp-iqos-xapp-rdl-f2` | Namespace `ricxapp` (apenas RDL F2) |
| **`make status-f2`** | Exibe o status detalhado dos pods no namespace `ricxapp` | Somente leitura |
| **`make logs-f2`** | Abre streaming dos logs da xApp RDL Fase 2 | Somente leitura |
| **`make test-f2`** | Testa `/health` (`:8080`) e `/metrics` (`:8081`) da Fase 2 | Somente leitura |
| **`make run-suite`** | Executa simulações ns-3 e benchmark de Machine Learning | Suíte experimental |
"""
    with open(os.path.join(P2_DIR, "docs", "03_guia_deploy_helm_e_k8s.md"), "w", encoding="utf-8") as f:
        f.write(doc_deploy_f2)
    print("[OK] docs/03_guia_deploy_helm_e_k8s.md atualizado com as diretrizes isoladas da Fase 2.")

    # 4. Atualizar README.md da Fase 2
    with open(os.path.join(P2_DIR, "README.md"), "r", encoding="utf-8") as f:
        readme = f.read()

    readme_updated = readme.replace("make helm-deploy", "make helm-deploy-f2")
    with open(os.path.join(P2_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_updated)
    print("[OK] README.md da Fase 2 atualizado para referenciar 'make helm-deploy-f2'.")

if __name__ == "__main__":
    update_deploy_config()
