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
Para habilitar observabilidade gráfica do fluxo de microsserviços e gerenciamento visual do cluster:
```bash
# Instalação/inicialização do Rancher Manager no k3d (se já não estiver em execução)
docker run -d --restart=unless-stopped -p 8443:443 --privileged --name rancher-server rancher/rancher:latest

# Instalação do Kiali (após provisionamento Istio)
bash scripts/install_kiali.sh

# Abertura do Kiali Dashboard via port-forward
make kiali-dashboard
```

- **Rancher Manager:** Fica acessível diretamente no seu navegador em: **`https://localhost:8443`** (para administração do cluster `rancher-lab`, inspeção gráfica de pods, nós, logs e monitoramento de namespaces `ricplt` e `ricxapp`).
- **Kiali Dashboard (Istio Service Mesh):** Fica acessível em: **`http://localhost:20001/kiali`** (para visualização topológica da malha de serviços, rastreamento de tráfego e telemetria de comunicação entre as xApps).

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

### 5.2. Execução dos Cenários ns-3 (S0 a S15)

O ambiente oferece duas formas complementares de execução: manual direta dentro do workspace do ns-3 ou automatizada com rastreamento científico de métricas FlowMonitor.

#### 5.2.1. Opção A: Execução Manual Direta no Workspace do ns-3
Indicada para depuração pontual, testes interativos ou verificação direta de logs de simulação:

1. **Sincronização dos cenários para o diretório `scratch/`:**
   ```bash
   cp ~/XApp-RDL-F1/simulations/ns3/*.cc ~/ns3-oran-workspace/ns-3-oran/scratch/
   ```

2. **Navegação até o workspace do simulador:**
   ```bash
   cd ~/ns3-oran-workspace/ns-3-oran
   ```

3. **Execução dos cenários individuais (S0 a S15):**
   > **Atenção:** No comando `./ns3 run "..."`, passe o nome do alvo **sem o prefixo `scratch/`** (ex.: `scenario_rdl_no_conflict` em vez de `scratch/scenario_rdl_no_conflict`), e execute a partir do diretório raiz do simulador `~/ns3-oran-workspace/ns-3-oran`.

   **Grupo 1: Cenários 5G Sub-6 GHz (S0 a S8)**
   ```bash
   # S0: Baseline Sem Conflito (Pass-Through Limpo de Controle)
   ./ns3 run "scenario_rdl_no_conflict --simTime=30.0 --gNbNum=2 --ueNum=30 --bandwidth=100e6 --centralFreq=3.5e9 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S1: Conflito Direto de PRB (xSlice vs Energy Saving com Disputa de Capacidade)
   ./ns3 run "scenario_rdl_direct_prb_conflict --simTime=30.0 --gNbNum=1 --ueNum=6 --conflictStart=10.0 --conflictEnd=20.0 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S2: Trade-off EEVS (Energy Saving vs SLA URLLC Multi-Métrica)
   ./ns3 run "scenario_rdl_energy_vs_qos --simTime=40.0 --gNbNum=2 --ueNum=20 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S3: Conflito TVS (Traffic Steering vs Fatiamento QoS com Handover A3)
   ./ns3 run "scenario_rdl_tvs_conflict --simTime=30.0 --gNbNum=2 --ueNumPerGnb=15 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S4: Conflito Indireto Mobilidade vs Modo Sleep (TS vs ES)
   ./ns3 run "scenario_rdl_ts_vs_energy --simTime=30.0 --gNbNum=2 --ueNum=20 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S5: Conflito Temporal Ping-Pong (Mitigação de Flapping via Lockout Hysteresis)
   ./ns3 run "scenario_rdl_temporal_pingpong --simTime=30.0 --gNbNum=2 --ueNum=10 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S6: Tempestade de Conflitos Multi-xApp Concorrente (Carga Alta L0-L4)
   ./ns3 run "scenario_rdl_conflict_storm --simTime=30.0 --gNbNum=2 --ueNum=30 --loadLevel=3 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S7: Injeção de Falhas SCTP e Rollback Determinístico (Partição de Rede E2)
   ./ns3 run "scenario_rdl_fault_injection --simTime=30.0 --gNbNum=2 --ueNum=20 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S8: Malha Fechada Canônica Integrada E2AP/E2SM com Agente NORI (Tempo Real)
   ./ns3 run "scenario_rdl_closed_loop_nori --demoMode=realtime --realtime=true --syncMode=BestEffort --ricIp=127.0.0.1 --ricPort=36422"
   ```

   **Grupo 2: Cenários Avançados NTN, SAGIN, V2X, IIoT, ISAC e Zero-Trust 6G (S9 a S15)**
   ```bash
   # S9: Handover Orbital NTN LEO Satellite (Compensação Doppler e RTT de 40ms)
   ./ns3 run "scenario_rdl_s9_ntn_orbital_handover --simTime=30.0 --ueNum=20 --orbitAltitudeKm=600.0 --satVelocityKmH=27000.0 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S10: Enxame Aéreo UAV e Alocação de Bateria com Fatiamento Dinâmico
   ./ns3 run "scenario_rdl_s10_uav_swarm_battery --simTime=30.0 --uavNum=4 --ueNum=40 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S11: Pelotão de Veículos Conectados V2X em Rodovia (Ultra-Baixa Latência)
   ./ns3 run "scenario_rdl_s11_v2x_highway_platooning --simTime=30.0 --vehicleNum=10 --vehicleSpeedKmh=120 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S12: Fatiamento IIoT de Jitter Zero (TSN e Coexistência em Fábricas Inteligentes)
   ./ns3 run "scenario_rdl_s12_iiot_zero_jitter_slicing --simTime=30.0 --robotUeNum=20 --videoUeNum=30 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S13: Resgate em Desastres em Redes SAGIN (Espaço-Ar-Terra Integrado)
   ./ns3 run "scenario_rdl_s13_sagin_disaster_rescue --simTime=30.0 --rescueUeNum=20 --civilianUeNum=30 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S14: Coexistência Comunicação e Sensoriamento ISAC Radar (FMCW Chirp)
   ./ns3 run "scenario_rdl_s14_isac_radar_comm --simTime=30.0 --commUeNum=20 --radarTargetNum=5 --sensingRatio=0.3 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"

   # S15: Segurança e Mitigação de Rogue NTN Feeder Hijacking (Zero-Trust)
   ./ns3 run "scenario_rdl_s15_rogue_ntn_feeder_hijacking --simTime=30.0 --injectedPower=55.0 --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"
   ```

#### 5.2.2. Opção B: Execução Automatizada com FlowMonitor e Geração de Relatórios (Recomendado)
A automação oficial do repositório compila o cenário, executa a simulação com preservação de traces FlowMonitor, atualiza os relatórios consolidados em Markdown e regera as 25 figuras analíticas (300 DPI) e 16 tabelas CSV:

```bash
cd ~/XApp-RDL-F1

# Executa todos os cenários (S0 a S15) em lote:
bash simulations/ns3/run_all_s0_s15_simulations.sh all --force

# Ou execute grupos específicos:
bash simulations/ns3/run_all_s0_s15_simulations.sh 5g --force   # Cenários S0 a S8
bash simulations/ns3/run_all_s0_s15_simulations.sh 6g --force   # Cenários S9 a S15

# Ou execute cenários individuais:
bash simulations/ns3/run_all_s0_s15_simulations.sh s0 --force
bash simulations/ns3/run_all_s0_s15_simulations.sh s1 --force
bash simulations/ns3/run_all_s0_s15_simulations.sh s9 --force
```

#### 5.2.3. Diagnóstico e Resolução de Erros de Terminal (Zsh & ns-3)

Ao executar simulações ns-3 via terminal interativo (especialmente com **Zsh** no Ubuntu/WSL2), erros comuns de parsing de argumentos ou caracteres especiais podem ocorrer. Abaixo está o catálogo completo de diagnóstico e correção:

| Erro Observado no Terminal | Causa Raiz Técnica | Solução Definitiva |
| :--- | :--- | :--- |
| `zsh: command not found: #` | No Zsh interativo, o caractere `#` não inicia comentários por padrão. Colar comandos com `# Comentário` faz o Zsh tentar executar um executável chamado `#`. | Executar: `echo 'setopt INTERACTIVE_COMMENTS' >> ~/.zshrc && source ~/.zshrc` |
| `zsh: missing end of string` | Quebra de linha acidental ou aspas desbalanceadas durante colagem em bloco no buffer do emulador de terminal. | Colar comandos linha a linha ou executar via script bash (`run_all_s0_s15_simulations.sh`). |
| `zsh: number expected` / `zsh: unknown file attribute: ...` | O Zsh com `EXTENDED_GLOB` interpreta parênteses não aspeados em comentários (ex.: `(Pass-Through...)`, `(Mitigação...)`) como qualificadores glob de arquivos (ex.: `(i)`, `(a)`) ou expressões matemáticas. | Habilitar `setopt INTERACTIVE_COMMENTS` ou copiar apenas as linhas executáveis `./ns3 run "..."`. |
| `zsh: no such file or directory: ./ns3` | O comando foi executado fora de `~/ns3-oran-workspace/ns-3-oran` (onde reside o launcher Python `./ns3`). | Navegar até a raiz do ns-3: `cd ~/ns3-oran-workspace/ns-3-oran`. |
| `Invalid command-line argument: --ricIp=...` ou `--enableE2=...` | O analisador `ns3::CommandLine` valida estritamente os parâmetros passados. Se um cenário C++ não declarar `cmd.AddValue(...)`, a execução é abortada. | Todos os cenários S0–S15 em `simulations/ns3/*.cc` foram padronizados para aceitar `--enableE2`, `--ricIp`, `--ricPort` e `--simTime`. Basta sincronizar e recompilar: `cp ~/XApp-RDL-F1/simulations/ns3/*.cc scratch/ && ./ns3 build`. |
| Erro com prefixo `scratch/` no `./ns3 run` | Passar `./ns3 run "scratch/scenario_rdl_..."` causa falha porque o CMake registra o alvo sem o prefixo de diretório. | Usar sempre `./ns3 run "scenario_rdl_..."` (sem o prefixo `scratch/`). |

### 5.3. Monitoramento em Tempo Real das Simulações ns-3 / NORI 5G-LENA (6 Painéis tmux / TUI)

O repositório disponibiliza um painel terminal interativo de alta densidade dividido em **6 blocos cognitivos sincronizados** (`scripts/wsl_pane_monitors.py` e `scripts/launch_wsl_tmux_6panes.sh`). 

Os painéis operam sobre evidências empíricas reais:
1. **Varredura Dinâmica em Tempo Real:** Escaneiam automaticamente `experiments/results/ns3_runs/` para identificar a simulação mais recente e atualizam as métricas a cada segundo (`1.0s`).
2. **Telemetria Direta do FlowMonitor:** Extraem vazão real por fluxo (Mbps), atraso de ida e volta (ms), perda de pacotes e violação estrita de SLA para UEs conectados aos gNodeBs 5G-LENA (`7.0.0.x`).
3. **Sinalização E2 / ASN.1 APER:** Exibem traces binários Little-Endian reais de frames capturados (`e2_closed_loop_live.pcap`) e hashes criptográficos SHA-256 de não-repúdio.
4. **Governança Cognitiva H-RDL:** Exibem o grafo semântico (SDL), detecção de conflitos, resolução Nash Bargaining e despacho de controle E2SM-RC (< 10 ms).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [PAINEL 1: UEs & gNBs 5G-LENA]   [PAINEL 2: SINALIZAÇÃO E2]   [PAINEL 3: PERCEPÇÃO]    │
│ Nó: gnb_nori_01 (Band n78)       PCAP: e2_live (79B, 77B)     Conflito: TVS / EEVS     │
│ 36 UEs | 160 MB | SLA Violations E2AP ASN.1 APER SHA-256      Parâmetro: PRB / CELL_HO │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [PAINEL 4: GRAFO SDL COGNITIVO]  [PAINEL 5: REFINAMENTO H-RDL][PAINEL 6: AÇÃO E2SM-RC] │
│ 7 Nós | 6 Arestas (CONFLICT)     Motor: Nash Bargaining       ActionID=6 | TxID=5001   │
│ Densidade: 0.143 | Ciclos: 1     Quotas: URLLC 50% / eMBB 50% Latência: 1.9 ms (<10ms)│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Como Executar os Monitores:

```bash
cd ~/XApp-RDL-F1

# 1. Abrir os 6 painéis simultâneos na mesma tela via tmux (auto-detecta última simulação com dados):
bash scripts/launch_wsl_tmux_6panes.sh

# 2. Abrir os 6 painéis focando especificamente em um cenário (ex: S3 - TVS Handover ou S8 - Closed Loop):
bash scripts/launch_wsl_tmux_6panes.sh S3
bash scripts/launch_wsl_tmux_6panes.sh S8
bash scripts/launch_wsl_tmux_6panes.sh S1

# 3. Execução individual de painéis em terminais separados:
python3 scripts/wsl_pane_monitors.py pane1        # Janela 1: UEs, IPs 7.0.0.x e Vazão/Atraso
python3 scripts/wsl_pane_monitors.py pane2        # Janela 2: Sinalização E2 e Traces PCAP
python3 scripts/wsl_pane_monitors.py pane3        # Janela 3: Módulo de Percepção & Violação SLA
python3 scripts/wsl_pane_monitors.py pane4        # Janela 4: Grafo de Conhecimento Cognitivo
python3 scripts/wsl_pane_monitors.py pane5        # Janela 5: Refinamento & Safety Guards H-RDL
python3 scripts/wsl_pane_monitors.py pane6        # Janela 6: Despacho E2SM-RC e Malha Fechada

# 4. Monitorar um cenário específico individualmente:
python3 scripts/wsl_pane_monitors.py pane1 S8     # Monitora Closed-Loop NORI
python3 scripts/wsl_pane_monitors.py pane1 S10    # Monitora Enxame UAV 3D 6G
python3 scripts/wsl_pane_monitors.py pane1 S13    # Monitora SAGIN Desastre Multi-Camada
```

### 5.4. Processamento de Traces FlowMonitor e Geração de Relatórios
```bash
# Parser e consolidação de métricas em Markdown e CSV
python3 scripts/generate_ns3_flowmonitor_markdown_report.py
```

### 5.5. Geração de Gráficos e Tabelas Analíticas
Para atualizar os gráficos e as tabelas analíticas a partir dos dados experimentais:
```bash
# Execução direta com uv:
uv run --with matplotlib --with seaborn --with pandas --with scipy python analysis/generate_plots.py
uv run --with matplotlib --with seaborn --with pandas --with scipy python analysis/export_tables.py
```

### 5.6. Co-Simulação Rica Integrada em Malha Fechada (Closed-Loop E2 Live)

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

### 5.6. Acompanhamento das Execuções ns-3 no Terminal WSL: 6 Painéis

> [!IMPORTANT]
> Os painéis acompanham o diretório de execução mais recente em `experiments/results/ns3_runs/`.
> O lançador grava `run_status.json` e atualiza `execution.log` durante a compilação/execução.
> O XML do FlowMonitor só fica disponível depois que o cenário termina; antes disso, os painéis
> mostram o estado e o log, sem inventar métricas parciais. O FlowMonitor não fornece por si só
> PRB, classificação de slice, decisão RDL, mensagens KPM ou ACK E2SM-RC.

Os seis painéis exibem:

```
┌──────────────────────────────────────┬──────────────────────────────────────┬──────────────────────────────────────┐
│ 1. Execução e FlowMonitor           │ 2. Log e evidências E2               │ 3. KPIs do FlowMonitor               │
│ Status, fluxos e bytes              │ PCAP/KPM por execução                 │ Vazão, atraso e perdas               │
├──────────────────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 4. Endpoints IP observados          │ 5. Artefato de decisão RDL           │ 6. Request/ACK E2SM-RC               │
│ Topologia extraída do XML           │ Disponibilidade por run              │ Disponibilidade por run              │
└──────────────────────────────────────┴──────────────────────────────────────┴──────────────────────────────────────┘
```

#### 5.6.1. Opção A: Layout Nativo via `tmux` no WSL Ubuntu (Recomendado)

O script `launch_wsl_tmux_6panes.sh` divide a tela do WSL Ubuntu em uma grade 2x3. Os
renderers consultam o estado da execução a cada segundo; a frequência dos KPIs depende dos
artefatos que o simulador produz.

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

Sem filtro, o painel acompanha o diretório de execução mais recente. Também é possível
selecionar um cenário ou parte do nome do diretório:

```bash
python3 scripts/wsl_pane_monitors.py pane1
python3 scripts/wsl_pane_monitors.py pane1 S8
python3 scripts/wsl_pane_monitors.py pane2 --run 20261029T161800Z_scenario_rdl_s15
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
| **`zsh: no such file or directory: ./ns3`** | Comando executado fora do workspace do simulador | Executar `cd ~/ns3-oran-workspace/ns-3-oran` antes de `./ns3` |
| **`zsh: missing end of string / number expected`** | Colagem de múltiplos comandos com `#` no zsh | Adicionar `setopt INTERACTIVE_COMMENTS` em `~/.zshrc` |
| **`Couldn't find the specified program: scratch/...`** | Prefixo `scratch/` incluído no `./ns3 run` | Passar apenas o nome do alvo (ex: `./ns3 run "scenario_rdl_no_conflict ..."`) |

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
