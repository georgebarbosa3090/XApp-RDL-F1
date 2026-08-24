# Stage 1: Build dependencies
FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    dpkg \
    gcc \
    python3-dev \
    && wget --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr_4.9.0_amd64.deb/download.deb \
    && dpkg -i rmr_4.9.0_amd64.deb \
    && rm -f rmr_4.9.0_amd64.deb \
    && wget --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr-dev_4.9.0_amd64.deb/download.deb \
    && dpkg -i rmr-dev_4.9.0_amd64.deb \
    && rm -f rmr-dev_4.9.0_amd64.deb \
    && ldconfig

WORKDIR /app
COPY requirements.txt ./
# Constrói todos os wheels e dependências transitivas (incluindo hiredis com C extensions)
RUN pip install --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final runtime image
FROM python:3.10-slim

# Install RMR runtime libraries, headers/symlinks and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    dpkg \
    curl \
    && wget --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr_4.9.0_amd64.deb/download.deb \
    && dpkg -i rmr_4.9.0_amd64.deb \
    && rm -f rmr_4.9.0_amd64.deb \
    && wget --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr-dev_4.9.0_amd64.deb/download.deb \
    && dpkg -i rmr-dev_4.9.0_amd64.deb \
    && rm -f rmr-dev_4.9.0_amd64.deb \
    && ldconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Environment variables
ENV RMR_SEED_RT=/app/configs/routes.rt
ENV CONFIG_FILE=/app/configs/config-file.json
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib64
ENV PYTHONPATH=/app
# Install wheels from builder (system-wide)
COPY --from=builder /app/wheels /tmp/wheels
COPY --from=builder /app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels -r /tmp/requirements.txt \
    && rm -rf /tmp/wheels /tmp/requirements.txt

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
HEALTHCHECK --interval=10s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1

# Start xApp
CMD ["python", "src/main.py"]

