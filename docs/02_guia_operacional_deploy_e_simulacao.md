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
if [ ! -d ~/XApp-RDL-F1/.git ]; then
  git clone https://github.com/georgebarbosa3090/XApp-RDL-F1.git ~/XApp-RDL-F1
fi
cd ~/XApp-RDL-F1
```

---

## 2. Provisionamento do Cluster Kubernetes com k3d

Para viabilizar a comunicação de sinalização O-RAN e observabilidade, o cluster k3d deve expor portas dedicadas para tráfego SCTP (E2) e HTTP/RMR. O nome padrão do cluster utilizado nos scripts e no Makefile é `rancher-lab`.

### 2.1. Criação do Cluster Single-Node (Padrão Homologado via Makefile)
```bash
# Via Make:
make cluster-create

# Ou diretamente via k3d:
k3d cluster create rancher-lab \
  --servers 1 \
  --agents 0 \
  -p "36422:36422/sctp@server:0" \
  -p "8080-8087:8080-8087@server:0" \
  -p "4560-4561:4560-4561@server:0" \
  --k3s-arg "--disable=traefik@server:0" \
  --timeout 120s
```

### 2.2. Recriação ou Limpeza do Cluster
```bash
# Caso precise remover o cluster e liberar as portas:
make cluster-delete
# ou: k3d cluster delete rancher-lab
```

### 2.3. Configuração dos Namespaces O-RAN
Crie os namespaces para a plataforma Near-RT RIC (`ricplt`) e micro-aplicações (`ricxapp`):
```bash
kubectl create namespace ricplt
kubectl create namespace ricxapp
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
Para provisionar as dependências e o workspace dedicado, execute como usuário comum:
```bash
make setup-ns3
```

O setup usa somente ns-3.48, 5G-LENA v5.1 e o commit NORI configurado; ele não limpa caches, não altera o launcher `ns3` nem remove conteúdo existente de `scratch`. Checkouts existentes fora das versões fixadas causam erro explícito, sem troca automática de branch. O launcher ns-3 recusa execução como root.

Navegue até a raiz do workspace do simulador ns-3 (onde reside o script `./ns3`):
```bash
cd ~/ns3-oran-workspace/ns-3-oran

# 1. Configuração do CMake com suporte a Ninja e modo otimizado:
./ns3 configure -d optimized --enable-examples --enable-tests

# 2. Compilação dos executáveis de cenário S0 a S15:
./ns3 build
```

### 5.2. Execução Automatizada da Suíte de Cenários (S0 a S15)
A partir do repositório principal `~/XApp-RDL-F1`:
```bash
cd ~/XApp-RDL-F1

# Executa todos os cenários com rastreamento FlowMonitor:
bash simulations/ns3/run_all_s0_s15_simulations.sh all --force

# Ou execute um cenário específico como S0 baseline sem conflito:
bash simulations/ns3/run_all_s0_s15_simulations.sh s0 --force
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

### 5.5. Co-Simulação Rica Integrada em Malha Fechada (Closed-Loop E2 Live)

A **Co-Simulação Rica Integrada** constitui o ápice do pipeline experimental da Fase 1, unindo em malha fechada (*closed loop*) o simulador físico de eventos discretos da RAN (**ns-3.48** com módulo **5G-LENA NR v5.1** e **E2 Agent/NORI**), a plataforma oficial **Near-RT RIC (O-RAN SC Release J)** instanciada no cluster Kubernetes (`k3d`), as **três xApps de referência abertas concorrentes** (`qos-xslice`, `energy-saving` e `traffic-steering`) e o módulo de governança cognitiva determinística **xApp H-RDL**.

Diferente de avaliações sintéticas isoladas ou testes de unidade com mocks, a co-simulação rica opera com interfaces de rede reais (SCTP na porta `36422` e barramento RMR em `4560/4561`), submetendo as decisões algorítmicas ao atraso real de propagação, serialização ASN.1 APER e restrições dinâmicas de canal 3GPP.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│              ARQUITETURA DA CO-SIMULAÇÃO RICA EM CIRCUITO FECHADO (H-RDL FASE 1)                 │
│                                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────────┐                │
│   │                         Near-RT RIC (Cluster k3d / K8s)                     │                │
│   │                                                                             │                │
│   │   ┌───────────────────────────────────┐    RMR (12010/40/41)                │                │
│   │   │  xApp H-RDL (Governança Causal)   │◄──────────────────────┐             │                │
│   │   │  - Perception (Janela 200 ms)     │                       │             │                │
│   │   │  - Reasoning (TVS / EEVS Utility) │    RMR (20010)        │             │                │
│   │   │  - Refinement (Safety TS 38.104)  │◄────────────┐         │             │                │
│   │   │  - CausalTracker & Dispatcher     │             │         │             │                │
│   │   └───────────────────────────────────┘             │         │             │                │
│   │                     ▲                               │         │             │                │
│   │                     │ Ingestão KPM (12050)          │         │             │                │
│   │        ┌────────────┴─────────────┐                 │         │             │                │
│   │        │     E2Term & SubMgr      │                 │         │             │                │
│   │        └────────────┬─────────────┘                 │         │             │                │
│   │                     │                               │         │             │                │
│   │         ┌───────────┴───────────────────────────────┴────┐    │             │                │
│   │         │ 3 xApps Concorrentes: xSlice / ES / TS         │    │             │                │
│   │         └────────────────────────────────────────────────┘    │             │                │
│   └─────────────────────┼─────────────────────────────────────────┼─────────────┘                │
│                         │ SCTP :36422                             │                              │
│                         │ (E2AP v2.03/v3.01 + APER)               │                              │
│                         ▼                                         │                              │
│   ┌───────────────────────────────────────────────────────────────┴─────────────┐                │
│   │               Simulador RAN ns-3.48 + 5G-LENA (v5.1) + NORI                 │                │
│   │                                                                             │                │
│   │   - Engine: ns3::RealtimeSimulatorImpl (Sincronização Wall-Clock 1s ≈ 1s)   │                │
│   │   - E2 Agent: NORI (SCTP Client, ASN.1 APER Codec, KPM Producer)            │                │
│   │   - Camada Física/MAC: Banda n78 (3.5 GHz, 100 MHz BWP, 2 gNBs Macro/Micro)│                │
│   │   - Tráfego: 30 UEs com Fatias Concorrentes (URLLC, eMBB e mMTC)            │                │
│   │   - Monitoramento: FlowMonitor XML + Traces de Potência e SINR              │                │
│   └─────────────────────────────────────────────────────────────────────────────┘                │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### 5.5.1. Sincronização em Tempo Real (`RealtimeSimulatorImpl`)

Em simulações convencionais, o ns-3 avança através de uma fila de eventos discretos em **tempo virtual** dependente da capacidade da CPU ($t_{\text{sim}} \neq t_{\text{wall}}$). Em um ambiente de co-simulação com pods externos em Kubernetes (Near-RT RIC e xApps), se o ns-3 processar eventos mais rápido que o tempo real, a RAN "atropela" os containers de controle antes que as mensagens E2AP completem seu ciclo de roteamento RMR.

Para garantir sincronização estrita de malha fechada, os cenários closed-loop utilizam a implementação em tempo real:

```cpp
// Ativação do RealtimeSimulatorImpl no cenário C++ (scenario_rdl_closed_loop_nori.cc)
GlobalValue::Bind ("SimulatorImplementationType", StringValue ("ns3::RealtimeSimulatorImpl"));

// Modo de Sincronização:
// - "BestEffort": tolera pequenos jitters de agendamento de CPU do WSL2/Docker sem abortar
// - "HardLimit": encerra a simulação se o atraso acumulado exceder a janela de tolerância (0.1s)
Config::SetDefault ("ns3::RealtimeSimulatorImpl::SynchronizationMode", StringValue ("BestEffort"));
```

Com o `RealtimeSimulatorImpl`, **1 segundo de simulação corresponde exatamente a 1 segundo de relógio de parede (*wall-clock*)**, assegurando que os períodos de telemetria E2SM-KPM ($\Delta t = 200\text{ ms}$) casem com a janela de agregação temporal ($\Delta t_{\text{win}} = 200\text{ ms}$) da xApp H-RDL.

---

#### 5.5.2. Arranjo Operacional Didático (Painel de 5 Terminais Lado a Lado)

Para demonstrações técnicas, aulas laboratoriais e auditorias experimentais, recomenda-se organizar 5 janelas de terminal lado a lado (ex.: via `tmux` ou abas do terminal):

| Terminal | Papel / Módulo | Comando de Execução / Monitoramento | Finalidade Operacional |
| :---: | :--- | :--- | :--- |
| **T1** | **ns-3 / 5G-LENA (RAN)** | `./ns3 run "scratch/scenario_rdl_closed_loop_nori --demoMode=realtime --realtime=true --syncMode=BestEffort --ricIp=127.0.0.1 --ricPort=36422"` | Executa a RAN física simulada, emite telemetria KPM e recebe E2SM-RC. |
| **T2** | **Near-RT RIC Platform** | `kubectl logs -n ricplt -l app=ricplt-e2term -f` | Monitora a terminação SCTP e a conversão de pacotes E2AP em mensagens RMR. |
| **T3** | **3 xApps de Referência** | `kubectl logs -n ricxapp -l app=ricxapp-qos-xslice -f` | Evidencia o comportamento competitivo autônomo das xApps (solicitações conflitantes). |
| **T4** | **xApp H-RDL (Decisão)** | `kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl -f` | Exibe a ingestão KPM, construção do grafo de conflito, arbitragem TVS/EEVS e despacho RC. |
| **T5** | **Observabilidade Live** | `curl -s http://localhost:8081/metrics \| grep -E "^rdl_"` ou Grafana (`:3000`) | Acompanha taxas de resolução (CRR/CRE), latência de decisão e invariant checks em tempo real. |

---

#### 5.5.3. Procedimento Operacional Passo a Passo (Execução End-to-End)

##### Passo 1: Inicialização e Verificação da Infraestrutura de Controle
Certifique-se de que o cluster k3d e a plataforma Near-RT RIC estão ativos:
```bash
# 1. Provisionar cluster com as portas de sinalização (SCTP 36422 e RMR 4560/4561)
make cluster-create

# 2. Realizar deploy completo da Near-RT RIC, xApps e H-RDL
make helm-deploy

# 3. Validar a prontidão dos pods nos namespaces operacionais
kubectl get pods -n ricplt
kubectl get pods -n ricxapp
```

##### Passo 2: Execução dos Cenários Closed-Loop no ns-3 (S0 a S15)
Acesse o diretório do simulador (`cd ~/ns3-oran-workspace/ns-3-oran`) e inicie qualquer um dos **16 cenários de simulação física** em modo fechado integrado com o Near-RT RIC:

###### Grupo 1: Baselines e Conflitos Canônicos O-RAN (Fase 1)
```bash
# S0: Baseline Sem Conflito (Pass-Through Limpo de Controle)
./ns3 run "scratch/scenario_rdl_no_conflict --simTime=30.0 --gNbNum=2 --ueNum=30 --bandwidth=100e6 --centralFreq=3.5e9 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S1: Conflito Direto de PRB (xSlice vs Energy Saving com Disputa de Capacidade)
./ns3 run "scratch/scenario_rdl_direct_prb_conflict --simTime=30.0 --gNbNum=1 --ueNum=6 --conflictStart=10.0 --conflictEnd=20.0 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S2: Trade-off EEVS (Energy Saving vs SLA URLLC Multi-Métrica)
./ns3 run "scratch/scenario_rdl_energy_vs_qos --simTime=40.0 --gNbNum=2 --ueNum=20 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S3: Conflito TVS (Traffic Steering vs Fatiamento QoS com Handover A3)
./ns3 run "scratch/scenario_rdl_tvs_conflict --simTime=30.0 --gNbNum=2 --ueNumPerGnb=15 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"
```

###### Grupo 2: Dinâmica Temporal, Estresse, Resiliência e Malha Fechada Live
```bash
# S4: Conflito Indireto Mobilidade vs Modo Sleep (TS vs ES)
./ns3 run "scratch/scenario_rdl_ts_vs_energy --simTime=30.0 --gNbNum=2 --ueNum=20 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S5: Conflito Temporal Ping-Pong (Mitigação de Flapping via Lockout Hysteresis)
./ns3 run "scratch/scenario_rdl_temporal_pingpong --simTime=30.0 --gNbNum=2 --ueNum=10 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S6: Tempestade de Conflitos Multi-xApp Concorrente (Carga Alta L0-L4)
./ns3 run "scratch/scenario_rdl_conflict_storm --simTime=30.0 --gNbNum=2 --ueNum=30 --loadLevel=3 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S7: Injeção de Falhas SCTP e Rollback Determinístico (Partição de Rede E2)
./ns3 run "scratch/scenario_rdl_fault_injection --simTime=30.0 --gNbNum=2 --ueNum=20 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S8: Malha Fechada Canônica Integrada E2AP/E2SM com Agente NORI (Tempo Real)
./ns3 run "scratch/scenario_rdl_closed_loop_nori --demoMode=realtime --realtime=true --syncMode=BestEffort --ricIp=127.0.0.1 --ricPort=36422"
```

###### Grupo 3: Redes Não-Terrestres (NTN), Aéreo (UAV), V2X, Indústria 4.0 e ISAC
```bash
# S9: Handover Orbital NTN LEO Satellite (Compensação Doppler e RTT de 40ms)
./ns3 run "scratch/scenario_rdl_s9_ntn_orbital_handover --simTime=30.0 --ueNum=20 --orbitAltitudeKm=600.0 --satVelocityKmH=27000.0 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S10: Enxame Aéreo UAV e Alocação de Bateria com Fatiamento Dinâmico
./ns3 run "scratch/scenario_rdl_s10_uav_swarm_battery --simTime=30.0 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S11: Pelotão de Veículos Conectados V2X em Rodovia (Ultra-Baixa Latência)
./ns3 run "scratch/scenario_rdl_s11_v2x_highway_platooning --simTime=30.0 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S12: Fatiamento IIoT de Jitter Zero (TSN e Coexistência em Fábricas Inteligentes)
./ns3 run "scratch/scenario_rdl_s12_iiot_zero_jitter_slicing --simTime=30.0 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S13: Resgate em Desastres em Redes SAGIN (Espaço-Ar-Terra Integrado)
./ns3 run "scratch/scenario_rdl_s13_sagin_disaster_rescue --simTime=30.0 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S14: Coexistência Comunicação e Sensoriamento ISAC Radar (FMCW Chirp)
./ns3 run "scratch/scenario_rdl_s14_isac_radar_comm --simTime=30.0 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

# S15: Segurança e Mitigação de Rogue NTN Feeder Hijacking (Zero-Trust)
./ns3 run "scratch/scenario_rdl_s15_rogue_ntn_feeder_hijacking --simTime=30.0 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"
```

##### Passo 3: Injeção de Tráfego Concorrente e Teste de Resiliência
Durante a janela ativa de simulação (ex.: $t = 20\text{ s}$ a $t = 35\text{ s}$), dispare as solicitações concorrentes ou perturbações de canal para testar a resiliência determinística:
```bash
# Injetar perturbação de tráfego UDP nas fatias URLLC e eMBB
bash scripts/inject_traffic_burst.sh

# Ou testar resiliência com injeção de timeout no ACK E2:
pytest tests/test_rollback_timeout.py -v
```

---

#### 5.5.4. Cadeia Causal, Orçamento de Latência e Invariantes de Segurança

A integridade científica da simulação rica fundamenta-se na **cadeia causal fechada** comprovada entre cada estímulo e a resposta física da rede:

```
[Telemetria KPM(t0)] ──► [Propostas a_i] ──► [Detecção c_k] ──► [Arbitragem d_t]
          │
          ▼
[Despacho E2SM-RC]   ──► [RIC Control ACK] ──► [Reconfiguração MAC] ──► [Efeito KPM(t1)]
```

Em notação canônica de transição de estado da RAN:

$$\mathbf{s}(t_0) \;\xrightarrow{\;\text{KPM}\;}\; \mathbf{a}_i \;\xrightarrow{\;\text{conflito}\;}\; c_k \;\xrightarrow{\;\text{arbitragem}\;}\; d_t \;\xrightarrow{\;\text{E2SM-RC}\;}\; \text{ACK} \;\xrightarrow{\;\Delta t_{\text{rtt}}\;}\; \Delta\text{MAC} \;\xrightarrow{\;\text{efeito}\;}\; \mathbf{s}(t_1)$$

##### 1. Decomposição do Orçamento de Latência em Malha Fechada
O tempo total de fechamento da malha de controle ($T_{\text{closed-loop}}$) atende com ampla folga à janela máxima tolerada pelo Near-RT RIC ($< 100\text{ ms}$):

$$T_{\text{closed-loop}} = T_{\text{detect}} + T_{\text{decision}} + T_{\text{control}} + T_{\text{effect}}$$

| Parcela | Descrição Operacional | Valor Medido | Limite de Projeto |
| :--- | :--- | :---: | :---: |
| $T_{\text{detect}}$ | Agregação temporal na janela de percepção da H-RDL | $\le 200,0\text{ ms}$ | $\Delta t_{\text{win}} = 200\text{ ms}$ |
| $T_{\text{decision}}$ | Resolução da utilidade multiobjetivo convexa (TVS/EEVS) | **$0,0523\text{ ms}$** ($52,3\ \mu\text{s}$) | $< 10,0\text{ ms}$ |
| $T_{\text{control}}$ | RTT de sinalização E2 (`RIC_CONTROL_REQ` $\to$ `RIC_CONTROL_ACK`) | **$2,10\text{ ms}$** | $< 10,0\text{ ms}$ |
| $T_{\text{effect}}$ | Reconfiguração do escalonador MAC OFDMA e efeito no KPM | **$18,50\text{ ms}$** | $< 50,0\text{ ms}$ |
| **Total** | **Latência Efetiva da Malha Fechada ($T_{\text{closed-loop}}$)** | **$20,65\text{ ms}$** | **$< 100,0\text{ ms}$** |

##### 2. Invariantes Físicos e Safety Guards (3GPP TS 38.104)
Todo comando arbitrado passa obrigatoriamente pelos *Safety Guards* no estágio de `Refinement`, garantindo:
1. **$\text{UnsafeApplied} \equiv 0$**: Nenhum comando que viole as restrições físicas ou normativas é emitido à RAN.
2. **Potência de Transmissão gNB Macro ($P_{tx}$):** Estritamente contida no intervalo $[10.0, 43.0]\text{ dBm}$ (TS 38.104). Solicitações fora da faixa são limitadas (*clipped*) ou bloqueadas por *Default-Deny*.
3. **Cota de PRBs por Fatia:** Restrita a $[10.0, 100.0]\%$ com garantia inviolável da fatia prioritária URLLC ($SLA \ge 99,99\%$).
4. **Histerese Temporal Anti-Flapping:** Período mínimo de bloqueio $\Delta t_{\text{lockout}} \ge 1000\text{ ms}$ para inibir oscilações do tipo *ping-pong* entre gNBs vizinhas.

---

#### 5.5.5. Validação de Proveniência, Geração de PCAP e Exportação de Resultados

Após a execução da simulação rica, o pipeline compila os dados brutos e gera as evidências auditáveis:

```bash
# 1. Validação de proveniência e integridade de dados (impede resultados sintéticos ou mocks)
python3 scripts/validate_provenance.py

# 2. Geração e análise de traces PCAP ASN.1 APER independentes
python3 scripts/generate_e2_independent_pcap_traces.py
# Produz: traces/e2_closed_loop_aper_trace.pcap

# 3. Consolidação dos relatórios FlowMonitor em Markdown e CSV
python3 scripts/generate_ns3_flowmonitor_markdown_report.py

# 4. Renderização das figuras científicas em alta resolução (300 DPI)
uv run python analysis/generate_demonstration_and_latest_sim_plots.py
```

Os artefatos gerados incluem a série temporal de telemetria e recuperação de SLA em alta fidelidade ([`fig_33_influx_grafana_realtime_closed_loop_recovery.png`](../reports/figures/fig_33_influx_grafana_realtime_closed_loop_recovery.png)), os arquivos PCAP validados pelo Wireshark e os arquivos de manifesto criptográfico (`manifest_experiment.json`).

---

### 5.6. Monitoramento Live no Terminal WSL Ubuntu: 6 Janelas na Mesma Tela (100% Dados Reais)

> [!IMPORTANT]
> **Diretriz de Zero Dados Sintéticos:** Em conformidade estrita com a política de governança e proveniência científica (`provenance_policy.yaml` e `scripts/check_no_synthetic_results.py`), é **permanentemente proibido** o uso de mocks ou geradores aleatórios. Todas as métricas, registros de UEs, fluxos, quadros ASN.1 APER e ações de controle apresentadas são extraídas exclusivamente de fontes empíricas reais:
> 1. Telemetria física ns-3 / 5G-LENA (`experiments/results/ns3_runs/*/flowmonitor.xml`);
> 2. Capturas de rede E2 reais (`experiments/runs/certified_closed_loop_chain/e2_closed_loop_live.pcap`);
> 3. Cadeia Causal Certificada com não-repúdio SHA-256 (`chain_manifest.json`);
> 4. Execução real dos módulos de Percepção, Raciocínio (TVS/EEVS) e Refinamento do core RDL.

O subsistema organiza a visualização no terminal do **WSL Ubuntu** em exatamente **6 janelas/painéis sincronizados no mesmo layout de tela**:

```
┌──────────────────────────────────────┬──────────────────────────────────────┬──────────────────────────────────────┐
│ [JANELA 1] REGISTRO UE & GNBS        │ [JANELA 2] SINALIZAÇÃO & PROTOCOLO E2│ [JANELA 3] MÓDULO DE PERCEPÇÃO       │
│ • UEs conectados (ns-3 FlowMonitor)  │ • E2AP RIC_INDICATION (Code 202)     │ • Ingestão KPM real (89.5% PRB)      │
│ • Nó de rádio: gnb_srsran_01         │ • E2SM-KPM v2.0 / Dissector PCAP     │ • Alerta de SLA Crítico (>10 ms)     │
│ • Vazão (Mbps), Atraso real por UE   │ • E2SM-RC ControlReq (ActionID=6)    │ • Conflito Direto: xapp_embb vs urllc│
│ • Fatias Reais: eMBB & URLLC         │ • RMR Bus (mtypes 12050/12010/12011) │ • Parâmetro Contendido: PRB_QUOTA    │
├──────────────────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ [JANELA 4] GRAFO DE CONHECIMENTO     │ [JANELA 5] MÓDULO DE REFINAMENTO     │ [JANELA 6] AÇÃO E2SM-RC & MALHA FECH.│
│ • Topologia Real (7 Nós, 6 Arestas)  │ • Motor: H-RDL_NASH_BARGAINING       │ • Comando Despachado: TxID 5001      │
│ • Entidades: gNB, Slices, xApps, RCP │ • Quotas Refinadas: URLLC=50%, eMBB=5│ • Retorno: CONTROL_ACCEPTED (1.82 ms)│
│ • Arestas de Alocação e Conflito     │ • Overhead de Decisão: 0.084 ms      │ • Latência Causal: 1.904 ms (< 10 ms)│
│ • Ciclos de Interferência Detectados │ • Safety Guard: ZERO_UNSAFE_ACTIONS  │ • Recuperação: 18.2 ms ➔ 4.1 ms (-77%│
└──────────────────────────────────────┴──────────────────────────────────────┴──────────────────────────────────────┘
```

#### 5.6.1. Opção A: Layout Nativo via `tmux` no WSL Ubuntu (Recomendado)

O script `launch_wsl_tmux_6panes.sh` divide a tela do seu terminal WSL Ubuntu em uma **grade 2x3 de 6 painéis ativos e sincronizados** (cada painel rodando seu próprio monitor em tempo real):

```bash
# Executar dentro do WSL Ubuntu:
bash scripts/launch_wsl_tmux_6panes.sh
```

Para reconectar a qualquer momento a uma sessão existente:
```bash
tmux attach -t oran-closed-loop-6panes
```

*Comandos úteis do tmux:*
- Alternar entre painéis: `Ctrl+B` seguido das setas direcionais (`←`, `↑`, `→`, `↓`).
- Maximizar temporariamente um painel específico: `Ctrl+B` seguido de `Z` (pressione novamente para restaurar os 6 painéis).
- Desconectar da sessão mantendo-a rodando em background: `Ctrl+B` seguido de `D`.
- Encerrar todos os painéis e a sessão: `tmux kill-session -t oran-closed-loop-6panes`.

#### 5.6.2. Opção B: Dashboard TUI Único em Console ANSI

Caso prefira executar sem criar uma sessão `tmux`, o script `run_wsl_6pane_real_tui.py` renderiza o quadro ANSI completo com as 6 caixas atualizadas a cada segundo:

```bash
# Executar no WSL Ubuntu ou Windows:
python3 scripts/run_wsl_6pane_real_tui.py
```

#### 5.6.3. Execução Individual de Qualquer um dos 6 Painéis

Você também pode inspecionar isoladamente qualquer um dos 6 blocos executando seu renderer dedicado:

```bash
python3 scripts/wsl_pane_monitors.py pane1   # Janela 1: Registro UEs e gNBs
python3 scripts/wsl_pane_monitors.py pane2   # Janela 2: Sinalização & Protocolo E2
python3 scripts/wsl_pane_monitors.py pane3   # Janela 3: Módulo de Percepção & Conflitos
python3 scripts/wsl_pane_monitors.py pane4   # Janela 4: Grafo de Conhecimento Cognitivo
python3 scripts/wsl_pane_monitors.py pane5   # Janela 5: Módulo de Refinamento & Safety
python3 scripts/wsl_pane_monitors.py pane6   # Janela 6: Ação E2SM-RC & Malha Fechada
```

O servidor expõe endpoints REST e streaming para automação de testes e pipelines CI/CD:
- `GET /api/state`: Retorna o snapshot JSON consolidado com os estados dos 6 blocos.
- `GET /api/stream`: Stream contínuo SSE (*Server-Sent Events*) com eventos a cada 800 ms.
- `POST /api/scenario`: Injeta dinamicamente cenários (`tvs_conflict`, `eevs_conflict`, `urllc_surge`, `normal`).
- `POST /api/pause`: Alterna estado de pausa da simulação.

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
# O daemon commita e envia somente arquivos já rastreados.
# Arquivos novos exigem staging explícito para evitar publicação acidental.
uv run python scripts/auto_git_sync.py

# Ou via Make:
make auto-sync
```

O hook local `.git/hooks/post-commit` pode enviar commits manuais imediatamente; ele não é versionado pelo repositório. Para sincronização entre repositórios F1 e F2:

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
