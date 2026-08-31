import os
import shutil

p1 = os.path.abspath('.')
p2 = os.path.abspath('../iqos-xapp-rdl-phase2')

print(f"Syncing from {p1} to {p2}")

# 1. Update requirements.txt in Phase 2
with open(os.path.join(p1, 'requirements.txt'), 'r', encoding='utf-8') as f:
    req_content = f.read()
with open(os.path.join(p2, 'requirements.txt'), 'w', encoding='utf-8') as f:
    f.write(req_content)
print("1. Synced requirements.txt")

# 2. Update logging.py in Phase 2
with open(os.path.join(p1, 'src/observability/logging.py'), 'r', encoding='utf-8') as f:
    log_content = f.read()
with open(os.path.join(p2, 'src/observability/logging.py'), 'w', encoding='utf-8') as f:
    f.write(log_content)
print("2. Synced src/observability/logging.py")

# 3. Update E2 codecs in Phase 2
for fname in ['kpm_decoder.py', 'rc_encoder.py', 'e2ap_decoder.py']:
    src_f = os.path.join(p1, 'src/e2', fname)
    dst_f = os.path.join(p2, 'src/e2', fname)
    shutil.copy2(src_f, dst_f)
    print(f"3. Copied src/e2/{fname}")

# 4. Update docker/Dockerfile in Phase 2 with ML-enabled multi-stage build
dockerfile_p2 = """# Stage 1: Build dependencies
FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \\
    wget \\
    dpkg \\
    gcc \\
    python3-dev \\
    && wget --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr_4.9.0_amd64.deb/download.deb \\
    && dpkg -i rmr_4.9.0_amd64.deb \\
    && rm -f rmr_4.9.0_amd64.deb \\
    && wget --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr-dev_4.9.0_amd64.deb/download.deb \\
    && dpkg -i rmr-dev_4.9.0_amd64.deb \\
    && rm -f rmr-dev_4.9.0_amd64.deb \\
    && ldconfig

WORKDIR /app
COPY requirements.txt requirements-ml.txt ./
# Pre-compile wheels for all requirements (base + ML packages)
RUN pip install --upgrade pip setuptools wheel && \\
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt -r requirements-ml.txt

# Stage 2: Final runtime image
FROM python:3.10-slim

# Install RMR runtime libraries, headers/symlinks and curl
RUN apt-get update && apt-get install -y --no-install-recommends \\
    wget \\
    dpkg \\
    curl \\
    && wget --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr_4.9.0_amd64.deb/download.deb \\
    && dpkg -i rmr_4.9.0_amd64.deb \\
    && rm -f rmr_4.9.0_amd64.deb \\
    && wget --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr-dev_4.9.0_amd64.deb/download.deb \\
    && dpkg -i rmr-dev_4.9.0_amd64.deb \\
    && rm -f rmr-dev_4.9.0_amd64.deb \\
    && ldconfig \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

# Environment variables
ENV RMR_SEED_RT=/app/configs/routes.rt
ENV CONFIG_FILE=/app/configs/config-file.json
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib64
ENV PYTHONPATH=/app
ENV ENABLE_TORCH=true

# Install wheels from builder (system-wide)
COPY --from=builder /app/wheels /tmp/wheels
COPY --from=builder /app/requirements.txt /tmp/requirements.txt
COPY --from=builder /app/requirements-ml.txt /tmp/requirements-ml.txt
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels -r /tmp/requirements.txt -r /tmp/requirements-ml.txt \\
    && rm -rf /tmp/wheels /tmp/requirements.txt /tmp/requirements-ml.txt

# Create non-root user
RUN useradd -m -s /bin/bash xapp
USER xapp
WORKDIR /app

# Copy source code and configs
COPY --chown=xapp:xapp src/ /app/src/
COPY --chown=xapp:xapp configs/ /app/configs/

# Ports for HTTP and Metrics
EXPOSE 8080 8081

# Healthcheck
HEALTHCHECK --interval=10s --timeout=3s \\
  CMD curl -f http://localhost:8080/health || exit 1

# Start xApp
CMD ["python", "src/main.py"]
"""

with open(os.path.join(p2, 'docker/Dockerfile'), 'w', encoding='utf-8') as f:
    f.write(dockerfile_p2)
print("4. Updated docker/Dockerfile in Phase 2")

# 5. Update src/rdl_xapp.py in Phase 2
with open(os.path.join(p1, 'src/rdl_xapp.py'), 'r', encoding='utf-8') as f:
    rdl_content = f.read()
with open(os.path.join(p2, 'src/rdl_xapp.py'), 'w', encoding='utf-8') as f:
    f.write(rdl_content)
print("5. Synced src/rdl_xapp.py in Phase 2")

# 6. Update Makefile in Phase 2 with full simulation & cluster pipeline
makefile_p2 = """.PHONY: build build-no-cache test validate package onboard install status logs smoke-test uninstall helm-deploy helm-deploy-baseline helm-package helm-test helm-uninstall k8s-deploy k8s-deploy-baseline k8s-uninstall k8s-test test-3xapps kiali-install kiali-dashboard inject-traffic start-traffic stop-traffic cluster-create cluster-delete cluster-recreate rancher-start rancher-stop rancher-logs rancher-password rancher-connect setup-ns3 deploy-rdl deploy-baseline run-baseline run-rdl run-experiments run-suite analyze-benchmarks view-results push-results sync auto-sync rollback rollback-push rollback-clean rollback-list

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 2.0.0
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

# Gestão do Cluster k3d
cluster-create:
	@echo "Criando cluster k3d $(CLUSTER_NAME)..."
	k3d cluster create $(CLUSTER_NAME) --servers 1 --agents 0 --port "36422:36422/SCTP@server:0" --port "8080:8080@server:0" --port "8081:8081@server:0" --port "4560:4560@server:0" --port "4561:4561@server:0"
	mkdir -p ~/.kube
	k3d kubeconfig get $(CLUSTER_NAME) > ~/.kube/config

cluster-delete:
	k3d cluster delete $(CLUSTER_NAME)

# Deploy Helm / K8s
helm-deploy:
	bash scripts/deploy_helm.sh --with-rdl

helm-deploy-baseline:
	bash scripts/deploy_helm.sh --baseline

test-3xapps:
	bash scripts/verify_3_xapps.sh

# Simulações ns-3 e Pipelines Experimentais
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

with open(os.path.join(p2, 'Makefile'), 'w', encoding='utf-8') as f:
    f.write(makefile_p2)
print("6. Updated Makefile in Phase 2 with full simulation & cluster pipeline")

# 7. Sync simulations directory
sim_src = os.path.join(p1, 'simulations')
sim_dst = os.path.join(p2, 'simulations')
if os.path.exists(sim_src):
    shutil.copytree(sim_src, sim_dst, dirs_exist_ok=True)
    print("7. Synced simulations/ (ns-3 scenarios) to Phase 2")

# 8. Sync experiment and maintenance scripts
scripts_to_sync = [
    'setup_ns3.sh',
    'run_baseline_experiment.sh',
    'run_rdl_experiment.sh',
    'run_full_experiment.sh',
    'run_experiment_suite.py',
    'run_and_analyze_benchmarks.py',
    'evaluate_and_improve_algorithms.py',
    'git_sync.ps1',
    'git_sync.sh',
    'git_auto_sync.ps1',
    'git_auto_sync.sh',
    'git_rollback.ps1',
    'git_rollback.sh'
]
for sc in scripts_to_sync:
    src_sc = os.path.join(p1, 'scripts', sc)
    dst_sc = os.path.join(p2, 'scripts', sc)
    if os.path.exists(src_sc):
        shutil.copy2(src_sc, dst_sc)
        print(f"8. Synced scripts/{sc} to Phase 2")

print("All Phase 2 sync tasks completed successfully!")
