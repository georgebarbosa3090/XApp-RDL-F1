# 06 — Metodologia e resultados

## 1. Pergunta avaliada

Quando várias xApps propõem controles conflitantes, a decisão da RDL-N1 leva a um desempenho de rede melhor ou mais seguro que alternativas simples (sem coordenação, FIFO, prioridade estática)?

Esta campanha avalia a **decisão** em malha aberta: as propostas são decididas por cada baseline e as ações resultantes são aplicadas na RAN simulada. Não há E2 nem realimentação de KPM; o closed loop é objeto da pilha NORI (gates G1–G4).

## 2. Desenho

| Elemento | Escolha |
| :-- | :-- |
| Simulador | ns-3.48 (`d2add90`) + 5G-LENA v5.1 (`cedcead`), perfil otimizado |
| Cenários | S0–S7 ([taxonomia](03_cenarios_e_conflitos.md)); S0 é controle sem conflito |
| Propostas | definidas por cenário em [`catalog.json`](../simulations/ns3/conflicts/catalog.json): mesma carga de conflito para todos os baselines e sementes |
| Baselines | B0 sem coordenação; B1 FIFO por janela e alvo; B2 prioridade estática por janela e alvo; B3 RDL-N1 |
| Janela de decisão | 200 ms; em B1–B3 a ação decidida é aplicada no fechamento da janela; em B0, na chegada |
| Atuação | PRB pela máscara de RBGs do escalonador; potência via `NrGnbPhy::SetTxPower`; handover X2 escalonado em 10 ms por UE |
| Sementes | 1001–1005, pareadas (mesma semente em todos os baselines de um cenário) |
| Medição | vazão e atraso por célula a cada 100 ms nos `UdpServer` dos UEs (`rdl_kpi_timeseries.csv`); ações aplicadas (`rdl_actuation_log.csv`) |

### 2.1 Como o B3 usa a RDL-N1 real

O driver ([`run_conflict_experiment.py`](../scripts/certification/run_conflict_experiment.py)) instancia a `RDLxApp` e chama `_process_action_group` para as propostas de cada janela, como a xApp faria em operação. Duas adaptações, ambas registradas no `decision_log.json`:

- o relógio do Refinement (histerese) é substituído pelo relógio simulado;
- o despacho E2 é capturado em vez de enviado; a ação capturada vira linha do cronograma e é registrada como confirmada (na simulação, a atuação é garantida).

### 2.2 Métricas

| Métrica | Definição |
| :-- | :-- |
| Vazão antes / no conflito / depois | média da vazão agregada (soma das células) nas janelas antes, durante e depois do intervalo de conflito do catálogo |
| Atraso no conflito | atraso médio fim a fim ponderado por pacote durante o conflito |
| Ações aplicadas, handovers | ações com status `APPLIED` no log de atuação |
| Ações inseguras aplicadas | `TX_POWER` fora de [−10, 43] dBm ou `PRB_QUOTA` fora de [0, 100] que chegaram à RAN |
| Oscilações | trocas de valor num mesmo alvo (gNB, parâmetro) |

Agregação por cenário × baseline: média, desvio-padrão e IC 95% (t de Student) quando n ≥ 2. Fluxos internos do EPC (GTP-C, porta 2123) não entram, porque a medição é feita nos servidores de aplicação dos UEs.

## 3. Proveniência

Cada execução tem manifesto, logs, saídas brutas e hashes em `experiments/runs/nr_<S>_<B>_seed<N>/` (formato em [04 §3](04_instalacao_e_operacao.md#3-executar-um-cenário-com-proveniência)). A análise ([`analyze_conflict_runs.py`](../scripts/certification/analyze_conflict_runs.py)) só usa execuções elegíveis no certificador e lista as ignoradas com o motivo.

Mudanças de método durante a campanha, todas registradas:

- 2026-11-08: os handovers passaram a ser escalonados em 10 ms por UE, e S2, S4 e S5 passaram a rodar com `--disableSrs=true`, porque o 5G-LENA v5.1 abortava em handover em massa. As execuções de S2, S4 e S5 feitas antes disso foram descartadas e refeitas; as falhas do simulador estão preservadas em `experiments/runs_failed/`.
- S0, S1, S3 e S7 (só B0 e B3) da semente 1001 foram executados antes dessas mudanças; elas não afetam cenários sem handover (a opção `--disableSrs` fica desligada e os cronogramas desses cenários não têm `HANDOVER`), mas o hash da fonte do cenário difere entre essas execuções e as posteriores (campo `scenario_sha256`). No S7 da semente 1001 isso ocorre dentro do mesmo conjunto pareado: B0/B3 com uma fonte e B1/B2 com a outra.
- 2026-11-08: `run_conflict_campaign.py` removia execuções interrompidas (sem `hashes.sha256`) mas não as recolocava na fila; corrigido, elas passam a ser refeitas na mesma rodada.
- 2026-11-13 (achado 68 de `docs/07`): o manifesto passa a gravar `repo_git_sha_full`, `repo_dirty` e `repo_dirty_paths` (mudanças não commitadas em `src/`, `scripts/`, `simulations/`, `configs/` e nas pastas de xApps), e o certificador reporta o commit na regra informativa R15. As execuções anteriores têm só `repo_git_sha` (7 caracteres) e não registram se a árvore estava suja.
- Regressão de decisão: `tests/integration/test_schedule_replay.py` refaz, com o código atual, o cronograma de cada execução nativa registrada e confere o `action_schedule_sha256` do manifesto (achado 69).

## 4. Resultados da pilha nativa (malha aberta, sem E2)

**Campanha concluída em 2026-11-08:** S0–S7 × B0–B3 × sementes 1001–1005, 160 execuções nativas (ns-3.48 + 5G-LENA v5.1), todas com `run_status: SUCCESS` e hashes conferidos. Relatório completo, com a tabela por execução: [`reports/conflicts/conflict_analysis_20261108T103510Z.md`](../reports/conflicts/conflict_analysis_20261108T103510Z.md). Certificado: [`reports/certification/certificate_20261108T103515Z.md`](../reports/certification/certificate_20261108T103515Z.md) (G0 CERTIFIED; G1–G6 não certificados, porque a avaliação é em malha aberta).

Média ± IC 95 % (t de Student), n = 5 por célula.

| Cenário | Baseline | Vazão no conflito (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras aplicadas | Oscilações |
| :-- | :-- | --: | --: | --: | --: | --: | --: |
| S0 | B0 | 2,63 ± 0,47 | 34,50 ± 12,26 | 2 | 0 | 0 | 0 |
| S0 | B1 = B2 = B3 | 2,68 ± 0,49 | 29,45 ± 10,93 | 2 | 0 | 0 | 0 |
| S1 | B0 | 118,04 ± 0,02 | 17,05 ± 0,00 | 10 | 0 | 0 | 9 |
| S1 | B1 = B2 = B3 | 278,97 ± 0,02 | 9,14 ± 0,00 | 5 | 0 | 0 | 0 |
| S2 | B0 | 197,49 ± 0,06 | 7,42 ± 0,84 | 5,8 | 0,8 | 0 | 0 |
| S2 | B1 = B2 | 197,56 ± 0,09 | 7,48 ± 0,90 | 5,8 | 0,8 | 0 | 0 |
| S2 | B3 | 193,24 ± 14,89 | 26,16 ± 23,40 | 5 | 0 | 0 | 0 |
| S3 | B0 | 12,20 ± 0,09 | 14,13 ± 12,72 | 10 | 0 | 0 | 9 |
| S3 | B1 = B2 = B3 | 11,86 ± 0,96 | 27,86 ± 44,55 | 5 | 0 | 0 | 0 |
| S4 | B0 | 23,87 ± 0,19 | 152,90 ± 0,79 | 11 | 1 | 0 | 0 |
| S4 | B1 = B2 | 23,75 ± 0,25 | 150,23 ± 1,02 | 11 | 1 | 0 | 0 |
| S4 | B3 | 23,75 ± 0,25 | 150,23 ± 1,02 | 10 | 1 | 0 | 0 |
| S5 | B0 | 9,02 ± 0,09 | 31,09 ± 6,69 | 8 | 8 | 0 | 0 |
| S5 | B1 = B2 = B3 | 9,01 ± 0,11 | 30,68 ± 6,89 | 8 | 8 | 0 | 0 |
| S6 | B0 | 18,97 ± 1,74 | 94,38 ± 12,82 | 80 | 0 | 0 | 57 |
| S6 | B1 | 20,65 ± 2,14 | 63,10 ± 14,90 | 55 | 0 | 0 | 9 |
| S6 | B2 | 20,74 ± 1,87 | 67,69 ± 18,49 | 55 | 0 | 0 | 9 |
| S6 | B3 | 21,19 ± 1,41 | 51,33 ± 6,67 | 25 | 0 | 0 | 0 |
| S7 | B0 | 5,54 ± 0,01 | 10,54 ± 0,35 | 15 | 0 | 10 | 0 |
| S7 | B1 = B2 | 5,49 ± 0,01 | 13,24 ± 0,77 | 15 | 0 | 10 | 0 |
| S7 | B3 | 5,48 ± 0,01 | 13,55 ± 0,73 | 5 | 0 | 0 | 0 |

Contagens (ações, handovers, inseguras, oscilações) sem IC são constantes nas cinco sementes.

### 4.1 Baselines com o mesmo cronograma

Linhas marcadas "B1 = B2 = B3" ou "B1 = B2" não são coincidência de medição: esses baselines produziram cronogramas de ações byte a byte iguais (mesmo `action_schedule_sha256` no manifesto), e com a mesma semente a simulação é a mesma.

| Cenário | Grupos com cronograma idêntico |
| :-- | :-- |
| S0, S1, S3, S5 | B0 · B1 = B2 = B3 |
| S2, S4, S7 | B0 · B1 = B2 · B3 |
| S6 | B0 · B1 · B2 · B3 (todos diferentes) |

Consequência: em S0, S1, S3 e S5 a campanha não distingue a RDL-N1 de FIFO ou prioridade estática; o que se mede ali é o efeito de coordenar versus não coordenar. A comparação específica da RDL-N1 só existe em S2, S4, S6 e S7.

### 4.2 Leitura

- **S1 (conflito direto de PRB):** coordenar elimina as 9 oscilações e eleva a vazão no conflito de 118 para 279 Mbps, com o atraso caindo de 17,1 para 9,1 ms. O ganho é de qualquer coordenação (B1–B3 decidem igual), não específico da RDL-N1. Sem coordenação, a xApp de energia escreve por último e a cota fica em 30 % na maior parte do tempo.
- **S6 (tempestade de conflitos):** a RDL-N1 aplica 25 ações (contra 55 do B1/B2 e 80 do B0) e zera as oscilações (9 no B1/B2, 57 no B0). O atraso no conflito é o menor (51,3 ± 6,7 ms). Os ICs por baseline se sobrepõem aos do B1 e do B2, mas a diferença pareada por semente exclui zero contra os três: B3 − B0 = −43,1 ± 11,0 ms, B3 − B1 = −11,8 ± 11,3 ms, B3 − B2 = −16,4 ± 12,5 ms, com o B3 melhor nas 5 sementes. A vazão não difere de forma distinguível entre os quatro.
- **S7 (injeção de falha):** só a RDL-N1 impede que as 10 ações inseguras (potência de 60 dBm, cota de 150 %) cheguem à RAN; B1 e B2 escolhem por janela e alvo, mas não validam valores. A vazão é igual; o atraso é menor no B0 (10,5 ms contra 13,2–13,6 ms), efeito de redução de interferência e não da arbitragem (achado 3 da seção 6).
- **S2 (handover × QoS):** a RDL-N1 evita o handover (0 contra 0,8 em média), mas o atraso no conflito fica maior e mais variável (26,2 ± 23,4 ms contra ~7,5 ms) e a vazão mais variável. Resultado desfavorável à RDL-N1 neste cenário, a investigar.
- **S4 e S5 (conflitos entre células):** a RDL-N1 remove uma ação no S4 sem efeito nos KPIs, e o handover ocorre igual; no S5 os quatro baselines aplicam os mesmos 8 handovers. Coerente com a limitação do achado 2 da seção 6 (a percepção não relaciona ações em células diferentes).
- **S0 (sem conflito):** sem diferença distinguível entre baselines, como esperado.

Sobreposição de IC não é um teste de hipótese pareado; com n = 5 os resultados indicam comportamento e não sustentam afirmações estatísticas fortes.

### 4.3 Relatório completo

O relatório [`relatorio_campanha_20261108T110655Z.md`](../reports/conflicts/relatorio_campanha_20261108T110655Z.md), gerado por [`generate_campaign_report.py`](../scripts/certification/generate_campaign_report.py), traz as hipóteses H0–H7 com critérios e vereditos (seis suportadas; H2 e H3 inconclusivas), uma tabela por semente com todas as métricas, as diferenças pareadas B3 − Bx, as conclusões, os comandos de execução no terminal WSL/Ubuntu e o comando ns-3 de cada execução.

### 4.4 Campanhas pré-registradas posteriores (pilha nativa, malha aberta)

Os resultados completos, com as tabelas geradas pelos scripts, ficam nos pré-registros. Resumo:

| Pré-registro | Desenho | Resultado |
| :-- | :-- | :-- |
| [08](preregistros/08_conflitos_entre_celulas_s4_s5.md) | regras entre células; S4/S5 × B0–B3 × sementes 1006–1010 | H9.1 confirmada (10/10); H9.2 refutada no S5/B3 (handovers sem UEs); H9.3 refutada (vazão do S4 menor no B3); no S4 a semente não varia o resultado (achado 54) |
| [09](preregistros/09_eevs_aditivo.md) | EEVS aditivo (B3A) contra a média (B3) em S2, S13 e S15; sementes 12001–12005 | H10.1–H10.3 confirmadas; o B3A evacua a célula em falha no S13; o aditivo virou o padrão (achado 66) |
| [10](preregistros/10_campanha_s9_s15_g1_g2.md) | S9–S13, S15, G1, G2 × B0–B3 × sementes 11001–11005 (S14 excluído antes da campanha) | H11.1–H11.5 confirmadas (5/5); penalidade de atraso no S9 e no S10 (o S15 reproduz o S9 semente a semente); ressalvas de replicação e de natureza das hipóteses no §6 do pré-registro |

## 5. Resultados com E2 real (bancada NORI)

Resultados das fases da cadeia E2 real (Near-RT RIC Release I + NORI + xApp kpm-probe), em ordem cronológica. Os comandos estão em [04](04_instalacao_e_operacao.md) e [05](05_observabilidade_e_campanhas.md); os pré-registros, em [preregistros/](preregistros/README.md).

### 5.1 Primeira execução E2: E2 Setup real (2026-11-08)

[`experiments/runs/nori_rc_demo_seed1`](../experiments/runs/nori_rc_demo_seed1/execution_manifest.json): `nori-rc-slicing-demo`, semente 1, 10 s em tempo real, contra o E2Term da Release I.

- **E2 Setup real concluído.** O NORI enviou o E2-SETUP-REQUEST e recebeu SETUP-RESPONSE-SUCCESS do Near-RT RIC. O PCAP (`raw/e2_sctp.pcap`, 12 pacotes) tem o handshake SCTP (INIT, INIT ACK, COOKIE ECHO, COOKIE ACK), o DATA do gNB com o pedido, o DATA do RIC com PPID 70 (E2AP) e o encerramento SHUTDOWN.
- O E2Mgr registrou o nó `gnb_268_341_00000001` na R-NIB com três funções RAN: 4 (CCC), 200 (KPM) e 300 (E2SM-RC v3.01, incluindo cota de PRB por fatia).
- Não houve RIC Subscription, Indication KPM nem Control RC: nenhuma xApp assinou o nó. Esses são os passos dos gates G1 e G3.
- Certificador: G0 `CERTIFIED` para a pilha NORI (commits conferem com `profile.nori`); a execução é `INCOMPLETE_EVIDENCE` porque o exemplo do NORI não grava o FlowMonitor (R9/R10, exigido pela política para `NORI_NS3`). A dissecação posterior ([04 §7.5](04_instalacao_e_operacao.md#75-dissecação-e2-do-pcap)) confirma as duas mensagens E2AP com o tshark (R14 `PASS`). R7 avisa que o SO do pod (Ubuntu 20.04, base do Dockerfile do NORI) difere da seção genérica `[infrastructure]` do lock.

### 5.2 Fase 2: subscrição e Indications KPM reais (2026-11-08)

Três execuções de `nori-rc-slicing-flowmon` (semente 1) com a xApp `kpm-probe` ativa:

| Execução | Configuração | Mensagens E2AP | Cadeia identificada | tshark | Indications PCAP ↔ xApp |
| :-- | :-- | --: | :-- | :-: | :-- |
| [`nori_kpm_flowmon_seed1`](../experiments/runs/nori_kpm_flowmon_seed1/execution_manifest.json) | 60 s; SubMgr consultado na porta errada (8080) | 2 | E2 Setup | concorda | sem subscrição |
| [`nori_kpm_flowmon_seed1_r2`](../experiments/runs/nori_kpm_flowmon_seed1_r2/execution_manifest.json) | 60 s; `E2Periodicity` padrão (10 ms) | 11 958 | Setup, Subscription, KPM_t0 | concorda nas 11 958 | 11 954 / 11 954 casadas |
| [`nori_kpm_flowmon_seed1_p1s`](../experiments/runs/nori_kpm_flowmon_seed1_p1s/execution_manifest.json) | 40 s; `E2Periodicity=1` | 84 | Setup, Subscription, KPM_t0 | concorda nas 84 | 80 / 80 casadas |

- A subscrição REST foi aceita pelo SubMgr (HTTP 201) e confirmada pelo nó (notificação com `E2EventInstanceId` ≠ 0). O E2Term encaminhou cada Indication à xApp com os mesmos bytes vistos no fio: nenhuma Indication recebida sem par no PCAP, nenhuma do PCAP perdida.
- RICrequestID atribuído pelo SubMgr: requestor 123, instância igual ao subscription id RMR (2 e 3); RAN function 200 (KPM).
- Os três FlowMonitor têm 6 fluxos com pacotes recebidos (R9/R10 `PASS`).
- Certificador: as três execuções são `ELIGIBLE`; **G1 `CERTIFIED`** com `nori_kpm_flowmon_seed1_r2` e `_p1s`. G3 continua `NOT_CERTIFIED`: nenhuma xApp enviou RIC Control (fase 3).
- Observação: no E2 Setup, o RANfunction-Item da função 4 traz o OID do E2SM-KPM v3 (`1.3.6.1.4.1.53148.1.3.2.2`), embora a descrição CCC do NORI declare `…1.6.2.4`; o dissecador classifica pelo OID do E2AP e a reporta como KPM. A cadeia usa a função da subscrição (200).

### 5.3 Fase 3: RIC Control E2SM-RC com ACK (2026-11-08)

**Achado que motivou o patch.** O NORI `8a30867` aplica o RIC Control da função 300 (E2SM-RC: cotas de PRB por fatia no escalonador `NrRLMacSchedulerOfdma`), mas nunca responde com RIC Control Acknowledge; só a função 4 (E2SM-CCC, JSON) confirma. Sem ACK, o G3 é impossível. Por decisão registrada, o chart aplica [`0001-rc-control-ack.patch`](../deploy/helm/nori-ns3/files/patches/0001-rc-control-ack.patch): a função 300 passa a enviar `RICcontrolAcknowledge` com o RICrequestID e o RANfunctionID do pedido, com o código que o próprio NORI usa na CCC, e só depois de decodificar ao menos uma cota. O patch e seu sha256 estão no `versions.lock`; o certificador (R6) recusa patches fora da lista. **A bancada que certifica G3 é, portanto, um NORI modificado.**

**Codec v3.01.** [`src/e2/v3/codec.py`](../src/e2/v3/codec.py): E2AP v03.01 em APER escrito à mão (RIC Control Request e leitura de Acknowledge/Failure, IEs na ordem do ASN.1) e E2SM-KPM v03.00 / E2SM-RC v03.01 com `asn1tools` sobre o ASN.1 do NORI (download conferido por sha256). O Control segue o que o NORI decodifica (`model/ric-control-message.cc`): Control Header Format 1 (estilo 2, ação 6) e Control Message Format 1 com o parâmetro 1 (lista de políticas) contendo, por fatia, 3 = SST, 4 = PRB máximo, 5 = PRB mínimo e 6 = PRB dedicado.

[`nori_rc_control_seed1`](../experiments/runs/nori_rc_control_seed1/execution_manifest.json) (`nori-rc-slicing-flowmon`, 40 s, `E2Periodicity=1`, NORI com o patch, xApp com cotas eMBB 70/10/5 % e URLLC 30/10/5 %):

| # | Mensagem | Direção | IDs | Evidência |
| --: | :-- | :-- | :-- | :-- |
| 2 | E2 Setup Response | RIC → nó | transação 1 | PCAP + tshark |
| 4 | Subscription Response | nó → RIC | 123/4, função 200 | PCAP + tshark |
| 8 | Indication (KPM_t0) | nó → RIC | 123/4, função 200 | PCAP + tshark; mesmo sha256 recebido pela xApp, que a usou para disparar o Control |
| 9 | RIC Control Request | RIC → nó | 1003/1, função 300 | PCAP + tshark; mesmos bytes enviados pela xApp |
| 10 | RIC Control Acknowledge | nó → RIC | 1003/1, função 300 | PCAP + tshark; recebido pela xApp 1,9 ms após o envio, correlacionado |
| 11 | Indication (KPM_t1) | nó → RIC | 123/4, função 200 | PCAP + tshark |

- 86 mensagens E2AP; o tshark concorda com o dissecador nas 86; as 80 Indications do PCAP chegaram à xApp com os mesmos bytes.
- Certificador: execução `ELIGIBLE` (R6 aceita o patch do lock); **G3 `CERTIFIED`**. **G4 `NOT_CERTIFIED`**: a cadeia está completa no fio, mas o Control registrado pela xApp tem `decision_source=FIXED_PROBE`; G4 exige uma decisão do RDL-N1 disparada pelo KPM_t0.
- O tshark 4.2 só conhece o OID E2SM-RC `…53148.1.1.2.3`; o NORI anuncia o RC v3 como `…1.3.2.3`, e o tshark cai no dissector KPM (aviso "Dissector version mismatch"). A confirmação independente cobre o E2AP do Control e do ACK; o conteúdo E2SM-RC é conferido pelo codec (ida e volta, testes) e pelo decodificador asn1c do NORI (o ACK só sai depois de decodificar cotas).
- Efeito: a vazão por fatia não mudou depois do Control (~102,7 Mbps nas duas). Cada UE pede 100 Mb/s e a célula de 100 MHz não satura, então um teto de 30 % de PRB ainda atende o URLLC. Demonstrar efeito causal (fase 4) exige cotas que restrinjam a carga ou carga maior.
- O perfil `optimized` compila sem `NS_LOG`: os logs de aplicação de cota e de envio do ACK não aparecem no `stdout.log`; a evidência é o PCAP.

### 5.4 Fase 4: decisão do RDL-N1 sobre o KPM_t0 e efeito na RAN (desenhos v1–v5, 2026-11-08)

**Desenho (fixado antes da execução).**

- **Decisão:** [`src/closed_loop/hrdl_slice_loop.py`](../src/closed_loop/hrdl_slice_loop.py). O KPM_t0 decodificado ([`src/e2/v3/codec.py`](../src/e2/v3/codec.py)) vira estado: congestionamento quando `RRU.PrbUsedDl ≥ 95 %` de `RRU.PrbAvailDl` no nó, e a fatia de cada UE por `DRB.NetworkSlicing.SST`. Sob congestionamento, com as duas fatias presentes, duas políticas de referência propõem `PRB_QUOTA` (teto % da eMBB; a URLLC recebe o complemento): `xapp-qos-xslice` (prioridade 90) propõe 40, `xapp-embb-throughput` (prioridade 60) propõe 80. O conflito vai ao pipeline real da xApp RDL (`RDLxApp._process_action_group`: Safety Guard, Perception, Reasoning TVS/EEVS, Refinement), o mesmo do B3 na campanha.
- **Entrega:** a xApp `kpm-probe` recebe o `src/` do commit `b48473d` ([`scripts/deploy_kpm_probe.sh`](../scripts/deploy_kpm_probe.sh)), decide dentro do pod e envia o Control com as cotas vencedoras.
- **Efeito:** [`scripts/certification/slice_effect.py`](../scripts/certification/slice_effect.py). O KPM do NORI não mede vazão por UE, então o efeito é medido na série do FlowMonitor por fatia (`raw/slice_series.csv`, gravada pela variante a cada 0,5 s com tempo simulado e relógio de parede). O instante do Control no PCAP é convertido em tempo simulado; as cotas vêm dos bytes do Control no PCAP. Janelas de 4 s antes e 4 s depois de 2 s de acomodação. Uma fatia com teto abaixo da sua parte da vazão (margem de 5 p.p.) deve perder ao menos 5 %; as demais não podem perder mais que 5 %. O certificador só aceita G4 com veredito `CONSISTENT` e hashes de origem conferidos.

[`nori_hrdl_loop_seed1`](../experiments/runs/nori_hrdl_loop_seed1/execution_manifest.json) (`nori-rc-slicing-flowmon`, 30 s, `E2Periodicity=1`, 300 Mb/s por UE, Control depois da 12.ª Indication):

| Elo | Evidência |
| :-- | :-- |
| KPM_t0 (#18) | PRB usados 236 / disponíveis 139 (congestionada); UE 1 em SST 1, UE 2 em SST 2 |
| Decisão RDL-N1 | conflito DIRECT entre as duas propostas; TVS escolheu `xapp-qos-xslice` (confiança 0,92) em 1,3 ms; cotas eMBB 40 % / URLLC 60 % |
| RIC Control (#19) | RICrequestID 1003/1, função 300; bytes iguais ao registro da xApp; disparado pelo KPM_t0 |
| ACK (#20) | correlacionado, recebido pela xApp em 14,8 ms (inclui a decisão) |
| KPM_t1 (#21) | presente |
| Efeito (t_sim do Control = 7,12 s) | eMBB 151,49 → 151,49 Mb/s (esperado: queda ≥ 5 %, **não cumprido**); URLLC 151,49 → 151,49 Mb/s (sem queda, cumprido) |

- 64 mensagens E2AP; o tshark concorda nas 64. A xApp recebeu 56 das 58 Indications: as duas primeiras saíram no mesmo milissegundo da resposta da subscrição, antes de a rota até a xApp existir no E2Term.
- Certificador: execução `ELIGIBLE`; G1 e G3 `CERTIFIED`; **G4 `NOT_CERTIFIED`**, efeito `INCONSISTENT`.
- **Por que o efeito não apareceu.** A vazão de cada UE para em 151,49 Mb/s em qualquer carga acima disso; a perda de 50 % vem desse teto por UE, não da disputa por PRB. A execução exploratória [`nori_rc_effect_load300_seed1`](../experiments/runs/nori_rc_effect_load300_seed1/execution_manifest.json) (cotas fixas 80/20, mesma carga) dá a escala: com teto de 20 %, a URLLC caiu para ~76,5 Mb/s, cerca de 3,8 Mb/s por ponto percentual de PRB; logo, os 151,5 Mb/s de cada UE correspondem a ~40 % dos PRBs. O teto de 40 % da eMBB ficou em cima do que ela já usava e não restringiu nada. O erro está na expectativa pré-registrada, que tomou a parte da vazão (50/50) como parte dos PRBs. As políticas e a regra não foram reajustadas depois de ver o resultado.
- **Desenho v2** ([pré-registro](preregistros/01_fase4_v2.md), commit `3962e97`): a calibração [`nori_cal30_seed101`](../experiments/runs/nori_cal30_seed101/execution_manifest.json) (teto de 30 % nas duas fatias) saiu inválida, porque nenhuma fatia perdeu vazão. Por isso as avaliações v2 não foram rodadas, como o pré-registro determina. Os dados sugeriam que o teto só limitaria com cotas somando 100 %.
- **Desenho v3** ([pré-registro](preregistros/02_fase4_v3.md), commit `7ded3b2`): calibrações com cotas complementares, [`nori_cal3070_seed201`](../experiments/runs/nori_cal3070_seed201/execution_manifest.json) e [`nori_cal7030_seed202`](../experiments/runs/nori_cal7030_seed202/execution_manifest.json). Um teto de 30 % não restringiu nenhuma das fatias, mesmo com soma 100 %. A hipótese da soma foi refutada, a calibração saiu inválida e as avaliações não foram rodadas. O único efeito observado continua sendo a URLLC a 20 %; a relação teto → vazão é não linear (ver o pré-registro v3, seção 7).
- **Desenho v4** ([pré-registro](preregistros/03_fase4_v4.md), commit `d9e046c`): a curva com a janela pré-registrada saiu inválida, e as avaliações não foram rodadas. A análise exploratória da série inteira mostrou que **a cota funciona e é linear** (~3,8 Mb/s por ponto percentual de PRB: 10 % → 37,5; 15 % → 56,2; 20 % → 76,5; 30 % → 114,0 Mb/s). O efeito começa quando o tempo simulado alcança o relógio de parede do instante do Control (~12 s simulados depois), porque o NORI agenda o Control a partir da thread do E2 no simulador em tempo real. Os nulos da v1 a v3 vieram da janela de análise.
- **Desenho v5** ([pré-registro](preregistros/04_fase4_v5.md), commit `6bb7773`): janela ancorada no instante de aplicação do Control. Nas três avaliações (`nori_hrdl_v5_seed1..3`, 40 s), o RDL-N1 decidiu 80/20 sobre o KPM_t0; a URLLC caiu de 151,49 para 76,44–76,45 Mb/s (previsão 75,49, erro de 1,3 %) e a eMBB não mudou. As três foram `CONSISTENT`, e o **G4 foi certificado**. Ressalvas na seção 7 do pré-registro.
- Limitações do sensor KPM do NORI usadas na decisão: `RRU.PrbUsedDl` do nó passa dos PRBs disponíveis mesmo sem saturação (225 de 139 a 100 Mb/s), então o sinal de congestionamento é sempre verdadeiro nesse cenário; `RRU.PrbUsedDl` por UE é calculado por símbolos OFDM (119 para cada UE, antes e depois do Control); `DRB.UEThpDl` sai sempre 0; nomes de métrica com `_` fora do alfabeto de `PrintableString` (lidos com um tipo equivalente em APER).

### 5.5 Campanha NORI S0–S8 × 1001–1005 (2026-11-09)

A campanha rodou as 45 execuções, todas concluídas. O resumo por execução está em [`reports/nori/resumo_campanha_nori_20261109T015402Z.md`](../reports/nori/resumo_campanha_nori_20261109T015402Z.md) e o certificado em `reports/certification/certificate_20261109T015457Z.md`.

| Cenário | Execuções | Cadeia completa | Efeito `CONSISTENT` | Observação |
| :-: | --: | --: | --: | :-- |
| S0, S1, S2, S6, S8 | 5 cada | 5 | 4 | semente 1005: ver achado 42 |
| S3, S4, S5 | 5 cada | 0 | 0 | sem nada atuável, portanto sem Control (`NOT_TESTABLE`) |
| S7 | 5 | 5 | 0 | regra de previsão no teto de 30 %: ver achado 41 |

Em todas as 45 execuções o tshark concordou com o dissecador. Em todas as 30 com Control:

- a decisão foi do RDL-N1 e teve o KPM_t0 entre as entradas;
- o ACK foi correlacionado;
- a eMBB não perdeu vazão.

Certificador: G0, G1 (60 execuções), G3 (43) e G4 (23 cadeias: 3 da v5 e 20 desta campanha) `CERTIFIED`. G5 continua `NOT_CERTIFIED`, porque o mínimo é 30 sementes pareadas e a campanha tem 5.

Vazão da URLLC antes e depois do Control (a mesma em todas as sementes de cada linha):

| Teto URLLC | Sementes 1001–1004 (antes → depois, Mb/s) | Previsão v5 | Semente 1005 (antes → depois, Mb/s) | Depois/antes |
| --: | :-- | --: | :-- | --: |
| 15 % (S6) | 151,49 → 56,25 | 56,95 | 75,74 → 28,10 | 0,371 |
| 20 % (S0, S2, S8) | 151,49 → 76,44 | 75,50 | 75,74 → 38,14 | 0,505 |
| 25 % (S1) | 151,49 → 95,24 | 95,22 | 75,74 → 47,52 | 0,628 |
| 30 % (S7) | 151,49 → 113,98 | 91,45 | 75,74 → 56,87 | 0,752 |

Três achados, registrados como exploratórios em docs/07:

- **Achado 41.** No S7, a regra v5 erra a previsão para o teto de 30 %. Ela deixa de fora o próprio nível e interpola entre 20 % e 70 %, mas 70 % já não restringe a vazão, que satura por volta de 40 % dos PRBs. A previsão sai 91,45 Mb/s; o medido, 113,98 Mb/s, é igual ao ponto de 30 % da curva.
- **Achado 42.** Com a semente 1005, cada UE chega no máximo a 75,74 Mb/s, metade das outras sementes, desde o início da execução. A curva v5 está em Mb/s absolutos e foi calibrada a 151,49 Mb/s. Por isso só funciona quando a vazão de base coincide com a da calibração: quatro execuções saíram `NOT_TESTABLE` e o S6 saiu `INCONSISTENT`. A razão depois/antes, porém, é a mesma nas duas vazões de base, para cada teto. Isso indica que o efeito da cota é relativo à vazão sem restrição.
- **Achado 43.** Em 6 das 45 execuções, a xApp não recebeu o primeiro par de Indications (78/80): o nó o enviou cerca de 2 ms depois do Subscription Response, antes de a rota RMR da subscrição chegar. A decisão, na 12.ª Indication, não é afetada.

Os vereditos acima são os da regra pré-registrada v5, sem ajuste depois de ver os dados. Uma regra relativa (razão depois/antes por teto) e uma interpolação só entre níveis que restringem exigem um novo desenho pré-registrado antes de serem aplicadas. Esse desenho é o [pré-registro v6](preregistros/05_fase4_v6.md), com avaliação em sementes novas (2001–2005): `bash scripts/run_nori_campaign.sh --scenarios "S0 S1 S2 S6 S7 S8" --seeds "2001 2002 2003 2004 2005"`. A coleta grava o veredito v6 em `slice_effect_v6.json`, e o resumo da campanha mostra as duas colunas.

### 5.6 Avaliação do desenho v6 (sementes 2001–2005, 2026-11-09)

As 30 avaliações pré-registradas em [docs/preregistros, v6](preregistros/05_fase4_v6.md) saíram `CONSISTENT` pela regra v6 (previsão relativa à vazão antes do Control), com erro de no máximo 0,03 %. Pela regra v5, 25 saíram `CONSISTENT` e os cinco S7 saíram `INCONSISTENT`.

| Hipótese | Resultado |
| :-- | :-- |
| H6.1 (cadeia E2 completa, decisão do RDL-N1 sobre o KPM_t0, ACK, tshark) | cumprida nas 30 |
| H6.2 (≥ 27 de 30 `CONSISTENT` pela v6) | cumprida: 30 de 30 |
| H6.3 (os cinco S7, teto de 30 %, `CONSISTENT`) | cumprida |
| H6.4 (invariância à vazão de base) | não testada: as cinco sementes deram 151,49 Mb/s |

Resumo em [`reports/nori/resumo_campanha_nori_20261109T043933Z.md`](../reports/nori/resumo_campanha_nori_20261109T043933Z.md). Certificado `certificate_20261109T043932Z`: G0, G1 (90), G3 (73) e G4 (48 cadeias, regra v5) `CERTIFIED`; G5 `NOT_CERTIFIED`. Com a v6 adotada no certificador, sem efeito retroativo, o G4 passou a 53 cadeias (`certificate_20261109T045007Z`).

### 5.7 Avaliação do desenho v7: banda de 50 MHz (sementes 4001–4005, 2026-11-09)

O [pré-registro v7](preregistros/06_fase4_v7.md) testou a H6.4 reduzindo a banda para 50 MHz (URLLC com vazão de base de 40 Mb/s). As 30 avaliações saíram `INCONSISTENT` pela regra v6, todas com cadeia E2 completa: **H6.4 refutada para mudança de banda.** Pela análise exploratória, o teto age em PRBs absolutos da portadora. Por exemplo, URLLC a 20 % de 50 MHz → 37,46 Mb/s, igual a 10 % de 100 MHz. A regra v6 continua válida na banda da calibração (100 MHz), onde foi confirmada.

### 5.8 Campanha do G5: S8 × B0–B3 × 30 sementes (2026-11-09)

O [pré-registro da campanha do G5](preregistros/07_campanha_g5_s8.md) rodou o S8 com os quatro baselines e E2 real nas sementes 5001–5033. Três pares foram perdidos e repostos, declarados antes das execuções de reposição: um pela corrida no disparo da decisão do B0 (5012), dois pela perda de registro do E2Term no RIC (5028 e 5029). **G5 `CERTIFIED`, com 30 pares.** Todas as execuções válidas saíram `CONSISTENT` pela regra v6, com as cotas previstas: B0 com dois Controls e 25/75 final, B1 80/20, B2 25/75, B3 80/20. Na vazão total, o RDL-N1 e o FIFO dão 227,93 Mb/s, e o B0 e o B2 dão 246,73 Mb/s, sem hipótese de superioridade pré-registrada. Resumo em [`reports/nori/resumo_campanha_nori_20261109T130646Z.md`](../reports/nori/resumo_campanha_nori_20261109T130646Z.md); certificado `certificate_20261109T130613Z`: G0, G1 (249), G3 (230), G4 (84) e G5 `CERTIFIED`, G6 `NOT_CERTIFIED`.

## 6. Achados sobre a RDL-N1

1. **Veto por associação (corrigido).** No S7, uma proposta insegura no mesmo conflito indireto que uma legítima fazia a validação rejeitar a resolução inteira, bloqueando também a ação legítima. Correção: Safety Guard por proposta antes da arbitragem.
2. **Conflitos entre células não eram detectados (corrigido em 2026-11-10, achado 52 de `docs/07`).** No S4 (handover para uma célula que o Energy Saving desliga) e no S5 (ping-pong entre duas células), as ações estão em nós diferentes e a percepção não as relacionava. As regras `HANDOVER_INTO_REDUCED_CELL`, `HANDOVER_PING_PONG` e `NEIGHBOR_SLEEP` (`src/core/inter_cell.py`) passaram a detectá-las e foram avaliadas no pré-registro 08 (§4.4). Os números da campanha C1 acima, de 2026-11-08, são anteriores à correção.
3. **Efeitos de rede que não vêm da arbitragem.** No S7, a melhora de atraso após uma restrição de PRB vem da redução de interferência entre células. Antes de atribuir um efeito à decisão, compare com um controle (execução sem cronograma ou com a ação isolada).

## 7. Ameaças à validade

- Malha aberta: a decisão não reage ao estado da RAN durante o experimento.
- As propostas do catálogo são estilizadas (valores e períodos fixos), não produzidas por xApps reais reagindo à rede.
- Cinco sementes por célula do desenho; para o gate G5 a política exige 30 sementes e E2 real.
- **Pseudorreplicação (achado 70 de `docs/07`).** Em vários cenários a semente não muda topologia nem tráfego: S4 (achado 54), S12 (o mesmo resultado nas cinco sementes da campanha 10), S8 na bancada (desvio-padrão entre sementes abaixo de 0,01 Mb/s no G5) e as contagens de S11 e S15. Nesses casos, "5/5" e "30 pares" contam repetições idênticas de um mesmo caso, não réplicas independentes. O critério "≥ 4 de 5" é heurístico: num teste de sinais com p = 0,5, 4 ou 5 acertos em 5 ocorrem ao acaso com probabilidade 6/32. Os próximos pré-registros devem definir a unidade de replicação e usar posições e tráfego dependentes da semente.
- **Hipóteses verdadeiras por construção.** Em malha aberta, uma hipótese sobre contagem de ações aplicadas (por exemplo, H11.3 e H11.4) decorre do cronograma fixo e das regras da RDL-N1: é verificação funcional, não medida de efeito na RAN.
- **Baselines pouco discriminativos.** B1 e B2 deram resultados idênticos em todos os cenários da campanha 10, e no S12 e no G1 B1 = B2 = B3 nas métricas de rádio. Um ganho "sobre a RDL-N1" nesses cenários também é ganho sobre FIFO e prioridade estática.
- **Viés de desenho.** O mesmo autor escreve o catálogo de cenários, as hipóteses, os baselines e a xApp; a reprodução independente (G6) não foi feita.
- Os pesos de TVS/EEVS são fixos e não foram calibrados por experimento.
- `SCHEDULER_WEIGHT` não tem atuação na RAN simulada.
- SRS desativado nos cenários com handover altera a estimação de canal de uplink (o tráfego avaliado é downlink).
