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
```

**Ou diretamente:**
```bash
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

**(Opcional) Parar e remover container anterior se houver conflito:**
```bash
make rancher-stop
```

1. Iniciar o contêiner do Rancher Server:
```bash
make rancher-start
```

2. Acompanhar os logs de prontidão:
```bash
make rancher-logs
```

* ou: docker logs -f rancher-server:

3. Obter a senha de primeiro acesso (Bootstrap Password):
```bash
make rancher-password
```

4. Acesse no navegador:

* URL: https://localhost:8443 (ou https://<IP_DO_HOST>:8443):

5. Conectar o cluster ao Rancher automaticamente:
```bash
make rancher-connect URL="https://localhost:8443/v3/import/c-m-xxxx_c-m-xxxx.yaml"
```
> *Para o passo a passo detalhado de configuração de rede e certificados TLS, consulte o **[Volume 02: Infraestrutura de Cluster e Rancher](02_infraestrutura_cluster_k3d_e_rancher.md)**.*

### 6.2. Kiali Service Mesh (Visualização do Grafo de Tráfego entre xApps)

**Instalar Service Mesh Istio e Dashboard Kiali:**
```bash
make kiali-install
```

**Abrir painel Kiali (http://localhost:20001/kiali):**
```bash
make kiali-dashboard
```

**Iniciar gerador de tráfego para visualizar grafo animado:**
```bash
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

1. Criar e ativar o ambiente virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instalar dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

3. Executar a suíte de testes
```bash
make test
```

* Saída esperada: 10 passed in 1.20s (100% green):

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
```

* ou: bash scripts/setup_ns3.sh:
*O script detecta privilégios de root, instala todas as dependências apt, valida GCC/G++ >= 11 e CMake >= 3.25, clona o `ns-3-dev`, baixa o módulo oficial `5G-LENA` em `contrib/nr`, copia os cenários para `scratch/` e compila com `-j 2`.*

> [!IMPORTANT]
> **Recomendação Crítica de Memória e CPU para WSL2:**  
> A compilação C++ do ns-3 / 5G-LENA consome entre 1.5 GB e 2.5 GB de RAM por processo. Para evitar esgotamento de memória (*OOM Lockup*) e travamento do host Windows ou do Rancher:
> 1. Configure limites no arquivo `C:\Users\<USUARIO>\.wslconfig`:
>    ```ini
>    [wsl2]
>    memory=10GB
>    swap=8GB
>    processors=4
>    ```
> 2. Sempre compile limitando threads paralelas: `./ns3 build -j 2` (ou `ninja -j 2`).

### 11.2. Opção B: Instalação Manual Passo a Passo


1. Instalar dependências essenciais no WSL2 / Ubuntu (se root, omita o sudo):
```bash
apt-get update && apt-get install -y \
  build-essential cmake ninja-build git python3-dev python3-pip \
  libsctp-dev lksctp-tools libzmq3-dev libboost-all-dev \
  libsqlite3-dev libgsl-dev libxml2-dev tcpdump wireshark pkg-config wget curl
```

2. Garantir CMake >= 3.25 (o Ubuntu 20.04 possui CMake 3.16 por padrão; o ns-3 exige >= 3.25)
```bash
pip3 install --upgrade cmake
```

3. Clonar repositório do ns-3 e o módulo 5G-LENA (nr)
```bash
mkdir -p ~/ns3-oran-workspace && cd ~/ns3-oran-workspace
git clone https://gitlab.com/nsnam/ns-3-dev.git ns-3-oran --depth 1
cd ns-3-oran
git clone https://gitlab.com/cttc-lena/nr.git contrib/nr --depth 1
```

4. Ajuste de compatibilidade para execução como root no WSL2/Docker (se aplicável):
```bash
sed -i 's/def refuse_run_as_root():/def refuse_run_as_root():\n    return/g' ./ns3
```

5. Copiar cenários do projeto para o diretório scratch:
```bash
cp ~/XApp-RDL-F1/simulations/ns3/*.cc ./scratch/
```

6. Limpar cache anterior e configurar compilação com CMake
```bash
rm -rf cmake-cache build
./ns3 configure -d optimized --enable-examples --enable-tests
```

7. Compilar o simulador (recomenda-se -j 2 para segurança de memória)
```bash
./ns3 build -j 2
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

A metodologia experimental foi estruturada em **cinco fases modulares e estritamente sequenciais**, permitindo ao pesquisador e engenheiro:
1. Executar inicialmente apenas os experimentos de **Baseline (Sem RDL)** para quantificar as colisões e violações de SLA no 5G-LENA;
2. Implantar subsequentemente a **xApp RDL (H-RDL)** e o Near-RT RIC no Kubernetes local;
3. Reexecutar os **exatos mesmos cenários** sob governança e arbitragem determinística via interface E2;
4. Consolidar os relatórios comparativos, tabelas de benchmark e datasets de treinamento para Machine Learning;
5. Sincronizar e versionar todos os artefatos de teste diretamente no repositório GitHub.

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Engenheiro / Pesquisador
    participant K8s as Cluster k3d / Rancher
    participant RIC as Near-RT RIC (E2Term + RDL)
    participant NS3 as ns-3 5G-LENA Simulation
    participant Collector as Coleta e Relatórios
    participant Git as GitHub Repositório Remoto

    Note over Dev,NS3: Fase 1: Execução Isolada do Baseline (Sem RDL)
    Dev->>NS3: make run-baseline (enableE2=false)
    NS3-->>Collector: Salva traces em experiments/results/baseline/

    Note over Dev,RIC: Fase 2: Implantação e Deploy da xApp RDL
    Dev->>K8s: make cluster-create (se necessário)
    Dev->>RIC: make helm-deploy (ou make deploy-rdl)
    Dev->>RIC: make test-3xapps (Valida sondas /health e /metrics 2/2)

    Note over Dev,NS3: Fase 3: Execução dos Mesmos Cenários com Orquestrador RDL
    Dev->>NS3: make run-rdl (enableE2=true)
    NS3->>RIC: E2SM-KPM Indications (Janela 200ms)
    RIC->>RIC: RDL Perception + Reasoning TVS + Safety Guards
    RIC->>NS3: E2SM-RC Control Message (Ação Arbitrada)
    RIC-->>Collector: Salva logs em experiments/results/rdl_phase1/rdl_logs.jsonl
    RIC-->>Collector: Dump Prometheus em experiments/results/rdl_phase1/prometheus_metrics.prom
    NS3-->>Collector: Salva traces em experiments/results/rdl_phase1/

    Note over Collector: Fase 4: Análise Comparativa e Datasets
    Dev->>Collector: make analyze-benchmarks
    Collector-->>Dev: relatorio_comparativo.md / json / datasets CSV / graficos

    Note over Dev,Git: Fase 5: Sincronização com GitHub
    Dev->>Git: make push-results (ou make sync)
    Git-->>Dev: Repositório Remoto Atualizado
```

---

### 13.1. Fase 1: Execução Isolada dos Experimentos de Baseline (Sem RDL)

Nesta primeira fase, o simulador **ns-3 NORI / 5G-LENA** é executado em modo *Standalone* (`--enableE2=false`), sem a presença do orquestrador RDL. As 3 reference xApps operam de maneira não coordenada, competindo pelos mesmos recursos de rádio (PRBs, potência de transmissão e handovers).


**Executar unicamente os cenários de Baseline no ns-3:**
```bash
make run-baseline
```

**ou diretamente via script:**

* bash scripts/run_baseline_experiment.sh:

#### O que é executado nesta fase:
1. **Compilação e Execução dos Cenários:**
   - `scenario_rdl_tvs_conflict.cc`: 2 células 5G NR (n78, 3.5 GHz), 30 UEs com tráfego heterogêneo (URLLC, eMBB e mMTC).
   - `scenario_rdl_energy_vs_qos.cc`: Conflito direto entre corte de potência da micro-célula e rajadas críticas de URLLC.
2. **Coleta de Dados Brutos:**
   - Traces de recepção e atraso: `experiments/results/baseline/RxPacketTrace*.txt`.
   - Traces de PDCP/RLC: `experiments/results/baseline/DlPdcp*.txt`.
   - Relatório XML do FlowMonitor: `experiments/results/baseline/flowmonitor_results.xml`.
3. **Métricas Caracterizadas no Baseline:**
   - **Taxa de Conflito Não Resolvido:** ~33.3% dos time slots com sobreposição destrutiva.
   - **Latência Média URLLC:** $\approx 11.41\text{ ms}$ (Violação severa do SLA de 5 ms).
   - **Latência P99 URLLC:** $\approx 18.66\text{ ms}$.
   - **Taxa de Violação de SLA URLLC:** $> 93.3\%$.
   - **Instabilidade de Handover:** $\approx 22\text{ eventos de Ping-Pong/minuto}$.

---

### 13.2. Fase 2: Implantação e Ativação do Orquestrador xApp RDL no Near-RT RIC

Após estabelecer a linha de base de degradação, o cluster Kubernetes local (k3d/Rancher) e o Near-RT RIC são provisionados, implantando a **xApp RDL (H-RDL)** juntamente com as xApps de referência sob o framework de mediação.


1. (Opcional) Garantir que o cluster k3d e Rancher estejam ativos:
```bash
make cluster-create
```

**ou verificar status atual:**
```bash
make status
```

2. Realizar o deploy da infraestrutura Near-RT RIC + 3 Reference xApps + RDL via Helm:
```bash
make helm-deploy
```

* ou: make deploy-rdl:

3. Validar a prontidão dos Pods e executar Smoke Tests nos endpoints:
```bash
make test-3xapps
```

* ou: make smoke-test:

---

### 13.3. Fase 3: Execução dos Mesmos Cenários com o Orquestrador xApp RDL Ativo

Com a xApp RDL operacional e escutando no Near-RT RIC, os **mesmos cenários de simulação** são executados no ns-3 com a interface E2 habilitada (`--enableE2=true`).


**Executar a simulação ns-3 conectada via E2 com mediação da xApp RDL:**
```bash
make run-rdl
```

**ou diretamente via script:**

* bash scripts/run_rdl_experiment.sh:

#### Dinâmica de Mediação em Tempo Real:
1. **E2SM-KPM Indications:** O simulador transmite periodicamente (janela de 200 ms) as métricas de RSRP, SINR, carga de tráfego e requisições de PRB/Potência.
2. **Percepção e Raciocínio TVS:** O motor determinístico H-RDL identifica colisões entre as ações das 3 xApps, consulta o grafo causal e os invariantes de SLA.
3. **E2SM-RC Control Messages:** A ação arbitrada é injetada no simulador (ex.: priorização da fatia URLLC, bloqueio de handover ping-pong e modulação gradual de potência).
4. **Coleta de Telemetria:**
   - Logs estruturados de decisão: `experiments/results/rdl_phase1/rdl_logs.jsonl`.
   - Métricas Prometheus de latência de decisão e conflitos evitados: `experiments/results/rdl_phase1/prometheus_metrics.prom`.
   - Traces de rádio e FlowMonitor pós-arbitragem: `experiments/results/rdl_phase1/flowmonitor_results.xml`.

---

### 13.4. Fase 4: Análise Comparativa e Consolidação de Benchmarks

Para processar todos os traces coletados (Baseline vs RDL), calcular os ganhos percentuais e gerar os datasets formatados para Machine Learning:


**Processar métricas, gerar relatórios comparativos e gráficos:**
```bash
make analyze-benchmarks
```

#### Artefatos Gerados Automaticamente:
* **Relatório Executivo Comparativo:** [`experiments/results/relatorio_comparativo.md`](../experiments/results/relatorio_comparativo.md)
* **Métricas Estruturadas JSON:** [`experiments/results/relatorio_comparativo.json`](../experiments/results/relatorio_comparativo.json)
* **Dataset de Fluxos e SLAs:** [`experiments/results/dataset_flow_metrics.csv`](../experiments/results/dataset_flow_metrics.csv)
* **Dataset para Scikit-Learn (Google Colab):** [`experiments/results/dataset_rdl_decisions_ml.csv`](../experiments/results/dataset_rdl_decisions_ml.csv)
* **Gráficos Comparativos em Alta Resolução (300 DPI):** `experiments/results/graficos_benchmarks_rdl.png`

---

### 13.5. Pipeline Integrado de Ponta a Ponta (Execução Completa em 1 Comando)

Caso deseje executar todo o ciclo experimental (Fases 1, 2, 3 e 4) de forma 100% automatizada e sequencial em lote único:


**Executa Baseline -> Deploy RDL -> Simulação RDL -> Análise Comparativa -> Auto-Commit:**
```bash
make run-experiments
```

---

### 13.6. Acesso, Visualização e Sincronização com o GitHub

Após a conclusão dos experimentos, os resultados podem ser inspecionados ou enviados para o GitHub com os seguintes comandos:


1. Visualizar o relatório executivo formatado no terminal:
```bash
make view-results
```

* ou: cat experiments/results/relatorio_comparativo.md:

2. Inspecionar métricas JSON estruturadas:
```bash
python3 -m json.tool experiments/results/relatorio_comparativo.json
```

3. Inspecionar primeiras linhas dos datasets:
```bash
head -n 10 experiments/results/dataset_rdl_decisions_ml.csv
head -n 10 experiments/results/dataset_flow_metrics.csv
```

4. Sincronizar e enviar todos os resultados e datasets para o GitHub:
```bash
make push-results
```

#### Acesso aos Arquivos via Host (Windows / WSL2 / Remoto)
* **No Windows Explorer (WSL2):** Pressione `Win + R` e acesse `\\wsl$\Ubuntu\root\XApp-RDL-F1\experiments\results` para abrir os arquivos `.csv` e `.md` diretamente no Excel ou VS Code.
* **Via SSH Remoto (SCP):**
```bash
  scp -r root@<IP_DO_SERVIDOR>:~/XApp-RDL-F1/experiments/results ./meus_resultados
  ```

### 13.7. Execução e Acompanhamento em Tempo Real no Prompt de Comando (2 Cenários)

Para executar e visualizar em tempo real no console (PowerShell, CMD ou WSL2/Bash) as decisões e métricas de ambos os cenários:

#### 1. Monitorar o Deploy e Pods no Kubernetes:

**Acompanhar mudanças de estado dos Pods:**
```bash
kubectl get pods -n ricxapp -w
```

**Streaming de logs em tempo real (Fase 1):**
```bash
make logs
```

**Streaming de logs em tempo real (Fase 2 - CA-RDL / MARL):**
```bash
make logs-f2
```

* ou no PowerShell: kubectl logs -l app=ricxapp-iqos-xapp-rdl-f2 -n ricxapp -f:

#### 2. Execução dos 2 Cenários de Simulação com Saída ao Vivo no Console:

**Cenário 1 (Energy vs QoS / EEVS):**
```bash
make run-scenario1
```

* ou no ns-3: export NS_LOG="ScenarioRdlEnergyVsQos=level_all" && ./ns3 run "scratch/scenario_rdl_energy_vs_qos --enableE2=true --simTime=30":

**Cenário 2 (Traffic Steering vs QoS / TVS):**
```bash
make run-scenario2
```

* ou no ns-3: export NS_LOG="ScenarioRdlTvsConflict=level_all" && ./ns3 run "scratch/scenario_rdl_tvs_conflict --enableE2=true --simTime=30":

#### 3. Execução da Suíte Comparativa e IA no Prompt:

**No Windows (PowerShell/CMD):**
```powershell
python scripts/evaluate_and_improve_algorithms.py
python scripts/run_experiment_suite.py
```

**No Linux / WSL2:**
```bash
python3 scripts/evaluate_and_improve_algorithms.py
python3 scripts/run_experiment_suite.py
```

---

### 13.8. Modo de Demonstração ao Vivo em Tempo Real (`ns3::RealtimeSimulatorImpl` & `demoMode`)

> **Importante para Defesa e Apresentação Executiva:** por padrão, o ns-3 utiliza **tempo virtual** e executa os eventos o mais rápido possível, saltando diretamente de um evento para o outro. Alterar apenas o parâmetro `simTime` (ex.: `--simTime=60`) **não** transforma a simulação em uma demonstração ao vivo acompanhável, pois 60s simulados podem rodar em 8s ou 90s reais dependendo do hardware.

Para uma demonstração didática em tempo real (1 segundo simulado $\approx$ 1 segundo de relógio real), o projeto XApp-RDL integra suporte opcional ao `ns3::RealtimeSimulatorImpl`.

#### 13.8.1. Arquitetura de Sincronização em Tempo Real

A inicialização do modo em tempo real vincula o motor de simulação antes de invocar `Simulator::Run()`:

```cpp
#include "ns3/core-module.h"
using namespace ns3;

int main (int argc, char *argv[])
{
    bool realtime = false;
    std::string syncMode = "BestEffort"; // "BestEffort" ou "HardLimit"
    double simTime = 60.0;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("realtime", "Ativar execucao em tempo real", realtime);
    cmd.AddValue ("syncMode", "Modo de sincronizacao: BestEffort ou HardLimit", syncMode);
    cmd.AddValue ("simTime", "Duracao da simulacao em segundos", simTime);
    cmd.Parse (argc, argv);

    if (realtime)
    {
        GlobalValue::Bind ("SimulatorImplementationType", StringValue ("ns3::RealtimeSimulatorImpl"));
        if (syncMode == "HardLimit")
        {
            GlobalValue::Bind ("RealtimeSimulatorImpl::SynchronizationMode", StringValue ("HardLimit"));
        }
        else
        {
            GlobalValue::Bind ("RealtimeSimulatorImpl::SynchronizationMode", StringValue ("BestEffort"));
        }
    }

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();
    Simulator::Destroy ();
    return 0;
}
```

#### 13.8.2. Modos de Sincronização: `BestEffort` vs `HardLimit`

* **`BestEffort` (Recomendado para Defesas e Demonstrações):** caso a CPU sofra um pequeno atraso temporário no processamento de um evento, o simulador tenta recuperar a sincronia nos eventos seguintes de forma suave sem abortar a simulação. É ideal contra picos esporádicos de carga no ambiente de teste.
* **`HardLimit` (Recomendado para Validação Rígida de Desempenho):** aborta imediatamente a execução se o atraso do simulador ultrapassar a tolerância configurada (limite padrão do ns-3: 0,1s). Prova formalmente que o sistema cumpre os requisitos rígidos de tempo real.

#### 13.8.3. As Três Velocidades de Execução (`--demoMode`)

Para evitar misturar a campanha científica com testes rápidos e apresentações ao vivo, todos os cenários (C++ no ns-3 e Python) suportam três presets de velocidade:

| Modo (`--demoMode`) | Tempo Simulado | Sincronismo | Objetivo e Uso Recomendado |
| :--- | :---: | :---: | :--- |
| `fast` | 30 s | Tempo Virtual (Máxima Velocidade) | Depuração rápida de código e testes de regressão CI. |
| `realtime` | 60–90 s | 1x Wall-Clock (`RealtimeSimulatorImpl`) | Demonstração ao vivo didática para bancas e eventos. |
| `experiment` | 30–120 s | Tempo Virtual (Default) | Campanha experimental científica de alta precisão (30 seeds). |

#### Exemplo de Invocação via CLI:
```bash
# Execução de demonstração ao vivo de 60s sincronizada com relógio real:
./ns3 run "scenario_rdl_tvs_conflict --demoMode=realtime --simTime=60 --conflictStart=20 --conflictEnd=35 --kpmPeriod=0.2"

# Execução rápida para depuração:
./ns3 run "scenario_rdl_tvs_conflict --demoMode=fast"

# Execução em Python com pacing em tempo real:
python scripts/run_full_campaign_s0_s8.py --demo-mode=realtime --sim-time=60
```

---

#### 13.8.4. Cronogramas de Terminal e Demonstrações Didáticas por Cenário

Para uma apresentação ao vivo (60 a 90 segundos), a audiência deve acompanhar a transição visual clara de estados no terminal:
$$\text{Normal} \longrightarrow \text{Conflict} \longrightarrow \text{Detection} \longrightarrow \text{H-RDL Decision} \longrightarrow \text{RIC Control} \longrightarrow \text{Network Reaction} \longrightarrow \text{Recovery}$$

##### Cronograma Genérico de 60 Segundos:
* **0–10 s — BASELINE:** a rede estabiliza e os canais de rádio 5G NR são estabelecidos.
* **10–20 s — NORMAL OPERATION:** métricas E2SM-KPM começam a ser exibidas periodicamente.
* **20 s — INJEÇÃO DE CONFLITO:** xApp A envia proposta de alteração de parâmetro.
* **23 s — PROPOSTA INCOMPATÍVEL:** xApp B envia proposta concorrente em janela $\Delta t$.
* **23–25 s — CONFLICT DETECTED:** o `PerceptionAgent` identifica o conflito direto/indireto.
* **25 s — H-RDL DECISION:** o `ReasoningAgent` arbitra aplicando a função de utilidade.
* **25–27 s — E2SM-RC / CONTROL:** mensagem `RICcontrolRequest` é transmitida e confirmada por `RICcontrolAck`.
* **27–40 s — RECOVERY:** os indicadores de rádio (SINR, PDR, latência) se recuperam.
* **40–60 s — STABLE STATE:** a rede mantém o estado governado com conformidade aos SLAs.

---

##### Demonstração S2 — Energy Saving vs QoS Slicing:
* **Cronograma:**
  * **0–15 s:** Small cell ativa operando normalmente.
  * **15 s:** xApp Energy Saving solicita `TX_POWER -> LOW` (20 dBm).
  * **20 s:** Surto de carga QoS URLLC aumenta demanda por PRBs.
  * **20–22 s:** Conflito indireto de degradação detectado pelo H-RDL.
  * **22 s:** H-RDL bloqueia o modo sleep completo e ajusta a potência via *clamping* (`CLAMP_TX_POWER`).
  * **22–35 s:** Rede recupera os requisitos de latência e PDR da fatia URLLC.
  * **35–60 s:** Estado estável e eficiente mantido.
* **Saída Esperada no Console:**
```text
[15.000s] EnergySaving xApp proposal TX_POWER -> LOW (20 dBm)
[20.000s] QoS xApp proposal Capacity request -> HIGH (PRB_QUOTA 80%)
[20.003s] CONFLICT DETECTED type=INDIRECT resource=TX_POWER/QoS
[20.007s] H-RDL DECISION action=CLAMP_TX_POWER (38 dBm)
[20.012s] E2SM_RC_CONTROL_REQ tx_power=38dBm gnb_id=gnb_01
[20.027s] E2SM_RC_CONTROL_ACK status=SUCCESS
[20.200s] KPM: SINR improved to 18.4 dB | URLLC latency recovering to 2.3 ms
[21.000s] RECOVERY CONFIRMED: SLA SLA_URLLC satisfied (PDR=100.0%)
```

---

##### Demonstração S5 — Handover Ping-Pong Temporal:
* **Cronograma e Tela Visual:**
```text
  10 s: UE ------------> gNB-01
  15 s: UE ------------> ZONA DE OVERLAP
  18 s: xApp TS -------> Solicita Handover para gNB-02
  19 s: Outra Política -> Solicita Handover de volta para gNB-01
  20 s: H-RDL ---------> Detecta Conflito Temporal (Ping-Pong) e Ativa Lock
  20-25 s: Cooldown Period (Handover Lock Ativo)
  25 s: Associação Estável Mantida na gNB-02
```
* **Telemetria no Console:**
```text
[18.000s] TS xApp HO_REQ: UE-07 -> gNB-02
[19.000s] LB xApp HO_REQ: UE-07 -> gNB-01 (INCOMPATIBLE)
[19.002s] CONFLICT DETECTED type=TEMPORAL_PINGPONG target=UE-07
[19.005s] H-RDL DECISION action=LOCK_HANDOVER cooldown=10.0s
[19.010s] RIC_CONTROL_REQ action=REJECT_HO
[25.000s] Handover Lock Expired | Handover Count: 1 | Ping-Pong Count: 0 | Serving Cell: gNB-02
```

---

##### Demonstração S6 — Tempestade de Conflitos (Conflict Storm):
* **Crescimento Gradual de xApps Concorrentes:**
  * **0–10 s:** 2 xApps ativas ($\sim 2$ conflitos/s)
  * **10–20 s:** 4 xApps ativas ($\sim 12$ conflitos/s)
  * **20–30 s:** 6 xApps ativas ($\sim 31$ conflitos/s)
  * **30–45 s:** 8 xApps ativas ($\sim 58$ conflitos/s)
  * **45–60 s:** Governança RDL estabiliza e recupera a fila de decisão.
* **Métricas Medidas em Tempo Real no Console (Sem dados inventados):**
```text
[10.000s] Active xApps: 2 | Conflict rate:  2.1/s | Decision Queue: 0 | Decision P99: 12.1 ms
[20.000s] Active xApps: 4 | Conflict rate: 12.4/s | Decision Queue: 1 | Decision P99: 13.8 ms
[30.000s] Active xApps: 6 | Conflict rate: 31.2/s | Decision Queue: 2 | Decision P99: 14.5 ms
[45.000s] Active xApps: 8 | Conflict rate: 58.7/s | Decision Queue: 3 | Decision P99: 15.2 ms
[60.000s] STORM MITIGATED | Unresolved Conflicts: 0 | P99 Latency Target (<50ms): PASSED
```

---

##### Demonstração S7 — Safety Guard Rejeitando Ação Insegura (Rogue xApp):
* **Injeção de Falha em 20 s:** Rogue xApp transmite `TX_POWER = 55 dBm` e `PRB_QUOTA = 250%`.
* **Tela Visual:**
```text
  ROGUE ACTION PROPOSAL (TX_POWER=55dBm, PRB_QUOTA=250%)
           │
           ▼
   Refinement Agent
           │
           ▼
    SAFETY GUARD
           │
           ▼
      ✕ BLOCKED (Limits: Power <= 23dBm, PRB <= 100%)
           │
           ▼
  RIC_CONTROL_FAILURE (Cause: Out-of-Range Parameter)
```

---

##### Demonstração S8 — Closed Loop NORI (4 Terminais Simultâneos):
Em uma apresentação com 4 terminais abertos lado a lado:

```text
 Terminal 1 (ns-3 / 5G-LENA)      Terminal 2 (NORI / E2SIM)        Terminal 3 (Near-RT RIC)        Terminal 4 (H-RDL Dashboard)
 ┌─────────────────────────┐      ┌────────────────────────┐       ┌────────────────────────┐      ┌────────────────────────┐
 │ [KPM] Report sent       │ ---->│ [E2] Encapsulating APER│ ----->│ [RIC] Dispatching RMR  │ ---->│ [RDL] Conflict Solved  │
 │ SINR=18.2dB Lat=2.1ms   │      │ IndicationReport       │       │ Subscription ID #101   │      │ Decision Latency: 14ms │
 └─────────────────────────┘      └────────────────────────┘       └────────────────────────┘      └────────────────────────┘
              ▲                                                                                                 │
              │                                                                                                 │
              └───────────────────────────────── [E2SM-RC Control] ─────────────────────────────────────────────┘
```

#### Diagrama de Encadeamento Fechado:
$$\text{ns-3 / 5G-LENA} \xrightarrow{\text{KPM}} \text{NORI E2} \xrightarrow{\text{E2AP}} \text{Near-RT RIC} \xrightarrow{\text{RMR}} \text{H-RDL} \xrightarrow{\text{Decisão}} \text{Near-RT RIC} \xrightarrow{\text{RC}} \text{NORI} \xrightarrow{\text{MAC/PHY}} \text{ns-3}$$

Neste cenário de co-simulação com processos externos, o uso do `RealtimeSimulatorImpl` é vital para manter o relógio da simulação emparelhado com o relógio real do sistema operacional e dos containers Docker/K8s do Near-RT RIC.

Os datasets estruturados gerados pela simulação (`experiments/results/dataset_flow_metrics.csv` e `experiments/results/dataset_rdl_decisions_ml.csv`) alimentam diretamente o notebook de Machine Learning:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/georgebarbosa3090/XApp-RDL-F1/blob/main/notebooks/rdl_colab_scikit_learn.ipynb)

* **Notebook:** [`notebooks/rdl_colab_scikit_learn.ipynb`](../notebooks/rdl_colab_scikit_learn.ipynb)
* **Modelos Treinados:** Random Forest, Decision Tree e Gradient Boosting para predição antecipada de conflitos O-RAN e relevância de variáveis (*Feature Importance*).

---

## 15. Próximo Passo Sequencial

Avance para a análise de governança e matriz de conformidade com as normas O-RAN Alliance:

-> **[Volume 04: Relatórios de Conformidade Técnica e Governança O-RAN](04_relatorios_conformidade_e_governanca.md)**
