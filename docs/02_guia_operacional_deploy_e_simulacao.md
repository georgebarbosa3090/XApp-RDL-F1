# Volume 02: Guia Operacional de Deploy, Simulação e Observabilidade

> **Navegação da Documentação Consolidada:**  
> **[01. Arquitetura & Modelagem](01_arquitetura_e_modelagem.md)** | **[02. Guia Operacional & Deploy](02_guia_operacional_deploy_e_simulacao.md)** | **[03. Taxonomia de Conflitos & Cenários](03_taxonomia_de_conflitos_e_cenarios.md)** | **[04. Relatório Científico Mestre](04_relatorio_cientifico_mestre_rdl.md)** | **[05. Auditoria & Conformidade O-RAN](05_auditoria_e_conformidade_oran.md)** | **[06. Roadmap & Futuro 6G](06_roadmap_e_pesquisa_futura_6g.md)** | **[07. Resultados Simulação (S0–S15)](07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md)**

---

## 1. Pré-Requisitos e Ambiente de Execução

O ambiente de execução e desenvolvimento da xApp RDL é homologado sobre **WSL2 / Ubuntu 22.04 LTS** ou instâncias Linux nativas:

| Componente | Versão Homologada | Finalidade |
| :--- | :---: | :--- |
| **Docker Engine** | ≥ 24.0 | Execução de containers e nós k3d |
| **k3d (K3s em Docker)** | ≥ 5.6.0 | Provisionamento de cluster Kubernetes leve |
| **Helm** | ≥ 3.12.0 | Gerenciamento de pacotes e deploys de xApps |
| **Python** | ≥ 3.10 | Runtime da xApp RDL, bibliotecas e agentes |
| **ns-3** | 3.48 | Simulador de eventos discretos da RAN |
| **5G-LENA** | v5.1 | Módulo NR CTTC-LENA para camada física/MAC |
| **NORI E2 Agent** | SBrT 2025 (`9b64c12`) | Agente E2 C++ com suporte a E2AP v2.03 / E2SM-KPM / E2SM-RC |

### 1.1. Clonagem e Preparação do Repositório (WSL2 / Linux)

Para clonar ou restaurar o ambiente limpo do repositório oficial da Fase 1:

```bash
cd ~
rm -rf ~/XApp-RDL-F1

git clone https://github.com/georgebarbosa3090/XApp-RDL-F1.git
cd ~/XApp-RDL-F1
```

---

## 2. Provisionamento do Cluster Kubernetes com k3d

Para viabilizar a comunicação de sinalização O-RAN e observabilidade, o cluster k3d deve expor portas dedicadas para tráfego SCTP (E2) e HTTP/RMR:

### 2.1. Criação do Cluster Single-Node (Padrão para Dev/CI)
```bash
k3d cluster create rdl-cluster \
  --servers 1 \
  -p "36422:36422/sctp@server:0" \
  -p "8080-8087:8080-8087@server:0" \
  -p "4560-4561:4560-4561@server:0"
```

### 2.2. Criação do Cluster Dual-Node (Separação Control-Plane e Worker)
```bash
k3d cluster create rdl-cluster \
  --servers 1 \
  --agents 1 \
  -p "36422:36422/sctp@server:0" \
  -p "8080-8087:8080-8087@server:0" \
  -p "4560-4561:4560-4561@server:0"
```

### 2.3. Configuração dos Namespaces O-RAN
```bash
kubectl create namespace ricplt    # Plataforma Near-RT RIC (E2term, AppMgr, SubMgr, SDL)
kubectl create namespace ricxapp   # Micro-aplicações (RDL, xSlice, Energy Saving, Traffic Steering)
```

---

## 3. Pipeline de Deploy das xApps e Near-RT RIC

### 3.1. Deploy via Helm Charts (Recomendado)
A automação oficial está centralizada no script `scripts/deploy_helm.sh`:

```bash
# Executa deploy completo: Near-RT RIC -> xApps de referência -> xApp RDL
bash scripts/deploy_helm.sh
```

Ou realize o deploy modular manualmente:
```bash
# 1. Deploy da infraestrutura Near-RT RIC e Redis DBAAS
kubectl apply -f deploy/kubernetes/near-rt-ric.yaml

# 2. Deploy das 3 xApps de referência abertas
helm install ricxapp-qos-xslice deploy/helm/xapp-qos-xslice -n ricxapp
helm install ricxapp-energy-saving deploy/helm/xapp-energy-saving -n ricxapp
helm install ricxapp-traffic-steering deploy/helm/xapp-traffic-steering -n ricxapp

# 3. Deploy da xApp RDL (Governança e Arbitragem)
helm install ricxapp-iqos-xapp-rdl deploy/helm/iqos-xapp-rdl -n ricxapp
```

### 3.2. Deploy Alternativo via Manifestos Kubernetes
```bash
kubectl apply -f deploy/kubernetes/near-rt-ric.yaml
kubectl apply -k deploy/kubernetes/
```

### 3.3. Verificação de Saúde e Prontidão dos Pods
```bash
# Verificar status de execução
kubectl get pods -n ricplt
kubectl get pods -n ricxapp

# Smoke test automatizado de todas as xApps
bash scripts/verify_3_xapps.sh
```

---

## 4. Observabilidade, Métricas e Telemetria

### 4.1. Endpoints de Saúde e Métricas HTTP
- **Health Check Probe:** `http://localhost:8080/health` (Retorna `{"status": "UP"}`)
- **Readiness Probe:** `http://localhost:8080/ready` (Retorna `{"status": "READY"}`)
- **Métricas Prometheus:** `http://localhost:8081/metrics`
  - `rdl_conflicts_total`: Total de conflitos detectados por tipo.
  - `rdl_decisions_total`: Total de decisões emitidas por nível.
  - `rdl_decision_latency_seconds`: Histograma da latência de decisão (*T*<sub>decision</sub>).
  - `rdl_safety_blocks_total`: Total de comandos inseguros barrados pelos Safety Guards.

### 4.2. Dashboard Rancher e Kiali Service Mesh
Para habilitar observabilidade gráfica do fluxo de microsserviços:
```bash
# Instalação do Rancher Manager no k3d
docker run -d --restart=unless-stopped -p 8443:443 --privileged --name rancher-server rancher/rancher:latest

# Instalação do Kiali (após provisionamento Istio)
bash scripts/install_kiali.sh
```

---

## 5. Pipeline de Co-Simulação ns-3.48 / 5G-LENA / NORI

### 5.1. Compilação dos Cenários ns-3
Dentro do workspace ns-3 com 5G-LENA v5.1 e extensão NORI:
```bash
# Configuração do CMake com suporte a Ninja e modo otimizado
./ns3 configure -d optimized --enable-examples --enable-tests

# Compilação dos executáveis de cenário (S0 a S15)
./ns3 build
```

### 5.2. Execução Automatizada da Suíte Completa (S0 a S15)
```bash
# Executa todos os 16 cenários com rastreamento FlowMonitor
bash simulations/ns3/run_all_s0_s15_simulations.sh all
```

### 5.3. Processamento de Traces FlowMonitor e Geração de Relatórios
```bash
# Parser e consolidação de métricas em Markdown e CSV
python3 scripts/generate_ns3_flowmonitor_markdown_report.py
```

### 5.4. Geração de Gráficos e Tabelas Analíticas
Para atualizar os gráficos e as tabelas analíticas a partir dos dados experimentais:
```bash
# Execução direta com uv:
uv run --with matplotlib --with seaborn --with pandas --with scipy python analysis/generate_plots.py
uv run --with matplotlib --with seaborn --with pandas --with scipy python analysis/export_tables.py
```

---

## 6. Integração com Testbed Físico GreenRAN (UFPA)

Para validação em hardware de rádio real e ambiente O-RAN desagregado:

```
┌─────────────────────────────────────────────────────────────┐
│                    TESTBED GREENRAN / UFPA                  │
│                                                             │
│  ┌──────────────────┐    SCTP:36422   ┌──────────────────┐  │
│  │   Near-RT RIC    │◄───────────────►│    srsRAN gNB    │  │
│  │   (xApp RDL)     │   E2AP / E2SM   │   (Open5GS Core) │  │
│  └──────────────────┘                 └────────┬─────────┘  │
│                                                │ RF / 3.5GHz│
│                                       ┌────────▼─────────┐  │
│                                       │  USRP N310 / B210│  │
│                                       └────────┬─────────┘  │
│                                                │ Over-The-Air│
│                                       ┌────────▼─────────┐  │
│                                       │ UEs Comerciais 5G│  │
│                                       └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

1. **Configuração da gNodeB srsRAN 24.10:** Configurar `e2_ip` apontando para o IP do pod `e2term` no cluster K8s.
2. **Core 5G (Open5GS):** Provisionar fatias URLLC (`SST=2, SD=0x000001`) e eMBB (`SST=1, SD=0x000001`).
3. **Rádios USRP:** Fixar potência de transmissão em 23 dBm (limite COTS indoor) e largura de canal em 100 MHz na banda n78 (3,5 GHz).

---

## 7. Troubleshooting e Limpeza do Ambiente

### 7.1. Diagnóstico e Resolução de Problemas
| Sintoma | Causa Mais Provável | Procedimento de Resolução |
| :--- | :--- | :--- |
| **Porta 36422 recusada (SCTP)** | Pod `e2term` não inicializado ou firewall | `kubectl describe pod -l app=e2term -n ricplt` e verificar regras `iptables` |
| **RMR Routing Failure (`RMR_ERR_NOENDPT`)** | Tabela de rotas RMR desatualizada | Verificar `configs/routes.rt` e reiniciar pod da RDL |
| **Conflitos de portas locais (8080)** | Outro serviço ocupando a porta | Modificar mapeamento no `k3d cluster create` para `8090:8080` |
| **Falha de memória no ns-3** | Múltiplas instâncias simultâneas | Executar com limitador de processos simultâneos |

### 7.2. Backup e Sincronização Automática com GitHub
Para manter qualquer alteração local sincronizada automaticamente no GitHub em tempo real:

```bash
# Execução do daemon de sincronização contínua (auto add, commit e push)
uv run python scripts/auto_git_sync.py

# Ou via Make:
make auto-sync
```

O repositório também inclui hook nativo `.git/hooks/post-commit` para envio automático imediato ao realizar commits manuais. Para sincronização entre repositórios F1 e F2:

```bash
make sync-cross
```

### 7.3. Limpeza e Reinicialização Completa do Ambiente
```bash
# Desinstala as xApps do cluster
make helm-uninstall

# Remove o cluster k3d e containers residuais
make cluster-delete
```
