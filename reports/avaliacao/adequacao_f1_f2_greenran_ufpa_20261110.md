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

## 7. Referências internas

- Fase 1: `README.md`, `docs/07_certificacao_e_achados.md` (achados 1, 11, 12, 25, 45, 50, 51), `docs/compliance/OPENRAN_BRASIL_INTEGRATION.md`, `docs/compliance/HRDL_F1_SRSRAN_TESTBED_PROFILE.md`, `docs/compliance/PHASE1_PHASE2_SYNC_CONTRACT.md`, `specs/claims.yaml`.
- Fase 2: `README.md`, `specs/claims.yaml`, `src/agents/marl/{mappo_agent,mappo_trainer,intent_classifier}.py`, `src/agents/marl/environments/nori_ran_environment.py`, `src/e2/rc/capability_registry.py`, `src/e2/backends/srsran_e2_adapter.py`, `src/coordination/control_dispatcher.py`, `experiments/runs/S1_B6_seed1001/`, `experiments/runs/certified_closed_loop_chain/`, `experiments/training/seed_042/training_manifest.json`, `.github/workflows/`.
- Proposta: *GreenRAN*, Anexo II, Programa OpenRAN@Brasil Etapa 2, 24/10/2025, seções 6.1–7.3.
