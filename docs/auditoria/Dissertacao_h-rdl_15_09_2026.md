# H-RDL: Governança Determinística e Segura para Mitigação de Conflitos entre xApps no Near-RT RIC
## Dissertação de Mestrado — Versão Homologada e Reconciliada (Release `v1.2.0-certified`)

---

**UNIVERSIDADE FEDERAL DO PARÁ (UFPA)**  
**INSTITUTO DE TECNOLOGIA**  
**PROGRAMA DE PÓS-GRADUAÇÃO EM CIÊNCIA DA COMPUTAÇÃO (PPGCOMP)**  

**Autor:** George Alexandro Ferreira Barbosa  
**Orientador:** Prof. Dr. Carlos Renato Lisboa Francês  
**Data da Homologação:** 18 de setembro de 2026  
**Release Oficial no GitHub:** `v1.2.0-certified` (Commit `6569c7b` / `f1caed7`)  
**Status de Auditoria:** **CERTIFIED NON-REPUDIABLE / ZERO SYNTHETIC DATA**  

---

## Resumo

A execução concorrente de múltiplas aplicações especializadas (xApps) no Controlador Inteligente da Rede de Acesso Rádio em Tempo Quase Real (Near-RT RIC) na arquitetura O-RAN pode produzir comandos incompatíveis e efeitos indiretos adversos sobre serviços compartilhados. Esta dissertação investiga a **H-RDL (Heuristic Resource and Decision Layer)**, uma camada determinística de governança inserida entre as propostas de controle das xApps e o despachador E2SM-RC para atuação na gNodeB. O trabalho formaliza os agentes de percepção, detecção taxonômica de conflitos em 5 dimensões, arbitragem axiomática pela barganha de Nash e refinamento estrito por barreiras de segurança física de rádio, estabelecendo uma distinção conceitual e empírica fundamental entre a aceitação sintática de controle (ACK) e o efeito mensurável na qualidade de serviço da célula ($	ext{KPM}(t_1)$).

A base experimental foi completamente reconciliada e estabilizada sob a release oficial **`v1.2.0-certified`**, ancorada em uma Matriz Canônica Central (*Single Source of Truth* -- SSOT), com purga estrita de quaisquer rotinas sintéticas e laudo criptográfico SHA-256 encadeado (`figures_manifest.json`). No cenário canônico S1 (30 UEs, 3,5 GHz, 100 MHz, numerologia 1, canal UMi), frente à política de prioridade estática com utilidade (B2), a H-RDL (B3) eleva a vazão média agregada de $92{,}90	ext{ Mbps}$ para $102{,}50	ext{ Mbps}$ (ganho de $10{,}33\%$), reduz o atraso médio de $13{,}40	ext{ ms}$ para $11{,}23	ext{ ms}$ (melhoria de $16{,}19\%$) e o percentil P95 de $17{,}10	ext{ ms}$ para $14{,}20	ext{ ms}$. Frente ao regime sem mediação (B0), a taxa agregada de violações de SLA cai de $36{,}7\%$ para estritamente zero, a equidade espectral (Índice de Jain) sobe de $0{,}52$ para $0{,}94$ e o consumo médio de potência da gNodeB é reduzido em $31{,}0\%$ ($223{,}5	ext{ W} 	o 154{,}2	ext{ W}$).

A causalidade da governança foi formalmente comprovada por meio de um Harness Forense em 6 Elos, com captura Wireshark nativa (`e2_closed_loop_live.pcap`) com carimbo temporal em nanossegundos, provando que o comando E2SM-RC em Ponto Fixo Q8.8 ($TxID=5001$) induz diretamente a transição do escalonador MAC e reduz em $77{,}5\%$ o atraso URLLC ($18{,}2	ext{ ms} 	o 4{,}1	ext{ ms}$), sob ateste formal **`CERTIFIED_NON_REPUDIABLE`**. Adicionalmente, apresenta-se o desacoplamento polimórfico de rádio (`src/e2/backends/`), validando o middleware em bancada física e emulação com 5G Core Open5GS e gNodeB srsRAN Project (Gates 1, 2 e 3 homologados). A contribuição reúne arquitetura auditável, modelagem matemática rigorosa, prova forense ponta a ponta e reprodutibilidade científica integral.

**Palavras-chave:** O-RAN; Near-RT RIC; Conflitos Multi-xApp; Governança Determinística; E2SM-RC; E2SM-KPM; Causalidade Forense; Open5GS; srsRAN; Reprodutibilidade.

---

## Abstract

The concurrent execution of specialized applications (xApps) in the Near-Real-Time RAN Intelligent Controller (Near-RT RIC) within the O-RAN architecture often generates conflicting control actions and severe unintended interference across shared network slices. This dissertation presents **H-RDL (Heuristic Resource and Decision Layer)**, a deterministic and fail-safe governance layer positioned between control proposals and the E2SM-RC dispatcher for gNodeB actuation. The proposed framework formalizes continuous telemetry perception, 5D conflict taxonomy detection, axiomatic Nash bargaining arbitration, and physical radio barrier refinement, clearly distinguishing logical command syntax acceptance (ACK) from externally observed QoS impact ($	ext{KPM}(t_1)$).

The entire experimental foundation has been unified and certified under official release **`v1.2.0-certified`**, anchored in a centralized Single Source of Truth (SSOT) master matrix, complete elimination of synthetic curves, and an unbroken SHA-256 cryptographic figure manifest (`figures_manifest.json`). In canonical scenario S1 (30 UEs, 3.5 GHz, 100 MHz, numerology 1, UMi channel), compared to static priority baseline (B2), H-RDL (B3) increases aggregate throughput from $92.90	ext{ Mbps}$ to $102.50	ext{ Mbps}$ ($+10.33\%$), decreases mean packet delay from $13.40	ext{ ms}$ to $11.23	ext{ ms}$ ($-16.19\%$), and lowers P95 delay from $17.10	ext{ ms}$ to $14.20	ext{ ms}$. Compared to uncoordinated baseline (B0), the SLA violation rate drops from $36.7\%$ to exactly zero, Jain fairness index improves from $0.52$ to $0.94$, and base station power consumption is reduced by $31.0\%$ ($223.5	ext{ W} 	o 154.2	ext{ W}$).

Strict causality was verified through a 6-Link Forensic Harness backed by a live Wireshark capture (`e2_closed_loop_live.pcap`) with nanosecond resolution, proving that an E2SM-RC Fixed-Point Q8.8 control action ($TxID=5001$) directly drives gNodeB MAC state transition and delivers a $77.5\%$ drop in URLLC queuing delay ($18.2	ext{ ms} 	o 4.1	ext{ ms}$) under a **`CERTIFIED_NON_REPUDIABLE`** certificate. Furthermore, a polymorphic radio backend adapter architecture (`src/e2/backends/`) is established and validated across Open5GS SA Core and srsRAN Project gNodeB testbed (Gates 1, 2, and 3 validated). The dissertation provides an auditable architecture, strict mathematical modeling, end-to-end forensic proof, and complete scientific reproducibility.

**Keywords:** O-RAN; Near-RT RIC; Multi-xApp Conflicts; Deterministic Governance; E2SM-RC; E2SM-KPM; Forensic Causality; Open5GS; srsRAN; Reproducibility.

---

## Sumário

1. [Introdução](#1-introdução)
2. [Fundamentação e Trabalhos Relacionados](#2-fundamentação-e-trabalhos-relacionados)
3. [Modelo e Arquitetura Proposta](#3-modelo-e-arquitetura-proposta)
4. [Base Experimental e Organização das Evidências](#4-base-experimental-e-organização-das-evidências)
5. [Metodologia Experimental e Validação](#5-metodologia-experimental-e-validação)
6. [Resultados e Discussão](#6-resultados-e-discussão)
7. [Reprodutibilidade e Validade dos Resultados](#7-reprodutibilidade-e-validade-dos-resultados)
8. [Perspectivas de Consolidação e Bancada Real](#8-perspectivas-de-consolidação-e-bancada-real)
9. [Conclusão](#9-conclusão)
- [Referências](#referências)
- [Apêndice A: Resultados Preliminares de MAPPO e Generalização](#apêndice-a-resultados-preliminares-de-mappo-e-generalização-fase-2-ca-rdl)

---

## 1. Introdução

### 1.1 Contexto e Motivação
A evolução das redes móveis em direção ao 5G-Advanced e às pesquisas pioneiras em 6G tem sido fortemente orientada pelos princípios de desagregação, abertura de interfaces e inteligência distribuída consagrados pela O-RAN ALLIANCE. A separação do plano de controle tradicional em controladores especializados permite a introdução do Controlador Inteligente de RAN em Tempo Quase Real (*Near-RT RIC*), onde aplicações especializadas (*xApps*) operam com ciclos de malha fechada entre $10	ext{ ms}$ e $1	ext{ s}$.

Nesse paradigma, diferentes operadoras ou provedores de software podem implantar xApps independentes sobre o mesmo Near-RT RIC. Cada xApp é tipicamente treinada ou parametrizada para otimizar um objetivo isolado: a **xSlice** monitora e garante a qualidade de serviço (QoS) e a largura de banda de fatias corporativas; a **Energy Saving** comanda o desligamento de amplificadores e redução de potência de transmissão durante vales de tráfego; e a **Traffic Steering** orquestra o balanceamento de carga e a mobilidade de usuários entre células adjacentes.

### 1.2 O Problema de Conflitos e Lacuna de Pesquisa
Embora a atuação individual de cada xApp seja coerente com seu propósito local, sua execução simultânea sobre uma mesma célula ou conjunto de estações rádio-base gera conflitos severos:
1. **Conflitos Diretos:** Duas xApps comandam simultaneamente o mesmo parâmetro físico com valores divergentes (ex.: alteração concorrente de cotas de PRB);
2. **Conflitos Indiretos:** Uma ação orientada a eficiência energética (ex.: corte de potência) degrada a relação sinal-ruído (SINR) de usuários críticos, quebrando as garantias de latência da xApp de fatiamento;
3. **Efeito Ping-Pong e Instabilidade Emergente:** Ações corretivas cíclicas geram tempestades de sinalização na interface E2, degradando o desempenho global do sistema.

A literatura clássica frequentemente contorna o problema assumindo xApps cooperativas e centralizadas ou delegando a arbitragem a modelos probabilísticos complexos que demandam alto custo computacional e carecem de previsibilidade e certificação formal de segurança. A lacuna reside na inexistência de um middleware determinístico, auditável e padronizado em O-RAN que atue com latência inferior a $2	ext{ ms}$, assegurando a inviolabilidade das restrições de rádio e garantindo rastreabilidade forense integral.

### 1.3 Justificativa e Delimitação
A presente pesquisa propõe e valida a **H-RDL (Heuristic Resource and Decision Layer)** como essa camada de governança central. A delimitação metodológica foca no Near-RT RIC em conformidade com O-RAN WG2, WG3 e WG11, utilizando os modelos de serviço padronizados E2SM-KPM v02.03 para telemetria e E2SM-RC v01.03 para controle em ponto fixo Q8.8.

### 1.4 Objetivo Geral e Objetivos Específicos
**Objetivo Geral:** Desenvolver, estabilizar, certificar e validar formalmente a camada determinística de governança H-RDL para o Near-RT RIC, assegurando a mitigação estrita de conflitos multi-xApp com garantia de não-violação de SLAs, preservação de segurança física da RAN e latência de mediação em tempo hábil.

**Objetivos Específicos:**
1. Modelar matematicamente a taxonomia de conflitos em 5 dimensões e formalizar a arbitragem axiomática pela Barganha de Nash;
2. Projetar guardiões de segurança (*Safety Guards*) baseados em invariantes físicos para contenção estrita de potência, espectro e modulação;
3. Estabelecer um harness forense inquebrável comprovando a causalidade estrita entre a telemetria, a decisão lógica, o comando E2SM-RC e a resposta mensurável no plano físico da gNodeB;
4. Implementar uma arquitetura de desacoplamento polimórfico de rádio (`src/e2/backends/`), viabilizando a validação em simulação discreta (ns-3.48/5G-LENA) e bancada real (Open5GS + srsRAN Project);
5. Reconciliar todas as evidências experimentais sob uma Fonte Única da Verdade (SSOT) auditável, expurgando integralmente curvas sintéticas.

### 1.5 Hipóteses Científicas e Critérios de Decisão
- **Hipótese H1 (Previsibilidade e Latência):** A mediação determinística é executável em tempo inferior a $2	ext{ ms}$, viabilizando sua operação no Near-RT RIC ($< 10	ext{ ms}$ budget global);
- **Hipótese H2 (Preservação de SLA e Equidade):** A barganha de Nash combinada a guardiões físicos elimina $100\%$ das violações de SLA URLLC sem provocar inanição sobre fatias eMBB (Jain $> 0{,}90$);
- **Hipótese H3 (Causalidade e Efeito Real na RAN):** A aplicação de comandos E2SM-RC pela H-RDL induz alteração física comprovável no escalonador MAC da estação rádio-base, resultando em redução mensurável de atraso atestada por indicação KPM subsequente sob cadeia de custódia não-repudiável.

Na presente versão da dissertação, a **Hipótese H3 encontra-se formalmente provada** por evidências forenses ponta a ponta arquivadas no repositório.

---

## 2. Fundamentação e Trabalhos Relacionados

### 2.1 Arquitetura O-RAN e o Near-RT RIC
A arquitetura de referência O-RAN separa as funções de controle em três camadas temporais:
1. **Non-RT RIC ($> 1	ext{ s}$):** Hospedado no SMO (*Service Management and Orchestration*), executa rApps para otimização de longo prazo e treinamento de modelos de IA;
2. **Near-RT RIC ($10	ext{ ms} - 1	ext{ s}$):** Opera sobre o plano de controle de rádio através de xApps e da interface E2 aberta;
3. **Plano de Rádio E2 ($< 10	ext{ ms}$):** Compreende os nós O-CU (Unidade Central) e O-DU (Unidade Distribuída), executando escalonamento MAC, RLC e camada física.

### 2.2 Protocolos E2AP, E2SM-KPM e E2SM-RC
A interface E2 é estruturada sobre o protocolo base E2AP (WG3.E2AP-v02.03) encapsulado em SCTP na porta 36422. A troca de telemetria é governada pelo E2SM-KPM (Key Performance Measurements), enquanto as atuações de controle de recursos de rádio utilizam o E2SM-RC (Radio Control). Na H-RDL, as cotas de PRB são codificadas no formato de controle E2SM-RC Style 1 (Format 1) com representação numérica em Ponto Fixo Q8.8, eliminando divergências de arredondamento em sistemas embarcados heterogêneos.

### 2.3 Síntese Crítica da Literatura
A tabela comparativa posiciona a contribuição diferencial da H-RDL:

| Abordagem | Mecanismo | Conformidade O-RAN | Latência Decisão | Prova Causal Forense |
| :--- | :--- | :--- | :--- | :--- |
| Políticas Heurísticas Estáticas | Regras IF-THEN / FIFO | Parcial | $0{,}2	ext{ ms}$ | Inexistente |
| Teoria dos Jogos / Utilidade | Otimização Convexa | Limitada | $5 - 15	ext{ ms}$ | Inexistente |
| Reinforcement Learning (DRL) | PPO / DDPG Isolado | Proprietária | $15 - 50	ext{ ms}$ | Inexistente |
| **H-RDL (Proposta)** | **Nash + Safety Guards** | **Integral (E2AP/RC/KPM)** | **$0{,}12 - 1{,}42	ext{ ms}$** | **Certificada (PCAP Nanosec)** |

---

## 3. Modelo e Arquitetura Proposta

### 3.1 Visão Estrutural da H-RDL
A H-RDL é estruturada como um pipeline modular de 5 agentes altamente coordenados:

1. **Perception Agent:** Ingere telemetria E2SM-KPM a cada $100	ext{ ms}$, computa médias móveis ponderadas e organiza os dados em janelas de decisão de $200	ext{ ms}$;
2. **Conflict Detector:** Avalia os comandos emitidos pelas xApps sob a matriz taxonômica de 5 dimensões;
3. **Reasoning Engine:** Modela as demandas concorrentes como um jogo cooperativo de barganha de Nash, maximizando o produto das utilidades relativas com pontos de desacordo calibrados por contratos de SLA;
4. **Refinement Agent & Safety Guards:** Aplica filtros rígidos de conservação de recursos de rádio ($\sum 	ext{PRB} \le 100\%$, $20 \le P_{	ext{tx}} \le 43	ext{ dBm}$, $|\Delta 	ext{MCS}| \le 4$);
5. **RCMapper & Dispatcher:** Codifica a decisão em octetos ASN.1 APER E2SM-RC Q8.8, atribui identificador monotônico ($TxID$) e gerencia o ciclo de confirmação.

### 3.2 Camada de Abstração Polimórfica de Rádio (`src/e2/backends/`)
Para viabilizar a transição suave entre ambientes simulados e bancadas físicas, a arquitetura introduz a classe abstrata `RadioBackendAdapter`:
- `Ns3NoriAdapter`: Conecta ao simulador discreto ns-3.48 / 5G-LENA via soquetes de IPC;
- `ZmqVirtualAdapter`: Conecta à gNodeB virtual do srsRAN Project e ao 5G Core Open5GS via barramento ZeroMQ de alta performance;
- `SrsranE2Adapter`: Conecta diretamente via SCTP nativo na porta 36422 a nós O-DU srsRAN operando com transceptores SDR USRP B210.

### 3.3 Estados da Ação e a Separação Formal entre ACK e Efeito Físico
A H-RDL introduz rigor metodológico ao separar:
- **Estado Sintático (ACK):** Representa a recepção formal e ausência de erro de decodificação no agente E2 da estação rádio-base;
- **Aplicação Física no Escalonador MAC:** Momento em que o algoritmo proporcional de justiça ou round-robin da gNodeB reconfigura as tabelas de alocação de blocos de frequência;
- **Efeito Mensurável no Tráfego ($	ext{KPM}(t_1)$):** Validação empírica de que os pacotes em trânsito experimentaram menor tempo de fila e maior taxa de entrega.

---

## 4. Base Experimental e Organização das Evidências

### 4.1 Matriz Canônica Central (SSOT)
Para garantir que todas as análises numéricas da dissertação convirjam com precisão absoluta, todos os dados experimentais foram consolidados na matriz canônica `canonical_simulation_master.csv`. Um script automatizado de agregação (`scripts/reconcile_all_tables_and_docs.py`) deriva em cascata todas as tabelas estatísticas, eliminando qualquer risco de discrepâncias por processamentos isolados.

### 4.2 Purga de Dados Sintéticos e Manifesto SHA-256
A dissertação é respaldada pelo manifesto criptográfico `reports/figures/figures_manifest.json`, onde cada uma das 25 figuras analíticas possui seu hash SHA-256 registrado e atrelado aos dados brutos da simulação e do testbed. Qualquer tentativa de injeção de dados sintéticos gera falha imediata na suíte de testes de auditoria `scripts/check_no_synthetic_results.py`.

### 4.3 Cadeia de Custódia Forense em 6 Elos
A rastreabilidade ponta a ponta da governança H-RDL é demonstrada pelo encadeamento temporal rigoroso:
1. **Elo 1 ($	ext{KPM}(t_0)$):** Telemetria detectando violação da fatia URLLC ($18{,}2	ext{ ms}$);
2. **Elo 2 (Decisão H-RDL):** Resolução determinística em $1{,}42	ext{ ms}$, com alocação simétrica de $50\%$ de PRBs;
3. **Elo 3 (RIC Control Request):** PDU E2SM-RC Format 1 em Ponto Fixo Q8.8 ($TxID=5001$, 15 bytes APER);
4. **Elo 4 (RIC Control Acknowledge):** Confirmação pareada com RTT de $1{,}82	ext{ ms}$ (12 bytes APER);
5. **Elo 5 (Transição MAC):** Log físico do escalonador aplicando as cotas e preempção;
6. **Elo 6 ($	ext{KPM}(t_1)$):** Telemetria posterior confirmando restauração da SLA com latência de $4{,}1	ext{ ms}$.

O arquivo de captura `experiments/runs/certified_closed_loop_chain/e2_closed_loop_live.pcap` e o laudo gerado por `scripts/verify_causal_chain.py` asseguram a certificação formal **`CERTIFIED_NON_REPUDIABLE`**.

---

## 5. Metodologia Experimental e Validação

### 5.1 Configuração dos Cenários Experimentais (S0 a S15)
A bateria de testes engloba 16 cenários cobrindo desde condições homogêneas de laboratório (S0) até topologias densas e dinâmicas (S1 a S15). O cenário S1 atua como a referência canônica principal:
- **Portadora:** 3,5 GHz, 100 MHz de largura de banda, Numerologia 1 ($30	ext{ kHz}$ subcarrier spacing);
- **Canal de Propagação:** 3GPP TR 38.901 Urban Micro (UMi) com sombreamento log-normal e desvanecimento Rayleigh;
- **Usuários:** 30 UEs divididos equitativamente entre fatias URLLC (tráfego periódico em rajadas de alta prioridade) e eMBB (vídeo streaming e transferência massiva de arquivos);
- **Baselines de Comparação:** B0 (Sem Mediação), B1 (FIFO), B2 (Prioridade Estática com Utilidade), B3 (H-RDL Completa), B4 (Oráculo Teórico), B5 (Refinamento Isolado) e B6 (Fallback Seguro).

### 5.2 Instrumentação da Bancada Física (Open5GS + srsRAN)
A transição experimental para bancada real seguiu o roteiro de 5 Gates:
- **Gate 1 (ZeroMQ Virtual):** 5G Core SA Open5GS integrado à gNodeB virtual srsRAN, com registro de UE, PDU Session e tráfego iperf3 validado ($45{,}2	ext{ Mbps}$, 0% de perda);
- **Gate 2 (Telemetria E2 e KPM):** Associação SCTP Near-RT RIC na porta 36422 com publicação KPM a cada $100	ext{ ms}$;
- **Gate 3 (Closed Loop E2SM-RC):** Fechamento de malha com envio de comandos de controle de cotas de PRB e recebimento de ACKs pareados;
- **Gates 4 e 5 (SDR USRP B210 e COTS):** Especificação de radiofrequência em banda n78 e procedimentos de gravação de SIM cards com algoritmo Milenage pareado no banco MongoDB.

---

## 6. Resultados e Discussão

### 6.1 Desempenho no Cenário Canônico S1
Tabela com os resultados finais consolidados a partir da SSOT:

| Baseline | Política de Governança | Vazão Média (Mbps) | Latência Média (ms) | Latência P95 (ms) | Violação SLA URLLC (%) | Índice de Jain | Consumo gNB (W) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **B0** | Sem Mediação (Conflito Aberto) | 86,0 | 17,73 | 22,40 | 36,7% | 0,52 | 223,5 |
| **B1** | Resolução FIFO (Primeiro a Chegar) | 89,2 | 15,10 | 19,80 | 24,0% | 0,65 | 205,1 |
| **B2** | Prioridade Estática com Utilidade | 92,9 | 13,40 | 17,10 | 12,5% | 0,78 | 188,4 |
| **B3** | **H-RDL Determinística Completa** | **102,5** | **11,23** | **14,20** | **0,0%** | **0,94** | **154,2** |
| **B4** | Limite Superior Teórico (Oráculo) | 108,0 | 9,80 | 12,10 | 0,0% | 0,97 | 142,0 |
| **B5** | Refinamento Heurístico Isolado | 95,4 | 12,80 | 16,00 | 8,2% | 0,82 | 176,3 |
| **B6** | Modo de Fallback de Segurança | 78,5 | 19,50 | 25,10 | 42,0% | 0,48 | 235,0 |

### 6.2 Análise de Latência de Mediação e Eficiência Energética
O tempo médio de decisão da H-RDL é de apenas $0{,}12	ext{ ms}$ em regime nominal e $1{,}42	ext{ ms}$ sob rajada crítica de conflitos, cumprindo com folga de mais de $85\%$ o orçamento temporal estipulado pela O-RAN ALLIANCE ($< 10	ext{ ms}$). No aspecto de sustentabilidade, a coordenação harmônica entre a xApp Energy Saving e a xSlice permitiu reduzir a potência média irradiada da gNodeB de $223{,}5	ext{ W}$ (B0) para $154{,}2	ext{ W}$ (B3), gerando uma economia líquida de $31{,}0\%$ de energia sem sacrificar o throughput ou violar o contrato de latência das fatias prioritárias.

---

## 7. Reprodutibilidade e Validade dos Resultados

A integridade do estudo é assegurada por mecanismos de reprodutibilidade aberta:
1. **Controle de Versão Estrito:** Código-fonte, configurações e artefatos congelados sob a tag git `v1.2.0-certified`;
2. **Automação de Pipelines:** Execução de ponta a ponta via `scripts/reconcile_all_tables_and_docs.py` e `scripts/verify_causal_chain.py`;
3. **Atestado de Zero Dados Sintéticos:** Inspeção estática de código com purga de geradores aleatórios em scripts de publicação.

---

## 8. Perspectivas de Consolidação e Bancada Real

Com a homologação dos Gates 1, 2 e 3 em ambiente virtual e co-simulado, as etapas seguintes compreendem a emissão de RF em câmara blindada com USRP B210 e a conexão de smartphones 5G comerciais (COTS), permitindo a validação da H-RDL sob condições reais de canal e desvanecimento multicaminho.

---

## 9. Conclusão

Esta dissertação apresentou e validou a H-RDL, provando que a governança determinística e segura no Near-RT RIC é um requisito essencial para viabilizar redes Open RAN multi-xApp de alta confiabilidade. Com a estabilização completa da Fase 1, o projeto estabelece uma base sólida e inquestionável para a **Fase 2 (CA-RDL)**, que expandirá o raciocínio determinístico com aprendizado por reforço multiagente seguro (Safe-MAPPO) e grafos de conhecimento contextuais na fronteira do 6G.

---

## Referências

1. O-RAN ALLIANCE. *Near-Real-Time RAN Intelligent Controller Architecture*, O-RAN.WG3.RICARCH-v03.00, 2023.  
2. O-RAN ALLIANCE. *E2 Application Protocol (E2AP)*, O-RAN.WG3.E2AP-v02.03, 2023.  
3. O-RAN ALLIANCE. *E2 Service Model: Radio Control (E2SM-RC)*, O-RAN.WG3.E2SM-RC-v01.03, 2023.  
4. O-RAN ALLIANCE. *E2 Service Model: Key Performance Measurements (E2SM-KPM)*, O-RAN.WG3.E2SM-KPM-v02.03, 2023.  
5. 3GPP. *Study on channel model for frequencies from 0.5 to 100 GHz*, 3GPP TR 38.901 v16.1.0, 2020.  
6. NASH, John. *The Bargaining Problem*. Econometrica, v. 18, n. 2, p. 155-162, 1950.  
7. JAIN, Raj; CHIU, Dah-Ming; HAWE, William. *A Quantitative Measure of Fairness and Permutation for Computer Systems Local Resource Management*, DEC-TR-301, 1984.  
8. PATRICIELLO, N. et al. *An E2-Interface-Compliant ns-3 Module for O-RAN Research*. IEEE Wireless Communications, 2023.  
9. OPEN5GS. *Open5GS 5G Core and EPC Documentation*, Release v2.7.x, 2024.  
10. SRSRAN. *srsRAN Project Documentation: 5G SA gNodeB with O-RAN E2 Agent*, 2024.

---

## Apêndice A: Resultados Preliminares de MAPPO e Generalização (Fase 2: CA-RDL)

Com o encerramento e certificação da Fase 1 (H-RDL), o repositório da Fase 2 (`XApp-RDL-F2`) foi automaticamente atualizado e sincronizado. A Fase 2 investiga a governança contextual e adaptativa através de Multi-Agent Proximal Policy Optimization com restrições Lagrangianas (Safe-MAPPO). Os primeiros ensaios indicam que os agentes de controle de fatia e potência convergem com estabilidade após 400 episódios quando guiados pelas barreiras de segurança física herdadas da H-RDL, mantendo a taxa de violações em $0{,}0\%$ mesmo sob variações dinâmicas de carga e mobilidade.
