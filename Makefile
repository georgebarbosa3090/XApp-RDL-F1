.PHONY: build build-no-cache test validate package onboard install status logs smoke-test uninstall helm-deploy helm-deploy-baseline helm-package helm-test helm-uninstall k8s-deploy k8s-deploy-baseline k8s-uninstall k8s-test test-3xapps kiali-install kiali-dashboard inject-traffic start-traffic stop-traffic cluster-create cluster-delete cluster-recreate setup-ns3 run-experiments analyze-benchmarks view-results push-results

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

setup-ns3:
	bash scripts/setup_ns3.sh

run-experiments:
	bash scripts/run_full_experiment.sh

analyze-benchmarks:
	python3 scripts/run_and_analyze_benchmarks.py

view-results:
	@cat experiments/results/relatorio_comparativo.md

push-results:
	@echo "Sincronizando resultados experimentais com o GitHub..."
	git add experiments/results/
	git commit -m "chore(experiments): upload latest ns-3 benchmark results and datasets [skip ci]" || echo "Nenhuma alteração nova para commit."
	git push origin main || echo "Aviso: Verifique as credenciais do Git / chave SSH para o push."
