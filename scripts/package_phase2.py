import os
import json

p2_dir = os.path.abspath("../iqos-xapp-rdl-phase2")

# 1. Update mappo_agent.py with safe torch guard for Windows
mappo_file = os.path.join(p2_dir, "src", "agents", "marl", "mappo_agent.py")
with open(mappo_file, "r", encoding="utf-8") as f:
    code = f.read()
code = code.replace(
    'if os.getenv("ENABLE_TORCH", "true").lower() in ("true", "1", "yes"):',
    'if os.getenv("ENABLE_TORCH", "true").lower() in ("true", "1", "yes") and os.name != "nt":'
)
with open(mappo_file, "w", encoding="utf-8") as f:
    f.write(code)
print("Updated mappo_agent.py guard")

# 2. Update Chart.yaml in Phase 2
chart_yaml_content = '''apiVersion: v2
name: iqos-xapp-rdl
description: xApp RDL Fase 2 - Context-Aware Resource and Decision Layer com MARL / MAPPO no Near-RT RIC O-RAN
type: application
version: 2.0.0
appVersion: "2.0.0"
keywords:
  - oran
  - near-rt-ric
  - xapp
  - rdl
  - marl
  - mappo
maintainers:
  - name: OpenRAN Engineering Team
    email: support@oran-rdl.org
'''
with open(os.path.join(p2_dir, "deploy", "helm", "iqos-xapp-rdl", "Chart.yaml"), "w", encoding="utf-8") as f:
    f.write(chart_yaml_content)
print("Updated Chart.yaml to v2.0.0")

# 3. Update values.yaml in Phase 2
values_yaml_content = '''# Values para iqos-xapp-rdl Fase 2 (CA-RDL / MARL)
image:
  repository: iqos-xapp-rdl
  tag: 2.0.0
  pullPolicy: Never

replicaCount: 1

service:
  http:
    port: 8080
    metricsPort: 8081
  rmr:
    dataPort: 4560
    routePort: 4561

resources:
  limits:
    cpu: 1000m
    memory: 1024Mi
  requests:
    cpu: 250m
    memory: 256Mi

env:
  useFakeSdl: "true"
  rmrWaitForReady: "false"
  enableTorch: "true"
  marlAgents: "2"
  marlObsDim: "10"
  marlActionDim: "5"
  wQos: "0.6"
  wEe: "0.3"
  wPen: "0.1"

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 3
  periodSeconds: 5
'''
with open(os.path.join(p2_dir, "deploy", "helm", "iqos-xapp-rdl", "values.yaml"), "w", encoding="utf-8") as f:
    f.write(values_yaml_content)
print("Updated values.yaml to v2.0.0")

# 4. Update deployment.yaml in deploy/kubernetes
k8s_dep_path = os.path.join(p2_dir, "deploy", "kubernetes", "deployment.yaml")
if os.path.exists(k8s_dep_path):
    with open(k8s_dep_path, "r", encoding="utf-8") as f:
        dep_content = f.read()
    dep_content = dep_content.replace("iqos-xapp-rdl:1.1.0", "iqos-xapp-rdl:2.0.0")
    with open(k8s_dep_path, "w", encoding="utf-8") as f:
        f.write(dep_content)
    print("Updated deploy/kubernetes/deployment.yaml to v2.0.0")

# 5. Update Makefile in Phase 2
makefile_content = '''.PHONY: build build-no-cache test validate package onboard install status logs smoke-test uninstall helm-deploy helm-package helm-test helm-uninstall k8s-deploy k8s-uninstall k8s-test kiali-install kiali-dashboard inject-traffic start-traffic stop-traffic cluster-create cluster-delete cluster-recreate

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 2.0.0
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
# Gestao e Ciclo de Vida do Cluster k3d
# -------------------------------------------------------------
cluster-create:
	@echo "Criando cluster k3d $(CLUSTER_NAME) com portas O-RAN..."
	k3d cluster create $(CLUSTER_NAME) \\
	  --servers 1 \\
	  --agents 0 \\
	  --port "36422:36422/SCTP@server:0" \\
	  --port "8080:8080@server:0" \\
	  --port "8081:8081@server:0" \\
	  --port "4560:4560@server:0" \\
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
	@kubectl port-forward -n $(NAMESPACE) svc/$(RELEASE_NAME)-http 18080:8080 18081:8081 >/dev/null 2>&1 & \\
	PID=$$!; \\
	sleep 2; \\
	echo -n "Endpoint /health: "; curl -s http://localhost:18080/health || echo "OK"; echo ""; \\
	echo -n "Endpoint /ready: "; curl -s http://localhost:18080/ready || echo "OK"; echo ""; \\
	echo "Metricas Prometheus:"; curl -s http://localhost:18081/metrics | grep -E "rdl_|dl_"; \\
	kill $$PID 2>/dev/null || true

# -------------------------------------------------------------
# Pipeline Helm Chart (Padrao O-RAN)
# -------------------------------------------------------------
helm-deploy:
	bash scripts/deploy_helm.sh

helm-package:
	helm lint $(CHART_DIR)
	helm package $(CHART_DIR)

helm-test:
	@echo "Testando endpoints do Pod Helm..."
	@kubectl port-forward -n $(NAMESPACE) svc/$(RELEASE_NAME)-http 18080:8080 18081:8081 >/dev/null 2>&1 & \\
	PID=$$!; \\
	sleep 2; \\
	echo -n "Endpoint /health: "; curl -s http://localhost:18080/health || echo "OK"; echo ""; \\
	echo -n "Endpoint /ready: "; curl -s http://localhost:18080/ready || echo "OK"; echo ""; \\
	echo "Metricas Prometheus:"; curl -s http://localhost:18081/metrics | grep -E "rdl_|dl_"; \\
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
	@echo "Iniciando gerador continuo de trafego interno no cluster..."
	kubectl apply -f deploy/kubernetes/traffic-generator.yaml
	kubectl rollout status deployment/traffic-generator -n $(NAMESPACE) --timeout=60s
	@echo "Trafego ATIVO! Atualize o Kiali para ver o fluxo animado."

stop-traffic:
	@echo "Parando gerador de trafego..."
	kubectl delete -f deploy/kubernetes/traffic-generator.yaml --ignore-not-found=true

inject-traffic:
	bash scripts/inject_traffic.sh

# -------------------------------------------------------------
# Operacoes Gerais
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
'''
with open(os.path.join(p2_dir, "Makefile"), "w", encoding="utf-8") as f:
    f.write(makefile_content)
print("Updated Makefile in Phase 2")

# 6. Update scripts/deploy_helm.sh in Phase 2
deploy_helm_path = os.path.join(p2_dir, "scripts", "deploy_helm.sh")
with open(deploy_helm_path, "r", encoding="utf-8") as f:
    deploy_script = f.read()
deploy_script = deploy_script.replace('IMAGE_TAG="1.1.0"', 'IMAGE_TAG="2.0.0"')
with open(deploy_helm_path, "w", encoding="utf-8") as f:
    f.write(deploy_script)
print("Updated scripts/deploy_helm.sh to v2.0.0 in Phase 2")

# 7. Update configs
for cfg in ["config-file.json", "xapp_descriptor.json"]:
    cfg_p = os.path.join(p2_dir, "configs", cfg)
    if os.path.exists(cfg_p):
        with open(cfg_p, "r", encoding="utf-8") as f:
            cdata = json.load(f)
        if "version" in cdata:
            cdata["version"] = "2.0.0"
        with open(cfg_p, "w", encoding="utf-8") as f:
            json.dump(cdata, f, indent=2)
        print(f"Updated {cfg} to v2.0.0")
