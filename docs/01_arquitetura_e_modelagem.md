# Volume 01: Arquitetura do Sistema, Módulos Core e Modelagem Matemática

> **Navegação da Documentação Consolidada:**  
> **[01. Arquitetura & Modelagem](01_arquitetura_e_modelagem.md)** | **[02. Guia Operacional & Deploy](02_guia_operacional_deploy_e_simulacao.md)** | **[03. Taxonomia de Conflitos & Cenários](03_taxonomia_de_conflitos_e_cenarios.md)** | **[04. Relatório Científico Mestre](04_relatorio_cientifico_mestre_rdl.md)** | **[05. Auditoria & Conformidade O-RAN](05_auditoria_e_conformidade_oran.md)** | **[06. Roadmap & Futuro 6G](06_roadmap_e_pesquisa_futura_6g.md)**

---

## 1. Visão Geral e Fundamentos Arquiteturais

No ecossistema **O-RAN (Open Radio Access Network)**, a arquitetura aberta e desagregada viabiliza a execução concorrente de micro-aplicações especializadas (**xApps**) sobre o **Near-RT RIC (Near-Real-Time RAN Intelligent Controller)**, operando em escalas temporais de $10\text{ ms} \le \Delta t \le 1000\text{ ms}$.

Contudo, a coexistência de múltiplas xApps operando de forma desacoplada e autônoma engendra conflitos severos de governança:
- **Conflitos Diretos:** Múltiplas xApps solicitam simultaneamente alterações concorrentes no mesmo parâmetro de rádio (ex.: *xSlice* solicitando aumento de PRBs enquanto *Energy Saving* solicita corte de potência ou sono de células).
- **Conflitos Indiretos:** Ações em parâmetros distintos que degradam métricas compartilhadas ou afetam fatias vizinhas (ex.: *Traffic Steering* migrando UEs para células que já operam no limite de capacidade URLLC).
- **Conflitos Temporais (*Parameter Flipping / Ping-Pong*):** Oscilações cíclicas de sinalização decorrentes de decisões reativas em malha fechada.

A arquitetura **xApp-RDL (Resource and Decision Layer)** foi projetada para atuar como o ponto único e determinístico de coordenação, validação e arbitragem no Near-RT RIC.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SMO & NEAR-RT RIC (OSC)                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                            xApp-RDL CORE                              │  │
│  │  - Perception Agent (Decodificador ASN.1 APER E2SM-KPM / Telemetria) │  │
│  │  - Conflict Detector (Direto, Indireto, Implícito, Temporal)          │  │
│  │  - Knowledge Graph & Context Engine (Neo4j / Matriz de Associação)    │  │
│  │  - Reasoning Engine: Nível 1 (H-RDL) | Nível 2 (NDT) | Nível 3 (MAPPO)│  │
│  │  - Refinement Agent & Safety Guard (Action Masking / Boundary Clip)   │  │
│  │  - RCMapper & Dispatcher (E2SM-RC Format 1 Header / Format 2 Message) │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │ RMR (%meid gnb_01)                   │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                  E2 TERMINATION (E2term / SCTP:36422)                 │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                       │ Protocolo E2AP v02.03 (SCTP)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    SIMULADOR DISCRETO ns-3.48 / 5G-LENA v5.1                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                           NORI E2 AGENT                               │  │
│  │  - E2AP Handler (SetupRequest, Subscription, RICcontrolRequest)       │  │
│  │  - RAN Function Capability Registry (RC_ID=3, KPM_ID=2)               │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │ Callback em Memória C++ / IPC        │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                      PILHA PROTOCOLAR 5G-LENA NR                      │  │
│  │  - SDAP / RLC-AM & RLC-UM (Buffers de 10 MB, HOL Delay Tracking)     │  │
│  │  - MAC: NrMacSchedulerOfdmaPF (Proportional Fair Slicing / BWP)       │  │
│  │  - PHY: 3GPP 38.901 UMi Channel (3.5 GHz n78, 100 MHz, HARQ-IR, AMC) │  │
│  │  - FlowMonitor: Coleta ponta a ponta (Drain Time: App 58s, Sim 60s)   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

![Arquitetura Global de Co-Simulação ns-3 e Near-RT RIC](figures/01_arquitetura_e_governanca/diagram_01_global_pipeline_architecture.png)

---

## 2. Paradigmas Evolutivos: H-RDL (Fase 1) × CA-RDL (Fase 2)

A RDL é estruturada em duas fases complementares:

| Dimensão de Comparação | Fase 1: H-RDL (Hierarchical / Heuristic) | Fase 2: CA-RDL (Context-Aware / MARL) |
| :--- | :--- | :--- |
| **Paradigma Decisório** | Heurística determinística + Matriz TVS/EEVS | Sensibilidade contextual + Grafo de Conhecimento + MAPPO |
| **Janela de Decisão** | Lote fixo ($\Delta t = 200\text{ ms}$) | Janela adaptativa orientada a eventos e telemetria |
| **Garantia de Segurança** | *Safety Guards* invariantes (Boundary Clipping) | *Action Masking* em tempo de inferência + Safety Guard desacoplado |
| **Sobrecarga ($T_{decision}$)** | **0,12 ms** (Sub-milissegundo, 0,06% do ciclo) | **1,84 ms** (Inferência de Redes Neurais, 0,92% do ciclo) |
| **Ganho de Vazão (vs B0)** | **+19,4%** (101,7 Mbps) | **+24,2%** (105,8 Mbps) |
| **Violações de SLA** | **0,0%** (Erradicação completa) | **0,0%** (Erradicação completa com maior eficiência) |

---

## 3. Estrutura de Software (Clean Architecture & Domain-Driven Design)

O código-fonte segue estritamente a separação em camadas independentes:

```text
src/
├── agents/                      # Camada de Inteligência e Governança
│   ├── perception_agent.py      # Agrupamento temporal e detecção de colisões
│   ├── reasoning_agent.py       # Resolução Nível 1 (Heurísticas) / Nível 2 (NDT) / Nível 3 (MAPPO)
│   └── refinement_agent.py      # Safety Guards físicos invariantes
├── conflict_types.py            # Contratos de dados imutáveis (RDLDecision, XAppAction)
├── coordination/                # Despacho e rastreamento de transações
│   ├── dispatcher.py            # Envio E2SM-RC via RMR
│   └── ack_tracker.py           # Rastreamento assíncrono de RIC_CONTROL_ACK e RTT
├── e2/                          # Camada Normativa O-RAN (ASN.1 APER isolado)
│   ├── e2ap/                    # Codecs E2AP v02.03 (Setup, Subscriptions, Control)
│   ├── kpm/                     # Codecs E2SM-KPM v03.00 (EventTrigger / ActionDefinition)
│   └── rc/                      # Codecs E2SM-RC v01.03 (RCMapper, Format 1 Header / Format 2 Message)
├── models/                      # Modelos Analíticos Calibrados de Rádio 5G
│   ├── shannon_capacity.py      # Capacidade espectral com overhead 3GPP
│   ├── queuing_delay.py         # Modelo de atraso M/G/1 com saturação
│   └── earth_energy.py          # Modelo linear de consumo energético (Earth Project)
├── observability/               # Telemetria e Saúde
│   ├── health_server.py         # HTTP Health/Ready probes (FastAPI porta 8080)
│   └── metrics_server.py        # Exportador Prometheus (porta 8081)
└── rdl_xapp.py                  # Ciclo de vida da xApp e loop principal
```

---

## 4. Agentes Especialistas e Pipeline de Decisão

### 4.1. PerceptionAgent (Percepção e Detecção)
- Agrupa propostas recebidas de múltiplas xApps dentro da janela de agregação ($\Delta t = 200\text{ ms}$).
- Constrói o grafo de conflitos $G = (V, E)$, onde $V$ são as propostas e $E$ representa interseções diretas no mesmo `(cell_id, parameter_id)` ou colisões indiretas de fatia (*slice coupling*).

### 4.2. ReasoningAgent (Raciocínio e Arbitragem)
- **Nível 1 (Heurística Hierárquica - H-RDL):** Executa matriz de prioridades de serviço:
  1. *Safety Invariants* (Proteção de enlace e integridade de rádio);
  2. *URLLC Critical Guarantee* (SLA de latência $D \le 5\text{ ms}$);
  3. *eMBB High-Throughput Allocation* (Vazão garantida $T \ge 60\text{ Mbps}$);
  4. *Energy Efficiency Trimming* (Economia de energia quando folga de SLA existe).
- **Nível 2 (Digital Twin & Árvore Decisória Não-Determinística - NDT):** Projeção preditiva do impacto antes da aplicação.
- **Nível 3 (Multi-Agent PPO - CA-RDL):** Otimização da política conjunta sob formulação CMDP.

### 4.3. RefinementAgent & Safety Guards (Segurança Invariante)
Aplica restrições físicas invioláveis antes de qualquer emissão para a interface E2:
1. **Limites de Potência ($P_{tx}$):** $P_{min} \le P_{tx} \le P_{max}$ (ex.: $10\text{ dBm} \le P_{tx} \le 43\text{ dBm}$).
2. **Orçamento de Recursos ($PRB$):** $\sum_{s \in \mathcal{S}} \text{Quota}(s) \le 100\%$.
3. **Janela Anti-Ping-Pong:** $\Delta t_{min} \ge 1000\text{ ms}$ entre comandos opostos no mesmo nó.

![Componentes e Fluxo de Decisão xApp-RDL](figures/01_arquitetura_e_governanca/fig_componentes_fluxo_decisao.png)

---

## 5. Modelagem Matemática Formal

### 5.1. Modelo Analítico de Capacidade e Rádio
A capacidade máxima alcançável em enlace descendente (DL) é modelada pela formulação de Shannon com calibração de overhead 3GPP:

$$C = BW_{\text{eff}} \cdot \log_2 \left( 1 + \min(\text{SINR}_{\text{eff}}, \text{SINR}_{\text{max}}) \right) \cdot (1 - \text{OH}_{\text{3GPP}})$$

Onde:
- $BW_{\text{eff}} = N_{\text{PRB}} \cdot 12 \cdot \Delta f$ (com $\Delta f = 30\text{ kHz}$ para numerologia $\mu = 1$);
- $\text{OH}_{\text{3GPP}} = 0,14$ (overhead de sinalização DMRS, PDCCH, CSI-RS e PBCH);
- $\text{SINR}_{\text{eff}} = \frac{\text{SINR}}{\Gamma}$, com penalidade de implementação $\Gamma = 1,25$ ($0,97\text{ dB}$).

### 5.2. Modelo de Atraso e Filas M/G/1
O atraso ponta a ponta $D$ é decomposto em atraso de transmissão, propagação e espera em buffer RLC:

$$D = D_{\text{prop}} + D_{\text{tx}} + \frac{\lambda \overline{X^2}}{2(1 - \rho)}$$

Onde $\rho = \frac{\lambda}{\mu}$ representa a utilização do canal. Se $\rho \to 1$, o *Head-of-Line (HOL) Delay* satura exponencialmente.

### 5.3. Modelo de Eficiência Energética (Earth Project / 3GPP)
A potência elétrica consumida pela gNodeB é expressa por:

$$P_{\text{total}} = N_{\text{TRX}} \cdot \left( P_0 + \alpha \cdot P_{\text{tx}} \right), \quad 0 \le P_{\text{tx}} \le P_{\text{max}}$$

Onde $P_0 = 130\text{ W}$ é a potência estática do circuito em repouso e $\alpha = 4,7$ é o coeficiente do amplificador de potência (PA).

### 5.4. Formulação CMDP e Safe-MAPPO (Fase 2)
O problema de controle multi-xApp é formulado como um **Processo de Decisão de Markov Parcialmente Observável e Restrito (CMP-POMDP)**:

$$\max_{\pi} \mathbb{E}_{\tau \sim \pi} \left[ \sum_{t=0}^{T} \gamma^t R(s_t, \mathbf{a}_t) \right] \quad \text{sujeito a} \quad \mathbb{E}_{\tau \sim \pi} \left[ \sum_{t=0}^{T} \gamma^t C_k(s_t, \mathbf{a}_t) \right] \le d_k, \quad \forall k$$

A função de recompensa global equilibra vazão, latência e equidade:

$$R(s_t, \mathbf{a}_t) = w_1 \sum_{s} T_s(t) - w_2 \sum_{s} \max(0, D_s(t) - D_{\text{max}, s}) + w_3 J_{\text{Jain}}(t)$$

As restrições de custo $C_k$ penalizam violações de invariantes físicas, resolvidas pelo método de Multiplicadores de Lagrange e *Action Masking* estrito no ator.

![Arquitetura Cognitiva Safe-MAPPO](figures/01_arquitetura_e_governanca/diagram_02_arquitetura_cognitiva_mappo.png)

---

## 6. Mapeamento Normativo O-RAN (E2AP, E2SM-KPM e E2SM-RC)

A camada RDL implementa o desacoplamento formal de codecs ASN.1 APER conforme os padrões O-RAN WG3:

| Protocolo | Versão Normativa | Função na Arquitetura RDL |
| :--- | :---: | :--- |
| **E2AP** | v02.03 | Transporte de mensagens de controle, setup e subscrição SCTP na porta 36422. |
| **E2SM-KPM** | v03.00 | Decodificação de telemetria periódica (Formato 1: PRBs alocados, vazão UE, BLER, perdas). |
| **E2SM-RC** | v01.03 | Mapeamento de decisões RDL (`RCMapper`) em comandos Formato 1 Header e Formato 2 Message. |

### Tabela Canônica de Parâmetros RAN Controlados
- `PRB_QUOTA` (Parameter ID: 1, Faixa: 0–100%);
- `SCHEDULER_WEIGHT` (Parameter ID: 2, Faixa: 1–100);
- `TX_POWER` (Parameter ID: 3, Faixa: 10–43 dBm);
- `HANDOVER_TARGET` (Parameter ID: 4, Cell ID de destino).

![Conformidade com os Padrões O-RAN Alliance](figures/01_arquitetura_e_governanca/diagram_05_conformidade_oran_standards.png)
