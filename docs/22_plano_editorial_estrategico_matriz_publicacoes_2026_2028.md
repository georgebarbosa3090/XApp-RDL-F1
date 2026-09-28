# Volume 22: Plano Editorial Estratégico & Matriz Exaustiva de Publicações (2026–2028)
## Roteiro de Submissões: H-RDL (Fase 1) $\to$ CA-RDL (Fase 2) $\to$ Multi-Tier Governance (Fase 3)

> **Navegação da Documentação Consolidada:**  
> **[01. Arquitetura & Modelagem](01_arquitetura_e_modelagem.md)** | **[02. Guia Operacional & Deploy](02_guia_operacional_deploy_e_simulacao.md)** | **[03. Taxonomia de Conflitos & Cenários](03_taxonomia_de_conflitos_e_cenarios.md)** | **[04. Relatório Científico Mestre](04_relatorio_cientifico_mestre_rdl.md)** | **[05. Auditoria & Conformidade O-RAN](05_auditoria_e_conformidade_oran.md)** | **[06. Roadmap & Futuro 6G](06_roadmap_e_pesquisa_futura_6g.md)** | **[07. Resultados Simulação (S0–S15)](07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md)** | **[20. Relatório Experimental FlowMonitor S0–S15](20_relatorio_experimental_ns3_flowmonitor_s0_s15.md)** | **[21. Demonstração Rica Closed-Loop](21_relatorio_demonstracao_rica_closed_loop.md)** | **[22. Plano Editorial Estratégico](22_plano_editorial_estrategico_matriz_publicacoes_2026_2028.md)**

---

### Metadados de Governança e Planejamento Editorial
- **Autor Principal:** George Alexandro Ferreira Barbosa
- **Orientador:** Prof. Dr. André Riker
- **Instituição:** Universidade Federal do Pará (UFPA) — Instituto de Tecnologia (ITEC) — Programa de Pós-Graduação em Ciência da Computação (PPGCOMP)
- **Data de Emissão:** 28 de Setembro de 2026
- **Status Metodológico:** Homologado para Execução Editorial e Submissões 2026–2028
- **Padrões Normativos:** IEEE Transactions Style Manual, Padrão SBC/SBRC, Diretrizes de Ciência Aberta e Reprodutibilidade (Artifact Badging)

---

## 1. Sumário Executivo do Planejamento Editorial

Este documento estabelece o **Plano Editorial Estratégico Oficial** do ecossistema de pesquisa **xApp-RDL (Resource and Decision Layer)**. O projeto decompõe-se em **seis manuscritos científicos independentes**, com escopos rigorosamente delimitados para eliminar qualquer sobreposição temático-metodológica (*zero salami slicing*) e maximizar o impacto nas principais revistas científicas internacionais da área de Redes de Computadores e Telecomunicações (IEEE ComSoc e Elsevier).

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 CRONOGRAMA GERAL DE SUBMISSÕES (2026–2028)                             │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  [PAPER 1: Q4/2026] ──► IEEE TNSM (H-RDL Flagship: Gestão de Conflito, Safety Guard & Loop E2)         │
│  [PAPER 2: Q1/2027] ──► IEEE TCCN (CA-RDL Cognitive: Knowledge Graph, Safe-MAPPO & Two-Tier dApp)      │
│  [PAPER 3: Q2/2027] ──► IEEE Network / CommMag (Visão Arquitetural: Governança Multi-Tier r/x/dApp)    │
│  [PAPER 4: Q3/2027] ──► Elsevier Computer Networks (Reprodutibilidade Experimental ns-3/5G-LENA/NORI) │
│  [PAPER 5: 2027]    ──► IEEE WCL / OJ-COMS (Letter: Formulação Matemática de Bounding Box Sub-1ms)    │
│  [PAPER 6: 2027/28] ──► IEEE COMST (Survey & SLR: Taxonomia Sistemática de Conflitos Open RAN)         │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Matriz Canônica de Auditoria e Desacoplamento Artigo $\times$ Artigo

### Tabela 1: Matriz Estratégica Completa dos 6 Manuscritos

| Dimensão Editorial | Paper 1 (H-RDL Flagship) | Paper 2 (CA-RDL Cognitive) | Paper 3 (Multi-Tier Governance) | Paper 4 (Reproducible Framework) | Paper 5 (Mathematical Letter) | Paper 6 (Comprehensive Survey) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Periódico Alvo** | **IEEE TNSM** (Q1, IF ~5.3) | **IEEE TCCN** (Q1, IF ~5.0) | **IEEE Network** (Q1, IF ~8.9) | **Elsevier COMNET** (Q1, IF ~4.4) | **IEEE WCL / OJ-COMS** (Q2/Q1) | **IEEE COMST** (Q1, IF ~35.6) |
| **Prazo de Submissão** | **Outubro–Novembro / 2026** | **Dezembro/2026 – Fevereiro/2027** | **Maio–Julho / 2027** | **Agosto–Outubro / 2027** | **Fluxo Contínuo 2027** | **2027–2028** |
| **Título Definitivo** | *Safe Closed-Loop Multi-xApp Conflict Mitigation in Open RAN through Hierarchical Arbitration and Deterministic Safety Guards* | *Context-Aware Multi-xApp Coordination in Open RAN through Knowledge Graphs and Constrained Multi-Agent Reinforcement Learning* | *Hierarchical Multi-Timescale Conflict Governance for Open RAN: From Non-RT Policies to Real-Time Distributed Units* | *A Fully Reproducible Co-Simulation Framework for Safe Multi-xApp Conflict Arbitration in Open RAN* | *Sub-Millisecond Bounding-Box Envelopes for Safe Real-Time Distributed App Preemption in Open RAN* | *A Survey and Taxonomy on Conflict Management, Dynamic Arbitration, and Safe Coordination in Open RAN* |
| **Contribuição Inédita Central** | Arquitetura Near-RT determinística que detecta colisões multi-xApp, arbitra via matriz multiobjetivo (TVS/EEVS) e garante $\text{Unsafe} \equiv 0$ com latência sub-milissegundo ($T_{\text{dec}} \ll T_{\text{NearRT}}$). | Coordenação contextual via Grafo de Conhecimento heterogêneo ($\kappa$) e Safe-MAPPO (CMDP com multiplicadores Lagrangianos) sob ambientes estocásticos densos e multi-fatia. | Modelo unificado de governança em 3 escalas temporais ($r\text{App} > 1\text{s} \leftrightarrow x\text{App} \approx 10\text{-}100\text{ms} \leftrightarrow d\text{App} < 1\text{ms}$ TTI) com barramento A1-P/E2. | Pipeline de co-simulação aberto (ns-3.48 + 5G-LENA + NORI + OSC Near-RT RIC) com decodificação ASN.1 APER estrita e datasets brutos para reprodutibilidade. | Formulação matemática da projeção do envelope de segurança $\Omega_{\text{dApp}}$ garantindo limites de PRB/potência no TTI sem violar a estabilidade macro do RIC. | Revisão sistemática da literatura (SLR PRISMA) classificando taxonomias de conflitos (C1–C5), mecanismos de mediação e lacunas normativas O-RAN WG3/WG2. |
| **Cenários Experimentais Suportados** | **B0 vs H-RDL, S1 (PRB Collision), S2 (Energy vs QoS), S3 (TVS Coupling), S8 (Validação Principal de Circuito Fechado E2AP/E2SM-KPM/RC)** + **Suite de Ablação A0–A5** + **Micro-benchmark de Escalabilidade Algorítmica de Decisão (2 a 100 propostas concorrentes)** [Simulação física ns-3 com até 6 xApps ativas de referência]. | **S6 (Conflict Storm), S9 (NTN LEO), S10 (UAV Swarm), S11 (V2X), S12 (TSN), S14 (ISAC)** + Curvas de Treinamento MAPPO. | **Cenário B (Two-Tier dApp) + Injeção de Políticas A1-P sintéticas** + Validação de Hierarquia de Controle rApp/xApp/dApp. | **Suite Completa S0–S15 + 30 Sementes Físicas** + Scripts de Automação de Testbed e Benchmarks de CPU/Memória. | **Micro-benchmarks de TTI (0.25ms / 0.5ms)** sob rajadas de preempção URLLC sobre eMBB com Bounding Box. | Não aplicável (SLR + Análise Bibliométrica + Mapeamento de Testbeds Globais). |
| **Formato & Limite de Páginas** | Máx. 10 páginas (IEEE Double Column, sem excess page fees). | Máx. 13 páginas (regular submission, IEEE Double Column). | 6–8 páginas (estilo Magazine, linguagem acessível, figuras conceituais de alto impacto). | 15–22 páginas (formato Elsevier Single/Double Column). | 4–5 páginas (IEEE Transactions Letter / OJ-COMS Track). | 25–35 páginas (IEEE COMST), análise exaustiva e taxonomia formal. |
| **Fronteira de Isolamento (Zero Overlap)** | Foco estrito em **governança determinística, heurísticas de prioridade e safety guards fixos**. Sem menção a MAPPO ou Grafos Cais. | Foco estrito em **aprendizado por reforço multiagente restrito (Safe-RL), representação em grafos e envelopes dinâmicos**. | Foco em **padronização O-RAN, políticas de longo prazo e decomposição de timescales**. | Foco em **engenharia de software de rede, codecs ASN.1, harness de testes e reprodutibilidade aberta**. | Foco em **prova analítica e tempo real estrito (< 1ms)** na O-DU, isolado da pilha do Near-RT RIC. | Foco em **síntese do estado da arte global e categorização metodológica**, sem resultados experimentais primários. |

---

## 3. Diretrizes de Normalização e Saneamento para o Paper 1 (IEEE TNSM)

### 3.1. Desambiguação Numérica do Orçamento Temporal ($T_{\text{Budget}}$)

Fica terminantemente proibido misturar métricas de latência com definições heterogêneas no Paper 1. O manuscrito deve apresentar a decomposição formal:

$$\boxed{T_{\text{inference}} \ll T_{\text{arbitration}} < T_{\text{pipeline}} \ll T_{\text{E2E}} \le T_{\text{NearRT}}^{\max}}$$

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                DECOMPOSIÇÃO TEMPORAL DE CIRCUITO FECHADO                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. T_inference = 0.0523 ms (52.3 µs)                                                             │
│    Tempo puro de execução da matriz de prioridades determinística TVS/EEVS no H-RDL.             │
│                                                                                                  │
│ 2. T_arbitration = 0.103 ms a 0.262 ms (103 µs - 262 µs)                                         │
│    Ciclo completo: Detecção formal C1-C5 + Resolução de Conflito + Validação de Safety Guard.    │
│                                                                                                  │
│ 3. T_pipeline = 14.20 ms (Pipeline Near-RT Interno)                                              │
│    Janela de Agregação (W_sync = 10ms) + Ingestão KPM APER + Arbitragem + Codificação E2SM-RC.  │
│                                                                                                  │
│ 4. T_E2E = 18.50 ms a 32.38 ms (Latência Fim-a-Fim de Controle-para-Efeito)                     │
│    Loop fechado completo: Telemetria da RAN -> SCTP -> Near-RT RIC -> E2SM-RC -> ACK -> RAN.   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

> **Aviso de Isolamento:** O valor de **$14{,}39\text{ ms}$** refere-se exclusivamente à inferência da rede neural Safe-MAPPO do CA-RDL (Fase 2) e **não deve constar no Paper 1**, garantindo que o H-RDL seja avaliado como solução determinística de latência sub-milissegundo ($T_{\text{arbitration}} \le 0{,}262\text{ ms}$).

---

### 3.2. Saneamento Terminológico e Assertivas Normativas

| Termo Original no Repositório | Substituição Editorial Obrigatória para IEEE TNSM | Justificativa de Rigor Científico |
| :--- | :--- | :--- |
| *"Homologado pelo O-RAN WG2 / WG3"* | **"Implemented in strict compliance with O-RAN WG3 E2SM-RC v01.03 and E2SM-KPM v02.03 specifications"** | Evita a alegação de certificação institucional formal pela O-RAN Alliance. |
| *"100% Validado / 100% Operacional"* | **"Demonstrating 0.0% residual conflict rate and 100% safety bound satisfaction across all evaluated N=30 physical seeds"** | Converte hipérboles em evidências estatísticas objetivas e delimitadas. |
| *"Provably Safe Conflict Mitigation"* | **"Safe Closed-Loop Multi-xApp Conflict Mitigation through Deterministic Safety Guards"** | Elimina a exigência de provas formais de estabilidade analítica de Lyapunov. |
| *"Zero Dados Sintéticos"* | **"Empirically derived from 3GPP TR 38.901 physical-layer simulations in ns-3/5G-LENA and real ASN.1 APER traces"** | Linguagem padrão e rigorosa em publicações IEEE Transactions. |

---

### 3.3. Formalização Matemática do Deterministic Safety Guard

No Paper 1, a garantia de segurança física é formalizada através do operador de projeção convexa $G: \mathcal{A} \to \Omega_{\text{safe}}$:

$$\mathbf{a}_t^{\text{final}} = G(\mathbf{a}_t^{\text{proposed}}) = \arg\min_{\mathbf{a} \in \Omega_{\text{safe}}} \|\mathbf{a} - \mathbf{a}_t^{\text{proposed}}\|_2^2$$

onde o conjunto admissível seguro $\Omega_{\text{safe}}$ é delimitado pelas restrições físicas conjuntas da RAN:

$$\Omega_{\text{safe}} = \left\{ \mathbf{a} = (\mathbf{r}_{\text{PRB}}, P_{\text{tx}}) \mid \sum_{s \in \mathcal{S}} r_{\text{PRB}}^{(s)} \le 1.0, \; r_{\text{PRB}}^{(\text{URLLC})} \ge r_{\min}, \; P_{\min} \le P_{\text{tx}} \le P_{\max} \right\}$$

Essa formalização assegura que **toda ação despachada via E2SM-RC pertence obrigatoriamente a $\Omega_{\text{safe}}$**, provendo segurança determinística por construção (*Safety-by-Design*).

---

### 3.4. O Cenário S8 como Validação Canônica de Circuito Fechado (Closed-Loop Validation Pillar)

O **Cenário S8 (Real NORI Closed Loop E2AP/E2SM)** constitui a evidência empírica principal de fechamento causal do Paper 1:

1. **Topologia de Malha Fechada Completa:**
   $$\text{ns-3/5G-LENA (O-DU/O-CU)} \xrightarrow[\text{E2SM-KPM v3.0}]{\text{SCTP:36422}} \text{Near-RT RIC} \xrightarrow{\text{H-RDL Arbitrage}} \text{Safety Guard} \xrightarrow[\text{E2SM-RC Format 1}]{\text{RIC\_CONTROL}} \text{E2 Agent} \xrightarrow{\text{RIC\_CONTROL\_ACK}} \text{MAC Scheduler}$$
2. **Fechamento Causal Comprovado:**
   - Taxa de Efeito Causal Confiável: $\text{CRE} = 100{,}0\%$.
   - Confirmação não-repudiável via captura de socket real (`experiments/results/traces/live_e2_loopback_capture.pcap`).
   - Latência fim-a-fim de malha fechada medida: $T_{\text{E2E}} = 32{,}38\text{ ms} \ll T_{\text{NearRT}}^{\max} (100\text{ ms})$.

### 3.5. Desambiguação Metodológica da Escalabilidade: Micro-Benchmark vs Simulação Física

Para prevenir qualquer ambiguidade durante a revisão por pares na IEEE TNSM, o manuscrito estabelece a separação categórica entre:

* **Simulação Física de Rede no ns-3/5G-LENA:**
  - Opera com **até 6 xApps ativas simultâneas** de referência (`xSlice`, `Energy Saving`, `Traffic Steering`, `MIMO Beamformer`, `ISAC Radar`, `Safety Guard / Zero-Trust`) atuando sobre 1 a 4 gNodeBs e fatias heterogêneas (URLLC, eMBB, mMTC). Esse limite reflete a capacidade realista de instanciação semântica concorrente na pilha física de rádio.
* **Micro-Benchmark de Escalabilidade Computacional do Motor (GATE 3):**
  - Avalia o pipeline de decisão de software isoladamente sob estresse sintético escalonado de **$N \in \{2, 5, 10, 20, 50, 100\}$ propostas de xApps** injetadas por ciclo de arbitragem (`scripts/benchmark_measured_scalability_100xapps.py`).
  - Demonstra que o tempo de resolução permanece linear $\mathcal{O}(N)$ e rigorosamente contido em $T_{\text{arbitration}} \le 0{,}262\text{ ms}$ mesmo sob o estresse extremo de 100 propostas concorrentes.

---

## 4. Tabela Sistemática de Comparação com o Estado da Arte (SOTA)

### Tabela 2: Comparativo Sistemático entre o H-RDL e o Estado da Arte em Coordenação Open RAN

| Abordagem / Framework | Paradigma de Controle | Suporte a Conflitos Concorrentes | Latência de Arbitragem ($T_{\text{dec}}$) | Garantia de Safety Guard ($\text{Unsafe} \equiv 0$) | Codec ASN.1 APER Real | Mecanismo de Rollback / Timeout E2 | Validação com Fatias Heterogêneas (URLLC/eMBB) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Uncoordinated (Baseline B0)** | Desgovernado (Direct E2) | ❌ Colisão Crítica | N/A (Sem mediação) | ❌ Violações Severas (36,7%) | ❌ Genérico | ❌ Ausente | ❌ Degradação de SLA |
| **Static FCFS / Priority Queue** | Fila Estática de Chegada | ⚠️ Rejeição Cega | $< 0,1\text{ ms}$ | ❌ Não assegurado | ❌ Mocks | ❌ Ausente | ❌ Inanição de eMBB |
| **O-RAN WG3 Non-RT Broker** | Mediação Reativa Non-RT | ⚠️ Apenas Longo Prazo | $> 1000\text{ ms}$ | ⚠️ Parcial (A1 Policies) | ⚠️ JSON/REST | ❌ Sem Rollback | ⚠️ Limitado a cotas macro |
| **ColO-RAN (Bonati et al., 2021)** | Emulação de Testbed DRL | ⚠️ Conflitos Binários | $10\text{--}50\text{ ms}$ | ❌ Probabilístico (Soft penalty) | ⚠️ Customizado | ❌ Ausente | ⚠️ eMBB predominante |
| **Sl-ORAN (D'Oro et al., 2022)** | Dynamic Slicing Controller | ⚠️ Limitado a PRB Slicing | $5\text{--}15\text{ ms}$ | ⚠️ Sem Hard Boundary | ⚠️ Protobuf | ❌ Ausente | ⚠️ Apenas Slicing |
| **Proposta H-RDL (Fase 1)** | **Hierárquico Determinístico** | **✅ Multi-xApp (C1 a C5)** | **$0{,}052\text{--}0{,}262\text{ ms}$** | **✅ Determinístico ($\text{Unsafe} \equiv 0$)** | **✅ E2SM-RC Format 1 (19 B)** | **✅ ACK Tracker + Rollback** | **✅ URLLC + eMBB + mMTC** |

---

## 5. Estrutura Canônica da Seção *Threats to Validity*

O Paper 1 integrará uma subseção explícita estruturada em 4 pilares:

1. **Internal Validity (Validade Interna):**
   - *Mitigação:* Avaliação estocástica sobre 30 sementes físicas pseudoaleatórias independentes (`seeds 1001 a 1030`), medição de latência via relógio monotônico de alta resolução (`time.perf_counter()`), e eliminação de efeitos transientes de inicialização (janela de aquecimento de $5\text{ s}$).
2. **External Validity (Validade Externa):**
   - *Mitigação:* Emprego da pilha padrão de rádio 3GPP NR no simulador 5G-LENA/ns-3 com modelos de canal padronizados (3GPP TR 38.901 UMi Street Canyon, desvanecimento rápido e sombreamento log-normal de $\sigma = 4\text{ dB}$).
3. **Construct Validity (Validade de Construto):**
   - *Mitigação:* Operacionalização estrita das métricas de conflito ($CRR$, $CRE$, $Action\ Churn$, $Jain\ Fairness$) e codificação E2SM em conformidade com as definições formais dos grupos de trabalho O-RAN WG3.
4. **Reproducibility & Open Science (Reprodutibilidade):**
   - *Mitigação:* Disponibilização pública de todo o código-fonte, scripts de compilação CMake/Ninja, sementes, datasets brutos e manifestos com hashes SHA-256 no repositório [XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1).

---

## 6. Cronograma de Submissão e Marcos de Execução (Paper 1 TNSM)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          CRONOGRAMA DE SUBMISSÃO DO PAPER 1 (IEEE TNSM)                        │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│  [FASE 1: 28/Set - 05/Out] Congelamento da Base de Dados & Tabela SOTA Formalizada             │
│  [FASE 2: 06/Out - 15/Out] Redação da Seção 3 (Arquitetura) e Seção 4 (Modelagem Matemática)   │
│  [FASE 3: 16/Out - 25/Out] Consolidação das Figuras Vetoriais & Seção 5 (Resultados N=30)      │
│  [FASE 4: 26/Out - 05/Nov] Redação de Threats to Validity, Introdução e Trabalhos Relacionados │
│  [FASE 5: 06/Nov - 12/Nov] Revisão de Estilo IEEE, Verificação de Limite de 10 Páginas e LaTeX│
│  [FASE 6: 15/Nov/2026]     Submissão Oficial no Portal IEEE TNSM (ScholarOne Manuscripts)     │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```
