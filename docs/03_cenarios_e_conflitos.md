# 03 — Cenários e conflitos

## 1. Tipos de conflito

| Tipo | Definição | Exemplo | Tratamento na H-RDL |
| :-- | :-- | :-- | :-- |
| Direto | Duas xApps pedem valores diferentes para o mesmo parâmetro do mesmo nó | xSlice pede 75 % de PRB, Energy Saving pede 30 % | detectado; TVS escolhe um vencedor |
| Indireto | Parâmetros diferentes do mesmo nó que afetam os mesmos KPIs | redução de potência junto com reserva de PRB | detectado pelo grafo de KPIs; EEVS escolhe o subconjunto |
| Temporal | Alternância de valores no mesmo alvo ao longo do tempo | ping-pong de handover | histerese de 1 s por alvo; entre células, ping-pong de handover detectado (`HANDOVER_PING_PONG`, desde 2026-11-10) |
| Entre células | Ações em nós diferentes que interferem entre si | handover para uma célula que outra xApp desliga | detectado desde 2026-11-10 (`INTER_CELL`: handover × célula desligada/reduzida, ping-pong, vizinhas dormindo); EEVS escolhe o subconjunto compatível ([02 §4.1](02_modelo_de_decisao_h_rdl.md#41-percepção-conflitos-agrupados-por-alvo)) |
| Ação insegura | Valor fora dos limites físicos ou inválido | 60 dBm, PRB 150 % | descartada pelo Safety Guard antes da arbitragem |
| Tempestade | Muitas propostas concorrentes na mesma janela | várias xApps em vários nós | eventos agrupados por alvo (custo limitado por O(P²) por nó) |

## 2. Cenários

Os cenários estão em [`simulations/ns3/`](../simulations/ns3/README.md). Todos usam 5G-LENA na banda de 3,5 GHz e tráfego UDP downlink de um host remoto para os UEs.

### 2.1 Cenários de conflito com atuação na RAN (S0–S7)

Desde 2026-11-08 estes cenários aplicam, durante a simulação, as ações decididas pelo baseline (cota de PRB, potência do gNB e handover X2) por meio de [`rdl-nr-common.h`](../simulations/ns3/rdl-nr-common.h). As propostas das xApps de cada cenário estão em [`conflicts/catalog.json`](../simulations/ns3/conflicts/catalog.json).

| ID | Arquivo | Topologia | Carga | Propostas das xApps (janela de conflito) |
| :-: | :-- | :-- | :-- | :-- |
| S0 | `scenario_rdl_no_conflict` | 2 gNBs a 250 m, 30 UEs | 256 B / 20 ms por UE | xSlice PRB 80 % na gNB0; Energy Saving 30 dBm na gNB1 — sem conflito (controle) |
| S1 | `scenario_rdl_direct_prb_conflict` | 1 gNB, 20 UEs | 1024 B / 200 µs por UE (saturada) | xSlice PRB 75 % (prio 90) × Energy Saving PRB 30 % (prio 65), reafirmadas a cada 1 s (10–15 s) |
| S2 | `scenario_rdl_tvs_conflict` | 2 gNBs a 80 m (grade), 30 UEs em fatias URLLC/eMBB/mMTC | URLLC 128 B / 1 ms; eMBB 1400 B / 200 µs; mMTC 64 B / 100 ms | xSlice PRB 80 % na macro (prio 90) × Traffic Steering handover macro → small cell (prio 80) |
| S3 | `scenario_rdl_energy_vs_qos` | 2 gNBs a 50 m (grade), 20 UEs, 50 MHz | duas classes de tráfego | xSlice 40 dBm (prio 90) × Energy Saving 10 dBm (prio 65) na mesma célula |
| S4 | `scenario_rdl_ts_vs_energy` | macro + small cell a 200 m, 40 UEs | 30 UEs pesados (1024 B / 8 ms), 10 leves | Traffic Steering handover gNB0 → gNB1 (prio 80) × Energy Saving 0 dBm na gNB1 (prio 65) — conflito entre células |
| S5 | `scenario_rdl_temporal_pingpong` | 2 gNBs a 150 m, 24 UEs no meio | 512 B / 10 ms | Traffic Steering gNB0 → gNB1 e Load Balancer gNB1 → gNB0, alternados a cada 2 s (18–26 s) |
| S6 | `scenario_rdl_conflict_storm` | 4 gNBs em quadrado de 200 m, 30 UEs (`--loadLevel=0`) | 512 B / 5 ms | seis xApps disputam PRB e potência nas quatro gNBs a cada 0,5 s |
| S7 | `scenario_rdl_fault_injection` | 2 gNBs a 200 m, 20 UEs | 512 B / 15 ms | xApp maliciosa pede 60 dBm e PRB 150 % (prio 100) contra xSlice PRB 70 % |

Observações dos experimentos:

- S2, S4 e S5 rodam com `--disableSrs=true`: o 5G-LENA v5.1 aborta em handover em massa por SRS sobrepostos no gNB de destino.
- A rede de base do S7 é limitada por interferência entre as duas células (atraso de 75–150 ms antes do conflito); restringir PRB numa célula reduz o atraso das duas.
- No S4 e no S5 os conflitos ocorrem entre células. Até 2026-11-10 a H-RDL não os detectava, e as campanhas registradas até essa data (nativa de 2026-11-08 e NORI de 2026-11-09) refletem isso. Desde então o B3 detecta os dois: no S4 a redução de potência da gNB1 perde para o handover (`HANDOVER_INTO_REDUCED_CELL`, prioridade 80 > 65); no S5 o handover de volta do Load Balancer perde para o do Traffic Steering (`HANDOVER_PING_PONG`, 80 > 70). Execuções novas desses cenários não são comparáveis às anteriores sem declarar a mudança.

### 2.2 Cenário S8 e o porte para a bancada NORI

O S8 é o closed loop da bancada NORI: xslice pede cota de PRB 25 % (prioridade 90) e embb_throughput pede 80 % (prioridade 60) no mesmo alvo. Os cenários S0–S7 também rodam na bancada NORI, com E2 real. O que cada um atua lá está na [seção 4](#4-cenários-na-bancada-nori-porte-de-s0s8-com-e2-real).

### 2.3 Cenários S9–S15 (removidos)

Os esboços S9–S15 (NTN, UAV, V2X, IIoT, SAGIN, ISAC, NTN malicioso) e três cenários exploratórios (5G-Advanced e 6G) não usavam a camada de atuação, não estavam no catálogo e nunca rodaram com proveniência. Foram removidos do repositório em 2026-11-09 (achado 45 de docs/07). Esses temas pertencem à Fase 2 (`XApp-RDL-F2`).

## 3. xApps que geram as propostas

As propostas do catálogo representam os papéis das xApps de [`reference-xapps/`](../reference-xapps/README.md): xSlice (QoS/fatias), Energy Saving, Traffic Steering, Load Balancer, Beamformer, ISAC Radar e uma xApp maliciosa de teste. Nos experimentos de simulação as propostas vêm do catálogo, não dos processos das xApps; isso torna a carga de conflito idêntica entre baselines e sementes.

## 4. Cenários na bancada NORI (porte de S0–S8 com E2 real)

| Pilha | Cenários | E2 | Gates que o certificador pode avaliar |
| :-- | :-- | :-- | :-- |
| Nativa (ns-3.48 + 5G-LENA v5.1) | S0–S7 (`simulations/ns3/scenario_s*.cc`) | não | G0 |
| NORI (ns-3.42 + 5G-LENA + E2 real) | S0–S8 (variante `nori-rc-slicing-flowmon`) | sim | G0–G4 |

A pilha nativa aplica um cronograma de ações dentro do ns-3, sem E2. Por isso a cadeia KPM_t0 → H-RDL → E2SM-RC → ACK → KPM_t1 só pode ser certificada na bancada NORI, o único lugar onde o nó E2 fala com o RIC.

Na bancada NORI, cada cenário do catálogo (`simulations/ns3/conflicts/catalog.json`) roda assim:

1. O cenário é escrito em `/data/rdl_scenario`, no volume da xApp kpm-probe.
2. A xApp, em modo `catalog`, assina o KPM do nó.
3. Na 12.ª Indication, o H-RDL real (`src/closed_loop/catalog_loop.py`) arbitra as propostas das xApps do cenário. O estado de entrada é o KPM decodificado: PRBs do nó, UEs e fatias.
4. Se houver o que atuar, a xApp envia o RIC Control E2SM-RC (função 300). O ACK e o efeito na vazão por fatia são medidos.

O que o NORI consegue atuar:

| Proposta do catálogo | Atuação no NORI |
| :-- | :-- |
| `PRB_QUOTA` no gNB 0 | RIC Control de cota de PRB por fatia: eMBB (SST 1) recebe o teto `v`, URLLC (SST 2) recebe `100 − v` |
| `TX_POWER`, `HANDOVER` | Decidida e registrada como **não atuável**: potência de transmissão não existe no E2SM-RC do NORI, e o handover ele só registra em log (há um único gNB) |
| Qualquer proposta nos gNBs 1–3 | Não atuável: o NORI tem um único gNB |

As propostas não atuáveis aparecem na decisão (`not_actuated`, com o motivo). Nenhum Control é enviado por elas.

Cada execução faz uma única decisão. Ela usa a primeira ocorrência de cada proposta (xApp, gNB, parâmetro) e mantém o gNB de origem no alvo (`<meid>#g<gnb>`). Assim, propostas para gNBs diferentes não viram conflito falso.

| Cenário | Decisão do H-RDL (verificada em `tests/unit/test_catalog_loop.py`) | Control no NORI |
| :-- | :-- | :-- |
| S0 | xslice `PRB_QUOTA` 80; `TX_POWER` no gNB 1 não atuável | 80/20 |
| S1 | conflito direto → TVS escolhe xslice 75 | 75/25 |
| S2 | conflito indireto → EEVS escolhe xslice 80; `HANDOVER` não selecionado | 80/20 |
| S3 | TVS escolhe `TX_POWER` (não atuável) | nenhum |
| S4 | conflito entre células desde 2026-11-10: `TX_POWER` no gNB 1 não é selecionado; `HANDOVER` no gNB 0 vence (só registrado em log pelo NORI) | nenhum |
| S5 | ping-pong entre células desde 2026-11-10: o `HANDOVER` do gNB 1 não é selecionado; o do gNB 0 vence (não atuável) | nenhum |
| S6 | xslice 85 | 85/15 |
| S7 | Safety Guard bloqueia `rogue_xapp` (`TX_POWER` 60 e `PRB_QUOTA` 150); xslice 70 | 70/30 |
| S8 | conflito direto xslice 25 × embb_throughput 80 → H-RDL escolhe embb_throughput 80 | 80/20 |

### 4.1 S8: o closed loop do NORI

O S8 antigo (`scenario_rdl_closed_loop_nori.cc`) não alterava a RAN e só imprimia um handshake E2 fixo (achados 14 e 15 da auditoria). Ele foi removido.

No catálogo, o S8 passou a ser o cenário de closed loop da bancada NORI:

- `"ns3": null`;
- `"backend": "NORI_NS3"`;
- `"nori_scenario": "nori-rc-slicing-flowmon"`.

Com isso, o S8 só roda pelo `scripts/run_nori_scenario.sh`. A campanha nativa recusa o S8 com a mensagem "cenário(s) só da bancada NORI".

### 4.2 Critério "disparado pelo KPM_t0"

O NORI envia o KPM de cada período em par: formato 1 (nó) e formato 3 (UEs), com menos de 1 ms entre os dois. O E2Term pode entregar esse par à xApp em ordem trocada.

A decisão usa as duas mensagens do par. Os sha256 de ambas ficam registrados em `decision.kpm_node_sha256` e `decision.kpm_ues_sha256`. Por isso, o dissector considera o Control disparado pelo KPM_t0 (o último KPM antes do Control, no PCAP) quando esse KPM é uma das entradas da decisão.

Na execução `nori_S1_B3_seed1001`, o gatilho registrado era a mensagem de formato 1 do par. No fio, porém, a última mensagem antes do Control era a de formato 3, que também entrou na decisão.

A xApp também só decide quando a Indication recebida completa o par do período (nó e UEs chegados a no máximo 0,5 s um do outro), em qualquer ordem de entrega, para que uma decisão rápida não use os UEs do período anterior (achado 48). Além disso, a xApp aquece o H-RDL antes do primeiro KPM (evento `decision_warm_up`). Isso evita que a importação das bibliotecas atrase o Control na hora da decisão.
