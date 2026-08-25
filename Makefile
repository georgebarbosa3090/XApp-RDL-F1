.PHONY: build build-no-cache test validate package onboard install status logs smoke-test uninstall helm-deploy helm-package helm-test helm-uninstall

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 1.1.0
CHART_DIR ?= deploy/helm/iqos-xapp-rdl
NAMESPACE ?= ricxapp
RELEASE_NAME ?= ricxapp-iqos-xapp-rdl

build:
	docker build --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

build-no-cache:
	docker build --no-cache --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

test:
	PYTHONPATH=. pytest tests/ -v

# Automação Helm Completa (Build + Import k3d + Package + Deploy + Wait)
helm-deploy:
	bash scripts/deploy_helm.sh

helm-package:
	helm lint $(CHART_DIR)
	helm package $(CHART_DIR)

helm-test:
	@echo "Testando endpoints do Pod..."
	kubectl port-forward -n $(NAMESPACE) svc/$(RELEASE_NAME)-http 8080:8080 8081:8081 & \
	PID=$$!; \
	sleep 2; \
	curl -s http://localhost:8080/health | jq .; \
	curl -s http://localhost:8081/metrics | grep -E "rdl_|dl_"; \
	kill $$PID

helm-uninstall:
	helm uninstall $(RELEASE_NAME) -n $(NAMESPACE)

validate:
	echo "Schema Validated"

onboard:
	dms_cli onboard configs/config-file.json configs/schema.json

install:
	dms_cli install --xapp-chart-name $(IMAGE_NAME) --version $(IMAGE_TAG) --namespace $(NAMESPACE)

status:
	helm status $(RELEASE_NAME) -n $(NAMESPACE)
	kubectl get pods -n $(NAMESPACE) -l app=$(RELEASE_NAME)

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
	helm uninstall $(RELEASE_NAME) -n $(NAMESPACE)
