.PHONY: build build-no-cache test validate package onboard install status logs smoke-test uninstall helm-deploy helm-package helm-test helm-uninstall k8s-deploy k8s-uninstall k8s-test kiali-install kiali-dashboard

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 1.1.0
CHART_DIR ?= deploy/helm/iqos-xapp-rdl
K8S_DIR ?= deploy/kubernetes
NAMESPACE ?= ricxapp
RELEASE_NAME ?= ricxapp-iqos-xapp-rdl

build:
	docker build --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

build-no-cache:
	docker build --no-cache --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

test:
	PYTHONPATH=. pytest tests/ -v

# -------------------------------------------------------------
# Pipeline Kubernetes Nativo (K8s Puro / Kustomize)
# -------------------------------------------------------------
k8s-deploy:
	bash scripts/deploy_k8s.sh

k8s-uninstall:
	kubectl delete -k $(K8S_DIR)

k8s-test:
	@echo "Testando endpoints do Pod K8s..."
	kubectl port-forward -n $(NAMESPACE) svc/$(RELEASE_NAME)-http 8080:8080 8081:8081 & \
	PID=$$!; \
	sleep 2; \
	curl -s http://localhost:8080/health | jq . || curl -s http://localhost:8080/health; \
	echo ""; \
	curl -s http://localhost:8081/metrics | grep -E "rdl_|dl_"; \
	kill $$PID

# -------------------------------------------------------------
# Pipeline Helm Chart
# -------------------------------------------------------------
helm-deploy:
	bash scripts/deploy_helm.sh

helm-package:
	helm lint $(CHART_DIR)
	helm package $(CHART_DIR)

helm-test:
	@echo "Testando endpoints do Pod Helm..."
	kubectl port-forward -n $(NAMESPACE) svc/$(RELEASE_NAME)-http 8080:8080 8081:8081 & \
	PID=$$!; \
	sleep 2; \
	curl -s http://localhost:8080/health | jq . || curl -s http://localhost:8080/health; \
	echo ""; \
	curl -s http://localhost:8081/metrics | grep -E "rdl_|dl_"; \
	kill $$PID

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
