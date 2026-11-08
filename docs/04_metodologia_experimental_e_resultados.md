# 04 — Metodologia experimental e resultados

## 1. Pergunta avaliada

Quando várias xApps propõem controles conflitantes, a decisão da H-RDL leva a um desempenho de rede melhor ou mais seguro que alternativas simples (sem coordenação, FIFO, prioridade estática)?

Esta campanha avalia a **decisão** em malha aberta: as propostas são decididas por cada baseline e as ações resultantes são aplicadas na RAN simulada. Não há E2 nem realimentação de KPM; o closed loop é objeto da pilha NORI (gates G1–G4).

## 2. Desenho

| Elemento | Escolha |
| :-- | :-- |
| Simulador | ns-3.48 (`d2add90`) + 5G-LENA v5.1 (`cedcead`), perfil otimizado |
| Cenários | S0–S7 ([taxonomia](03_taxonomia_de_conflitos_e_cenarios.md)); S0 é controle sem conflito |
| Propostas | definidas por cenário em [`catalog.json`](../simulations/ns3/conflicts/catalog.json): mesma carga de conflito para todos os baselines e sementes |
| Baselines | B0 sem coordenação; B1 FIFO por janela e alvo; B2 prioridade estática por janela e alvo; B3 H-RDL |
| Janela de decisão | 200 ms; em B1–B3 a ação decidida é aplicada no fechamento da janela; em B0, na chegada |
| Atuação | PRB pela máscara de RBGs do escalonador; potência via `NrGnbPhy::SetTxPower`; handover X2 escalonado em 10 ms por UE |
| Sementes | 1001–1005, pareadas (mesma semente em todos os baselines de um cenário) |
| Medição | vazão e atraso por célula a cada 100 ms nos `UdpServer` dos UEs (`rdl_kpi_timeseries.csv`); ações aplicadas (`rdl_actuation_log.csv`) |

### 2.1 Como o B3 usa a H-RDL real

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

Cada execução tem manifesto, logs, saídas brutas e hashes em `experiments/runs/nr_<S>_<B>_seed<N>/` (formato em [`02_guia_operacional`](02_guia_operacional_deploy_e_simulacao.md#3-executar-um-cenário-com-proveniência)). A análise ([`analyze_conflict_runs.py`](../scripts/certification/analyze_conflict_runs.py)) só usa execuções elegíveis no certificador e lista as ignoradas com o motivo.

Mudanças de método durante a campanha, todas registradas:

- 2026-11-08: os handovers passaram a ser escalonados em 10 ms por UE, e S2, S4 e S5 passaram a rodar com `--disableSrs=true`, porque o 5G-LENA v5.1 abortava em handover em massa. As execuções de S2, S4 e S5 feitas antes disso foram descartadas e refeitas; as falhas do simulador estão preservadas em `experiments/runs_failed/`.
- S0, S1, S3 e S7 (só B0 e B3) da semente 1001 foram executados antes dessas mudanças; elas não afetam cenários sem handover (a opção `--disableSrs` fica desligada e os cronogramas desses cenários não têm `HANDOVER`), mas o hash da fonte do cenário difere entre essas execuções e as posteriores (campo `scenario_sha256`). No S7 da semente 1001 isso ocorre dentro do mesmo conjunto pareado: B0/B3 com uma fonte e B1/B2 com a outra.
- 2026-11-08: `run_conflict_campaign.py` removia execuções interrompidas (sem `hashes.sha256`) mas não as recolocava na fila; corrigido, elas passam a ser refeitas na mesma rodada.

## 4. Resultados

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

Consequência: em S0, S1, S3 e S5 a campanha não distingue a H-RDL de FIFO ou prioridade estática; o que se mede ali é o efeito de coordenar versus não coordenar. A comparação específica da H-RDL só existe em S2, S4, S6 e S7.

### 4.2 Leitura

- **S1 (conflito direto de PRB):** coordenar elimina as 9 oscilações e eleva a vazão no conflito de 118 para 279 Mbps, com o atraso caindo de 17,1 para 9,1 ms. O ganho é de qualquer coordenação (B1–B3 decidem igual), não específico da H-RDL. Sem coordenação, a xApp de energia escreve por último e a cota fica em 30 % na maior parte do tempo.
- **S6 (tempestade de conflitos):** a H-RDL aplica 25 ações (contra 55 do B1/B2 e 80 do B0) e zera as oscilações (9 no B1/B2, 57 no B0). O atraso no conflito é o menor (51,3 ± 6,7 ms); o IC não se sobrepõe ao do B0 (94,4 ± 12,8 ms), mas se sobrepõe aos do B1 e do B2. A vazão não difere de forma distinguível entre os quatro.
- **S7 (injeção de falha):** só a H-RDL impede que as 10 ações inseguras (potência de 60 dBm, cota de 150 %) cheguem à RAN; B1 e B2 escolhem por janela e alvo, mas não validam valores. A vazão é igual; o atraso é menor no B0 (10,5 ms contra 13,2–13,6 ms), efeito de redução de interferência e não da arbitragem (achado 3 da seção 5).
- **S2 (handover × QoS):** a H-RDL evita o handover (0 contra 0,8 em média), mas o atraso no conflito fica maior e mais variável (26,2 ± 23,4 ms contra ~7,5 ms) e a vazão mais variável. Resultado desfavorável à H-RDL neste cenário, a investigar.
- **S4 e S5 (conflitos entre células):** a H-RDL remove uma ação no S4 sem efeito nos KPIs, e o handover ocorre igual; no S5 os quatro baselines aplicam os mesmos 8 handovers. Coerente com a limitação do achado 2 da seção 5 (a percepção não relaciona ações em células diferentes).
- **S0 (sem conflito):** sem diferença distinguível entre baselines, como esperado.

Sobreposição de IC não é um teste de hipótese pareado; com n = 5 os resultados indicam comportamento e não sustentam afirmações estatísticas fortes.

## 5. Achados sobre a H-RDL

1. **Veto por associação (corrigido).** No S7, uma proposta insegura no mesmo conflito indireto que uma legítima fazia a validação rejeitar a resolução inteira, bloqueando também a ação legítima. Correção: Safety Guard por proposta antes da arbitragem.
2. **Conflitos entre células não são detectados (limitação).** No S4 (handover para uma célula que o Energy Saving desliga) e no S5 (ping-pong entre duas células), as ações estão em nós diferentes e a percepção não as relaciona.
3. **Efeitos de rede que não vêm da arbitragem.** No S7, a melhora de atraso após uma restrição de PRB vem da redução de interferência entre células. Antes de atribuir um efeito à decisão, compare com um controle (execução sem cronograma ou com a ação isolada).

## 6. Ameaças à validade

- Malha aberta: a decisão não reage ao estado da RAN durante o experimento.
- As propostas do catálogo são estilizadas (valores e períodos fixos), não produzidas por xApps reais reagindo à rede.
- Cinco sementes por célula do desenho; para o gate G5 a política exige 30 sementes e E2 real.
- Os pesos de TVS/EEVS são fixos e não foram calibrados por experimento.
- `SCHEDULER_WEIGHT` não tem atuação na RAN simulada.
- SRS desativado nos cenários com handover altera a estimação de canal de uplink (o tráfego avaliado é downlink).
