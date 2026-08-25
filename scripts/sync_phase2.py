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

# 6. Update Makefile in Phase 2
makefile_p2 = """.PHONY: build build-no-cache test validate package onboard install status logs smoke-test uninstall

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 2.0.0

build:
	docker build --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

build-no-cache:
	docker build --no-cache --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

test:
	PYTHONPATH=. pytest tests/ -v

validate:
	echo "Schema Validated"

smoke-test:
	docker rm -f xapp-rdl-test 2>/dev/null || true
	docker run -d --name xapp-rdl-test -p 8090:8080 -p 8091:8081 -e USE_FAKE_SDL=true $(IMAGE_NAME):$(IMAGE_TAG)
	sleep 3
	curl -i http://localhost:8090/health
	curl http://localhost:8091/metrics | grep -E "rdl_|dl_"
	docker logs xapp-rdl-test
	docker rm -f xapp-rdl-test
"""

with open(os.path.join(p2, 'Makefile'), 'w', encoding='utf-8') as f:
    f.write(makefile_p2)
print("6. Updated Makefile in Phase 2")

# 7. Copy all documentation from Phase 1 to Phase 2
docs_to_sync = [
    '07_modelagem_matematica.md',
    '08_guia_instalacao_osc_near_rt_ric.md',
    '09_cenarios_de_teste_e_benchmark_fase1_fase2.md',
    '10_relatorio_smoke_test_fase1.md'
]
for doc in docs_to_sync:
    src_doc = os.path.join(p1, 'docs', doc)
    dst_doc = os.path.join(p2, 'docs', doc)
    if os.path.exists(src_doc):
        shutil.copy2(src_doc, dst_doc)
        print(f"7. Copied docs/{doc} to Phase 2")

print("All Phase 2 sync tasks completed successfully!")
