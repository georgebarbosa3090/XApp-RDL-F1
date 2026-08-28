# Volume 03: Guia de Deploy, Observabilidade, Testes e Simulações no ns-3 NORI / 5G-LENA

> **Navegação Sequencial:** [Vol 01: Arquitetura Core](01_arquitetura_e_modelagem_matematica.md) -> [Vol 02: Infraestrutura & Rancher](02_infraestrutura_cluster_k3d_e_rancher.md) -> **[Vol 03: Deploy, Testes & Simulações ns-3]** -> [Vol 04: Conformidade O-RAN](04_relatorios_conformidade_e_governanca.md) -> [Vol 05: Operação & Troubleshooting](05_operacao_troubleshooting_e_backup.md)

**Documento:** Volume Temático 03 (Unificado)  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL Determinística)  
**Escopo:** Pipeline Completo de Deploy (Near-RT RIC, 3 Reference xApps, xApp RDL via Helm e K8s), Observabilidade em Tempo Real (Rancher & Kiali), Suíte de Testes (Unitários e Smoke Test), Guia de Instalação do ns-3 NORI / 5G-LENA, Cenários C++, Protocolo Experimental Passo a Passo (Baseline vs H-RDL), Datasets CSV e Integração Google Colab / Scikit-Learn.  
**Data de Consolidação:** 28/08/2026  

---

# PARTE I: GUIA DE DEPLOY DO NEAR-RT RIC, DAS 3 REFERENCE XAPPS E DA XAPP RDL (HELM & K8S)

---

## 1. Visão Geral da Arquitetura de Implantação

O pipeline de implantação orquestra os componentes em dois namespaces isolados (`ricplt` e `ricxapp`) com dependência estrita de ordem:

```mermaid
flowchart TD
    subgraph STAGE1["Etapa 1: Infraestrutura Near-RT RIC (Namespace: ricplt)"]
        REDIS["Redis DBAAS (:6379)<br/>Shared Data Layer"]
        E2TERM["E2Term SCTP/RMR (:36422 / :38000)"]
        SUBMGR["Subscription Manager (:4560)"]
    end

    subgraph STAGE2["Etapa 2: Workloads Concorrentes (Namespace: ricxapp)"]
        XSLICE["1. xSlice QoS xApp<br/>(peihaoY/xslice-oran)<br/>HTTP :8082 | Metrics :8083"]
        ES["2. Energy Saving xApp<br/>(Orange-OpenSource/ns-O-RAN-flexric)<br/>HTTP :8084 | Metrics :8085"]
        TS["3. Traffic Steering xApp<br/>(o-ran-sc/ric-app-ts)<br/>HTTP :8086 | Metrics :8087"]
    end

    subgraph STAGE3["Etapa 3: Arbitragem & Governança (Namespace: ricxapp)"]
        RDL["4. xApp RDL (Fase 1: H-RDL)<br/>Arbitrador TVS/EEVS & Safety Guards<br/>HTTP :8080 | Metrics :8081 | RMR :4560"]
    end

    STAGE1 -->|Plataforma Pronta| STAGE2
    STAGE2 -.->|"Modo Baseline (Sem RDL)"| NS3_BASELINE["Conflitos Diretos na RAN (Sem Governança)"]
    STAGE2 -->|"Modo Governança (Com RDL)"| STAGE3
    STAGE3 -->|Decisões Arbitradas E2SM-RC| E2TERM
```

---

## 2. As 3 Reference xApps da Literatura Integradas

| xApp | Projeto Base / Repositório | Porta HTTP / Métricas | Parâmetro Emitido (`RDL_ACTION_PROPOSAL`) |
| :--- | :--- | :---: | :--- |
| **1. xSlice (QoS & Slicing)** | [`peihaoY/xslice-oran`](https://github.com/peihaoY/xslice-oran) | `:8082` / `:8083` | `PRB_QUOTA = 80%` (Prioridade: 90 / Fatias URLLC) |
| **2. Energy Saving (ES)** | [`Orange-OpenSource/ns-O-RAN-flexric`](https://github.com/Orange-OpenSource/ns-O-RAN-flexric) | `:8084` / `:8085` | `TX_POWER = 20 dBm` (Prioridade: 65 / Green RAN) |
| **3. Traffic Steering (TS)** | [`o-ran-sc/ric-app-ts`](https://github.com/o-ran-sc/ric-app-ts) | `:8086` / `:8087` | `HANDOVER = UE-07 -> gNB-02` (Prioridade: 80) |

---

## 3. Deploy via Helm (Padrão O-RAN)

### 3.1. Modo Baseline (Near-RT RIC + 3 Reference xApps SEM RDL)
Implanta a plataforma Near-RT RIC e as 3 xApps concorrentes isoladas, sem o arbitrador RDL, para fins de coleta de dados de referência e validação de conflitos:
```bash
make helm-deploy-baseline
```

### 3.2. Modo Governança Completa (Near-RT RIC + 3 Reference xApps + RDL)
Implanta a plataforma Near-RT RIC, as 3 xApps concorrentes e a camada de arbitragem RDL:
```bash
make helm-deploy
```

---

## 4. Deploy Kubernetes Puro / Kustomize

### 4.1. Modo Baseline (Sem RDL):
```bash
make k8s-deploy-baseline
```

### 4.2. Modo Governança (Com RDL):
```bash
make k8s-deploy
```

---

## 5. Validação Automatizada e Smoke Test (`make test-3xapps`)

O repositório disponibiliza um verificador em tempo real que abre conexões e valida a saúde e as métricas Prometheus de todas as xApps ativas:

```bash
make test-3xapps
# Ou diretamente:
bash scripts/verify_3_xapps.sh
```

**Saída Esperada no Terminal:**
```text
======================================================================
   Validação e Smoke Test das xApps O-RAN no namespace 'ricxapp'
======================================================================

[1/4] Listando Pods em execucao no namespace ricxapp...
NAME                                       READY   STATUS    RESTARTS   AGE
ricxapp-qos-xslice-5c49d8c977-ab12         1/1     Running   0          45s
ricxapp-energy-saving-6d8b9487c-ef34       1/1     Running   0          45s
ricxapp-traffic-steering-747d95b5cb-xy56   1/1     Running   0          45s
ricxapp-iqos-xapp-rdl-84cfbb996b-zw78      1/1     Running   0          40s

[2/4] Validando 1. xSlice QoS xApp (peihaoY/xslice-oran)...
  -> Healthcheck /health: {"status":"UP","xapp":"xslice_oran","role":"QoS_Slicing"}
  -> Proposta Recente /proposals/latest: {"xapp_id":"xslice_oran","parameter":"PRB_QUOTA","value":80.0,"priority":90}
  -> Metricas Prometheus: xslice_proposals_total 12.0

[3/4] Validando 2. Energy Saving xApp (Orange-OpenSource/ns-O-RAN-flexric)...
  -> Healthcheck /health: {"status":"UP","xapp":"energy_saving_orange","role":"Energy_Saving"}
  -> Proposta Recente /proposals/latest: {"xapp_id":"energy_saving_orange","parameter":"TX_POWER","value":20.0,"priority":65}
  -> Metricas Prometheus: es_proposals_total 10.0

[4/4] Validando 3. Traffic Steering xApp (o-ran-sc/ric-app-ts)...
  -> Healthcheck /health: {"status":"UP","xapp":"traffic_steering_oransc","role":"Traffic_Steering"}
  -> Proposta Recente /proposals/latest: {"xapp_id":"traffic_steering_oransc","parameter":"HANDOVER","priority":80}
  -> Metricas Prometheus: ts_proposals_total 8.0

[EXTRA] Validando 4. xApp RDL (Resource and Decision Layer - Fase 1)...
  -> Healthcheck /health: {"status":"UP","ready":true}
  -> Metricas Prometheus: rdl_decisions_total 30.0

======================================================================
   Verificação Concluída com SUCESSO!
======================================================================
```

---

## 6. Observabilidade e Gestão de Cluster (Rancher & Kiali)

### 6.1. Rancher Dashboard (Gestão Global do Cluster e Nós)
```bash
# 1. Iniciar o contêiner do Rancher Server:
make rancher-start

# 2. Obter a senha de primeiro acesso (Bootstrap Password):
make rancher-password

# 3. Acessar https://localhost:8443 no navegador e importar o cluster 'rancher-lab'
# 4. Conectar o cluster ao Rancher automaticamente:
make rancher-connect URL="https://localhost:8443/v3/import/c-m-xxxx_c-m-xxxx.yaml"
```
> *Para o passo a passo detalhado de configuração de rede e certificados TLS, consulte o **[Volume 02: Infraestrutura de Cluster e Rancher](02_infraestrutura_cluster_k3d_e_rancher.md)**.*

### 6.2. Kiali Service Mesh (Visualização do Grafo de Tráfego entre xApps)
```bash
# Instalar Service Mesh Istio e Dashboard Kiali:
make kiali-install

# Abrir painel Kiali (http://localhost:20001/kiali):
make kiali-dashboard

# Iniciar gerador de tráfego para visualizar grafo animado:
make start-traffic
```

---
---

# PARTE II: TESTES, SIMULAÇÃO NO NS-3 NORI / 5G-LENA, PROCEDIMENTO EXPERIMENTAL E BENCHMARKS

---

## 7. Estratégia de Testes Unitários e Validação de CI

A suíte de testes unitários cobre 100% dos componentes críticos da xApp RDL, executada via `pytest`:

* **Testes de Codecs APER (`tests/test_aper_codecs.py`):** Validação de decodificação E2AP/KPM e codificação E2SM-RC.
* **Testes de Percepção (`tests/test_perception_agent.py`):** Detecção de conflitos diretos, indiretos e cenários de tráfego regular.
* **Testes de Raciocínio (`tests/test_reasoning_agent.py`):** Resolução por prioridade de fatias de serviço (URLLC > eMBB > mMTC).
* **Testes de Refinamento (`tests/test_refinement_agent.py`):** Validação dos *Safety Guards* (limites de potência, PRB e taxa).

### 7.1. Execução dos Testes Unitários:

#### Opção A: Execução no Host (Virtualenv)
```bash
# 1. Criar e ativar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt

# 3. Executar a suíte de testes
make test
# Saída esperada: 10 passed in 1.20s (100% green)
```

#### Opção B: Execução via Contêiner Docker (Sem dependências no host)
```bash
docker run --rm -v $(pwd):/app -w /app -u 0 iqos-xapp-rdl:1.1.0 sh -c "pip install -r requirements-dev.txt && pytest tests/ -v"
```

---

## 8. Relatório Formal do Smoke Test (Standalone Container)

O Smoke Test valida a integridade dos serviços HTTP e Prometheus em container isolado antes do deploy no Kubernetes:

| Endpoint / Serviço | Porta | Método | Resposta Esperada | Status |
| :--- | :---: | :---: | :--- | :---: |
| **Liveness / Health** | `8090` | `GET /health` | HTTP `200 OK` `{"status":"UP"}` | APROVADO |
| **Readiness** | `8090` | `GET /ready` | HTTP `200 OK` `{"ready":true}` | APROVADO |
| **Prometheus Metrics** | `8091` | `GET /metrics` | Métricas `rdl_decision_latency_seconds`, `dl_kpm_indications_total` | APROVADO |

```bash
make smoke-test
```

---

## 9. Visão Geral da Co-Simulação ns-3 NORI / 5G-LENA e Near-RT RIC

O **ns-3 NORI** (integrado ao ecossistema *ns-O-RAN* do OpenRAN Gym) conecta o simulador de rede de eventos discretos **ns-3** (com o módulo 5G **5G-LENA**) à arquitetura padronizada **O-RAN Alliance**.

Na **Fase 1 (H-RDL)**, as estações rádio-base 5G NR (*gNodeBs*) simuladas no ns-3 enviam telemetria de rádio contínua (**E2SM-KPM**) via socket SCTP (porta 36422) para a terminação **E2Term** do Near-RT RIC. Múltiplas xApps concorrentes emitem requisições de controle (**E2SM-RC**) para os mesmos nós, e a **xApp RDL** arbitra esses conflitos de forma determinística utilizando janelas de decisão em lote ($\Delta t = 200\text{ ms}$), funções de utilidade multiobjetivo (**TVS/EEVS**) e barreiras de segurança física (*Safety Guards*).

```mermaid
flowchart TD
    subgraph NS3["Ambiente de Simulação de Rádio (ns-3 NORI / 5G-LENA)"]
        GNB1["gNodeB 01 (Macro Cell)<br/>3.5 GHz n78 (100 MHz)"]
        GNB2["gNodeB 02 (Small Cell)<br/>3.5 GHz n78 (100 MHz)"]
        UES["Terminal de Usuários (30 UEs)<br/>Fatias: URLLC | eMBB | mMTC"]
        E2A["E2 Agent (ns-O-RAN)<br/>SCTP Client (Porta 36422)"]
        
        UES <-->|Canal 3GPP UMi| GNB1
        UES <-->|Canal 3GPP UMi| GNB2
        GNB1 --> E2A
        GNB2 --> E2A
    end

    subgraph O_RAN_RIC["Cluster Near-RT RIC (Kubernetes / k3d)"]
        E2T["E2 Termination (E2Term)<br/>SCTP Server (:36422)"]
        RMR["RMR Bus (Mensageria O-RAN)"]
        
        subgraph XAPPS["Namespace: ricxapp"]
            TS["xApp Traffic Steering<br/>(Solicita Handover)"]
            QOS["xApp QoS Manager<br/>(Solicita Boost de PRB)"]
            ES["xApp Energy Savings<br/>(Solicita Corte de Potência)"]
            
            subgraph RDL_CORE["xApp RDL (Fase 1: H-RDL)"]
                DW["Decision Window (200ms Buffer)"]
                PA["PerceptionAgent<br/>(Detecção Par a Par)"]
                RA["ReasoningAgent<br/>(Heurísticas TVS / EEVS)"]
                SG["RefinementAgent<br/>(Safety Guards & Clamp)"]
            end
        end
    end

    E2A <-->|"SCTP 36422: E2SM-KPM / E2SM-RC"| E2T
    E2T <-->|RMR Internal Msg| RMR
    RMR <--> TS
    RMR <--> QOS
    RMR <--> ES
    RMR --> DW
    DW --> PA --> RA --> SG
    SG -->|E2SM-RC Control Arbitrado| RMR
    RMR --> E2T
```

---

## 10. Dicionário de Parâmetros de Simulação e Slices 5G

### 10.1. Parâmetros de Camada Física e Rádio (5G-LENA)
| Parâmetro | Variável C++ / ns-3 | Valor Padrão | Descrição Técnica |
| :--- | :--- | :---: | :--- |
| **Frequência Central** | `centralFrequencyBand1` | `3.5e9` (3.5 GHz) | Banda n78 (FR1) padrão para redes 5G privativas e públicas. |
| **Largura de Banda** | `bandwidthBand1` | `100e6` (100 MHz) | Largura de canal fornecendo até 273 Resource Blocks (PRBs). |
| **Numerologia ($\mu$)** | `numerologyBwp1` | `1` | Espaçamento de subportadora $\Delta f = 30\text{ kHz}$ ($14 \text{ slots/ms}$). |
| **Modulação e Codificação** | `FixedMcsDl` / `StartingMcsDl` | Adaptativo (MCS 0-28) | Ajuste dinâmico de taxa com base no CQI/SINR reportado pelos UEs. |
| **Distância entre gNBs** | `gridScenario.SetHorizontalBsDistance()` | `80.0 m` | Distância que força sobreposição de cobertura e conflitos de ação. |
| **Elementos de Antena gNB** | `NumRows=4, NumColumns=8` | 32 elementos | Matriz planar uniforme para beamforming massivo (mMIMO). |

### 10.2. Parâmetros de Tráfego por Fatia de Serviço (Network Slicing)
| Fatia de Rede | Tipo de Tráfego | Tamanho do Pacote | Intervalo de Envio | Taxa / Vazão | Prioridade na RDL |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Fatia 1: URLLC** | Missão Crítica / Controle | 128 Bytes | $1\text{ ms}$ | ~1.02 Mbps | **1 (Máxima)** |
| **Fatia 2: eMBB** | Streaming 4K / Alta Taxa | 1400 Bytes | $200\text{ }\mu\text{s}$ | ~56 Mbps | **2 (Média)** |
| **Fatia 3: mMTC** | Telemetria Sensores IoT | 64 Bytes | $100\text{ ms}$ | ~5.12 kbps | **3 (Baixa)** |

---

## 11. Guia de Instalação e Compilação do ns-3 NORI / 5G-LENA

O simulador pode ser configurado de forma totalmente automatizada através do script de automação ou manualmente.

### 11.1. Opção A: Instalação Automatizada (Recomendada)
A partir da raiz do repositório (`~/XApp-RDL-F1`), execute:
```bash
make setup-ns3
# ou: bash scripts/setup_ns3.sh
```
*O script detecta privilégios de root, instala todas as dependências apt, valida GCC/G++ >= 11 e CMake >= 3.25, clona o `ns-3-dev`, baixa o módulo oficial `5G-LENA` em `contrib/nr`, copia os cenários para `scratch/` e compila com `-j$(nproc)`.*

### 11.2. Opção B: Instalação Manual Passo a Passo

```bash
# 1. Instalar dependências essenciais no WSL2 / Ubuntu (se root, omita o sudo):
apt-get update && apt-get install -y \
  build-essential cmake ninja-build git python3-dev python3-pip \
  libsctp-dev lksctp-tools libzmq3-dev libboost-all-dev \
  libsqlite3-dev libgsl-dev libxml2-dev tcpdump wireshark pkg-config wget curl

# 2. Garantir CMake >= 3.25 (o Ubuntu 20.04 possui CMake 3.16 por padrão; o ns-3 exige >= 3.25)
pip3 install --upgrade cmake

# 3. Clonar repositório do ns-3 e o módulo 5G-LENA (nr)
mkdir -p ~/ns3-oran-workspace && cd ~/ns3-oran-workspace
git clone https://gitlab.com/nsnam/ns-3-dev.git ns-3-oran --depth 1
cd ns-3-oran
git clone https://gitlab.com/cttc-lena/nr.git contrib/nr --depth 1

# 4. Ajuste de compatibilidade para execução como root no WSL2/Docker (se aplicável):
sed -i 's/def refuse_run_as_root():/def refuse_run_as_root():\n    return/g' ./ns3

# 5. Copiar cenários do projeto para o diretório scratch:
cp ~/XApp-RDL-F1/simulations/ns3/*.cc ./scratch/

# 6. Limpar cache anterior e configurar compilação com CMake
rm -rf cmake-cache build
./ns3 configure -d optimized --enable-examples --enable-tests

# 7. Compilar o simulador
./ns3 build -j$(nproc)
```

---

## 12. Cenários de Simulação Implementados em C++

1. **Cenário 1: Mitigação de Conflitos TVS (`simulations/ns3/scenario_rdl_tvs_conflict.cc`):**
   - 2 células com 30 UEs sob alta interferência.
   - A xApp Traffic Steering solicita transição forçada de 10 UEs para a célula secundária, enquanto a xApp QoS solicita aumento de PRBs para a Fatia 1 (URLLC).
   - A xApp RDL intercepta as mensagens E2, detecta o conflito na janela de 200ms e arbitra a favor da fatia URLLC.

2. **Cenário 2: Economia de Energia vs Garantia de SLA (`simulations/ns3/scenario_rdl_energy_vs_qos.cc`):**
   - A xApp Energy Savings tenta desligar a portadora da micro-célula no instante $t = 10\text{ s}$.
   - No mesmo instante, surge uma rajada crítica de pacotes URLLC.
   - A xApp RDL avalia a função EEVS e bloqueia o corte de energia enquanto a demanda de SLA estiver ativa.

---

## 13. Procedimento Experimental Passo a Passo

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Engenheiro / Pesquisador
    participant K8s as Cluster k3d / Rancher
    participant RIC as Near-RT RIC (E2Term + RDL)
    participant NS3 as ns-3 NORI Simulation
    participant Collector as Coleta e Relatórios

    Note over Dev,NS3: Rodada 1: Baseline Sem RDL
    Dev->>NS3: ./ns3 run "scenario_rdl_tvs_conflict --enableE2=false"
    NS3-->>Collector: Salva traces em experiments/results/baseline/

    Note over Dev,RIC: Rodada 2: Com xApp RDL (H-RDL)
    Dev->>K8s: make cluster-create
    Dev->>RIC: make helm-deploy
    Dev->>NS3: ./ns3 run "scenario_rdl_tvs_conflict --enableE2=true"
    NS3->>RIC: E2SM-KPM Indications (200ms)
    RIC->>RIC: RDL Perception + Reasoning TVS + Safety Guards
    RIC->>NS3: E2SM-RC Control Message (Ação Arbitrada)
    RIC-->>Collector: Salva logs em experiments/results/rdl_phase1/rdl_logs.jsonl
    RIC-->>Collector: Dump Prometheus em experiments/results/rdl_phase1/prometheus_metrics.prom
    NS3-->>Collector: Salva traces em experiments/results/rdl_phase1/

    Note over Collector: Etapa 3: Consolidação e Gráficos
    Dev->>Collector: python3 scripts/run_and_analyze_benchmarks.py
    Collector-->>Dev: relatorio_comparativo.md / json / graficos_benchmarks_rdl.png
```

### 13.1. Execução do Pipeline Automatizado
Para executar as duas rodadas experimentais, processar os traces com FlowMonitor e gerar relatórios comparativos:

```bash
# Executar pipeline completo (Baseline + H-RDL + Análise):
make run-experiments

# Reprocessar métricas e regenerar datasets CSV a qualquer momento:
make analyze-benchmarks
```

### 13.2. Acesso, Visualização e Sincronização com o GitHub

Após a conclusão dos experimentos, os resultados podem ser inspecionados ou enviados para o GitHub com os seguintes comandos:

```bash
# 1. Visualizar o relatório executivo formatado no terminal:
make view-results
# ou: cat experiments/results/relatorio_comparativo.md

# 2. Inspecionar métricas JSON estruturadas:
python3 -m json.tool experiments/results/relatorio_comparativo.json

# 3. Inspecionar primeiras linhas dos datasets:
head -n 10 experiments/results/dataset_rdl_decisions_ml.csv
head -n 10 experiments/results/dataset_flow_metrics.csv

# 4. Sincronizar e enviar todos os resultados e datasets para o GitHub:
make push-results
```

#### Acesso aos Arquivos via Host (Windows / WSL2 / Remoto)
* **No Windows Explorer (WSL2):** Pressione `Win + R` e acesse `\\wsl$\Ubuntu\root\XApp-RDL-F1\experiments\results` para abrir os arquivos `.csv` e `.md` diretamente no Excel ou VS Code.
* **Via SSH Remoto (SCP):**
  ```bash
  scp -r root@<IP_DO_SERVIDOR>:~/XApp-RDL-F1/experiments/results ./meus_resultados
  ```

---

## 14. Análise com Scikit-Learn e Google Colab

Os datasets estruturados gerados pela simulação (`experiments/results/dataset_flow_metrics.csv` e `experiments/results/dataset_rdl_decisions_ml.csv`) alimentam diretamente o notebook de Machine Learning:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/georgebarbosa3090/XApp-RDL-F1/blob/main/notebooks/rdl_colab_scikit_learn.ipynb)

* **Notebook:** [`notebooks/rdl_colab_scikit_learn.ipynb`](../notebooks/rdl_colab_scikit_learn.ipynb)
* **Modelos Treinados:** Random Forest, Decision Tree e Gradient Boosting para predição antecipada de conflitos O-RAN e relevância de variáveis (*Feature Importance*).

---

## 15. Próximo Passo Sequencial

Avance para a análise de governança e matriz de conformidade com as normas O-RAN Alliance:

-> **[Volume 04: Relatórios de Conformidade Técnica e Governança O-RAN](04_relatorios_conformidade_e_governanca.md)**
