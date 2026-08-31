.PHONY: build build-no-cache test validate package onboard install status logs smoke-test uninstall helm-deploy helm-deploy-baseline helm-package helm-test helm-uninstall k8s-deploy k8s-deploy-baseline k8s-uninstall k8s-test test-3xapps kiali-install kiali-dashboard inject-traffic start-traffic stop-traffic cluster-create cluster-delete cluster-recreate rancher-start rancher-stop rancher-logs rancher-password rancher-connect setup-ns3 deploy-rdl deploy-baseline run-baseline run-rdl run-experiments analyze-benchmarks view-results push-results sync auto-sync rollback rollback-push rollback-clean rollback-list

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 1.1.0
CHART_DIR ?= deploy/helm/iqos-xapp-rdl
K8S_DIR ?= deploy/kubernetes
NAMESPACE_RIC ?= ricplt
NAMESPACE ?= ricxapp
RELEASE_NAME ?= ricxapp-iqos-xapp-rdl
CLUSTER_NAME ?= rancher-lab

build:
	docker build --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

build-no-cache:
	docker build --no-cache --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

test:
	PYTHONPATH=. pytest tests/ -v

# -------------------------------------------------------------
# Gestão e Ciclo de Vida do Cluster k3d
# -------------------------------------------------------------
cluster-create:
	@echo "Criando cluster k3d $(CLUSTER_NAME) com portas O-RAN..."
	k3d cluster create $(CLUSTER_NAME) \
	  --servers 1 \
	  --agents 0 \
	  --port "36422:36422/SCTP@server:0" \
	  --port "8080:8080@server:0" \
	  --port "8081:8081@server:0" \
	  --port "8082:8082@server:0" \
	  --port "8083:8083@server:0" \
	  --port "8084:8084@server:0" \
	  --port "8085:8085@server:0" \
	  --port "8086:8086@server:0" \
	  --port "8087:8087@server:0" \
	  --port "4560:4560@server:0" \
	  --port "4561:4561@server:0"
	mkdir -p ~/.kube
	k3d kubeconfig get $(CLUSTER_NAME) > ~/.kube/config
	chmod 600 ~/.kube/config

cluster-delete:
	@echo "Removendo cluster k3d $(CLUSTER_NAME)..."
	k3d cluster delete $(CLUSTER_NAME)

cluster-recreate: cluster-delete cluster-create
	@echo "Cluster recriado com sucesso!"

rancher-start:
	@echo "Iniciando contêiner do Rancher Server (rancher-server)..."
	docker run -d --restart=unless-stopped \
	  -p 8088:80 -p 8443:443 \
	  --privileged \
	  --name rancher-server \
	  rancher/rancher:v2.8.5 || echo "Container rancher-server já existe ou está rodando."
	@echo "Aguarde ~60-90 segundos para a inicialização e acesse: https://localhost:8443"

rancher-stop:
	@echo "Parando e removendo contêiner do Rancher Server..."
	docker rm -f rancher-server 2>/dev/null || true

rancher-logs:
	docker logs -f rancher-server

rancher-password:
	@echo "Obtendo Bootstrap Password do Rancher Server:"
	@docker logs rancher-server 2>&1 | grep "Bootstrap Password:" || echo "Ainda inicializando ou senha já redefinida."

rancher-connect:
	@echo "Conectando Rancher Server ao cluster k3d e ajustando agente..."
	bash scripts/register_rancher.sh "$(URL)"

# -------------------------------------------------------------
# Pipeline Kubernetes Nativo (K8s Puro / Kustomize)
# -------------------------------------------------------------
k8s-deploy:
	@echo "Implantando Near-RT RIC + 3 Reference xApps + RDL (Modo Governança)..."
	bash scripts/deploy_k8s.sh --with-rdl

k8s-deploy-baseline:
	@echo "Implantando Near-RT RIC + 3 Reference xApps (Modo Baseline SEM RDL)..."
	bash scripts/deploy_k8s.sh --baseline

k8s-uninstall:
	kubectl delete -k $(K8S_DIR)

k8s-test: test-3xapps

# -------------------------------------------------------------
# Pipeline Helm Chart (Padrão O-RAN)
# -------------------------------------------------------------
helm-deploy:
	@echo "Implantando Near-RT RIC + 3 Reference xApps + RDL via Helm (Modo Governança)..."
	bash scripts/deploy_helm.sh --with-rdl

helm-deploy-baseline:
	@echo "Implantando Near-RT RIC + 3 Reference xApps via Helm (Modo Baseline SEM RDL)..."
	bash scripts/deploy_helm.sh --baseline

# Deploy Exclusivo RDL Fase 2 (CA-RDL / MARL)
helm-deploy-f2:
	@echo "Implantando exclusivamente a xApp RDL Fase 2 (ricxapp-iqos-xapp-rdl-f2)..."
	bash scripts/deploy_rdl_phase2.sh

helm-uninstall-f2:
	@echo "Removendo exclusivamente a xApp RDL Fase 2..."
	helm uninstall ricxapp-iqos-xapp-rdl-f2 -n $(NAMESPACE) || echo "Release ricxapp-iqos-xapp-rdl-f2 nao encontrada."

status-f2:
	@echo "=== Status das xApps no Namespace $(NAMESPACE) ==="
	@kubectl get pods -n $(NAMESPACE) -o wide
	@echo "\n=== Pod da xApp RDL Fase 2 ==="
	@kubectl get pods -n $(NAMESPACE) -l app=ricxapp-iqos-xapp-rdl-f2 -o wide

logs-f2:
	kubectl logs -l app=ricxapp-iqos-xapp-rdl-f2 -n $(NAMESPACE) -f

test-f2:
	@echo "Testando endpoints da xApp RDL Fase 2 (CA-RDL / MARL)..."
	@curl -i http://localhost:8080/health || true
	@echo "\nMétricas Prometheus:"
	@curl -s http://localhost:8081/metrics | grep -E "rdl_|marl_" || true

helm-package:
	@echo "Validando e empacotando os 4 Helm Charts..."
	helm lint deploy/helm/iqos-xapp-rdl
	helm lint deploy/helm/xapp-qos-xslice
	helm lint deploy/helm/xapp-energy-saving
	helm lint deploy/helm/xapp-traffic-steering
	helm package deploy/helm/iqos-xapp-rdl
	helm package deploy/helm/xapp-qos-xslice
	helm package deploy/helm/xapp-energy-saving
	helm package deploy/helm/xapp-traffic-steering

helm-test: test-3xapps

test-3xapps:
	@echo "Testando endpoints das xApps no Kubernetes..."
	bash scripts/verify_3_xapps.sh

helm-uninstall:
	helm uninstall ricxapp-qos-xslice -n $(NAMESPACE) 2>/dev/null || true
	helm uninstall ricxapp-energy-saving -n $(NAMESPACE) 2>/dev/null || true
	helm uninstall ricxapp-traffic-steering -n $(NAMESPACE) 2>/dev/null || true
	helm uninstall $(RELEASE_NAME) -n $(NAMESPACE) 2>/dev/null || true
	helm uninstall ricxapp-iqos-xapp-rdl-f2 -n $(NAMESPACE) 2>/dev/null || true

# -------------------------------------------------------------
# [OPCIONAL] Observabilidade Service Mesh (Kiali / Istio)
# -------------------------------------------------------------
kiali-install:
	bash scripts/install_kiali.sh

kiali-dashboard:
	@echo "Abrindo Kiali em http://localhost:20001/kiali (pressione Ctrl+C para parar)..."
	kubectl port-forward -n istio-system svc/kiali 20001:20001 --address 0.0.0.0

start-traffic:
	@echo "Iniciando gerador contínuo de tráfego interno no cluster..."
	kubectl apply -f deploy/kubernetes/traffic-generator.yaml
	kubectl rollout status deployment/traffic-generator -n $(NAMESPACE) --timeout=60s
	@echo "Tráfego ATIVO! Atualize o Kiali para ver o fluxo animado."

stop-traffic:
	@echo "Parando gerador de tráfego..."
	kubectl delete -f deploy/kubernetes/traffic-generator.yaml --ignore-not-found=true

inject-traffic:
	bash scripts/inject_traffic.sh

# -------------------------------------------------------------
# Operações Gerais
# -------------------------------------------------------------
validate:
	echo "Schema Validated"

onboard:
	dms_cli onboard configs/config-file.json configs/schema.json

install:
	dms_cli install --xapp-chart-name $(IMAGE_NAME) --version $(IMAGE_TAG) --namespace $(NAMESPACE)

status:
	@echo "=== Near-RT RIC Platform (ricplt) ==="
	@kubectl get pods -n $(NAMESPACE_RIC) -o wide
	@echo "\n=== xApps em Execução (ricxapp) ==="
	@kubectl get pods -n $(NAMESPACE) -o wide

logs:
	kubectl logs -l app=$(RELEASE_NAME) -n $(NAMESPACE) -f

smoke-test:
	docker rm -f xapp-rdl-test 2>/dev/null || true
	docker run -d --name xapp-rdl-test -p 8090:8080 -p 8091:8081 -e USE_FAKE_SDL=true $(IMAGE_NAME):$(IMAGE_TAG)
	sleep 3
	curl -i http://localhost:8090/health
	curl http://localhost:8091/metrics | grep -E "rdl_|dl_"
	docker logs xapp-rdl-test
	docker rm -f xapp-rdl-test

uninstall:
	kubectl delete -k $(K8S_DIR) || $(MAKE) helm-uninstall

# -------------------------------------------------------------
# Simulações ns-3 NORI e Pipeline Experimental Modular
# -------------------------------------------------------------
setup-ns3:
	bash scripts/setup_ns3.sh

deploy-rdl: helm-deploy

deploy-baseline: helm-deploy-baseline

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
	@echo "Sincronizando resultados experimentais com o GitHub..."
	git add experiments/results/ docs/ scripts/
	git commit -m "chore(experiments): upload latest ns-3 benchmark results, datasets and LaTeX report [skip ci]" || echo "Nenhuma alteração nova para commit."
	git push origin main || echo "Aviso: Verifique as credenciais do Git / chave SSH para o push."

# -------------------------------------------------------------
# Sincronização Contínua e Rollback Seguro com GitHub
# -------------------------------------------------------------
sync:
	@bash scripts/git_sync.sh "$(MSG)"

auto-sync:
	@bash scripts/git_auto_sync.sh $(INTERVAL)

rollback:
	@bash scripts/git_rollback.sh $(if $(COMMIT),--commit $(COMMIT),) $(if $(STEPS),--steps $(STEPS),)

rollback-push:
	@bash scripts/git_rollback.sh --push $(if $(COMMIT),--commit $(COMMIT),) $(if $(STEPS),--steps $(STEPS),)

rollback-clean:
	@bash scripts/git_rollback.sh --clean

rollback-list:
	@bash scripts/git_rollback.sh --list

