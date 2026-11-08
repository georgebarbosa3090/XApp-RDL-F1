# 03 — Taxonomia de conflitos e cenários

## 1. Tipos de conflito

| Tipo | Definição | Exemplo | Tratamento na H-RDL |
| :-- | :-- | :-- | :-- |
| Direto | Duas xApps pedem valores diferentes para o mesmo parâmetro do mesmo nó | xSlice pede 75 % de PRB, Energy Saving pede 30 % | detectado; TVS escolhe um vencedor |
| Indireto | Parâmetros diferentes do mesmo nó que afetam os mesmos KPIs | redução de potência junto com reserva de PRB | detectado pelo grafo de KPIs; EEVS escolhe o subconjunto |
| Temporal | Alternância de valores no mesmo alvo ao longo do tempo | ping-pong de handover | parcialmente: histerese de 1 s por alvo; **não detectado quando as ações estão em células diferentes** |
| Entre células | Ações em nós diferentes que interferem entre si | handover para uma célula que outra xApp desliga | **não detectado** (conflitos são agrupados por nó) |
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
- No S4 e no S5 os conflitos ocorrem entre células e não são detectados pela H-RDL.

### 2.2 Cenário S8 — closed loop na bancada NORI, e o porte de S0–S7

O S8 antigo (`scenario_rdl_closed_loop_nori.cc`) não alterava a RAN e só imprimia um handshake E2 fixo (achados 14 e 15 de docs/05). Ele foi removido. No catálogo, o S8 passou a ser o closed loop da bancada NORI (`"ns3": null`, `"backend": "NORI_NS3"`, `"nori_scenario": "nori-rc-slicing-flowmon"`): xslice pede cota de PRB 25 % (prioridade 90) e embb_throughput pede 80 % (prioridade 60) no mesmo alvo. O H-RDL decide sobre o KPM real do nó e a xApp envia o RIC Control E2SM-RC.

Os cenários S0–S7 também foram portados para a bancada NORI (`src/closed_loop/catalog_loop.py`, xApp kpm-probe em modo `catalog`). Em cada execução, o H-RDL arbitra uma vez as propostas do cenário e só a cota de PRB no gNB 0 é atuada; potência, handover e propostas para outros gNBs são decididas e registradas como não atuáveis. A tabela de decisões por cenário, os comandos e os limites estão em [docs/11](11_observabilidade_e_campanhas.md).

### 2.3 Cenários de pesquisa futura (S9–S15)

| ID | Tema | Arquivo |
| :-: | :-- | :-- |
| S9 | Handover orbital em NTN (LEO) | `scenario_rdl_s9_ntn_orbital_handover.cc` |
| S10 | Enxame de UAVs e bateria | `scenario_rdl_s10_uav_swarm_battery.cc` |
| S11 | Pelotão V2X em rodovia | `scenario_rdl_s11_v2x_highway_platooning.cc` |
| S12 | IIoT com jitter determinístico | `scenario_rdl_s12_iiot_zero_jitter_slicing.cc` |
| S13 | SAGIN em resgate | `scenario_rdl_s13_sagin_disaster_rescue.cc` |
| S14 | ISAC radar + comunicação | `scenario_rdl_s14_isac_radar_comm.cc` |
| S15 | xApp maliciosa em enlace NTN | `scenario_rdl_s15_rogue_ntn_feeder_hijacking.cc` |

Estes arquivos existem, mas **não usam a camada de atuação** nem estão no catálogo de conflitos; não foram executados com proveniência. Há também três cenários exploratórios (`scenario_rdl_5ga_multicarrier_mimo`, `scenario_rdl_6g_cross_tier_governance`, `scenario_rdl_6g_isac_sensing_coexistence`) na mesma situação.

## 3. xApps que geram as propostas

As propostas do catálogo representam os papéis das xApps de [`reference-xapps/`](../reference-xapps/README.md): xSlice (QoS/fatias), Energy Saving, Traffic Steering, Load Balancer, Beamformer, ISAC Radar e uma xApp maliciosa de teste. Nos experimentos de simulação as propostas vêm do catálogo, não dos processos das xApps; isso torna a carga de conflito idêntica entre baselines e sementes.
