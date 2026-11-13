#!/usr/bin/env bash
# Painel de observação ao vivo (tmux): uma janela por aba.
#   0 campanha   terminal livre para rodar a campanha ou um cenário (comandos sugeridos já digitados)
#   1 nori       execução NORI corrente: vazão por fatia, [RDL-UE], E2 Setup, Subscription, Control
#   2 e2ap       protocolo E2AP decodificado ao vivo pelo tshark (tcpdump do pod)
#   3 xapp       subscrição, KPM decodificado por UE, decisão do RDL-N1, RIC Control e ACK
#   4 ric        logs filtrados de E2Term, E2Mgr, SubMgr e RtMgr (painel de cima) e estado do RIC (embaixo)
#   5 k8s        deployments e pods de ricplt, ricxapp e ricsim
#   6 ues        registro de UEs ([RDL-UE])
#   7 influx     alimentador do InfluxDB (NORI, xApp e campanhas -> Grafana); exige deploy_observability.sh
#   8 grafana    port-forward do Grafana em http://localhost:3000
# Uso (Ubuntu do WSL): bash scripts/observe/panel.sh     Navegação: Ctrl-b <número>; sair: Ctrl-b d
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
O="$REPO/scripts/observe"
S="${SESSION:-rdl}"
command -v tmux >/dev/null || { echo "tmux não instalado (sudo apt-get install -y tmux)" >&2; exit 3; }
tmux has-session -t "$S" 2>/dev/null && exec tmux attach -t "$S"
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
tmux new-session -d -s "$S" -n campanha -c "$REPO"
tmux send-keys -t "$S:campanha" "# Campanha NORI (S0–S8 × 5 sementes, E2 real):  bash scripts/run_nori_campaign.sh" C-m
tmux send-keys -t "$S:campanha" "# Um cenário NORI:                               bash scripts/run_nori_scenario.sh S1 1001" C-m
tmux send-keys -t "$S:campanha" "# Campanha nativa (S0–S7 × B0–B3 × 5 sementes):  bash scripts/run_native_campaign.sh" C-m
tmux new-window -t "$S" -n nori -c "$REPO" "bash $O/nori_live.sh"
tmux new-window -t "$S" -n e2ap -c "$REPO" "bash $O/e2ap_live.sh"
tmux new-window -t "$S" -n xapp -c "$REPO" "bash $O/xapp_live.sh"
tmux new-window -t "$S" -n ric -c "$REPO" "bash $O/ric_live.sh"
tmux split-window -t "$S:ric" -v -l 12 -c "$REPO" "bash $O/ric_nodes.sh"
tmux new-window -t "$S" -n k8s -c "$REPO" "bash $O/k8s_live.sh"
tmux new-window -t "$S" -n ues -c "$REPO" "bash $O/ue_live.sh"
if kubectl -n monitoring get svc influxdb2 grafana >/dev/null 2>&1; then
  tmux new-window -t "$S" -n influx -c "$REPO" "bash $O/influx_live.sh"
  tmux new-window -t "$S" -n grafana -c "$REPO" "bash $O/grafana.sh"
fi
tmux select-window -t "$S:campanha"
exec tmux attach -t "$S"
