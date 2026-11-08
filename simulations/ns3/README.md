# Mapeamento e Matriz Metodológica da Campanha de Cenários (S0 a S15)

Este diretório contém fontes e instruções para cenários de co-simulação **ns-3 + 5G-LENA + NORI/E2**, destinados à avaliação do middleware **xApp RDL (H-RDL)**. A presença de um cenário C++ ou de um teste local não comprova execução integrada nem evidência externa: os gates G1, G3, G4 e G5 permanecem sujeitos aos critérios do [README principal](../../README.md).

---

## 1. Núcleo Fase 1 (S0–S8): Validação Obrigatória H-RDL

| Identificador | Nome do Cenário | Arquivo C++ Executável | Propósito Metodológico / Métrica Principal |
| :---: | :--- | :--- | :--- |
| **S0** | Passthrough Limpo e Não-Interferência | [`scenario_rdl_no_conflict.cc`](scenario_rdl_no_conflict.cc) | Taxa de Interferência = 0%, Preservação de Ações Válidas |
| **S1** | Conflito Direto de PRB | [`scenario_rdl_direct_prb_conflict.cc`](scenario_rdl_direct_prb_conflict.cc) | Precision, Recall, F1-Score em Colisão de Bloco de Recursos |
| **S2** | Conflito Indireto TVS (Throughput x Slicing) | [`scenario_rdl_tvs_conflict.cc`](scenario_rdl_tvs_conflict.cc) | Resolução de Conflito de Domínio Cruzado (PRB vs SLA) |
| **S3** | Multi-Métrica Cross-Layer (Power x QoS) | [`scenario_rdl_energy_vs_qos.cc`](scenario_rdl_energy_vs_qos.cc) | Equilíbrio Pareto entre Economia de Energia e SLA |
| **S4** | Mobilidade (TS) x Economia de Energia (ES) | [`scenario_rdl_ts_vs_energy.cc`](scenario_rdl_ts_vs_energy.cc) | Arbitragem Assimétrica de Sono de gNB e Cobertura |
| **S5** | Histerese Temporal e Trava de Ping-Pong | [`scenario_rdl_temporal_pingpong.cc`](scenario_rdl_temporal_pingpong.cc) | Cooldown Lock e Supressão de Oscilação Temporal |
| **S6** | Conflict Storm (50 req/janela) | [`scenario_rdl_conflict_storm.cc`](scenario_rdl_conflict_storm.cc) | Meta do projeto: avaliar tempo de resolução abaixo de 50 ms |
| **S7** | Injeção de Falhas | [`scenario_rdl_fault_injection.cc`](scenario_rdl_fault_injection.cc) | Testar bloqueio de ações inseguras; não é taxa de sucesso empírica de RAN |
| **S8** | Tráfego 5G-LENA com agente E2 opcional | [`scenario_rdl_closed_loop_nori.cc`](scenario_rdl_closed_loop_nori.cc) | Coletar métricas NR/FlowMonitor; o código atual não implementa atuação E2SM-RC/RDL nem comprova closed loop |

---

## 2. Suíte Avançada 5G-A/6G (S9–S15): Roadmap e Generalização

Os cenários **S9 a S15** representam a extensão da campanha para ambientes de próxima geração (5G-Advanced / 6G). Estão documentados no roadmap formal em [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../../docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) e cobertos por contratos de validação em [`tests/unit/test_campaign_scenarios.py`](../../tests/unit/test_campaign_scenarios.py).

| Identificador | Domínio de Pesquisa | xApp Relacionada | Requisito Principal de Simulação |
| :---: | :--- | :--- | :--- |
| **S9** | Non-Terrestrial Networks (NTN) | `ntn-steering`, `satellite-ho` | Handover Orbital LEO & Compensação Doppler |
| **S10** | UAV Swarm & Cobertura Aérea | `uav-mobility`, `energy-conserver-uav` | Gestão de Bateria SoC & Mobilidade 3D em Enxame |
| **S11** | V2X Platoon Highway (110 km/h) | `v2x-mobility`, `platoon-qos` | Latência URLLC Sub-10ms & Handover de Alta Velocidade |
| **S12** | IIoT / Factory TSN | `industrial-qos` | Latência Determinística & Supressão de Jitter |
| **S13** | Emergency SAGIN | `rescue-qos` | Orquestração Multidomínio Satélite-UAV-Terrestre |
| **S14** | 6G ISAC (Radar + Comms) | `isac-radar` | Mitigação de Interferência Sensoriamento x Comunicação |
| **S15** | Segurança Cross-Tier Zero-Trust | `sec-guardian` | Controle Hieraquico Near-RT / Non-RT com Zero-Trust |

---

## 3. Diretriz Inviolável: Zero Dados Sintéticos e Proveniência Estrita do ns-3 FlowMonitor

**É expressamente proibido utilizar simuladores discretos simplificados ou geradores sintéticos estáticos para produzir dados científicos.**

Métricas de tráfego e QoS da simulação devem ser exportadas pelo módulo nativo `FlowMonitor` do ns-3 (5G-LENA v5.1). Alegações de KPM, controle RC ou closed loop também exigem traces E2/RIC externos e manifesto de proveniência; FlowMonitor isoladamente não comprova esses elos. Cenários definidos ou compiláveis, por si só, não constituem resultados experimentais.

$$
\text{Cenário C++} \longrightarrow \text{ns-3.48 + 5G-LENA v5.1} \longrightarrow \text{FlowMonitor XML/CSV} \longrightarrow \text{Relatório Markdown Oficial}
$$

---

## 4. Passo a Passo de Instalação, Compilação e Execução

### 4.1. Atualizar o Repositório no Host
```bash
git pull origin main
```

### 4.2. Pilhas de simulação

São duas pilhas distintas, porque o NORI oficial não roda em ns-3.48 / 5G-LENA v5.1:

| Pilha | Versões | Backend no manifesto | Serve para |
| :-- | :-- | :-- | :-- |
| Nativa | ns-3.48 (`d2add90`) + 5G-LENA v5.1 (`cedcead`) | `NS3_5GLENA` | Cenários de conflito S0–S7 (FlowMonitor); **sem E2** |
| NORI | ns-3.42 (`ab4cce0`) + nr `78b7179` + NORI `8a30867` | `NORI_NS3` | E2 real e closed loop (S8), via Helm |

A instalação fixada da pilha nativa está no [guia operacional](../../docs/02_guia_operacional_deploy_e_simulacao.md#5-pipeline-de-co-simulação-ns-348--5g-lena--nori); a do NORI, em [`deploy/helm/nori-ns3`](../../deploy/helm/nori-ns3/README.md). O `scripts/setup_ns3.sh` legado recai silenciosamente em outras versões e não deve ser usado para gerar evidência.

### 4.3. Executar um cenário com proveniência (saída ao vivo)
```bash
bash scripts/certification/run_ns3_certified.sh --scenario scenario_rdl_direct_prb_conflict --seed 1001 --baseline B3 -- --simTime=10
python scripts/certification/certify_chain.py --run scenario_rdl_direct_prb_conflict_B3_seed1001
```
O executor mostra a saída do simulador em tempo real e grava em `experiments/runs/<run_id>/` o manifesto (versões lidas dos checkouts, comando, horários, código de saída), `logs/`, as saídas em `raw/` e `hashes.sha256`. Ele nunca sobrescreve uma execução existente.

### 4.3.1. Experimentos de conflito com atuação real na RAN (S0–S7)

Desde 2026-11-08 os cenários S0–S7 aplicam conflitos na RAN durante a simulação, por meio de [`rdl-nr-common.h`](rdl-nr-common.h):

| Ação de controle | Atuação no 5G-LENA v5.1 |
| :-- | :-- |
| `PRB_QUOTA` (%) | máscara de RBGs do escalonador (`NrMacSchedulerNs3::SetDlNotchedRbgMask`; o escalonador padrão `NrMacSchedulerTdmaRR` respeita a máscara) |
| `TX_POWER` (dBm) | potência do gNB (`NrGnbPhy::SetTxPower`) |
| `HANDOVER` (índice do gNB de destino) | handover X2 dos UEs servidos pelo gNB de origem (`NrHelper::HandoverRequest`) |
| `SCHEDULER_WEIGHT` | sem mapeamento; registrado como `UNSUPPORTED` |

O cabeçalho também monta a rede NR funcional usada por S0 e S4–S7, cuja montagem anterior não anexava os UEs nem lhes atribuía IP (FlowMonitor vazio), e grava duas séries medidas no simulador: `rdl_actuation_log.csv` (cada ação aplicada, com instante e efeito) e `rdl_kpi_timeseries.csv` (vazão e atraso por célula a cada `--kpiPeriod`). A saída `[RDL-ACT]`/`[RDL-KPI]` aparece ao vivo no terminal.

As propostas das xApps de cada cenário estão em [`conflicts/catalog.json`](conflicts/catalog.json). O baseline decide o que chega à RAN:

| Baseline | Regra |
| :-- | :-- |
| B0 | sem coordenação: cada proposta é aplicada ao chegar |
| B1 | FIFO por janela de 200 ms e alvo |
| B2 | prioridade estática por janela e alvo |
| B3 | H-RDL: pipeline real `RDLxApp._process_action_group` por janela, no relógio simulado |

```bash
python scripts/certification/run_conflict_experiment.py --scenario S1 --baseline B3 --seed 1001
python scripts/certification/analyze_conflict_runs.py      # tabela por cenário × baseline em reports/conflicts/

# Campanha: cenários × baselines × sementes, retomável, com execuções em paralelo
python scripts/certification/run_conflict_campaign.py --seeds 1001-1005 --jobs 2
```
A campanha compila os cenários uma única vez e roda cada execução com `--no-build` (o executor só aceita esse modo se a fonte em `scratch/` for idêntica à do repositório e o binário for mais novo que ela), o que permite paralelismo sem disputa pela árvore de build. Execuções já existentes são puladas; a ordem por semente garante conjuntos pareados completos. As linhas `[RDL-ACT]`/`[RDL-KPI]` de cada execução aparecem ao vivo, prefixadas pelo `run_id`; ao final rodam a análise e o certificador.

**Handover no 5G-LENA v5.1:** transferir vários UEs para outra célula leva o simulador a abortar em `NrSpectrumPhy::StartRxSrs` ("Not allowed state for starting SRS reception"), porque o gNB de destino recebe SRS sobrepostos. Escalonar os handovers (10 ms por UE, mantido em `rdl-nr-common.h`) não basta; por isso os cenários com handover (S2, S4, S5) rodam com `--disableSrs=true`, igual para todos os baselines, conforme registrado em `conflicts/catalog.json`. O SRS serve à estimação de canal de uplink; o tráfego dos cenários é downlink.

**Falhas e interrupções na campanha:** só conta como concluída a execução com `hashes.sha256`. Execuções interrompidas são removidas e refeitas; com `--retry-failed`, execuções com `run_status` diferente de `SUCCESS` são movidas para `experiments/runs_failed/<run_id>__<UTC>` (preservadas como registro da falha) e refeitas. O manifesto registra o SHA-256 dos cabeçalhos de suporte (`support_files_sha256`).

**Espaço em disco:** o executor recusa rodar com menos de 1 GB livre (`MIN_FREE_MB`) no disco das evidências ou no temporário do simulador, e a campanha para sozinha nesse limite (basta rodá-la de novo depois). Em S2 e S3 os traces completos do 5G-LENA (`nrHelper->EnableTraces`), que geram vários GB por execução, ficam desligados salvo `--nrTraces=true`; isso não altera a simulação, só os arquivos gravados.
Cada execução fica em `experiments/runs/nr_<S>_<B>_seed<N>/` com o cronograma (`raw/action_schedule.csv`) e o log de decisões (`raw/decision_log.json`) cobertos pelos hashes. É uma avaliação **em malha aberta** (sem E2 nem realimentação de KPM); o closed loop exige a pilha NORI.

**Achados das primeiras execuções (2026-11-08):**
- S1 (seed 1001): no B0 a cota oscila 75 %→30 % e a vazão cai de 367 para 118 Mbps (atraso 17 ms); com B3 a H-RDL mantém 75 % (279 Mbps, 9,1 ms).
- S7: no B0 chegam à RAN 10 ações fora dos limites físicos (60 dBm, PRB 150 %); no B3, nenhuma. A rede do S7 é limitada por interferência entre as duas células (atraso de 75–150 ms antes do conflito); restringir PRB numa célula reduz o atraso das duas.
- A percepção da H-RDL agrupa conflitos por gNB: conflitos **entre células** (S4: handover para uma célula que o Energy Saving desliga; S5: ping-pong entre gNB0 e gNB1) não são detectados.
- Na análise do FlowMonitor, exclua os fluxos internos do EPC (GTP-C, porta 2123).

> **Semente:** os cenários chamam `SeedManager::SetSeed(--seed)` e `SetRun(--run)` depois de ler a linha de comando, o que anula `--RngRun`. O executor certificado passa a semente por `--seed` quando o cenário expõe essa opção e registra o argumento em `rng_args` no manifesto.

> **Atenção:** até 2026-11-08 `scenario_rdl_tvs_conflict.cc` e `scenario_rdl_energy_vs_qos.cc` gravavam o mesmo `flowmonitor_results.xml` (agora cada um grava `flowmonitor_<cenário>.xml`), e os FlowMonitor de S8 em `experiments/results/ns3_runs/` são byte-idênticos aos de S3. Confira o hash de cada saída antes de atribuí-la a um cenário. O `scenario_rdl_closed_loop_nori.cc` imprime mensagens E2 fixas por `std::cout` (`TraceLifecycleE2`), que não são evidência de protocolo.

### 4.4. Suíte legada (sem proveniência)
O script abaixo não grava manifesto e faz `git commit`/`git push` automáticos; seus resultados não são certificáveis.
```bash
# Executar todos os 16 cenários (S0 a S15)
bash simulations/ns3/run_all_s0_s15_simulations.sh all

# Ou executar por grupo tecnológico:
bash simulations/ns3/run_all_s0_s15_simulations.sh 5g
bash simulations/ns3/run_all_s0_s15_simulations.sh 6g

# Ou executar cenário individual (ex: S1 Direct PRB Conflict):
bash simulations/ns3/run_all_s0_s15_simulations.sh S1
```

### 4.5. Gerar Relatório Markdown a partir dos Traces XML Reais
```bash
python3 scripts/generate_ns3_flowmonitor_markdown_report.py
```

---

## 5. Como Sincronizar e Subir os Resultados para o GitHub

Após rodar os testes ou simulações, você pode subir todos os resultados usando qualquer uma das opções abaixo:

### Opção A: Via Atalho Make (Recomendado)
```bash
make push-results
```

### Opção B: Manual via Git
```bash
git add experiments/results/ docs/
git commit -m "chore(sim): update ns-3 FlowMonitor experimental traces and reports"
git push origin main
```
