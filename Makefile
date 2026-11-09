.PHONY: test test-unit test-codec test-integration test-interop generate-golden-vectors verify-no-synthetic \
        verify-provenance gate1-check check-local-paths certify setup-ns3 conflict-experiment native-campaign \
        deploy-ric deploy-kpm-probe nori-scenario nori-campaign panel helm-package helm-deploy helm-deploy-baseline \
        helm-uninstall deploy-reference-xapps build cluster-create cluster-delete cluster-recreate rancher-start \
        rancher-stop rancher-logs rancher-password rancher-connect kiali-install kiali-dashboard status

# Uso detalhado: docs/04 (instalação, campanhas, certificação) e docs/05 (bancada NORI e observabilidade ao vivo).
# Os alvos de simulação, RIC e NORI rodam no Ubuntu do WSL.

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 1.1.0
NAMESPACE_RIC ?= ricplt
NAMESPACE ?= ricxapp
RELEASE_NAME ?= ricxapp-iqos-xapp-rdl
CLUSTER_NAME ?= rancher-lab
SCENARIO ?= S1
BASELINE ?= B3
SEED ?= 1001

# -------------------------------------------------------------
# Testes e verificações
# -------------------------------------------------------------
test:
	pytest tests/ -q

test-unit:
	pytest tests/unit/ -v

test-codec:
	pytest tests/codec/ -v

test-integration:
	pytest tests/integration/ -v

test-interop:
	pytest tests/interoperability/ -v

generate-golden-vectors:
	python scripts/generate_golden_vectors.py

verify-no-synthetic:
	python scripts/check_no_synthetic_results.py

verify-provenance: verify-no-synthetic
	python scripts/validate_provenance.py

gate1-check:
	python scripts/validate_experiment_tree.py --check-gate1

check-local-paths:
	python scripts/certification/redact_local_paths.py --check

certify:
	python scripts/certification/certify_chain.py

# -------------------------------------------------------------
# Pilha nativa (ns-3.48 + 5G-LENA v5.1, sem E2)
# -------------------------------------------------------------
setup-ns3:
	bash scripts/setup_ns3.sh

conflict-experiment:
	python scripts/certification/run_conflict_experiment.py --scenario $(SCENARIO) --baseline $(BASELINE) --seed $(SEED)

native-campaign:
	bash scripts/run_native_campaign.sh

# -------------------------------------------------------------
# Near-RT RIC Release I, bancada NORI e xApp kpm-probe (E2 real)
# -------------------------------------------------------------
deploy-ric:
	bash scripts/deploy_ric_i_release.sh

deploy-kpm-probe:
	bash scripts/deploy_kpm_probe.sh --set rc.decision=catalog --set rc.afterIndications=12

nori-scenario:
	bash scripts/run_nori_scenario.sh $(SCENARIO) $(SEED)

nori-campaign:
	bash scripts/run_nori_campaign.sh

panel:
	bash scripts/observe/panel.sh

# -------------------------------------------------------------
# Charts Helm da xApp RDL e das xApps de referência
# -------------------------------------------------------------
helm-package:
	helm lint deploy/helm/iqos-xapp-rdl
	helm lint deploy/helm/xapp-qos-xslice
	helm lint deploy/helm/xapp-energy-saving
	helm lint deploy/helm/xapp-traffic-steering
	helm lint deploy/helm/xapp-kpm-probe --set srcBundle=x --set srcCommit=x
	helm lint deploy/helm/nori-ns3

helm-deploy:
	bash scripts/deploy_helm.sh --with-rdl

helm-deploy-baseline:
	bash scripts/deploy_helm.sh --baseline

helm-uninstall:
	helm uninstall ricxapp-qos-xslice -n $(NAMESPACE) 2>/dev/null || true
	helm uninstall ricxapp-energy-saving -n $(NAMESPACE) 2>/dev/null || true
	helm uninstall ricxapp-traffic-steering -n $(NAMESPACE) 2>/dev/null || true
	helm uninstall $(RELEASE_NAME) -n $(NAMESPACE) 2>/dev/null || true

deploy-reference-xapps:
	bash scripts/deploy_reference_xapps.sh

build:
	docker build --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

# -------------------------------------------------------------
# Cluster k3d e Rancher (opcional)
# -------------------------------------------------------------
cluster-create:
	k3d cluster create $(CLUSTER_NAME) --servers 1 --agents 0 \
	  --port "36422:36422/SCTP@server:0" \
	  --port "8080:8080@server:0" --port "8081:8081@server:0" \
	  --port "4560:4560@server:0" --port "4561:4561@server:0"
	mkdir -p ~/.kube
	k3d kubeconfig get $(CLUSTER_NAME) > ~/.kube/config
	chmod 600 ~/.kube/config

cluster-delete:
	k3d cluster delete $(CLUSTER_NAME)

cluster-recreate: cluster-delete cluster-create

rancher-start:
	@if [ "$$(docker ps -a -q -f name=^/rancher-server$$)" ]; then docker start rancher-server; else \
		docker run -d --restart=unless-stopped -p 8088:80 -p 8443:443 --privileged --name rancher-server rancher/rancher:v2.8.5; fi

rancher-stop:
	docker rm -f rancher-server 2>/dev/null || true

rancher-logs:
	docker logs -f rancher-server

rancher-password:
	@docker logs rancher-server 2>&1 | grep "Bootstrap Password:" || echo "Ainda inicializando ou senha já redefinida."

rancher-connect:
	bash scripts/register_rancher.sh "$(URL)"

kiali-install:
	bash scripts/install_kiali.sh

kiali-dashboard:
	kubectl port-forward -n istio-system svc/kiali 20001:20001 --address 0.0.0.0

status:
	@kubectl get pods -n $(NAMESPACE_RIC) -o wide
	@kubectl get pods -n $(NAMESPACE) -o wide
	@kubectl get pods -n ricsim -o wide
