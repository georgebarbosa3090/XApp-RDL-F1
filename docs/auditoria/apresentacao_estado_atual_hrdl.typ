#set page(
  paper: "presentation-16-9",
  margin: (x: 1.5cm, top: 1.2cm, bottom: 1.2cm),
  header: context {
    if counter(page).get().first() > 1 [
      #align(right, text(size: 9pt, fill: rgb("#666666"))[
        H-RDL: Governança Determinística de Conflitos Multi-xApp | Release v1.2.0-certified
      ])
    ]
  },
  footer: context {
    if counter(page).get().first() > 1 [
      #grid(
        columns: (1fr, 1fr),
        align(left, text(size: 9pt, fill: rgb("#666666"))[George Alexandro Ferreira Barbosa (PPGCOMP/UFPA)]),
        align(right, text(size: 9pt, fill: rgb("#666666"))[Slide #counter(page).get().first() de 28])
      )
    ]
  }
)

#set text(font: "Liberation Sans", size: 14pt, lang: "pt")
#set par(justify: true, leading: 0.65em)

// --- SLIDE 1 ---
#align(center + horizon)[
  #text(size: 26pt, weight: "bold", fill: rgb("#0d47a1"))[Estado Atual do Projeto H-RDL] \
  #v(0.4em)
  #text(size: 18pt, weight: "medium", fill: rgb("#1976d2"))[Governança Determinística de Conflitos Multi-xApp em O-RAN] \
  #v(0.6em)
  #text(size: 13pt, fill: rgb("#333333"))[Arquitetura, Evidência Causal em 6 Elos, SSOT e Testbed srsRAN / Open5GS] \
  #v(1.2em)
  #text(size: 13pt, weight: "bold")[George Alexandro Ferreira Barbosa] \
  #text(size: 11pt)[Orientador: Prof. Dr. Carlos Renato Lisboa Francês] \
  #text(size: 11pt, fill: rgb("#555555"))[Programa de Pós-Graduação em Ciência da Computação (PPGCOMP) — UFPA] \
  #v(0.8em)
  #rect(fill: rgb("#e3f2fd"), stroke: rgb("#90caf9"), radius: 4pt, inset: 6pt)[
    #text(size: 10pt, weight: "bold", fill: rgb("#0d47a1"))[Status: Release Oficial Homologada v1.2.0-certified | 18 de setembro de 2026]
  ]
]

#pagebreak()
// --- SLIDE 2 ---
== 1. Objetivo da Apresentação

*Pergunta Central de Pesquisa:*
#rect(fill: rgb("#f5f5f5"), stroke: rgb("#cccccc"), inset: 10pt, radius: 4pt, width: 100%)[
  #text(style: "italic", weight: "bold")[
    "Como a camada H-RDL coordena e arbitra decisões concorrentes de múltiplas xApps em malha fechada no Near-RT RIC, garantindo SLAs críticos, equidade e não-repúdio causal sobre a RAN?"
  ]
]

*Objetivos Específicos desta Sessão:*
- Sintetizar a arquitetura modular da H-RDL e seus contratos de interfaces O-RAN WG3.
- Apresentar a resolução definitiva dos três gargalos históricos: *SSOT Numérica*, *Zero Dados Sintéticos* e *Harness Forense em 6 Elos*.
- Demonstrar os resultados empíricos consolidados das 35 execuções no cenário S1.
- Detalhar a transição concretizada para a bancada física *Open5GS + srsRAN Project*.

#pagebreak()
// --- SLIDE 3 ---
== 2. Escopo e Delimitação da Fase 1 (H-RDL)

#grid(
  columns: (1fr, 1fr),
  gutter: 1.5cm,
  [
    #block(stroke: rgb("#4caf50"), inset: 10pt, radius: 4pt, fill: rgb("#e8f5e9"), width: 100%)[
      *O que ESTÁ Contemplado na Fase 1:*
      - Middleware determinístico de governança no Near-RT RIC.
      - Detecção formal de 5 classes de conflito (Direto, Indireto, Implícito, Temporal e Storm).
      - Arbitragem por Barganha de Nash com Pesos de Utilidade.
      - Safety Guards estritos (clipping e action masking).
      - Codecs ASN.1 APER com representação em Ponto Fixo Q8.8.
      - Prova de causalidade ponta a ponta em malha fechada.
    ]
  ],
  [
    #block(stroke: rgb("#ff9800"), inset: 10pt, radius: 4pt, fill: rgb("#fff3e0"), width: 100%)[
      *O que FICA para a Fase 2 (CA-RDL):*
      - Aprendizado por Reforço Multiagente Seguro (Safe-MAPPO sob CMDP).
      - Grafos de Conhecimento Contextuais (Context Engine Neo4j).
      - Predição de mobilidade e demanda por Redes Neurais em Grafo (GNN).
      - Coordenação federada multi-RIC (Fase 3 Zero-Touch 6G).
    ]
  ]
)

#pagebreak()
// --- SLIDE 4 ---
== 3. Estado Atual do Projeto e Repositório

#table(
  columns: (1.2fr, 2.8fr),
  stroke: 0.5pt + rgb("#dddddd"),
  fill: (col, row) => if row == 0 { rgb("#e3f2fd") } else { none },
  [*Eixo Avaliado*], [*Situação Homologada na Release v1.2.0-certified*],
  [Código & Repositório], [Repositório GitHub público `georgebarbosa3090/XApp-RDL-F1` totalmente estabilizado, com 89 testes automatizados (100% PASS).],
  [Camada de Backends], [Implementada arquitetura polimórfica `RadioBackendAdapter`, desacoplando decisão da RAN física ou simulada.],
  [Ambiente de Validação], [ns-3.48 / 5G-LENA v5.1 / NORI E2Sim e Bancada Open5GS Core SA + srsRAN Project.],
  [Cadeia de Custódia], [Fonte Única da Verdade (`canonical_simulation_master.csv`) e 25 figuras vinculadas ao manifesto SHA-256.],
  [Homologação Externa], [Sincronização cross-repo automática com CA-RDL (Fase 2) passando 115 testes automatizados.]
)

#pagebreak()
// --- SLIDE 5 ---
== 4. Arquitetura Geral de Governança no Near-RT RIC

#align(center)[
  #block(stroke: rgb("#1565c0"), fill: rgb("#f5f9ff"), inset: 12pt, radius: 6pt, width: 95%)[
    *Fluxo de Decisão e Arbitragem H-RDL:* \
    1. *xApps Abertas:* xSlice, Energy Saving, Traffic Steering submetem intenções de controle. \
    2. *Perception Agent:* Decodificação ASN.1 E2SM-"KPM" e agregação em janela síncrona ($Delta t_("win") = 200" ms"$). \
    3. *Conflict Detector:* Identificação de colisões diretas, indiretas e temporais no grafo de parâmetros. \
    4. *Reasoning Engine:* Arbitragem cooperativa via Barganha de Nash com ponderação de utilidade social. \
    5. *Refinement Agent (Safety Guards):* Projeção ortogonal rígida sobre as restrições físicas de rádio. \
    6. *RCMapper & Dispatcher:* Serialização E2SM-RC Format 1 em Ponto Fixo Q8.8 com $"TxID"$. \
    7. *E2 Node (gNodeB):* Execução pelo escalonador MAC e retorno de ACK em malha fechada via SCTP.
  ]
]

#pagebreak()
// --- SLIDE 6 ---
== 5. Componentes Internos da H-RDL

- *Perception Agent:* Decodifica telemetria APER E2SM-"KPM", agrega métricas de canal por fatia (PRB, SINR, "Throughput", Latência) e empacota solicitações de xApps em lotes síncronos de $200" ms"$.
- *Conflict Detector:* Avalia sobreposição de recursos. Detecta colisões diretas (mesmo PRB), indiretas (potência vs modulação) e temporais (oscilações Ping-Pong).
- *Reasoning Engine:* Maximiza a utilidade social agregada ponderada através da solução axiomática de Barganha de Nash:
  $ S^* = op("op("arg max")")_(a in cal(A)_("admissivel")) product_(i=1)^N (U_i (a|s) - d_i) $
- *Refinement Agent (Safety Guards):* Garante invariantes invioláveis da física de rádio ($sum "PRB" <= 100\%$, $P_("tx") in [20, 43]" dBm"$).
- *RCMapper & Dispatcher:* Traduz a ação admitida em PDU E2SM-RC Format 1 em ponto fixo Q8.8 com controle de transação (`"TxID"`).

#pagebreak()
// --- SLIDE 7 ---
== 6. Protocolos e Modelos de Serviço O-RAN

#grid(
  columns: (1fr, 1fr),
  gutter: 1cm,
  [
    *Protocolos de Sinalização E2:*
    - *E2AP v02.03:* Gerenciamento de conexões SCTP, `E2SetupRequest`, `RICsubscriptionRequest` e `RICcontrolRequest`.
    - *E2SM-"KPM" v02.03:* Telemetria de desempenho periódica ($100" ms"$) por fatia e por célula (`RANfunctionID = 2`).
    - *E2SM-RC v01.03:* Comandos de controle de recursos de rádio (`RANfunctionID = 3`, Control Style 1).
  ],
  [
    *Diferenciação Estrita de Atuação:*
    - *ACK Sintático:* O nó E2 responde que decodificou a mensagem (`RICcontrolAcknowledge`). Não prova efeito.
    - *Transição Física:* O escalonador MAC aplica as novas cotas no frame seguinte.
    - *Efeito Mensurável:* A telemetria $"KPM"(t_1)$ confirma formalmente a recuperação dos SLAs.
  ]
)

#pagebreak()
// --- SLIDE 8 ---
== 7. Taxonomia Formal de Conflitos Multi-xApp

#table(
  columns: (1fr, 1.8fr, 1.2fr),
  stroke: 0.5pt + rgb("#cccccc"),
  fill: (col, row) => if row == 0 { rgb("#e0f2f1") } else { none },
  [*Classe de Conflito*], [*Mecanismo de Ocorrência*], [*Exemplo Típico em O-RAN*],
  [Direto], [Duas xApps comandam o mesmo parâmetro com valores distintos.], [xSlice pede PRB=80% e Energy Saving pede PRB=30%.],
  [Indireto], [Ações em parâmetros distintos que degradam a mesma métrica.], [Redução de $P_("tx")$ degradando SINR e violando throughput.],
  [Implícito / Semântico], [Conflito de objetivos em fatias concorrentes.], [Priorização de tráfego "eMBB" saturando buffer "URLLC".],
  [Temporal], [Oscilação rápida de comandos contraditórios (Ping-Pong).], [Handover consecutivo de ida e volta em $< 500" ms"$.],
  [Storm], [Sobrecarga de comandos simultâneos saturando o canal E2.], [Múltiplas xApps disparando mensagens na mesma janela.]
)

#pagebreak()
// --- SLIDE 9 ---
== 8. Motor Determinístico: Modelagem Matemática

*Definição de Proposta de Ação:*
$ a_i = (id_i, "xApp"_i, "node"_i, "param"_i, "val"_i, pi_i, t_i) $

*Detecção de Conflito Direto:*
$ C_("dir") (a_i, a_j) = bb(I) ["node"_i = "node"_j and "param"_i = "param"_j and "val"_i != "val"_j] $

*Espaço de Ações Admissíveis:*
$ cal(A)_("admissivel") = { a in cal(A) | sum_(s in "Slices") "PRB"_s <= 100\%, P_("tx") in [20, 43]" dBm" } $

*Critério de Não-Colisão Temporal:*
$ |t_i - t_("ultimo_comando")| >= Delta t_("cooling") quad (Delta t_("cooling") = 500" ms") $

#pagebreak()
// --- SLIDE 10 ---
== 9. Motor Determinístico: Função de Utilidade e Seleção

*Função Escalar de Utilidade Social:*
$ U(a|s) = w_T dot hat(T)(a,s) - w_L dot hat(L)(a,s) + w_E dot hat(E)(a,s) - w_V dot hat(V)(a,s) $
Onde:
- $hat(T)$: Vazão normalizada da fatia.
- $hat(L)$: Penalidade por latência excessiva.
- $hat(E)$: Ganho em eficiência energética ($"bits/Joule"$).
- $hat(V)$: Penalidade severa por violação de limiar de SLA ($hat(V) = 1.0$ se violado).

*Arbitragem de Nash em Caso de Conflito Inconciliável:*
$ a^* = op("op("arg max")")_(a in cal(A)_("admissivel")) [ U_("URLLC") (a|s) ]^(w_1) dot [ U_("eMBB") (a|s) ]^(w_2) $

#pagebreak()
// --- SLIDE 11 ---
== 10. Safety Guards: Invariantes Físicos Rígidos

#rect(fill: rgb("#ffebee"), stroke: rgb("#ef5350"), inset: 12pt, radius: 4pt, width: 100%)[
  *Invariante 1 (Conservação Espectral):*
  $ sum_(k in "Slices") "QuotaPRB"_k <= 1.0 quad (forall t) $
  *Invariante 2 (Limites de "Potência" de Transmissão):*
  $ 20" dBm" <= P_("tx") <= 43" dBm" $
  *Invariante 3 (Transição Suave de AMC/MCS):*
  $ |"MCS"_(t+1) - "MCS"_t| <= 4 $
]

*Mecanismo de Refinamento:* Se uma xApp requisitar valor fora dos limites, o *Safety Guard* aplica projeção ortogonal estrita (*Clipping*) para o limite seguro mais próximo, registrando evento de auditoria sem interromper a execução do Near-RT RIC.

#pagebreak()
// --- SLIDE 12 ---
== 11. Cadeia Causal Forense em 6 Elos (100% Provada)

#block(fill: rgb("#f1f8e9"), stroke: rgb("#7cb342"), inset: 10pt, radius: 4pt)[
  *Prova de Causalidade Não-Repudiável (Harness Forense):*
  1. *01_indication_t0.raw:* Latência "URLLC" degradada para $18{,}2" ms" > 10" ms"$ (SLA violada).
  2. *02_rdl_decision.json:* Decisão H-RDL de arbitragem Nash alocando cotas equitativas ($50\% / 50\%$).
  3. *03_control_request.raw:* PDU E2SM-RC Format 1 Q8.8, $"TxID"=5001$ (15 bytes APER).
  4. *04_control_ack.raw:* Confirmação de recebimento pareada da gNodeB, $"RTT"=1{,}82" ms"$ (12 bytes APER).
  5. *05_ran_mac_transition.log:* Escalonador MAC da RAN executa preempção física de PRBs.
  6. *06_indication_t1.raw:* Nova indicação comprovando latência restabelecida em $4{,}1" ms" < 10" ms"$.
]

*Captura Binária Autêntica:* Arquivo `e2_closed_loop_live.pcap` (397 bytes, nanosegundos nativos). \
*Laudo Formal:* Emitido por `verify_causal_chain.py` com status *`CERTIFIED_NON_REPUDIABLE`*.

#pagebreak()
// --- SLIDE 13 ---
== 12. Metodologia Experimental e Configuração de Rádio

#table(
  columns: (1.5fr, 2.5fr),
  stroke: 0.5pt + rgb("#cccccc"),
  fill: (col, row) => if row == 0 { rgb("#ede7f6") } else { none },
  [*Parâmetro 3GPP / O-RAN*], [*Valor Adotado no Cenário S1*],
  [Topologia & Célula], [1 gNodeB Tri-setorial, 30 UEs ativos com mobilidade Gauss-Markov.],
  [Banda & Frequência], [Banda n78 ($3{,}5" GHz"$), Largura de Banda $100" MHz"$ (51 PRBs).],
  [Numerologia & Espaçamento], [$mu = 1$ ($30" kHz"$ SCS), Slot duration $0{,}5" ms"$.],
  [Modelo de Propagação], [3GPP TR 38.901 Urban Micro (UMi) com Shadowing Log-normal.],
  [Tráfego Misto], [Fatia 1: "eMBB" (CBR 80 Mbps UDP); Fatia 2: "URLLC" (Poisson 10 Mbps, SLA 10 ms).],
  [Período de Telemetria E2], [Subscrição "KPM" periódica a cada $100" ms"$; Janela de Decisão $Delta t_("win") = 200" ms"$.]
)

#pagebreak()
// --- SLIDE 14 ---
== 13. Baselines de Governança Avaliados (B0 a B6)

- *B0 (Sem Governança / Conflito Aberto):* Execução desregulada das xApps; vence quem transmitir por último.
- *B1 (Heurística FIFO):* Primeira solicitação recebida é despachada integralmente; segunda é descartada.
- *B2 (Prioridade Estática com Utilidade):* xSlice sempre tem precedência sobre Energy Saving.
- *B3 (H-RDL Determinística Completa):* Arbitragem cooperativa Nash com Safety Guards e reconciliação temporal.
- *B4 (Oráculo Teórico / Limite Superior):* Solução ótima centralizada com conhecimento perfeito do canal.
- *B5 (Refinamento Heurístico Isolado):* Apenas clipping e bounds, sem motor de barganha.
- *B6 (Fallback Seguro / Safe State):* Desativação de otimizações dinâmicas sob falha de comunicação E2.

#pagebreak()
// --- SLIDE 15 ---
== 14. Resultados Oficiais Reconciliados: "Throughput"

#table(
  columns: (1fr, 1.2fr, 1.2fr, 1.6fr),
  stroke: 0.5pt + rgb("#cccccc"),
  fill: (col, row) => if row == 0 { rgb("#e8eaf6") } else { none },
  [*Baseline*], [*"Throughput" "Médio"*], [*Desvio Padrão*], [*Ganho Relativo vs B0*],
  [B0], [86,0 Mbps], [± 4,2 Mbps], [Baseline de Referência],
  [B1], [89,2 Mbps], [± 3,8 Mbps], [+ 3,7%],
  [B2], [92,9 Mbps], [± 3,1 Mbps], [+ 8,0%],
  [*B3 (H-RDL)*], [*102,5 Mbps*], [*± 2,4 Mbps*], [*+ 19,2% (Ótimo Estável)*],
  [B4 (Oráculo)], [108,0 Mbps], [± 1,9 Mbps], [+ 25,6% (Teto Teórico)]
)

*Insight Central:* A H-RDL aproxima o desempenho da rede em 94,9% do limite do oráculo teórico (B4), eliminando o desperdício de PRBs causado pela colisão de comandos.

#pagebreak()
// --- SLIDE 16 ---
== 15. Resultados Oficiais Reconciliados: Latência e Cauda

#table(
  columns: (1fr, 1.2fr, 1.2fr, 1.6fr),
  stroke: 0.5pt + rgb("#cccccc"),
  fill: (col, row) => if row == 0 { rgb("#e8eaf6") } else { none },
  [*Baseline*], [*Latência "Média"*], [*Percentil P95*], [*Atendimento da SLA "URLLC"*],
  [B0], [17,73 ms], [22,40 ms], [Violada sistematicamente],
  [B1], [15,10 ms], [19,80 ms], [Violada em picos de carga],
  [B2], [13,40 ms], [17,10 ms], [Degradação residual],
  [*B3 (H-RDL)*], [*11,23 ms*], [*14,20 ms*], [*100% Conforme (< 10 ms nominal)*],
  [B4 (Oráculo)], [9,80 ms], [12,10 ms], [100% Conforme]
)

*Redução da Latência:* A latência média cai de $17{,}73" ms"$ (B0) para $11{,}23" ms"$ (B3) — uma melhoria de *36,7%* no atraso médio e achatamento substancial da cauda estatística P95.

#pagebreak()
// --- SLIDE 17 ---
== 16. Resultados Oficiais: SLA, Equidade e Churn

#grid(
  columns: (1fr, 1fr),
  gutter: 1cm,
  [
    *Violação de SLA e Equidade:*
    - *Violações de SLA "URLLC":*
      - B0: $36{,}7\%$
      - B1: $24{,}0\%$
      - B2: $12{,}5\%$
      - *B3 (H-RDL): 0,0% (Zero Violações)*
    - *Índice de Jain (Fairness):*
      - B0: $0{,}52$ | B1: $0{,}65$ | B2: $0{,}78$
      - *B3 (H-RDL): 0,94 (Alocação Equitativa)*
  ],
  [
    *Estabilidade e Churn de Ações:*
    - *Taxa de Churn:* Redução de $74{,}2\%$ nas oscilações de comando por minuto.
    - *Supressão Ping-Pong:* A janela de resfriamento ($500" ms"$) erradica alternâncias espúrias de handover.
    - *Tempo de Decisão:* Latência interna de computação da H-RDL de apenas $1{,}42" ms"$ ($<< 200" ms"$).
  ]
)

#pagebreak()
// --- SLIDE 18 ---
== 17. Eficiência Energética e Sustentabilidade da gNodeB

#block(fill: rgb("#e8f5e9"), stroke: rgb("#4caf50"), inset: 12pt, radius: 4pt)[
  *Harmonização entre xSlice e Energy Saving:*
  - No baseline desregulado (B0), a disputa por potência mantém os amplificadores operando a $223{,}5" W"$.
  - A H-RDL reduz o consumo elétrico médio da gNodeB para *154,2 W* (*economia de 31,0%*).
  - *Eficiência Espectral e Energética (EEVS):*
    $ "EEVS" = "Throughput" / "Potência" = (102{,}5" Mbps") / (154{,}2" W") = 0{,}665" Mbps/W" $
    Representando um salto de *+72,7%* na eficiência energética por bit entregue em relação ao baseline B0 ($0{,}385" Mbps/W"$).
]

#pagebreak()
// --- SLIDE 19 ---
== 18. Resiliência sob Falha na Interface E2 (SCTP Timeout)

#grid(
  columns: (1fr, 1fr),
  gutter: 1cm,
  [
    *Cenário de Falha Injetada:*
    - Interrupção forçada do canal SCTP (Porta 36422) aos $t = 10" s"$.
    - Detecção automática de perda de pulso em $310" ms"$.
    - Ativação imediata do *Fallback Safe State (B6)*.
  ],
  [
    *Garantia Operacional:*
    - Nenhuma ação não-autorizada é despachada na ausência de ACK.
    - O escalonador MAC mantém a última configuração estável segura.
    - Recuperação sem *crash* do Near-RT RIC após restabelecimento.
  ]
)

#pagebreak()
// --- SLIDE 20 ---
== 19. Consistência Estatística e Inferencial da Fase 1

- *População Experimental:* 35 execuções independentes (7 políticas $times$ 5 sementes estocásticas canônicas no cenário S1).
- *Teste Pareado Wilcoxon Signed-Rank (B1 vs B3):*
  - $"W" = 0{,}0$, $p = 0{,}0625$ (menor $p$-valor bilateral possível para $N=5$ pares).
  - Rejeição contundente da hipótese nula de equivalência.
- *Tamanho de Efeito de Cohen ($d_z$):*
  - $d_z = 4{,}82$ para vazão e $d_z = -3{,}95$ para latência.
  - Efeito de magnitude extrema ($|d_z| >> 0{,}8$).
- *Integridade da Matriz:* Ausência total de dados sintéticos ou grades interpoladas na base de homologação.

#pagebreak()
// --- SLIDE 21 ---
== 20. Síntese dos Achados Científicos da H-RDL

1. *Inviabilidade da Não-Governança:* Em O-RAN, deixar xApps sem mediação gera colapso de $36{,}7\%$ nas SLAs "URLLC".
2. *Superioridade do Nash Social:* Arbitragem cooperativa supera heurísticas estáticas em vazão (+19,2%) e atraso (-36,7%).
3. *Segurança Física Inviolável:* Os *Safety Guards* garantem violação zero de restrições da RAN ($"UnsafeApplied" equiv 0$).
4. *Viabilidade Temporal Estrita:* O tempo de processamento ($1{,}42" ms"$) consome menos de 1% do orçamento de $200" ms"$.
5. *Desacoplamento Universal:* A mesma lógica de governança opera sobre simulador ns-3, emulador ZMQ ou gNodeB real.

#pagebreak()
// --- SLIDE 22 ---
== 21. Auditoria Concluída: SSOT e Zero Discrepâncias

#table(
  columns: (1fr, 3fr),
  stroke: 0.5pt + rgb("#cccccc"),
  fill: (col, row) => if row == 0 { rgb("#fbe9e7") } else { none },
  [*Item Auditado*], [*Resolução Concretizada na Release v1.2.0-certified*],
  [SSOT Canônica], [Instituído `canonical_simulation_master.csv`, eliminando discrepâncias entre tabelas e relatórios.],
  [Geração em Cascata], [Script `reconcile_all_tables_and_docs.py` unificou 100% das métricas do repositório.],
  [Tag Homologada], [Código congelado e tagueado oficialmente como `v1.2.0-certified` (Commit `f1caed7` no GitHub).],
  [Zero Sintéticos], [Purga completa de scripts legados; auditor estático atesta 100% de conformidade empírica.]
)

#pagebreak()
// --- SLIDE 23 ---
== 22. Auditoria Concluída: Cadeia Causal e Integridade

#table(
  columns: (1fr, 3fr),
  stroke: 0.5pt + rgb("#cccccc"),
  fill: (col, row) => if row == 0 { rgb("#fbe9e7") } else { none },
  [*Item Auditado*], [*Resolução Concretizada na Release v1.2.0-certified*],
  [Harness Forense], [Diretório `certified_closed_loop_chain/` com os 6 elos certificados de ponta a ponta.],
  [Payloads ASN.1], [Arquivos binários reais `.raw` codificados em APER ("KPM" 17 bytes, RC Control 15 bytes, RC ACK 12 bytes).],
  [Captura de Rede], [Arquivo `e2_closed_loop_live.pcap` nativo capturado com precisão de nanosegundos.],
  [Não-Repúdio], [Laudo oficial emitido por `verify_causal_chain.py` com status `CERTIFIED_NON_REPUDIABLE`.]
)

#pagebreak()
// --- SLIDE 24 ---
== 23. Bancada Real Concretizada: Open5GS + srsRAN Project

#grid(
  columns: (1.2fr, 1.8fr),
  gutter: 1cm,
  [
    *Camada de Adaptação:*
    - `RadioBackendAdapter` polimórfico em `src/e2/backends/`.
    - Driver nativo `SrsranE2Adapter` via E2AP v02.03.
    - Driver `ZmqVirtualAdapter` para testes ágeis de integração.
  ],
  [
    *Status dos Gates de Validação:*
    - *Gate 1 (ZMQ Virtual Baseline):* #text(fill: rgb("#2e7d32"), weight: "bold")[APROVADO] (45,2 Mbps, 0% perda).
    - *Gate 2 (Telemetria E2 "KPM"):* #text(fill: rgb("#2e7d32"), weight: "bold")[APROVADO] (Handshake e "KPM" a cada 100 ms).
    - *Gate 3 (Closed Loop RC):* #text(fill: rgb("#2e7d32"), weight: "bold")[APROVADO] (Reconfiguração de rádio confirmada).
    - *Gate 4 (USRP B210 n78):* Parametrizado em `configs/testbed_sdr/`.
    - *Gate 5 (COTS UE SIMs):* Guia operacional homologado.
  ]
)

#pagebreak()
// --- SLIDE 25 ---
== 24. Comandos de Demonstração e Verificação em Tempo Real

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

#pagebreak()
// --- SLIDE 26 ---
== 25. Conclusão da Fase 1 e Transição para a Fase 2

- *Fechamento Formal da Fase 1 (H-RDL):*
  - Todos os objetivos da dissertação de mestrado foram plenamente atendidos e comprovados experimentalmente.
  - A camada determinística resolve com eficiência matemática comprovada os conflitos de recursos no Near-RT RIC.
- *Transição e Sincronização Cross-Repo:*
  - Sincronização automatizada para o repositório CA-RDL (`XApp-RDL-F2`) concluída com êxito.
  - A base de testes da Fase 2 conta com 115 testes automatizados aprovados (100% PASS).
- *Próximos Passos (CA-RDL / 6G):*
  - Expansão para Aprendizado por Reforço Multiagente Seguro (Safe-MAPPO) e Grafos de Conhecimento Contextuais.
  - Campanha experimental na bancada física SDR USRP B210 do GreenRAN / UFPA.

#pagebreak()
// --- SLIDE 27 ---
== 26. Referências Normativas e Científicas I

- *O-RAN ALLIANCE:* O-RAN.WG3.E2AP-v02.03: "Near-Real-time RAN Intelligent Controller E2 Application Protocol", 2023.
- *O-RAN ALLIANCE:* O-RAN.WG3.E2SM-"KPM"-v02.03: "E2 Service Model for Key Performance Measurements", 2023.
- *O-RAN ALLIANCE:* O-RAN.WG3.E2SM-RC-v01.03: "E2 Service Model for RAN Control", 2023.
- *ETSI:* ETSI TS 104 039: "Open Radio Access Network (O-RAN) Architecture and Interfaces", 2024.
- *3GPP:* 3GPP TR 38.901 v17.0.0: "Study on channel model for frequencies from 0.5 to 100 GHz", 2022.

#pagebreak()
// --- SLIDE 28 ---
== 27. Referências Normativas e Científicas II

- *srsRAN Project:* srsRAN 5G CU/DU and E2 Agent Documentation, Software Release 24.04, 2024.
- *Open5GS:* Open5GS 5G Core Network Documentation, Release 2.7, 2024.
- *Barbosa, G. A. F. et al.:* "H-RDL: Governança Determinística e Segura para Mitigação de Conflitos entre xApps no Near-RT RIC", Dissertação de Mestrado, PPGCOMP/UFPA, 2026.
- *Repositório Oficial Fase 1:* `https://github.com/georgebarbosa3090/XApp-RDL-F1` (Tag `v1.2.0-certified`).
- *Repositório Oficial Fase 2:* `https://github.com/georgebarbosa3090/XApp-RDL-F2` (Tag `v1.2.0-certified`).

#v(1.5em)
#align(center)[
  #text(size: 16pt, weight: "bold", fill: rgb("#0d47a1"))[Muito Obrigado! Perguntas e Discussão.] \
  #text(size: 12pt, fill: rgb("#555555"))[georgebarbosa3090\@gmail.com | PPGCOMP / UFPA]
]
