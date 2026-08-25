.PHONY: build build-no-cache test validate package onboard install status logs smoke-test uninstall helm-deploy helm-package helm-test helm-uninstall k8s-deploy k8s-uninstall k8s-test kiali-install kiali-dashboard inject-traffic start-traffic stop-traffic cluster-create cluster-delete cluster-recreate

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 1.1.0
CHART_DIR ?= deploy/helm/iqos-xapp-rdl
K8S_DIR ?= deploy/kubernetes
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

# -------------------------------------------------------------
# Pipeline Kubernetes Nativo (K8s Puro / Kustomize)
# -------------------------------------------------------------
k8s-deploy:
	bash scripts/deploy_k8s.sh

k8s-uninstall:
	kubectl delete -k $(K8S_DIR)

k8s-test:
	@echo "Testando endpoints do Pod K8s..."
	@kubectl port-forward -n $(NAMESPACE) svc/$(RELEASE_NAME)-http 18080:8080 18081:8081 >/dev/null 2>&1 & \
	PID=$$!; \
	sleep 2; \
	echo -n "Endpoint /health: "; curl -s http://localhost:18080/health || echo "OK"; echo ""; \
	echo -n "Endpoint /ready: "; curl -s http://localhost:18080/ready || echo "OK"; echo ""; \
	echo "Métricas Prometheus:"; curl -s http://localhost:18081/metrics | grep -E "rdl_|dl_"; \
	kill $$PID 2>/dev/null || true

# -------------------------------------------------------------
# Pipeline Helm Chart (Padrão O-RAN)
# -------------------------------------------------------------
helm-deploy:
	bash scripts/deploy_helm.sh

helm-package:
	helm lint $(CHART_DIR)
	helm package $(CHART_DIR)

helm-test:
	@echo "Testando endpoints do Pod Helm..."
	@kubectl port-forward -n $(NAMESPACE) svc/$(RELEASE_NAME)-http 18080:8080 18081:8081 >/dev/null 2>&1 & \
	PID=$$!; \
	sleep 2; \
	echo -n "Endpoint /health: "; curl -s http://localhost:18080/health || echo "OK"; echo ""; \
	echo -n "Endpoint /ready: "; curl -s http://localhost:18080/ready || echo "OK"; echo ""; \
	echo "Métricas Prometheus:"; curl -s http://localhost:18081/metrics | grep -E "rdl_|dl_"; \
	kill $$PID 2>/dev/null || true

helm-uninstall:
	helm uninstall $(RELEASE_NAME) -n $(NAMESPACE)

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
	kubectl get pods -n $(NAMESPACE) -l app=$(RELEASE_NAME) -o wide

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
	kubectl delete -k $(K8S_DIR) || helm uninstall $(RELEASE_NAME) -n $(NAMESPACE)
