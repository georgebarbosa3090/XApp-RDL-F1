# Adequação das Fases 1 (H-RDL) e 2 (CA-RDL) ao testbed UFPA do projeto GreenRAN (OpenRAN@Brasil)

Data: 2026-11-10. Escopo: repositório da Fase 1 (`XApp-RDL-F1`, commit `b152b4b1`, local) e da Fase 2 (`XApp-RDL-F2`, `main`, último push em 2026-09-30, lido pelo GitHub) comparados à proposta *GreenRAN: Open RAN Sustentável para o Agro e Campi Inteligentes* (Programa OpenRAN@Brasil, Etapa 2, hospedeiro POP-PA/UFPA).

Nenhum experimento novo foi executado para este levantamento. As constatações vêm da leitura do código, dos documentos, dos manifestos e de bytes dos artefatos de evidência. A configuração real do testbed UFPA (versões de OAI/srsRAN, release do RIC, RUs) não está descrita na proposta e precisa ser confirmada com a equipe do hospedeiro.

---

## 1. Veredito

| Item | Veredito | Motivo principal |
| :-- | :-- | :-- |
| Fase 1 (H-RDL) como base científica para o GreenRAN | **Adequada, com lacunas** | Resolve exatamente o conflito xApp1-RANSlicer × xApp2-EnergySaver previsto pela proposta; E2 real (KPM + RC + ACK) e closed loop certificados no NORI, com proveniência. |
| Fase 1 pronta para rodar no testbed UFPA | **Ainda não** | Só validada no NORI (ns-3). Gates de testbed TB0–TB10 não executados; nada com OAI; só cota de PRB é atuável; não detecta conflito entre células (central para desligamento de células). |
| Fase 2 (CA-RDL) no estado atual | **Inadequada** | Evidência sintética ainda publicada e rotulada como verificada; MAPPO não treinado na inferência; GNN/grafo de conhecimento não implementados; CI falhando; código anterior às 51 correções da Fase 1. |
| Fase 2 como conceito | **Muito aderente** | Safe-RL, intenção e agentes coincidem com O1.2–O1.4 do GreenRAN (Nagib 2025, Nahum 2023/2025, Agentic-AI-Green). Precisa ser reconstruída sobre a Fase 1. |

> **Atualização (2026-11-11):** o estado depois das correções está na [seção 7.3](#73-estado-em-2026-11-11). Em resumo:
> - a Fase 1 passou a detectar conflitos entre células e a atuar `CELL_STATE`;
> - S9–S15, G1 e G2 rodam no rádio NR;
> - a Fase 2 foi reconstruída sobre a Fase 1 e está na `main` (`19822d8`, núcleo fixado em `b68ac8f5`, CI verde).
>
> Os vereditos de "pronta para o testbed" não mudam: nada rodou no testbed UFPA.

---

## 2. O que o GreenRAN exige do lado RAN/RIC

Extraído da proposta (seções 6.2, 6.3 e PT1):

| Ref. | Requisito | Prazo |
| :-- | :-- | :-- |
| A1.1 / O1.1a | Controle de PRB por slice na CU/DU (OAI ou srsRAN) via E2 | M1–M4 |
| A1.2 / O1.1b | Controle de potência (por PRB no DL, por UE no UL) via E2 | M1–M4 |
| A1.3 / O1.1c-d | Desligamento de RUs/células e *layers* SDM via E2 | M1–M4 |
| A1.4 / O1.1e | Expansão das métricas KPM (inclusive canal/CSI-RS e energia) | M1–M4 |
| A1.5 | xApp1-RANSlicer (ML, por intenção, *safe RL*) | M4–M8 |
| A1.6 | xApp2-EnergySaver (ML, padrões sazonais, borda entre duas RUs) | M4–M12 |
| A1.7 | rApp-ResourceOptimizer no Non-RT RIC coordenando xApp1 e xApp2 | M12–M20 |
| A1.8/1.9 | Agent-AI-OpenRAN e Agent-AI-Usuário (intenção em linguagem natural → rApp) | M8–M20 |
| A1.10 | Integração com App1-Vigilância (eMBB, 25 Mb/s por câmera 4K, < 100 ms) e App2-Monitoramento (mMTC) | M20–M24 |
| A1.11 / O1.5 | Defesa contra ataques de evasão em modelos de ML de xApps | M4–M20 |
| E4.3 | Código-fonte aberto final no ambiente da RNP | M24 |

Ponto-chave: a proposta reconhece que as xApps operam com "visão isolada" e entrega a coordenação ao rApp (escala não-RT, > 1 s). Não há componente que resolva conflitos **na escala Near-RT** quando xApp1 e xApp2 agem sobre a mesma célula na mesma janela. Esse é o espaço da RDL.

---

## 3. Mapeamento requisito × estado

Legenda: ✅ verificado com evidência; 🟡 implementado sem verificação ou parcial; ❌ ausente; ⚠️ declarado sem evidência válida.

| Requisito GreenRAN | Fase 1 | Fase 2 | Lacuna para o testbed |
| :-- | :-- | :-- | :-- |
| E2 Setup / Subscription / KPM com RIC O-RAN SC | ✅ G1 (249 execuções NORI, Release I, tshark) | ⚠️ PCAPs vazios ou montados à mão | Repetir com o E2 Agent da CU/DU do testbed (TB2–TB4). |
| RIC Control E2SM-RC de cota de PRB por slice | ✅ G3 (Style 2 / Action 6, v3.01, ACK com patch no NORI) | ⚠️ mapeamento fora da norma (PRB em Style 1 / Action 1) | Confirmar que o RAN-CodeUpdates da UFPA expõe PRB por slice no mesmo Style/Action (TB5–TB6). |
| Closed loop KPM → decisão → RC → efeito | ✅ G4 (84 cadeias), com ressalvas (efeito medido no FlowMonitor, cenário único, atraso de ~12 s simulados do NORI) | ⚠️ "cadeia certificada" montada por script | Medir efeito no KPM real do testbed (TB8). |
| Controle de potência de transmissão | 🟡 decidido e aplicado só na pilha nativa (sem E2); no NORI é "não atuável" | ⚠️ `TX_POWER` em Style 2 / Action 1, que não existe no E2SM-RC | Depende de A1.2; definir o canal (RC customizado ou E2SM-CCC). |
| Desligamento de células / *layers* | ❌ | ❌ (só declarado no README) | Depende de A1.3. O caminho normativo é o E2SM-CCC (o NORI já anuncia a função, achado 25). |
| Métricas de energia (KPM/O1) | ❌ | ❌ | Sem métrica de consumo não há como avaliar "green". Incluir na A1.4 (ex.: medidas PEE). |
| Conflito entre células (UE na borda de duas RUs, *handover* para célula desligada) | ❌ limitação conhecida (achado 11, S4/S5) | ❌ | **Lacuna crítica**: é o caso descrito para o xApp2-EnergySaver. |
| Coordenação Near-RT xApp1 × xApp2 | ✅ TVS/EEVS + Safety Guard; G5 com 30 pares B0–B3 em S8 | ⚠️ resultados sintéticos (Cohen d = 49,85) | Generalizar para S0–S2, S6, S7 e para o par real xApp1/xApp2. |
| Políticas A1 vindas do rApp | 🟡 receptor A1 existe, **não ligado à decisão** | ❌ | Ligar A1 a pesos do TVS/EEVS e limites do Refinement; definir *policy type* com a UFRGS. |
| Non-RT RIC / rApp | ❌ (fora do escopo) | ❌ | Fora do escopo da RDL; interface via A1. |
| Intenção / agentes de IA | ❌ | ⚠️ `IntentClassifier` é *stub* treinado com dados aleatórios | Componente da UNICAMP; a RDL só precisa consumir objetivos por A1. |
| Safe RL para slicing | ❌ | ⚠️ MAPPO sem pesos treinados na inferência | Reconstruir com treino em ambiente real (NORI) e *fallback* para H-RDL. |
| Robustez/segurança (O1.5) | 🟡 Safety Guard por proposta, xApp *rogue* de referência; falta autenticar a identidade das xApps (pendência 5) | 🟡 mesma ideia, código anterior às correções | Contribuição natural para A1.11: arbitragem resistente a xApp maliciosa. |
| Fatias eMBB (câmeras) e mMTC (sensores) | 🟡 cenários com URLLC/eMBB | 🟡 | Criar perfil de tráfego GreenRAN: N câmeras × 25 Mb/s com < 100 ms + fatia mMTC intermitente. |
| OAI | ❌ (só menção) | ❌ | A proposta cita OAI primeiro (RAN-CodeUpdates). Sem adaptador nem teste. |
| srsRAN + Open5GS | 🟡 adaptador e configs, nunca executados (perfil "planejado") | 🟡 adaptador com socket próprio e modo *mock* | TB0–TB10 todos pendentes. |
| Implantação em Kubernetes | ✅ Helm, receita do RIC Release I, observabilidade | 🟡 Helm/k3d, manifestos "Blueprint v3" sem evidência | Confirmar release do RIC do testbed (I vs J). |
| Código aberto reproduzível (E4.3) | 🟡 G6 não certificado (falta reprodução por terceiros) | ❌ sem arquivo LICENSE apesar de declarar Apache 2.0 | Reprodução independente (idealmente pela própria equipe do testbed). |

---

## 4. Análise profunda da Fase 2 (CA-RDL)

> **Atualização (2026-11-10):** o saneamento da seção 6.1, itens 1 e parte do 3, foi feito no repositório da Fase 2 e está na `main` (commits `1ab2a1e`, `6390581` e `a548388`): 927 arquivos removidos, claims de volta a `NOT_VERIFIED`, README reescrito, LICENSE adicionada, CI corrigido e verde (execução 42877786595). Registro em `XApp-RDL-F2/docs/SANEAMENTO_20261110.md`. As constatações abaixo descrevem o estado anterior; os itens de código (MAPPO, E2, rebase sobre a Fase 1) continuam pendentes.

### 4.1 Evidência experimental — problema bloqueante

A Fase 1 já classificou estes artefatos como sintéticos e os removeu do seu repositório (achado 45). Na Fase 2 eles continuam publicados e rotulados como verificados:

| Artefato na Fase 2 | Constatação |
| :-- | :-- |
| `experiments/runs/S1_B0..B6_seed1001..1005` (35 execuções) | Os arquivos `raw/*.raw` contêm texto ASCII, não APER: `kpm_t0.raw` = `ASN1_APER_PAYLOAD_kpm_t0.raw_S1_B6_seed1001`. O `pcap/e2.pcap` tem 24 bytes (só o cabeçalho, nenhum pacote). |
| Manifesto dessas execuções | `backend: NORI_NS3_5GLENA`, `ns3_version: 3.48`, `nori_commit: 9b64c12`. Esse commit não existe no NORI oficial e o NORI não compila sobre ns-3.48 (achado 12 da Fase 1). |
| `experiments/runs/certified_closed_loop_chain` | PCAP com MACs `00:11:22:33:44:55` / `66:77:88:99:aa:bb`, IP ID `0x1234`, *verification tag* SCTP `0x12345678` e checksum zero: pacotes montados por script. O log `05_ran_mac_transition.log` tem cinco linhas espaçadas de 5 µs exatos. |
| `specs/claims.yaml` | C1–C6 marcados `VERIFIED_EMPIRICAL`. Na Fase 1, os mesmos C1–C6 estão `NOT_VERIFIED`. |
| `docs/07_...md` | Cohen d = 49,85 entre B0 e B3, tamanho de efeito incompatível com dados medidos. |
| README | "Validada Experimentalmente (N=30 Seeds)" para a Fase 2; latência CA-RDL de 14,39 ms e 4,8 ms em lugares diferentes; "Pareto Score 0,942"; sem execução correspondente. |

Consequência: nenhum número da Fase 2 pode ser usado em relatório do GreenRAN, artigo ou dissertação. Se a banca, a RNP ou a equipe do hospedeiro abrir o repositório, a contradição com a Fase 1 é imediata.

### 4.2 Motor de decisão

| Componente declarado | O que o código faz |
| :-- | :-- |
| Safe-MAPPO (CMDP Lagrangiano) | `MAPPOCoordinator.decide` usa a rede recém-inicializada: nenhum *checkpoint* é carregado. A confiança é forçada a no mínimo 0,80 (`confidence = max(0.80, ...)`). |
| Treinamento | `MAPPOTrainer` usa observações `np.random.randn` e recompensa `sin(step)`; o próprio manifesto diz `environment: MAPPO_SMOKE_ENV`, `publication_eligible: false`, 0,26 s de treino, sem PyTorch. |
| `NoriRanEnvironment` | Não conversa com o NORI: é uma tabela fixa (cota ≥ 60 % → 101,5 Mb/s; ≥ 50 % → 95; senão 85). |
| GNN / GraphSAGE / grafo de conhecimento | Inexistentes. Só um grafo `networkx` simples na percepção; `neo4j` e `torch` estão nas dependências sem uso efetivo. |
| Janela adaptativa 50–500 ms | Não encontrada no código. |
| `IntentClassifier` | *Stub*: RandomForest treinada com 10 amostras aleatórias. |
| Reserva determinística (contrato F1↔F2) | Não verificada em lugar algum. |

### 4.3 Interoperabilidade E2

- O código da Fase 2 parou antes das correções da Fase 1. Exemplo: `control_dispatcher.py` ainda chama `rmr_send(payload, 12010, target_node)`, passando o nó como `retries` (achado 1 da Fase 1: todo controle real falharia).
- E2SM-RC: cota de PRB mapeada em Style 1 / Action 1 (Style 1 é *Radio Bearer Control*); a Fase 1 corrigiu para Style 2 / Action 6. `TX_POWER` em Style 2 / Action 1 não existe na norma.
- O README declara E2AP v02.03, RC v01.03 e KPM v02.03; o perfil da Fase 1 diz que a Fase 2 mira E2AP v03.01, KPM v08.00 e RC v10.00; o testbed exigirá o que o E2 Agent da CU/DU implementar. Hoje não há perfil coerente.
- `SrsranE2Adapter` abre socket SCTP/TCP direto da xApp para o E2T/gNB. Numa implantação O-RAN SC, a xApp fala RMR/REST com o E2Term e o SubMgr, não SCTP com a RAN.
- `deploy/openran-br-v3/README.md` se diz "homologado em conformidade com consórcio OpenRAN@Brasil (LABORA/UFG, CPQD, INATEL, UFPA PCT)" sem nenhum registro dessa homologação.

### 4.4 Engenharia e higiene

- CI: as três últimas execuções do workflow `CI - RDL xApp` falharam (29 e 30/09/2026). O workflow chama `scripts/run_pyright_check.py` e `scripts/validate_ml_provenance.py`, que não existem no repositório.
- README referencia `src.orchestration.decision_engine`, módulo inexistente.
- Não há arquivo `LICENSE`, embora o README declare Apache 2.0 (necessário para o E4.3 do GreenRAN).
- O README publica o token do InfluxDB e as senhas do Grafana/InfluxDB. São da bancada local, mas convém trocá-los e retirá-los.
- `configs/testbed_sdr/cots_ue_provisioning.md` traz Ki/OPc de SIM de teste. Aceitável apenas se forem valores de teste que nunca irão para um SIM do testbed.
- Repositório de 245 MB, dos quais ~135 MB são figuras; `scratch/` contém textos integrais de artigos do arXiv, figuras de referência e um arquivo sem relação com o projeto (`200_Questoes_Contratacao_TI_Lei14133...md`). Há risco de direitos autorais e de ruído para avaliadores.
- Link público para uma pasta do Google Drive no README.

### 4.5 O que vale aproveitar da Fase 2

- A ideia de níveis (heurística → utilidade → MARL) com a H-RDL como reserva determinística, desde que reimplementada sobre o código atual da Fase 1.
- As xApps de referência (*beamformer*, *isac-radar*, *rogue-xapp*) como geradores de propostas, após revisão.
- Os campos opcionais do contrato (`context_features`, `confidence_score`, `marl_agent_id`), já aceitos pela Fase 1.

---

## 5. Levantamento da Fase 1 (H-RDL)

### 5.1 Pontos fortes para o GreenRAN

- **Alinhamento direto com o problema**: o par xSlice × Energy Saving dos cenários S1/EEVS é o par xApp1-RANSlicer × xApp2-EnergySaver da proposta.
- **E2 real com a ferramenta do próprio grupo**: o NORI é o trabalho citado na proposta (Oliveira et al., SBrT 2025, com Klautau), com RIC O-RAN SC Release I em Kubernetes.
- **Rigor de evidência**: pré-registros (v2–v7), resultados negativos registrados, proveniência por execução, dissecação E2AP confirmada pelo tshark, certificador automático, limpeza de dados sintéticos. Isso atende ao padrão de relatórios quadrimestrais e whitepaper (E4.1/E4.2).
- **Segurança**: Safety Guard por proposta, impedindo que uma xApp maliciosa vete ações legítimas, e xApp *rogue* de referência, base para contribuir com A1.11/O1.5.
- **Implantação**: Helm, receita do RIC, observabilidade (InfluxDB/Grafana), documentação numerada.

### 5.2 Lacunas para o testbed

1. **Só NORI**: nenhuma execução com CU/DU real. srsRAN tem adaptador e configs (n78, B210, Open5GS) nunca executados; OAI não tem nada.
2. **Ações atuáveis**: no E2 real, só a cota de PRB no gNB 0. Potência, *handover* e desligamento ficam "decididos, não atuáveis".
3. **Conflito entre células** não detectado (achado 11). O xApp2-EnergySaver da proposta atua exatamente quando UEs estão na borda entre duas RUs.
4. **A1 desconectado** da decisão: sem caminho para o rApp-ResourceOptimizer influenciar a RDL.
5. **Energia não medida**: nenhuma métrica de consumo no KPM nem no ns-3; os ganhos "green" não são mensuráveis hoje.
6. **G6 não certificado** e claims C1–C6 `NOT_VERIFIED`.
7. **Recursos da bancada**: host com 7,7 GB de RAM e WSL com 5 GB, com reinícios e perda de rotas do RIC (achados 50–51). Inviável como ambiente de integração do projeto; o testbed precisa de servidor dedicado.
8. **Inconsistências internas de documentação**: `docs/07` §2 ainda diz que o codec RC é "não normativo" e o A1 "não conectado"; §5 lista "fechar o loop (G4)" como pendente, enquanto o README e a tabela de gates dão G4 como certificado. A xApp principal (`RDLxApp`) e a xApp que fechou o loop na bancada (`kpm-probe` com `src/e2/v3/codec.py`) não são a mesma: deixar claro qual caminho vai para o testbed. Uma linha da tabela "Estado atual" do README tem uma coluna a mais.

---

## 6. Recomendações e roteiro

> **Atualização (2026-11-10):** feitos no código da Fase 1, sem execução no testbed (achado 52 de `docs/07`):
> - **6.3, item 7:** conflitos entre células detectados e respeitados pelo EEVS.
> - **6.3, item 8:** política A1 ligada à decisão, com o tipo 20001 `GreenRAN_Intent_Policy`.
> - **6.2, item 6, parcial:** parâmetro `CELL_STATE`, com despacho *fail-closed* até o nó anunciar a capacidade.
> - **6.3, item 1, só o modelo:** `configs/testbed_ufpa/profile.yaml`.
>
> As perguntas ao hospedeiro e os gates GR1–GR4 estão em `docs/compliance/GREENRAN_UFPA_TESTBED_PROFILE.md`. Ainda faltam a métrica de energia (6.3, item 9) e tudo o que depende do testbed (TB1–TB10).

### 6.1 Imediato (antes de qualquer apresentação ao GreenRAN)

1. **Sanear a Fase 2**: aplicar o mesmo procedimento do achado 45 da Fase 1 (remover `experiments/runs/S1_*`, `certified_closed_loop_chain`, `experiments/results`, tabelas manuais, `scratch/`), voltar C1–C6 para `NOT_VERIFIED`, retirar do README "Validada Experimentalmente (N=30)", "homologado OpenRAN@Brasil", credenciais e o link do Drive; adicionar `LICENSE`; consertar ou remover os passos do CI que chamam scripts inexistentes.
2. **Rebasear a Fase 2 sobre a Fase 1**: a CA-RDL deve importar o núcleo atual da Fase 1 (pacote ou submódulo), não manter uma cópia antiga. Só o motor de contexto/MARL fica na Fase 2.
3. **Corrigir a documentação da Fase 1** apontada em 5.2 item 8.

### 6.2 Alinhamento com o hospedeiro (UFPA/LASSE, PT1)

4. Confirmar com a equipe do testbed: CU/DU (OAI ou srsRAN e versão), E2 Agent e versões E2AP/KPM/RC, release do RIC, quantas RUs por gNB, se haverá Non-RT RIC (qual) e *policy types* A1.
5. Propor a RDL como **camada de coordenação Near-RT entre xApp1 e xApp2**, abaixo do rApp-ResourceOptimizer: o rApp define objetivos por A1, a RDL garante que as ações das duas xApps numa mesma janela não conflitem e respeitem limites. Isso complementa a proposta sem disputar entregáveis da UFRGS/UNICAMP.
6. Combinar o formato dos controles de potência e desligamento que sairão das atividades 1.2 e 1.3 (RC customizado ou E2SM-CCC) para que o Refinement e o mapeador RC já nasçam compatíveis.

### 6.3 Técnico (Fase 1 → testbed)

| Ordem | Entrega | Gate |
| :-: | :-- | :-- |
| 1 | Perfil do testbed congelado (versões, commits, hashes) | TB0 |
| 2 | Bancada srsRAN ou OAI + Open5GS em ZMQ (sem rádio), no padrão `scripts/certification/` | TB1–TB4 |
| 3 | RC de cota de PRB contra o E2 Agent real, com ACK | TB5–TB6 |
| 4 | Arbitragem entre duas xApps reais (RANSlicer e EnergySaver de referência) | TB7 |
| 5 | Closed loop com efeito medido no KPM do testbed | TB8 |
| 6 | Mesmas decisões no NORI e no backend real | TB9 |
| 7 | Detecção de conflitos entre células (vizinhança de RUs, *handover* × desligamento) | novo cenário |
| 8 | Ligação A1 → pesos TVS/EEVS e limites; *policy type* acordado com o rApp | novo gate |
| 9 | Métrica de energia (KPM ou O1) e cenário GreenRAN: câmeras 4K a 25 Mb/s, < 100 ms + fatia mMTC | novo cenário |
| 10 | Ilha física com RU e UE comercial | TB10 |

### 6.4 Científico (Fase 2 reconstruída)

- Treinar o Safe-MAPPO no NORI com E2 real (ambiente Gymnasium que conversa com a kpm-probe), registrar *checkpoints* com proveniência e carregá-los na inferência.
- Medir a reserva determinística (decisão em ≤ 200 ms com *fallback* para H-RDL) como gate próprio.
- Pré-registrar a comparação H-RDL × CA-RDL no cenário GreenRAN antes de executar, como já é feito na Fase 1.
- Implementar GNN/grafo apenas se houver hipótese que precise deles (por exemplo, conflitos entre células); caso contrário, retirar das alegações.

---

## 7. Avaliação das xApps de referência e dos cenários S9–S15 (2026-11-10)

### 7.1 xApps de referência (`reference-xapps/`)

Origem declarada e o que cada xApp de fato faz. Nenhuma lê KPM: todas geram propostas a partir de valores de configuração.

| xApp | Origem | Parâmetro proposto | Aceito pela RDL (default-deny) | Entrega a proposta à RDL? |
| :-- | :-- | :-- | :-: | :-- |
| xSlice | inspirada em Yan et al. (`peihaoY/xslice-oran`), sem código dele | `PRB_QUOTA` | sim | HTTP para `RDL_HTTP_URL`, mas a RDL só recebe propostas por RMR (mtype 30000): **não chega** |
| Energy Saving | inspirada em Wadud et al. (`xapp_es_with_cell_util`), sem código dele | `TX_POWER` | sim | idem: **não chega** |
| Traffic Steering | inspirada no papel da `o-ran-sc/ric-app-ts`, sem código dela | `HANDOVER` | sim | idem: **não chega** |
| Beamformer | **própria** | `VERTICAL_DOWNTILT` | **não** (fora do catálogo) | não envia |
| ISAC Radar | **própria** | `SENSING_RATIO` | **não** | não envia |
| Load Balancer | **própria** (a docstring dizia "O-RAN SC Standard lb-xapp") | `LOAD_THRESHOLD` | **não** | não envia |
| Bouncer | **própria** (a docstring dizia "O-RAN SC Standard b-xapp") | `PING_INTERVAL` | **não** | não envia |
| Rogue | **própria** | `TX_POWER` 45/5 dBm alternados | 5 dBm sim, 45 dBm não | não envia |
| kpm-probe (`deploy/helm/xapp-kpm-probe`) | **própria** | assina KPM e envia RIC Control | — | é a única que fala E2 com o RIC (G1, G3, G4, G5) |

Constatações:

1. **As xApps próprias não são adequadas como geradoras de conflito real.** Quatro das cinco propõem parâmetros que a RDL rejeita por *default-deny*, nenhuma envia propostas, nenhuma lê KPM, e todas emitem um valor fixo em laço. Servem hoje só como exemplos de formato. A Rogue é a exceção útil: exercita o Safety Guard, mas também não envia.
2. **Nos experimentos, as propostas vêm do catálogo** (`simulations/ns3/conflicts/catalog.json`), não destes processos (docs/03 §3). Os resultados de S0–S8 não dependem das xApps de referência.
3. **Contrato do `HANDOVER` incoerente** (corrigido): o Traffic Steering enviava `value = 1.0` ("disparo") e o destino em `target_node`, que a RDL ignora. A RDL e as regras entre células tratam `value` como índice da célula de destino. Agora `value` sai do sufixo de `target_node` (`gnb_02` → 2), e o resolvedor preserva o zero à esquerda (`gnb_01` + 2 → `gnb_02`).
4. **Descrições corrigidas:**
   - Load Balancer e Bouncer se apresentavam como xApps padrão do O-RAN SC.
   - Beamformer e ISAC anunciavam parâmetros não implementados (`BEAM_WEIGHTS`, `RADAR_BURST_PERIOD`).
   - A Rogue anunciava `PRB_QUOTA` inválida, que não gera.
5. **Para o GreenRAN**, as xApps que importam são o xApp1-RANSlicer (UFRGS) e o xApp2-EnergySaver (UFPA), que ainda não existem. As xSlice e Energy Saving locais cobrem esses papéis só no formato.
   - **Para servir de stand-ins no testbed:** enviar por RMR 30000 (ou a RDL ganhar um endpoint HTTP de propostas) e ler KPM.
   - **Energy Saving:** propor `CELL_STATE` além de `TX_POWER`.
   - **Própria ISAC/Beamformer:** não têm papel no GreenRAN.

O teste `tests/integration/test_all_reference_xapps.py::test_reference_xapps_contract_with_rdl_safety_guard` fixa o que a RDL aceita de cada xApp.

### 7.2 Cenários S9–S15

Os arquivos estão só no repositório da Fase 2 (`simulations/ns3/scenario_rdl_s9…s15*.cc`); na Fase 1 foram removidos em 2026-11-09 (achado 45), sem nunca terem rodado com proveniência.

| Cenário | Declara | O que o código faz |
| :-- | :-- | :-- |
| S9 NTN Orbital Handover | handover LEO com Doppler | nós "satélite" e "gNB" ligados aos UEs por **cabo ponto a ponto** (100 Mb/s, 20 ms) com UDP; sem canal NTN, sem handover; `--enableE2` declarado e não usado |
| S10 UAV Swarm | handover de emergência por bateria | ponto a ponto + UDP; sem bateria, sem handover |
| S11 V2X Platooning | handover preditivo a 120 km/h | veículos em movimento, mas ligados por cabo ponto a ponto: o movimento não afeta nada |
| S12 IIoT | fatiamento com jitter < 0,8 ms | ponto a ponto + UDP; jitter e TSN só nos comentários |
| S13 SAGIN | resgate multidomínio | ponto a ponto + UDP |
| S14 ISAC | radar × comunicação | ponto a ponto + UDP; alvos móveis sem sensoriamento |
| S15 Rogue NTN | sequestro de *feeder link* | ponto a ponto + UDP |

Em todos os sete:

- nenhum usa o rádio NR (`NrHelper`);
- nenhum aplica ações da RDL (não usam `rdl-nr-common.h` nem o catálogo);
- nenhum controla a semente;
- todos terminam imprimindo "executado com sucesso".

**Avaliação:** não modelam o fenômeno que declaram e não exercitam a RDL. Rodá-los produziria FlowMonitor de enlaces cabeados, sem valor como evidência; por isso não foram executados.

**Aderência ao GreenRAN** (verticais Agro e Campus; casos eMBB de câmeras e mMTC de sensores):

| Cenário | Aderência | Motivo |
| :-- | :-- | :-- |
| S9 (NTN) | parcial | a proposta prevê NTN *direct-to-cell* (Skylo) para mMTC rural, mas como enlace de sensores, não como handover LEO |
| S13 (resiliência) | parcial | conectividade rural |
| S15 | parcial | segurança (atividade A1.11) |
| S10, S11, S12, S14 | nenhuma | UAV, V2X, IIoT/TSN e ISAC não fazem parte da proposta |

**Recomendação:** não portar S9–S15 como estão. Substituí-los por cenários GreenRAN no padrão de S0–S8 (5G-LENA, catálogo, atuação, sementes):

- **G1:** fatia eMBB de câmeras × fatia mMTC de sensores (RANSlicer × EnergySaver na mesma célula, cota de PRB).
- **G2:** baixa demanda noturna com UEs na borda entre duas RUs (desligamento × handover, regra entre células; exige atuar `CELL_STATE` em `rdl-nr-common.h`).
- **G3, opcional:** sensores mMTC por enlace NTN, se o ns-3 da pilha tiver o modelo de propagação NTN do 3GPP TR 38.811 utilizável com o 5G-LENA.

### 7.3 Estado em 2026-11-11

O que mudou depois desta avaliação. Commits: Fase 1 `a0cb21eb`, `48fab8eb` e `4924e7e4` (`main`); Fase 2 `19822d8` (`main`, merge do ramo `fase2-sobre-fase1` em 2026-11-11).

**Cenários S9–S15 e GreenRAN G1–G2.** Os sete cenários foram reescritos no padrão de S0–S8, com:

- rádio NR do 5G-LENA, num cenário multicélula paramétrico (`simulations/ns3/scenario_rdl_multicell.cc`);
- propostas e topologia no catálogo, atuação das ações da RDL e semente controlada;
- canal NTN-Rural com posição geocêntrica em S9 e S15.

O teste curto (uma semente, B0 e B3) está em `docs/03` §2.4. Os números servem para mostrar que os cenários rodam, não como evidência:

- **G2:** o B3 evita derrubar o serviço (1,80 contra 0,04 Mb/s).
- **G1:** o B3 protege a fatia de câmeras.
- **Pioras do B3:** S10 (atraso maior) e S13 (não evacua a célula em falha, achado 55).
- **Sem conflito efetivo:** S12 e S14, cuja carga não chega ao teto de PRB (achado 57).

**xApps de referência:**

- Beamformer, ISAC Radar, Load Balancer e Bouncer foram removidas (achado 58).
- Restam xSlice, Energy Saving, Traffic Steering e Rogue. Nenhuma entrega propostas à RDL implantada: falta enviar por RMR 30000.

**Gates do GreenRAN.** Lógica implementada e testada, sem execução no testbed:

| Gate | Implementado | Falta |
| :-- | :-- | :-- |
| GR1 (política A1 muda a decisão) | caminho A1-PMS → adaptador → A1 Mediator → RMR → xApp; o kpm-probe responde 20010/20011, consulta 20012 e repassa a política ao B3 | implantar o kpm-probe novo e ver a política `ENFORCED` mudar um RIC Control real |
| GR2 (conflito entre células) | regras `HANDOVER_INTO_REDUCED_CELL`, `HANDOVER_PING_PONG` e `NEIGHBOR_SLEEP`; campanha 08 (S4/S5, 10/10 detecções) | H9.2 e H9.3 refutadas: detectar não bastou para ganhar em S4 |
| GR3 (`CELL_STATE`) | atuação no ns-3 (−30 dBm; os UEs entram em RLF e se reconectam) | nó E2 real que aceite o parâmetro (OAI/srsRAN do testbed) |
| GR4 (testbed) | perfil em `docs/compliance/GREENRAN_UFPA_TESTBED_PROFILE.md` | tudo: depende do acesso ao testbed |

**Grafo de conhecimento.** Implementado na Fase 1 (`src/core/knowledge_graph.py`, alimentado pela Percepção e exposto em `GET /kg`). A Fase 2 usa o mesmo grafo pela `RDLxApp` e registra no `DecisionRecord` o contexto que dele extrai.

**Janela de decisão.** `src/core/decision_window.py` define três classes de urgência:

- **CRITICAL:** age sem esperar os 200 ms;
- **URGENT:** janela curta;
- **NORMAL:** janela padrão.

Ações que não cabem no Near-RT RIC (dApps no DU/CU, política E2SM-RC, guarda no DU) estão descritas como alternativa em `docs/09_frameworks_e_acoes_criticas.md`.

**SMO.** O O-RAN SC A1-PMS 2.8.0 roda por Helm (`deploy/helm/a1pms`) com um adaptador próprio (achado 56) e um rApp de exemplo (`rapps/greenran_resource_optimizer.py`). O SMO completo (ONAP/OSC) ficou documentado como passo a passo para o testbed UFPA (`docs/10_smo_non_rt_ric_e_rapp.md`): não cabe nesta máquina.

**MAPPO da Fase 2.** Treinado num ambiente calibrado pela curva medida no NORI (`XApp-RDL-F2/docs/15_treino_mappo_calibrado.md`):

- duas de três sementes trocam SLA por energia dentro do limite do CMDP;
- a terceira não converge para uma política segura (34 % de violações);
- não é evidência de RAN (`publication_eligible: false`).

**Pendências que bloqueiam o uso no GreenRAN:**

1. Validação pré-registrada CA-RDL × H-RDL no NORI, com critério de seleção de semente fixado antes.
2. Campanha pareada de S9–S15/G1–G2, com mais carga em S12 e S14.
3. Correção pré-registrada da utilidade do EEVS (achado 55).
4. Entrega de propostas das xApps por RMR 30000.
5. GR1 com o kpm-probe implantado.
6. Execução no testbed UFPA.

## 8. Referências internas

- Fase 1: `README.md`, `docs/07_certificacao_e_achados.md` (achados 1, 11, 12, 25, 45, 50, 51), `docs/compliance/OPENRAN_BRASIL_INTEGRATION.md`, `docs/compliance/HRDL_F1_SRSRAN_TESTBED_PROFILE.md`, `docs/compliance/PHASE1_PHASE2_SYNC_CONTRACT.md`, `specs/claims.yaml`.
- Fase 2: `README.md`, `specs/claims.yaml`, `src/agents/marl/{mappo_agent,mappo_trainer,intent_classifier}.py`, `src/agents/marl/environments/nori_ran_environment.py`, `src/e2/rc/capability_registry.py`, `src/e2/backends/srsran_e2_adapter.py`, `src/coordination/control_dispatcher.py`, `experiments/runs/S1_B6_seed1001/`, `experiments/runs/certified_closed_loop_chain/`, `experiments/training/seed_042/training_manifest.json`, `.github/workflows/`. Esses caminhos descrevem a `main` de 2026-09-30, lida para as seções 1–6.
- Fase 2 reconstruída (`main` desde `19822d8`): `cardl/engine.py`, `cardl/marl/{calibration,env,mappo,baselines,train}.py`, `experiments/training/mappo_seed{101,102,103}/`, `docs/15_treino_mappo_calibrado.md`.
- Proposta: *GreenRAN*, Anexo II, Programa OpenRAN@Brasil Etapa 2, 24/10/2025, seções 6.1–7.3.
