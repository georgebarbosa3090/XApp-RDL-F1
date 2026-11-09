# Cenários ns-3 + 5G-LENA

Cenários C++ usados para avaliar a xApp RDL (H-RDL). Um cenário existir ou compilar não é resultado: só contam execuções feitas pelos executores com proveniência e aprovadas pelo certificador (ver [política de evidência](../../docs/compliance/EXPERIMENTAL_EVIDENCE_POLICY.md)).

## 1. Pilhas

| Pilha | Versões | Backend no manifesto | Uso |
| :-- | :-- | :-- | :-- |
| Nativa | ns-3.48 (`d2add90`) + 5G-LENA v5.1 (`cedcead`) | `NS3_5GLENA` | cenários de conflito S0–S7; **sem E2** |
| NORI | ns-3.42 (`ab4cce0`) + nr `78b7179` + NORI `8a30867` | `NORI_NS3` | E2 real e closed loop (S8), via Helm em [`deploy/helm/nori-ns3`](../../deploy/helm/nori-ns3/README.md) |

O NORI não compila sobre ns-3.48 / 5G-LENA v5.1, por isso as pilhas são separadas. A instalação da pilha nativa está no [guia operacional](../../docs/04_instalacao_e_operacao.md). O `scripts/setup_ns3.sh` legado pode instalar outras versões e não deve ser usado para gerar evidência.

## 2. Cenários da Fase 1

| ID | Cenário | Arquivo | Conflito exercitado |
| :-: | :-- | :-- | :-- |
| S0 | sem conflito | [`scenario_rdl_no_conflict.cc`](scenario_rdl_no_conflict.cc) | nenhum; a H-RDL não deve interferir |
| S1 | conflito direto de PRB | [`scenario_rdl_direct_prb_conflict.cc`](scenario_rdl_direct_prb_conflict.cc) | duas xApps com cotas de PRB diferentes no mesmo alvo |
| S2 | conflito indireto (TVS) | [`scenario_rdl_tvs_conflict.cc`](scenario_rdl_tvs_conflict.cc) | cota de PRB × handover |
| S3 | energia × QoS | [`scenario_rdl_energy_vs_qos.cc`](scenario_rdl_energy_vs_qos.cc) | potência de transmissão × cota de PRB |
| S4 | mobilidade × energia | [`scenario_rdl_ts_vs_energy.cc`](scenario_rdl_ts_vs_energy.cc) | handover para célula que a Energy Saving reduz |
| S5 | ping-pong temporal | [`scenario_rdl_temporal_pingpong.cc`](scenario_rdl_temporal_pingpong.cc) | handovers alternados entre duas células |
| S6 | tempestade de conflitos | [`scenario_rdl_conflict_storm.cc`](scenario_rdl_conflict_storm.cc) | muitas propostas por janela |
| S7 | injeção de falhas | [`scenario_rdl_fault_injection.cc`](scenario_rdl_fault_injection.cc) | propostas fora dos limites físicos |
| S8 | closed loop com NORI | — (só na bancada NORI: variante `nori-rc-slicing-flowmon`, `bash scripts/run_nori_scenario.sh S8 <semente>`) | xslice × embb_throughput disputam a cota de PRB; o H-RDL decide sobre o KPM real e o RIC Control E2SM-RC altera a RAN |

As propostas de cada cenário estão em [`conflicts/catalog.json`](conflicts/catalog.json). Os cenários S0–S8 também rodam na bancada NORI com a cadeia E2 real (só a cota de PRB no gNB 0 é atuável lá); ver [docs/05](../../docs/05_observabilidade_e_campanhas.md).

## 3. Atuação na RAN

[`rdl-nr-common.h`](rdl-nr-common.h) monta a rede NR (S0 e S4–S7), aplica as ações durante a simulação e mede KPIs:

| Ação | Efeito no 5G-LENA v5.1 |
| :-- | :-- |
| `PRB_QUOTA` (%) | máscara de RBG no escalonador (`NrMacSchedulerNs3::SetDlNotchedRbgMask`; o `NrMacSchedulerTdmaRR` padrão respeita a máscara) |
| `TX_POWER` (dBm) | `NrGnbPhy::SetTxPower` |
| `HANDOVER` (gNB de destino) | `NrHelper::HandoverRequest` para os UEs do gNB de origem, um a cada 10 ms |
| `SCHEDULER_WEIGHT` | não suportado; registrado como `UNSUPPORTED` |

Saídas por execução: `rdl_actuation_log.csv` (cada ação, instante e efeito) e `rdl_kpi_timeseries.csv` (vazão e atraso por célula a cada `--kpiPeriod`). As linhas `[RDL-ACT]` e `[RDL-KPI]` aparecem ao vivo no terminal.

## 4. Baselines

| Baseline | Regra |
| :-- | :-- |
| B0 | sem coordenação: cada proposta é aplicada ao chegar |
| B1 | FIFO por janela de 200 ms e alvo |
| B2 | prioridade estática por janela e alvo |
| B3 | H-RDL: `RDLxApp._process_action_group` por janela, no relógio simulado |

É uma avaliação **em malha aberta**: o cronograma de propostas é fixo e não há E2 nem realimentação de KPM.

## 5. Execução

Uma execução:

```bash
python scripts/certification/run_conflict_experiment.py --scenario S1 --baseline B3 --seed 1001
```

Campanha (retomável; compila uma vez e roda cada execução com `--no-build`):

```bash
python scripts/certification/run_conflict_campaign.py --seeds 1001-1005 --jobs 2
```

Análise e certificação:

```bash
python scripts/certification/analyze_conflict_runs.py
```

```bash
python scripts/certification/certify_chain.py
```

Cenário avulso, sem o driver de conflitos:

```bash
bash scripts/certification/run_ns3_certified.sh --scenario scenario_rdl_direct_prb_conflict --seed 1001 --baseline B3 -- --simTime=10
```

Cada execução fica em `experiments/runs/<run_id>/` com `execution_manifest.json`, `logs/`, `raw/` (FlowMonitor, séries do `rdl-nr-common.h`, `action_schedule.csv`, `decision_log.json`) e `hashes.sha256`. Execuções existentes nunca são sobrescritas.

## 6. Particularidades

- **SRS e handover.** Transferir vários UEs aborta o 5G-LENA v5.1 em `NrSpectrumPhy::StartRxSrs`. Escalonar os handovers não basta; S2, S4 e S5 rodam com `--disableSrs=true` em todos os baselines (registrado em `conflicts/catalog.json`). O tráfego dos cenários é downlink.
- **Semente.** Os cenários chamam `SeedManager::SetSeed(--seed)` depois de ler a linha de comando, o que anula `--RngRun`; o executor passa `--seed` e registra `rng_args` no manifesto.
- **Disco.** O executor recusa rodar com menos de 1 GB livre; a campanha para e pode ser retomada. Os traces completos do 5G-LENA em S2/S3 ficam desligados salvo `--nrTraces=true`.
- **Falhas.** Só conta a execução com `hashes.sha256`. Com `--retry-failed`, execuções sem `SUCCESS` vão para `experiments/runs_failed/` e são refeitas.
- **FlowMonitor.** Exclua os fluxos internos do EPC (GTP-C, porta 2123). Antes de 2026-11-08, S2 e S3 gravavam o mesmo `flowmonitor_results.xml`, e os arquivos de S8 em `experiments/results/ns3_runs/` são idênticos aos de S3.

## 7. Limitações conhecidas

- A percepção agrupa conflitos por gNB: conflitos **entre células** (S4, S5) não são detectados.
- Não há E2 nem closed loop na pilha nativa.

Resultados: [`docs/06_metodologia_e_resultados.md`](../../docs/06_metodologia_e_resultados.md).

## 8. Arquivos removidos

Os esboços S9–S15, os cenários exploratórios 5G-Advanced/6G e os roteiros legados `run_all_s0_s15_simulations.sh` e `run_b0_b6_campaign_30seeds.sh` (sem manifesto, com `git commit`/`git push` automáticos) foram removidos em 2026-11-09 (achado 45 de docs/07). As execuções vêm só de `scripts/certification/run_conflict_experiment.py` (pilha nativa) e `scripts/run_nori_scenario.sh` (bancada NORI).
