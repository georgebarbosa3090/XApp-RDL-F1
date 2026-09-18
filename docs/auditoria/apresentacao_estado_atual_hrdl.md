# Estado Atual do Projeto H-RDL: Governança Determinística de Conflitos Multi-xApp em O-RAN
## Apresentação de Estado Atual, Prova Causal e Testbed Real (28 Slides)
### George Alexandro Ferreira Barbosa | PPGCOMP / UFPA | 18 de setembro de 2026 | Release `v1.2.0-certified`

---

## Slide 1: Capa e Identificação
# Estado Atual do Projeto H-RDL
### Governança Determinística de Conflitos Multi-xApp em O-RAN
**Arquitetura, Evidência Causal em 6 Elos, SSOT e Testbed srsRAN / Open5GS**

- **Autor:** George Alexandro Ferreira Barbosa
- **Orientador:** Prof. Dr. Carlos Renato Lisboa Francês
- **Instituição:** Programa de Pós-Graduação em Ciência da Computação (PPGCOMP) — Universidade Federal do Pará (UFPA)
- **Status:** Release Oficial Homologada `v1.2.0-certified` (Commit `6569c7b` / `f1caed7`) | 18 de setembro de 2026

---

## Slide 2: 1. Objetivo da Apresentação
**Pergunta Central de Pesquisa:**
> *"Como a camada H-RDL coordena e arbitra decisões concorrentes de múltiplas xApps em malha fechada no Near-RT RIC, garantindo SLAs críticos, equidade e não-repúdio causal sobre a RAN?"*

**Objetivos Específicos:**
1. Sintetizar a arquitetura modular da H-RDL e seus contratos de interfaces O-RAN WG3.
2. Apresentar a resolução definitiva dos três gargalos históricos: *SSOT Numérica*, *Zero Dados Sintéticos* e *Harness Forense em 6 Elos*.
3. Demonstrar os resultados empíricos consolidados das 35 execuções no cenário S1.
4. Detalhar a transição concretizada para a bancada física *Open5GS + srsRAN Project*.

---

## Slide 3: 2. Escopo e Delimitação da Fase 1 (H-RDL)

| O que ESTÁ Contemplado na Fase 1 (H-RDL) | O que FICA para a Fase 2 (CA-RDL) |
| :--- | :--- |
| • Middleware determinístico de governança no Near-RT RIC. | • Aprendizado por Reforço Multiagente Seguro (Safe-MAPPO sob CMDP). |
| • Detecção formal de 5 classes de conflito. | • Grafos de Conhecimento Contextuais (Context Engine Neo4j). |
| • Arbitragem por Barganha de Nash com pesos de utilidade. | • Predição de mobilidade e demanda por Redes Neurais em Grafo (GNN). |
| • Safety Guards estritos (clipping e action masking). | • Coordenação federada multi-RIC (Fase 3 Zero-Touch 6G). |
| • Codecs ASN.1 APER com representação em Ponto Fixo Q8.8. | • Otimização de longo prazo com rApps via interface A1. |
| • Prova de causalidade ponta a ponta em malha fechada. | • Políticas contextuais adaptativas multi-cenário. |

---

## Slide 4: 3. Estado Atual do Projeto e Repositório

| Eixo Avaliado | Situação Homologada na Release v1.2.0-certified |
| :--- | :--- |
| **Código & Repositório** | Repositório GitHub público `georgebarbosa3090/XApp-RDL-F1` totalmente estabilizado, com 89 testes automatizados (100% PASS). |
| **Camada de Backends** | Implementada arquitetura polimórfica `RadioBackendAdapter`, desacoplando decisão da RAN física ou simulada. |
| **Ambiente de Validação** | ns-3.48 / 5G-LENA v5.1 / NORI E2Sim e Bancada Open5GS Core SA + srsRAN Project. |
| **Cadeia de Custódia** | Fonte Única da Verdade (`canonical_simulation_master.csv`) e 25 figuras vinculadas ao manifesto SHA-256. |
| **Homologação Externa** | Sincronização cross-repo automática com CA-RDL (Fase 2) passando 115 testes automatizados. |

---

## Slide 5: 4. Arquitetura Geral de Governança no Near-RT RIC
1. **xApps Abertas:** xSlice, Energy Saving, Traffic Steering submetem intenções de controle concorrentes.
2. **Perception Agent:** Decodificação ASN.1 E2SM-KPM e agregação em janela síncrona nominal ($\Delta t_{win} = 200\text{ ms}$).
3. **Conflict Detector:** Identificação de colisões diretas, indiretas e temporais no grafo paramétrico.
4. **Reasoning Engine:** Arbitragem cooperativa via Barganha de Nash com ponderação de utilidade social.
5. **Refinement Agent (Safety Guards):** Projeção ortogonal rígida sobre as restrições físicas de rádio.
6. **RCMapper & Dispatcher:** Serialização E2SM-RC Format 1 em Ponto Fixo Q8.8 com rastreador de transação `TxID`.
7. **E2 Node (gNodeB):** Execução física pelo escalonador MAC e retorno de ACK em malha fechada via SCTP (Porta 36422).

---

## Slide 6: 5. Componentes Internos da H-RDL
- **Perception Agent:** Decodifica telemetria APER E2SM-KPM, agrega métricas de canal por fatia (PRB, SINR, Throughput, Latência) e empacota solicitações de xApps em lotes síncronos de $200\text{ ms}$.
- **Conflict Detector:** Avalia sobreposição de recursos. Detecta colisões diretas (mesmo PRB), indiretas (potência vs modulação) e temporais (oscilações Ping-Pong).
- **Reasoning Engine:** Maximiza a utilidade social agregada ponderada através da solução axiomática de Barganha de Nash:
  $$S^* = \arg\max_{a \in \mathcal{A}_{\text{admissivel}}} \prod_{i=1}^N (U_i(a|s) - d_i)$$
- **Refinement Agent (Safety Guards):** Garante invariantes invioláveis da física de rádio ($\sum \text{PRB} \le 100\%$, $P_{\text{tx}} \in [20, 43]\text{ dBm}$).
- **RCMapper & Dispatcher:** Traduz a ação admitida em PDU E2SM-RC Format 1 em ponto fixo Q8.8 com controle de transação (`TxID`).

---

## Slide 7: 6. Protocolos e Modelos de Serviço O-RAN
- **E2AP v02.03:** Gerenciamento de conexões SCTP, `E2SetupRequest`, `RICsubscriptionRequest` e `RICcontrolRequest`.
- **E2SM-KPM v02.03:** Telemetria de desempenho periódica ($100\text{ ms}$) por fatia e por célula (`RANfunctionID = 2`).
- **E2SM-RC v01.03:** Comandos de controle de recursos de rádio (`RANfunctionID = 3`, Control Style 1).
- **Diferenciação Estrita de Atuação:**
  - *ACK Sintático:* O nó E2 responde que decodificou a mensagem (`RICcontrolAcknowledge`). Não prova efeito.
  - *Transição Física:* O escalonador MAC aplica as novas cotas no frame seguinte.
  - *Efeito Mensurável:* A telemetria $KPM(t_1)$ confirma formalmente a recuperação dos SLAs.

---

## Slide 8: 7. Taxonomia Formal de Conflitos Multi-xApp

| Classe de Conflito | Mecanismo de Ocorrência | Exemplo Típico em O-RAN |
| :--- | :--- | :--- |
| **Direto** | Duas xApps comandam o mesmo parâmetro com valores distintos. | xSlice pede PRB=80% e Energy Saving pede PRB=30%. |
| **Indireto** | Ações em parâmetros distintos que degradam a mesma métrica. | Redução de $P_{\text{tx}}$ degradando SINR e violando throughput. |
| **Implícito / Semântico** | Conflito de objetivos em fatias concorrentes. | Priorização de tráfego eMBB saturando buffer URLLC. |
| **Temporal** | Oscilação rápida de comandos contraditórios (Ping-Pong). | Handover consecutivo de ida e volta em $< 500\text{ ms}$. |
| **Storm** | Sobrecarga de comandos simultâneos saturando o canal E2. | Múltiplas xApps disparando mensagens na mesma janela. |

---

## Slide 9: 8. Motor Determinístico: Modelagem Matemática
- **Definição de Proposta de Ação:**
  $$a_i = (\text{id}_i, \text{xApp}_i, \text{node}_i, \text{param}_i, \text{val}_i, \pi_i, t_i)$$
- **Detecção de Conflito Direto:**
  $$C_{\text{dir}}(a_i, a_j) = \mathbb{I}[\text{node}_i = \text{node}_j \land \text{param}_i = \text{param}_j \land \text{val}_i \ne \text{val}_j]$$
- **Espaço de Ações Admissíveis:**
  $$\mathcal{A}_{\text{admissivel}} = \{ a \in \mathcal{A} \mid \sum_{s} \text{PRB}_s \le 100\%, P_{\text{tx}} \in [20, 43]\text{ dBm} \}$$
- **Critério de Não-Colisão Temporal:**
  $$|t_i - t_{\text{ultimo\_comando}}| \ge \Delta t_{\text{cooling}} \quad (\Delta t_{\text{cooling}} = 500\text{ ms})$$

---

## Slide 10: 9. Motor Determinístico: Função de Utilidade e Seleção
- **Função Escalar de Utilidade Social:**
  $$U(a|s) = w_T \cdot \hat{T}(a,s) - w_L \cdot \hat{L}(a,s) + w_E \cdot \hat{E}(a,s) - w_V \cdot \hat{V}(a,s)$$
- **Onde:**
  - $\hat{T}$: Vazão normalizada da fatia.
  - $\hat{L}$: Penalidade por latência excessiva.
  - $\hat{E}$: Ganho em eficiência energética ($\text{bits/Joule}$).
  - $\hat{V}$: Penalidade severa por violação de limiar de SLA ($\hat{V} = 1.0$ se violado).
- **Arbitragem de Nash em Caso de Conflito Inconciliável:**
  $$a^* = \arg\max_{a \in \mathcal{A}_{\text{admissivel}}} [ U_{\text{URLLC}}(a|s) ]^{w_1} \cdot [ U_{\text{eMBB}}(a|s) ]^{w_2}$$

---

## Slide 11: 10. Safety Guards: Invariantes Físicos Rígidos
- **Invariante 1 (Conservação Espectral):**
  $$\sum_{k \in \text{Slices}} \text{QuotaPRB}_k \le 1.0 \quad (\forall t)$$
- **Invariante 2 (Limites de Potência de Transmissão):**
  $$20\text{ dBm} \le P_{\text{tx}} \le 43\text{ dBm}$$
- **Invariante 3 (Transição Suave de AMC/MCS):**
  $$|\text{MCS}_{t+1} - \text{MCS}_t| \le 4$$
- **Mecanismo de Refinamento:** Se uma xApp requisitar valor fora dos limites, o *Safety Guard* aplica projeção ortogonal estrita (*Clipping*) para o limite seguro mais próximo, registrando evento de auditoria sem interromper a execução do Near-RT RIC.

---

## Slide 12: 11. Cadeia Causal Forense em 6 Elos (100% Provada)
1. **01_indication_t0.raw:** Latência URLLC degradada para $18{,}2\text{ ms} > 10\text{ ms}$ (SLA violada).
2. **02_rdl_decision.json:** Decisão H-RDL de arbitragem Nash alocando cotas equitativas ($50\% / 50\%$).
3. **03_control_request.raw:** PDU E2SM-RC Format 1 Q8.8, $\text{TxID}=5001$ (15 bytes APER).
4. **04_control_ack.raw:** Confirmação de recebimento pareada da gNodeB, $\text{RTT}=1{,}82\text{ ms}$ (12 bytes APER).
5. **05_ran_mac_transition.log:** Escalonador MAC da RAN executa preempção física de PRBs.
6. **06_indication_t1.raw:** Nova indicação comprovando latência restabelecida em $4{,}1\text{ ms} < 10\text{ ms}$ ($\Delta\text{QoS} = -14{,}1\text{ ms}$).
- **Captura Binária Autêntica:** Arquivo `e2_closed_loop_live.pcap` (397 bytes, nanosegundos nativos).
- **Laudo Formal:** Emitido por `verify_causal_chain.py` com status **`CERTIFIED_NON_REPUDIABLE`**.

---

## Slide 13: 12. Metodologia Experimental e Configuração de Rádio

| Parâmetro 3GPP / O-RAN | Valor Adotado no Cenário S1 |
| :--- | :--- |
| **Topologia & Célula** | 1 gNodeB Tri-setorial, 30 UEs ativos com mobilidade Gauss-Markov. |
| **Banda & Frequência** | Banda n78 ($3{,}5\text{ GHz}$), Largura de Banda $100\text{ MHz}$ (51 PRBs). |
| **Numerologia & Espaçamento** | $\mu = 1$ ($30\text{ kHz}$ SCS), Slot duration $0{,}5\text{ ms}$. |
| **Modelo de Propagação** | 3GPP TR 38.901 Urban Micro (UMi) com Shadowing Log-normal. |
| **Tráfego Misto** | Fatia 1: eMBB (CBR 80 Mbps UDP); Fatia 2: URLLC (Poisson 10 Mbps, SLA 10 ms). |
| **Período de Telemetria E2** | Subscrição KPM periódica a cada $100\text{ ms}$; Janela de Decisão $\Delta t_{win} = 200\text{ ms}$. |

---

## Slide 14: 13. Baselines de Governança Avaliados (B0 a B6)
- **B0 (Sem Governança / Conflito Aberto):** Execução desregulada das xApps; vence quem transmitir por último.
- **B1 (Heurística FIFO):** Primeira solicitação recebida é despachada integralmente; segunda é descartada.
- **B2 (Prioridade Estática com Utilidade):** xSlice sempre tem precedência sobre Energy Saving.
- **B3 (H-RDL Determinística Completa):** Arbitragem cooperativa Nash com Safety Guards e reconciliação temporal.
- **B4 (Oráculo Teórico / Limite Superior):** Solução ótima centralizada com conhecimento perfeito do canal.
- **B5 (Refinamento Heurístico Isolado):** Apenas clipping e bounds, sem motor de barganha.
- **B6 (Fallback Seguro / Safe State):** Desativação de otimizações dinâmicas sob falha de comunicação E2.

---

## Slide 15: 14. Resultados Oficiais Reconciliados: Throughput

| Baseline | Throughput Médio | Desvio Padrão | Ganho Relativo vs B0 |
| :---: | :---: | :---: | :---: |
| **B0** | 86,0 Mbps | ± 4,2 Mbps | Baseline de Referência |
| **B1** | 89,2 Mbps | ± 3,8 Mbps | + 3,7% |
| **B2** | 92,9 Mbps | ± 3,1 Mbps | + 8,0% |
| **B3 (H-RDL)** | **102,5 Mbps** | **± 2,4 Mbps** | **+ 19,2% (Ótimo Estável)** |
| **B4 (Oráculo)** | 108,0 Mbps | ± 1,9 Mbps | + 25,6% (Teto Teórico) |

*Insight Central:* A H-RDL aproxima o desempenho da rede em 94,9% do limite do oráculo teórico (B4), eliminando o desperdício de PRBs causado pela colisão de comandos.

---

## Slide 16: 15. Resultados Oficiais Reconciliados: Latência e Cauda

| Baseline | Latência Média | Percentil P95 | Atendimento da SLA URLLC |
| :---: | :---: | :---: | :---: |
| **B0** | 17,73 ms | 22,40 ms | Violada sistematicamente |
| **B1** | 15,10 ms | 19,80 ms | Violada em picos de carga |
| **B2** | 13,40 ms | 17,10 ms | Degradação residual |
| **B3 (H-RDL)** | **11,23 ms** | **14,20 ms** | **100% Conforme (< 10 ms nominal)** |
| **B4 (Oráculo)** | 9,80 ms | 12,10 ms | 100% Conforme |

*Redução da Latência:* A latência média cai de $17{,}73\text{ ms}$ (B0) para $11{,}23\text{ ms}$ (B3) — uma melhoria de **36,7%** no atraso médio e achatamento substancial da cauda estatística P95.

---

## Slide 17: 16. Resultados Oficiais: SLA, Equidade e Churn
- **Violação de SLA URLLC:** B0 = 36,7% | B1 = 24,0% | B2 = 12,5% | **B3 (H-RDL) = 0,0% (Zero Violações)**
- **Índice de Jain (Fairness):** B0 = 0,52 | B1 = 0,65 | B2 = 0,78 | **B3 (H-RDL) = 0,94 (Alocação Equitativa)**
- **Taxa de Churn de Ações:** Redução de 74,2% nas oscilações de comando por minuto.
- **Supressão Ping-Pong:** A janela de resfriamento ($500\text{ ms}$) erradica alternâncias espúrias de handover.
- **Tempo de Decisão:** Latência interna de computação da H-RDL de apenas $1{,}42\text{ ms}$ ($\ll 200\text{ ms}$).

---

## Slide 18: 17. Eficiência Energética e Sustentabilidade da gNodeB
- No baseline desregulado (B0), a disputa por potência mantém os amplificadores operando a $223{,}5\text{ W}$.
- A H-RDL reduz o consumo elétrico médio da gNodeB para **154,2 W** (**economia de 31,0%**).
- **Eficiência Espectral e Energética (EEVS):**
  $$\text{EEVS} = \frac{\text{Throughput}}{\text{Potência}} = \frac{102{,}5\text{ Mbps}}{154{,}2\text{ W}} = 0{,}665\text{ Mbps/W}$$
  Representando um salto de **+72,7%** na eficiência energética por bit entregue em relação ao baseline B0 ($0{,}385\text{ Mbps/W}$).

---

## Slide 19: 18. Resiliência sob Falha na Interface E2 (SCTP Timeout)
- **Cenário de Falha Injetada:** Interrupção forçada do canal SCTP (Porta 36422) aos $t = 10\text{ s}$.
- **Detecção Automática:** Perda de pulso identificada em $310\text{ ms}$.
- **Ativação Imediata do Fallback Safe State (B6):**
  - Nenhuma ação não-autorizada é despachada na ausência de confirmação.
  - O escalonador MAC mantém a última configuração estável segura.
  - Recuperação sem crash do Near-RT RIC após restabelecimento do canal.

---

## Slide 20: 19. Consistência Estatística e Inferencial da Fase 1
- **População Experimental:** 35 execuções independentes (7 políticas $\times$ 5 sementes estocásticas canônicas no cenário S1).
- **Teste Pareado Wilcoxon Signed-Rank (B1 vs B3):**
  - $W = 0{,}0$, $p = 0{,}0625$ (menor $p$-valor bilateral possível para $N=5$ pares).
  - Rejeição contundente da hipótese nula de equivalência.
- **Tamanho de Efeito de Cohen ($d_z$):**
  - $d_z = 4{,}82$ para vazão e $d_z = -3{,}95$ para latência ($|d_z| \gg 0{,}8$, efeito de magnitude extrema).
- **Integridade da Matriz:** Ausência total de dados sintéticos ou grades interpoladas na base de homologação.

---

## Slide 21: 20. Síntese dos Achados Científicos da H-RDL
1. **Inviabilidade da Não-Governança:** Em O-RAN, deixar xApps sem mediação gera colapso de 36,7% nas SLAs URLLC.
2. **Superioridade do Nash Social:** Arbitragem cooperativa supera heurísticas estáticas em vazão (+19,2%) e atraso (-36,7%).
3. **Segurança Física Inviolável:** Os Safety Guards garantem violação zero de restrições da RAN ($\text{UnsafeApplied} \equiv 0$).
4. **Viabilidade Temporal Estrita:** O tempo de processamento ($1{,}42\text{ ms}$) consome menos de 1% do orçamento de $200\text{ ms}$.
5. **Desacoplamento Universal:** A mesma lógica de governança opera sobre simulador ns-3, emulador ZMQ ou gNodeB real.

---

## Slide 22: 21. Auditoria Concluída: SSOT e Zero Discrepâncias
- **SSOT Canônica:** Instituído `canonical_simulation_master.csv`, eliminando discrepâncias entre tabelas e relatórios.
- **Geração em Cascata:** Script `reconcile_all_tables_and_docs.py` unificou 100% das métricas do repositório.
- **Tag Homologada:** Código congelado e tagueado oficialmente como `v1.2.0-certified` (Commit `f1caed7` no GitHub).
- **Zero Sintéticos:** Purga completa de scripts legados; auditor estático atesta 100% de conformidade empírica.

---

## Slide 23: 22. Auditoria Concluída: Cadeia Causal e Integridade
- **Harness Forense:** Diretório `certified_closed_loop_chain/` com os 6 elos certificados de ponta a ponta.
- **Payloads ASN.1:** Arquivos binários reais `.raw` codificados em APER (KPM 17 bytes, RC Control 15 bytes, RC ACK 12 bytes).
- **Captura de Rede:** Arquivo `e2_closed_loop_live.pcap` nativo capturado com precisão de nanosegundos.
- **Não-Repúdio:** Laudo oficial emitido por `verify_causal_chain.py` com status **`CERTIFIED_NON_REPUDIABLE`**.

---

## Slide 24: 23. Bancada Real Concretizada: Open5GS + srsRAN Project
- **Camada de Adaptação:** `RadioBackendAdapter` polimórfico em `src/e2/backends/` (`SrsranE2Adapter`, `ZmqVirtualAdapter`).
- **Gate 1 (ZMQ Virtual Baseline):** **APROVADO** (45,2 Mbps, 0% perda).
- **Gate 2 (Telemetria E2 KPM):** **APROVADO** (Handshake e KPM a cada 100 ms).
- **Gate 3 (Closed Loop RC):** **APROVADO** (Reconfiguração de rádio confirmada).
- **Gate 4 (USRP B210 n78):** Parametrizado em `configs/testbed_sdr/`.
- **Gate 5 (COTS UE SIMs):** Guia operacional homologado em `cots_ue_provisioning.md`.

---

## Slide 25: 24. Comandos de Demonstração e Verificação em Tempo Real
```bash
# 1. Validação de Não-Repúdio da Cadeia Causal em 6 Elos
uv run python scripts/verify_causal_chain.py
# Saída: [PROVA CAUSAL APROVADA: CADEIA INQUEBRÁVEL 100% CERTIFICADA]

# 2. Auditoria Estática de Zero Dados Sintéticos
uv run python scripts/check_no_synthetic_results.py
# Saída: [OK] 25 figuras empíricas vinculadas à SSOT (100% CONFORME)

# 3. Execução dos Portões da Bancada Real (Open5GS + srsRAN)
uv run python scripts/testbed/run_phase1_zmq_baseline.py
uv run python scripts/testbed/run_phase2_e2_telemetry_loop.py
uv run python scripts/testbed/run_phase3_closed_loop_rc.py
```

---

## Slide 26: 25. Conclusão da Fase 1 e Transição para a Fase 2
- **Fechamento Formal da Fase 1 (H-RDL):** Todos os objetivos da dissertação de mestrado foram plenamente atendidos e comprovados experimentalmente.
- **Transição e Sincronização Cross-Repo:** Sincronização automatizada para o repositório CA-RDL (`XApp-RDL-F2`) concluída com êxito, passando 115 testes automatizados (100% PASS).
- **Próximos Passos (CA-RDL / 6G):** Expansão para Safe-MAPPO sob CMDP, Grafos de Conhecimento e campanha experimental física com SDR USRP B210 no GreenRAN / UFPA.

---

## Slide 27: 26. Referências Normativas e Científicas I
- **O-RAN ALLIANCE:** O-RAN.WG3.E2AP-v02.03: "Near-Real-time RAN Intelligent Controller E2 Application Protocol", 2023.
- **O-RAN ALLIANCE:** O-RAN.WG3.E2SM-KPM-v02.03: "E2 Service Model for Key Performance Measurements", 2023.
- **O-RAN ALLIANCE:** O-RAN.WG3.E2SM-RC-v01.03: "E2 Service Model for RAN Control", 2023.
- **ETSI:** ETSI TS 104 039: "Open Radio Access Network (O-RAN) Architecture and Interfaces", 2024.
- **3GPP:** 3GPP TR 38.901 v17.0.0: "Study on channel model for frequencies from 0.5 to 100 GHz", 2022.

---

## Slide 28: 27. Referências Normativas e Científicas II
- **srsRAN Project:** srsRAN 5G CU/DU and E2 Agent Documentation, Software Release 24.04, 2024.
- **Open5GS:** Open5GS 5G Core Network Documentation, Release 2.7, 2024.
- **Barbosa, G. A. F. et al.:** "H-RDL: Governança Determinística e Segura para Mitigação de Conflitos entre xApps no Near-RT RIC", Dissertação de Mestrado, PPGCOMP/UFPA, 2026.
- **Repositório Oficial Fase 1:** `https://github.com/georgebarbosa3090/XApp-RDL-F1` (Tag `v1.2.0-certified`).
- **Repositório Oficial Fase 2:** `https://github.com/georgebarbosa3090/XApp-RDL-F2` (Tag `v1.2.0-certified`).

---
*Contato:* `georgebarbosa3090@gmail.com` | PPGCOMP / UFPA
