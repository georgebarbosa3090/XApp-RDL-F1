#!/usr/bin/env bash
# =============================================================================
# Instala o k3s nativo do WSL como serviço systemd permanente (sobe junto com o WSL).
# Uso (uma vez, no terminal do Ubuntu):  sudo bash scripts/install_k3s_service.sh
#
# O binário /usr/local/bin/k3s (v1.26.5) já existe; aqui só se cria a unidade, no formato
# da unidade oficial do instalador do k3s, com o kubeconfig legível (modo 644) para que
# kubectl/helm funcionem sem sudo. Requer systemd=true em /etc/wsl.conf.
# Para remover: sudo systemctl disable --now k3s && sudo rm /etc/systemd/system/k3s.service
# =============================================================================
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Rode com sudo." >&2; exit 1; }
[ -x /usr/local/bin/k3s ] || { echo "/usr/local/bin/k3s não encontrado." >&2; exit 1; }

if systemctl is-active --quiet k3s && [ ! -f /etc/systemd/system/k3s.service ]; then
  echo "Parando o k3s transitório (systemd-run) para trocar pela unidade permanente..."
  systemctl stop k3s
fi

cat >/etc/systemd/system/k3s.service <<'UNIT'
[Unit]
Description=Lightweight Kubernetes (k3s) - XApp-RDL-F1
Documentation=https://k3s.io
Wants=network-online.target
After=network-online.target

[Service]
Type=notify
ExecStart=/usr/local/bin/k3s server --write-kubeconfig-mode 644
KillMode=process
Delegate=yes
LimitNOFILE=1048576
LimitNPROC=infinity
LimitCORE=infinity
TasksMax=infinity
TimeoutStartSec=0
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now k3s
echo "Aguardando a API do k3s..."
for _ in $(seq 1 60); do
  KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl get nodes 2>/dev/null && break
  sleep 5
done
systemctl is-enabled k3s
systemctl is-active k3s
grep -E 'MemTotal|MemAvailable' /proc/meminfo
