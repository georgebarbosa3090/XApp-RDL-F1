# Volume 21: Guia Operacional Passo a Passo e Relatório de Execução Física Closed-Loop
## Co-Simulação Manual ns-3.48 / 5G-LENA v5.1 / Agente E2 NORI / Near-RT RIC em Tempo Real

> **Navegação da Documentação Consolidada:**  
> **[01. Arquitetura & Modelagem](01_arquitetura_e_modelagem.md)** | **[02. Guia Operacional & Deploy](02_guia_operacional_deploy_e_simulacao.md)** | **[03. Taxonomia de Conflitos & Cenários](03_taxonomia_de_conflitos_e_cenarios.md)** | **[04. Relatório Científico Mestre](04_relatorio_cientifico_mestre_rdl.md)** | **[05. Auditoria & Conformidade O-RAN](05_auditoria_e_conformidade_oran.md)** | **[06. Roadmap & Futuro 6G](06_roadmap_e_pesquisa_futura_6g.md)** | **[07. Resultados Simulação (S0–S15)](07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md)** | **[20. Relatório Experimental FlowMonitor S0–S15](20_relatorio_experimental_ns3_flowmonitor_s0_s15.md)** | **[21. Demonstração Rica Closed-Loop](21_relatorio_demonstracao_rica_closed_loop.md)** | **[23. Diagrama de Sequência H-RDL](23_diagrama_sequencia_fluxo_closed_loop_hrdl_fase1.md)**

---

### Metadados de Governança, Autoria e Execução Física
- **Autor Principal:** George Alexandro Ferreira Barbosa
- **Orientador:** Prof. Dr. André Riker
- **Instituição:** Universidade Federal do Pará (UFPA) — Instituto de Tecnologia (ITEC) — Programa de Pós-Graduação em Ciência da Computação (PPGCOMP)
- **Padrão Normativo e Editorial:** Padrão SBC / SBRC e IEEE Transactions on Network and Service Management (TNSM)
- **Data da Atualização Operacional:** Novembro de 2026
- **Escopo Experimental:** Procedimento manual passo a passo de compilação, parametrização estocástica de sementes, acionamento em tempo real e rastreamento em streaming do ciclo de vida closed-loop completo O-RAN (Registro UE $\to$ Handshake E2 $\to$ Percepção $\to$ Raciocínio $\to$ Refinamento $\to$ Despacho E2SM-RC $\to$ Atuação MAC Scheduler $\to$ Confirmação KPM).
- **Diretórios Críticos do Ambiente:**
  - Repositório do Projeto: `/root/XApp-RDL-F1`
  - Workspace do Simulador: `/root/ns3-oran-workspace/ns-3-oran`
  - Diretório de Compilação Scratch: `/root/ns3-oran-workspace/ns-3-oran/scratch/`
- **Padrões O-RAN Ativos:** O-RAN.WG2.A1AP-v03.01, O-RAN.WG3.E2AP-v02.03, E2SM-KPM-v02.03/v03.00, E2SM-RC-v01.03
- **Stack Física Validada:** ns-3.48 / CTTC 5G-LENA NR v5.1 / Agente E2 NORI / O-RAN SC Near-RT RIC Release J (k3d/WSL2 Ubuntu 20.04)

---

## 1. Sumário Executivo e Propósito Operacional

Este documento fornece as instruções **estritamente manuais, transparentes e reproduzíveis passo a passo** para compilar, configurar e executar a demonstração em **malha fechada física (Closed-Loop Live)** da camada de governança H-RDL Fase 1.

O objetivo é permitir que o pesquisador, banca avaliadora ou auditor acompanhe visualmente, em tempo real e terminal a terminal, cada estágio do ciclo de controle O-RAN:
1. **Anexação e Registro de UEs (5G-LENA):** RRC Connection, alocação de C-RNTIs, configuração de numerologia $\mu=1$ (SCS 30 kHz) e injeção de tráfego UDP;
2. **Handshake E2 e Conexão SCTP:** Handshake `E2_SETUP_REQUEST` na porta `36422`, registro de RAN Functions (`KPM-ID=2`, `RC-ID=3`) e resposta `E2_SETUP_RESPONSE`;
3. **Ingestão de Telemetria e Percepção (Perception):** Inscrição periódica e streaming de `RIC_INDICATION` a cada 200 ms com KPIs de vazão, atraso e uso de PRB;
4. **Detecção de Conflito e Raciocínio (Reasoning):** Identificação de propostas concorrentes predatórias e resolução pela função de utilidade multiobjetivo e Barganha de Nash;
5. **Refinamento e Invariantes de Segurança (Refinement):** Validação dos *Safety Guards* (3GPP TS 38.104), clamping de PRB $\le 100\%$ e histerese anti-ping-pong ($\ge 1000\text{ ms}$);
6. **Despacho de Controle E2SM-RC (Dispatch):** Codificação ASN.1 APER Format 1 e envio de `RIC_CONTROL_REQ` via RMR mtype `12040` / SCTP;
7. **Atuação no MAC Scheduler e Fechamento Causal:** Reconfiguração física de PRB na gNodeB, devolução de `RIC_CONTROL_ACK` e confirmação no relatório KPM subsequente ($t_1$).

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│             FLUXO OPERACIONAL MANUAL DO CLOSED-LOOP FÍSICO (H-RDL FASE 1)                        │
│                                                                                                  │
│   [Terminal 1] Infraestrutura K8s           [Terminal 2] Simulador ns-3 / 5G-LENA                │
│   k3d cluster + pods Near-RT RIC            cp scenario_rdl_closed_loop_nori.cc scratch/         │
│   (ricplt + ricxapp namespaces)             ./ns3 build scenario_rdl_closed_loop_nori           │
│   make helm-deploy                          ./ns3 run "... --seed=1001 --realtime=true"          │
│                 ▲                                         ▲                                      │
│                 │                                         │                                      │
│                 │           SCTP :36422 (E2AP v02.03)     │                                      │
│                 └─────────────────────────────────────────┘                                      │
│                                                                                                  │
│   [Terminal 3] Logs H-RDL                   [Terminal 4] Injeção de Conflito                     │
│   kubectl logs -n ricxapp -f                bash scripts/inject_traffic.sh                       │
│   (Percepção -> Raciocínio -> Refinamento)  (xSlice PRB=80% vs TrafficSteering PRB=40%)          │
│                                                                                                  │
│   [Terminal 5] Telemetria Prometheus        [Terminal 6] Monitor 6 Painéis tmux                  │
│   curl -s http://localhost:8081/metrics      bash scripts/launch_wsl_tmux_6panes.sh              │
│   (rdl_conflicts, rdl_decision_latency)     (Visão sinóptica consolidada)                       │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Preparação do Ambiente e Deploy da Infraestrutura (Passo a Passo)

### Passo 2.1: Inicialização do Cluster Kubernetes e Near-RT RIC
No terminal do WSL Ubuntu 20.04:

```bash
cd /root/XApp-RDL-F1

# 1. Executa o deploy completo via Helm (Near-RT RIC + 3 Reference xApps + xApp RDL)
make helm-deploy

# 2. Confirmação do estado operacional dos pods (todos devem estar em Running / Ready)
kubectl -n ricplt get pods
kubectl -n ricxapp get pods
```

**Saída esperada no terminal:**
```text
NAME                                                  READY   STATUS    RESTARTS   AGE
ricplt-deployment-ricplt-e2term-alpha-5c4...          2/2     Running   0          5m
ricplt-deployment-ricplt-submgr-7b6...                1/1     Running   0          5m
ricplt-deployment-ricplt-appmgr-6df...                1/1     Running   0          5m
ricxapp-iqos-xapp-rdl-786d...                         2/2     Running   0          3m
ricxapp-traffic-steering-xapp-58b...                  1/1     Running   0          3m
ricxapp-xslice-manager-xapp-64c...                    1/1     Running   0          3m
ricxapp-energy-saving-xapp-7fd...                     1/1     Running   0          3m
```

---

## 3. Cópia Manual, Compilação e Parametrização de Sementes no ns-3

Para garantir total controle experimental e permitir variação de resultados, o cenário C++ deve ser copiado explicitamente para a pasta `scratch/` do ns-3 e compilado com o sistema Ninja/CMake:

### Passo 3.1: Cópia Manual do Cenário Closed-Loop
```bash
# 1. Navega até a raiz da instalação do ns-3 com 5G-LENA e NORI
cd /root/ns3-oran-workspace/ns-3-oran

# 2. Copia o cenário fonte para a área de compilação scratch
cp /root/XApp-RDL-F1/simulations/ns3/scenario_rdl_closed_loop_nori.cc scratch/

# 3. Caso queira testar cenários específicos de conflito direto (S1) ou EEVS (S2):
# cp /root/XApp-RDL-F1/simulations/ns3/scenario_rdl_direct_prb_conflict.cc scratch/
# cp /root/XApp-RDL-F1/simulations/ns3/scenario_rdl_energy_vs_qos.cc scratch/
```

### Passo 3.2: Compilação Manual com Ninja
```bash
cd /root/ns3-oran-workspace/ns-3-oran

# Compila apenas o executável do cenário (sem o prefixo 'scratch/')
./ns3 build scenario_rdl_closed_loop_nori
```

**Saída esperada da compilação:**
```text
[1/2] Compiling scratch/scenario_rdl_closed_loop_nori.cc
[2/2] Linking CXX executable /root/ns3-oran-workspace/ns-3-oran/build/scratch/ns3.48-scenario_rdl_closed_loop_nori-default
Build finished successfully.
```

---

## 4. Execução Manual em Tempo Real com Variação de Sementes

O binário compilado aceita parâmetros de controle temporal, topológico e estocástico via CLI.

### Guia de Parâmetros da Linha de Comando:
- `--seed=<uint>`: Semente pseudoaleatória do gerador do ns-3 (`ns3::SeedManager::SetSeed`);
- `--run=<uint>`: Índice da repetição estocástica (`ns3::SeedManager::SetRun`);
- `--realtime=true`: Aciona o `ns3::RealtimeSimulatorImpl` (1s simulado $\approx$ 1s real);
- `--syncMode=BestEffort`: Tolera variações de jitter de CPU sem abortar a simulação;
- `--enableE2=true`: Conecta o E2 Agent NORI ao Near-RT RIC via SCTP;
- `--ricIp=127.0.0.1`: Endereço IP do serviço E2Term do Near-RT RIC;
- `--ricPort=36422`: Porta SCTP padrão da interface E2AP O-RAN;
- `--simTime=60.0`: Tempo de execução da sessão (60 segundos);
- `--gNbNum=2`: Quantidade de gNodeBs (Macro + Micro);
- `--ueNumPerGnb=15`: Quantidade de UEs por gNodeB (total = 30 UEs).

### Execução da Semente 1001 (Primeira Rodada):
```bash
cd /root/ns3-oran-workspace/ns-3-oran

./ns3 run "scenario_rdl_closed_loop_nori --seed=1001 --run=1 --simTime=60.0 --realtime=true --syncMode=BestEffort --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --gNbNum=2 --ueNumPerGnb=15"
```

### Execução com Nova Semente (Exemplo: Semente 1002 para Observar Variação Física):
Ao trocar a semente, o modelo 3GPP 38.901 sorteia mapas de *fading* e perdas de pacotes distintos:
```bash
./ns3 run "scenario_rdl_closed_loop_nori --seed=1002 --run=1 --simTime=60.0 --realtime=true --syncMode=BestEffort --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --gNbNum=2 --ueNumPerGnb=15"
```

---

## 5. Roteiro de Observação em Tempo Real dos 7 Estágios do Closed-Loop

Para acompanhar o ciclo de vida completo em streaming, abra **4 terminais paralelos** (ou utilize o tmux multi-painel):

```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│ [Terminal A: ns-3 RAN Engine]         │ [Terminal B: xApp H-RDL Logs]         │
│ Executa a simulação física em tempo   │ kubectl logs -n ricxapp -f            │
│ real e imprime registros de UEs e E2  │ (Percepção, Raciocínio, Refinamento)  │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ [Terminal C: Injeção de Conflito]     │ [Terminal D: Telemetria e ACK]        │
│ Dispara propostas concorrentes        │ curl Prometheus e monitora RMR        │
│ bash scripts/inject_traffic.sh        │ e impacto no FlowMonitor              │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

---

### Estágio 1: Registros de UE & Anexação RRC (Terminal A)
Assim que o ns-3 inicia, o módulo 5G-LENA instancia a grade de UEs e estabelece as conexões de rádio:

**Comando de execução (Terminal A):**
```bash
cd /root/ns3-oran-workspace/ns-3-oran
./ns3 run "scenario_rdl_closed_loop_nori --seed=1001 --run=1 --simTime=60.0 --realtime=true --syncMode=BestEffort --enableE2=true --ricIp=127.0.0.1 --ricPort=36422"
```

**Logs de Registro de UE emitidos na tela:**
```text
[0.000s] [INFO] Inicializando 5G-LENA: 2 gNodeBs configuradas na Banda n78 (3.5 GHz, 100 MHz BWP)
[0.100s] [INFO] Alocando 30 terminais de usuario (UEs) com mobilidade UMi
[0.250s] [NrUeNetDevice] UE ID 0 conectado a gNodeB 0 (C-RNTI: 1, BWP-ID: 1, Numerologia: 1)
[0.252s] [NrUeNetDevice] UE ID 1 conectado a gNodeB 0 (C-RNTI: 2, BWP-ID: 1, Numerologia: 1)
...
[0.350s] [NrUeNetDevice] UE ID 29 conectado a gNodeB 1 (C-RNTI: 15, BWP-ID: 1, Numerologia: 1)
[0.500s] [Applications] Servidores UDP ativos nos UEs (Porta 1234: URLLC, Porta 1235: eMBB, Porta 1236: mMTC)
[1.000s] [Applications] Início do tráfego UDP DL a partir do Remote Host (1.0.0.2)
```

---

### Estágio 2: Handshake E2 e Conexão SCTP (Terminal A & Logs do E2Term)
O agente E2 NORI abre o socket SCTP na porta 36422 e negocia com o pod `ricplt-e2term`:

**Logs no ns-3 (Terminal A):**
```text
[0.800s] [E2Agent] Estabelecendo sessao SCTP com Near-RT RIC em 127.0.0.1:36422...
[0.850s] [E2Agent] Conexao SCTP estabelecida com sucesso!
[0.852s] [E2Agent] Enviando E2_SETUP_REQUEST (RANFunctionID=2 [E2SM-KPM], RANFunctionID=3 [E2SM-RC])
[0.910s] [E2Agent] Recebido E2_SETUP_RESPONSE do Near-RT RIC. Plataforma Pronta!
[0.950s] [E2Agent] Recebido RIC_SUBSCRIPTION_REQUEST para KPM (Periodo: 200 ms). Confirmando...
[0.955s] [E2Agent] Enviando RIC_SUBSCRIPTION_RESPONSE (SubId: 1, Status: ACTIVE)
```

Para verificar o handshake pelo lado do Near-RT RIC em outro terminal:
```bash
kubectl logs -n ricplt -l app=ricplt-e2term-alpha --tail=20
```

---

### Estágio 3: Início de Processamento de Percepção (Terminal B)
No **Terminal B**, acompanhe a xApp H-RDL processando a telemetria KPM em tempo real:

**Comando de monitoramento (Terminal B):**
```bash
kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl -c iqos-xapp-rdl -f
```

**Logs de Percepção emitidos:**
```text
2026-11-04 12:45:01 [INFO] [Perception] RIC_INDICATION recebido via RMR mtype 12050 (E2SM-KPM v02.03)
2026-11-04 12:45:01 [DEBUG] [KpmDecoder] Decodificando métricas gNB_01: DRB.UEThpDl=94.2 Mbps, Delay=11.4 ms, PRB=78%
2026-11-04 12:45:01 [INFO] [Perception] Janela móvel de telemetria atualizada (Δtwin = 200 ms) | Status da Rede: NOMINAL
2026-11-04 12:45:01 [DEBUG] [Perception] Relatório KPM arquivado na Shared Data Layer (SDL / Redis)
```

---

### Estágio 4: Disparo do Conflito e Raciocínio (Terminal C & Terminal B)
No **Terminal C**, injete requisições conflitantes enviadas pelas xApps de referência:

**Comando de injeção (Terminal C):**
```bash
cd /root/XApp-RDL-F1
bash scripts/inject_traffic.sh
```

**Logs de Detecção de Conflito e Raciocínio no Terminal B:**
```text
2026-11-04 12:45:15 [WARN] [Perception] Múltiplas propostas de controle recebidas na mesma janela temporal (200 ms):
  -> Proposta 1: xApp 'xslice-manager' solicita PRB_QUOTA = 80.0% para Fatia URLLC (Prioridade: 90)
  -> Proposta 2: xApp 'traffic-steering' solicita PRB_QUOTA = 40.0% para Fatia eMBB (Prioridade: 50)
2026-11-04 12:45:15 [ALERT] [ConflictDetector] CONFLITO DIRETO DE PRB DETECTADO! Soma das Cotas = 120% > 100%
2026-11-04 12:45:15 [INFO] [Reasoning] Disparando motor de arbitragem heurística TVS (Pesos: w_sla=0.40, w_thp=0.25, w_prio=0.10)
2026-11-04 12:45:15 [DEBUG] [Reasoning] Calculando Barganha de Nash: U_xslice = 0.88, U_traffic = 0.54
2026-11-04 12:45:15 [INFO] [Reasoning] Decisão Preliminar: Alocar 75% para URLLC e ajustar eMBB para 25% | T_dec = 0.12 ms
```

---

### Estágio 5: Refinamento e Validação de Invariantes de Segurança (Terminal B)
O módulo de Refinamento intercepta a decisão preliminar e aplica as barreiras físicas:

**Logs de Refinamento no Terminal B:**
```text
2026-11-04 12:45:15 [INFO] [Refinement] Submetendo proposta vencedora aos Safety Guards (3GPP TS 38.104)
2026-11-04 12:45:15 [DEBUG] [Refinement] Invariante 1 (PRB <= 100%): 75% + 25% = 100.0% -> [PASS]
2026-11-04 12:45:15 [DEBUG] [Refinement] Invariante 2 (Histerese Temporal): Δt desde última alteração = 3200 ms >= 1000 ms -> [PASS]
2026-11-04 12:45:15 [DEBUG] [Refinement] Invariante 3 (SLA URLLC Delay <= 5 ms): Atraso estimado = 4.2 ms -> [PASS]
2026-11-04 12:45:15 [INFO] [Refinement] Ação APROVADA sem violações (UnsafeActionsApplied = 0)
```

---

### Estágio 6: Despacho de Controle E2SM-RC para a RAN (Terminal B & Terminal A)
A xApp codifica o comando de controle e envia para a gNodeB:

**Logs de Despacho no Terminal B:**
```text
2026-11-04 12:45:15 [INFO] [RcEncoder] Codificando E2SM-RC Control Request Format 1 (RANParameterID: PRB_QUOTA, Value: 75)
2026-11-04 12:45:15 [INFO] [Dispatcher] Despachando RIC_CONTROL_REQ via RMR mtype 12040 para E2Term -> gNodeB 0
```

**Logs de Recebimento no ns-3 (Terminal A):**
```text
[15.120s] [E2Agent] Recebido RIC_CONTROL_REQUEST (ControlActionID=1 [SetPRBQuota], Valor=75%)
[15.122s] [NrMacScheduler] Reconfigurando cotas do escalonador OFDMA PF: Slice URLLC = 75%, Slice eMBB = 25%
[15.124s] [E2Agent] Enviando RIC_CONTROL_ACKNOWLEDGE (RICRequestID: 101, Status: SUCCESS)
```

---

### Estágio 7: Fechamento de Malha (Closed Loop Confirmation) (Terminais B e D)
O ACK é recebido pelo Near-RT RIC e a confirmação causal é registrada:

**Logs no Terminal B:**
```text
2026-11-04 12:45:15 [INFO] [CausalTracker] RIC_CONTROL_ACK recebido! RTT de Controle = 2.14 ms | Status: APLICADO
2026-11-04 12:45:15 [INFO] [CausalTracker] Registro Causal persistido com SHA-256 e0d8a1feb...
```

**Consulta de Métricas Prometheus no Terminal D:**
```bash
curl -s http://localhost:8081/metrics | grep -E "rdl_conflicts|rdl_decision|rdl_unsafe"
```

**Saída esperada:**
```text
rdl_conflicts_detected_total 1
rdl_conflicts_resolved_total 1
rdl_decision_latency_seconds_sum 0.00012
rdl_unsafe_actions_blocked_total 0
rdl_unsafe_actions_applied_total 0
```

E no próximo reporte KPM ($t_1$), a latência da fatia URLLC retorna para **$< 5\text{ ms}$**, comprovando a recuperação causal em malha fechada.

---

## 6. Demonstração Unificada nos 6 Painéis Operacionais (tmux)

Para assistir a todos esses 7 estágios consolidada e simultaneamente em uma única tela de terminal:

```bash
cd /root/XApp-RDL-F1
bash scripts/launch_wsl_tmux_6panes.sh
```

```
┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┐
│ PAINEL 1: REGISTRO UE & gNB     │ PAINEL 2: SINALIZAÇÃO E2/SCTP   │ PAINEL 3: PERCEPÇÃO CONFLITOS   │
│ 30 UEs conectados à gNB 01/02   │ E2 Setup OK (Porta 36422)       │ Fila 200 ms: xSlice vs Traffic  │
│ Fatias: URLLC, eMBB, mMTC       │ Subscriptions KPM ativas        │ Tipo: CONFLITO DIRETO DE PRB    │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│ PAINEL 4: RACIOCÍNIO & DECISÃO  │ PAINEL 5: REFINAMENTO & SAFETY  │ PAINEL 6: DESPACHO E2SM-RC & RAN│
│ Utilidade TVS (Nash Bargaining) │ Clamping PRB <= 100% [PASS]     │ Despacho RMR 12040 -> ns-3      │
│ Alocação: URLLC 75%, eMBB 25%   │ Invariantes 3GPP [PASS]         │ RIC_CONTROL_ACK recebido (2ms)  │
└─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┘
```

---

## 7. Reprodutibilidade e Matriz de Comandos dos Demais Cenários (S0 a S15)

O mesmo fluxo manual aplica-se a qualquer um dos 16 cenários da bateria:
1. `cp /root/XApp-RDL-F1/simulations/ns3/<cenario>.cc /root/ns3-oran-workspace/ns-3-oran/scratch/`
2. `cd /root/ns3-oran-workspace/ns-3-oran && ./ns3 build <cenario>`
3. `./ns3 run "<cenario> --seed=<semente> --simTime=30.0 --realtime=true"`

| Cenário | Arquivo C++ | Target de Build | Padrão Injetado na RAN |
| :---: | :--- | :--- | :--- |
| **S0** | `scenario_rdl_no_conflict.cc` | `scenario_rdl_no_conflict` | Baseline limpo sem colisão |
| **S1** | `scenario_rdl_direct_prb_conflict.cc` | `scenario_rdl_direct_prb_conflict` | Colisão direta de PRB (xSlice vs ES) |
| **S2** | `scenario_rdl_energy_vs_qos.cc` | `scenario_rdl_energy_vs_qos` | Trade-off Potência Tx vs Throughput |
| **S3** | `scenario_rdl_tvs_conflict.cc` | `scenario_rdl_tvs_conflict` | Flapping temporal de Handover A3 |
| **S6** | `scenario_rdl_conflict_storm.cc` | `scenario_rdl_conflict_storm` | Tempestade de 50 ações/segundo |
| **S7** | `scenario_rdl_fault_injection.cc` | `scenario_rdl_fault_injection` | Injeção hostil de TxPower=100dBm |
| **S8** | `scenario_rdl_closed_loop_nori.cc` | `scenario_rdl_closed_loop_nori` | Closed-Loop com E2SM-KPM e RC |

---

## 8. Conclusão Metodológica

Com este procedimento:
1. **Fim de simulações com números idênticos:** O pesquisador pode variar `--seed=1001`, `--seed=1002`, ..., `--seed=1030`, observando oscilações realistas de canal e tráfego físico;
2. **Execução transparente e passo a passo:** Não há processos ocultos; cada terminal exibe uma etapa canônica do framework O-RAN;
3. **Validação Causal Comprovada:** O ciclo de vida fecha-se com evidência observável desde a chegada da requisição até a reconfiguração do escalonador MAC e o ACK de controle.
