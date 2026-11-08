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
- S0, S1, S3 e S7 da semente 1001 foram executados antes dessas mudanças; elas não afetam cenários sem handover, mas o hash da fonte do cenário difere entre essas execuções e as posteriores (campo `scenario_sha256`).

## 4. Resultados

**Campanha em andamento** (S0–S7 × B0–B3 × sementes 1001–1005). O relatório mais recente gerado pela análise fica em [`reports/conflicts/`](../reports/conflicts/); esta seção será atualizada com a tabela final.

### 4.1 Resultados preliminares (semente 1001, n = 1)

Sem repetição, estes valores mostram o comportamento, não diferenças estatísticas.

| Cenário | Baseline | Vazão no conflito | Atraso no conflito | Ações inseguras aplicadas | Oscilações |
| :-- | :-- | --: | --: | --: | --: |
| S1 | B0 | 118 Mbps | 17,1 ms | 0 | 9 |
| S1 | B3 | 279 Mbps | 9,1 ms | 0 | 0 |
| S7 | B0 | 5,5 Mbps | 10,3 ms | 10 | 0 |
| S7 | B3 | 5,5 Mbps | 13,1 ms | 0 | 0 |

- **S1:** sem coordenação, a xApp de energia escreve por último e a cota fica em 30 % na maior parte do tempo; a H-RDL mantém 75 % (vence a xApp de QoS pela utilidade TVS).
- **S7:** sem coordenação, a potência de 60 dBm e a cota de 150 % chegam à RAN; com a H-RDL, nenhuma. O efeito na vazão foi pequeno neste cenário.

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
