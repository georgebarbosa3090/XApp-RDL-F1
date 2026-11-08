# Relatório da campanha de conflitos multi-xApp (ns-3.48 + 5G-LENA v5.1)

Gerado em 2026-11-08T11:06:55Z por [`generate_campaign_report.py`](../../scripts/certification/generate_campaign_report.py) a partir de [`conflict_analysis_20261108T103510Z.json`](conflict_analysis_20261108T103510Z.json) (análise gerada em 2026-11-08T10:35:10Z), dos manifestos das execuções e do catálogo de cenários. Nenhum valor foi digitado à mão.

## 1. Resumo

- **Desenho:** 8 cenários (S0–S7) × 4 baselines (B0, B1, B2, B3) × 5 sementes (1001–1005) = 160 execuções.
- **Status:** 160 `SUCCESS`; 0 execução(ões) ignorada(s) pela análise.
- **Avaliação em malha aberta:** as propostas das xApps vêm do catálogo, cada baseline decide e as ações decididas são aplicadas na RAN simulada. Não há E2 nem realimentação de KPM.
- **Hipóteses:** inconclusiva: H2, H3; suportada: H0, H1, H4, H5, H6, H7 (seção 9).
- **Certificação:** G0 CERTIFIED, G1 NOT_CERTIFIED, G2 LOCAL_ONLY, G3 BLOCKED, G4 BLOCKED, G5 BLOCKED, G6 BLOCKED ([`certificate_20261108T103515Z.json`](../certification/certificate_20261108T103515Z.json)).

## 2. Pergunta e hipóteses

**Pergunta.** Quando várias xApps propõem controles conflitantes, a decisão da H-RDL (B3) leva a um desempenho de rede melhor ou mais seguro que não coordenar (B0), FIFO por janela e alvo (B1) ou prioridade estática por janela e alvo (B2)?

As hipóteses abaixo foram derivadas do tratamento esperado de cada tipo de conflito na [taxonomia](../../docs/03_taxonomia_de_conflitos_e_cenarios.md), escrita antes desta campanha. Não houve pré-registro formal. H4 e H5 descrevem limitações conhecidas: "suportada" significa que a limitação se confirmou.

| ID | Cenário | Tipo de conflito | Hipótese | Critérios |
| :-- | :-- | :-- | :-- | :-- |
| H0 | S0 | controle (sem conflito) | Sem conflito, a H-RDL é transparente: B3 não difere do B0 em vazão nem em atraso. | B3 − B0 em Vazão no conflito (Mbps): `=0`; B3 − B0 em Atraso no conflito (ms): `=0` |
| H1 | S1 | direto (PRB) | Em conflito direto de PRB, a H-RDL elimina as oscilações e melhora vazão e atraso em relação ao B0. | Oscilações de B3 == 0 em todas as sementes; B3 − B0 em Vazão no conflito (Mbps): `>0`; B3 − B0 em Atraso no conflito (ms): `<0` |
| H2 | S2 | indireto (TVS) | Em conflito indireto, a H-RDL escolhe um subconjunto de ações que não piora vazão nem atraso em relação a B0, B1 e B2. | B3 − B0 em Vazão no conflito (Mbps): `>=0`; B3 − B0 em Atraso no conflito (ms): `<=0`; B3 − B1 em Vazão no conflito (Mbps): `>=0`; B3 − B1 em Atraso no conflito (ms): `<=0` |
| H3 | S3 | direto (potência) | Em conflito direto de potência, a H-RDL elimina as oscilações sem perda de vazão em relação ao B0. | Oscilações de B3 == 0 em todas as sementes; B3 − B0 em Vazão no conflito (Mbps): `>=0` |
| H4 | S4 | entre células (limitação esperada) | A H-RDL não detecta o conflito entre células: o handover acontece e B3 não difere do B1 em vazão nem em atraso. | Handovers de B3 > 0 em todas as sementes; B3 − B1 em Vazão no conflito (Mbps): `=0`; B3 − B1 em Atraso no conflito (ms): `=0` |
| H5 | S5 | temporal entre células (limitação esperada) | A H-RDL não detecta o ping-pong entre células: B3 aplica os mesmos handovers que o B0. | B3 − B0 em Handovers: `=0`; B3 − B0 em Vazão no conflito (Mbps): `=0` |
| H6 | S6 | tempestade | Sob tempestade de conflitos, a H-RDL aplica menos ações, elimina as oscilações e reduz o atraso em relação a B0, B1 e B2. | B3 − B1 em Ações aplicadas: `<0`; Oscilações de B3 == 0 em todas as sementes; B3 − B0 em Atraso no conflito (ms): `<0`; B3 − B1 em Atraso no conflito (ms): `<0`; B3 − B2 em Atraso no conflito (ms): `<0` |
| H7 | S7 | ação insegura | O Safety Guard impede que ações inseguras cheguem à RAN no B3, enquanto B0, B1 e B2 as aplicam. | Ações inseguras de B3 == 0 em todas as sementes; Ações inseguras de B0 > 0 em todas as sementes; Ações inseguras de B1 > 0 em todas as sementes; Ações inseguras de B2 > 0 em todas as sementes |

Regras de decisão sobre a diferença pareada por semente (A − B), com IC 95 % de t de Student:

- `<0` / `>0`: atendido se o IC inteiro está do lado esperado; não atendido se o IC inteiro está do lado oposto; inconclusivo se o IC contém zero.
- `<=0` / `>=0` (não piora): não atendido se o IC inteiro está do lado desfavorável; com o IC contendo zero, atendido se a média não está do lado desfavorável e inconclusivo caso contrário.
- `=0`: atendido se o IC contém zero. Isso indica ausência de diferença detectável com n = 5, não equivalência.
- Hipótese **suportada** se todos os critérios forem atendidos, **refutada** se algum não for, **inconclusiva** nos demais casos.

## 3. Desenho, cenários e ambiente

| Cenário | Programa ns-3 | Janela de conflito | Argumentos | Conflito |
| :-- | :-- | :-- | :-- | :-- |
| S0 | `scenario_rdl_no_conflict` | 10,0–15,0 s | `--simTime=20` | Ações independentes em gNBs distintos: não há conflito; serve de controle (pass-through). |
| S1 | `scenario_rdl_direct_prb_conflict` | 10,0–15,0 s | `--simTime=20` `--udpIntervalUs=200` | Conflito direto de PRB na mesma célula: xApp-QoS pede 75%, xApp-Energy pede 30%. |
| S2 | `scenario_rdl_tvs_conflict` | 10,0–15,0 s | `--simTime=20` `--disableSrs=true` | Conflito indireto TVS: xSlice reserva PRB na célula macro enquanto o Traffic Steering move os UEs dela para a small cell. |
| S3 | `scenario_rdl_energy_vs_qos` | 10,0–15,0 s | `--simTime=20` | Conflito direto de potência: Energy Saving reduz para 10 dBm, xSlice exige 40 dBm na mesma célula. |
| S4 | `scenario_rdl_ts_vs_energy` | 15,0–25,0 s | `--simTime=30` `--disableSrs=true` | Conflito entre células: Traffic Steering move UEs da gNB0 congestionada para a gNB1 enquanto o Energy Saving coloca a gNB1 em baixa potência. |
| S5 | `scenario_rdl_temporal_pingpong` | 18,0–26,0 s | `--simTime=30` `--disableSrs=true` | Ping-pong temporal: Traffic Steering move UEs para a gNB1 e o Load Balancer os devolve à gNB0, alternadamente. |
| S6 | `scenario_rdl_conflict_storm` | 10,0–15,0 s | `--simTime=20` `--loadLevel=0` | Tempestade de conflitos: seis xApps disputam PRB e potência nas quatro gNBs a cada 0,5 s. |
| S7 | `scenario_rdl_fault_injection` | 10,0–15,0 s | `--simTime=25` | Injeção de falhas: uma xApp maliciosa pede potência fora do limite físico (60 dBm) e cota de PRB inválida (150%), concorrendo com ações legítimas. |

Janela de decisão dos baselines: 200 ms. Janelas de medição: antes = (máx(1,5; início − 5), início]; conflito = (início, fim]; depois = (fim, simTime − 0,5] s.

| Métrica | Definição |
| :-- | :-- |
| Vazão antes / no conflito / depois | média, por intervalo de 100 ms, da vazão somada de todas as células (Mbps) |
| Atraso no conflito | atraso médio fim a fim ponderado por pacote durante a janela de conflito (ms) |
| Ações aplicadas, handovers | linhas com status `APPLIED` em `rdl_actuation_log.csv` |
| Ações inseguras | `TX_POWER` fora de [−10, 43] dBm ou `PRB_QUOTA` fora de [0, 100] aplicadas na RAN |
| Oscilações | trocas de valor num mesmo alvo (gNB, parâmetro) entre ações aplicadas |

| Componente | Valor(es) registrados nos manifestos |
| :-- | :-- |
| ns-3 | 3.48 (`d2add90`) |
| 5G-LENA | v5.1 (`cedcead`) |
| os | Ubuntu 24.04.1 LTS |
| kernel | 6.6.87.2-microsoft-standard-WSL2 |
| compiler | g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0 |
| cmake | cmake version 3.28.3 |
| commit do repositório | `8fbbf98`; `c18760b`; `dedae21`; `dfe8b1f`; `ee72885` |

Execuções entre 2026-11-08T02:47:45Z e 2026-11-08T10:35:06Z (UTC).

## 4. Comandos de execução (terminal WSL/Ubuntu)

Todos os comandos abaixo rodam direto no terminal do Ubuntu (WSL), sem passar pelo Windows. O ns-3.48 + 5G-LENA v5.1 compilado fica em `~/ns3-oran-workspace/ns-3-oran` (variável `NS3_DIR`); a saída `[RDL-ACT]`/`[RDL-KPI]` de cada execução aparece ao vivo. Detalhes do ambiente no [guia operacional](../../docs/02_guia_operacional_deploy_e_simulacao.md).

**Preparação (uma vez).** O driver usa a `RDLxApp` real no B3 e precisa das dependências do projeto. Sem `sudo` (o Ubuntu 24.04 não traz `python3-venv`), o venv é criado sem pip e as dependências são instaladas com o pip do sistema:

```bash
python3 -m venv --without-pip ~/.venvs/xapp-rdl
python3 -m pip --python ~/.venvs/xapp-rdl/bin/python install "pydantic>=2.0.0" "structlog>=23.1.0" "prometheus-client>=0.19.0" "pycrate>=0.7.0" "requests>=2.31.0" "numpy>=1.24.0" "fastapi>=0.100.0" "uvicorn>=0.20.0"
```

**Em cada terminal novo:**

```bash
cd <repo>
source ~/.venvs/xapp-rdl/bin/activate
```

Campanha completa (retomável: execuções com `hashes.sha256` são puladas; interrompidas são removidas e refeitas):

```bash
python scripts/certification/run_conflict_campaign.py \
    --scenarios S0 S1 S2 S3 S4 S5 S6 S7 --baselines B0 B1 B2 B3 --seeds 1001-1005 --jobs 2
```

Uma semente por vez (cada semente concluída forma um conjunto pareado completo):

```bash
for s in 1001 1002 1003 1004 1005; do
  python scripts/certification/run_conflict_campaign.py --scenarios S0 S1 S2 S3 S4 S5 S6 S7 --baselines B0 B1 B2 B3 --seeds $s --jobs 2 --skip-analysis
done
```

Refazer execuções com falha (as originais vão para `experiments/runs_failed/<run_id>__<UTC>`):

```bash
python scripts/certification/run_conflict_campaign.py \
    --scenarios S0 S1 S2 S3 S4 S5 S6 S7 --baselines B0 B1 B2 B3 --seeds 1001-1005 --jobs 2 --retry-failed
```

Uma execução isolada:

```bash
python scripts/certification/run_conflict_experiment.py --scenario S1 --baseline B3 --seed 1001
```

Só o cronograma de ações decidido pelo baseline, sem simular:

```bash
python scripts/certification/run_conflict_experiment.py --scenario S1 --baseline B3 --seed 1001 --dry-run
```

Análise, certificação e este relatório (a campanha já roda os dois primeiros ao final):

```bash
python scripts/certification/analyze_conflict_runs.py
python scripts/certification/certify_chain.py
python scripts/certification/generate_campaign_report.py
```

Na B3, as mensagens de porta 8080/8081 em uso vêm dos servidores de saúde e métricas da `RDLxApp` e não afetam a decisão.

Por baixo, cada execução chama o executor com proveniência [`run_ns3_certified.sh`](../../scripts/certification/run_ns3_certified.sh), que roda o comando ns-3 registrado no manifesto (lista completa no apêndice A). Exemplo:

```bash
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S1_B3_seed1001/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
```

## 5. Resultados agregados

Média ± IC 95 % (t de Student) sobre as sementes; n por célula na coluna n.

| Cenário | Baseline | n | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| S0 | B0 | 5 | 3,07 ± 0,00 | 2,63 ± 0,47 | 2,28 ± 0,59 | 34,50 ± 12,26 | 2,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S0 | B1 | 5 | 3,07 ± 0,00 | 2,68 ± 0,49 | 2,38 ± 0,68 | 29,45 ± 10,93 | 2,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S0 | B2 | 5 | 3,07 ± 0,00 | 2,68 ± 0,49 | 2,38 ± 0,68 | 29,45 ± 10,93 | 2,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S0 | B3 | 5 | 3,07 ± 0,00 | 2,68 ± 0,49 | 2,38 ± 0,68 | 29,45 ± 10,93 | 2,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S1 | B0 | 5 | 366,77 ± 0,02 | 118,04 ± 0,02 | 109,68 ± 0,0044 | 17,05 ± 0,0017 | 10,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 9,00 ± 0,00 |
| S1 | B1 | 5 | 366,77 ± 0,02 | 278,97 ± 0,02 | 275,30 ± 0,01 | 9,14 ± 0,0004 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S1 | B2 | 5 | 366,77 ± 0,02 | 278,97 ± 0,02 | 275,30 ± 0,01 | 9,14 ± 0,0004 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S1 | B3 | 5 | 366,77 ± 0,02 | 278,97 ± 0,02 | 275,30 ± 0,01 | 9,14 ± 0,0004 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S2 | B0 | 5 | 194,94 ± 4,78 | 197,49 ± 0,06 | 197,52 ± 0,01 | 7,42 ± 0,84 | 5,80 ± 0,56 | 0,80 ± 0,56 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S2 | B1 | 5 | 194,94 ± 4,78 | 197,56 ± 0,09 | 197,51 ± 0,01 | 7,48 ± 0,90 | 5,80 ± 0,56 | 0,80 ± 0,56 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S2 | B2 | 5 | 194,94 ± 4,78 | 197,56 ± 0,09 | 197,51 ± 0,01 | 7,48 ± 0,90 | 5,80 ± 0,56 | 0,80 ± 0,56 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S2 | B3 | 5 | 194,94 ± 4,78 | 193,24 ± 14,89 | 202,21 ± 37,83 | 26,16 ± 23,40 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S3 | B0 | 5 | 1,93 ± 0,34 | 12,20 ± 0,09 | 12,21 ± 0,09 | 14,13 ± 12,72 | 10,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 9,00 ± 0,00 |
| S3 | B1 | 5 | 1,93 ± 0,34 | 11,86 ± 0,96 | 11,94 ± 0,85 | 27,86 ± 44,55 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S3 | B2 | 5 | 1,93 ± 0,34 | 11,86 ± 0,96 | 11,94 ± 0,85 | 27,86 ± 44,55 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S3 | B3 | 5 | 1,93 ± 0,34 | 11,86 ± 0,96 | 11,94 ± 0,85 | 27,86 ± 44,55 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S4 | B0 | 5 | 32,36 ± 0,00 | 23,87 ± 0,19 | 24,09 ± 0,25 | 152,90 ± 0,79 | 11,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S4 | B1 | 5 | 32,36 ± 0,00 | 23,75 ± 0,25 | 23,75 ± 0,33 | 150,23 ± 1,02 | 11,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S4 | B2 | 5 | 32,36 ± 0,00 | 23,75 ± 0,25 | 23,75 ± 0,33 | 150,23 ± 1,02 | 11,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S4 | B3 | 5 | 32,36 ± 0,00 | 23,75 ± 0,25 | 23,75 ± 0,33 | 150,23 ± 1,02 | 10,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S5 | B0 | 5 | 9,01 ± 0,57 | 9,02 ± 0,09 | 8,90 ± 0,23 | 31,09 ± 6,69 | 8,00 ± 0,00 | 8,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S5 | B1 | 5 | 9,01 ± 0,57 | 9,01 ± 0,11 | 8,86 ± 0,22 | 30,68 ± 6,89 | 8,00 ± 0,00 | 8,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S5 | B2 | 5 | 9,01 ± 0,57 | 9,01 ± 0,11 | 8,86 ± 0,22 | 30,68 ± 6,89 | 8,00 ± 0,00 | 8,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S5 | B3 | 5 | 9,01 ± 0,57 | 9,01 ± 0,11 | 8,86 ± 0,22 | 30,68 ± 6,89 | 8,00 ± 0,00 | 8,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S6 | B0 | 5 | 19,84 ± 0,37 | 18,97 ± 1,74 | 20,47 ± 3,23 | 94,38 ± 12,82 | 80,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 57,00 ± 0,00 |
| S6 | B1 | 5 | 19,84 ± 0,37 | 20,65 ± 2,14 | 22,22 ± 2,33 | 63,10 ± 14,90 | 55,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 9,00 ± 0,00 |
| S6 | B2 | 5 | 19,84 ± 0,37 | 20,74 ± 1,87 | 22,24 ± 2,02 | 67,69 ± 18,49 | 55,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 9,00 ± 0,00 |
| S6 | B3 | 5 | 19,84 ± 0,37 | 21,19 ± 1,41 | 23,03 ± 0,59 | 51,33 ± 6,67 | 25,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S7 | B0 | 5 | 4,17 ± 0,17 | 5,54 ± 0,01 | 5,46 ± 0,0010 | 10,54 ± 0,35 | 15,00 ± 0,00 | 0,00 ± 0,00 | 10,00 ± 0,00 | 0,00 ± 0,00 |
| S7 | B1 | 5 | 4,17 ± 0,17 | 5,49 ± 0,01 | 5,46 ± 0,0013 | 13,24 ± 0,77 | 15,00 ± 0,00 | 0,00 ± 0,00 | 10,00 ± 0,00 | 0,00 ± 0,00 |
| S7 | B2 | 5 | 4,17 ± 0,17 | 5,49 ± 0,01 | 5,46 ± 0,0013 | 13,24 ± 0,77 | 15,00 ± 0,00 | 0,00 ± 0,00 | 10,00 ± 0,00 | 0,00 ± 0,00 |
| S7 | B3 | 5 | 4,17 ± 0,17 | 5,48 ± 0,01 | 5,46 ± 0,0005 | 13,55 ± 0,73 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |

## 6. Resultados por semente

Valores de cada execução, como calculados pela análise a partir de `raw/rdl_kpi_timeseries.csv` e `raw/rdl_actuation_log.csv` da própria execução.

### 6.1 Semente 1001

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | 3,07 | 2,98 | 2,40 | 37,27 | 2 | 0 | 0 | 0 | `nr_S0_B0_seed1001` |
| S0 | B1 | 3,07 | 3,06 | 2,90 | 22,30 | 2 | 0 | 0 | 0 | `nr_S0_B1_seed1001` |
| S0 | B2 | 3,07 | 3,06 | 2,90 | 22,30 | 2 | 0 | 0 | 0 | `nr_S0_B2_seed1001` |
| S0 | B3 | 3,07 | 3,06 | 2,90 | 22,30 | 2 | 0 | 0 | 0 | `nr_S0_B3_seed1001` |
| S1 | B0 | 366,75 | 118,06 | 109,68 | 17,05 | 10 | 0 | 0 | 9 | `nr_S1_B0_seed1001` |
| S1 | B1 | 366,75 | 278,98 | 275,30 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B1_seed1001` |
| S1 | B2 | 366,75 | 278,98 | 275,30 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B2_seed1001` |
| S1 | B3 | 366,75 | 278,98 | 275,30 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B3_seed1001` |
| S2 | B0 | 197,51 | 197,49 | 197,52 | 6,71 | 6 | 1 | 0 | 0 | `nr_S2_B0_seed1001` |
| S2 | B1 | 197,51 | 197,49 | 197,52 | 6,71 | 6 | 1 | 0 | 0 | `nr_S2_B1_seed1001` |
| S2 | B2 | 197,51 | 197,49 | 197,52 | 6,71 | 6 | 1 | 0 | 0 | `nr_S2_B2_seed1001` |
| S2 | B3 | 197,51 | 197,49 | 197,52 | 6,72 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed1001` |
| S3 | B0 | 2,05 | 12,27 | 12,29 | 5,66 | 10 | 0 | 0 | 9 | `nr_S3_B0_seed1001` |
| S3 | B1 | 2,05 | 12,26 | 12,29 | 7,16 | 5 | 0 | 0 | 0 | `nr_S3_B1_seed1001` |
| S3 | B2 | 2,05 | 12,26 | 12,29 | 7,16 | 5 | 0 | 0 | 0 | `nr_S3_B2_seed1001` |
| S3 | B3 | 2,05 | 12,26 | 12,29 | 7,16 | 5 | 0 | 0 | 0 | `nr_S3_B3_seed1001` |
| S4 | B0 | 32,36 | 23,73 | 23,78 | 153,15 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1001` |
| S4 | B1 | 32,36 | 23,45 | 23,77 | 149,31 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1001` |
| S4 | B2 | 32,36 | 23,45 | 23,77 | 149,31 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1001` |
| S4 | B3 | 32,36 | 23,45 | 23,77 | 149,31 | 10 | 1 | 0 | 0 | `nr_S4_B3_seed1001` |
| S5 | B0 | 8,81 | 8,93 | 9,03 | 36,33 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1001` |
| S5 | B1 | 8,81 | 8,96 | 9,04 | 34,70 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1001` |
| S5 | B2 | 8,81 | 8,96 | 9,04 | 34,70 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1001` |
| S5 | B3 | 8,81 | 8,96 | 9,04 | 34,70 | 8 | 8 | 0 | 0 | `nr_S5_B3_seed1001` |
| S6 | B0 | 19,98 | 17,45 | 16,66 | 106,09 | 80 | 0 | 0 | 57 | `nr_S6_B0_seed1001` |
| S6 | B1 | 19,98 | 18,99 | 24,64 | 79,33 | 55 | 0 | 0 | 9 | `nr_S6_B1_seed1001` |
| S6 | B2 | 19,98 | 18,68 | 24,72 | 92,94 | 55 | 0 | 0 | 9 | `nr_S6_B2_seed1001` |
| S6 | B3 | 19,98 | 19,99 | 23,53 | 60,57 | 25 | 0 | 0 | 0 | `nr_S6_B3_seed1001` |
| S7 | B0 | 4,04 | 5,54 | 5,46 | 10,27 | 15 | 0 | 10 | 0 | `nr_S7_B0_seed1001` |
| S7 | B1 | 4,04 | 5,48 | 5,46 | 12,86 | 15 | 0 | 10 | 0 | `nr_S7_B1_seed1001` |
| S7 | B2 | 4,04 | 5,48 | 5,46 | 12,86 | 15 | 0 | 10 | 0 | `nr_S7_B2_seed1001` |
| S7 | B3 | 4,04 | 5,47 | 5,46 | 13,13 | 5 | 0 | 0 | 0 | `nr_S7_B3_seed1001` |

### 6.2 Semente 1002

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | 3,07 | 2,31 | 1,98 | 42,24 | 2 | 0 | 0 | 0 | `nr_S0_B0_seed1002` |
| S0 | B1 | 3,07 | 2,24 | 1,97 | 38,27 | 2 | 0 | 0 | 0 | `nr_S0_B1_seed1002` |
| S0 | B2 | 3,07 | 2,24 | 1,97 | 38,27 | 2 | 0 | 0 | 0 | `nr_S0_B2_seed1002` |
| S0 | B3 | 3,07 | 2,24 | 1,97 | 38,27 | 2 | 0 | 0 | 0 | `nr_S0_B3_seed1002` |
| S1 | B0 | 366,76 | 118,03 | 109,68 | 17,05 | 10 | 0 | 0 | 9 | `nr_S1_B0_seed1002` |
| S1 | B1 | 366,76 | 278,98 | 275,29 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B1_seed1002` |
| S1 | B2 | 366,76 | 278,98 | 275,29 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B2_seed1002` |
| S1 | B3 | 366,76 | 278,98 | 275,29 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B3_seed1002` |
| S2 | B0 | 188,29 | 197,55 | 197,52 | 8,20 | 6 | 1 | 0 | 0 | `nr_S2_B0_seed1002` |
| S2 | B1 | 188,29 | 197,56 | 197,51 | 8,21 | 6 | 1 | 0 | 0 | `nr_S2_B1_seed1002` |
| S2 | B2 | 188,29 | 197,56 | 197,51 | 8,21 | 6 | 1 | 0 | 0 | `nr_S2_B2_seed1002` |
| S2 | B3 | 188,29 | 208,79 | 254,55 | 49,45 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed1002` |
| S3 | B0 | 2,05 | 12,20 | 12,21 | 17,32 | 10 | 0 | 0 | 9 | `nr_S3_B0_seed1002` |
| S3 | B1 | 2,05 | 12,09 | 12,17 | 25,71 | 5 | 0 | 0 | 0 | `nr_S3_B1_seed1002` |
| S3 | B2 | 2,05 | 12,09 | 12,17 | 25,71 | 5 | 0 | 0 | 0 | `nr_S3_B2_seed1002` |
| S3 | B3 | 2,05 | 12,09 | 12,17 | 25,71 | 5 | 0 | 0 | 0 | `nr_S3_B3_seed1002` |
| S4 | B0 | 32,36 | 24,02 | 24,35 | 152,84 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1002` |
| S4 | B1 | 32,36 | 23,90 | 24,04 | 149,59 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1002` |
| S4 | B2 | 32,36 | 23,90 | 24,04 | 149,59 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1002` |
| S4 | B3 | 32,36 | 23,90 | 24,04 | 149,59 | 10 | 1 | 0 | 0 | `nr_S4_B3_seed1002` |
| S5 | B0 | 8,81 | 8,97 | 8,81 | 33,89 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1002` |
| S5 | B1 | 8,81 | 8,94 | 8,82 | 34,59 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1002` |
| S5 | B2 | 8,81 | 8,94 | 8,82 | 34,59 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1002` |
| S5 | B3 | 8,81 | 8,94 | 8,82 | 34,59 | 8 | 8 | 0 | 0 | `nr_S5_B3_seed1002` |
| S6 | B0 | 19,48 | 20,73 | 22,50 | 90,55 | 80 | 0 | 0 | 57 | `nr_S6_B0_seed1002` |
| S6 | B1 | 19,48 | 22,30 | 23,76 | 50,03 | 55 | 0 | 0 | 9 | `nr_S6_B1_seed1002` |
| S6 | B2 | 19,48 | 22,06 | 21,62 | 54,32 | 55 | 0 | 0 | 9 | `nr_S6_B2_seed1002` |
| S6 | B3 | 19,48 | 22,10 | 23,25 | 47,40 | 25 | 0 | 0 | 0 | `nr_S6_B3_seed1002` |
| S7 | B0 | 4,19 | 5,54 | 5,46 | 10,73 | 15 | 0 | 10 | 0 | `nr_S7_B0_seed1002` |
| S7 | B1 | 4,19 | 5,49 | 5,46 | 13,59 | 15 | 0 | 10 | 0 | `nr_S7_B1_seed1002` |
| S7 | B2 | 4,19 | 5,49 | 5,46 | 13,59 | 15 | 0 | 10 | 0 | `nr_S7_B2_seed1002` |
| S7 | B3 | 4,19 | 5,48 | 5,46 | 13,64 | 5 | 0 | 0 | 0 | `nr_S7_B3_seed1002` |

### 6.3 Semente 1003

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | 3,07 | 2,53 | 1,94 | 41,40 | 2 | 0 | 0 | 0 | `nr_S0_B0_seed1003` |
| S0 | B1 | 3,07 | 2,74 | 1,96 | 35,53 | 2 | 0 | 0 | 0 | `nr_S0_B1_seed1003` |
| S0 | B2 | 3,07 | 2,74 | 1,96 | 35,53 | 2 | 0 | 0 | 0 | `nr_S0_B2_seed1003` |
| S0 | B3 | 3,07 | 2,74 | 1,96 | 35,53 | 2 | 0 | 0 | 0 | `nr_S0_B3_seed1003` |
| S1 | B0 | 366,79 | 118,04 | 109,68 | 17,05 | 10 | 0 | 0 | 9 | `nr_S1_B0_seed1003` |
| S1 | B1 | 366,79 | 278,95 | 275,29 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B1_seed1003` |
| S1 | B2 | 366,79 | 278,95 | 275,29 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B2_seed1003` |
| S1 | B3 | 366,79 | 278,95 | 275,29 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B3_seed1003` |
| S2 | B0 | 195,04 | 197,42 | 197,51 | 7,63 | 6 | 1 | 0 | 0 | `nr_S2_B0_seed1003` |
| S2 | B1 | 195,04 | 197,65 | 197,50 | 7,79 | 6 | 1 | 0 | 0 | `nr_S2_B1_seed1003` |
| S2 | B2 | 195,04 | 197,65 | 197,50 | 7,79 | 6 | 1 | 0 | 0 | `nr_S2_B2_seed1003` |
| S2 | B3 | 195,04 | 183,22 | 182,85 | 34,61 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed1003` |
| S3 | B0 | 2,05 | 12,14 | 12,14 | 29,94 | 10 | 0 | 0 | 9 | `nr_S3_B0_seed1003` |
| S3 | B1 | 2,05 | 10,48 | 10,73 | 90,38 | 5 | 0 | 0 | 0 | `nr_S3_B1_seed1003` |
| S3 | B2 | 2,05 | 10,48 | 10,73 | 90,38 | 5 | 0 | 0 | 0 | `nr_S3_B2_seed1003` |
| S3 | B3 | 2,05 | 10,48 | 10,73 | 90,38 | 5 | 0 | 0 | 0 | `nr_S3_B3_seed1003` |
| S4 | B0 | 32,36 | 23,71 | 24,07 | 152,87 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1003` |
| S4 | B1 | 32,36 | 23,68 | 23,35 | 150,30 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1003` |
| S4 | B2 | 32,36 | 23,68 | 23,35 | 150,30 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1003` |
| S4 | B3 | 32,36 | 23,68 | 23,35 | 150,30 | 10 | 1 | 0 | 0 | `nr_S4_B3_seed1003` |
| S5 | B0 | 9,83 | 9,13 | 9,01 | 22,22 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1003` |
| S5 | B1 | 9,83 | 9,15 | 9,01 | 21,80 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1003` |
| S5 | B2 | 9,83 | 9,15 | 9,01 | 21,80 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1003` |
| S5 | B3 | 9,83 | 9,15 | 9,01 | 21,80 | 8 | 8 | 0 | 0 | `nr_S5_B3_seed1003` |
| S6 | B0 | 19,57 | 20,12 | 22,64 | 80,87 | 80 | 0 | 0 | 57 | `nr_S6_B0_seed1003` |
| S6 | B1 | 19,57 | 21,08 | 20,73 | 53,17 | 55 | 0 | 0 | 9 | `nr_S6_B1_seed1003` |
| S6 | B2 | 19,57 | 21,08 | 20,60 | 60,11 | 55 | 0 | 0 | 9 | `nr_S6_B2_seed1003` |
| S6 | B3 | 19,57 | 21,00 | 22,62 | 51,37 | 25 | 0 | 0 | 0 | `nr_S6_B3_seed1003` |
| S7 | B0 | 4,20 | 5,54 | 5,46 | 10,30 | 15 | 0 | 10 | 0 | `nr_S7_B0_seed1003` |
| S7 | B1 | 4,20 | 5,48 | 5,46 | 13,40 | 15 | 0 | 10 | 0 | `nr_S7_B1_seed1003` |
| S7 | B2 | 4,20 | 5,48 | 5,46 | 13,40 | 15 | 0 | 10 | 0 | `nr_S7_B2_seed1003` |
| S7 | B3 | 4,20 | 5,48 | 5,46 | 13,68 | 5 | 0 | 0 | 0 | `nr_S7_B3_seed1003` |

### 6.4 Semente 1004

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | 3,07 | 3,06 | 3,06 | 17,95 | 2 | 0 | 0 | 0 | `nr_S0_B0_seed1004` |
| S0 | B1 | 3,07 | 3,05 | 3,06 | 18,02 | 2 | 0 | 0 | 0 | `nr_S0_B1_seed1004` |
| S0 | B2 | 3,07 | 3,05 | 3,06 | 18,02 | 2 | 0 | 0 | 0 | `nr_S0_B2_seed1004` |
| S0 | B3 | 3,07 | 3,05 | 3,06 | 18,02 | 2 | 0 | 0 | 0 | `nr_S0_B3_seed1004` |
| S1 | B0 | 366,78 | 118,04 | 109,67 | 17,05 | 10 | 0 | 0 | 9 | `nr_S1_B0_seed1004` |
| S1 | B1 | 366,78 | 278,95 | 275,30 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B1_seed1004` |
| S1 | B2 | 366,78 | 278,95 | 275,30 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B2_seed1004` |
| S1 | B3 | 366,78 | 278,95 | 275,30 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B3_seed1004` |
| S2 | B0 | 197,51 | 197,49 | 197,52 | 6,71 | 5 | 0 | 0 | 0 | `nr_S2_B0_seed1004` |
| S2 | B1 | 197,51 | 197,49 | 197,52 | 6,71 | 5 | 0 | 0 | 0 | `nr_S2_B1_seed1004` |
| S2 | B2 | 197,51 | 197,49 | 197,52 | 6,71 | 5 | 0 | 0 | 0 | `nr_S2_B2_seed1004` |
| S2 | B3 | 197,51 | 197,49 | 197,52 | 6,71 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed1004` |
| S3 | B0 | 2,05 | 12,27 | 12,28 | 4,84 | 10 | 0 | 0 | 9 | `nr_S3_B0_seed1004` |
| S3 | B1 | 2,05 | 12,27 | 12,29 | 4,80 | 5 | 0 | 0 | 0 | `nr_S3_B1_seed1004` |
| S3 | B2 | 2,05 | 12,27 | 12,29 | 4,80 | 5 | 0 | 0 | 0 | `nr_S3_B2_seed1004` |
| S3 | B3 | 2,05 | 12,27 | 12,29 | 4,80 | 5 | 0 | 0 | 0 | `nr_S3_B3_seed1004` |
| S4 | B0 | 32,36 | 24,04 | 24,09 | 151,94 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1004` |
| S4 | B1 | 32,36 | 23,71 | 23,67 | 150,55 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1004` |
| S4 | B2 | 32,36 | 23,71 | 23,67 | 150,55 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1004` |
| S4 | B3 | 32,36 | 23,71 | 23,67 | 150,55 | 10 | 1 | 0 | 0 | `nr_S4_B3_seed1004` |
| S5 | B0 | 8,81 | 9,02 | 9,03 | 32,49 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1004` |
| S5 | B1 | 8,81 | 8,96 | 8,80 | 33,62 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1004` |
| S5 | B2 | 8,81 | 8,96 | 8,80 | 33,62 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1004` |
| S5 | B3 | 8,81 | 8,96 | 8,80 | 33,62 | 8 | 8 | 0 | 0 | `nr_S5_B3_seed1004` |
| S6 | B0 | 20,00 | 17,98 | 18,93 | 103,38 | 80 | 0 | 0 | 57 | `nr_S6_B0_seed1004` |
| S6 | B1 | 20,00 | 22,17 | 21,47 | 63,33 | 55 | 0 | 0 | 9 | `nr_S6_B1_seed1004` |
| S6 | B2 | 20,00 | 22,12 | 21,31 | 67,04 | 55 | 0 | 0 | 9 | `nr_S6_B2_seed1004` |
| S6 | B3 | 20,00 | 22,59 | 23,33 | 49,10 | 25 | 0 | 0 | 0 | `nr_S6_B3_seed1004` |
| S7 | B0 | 4,37 | 5,53 | 5,46 | 10,46 | 15 | 0 | 10 | 0 | `nr_S7_B0_seed1004` |
| S7 | B1 | 4,37 | 5,49 | 5,46 | 12,38 | 15 | 0 | 10 | 0 | `nr_S7_B1_seed1004` |
| S7 | B2 | 4,37 | 5,49 | 5,46 | 12,38 | 15 | 0 | 10 | 0 | `nr_S7_B2_seed1004` |
| S7 | B3 | 4,37 | 5,48 | 5,46 | 12,88 | 5 | 0 | 0 | 0 | `nr_S7_B3_seed1004` |

### 6.5 Semente 1005

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | 3,07 | 2,25 | 2,01 | 33,62 | 2 | 0 | 0 | 0 | `nr_S0_B0_seed1005` |
| S0 | B1 | 3,07 | 2,29 | 2,02 | 33,15 | 2 | 0 | 0 | 0 | `nr_S0_B1_seed1005` |
| S0 | B2 | 3,07 | 2,29 | 2,02 | 33,15 | 2 | 0 | 0 | 0 | `nr_S0_B2_seed1005` |
| S0 | B3 | 3,07 | 2,29 | 2,02 | 33,15 | 2 | 0 | 0 | 0 | `nr_S0_B3_seed1005` |
| S1 | B0 | 366,77 | 118,05 | 109,68 | 17,05 | 10 | 0 | 0 | 9 | `nr_S1_B0_seed1005` |
| S1 | B1 | 366,77 | 278,97 | 275,31 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B1_seed1005` |
| S1 | B2 | 366,77 | 278,97 | 275,31 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B2_seed1005` |
| S1 | B3 | 366,77 | 278,97 | 275,31 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B3_seed1005` |
| S2 | B0 | 196,34 | 197,51 | 197,51 | 7,83 | 6 | 1 | 0 | 0 | `nr_S2_B0_seed1005` |
| S2 | B1 | 196,34 | 197,62 | 197,50 | 8,00 | 6 | 1 | 0 | 0 | `nr_S2_B1_seed1005` |
| S2 | B2 | 196,34 | 197,62 | 197,50 | 8,00 | 6 | 1 | 0 | 0 | `nr_S2_B2_seed1005` |
| S2 | B3 | 196,34 | 179,21 | 178,62 | 33,31 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed1005` |
| S3 | B0 | 1,43 | 12,13 | 12,13 | 12,88 | 10 | 0 | 0 | 9 | `nr_S3_B0_seed1005` |
| S3 | B1 | 1,43 | 12,18 | 12,25 | 11,23 | 5 | 0 | 0 | 0 | `nr_S3_B1_seed1005` |
| S3 | B2 | 1,43 | 12,18 | 12,25 | 11,23 | 5 | 0 | 0 | 0 | `nr_S3_B2_seed1005` |
| S3 | B3 | 1,43 | 12,18 | 12,25 | 11,23 | 5 | 0 | 0 | 0 | `nr_S3_B3_seed1005` |
| S4 | B0 | 32,36 | 23,86 | 24,17 | 153,70 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1005` |
| S4 | B1 | 32,36 | 23,98 | 23,94 | 151,39 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1005` |
| S4 | B2 | 32,36 | 23,98 | 23,94 | 151,39 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1005` |
| S4 | B3 | 32,36 | 23,98 | 23,94 | 151,39 | 10 | 1 | 0 | 0 | `nr_S4_B3_seed1005` |
| S5 | B0 | 8,81 | 9,02 | 8,60 | 30,51 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1005` |
| S5 | B1 | 8,81 | 9,04 | 8,61 | 28,68 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1005` |
| S5 | B2 | 8,81 | 9,04 | 8,61 | 28,68 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1005` |
| S5 | B3 | 8,81 | 9,04 | 8,61 | 28,68 | 8 | 8 | 0 | 0 | `nr_S5_B3_seed1005` |
| S6 | B0 | 20,18 | 18,59 | 21,63 | 91,02 | 80 | 0 | 0 | 57 | `nr_S6_B0_seed1005` |
| S6 | B1 | 20,18 | 18,69 | 20,48 | 69,66 | 55 | 0 | 0 | 9 | `nr_S6_B1_seed1005` |
| S6 | B2 | 20,18 | 19,74 | 22,94 | 64,06 | 55 | 0 | 0 | 9 | `nr_S6_B2_seed1005` |
| S6 | B3 | 20,18 | 20,25 | 22,45 | 48,21 | 25 | 0 | 0 | 0 | `nr_S6_B3_seed1005` |
| S7 | B0 | 4,04 | 5,55 | 5,46 | 10,93 | 15 | 0 | 10 | 0 | `nr_S7_B0_seed1005` |
| S7 | B1 | 4,04 | 5,49 | 5,46 | 13,95 | 15 | 0 | 10 | 0 | `nr_S7_B1_seed1005` |
| S7 | B2 | 4,04 | 5,49 | 5,46 | 13,95 | 15 | 0 | 10 | 0 | `nr_S7_B2_seed1005` |
| S7 | B3 | 4,04 | 5,49 | 5,46 | 14,41 | 5 | 0 | 0 | 0 | `nr_S7_B3_seed1005` |

## 7. Diferenças pareadas B3 − Bx

Para cada semente, valor do B3 menos o do baseline de comparação, na mesma semente. Média ± IC 95 %; "melhor / pior / empate" conta as sementes em que o B3 teve vazão maior (atraso menor), menor (maior) ou igual. "IC exclui 0" marca diferenças distinguíveis de zero com n = 5.

| Cenário | Comparação | Métrica | Diferença média ± IC 95 % | Melhor / pior / empate | IC exclui 0 |
| :-- | :-- | :-- | --: | --: | :-: |
| S0 | B3 − B0 | Vazão no conflito (Mbps) | 0,05 ± 0,13 | 3 / 2 / 0 | não |
| S0 | B3 − B0 | Atraso no conflito (ms) | -5,04 ± 7,54 | 4 / 1 / 0 | não |
| S0 | B3 − B1 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S0 | B3 − B1 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S0 | B3 − B2 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S0 | B3 − B2 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S1 | B3 − B0 | Vazão no conflito (Mbps) | 160,92 ± 0,01 | 5 / 0 / 0 | sim |
| S1 | B3 − B0 | Atraso no conflito (ms) | -7,91 ± 0,0015 | 5 / 0 / 0 | sim |
| S1 | B3 − B1 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S1 | B3 − B1 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S1 | B3 − B2 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S1 | B3 − B2 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S2 | B3 − B0 | Vazão no conflito (Mbps) | -4,25 ± 14,85 | 2 / 2 / 1 | não |
| S2 | B3 − B0 | Atraso no conflito (ms) | 18,74 ± 22,57 | 0 / 4 / 1 | não |
| S2 | B3 − B1 | Vazão no conflito (Mbps) | -4,32 ± 14,95 | 2 / 2 / 1 | não |
| S2 | B3 − B1 | Atraso no conflito (ms) | 18,67 ± 22,53 | 0 / 4 / 1 | não |
| S2 | B3 − B2 | Vazão no conflito (Mbps) | -4,32 ± 14,95 | 2 / 2 / 1 | não |
| S2 | B3 − B2 | Atraso no conflito (ms) | 18,67 ± 22,53 | 0 / 4 / 1 | não |
| S3 | B3 − B0 | Vazão no conflito (Mbps) | -0,34 ± 0,91 | 1 / 4 / 0 | não |
| S3 | B3 − B0 | Atraso no conflito (ms) | 13,73 ± 32,76 | 2 / 3 / 0 | não |
| S3 | B3 − B1 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S3 | B3 − B1 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S3 | B3 − B2 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S3 | B3 − B2 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S4 | B3 − B0 | Vazão no conflito (Mbps) | -0,12 ± 0,23 | 1 / 4 / 0 | não |
| S4 | B3 − B0 | Atraso no conflito (ms) | -2,67 ± 1,16 | 5 / 0 / 0 | sim |
| S4 | B3 − B1 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S4 | B3 − B1 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S4 | B3 − B2 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S4 | B3 − B2 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S5 | B3 − B0 | Vazão no conflito (Mbps) | -0,01 ± 0,05 | 3 / 2 / 0 | não |
| S5 | B3 − B0 | Atraso no conflito (ms) | -0,41 ± 1,65 | 3 / 2 / 0 | não |
| S5 | B3 − B1 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S5 | B3 − B1 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S5 | B3 − B2 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S5 | B3 − B2 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S6 | B3 − B0 | Vazão no conflito (Mbps) | 2,21 ± 1,82 | 5 / 0 / 0 | sim |
| S6 | B3 − B0 | Atraso no conflito (ms) | -43,05 ± 11,03 | 5 / 0 / 0 | sim |
| S6 | B3 − B1 | Vazão no conflito (Mbps) | 0,54 ± 0,92 | 3 / 2 / 0 | não |
| S6 | B3 − B1 | Atraso no conflito (ms) | -11,77 ± 11,30 | 5 / 0 / 0 | sim |
| S6 | B3 − B2 | Vazão no conflito (Mbps) | 0,45 ± 0,68 | 4 / 1 / 0 | não |
| S6 | B3 − B2 | Atraso no conflito (ms) | -16,36 ± 12,51 | 5 / 0 / 0 | sim |
| S7 | B3 − B0 | Vazão no conflito (Mbps) | -0,06 ± 0,01 | 0 / 5 / 0 | sim |
| S7 | B3 − B0 | Atraso no conflito (ms) | 3,01 ± 0,54 | 0 / 5 / 0 | sim |
| S7 | B3 − B1 | Vazão no conflito (Mbps) | -0,0048 ± 0,0012 | 0 / 5 / 0 | sim |
| S7 | B3 − B1 | Atraso no conflito (ms) | 0,31 ± 0,22 | 0 / 5 / 0 | sim |
| S7 | B3 − B2 | Vazão no conflito (Mbps) | -0,0048 ± 0,0012 | 0 / 5 / 0 | sim |
| S7 | B3 − B2 | Atraso no conflito (ms) | 0,31 ± 0,22 | 0 / 5 / 0 | sim |

## 8. Cronogramas de ações idênticos entre baselines

Baselines com o mesmo `action_schedule_sha256` aplicaram exatamente as mesmas ações; com a mesma semente, a simulação é a mesma e os resultados coincidem por construção.

| Cenário | Grupos com cronograma idêntico | Mesmo padrão em todas as sementes |
| :-- | :-- | :-- |
| S0 | B0 · B1 = B2 = B3 | sim |
| S1 | B0 · B1 = B2 = B3 | sim |
| S2 | B0 · B1 = B2 · B3 | sim |
| S3 | B0 · B1 = B2 = B3 | sim |
| S4 | B0 · B1 = B2 · B3 | sim |
| S5 | B0 · B1 = B2 = B3 | sim |
| S6 | B0 · B1 · B2 · B3 | sim |
| S7 | B0 · B1 = B2 · B3 | sim |

## 9. Avaliação das hipóteses

### H0 (S0, controle (sem conflito)): SUPORTADA

Sem conflito, a H-RDL é transparente: B3 não difere do B0 em vazão nem em atraso.

- ATENDIDO: Vazão no conflito (Mbps) B3 − B0 = 0,05 (IC 95 % [-0,08; 0,18], n = 5)
- ATENDIDO: Atraso no conflito (ms) B3 − B0 = -5,04 (IC 95 % [-12,58; 2,49], n = 5)

### H1 (S1, direto (PRB)): SUPORTADA

Em conflito direto de PRB, a H-RDL elimina as oscilações e melhora vazão e atraso em relação ao B0.

- ATENDIDO: Oscilações de B3 == 0 em todas as sementes: [0, 0, 0, 0, 0]
- ATENDIDO: Vazão no conflito (Mbps) B3 − B0 = 160,92 (IC 95 % [160,91; 160,94], n = 5)
- ATENDIDO: Atraso no conflito (ms) B3 − B0 = -7,91 (IC 95 % [-7,91; -7,91], n = 5)

### H2 (S2, indireto (TVS)): INCONCLUSIVA

Em conflito indireto, a H-RDL escolhe um subconjunto de ações que não piora vazão nem atraso em relação a B0, B1 e B2.

- INCONCLUSIVO: Vazão no conflito (Mbps) B3 − B0 = -4,25 (IC 95 % [-19,11; 10,60], n = 5)
- INCONCLUSIVO: Atraso no conflito (ms) B3 − B0 = 18,74 (IC 95 % [-3,83; 41,31], n = 5)
- INCONCLUSIVO: Vazão no conflito (Mbps) B3 − B1 = -4,32 (IC 95 % [-19,27; 10,63], n = 5)
- INCONCLUSIVO: Atraso no conflito (ms) B3 − B1 = 18,67 (IC 95 % [-3,85; 41,20], n = 5)

### H3 (S3, direto (potência)): INCONCLUSIVA

Em conflito direto de potência, a H-RDL elimina as oscilações sem perda de vazão em relação ao B0.

- ATENDIDO: Oscilações de B3 == 0 em todas as sementes: [0, 0, 0, 0, 0]
- INCONCLUSIVO: Vazão no conflito (Mbps) B3 − B0 = -0,34 (IC 95 % [-1,25; 0,57], n = 5)

### H4 (S4, entre células (limitação esperada)): SUPORTADA

A H-RDL não detecta o conflito entre células: o handover acontece e B3 não difere do B1 em vazão nem em atraso.

- ATENDIDO: Handovers de B3 > 0 em todas as sementes: [1, 1, 1, 1, 1]
- ATENDIDO: Vazão no conflito (Mbps) B3 − B1 = 0,00 (IC 95 % [0,00; 0,00], n = 5); diferença zero em todas as sementes
- ATENDIDO: Atraso no conflito (ms) B3 − B1 = 0,00 (IC 95 % [0,00; 0,00], n = 5); diferença zero em todas as sementes

### H5 (S5, temporal entre células (limitação esperada)): SUPORTADA

A H-RDL não detecta o ping-pong entre células: B3 aplica os mesmos handovers que o B0.

- ATENDIDO: Handovers B3 − B0 = 0,00 (IC 95 % [0,00; 0,00], n = 5); diferença zero em todas as sementes
- ATENDIDO: Vazão no conflito (Mbps) B3 − B0 = -0,01 (IC 95 % [-0,05; 0,04], n = 5)

### H6 (S6, tempestade): SUPORTADA

Sob tempestade de conflitos, a H-RDL aplica menos ações, elimina as oscilações e reduz o atraso em relação a B0, B1 e B2.

- ATENDIDO: Ações aplicadas B3 − B1 = -30,00 (IC 95 % [-30,00; -30,00], n = 5)
- ATENDIDO: Oscilações de B3 == 0 em todas as sementes: [0, 0, 0, 0, 0]
- ATENDIDO: Atraso no conflito (ms) B3 − B0 = -43,05 (IC 95 % [-54,08; -32,02], n = 5)
- ATENDIDO: Atraso no conflito (ms) B3 − B1 = -11,77 (IC 95 % [-23,07; -0,47], n = 5)
- ATENDIDO: Atraso no conflito (ms) B3 − B2 = -16,36 (IC 95 % [-28,87; -3,85], n = 5)

### H7 (S7, ação insegura): SUPORTADA

O Safety Guard impede que ações inseguras cheguem à RAN no B3, enquanto B0, B1 e B2 as aplicam.

- ATENDIDO: Ações inseguras de B3 == 0 em todas as sementes: [0, 0, 0, 0, 0]
- ATENDIDO: Ações inseguras de B0 > 0 em todas as sementes: [10, 10, 10, 10, 10]
- ATENDIDO: Ações inseguras de B1 > 0 em todas as sementes: [10, 10, 10, 10, 10]
- ATENDIDO: Ações inseguras de B2 > 0 em todas as sementes: [10, 10, 10, 10, 10]

## 10. Conclusões

**Suportadas:**

- H0 (S0): Sem conflito, a H-RDL é transparente: B3 não difere do B0 em vazão nem em atraso.
- H1 (S1): Em conflito direto de PRB, a H-RDL elimina as oscilações e melhora vazão e atraso em relação ao B0.
- H4 (S4): A H-RDL não detecta o conflito entre células: o handover acontece e B3 não difere do B1 em vazão nem em atraso.
- H5 (S5): A H-RDL não detecta o ping-pong entre células: B3 aplica os mesmos handovers que o B0.
- H6 (S6): Sob tempestade de conflitos, a H-RDL aplica menos ações, elimina as oscilações e reduz o atraso em relação a B0, B1 e B2.
- H7 (S7): O Safety Guard impede que ações inseguras cheguem à RAN no B3, enquanto B0, B1 e B2 as aplicam.

**Inconclusivas:**

- H2 (S2): Em conflito indireto, a H-RDL escolhe um subconjunto de ações que não piora vazão nem atraso em relação a B0, B1 e B2.
  - INCONCLUSIVO: Vazão no conflito (Mbps) B3 − B0 = -4,25 (IC 95 % [-19,11; 10,60], n = 5)
  - INCONCLUSIVO: Atraso no conflito (ms) B3 − B0 = 18,74 (IC 95 % [-3,83; 41,31], n = 5)
  - INCONCLUSIVO: Vazão no conflito (Mbps) B3 − B1 = -4,32 (IC 95 % [-19,27; 10,63], n = 5)
  - INCONCLUSIVO: Atraso no conflito (ms) B3 − B1 = 18,67 (IC 95 % [-3,85; 41,20], n = 5)
- H3 (S3): Em conflito direto de potência, a H-RDL elimina as oscilações sem perda de vazão em relação ao B0.
  - INCONCLUSIVO: Vazão no conflito (Mbps) B3 − B0 = -0,34 (IC 95 % [-1,25; 0,57], n = 5)

**Diferenças desfavoráveis ao B3 com IC 95 % excluindo zero** (fora ou além das hipóteses; seção 7):

- S7, B3 − B0, Vazão no conflito (Mbps): -0,06 ± 0,01 (B3 pior em 5/5 sementes)
- S7, B3 − B0, Atraso no conflito (ms): 3,01 ± 0,54 (B3 pior em 5/5 sementes)
- S7, B3 − B1, Vazão no conflito (Mbps): -0,0048 ± 0,0012 (B3 pior em 5/5 sementes)
- S7, B3 − B1, Atraso no conflito (ms): 0,31 ± 0,22 (B3 pior em 5/5 sementes)
- S7, B3 − B2, Vazão no conflito (Mbps): -0,0048 ± 0,0012 (B3 pior em 5/5 sementes)
- S7, B3 − B2, Atraso no conflito (ms): 0,31 ± 0,22 (B3 pior em 5/5 sementes)

Nos cenários S0, S1, S3, S5, B1, B2 e B3 aplicaram o mesmo cronograma em todas as sementes. Nesses cenários a campanha mede o efeito de coordenar versus não coordenar, não uma vantagem específica da H-RDL sobre FIFO ou prioridade estática.

## 11. Ameaças à validade e proveniência

- Malha aberta: a decisão não reage ao estado da RAN; o closed loop E2 (gates G1–G4) não é avaliado aqui.
- As propostas são estilizadas (valores e períodos fixos do catálogo), idênticas entre baselines e sementes.
- n = 5 sementes por célula: ICs largos em métricas com variância entre sementes; sobreposição de IC não é teste de hipótese, e as regras da seção 2 usam a diferença pareada.
- Contagens (ações, handovers, inseguras, oscilações) dependem só do cronograma e são constantes entre sementes.
- S2, S4 e S5 rodam com `--disableSrs=true` (contorno de falha do 5G-LENA v5.1 em handover), igual para todos os baselines.
- Fonte do cenário diferente dentro de um conjunto pareado: S7 semente 1001 (B0/B3 `d40477f2`; B1/B2 `881dd752`). A mudança entre as versões (opção `--disableSrs`, desligada por padrão, e escalonamento de handover) não afeta cenários sem `HANDOVER` no cronograma.

Execuções com falha preservadas em `experiments/runs_failed/` (não entram na análise):

| Execução | Status | Motivo (stderr) |
| :-- | :-- | :-- |
| `nr_S5_B1_seed1001__20261108T061606Z` | FAILED | simulador: Not allowed state for starting SRS reception. |
| `nr_S5_B1_seed1001__20261108T062045Z` | FAILED | simulador: Not allowed state for starting SRS reception. |
| `nr_S5_B3_seed1001__20261108T062443Z` | FAILED | exit_code 120; stderr vazio; última saída: `[RDL-KPI] t=2.0s vazao=8.72 Mbps atraso=57.26 ms` (execução interrompida) |

## Apêndice A. Comando ns-3 de cada execução

Campo `command` do `execution_manifest.json`, executado no WSL. Os caminhos de `--actionSchedule` apontam para `raw/action_schedule.csv` da própria execução.

```bash
# nr_S0_B0_seed1001  (SUCCESS, 2026-11-08T03:24:40Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S0_B0_seed1001/raw/action_schedule.csv --simTime=20'
# nr_S0_B0_seed1002  (SUCCESS, 2026-11-08T07:07:01Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S0_B0_seed1002/raw/action_schedule.csv --simTime=20'
# nr_S0_B0_seed1003  (SUCCESS, 2026-11-08T08:16:23Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S0_B0_seed1003/raw/action_schedule.csv --simTime=20'
# nr_S0_B0_seed1004  (SUCCESS, 2026-11-08T09:02:40Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S0_B0_seed1004/raw/action_schedule.csv --simTime=20'
# nr_S0_B0_seed1005  (SUCCESS, 2026-11-08T09:48:56Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S0_B0_seed1005/raw/action_schedule.csv --simTime=20'
# nr_S0_B1_seed1001  (SUCCESS, 2026-11-08T05:50:06Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S0_B1_seed1001/raw/action_schedule.csv --simTime=20'
# nr_S0_B1_seed1002  (SUCCESS, 2026-11-08T07:07:56Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S0_B1_seed1002/raw/action_schedule.csv --simTime=20'
# nr_S0_B1_seed1003  (SUCCESS, 2026-11-08T08:16:23Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S0_B1_seed1003/raw/action_schedule.csv --simTime=20'
# nr_S0_B1_seed1004  (SUCCESS, 2026-11-08T09:03:00Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S0_B1_seed1004/raw/action_schedule.csv --simTime=20'
# nr_S0_B1_seed1005  (SUCCESS, 2026-11-08T09:49:29Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S0_B1_seed1005/raw/action_schedule.csv --simTime=20'
# nr_S0_B2_seed1001  (SUCCESS, 2026-11-08T05:50:06Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S0_B2_seed1001/raw/action_schedule.csv --simTime=20'
# nr_S0_B2_seed1002  (SUCCESS, 2026-11-08T07:08:24Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S0_B2_seed1002/raw/action_schedule.csv --simTime=20'
# nr_S0_B2_seed1003  (SUCCESS, 2026-11-08T08:18:20Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S0_B2_seed1003/raw/action_schedule.csv --simTime=20'
# nr_S0_B2_seed1004  (SUCCESS, 2026-11-08T09:03:39Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S0_B2_seed1004/raw/action_schedule.csv --simTime=20'
# nr_S0_B2_seed1005  (SUCCESS, 2026-11-08T09:49:54Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S0_B2_seed1005/raw/action_schedule.csv --simTime=20'
# nr_S0_B3_seed1001  (SUCCESS, 2026-11-08T03:24:48Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S0_B3_seed1001/raw/action_schedule.csv --simTime=20'
# nr_S0_B3_seed1002  (SUCCESS, 2026-11-08T07:08:53Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S0_B3_seed1002/raw/action_schedule.csv --simTime=20'
# nr_S0_B3_seed1003  (SUCCESS, 2026-11-08T08:18:24Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S0_B3_seed1003/raw/action_schedule.csv --simTime=20'
# nr_S0_B3_seed1004  (SUCCESS, 2026-11-08T09:04:00Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S0_B3_seed1004/raw/action_schedule.csv --simTime=20'
# nr_S0_B3_seed1005  (SUCCESS, 2026-11-08T09:50:27Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_no_conflict --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S0_B3_seed1005/raw/action_schedule.csv --simTime=20'
# nr_S1_B0_seed1001  (SUCCESS, 2026-11-08T02:47:45Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S1_B0_seed1001/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B0_seed1002  (SUCCESS, 2026-11-08T07:09:20Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S1_B0_seed1002/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B0_seed1003  (SUCCESS, 2026-11-08T08:19:41Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S1_B0_seed1003/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B0_seed1004  (SUCCESS, 2026-11-08T09:04:39Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S1_B0_seed1004/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B0_seed1005  (SUCCESS, 2026-11-08T09:50:52Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S1_B0_seed1005/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B1_seed1001  (SUCCESS, 2026-11-08T05:51:13Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S1_B1_seed1001/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B1_seed1002  (SUCCESS, 2026-11-08T07:09:49Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S1_B1_seed1002/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B1_seed1003  (SUCCESS, 2026-11-08T08:19:42Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S1_B1_seed1003/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B1_seed1004  (SUCCESS, 2026-11-08T09:05:06Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S1_B1_seed1004/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B1_seed1005  (SUCCESS, 2026-11-08T09:51:32Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S1_B1_seed1005/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B2_seed1001  (SUCCESS, 2026-11-08T05:51:13Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S1_B2_seed1001/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B2_seed1002  (SUCCESS, 2026-11-08T07:13:49Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S1_B2_seed1002/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B2_seed1003  (SUCCESS, 2026-11-08T08:25:03Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S1_B2_seed1003/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B2_seed1004  (SUCCESS, 2026-11-08T09:09:30Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S1_B2_seed1004/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B2_seed1005  (SUCCESS, 2026-11-08T09:55:58Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S1_B2_seed1005/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B3_seed1001  (SUCCESS, 2026-11-08T02:53:35Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S1_B3_seed1001/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B3_seed1002  (SUCCESS, 2026-11-08T07:14:26Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S1_B3_seed1002/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B3_seed1003  (SUCCESS, 2026-11-08T08:25:24Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S1_B3_seed1003/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B3_seed1004  (SUCCESS, 2026-11-08T09:10:05Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S1_B3_seed1004/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S1_B3_seed1005  (SUCCESS, 2026-11-08T09:56:42Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_direct_prb_conflict --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S1_B3_seed1005/raw/action_schedule.csv --simTime=20 --udpIntervalUs=200'
# nr_S2_B0_seed1001  (SUCCESS, 2026-11-08T06:35:57Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S2_B0_seed1001/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B0_seed1002  (SUCCESS, 2026-11-08T07:18:17Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S2_B0_seed1002/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B0_seed1003  (SUCCESS, 2026-11-08T08:29:58Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S2_B0_seed1003/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B0_seed1004  (SUCCESS, 2026-11-08T09:14:32Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S2_B0_seed1004/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B0_seed1005  (SUCCESS, 2026-11-08T10:01:03Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S2_B0_seed1005/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B1_seed1001  (SUCCESS, 2026-11-08T06:35:57Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S2_B1_seed1001/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B1_seed1002  (SUCCESS, 2026-11-08T07:19:00Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S2_B1_seed1002/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B1_seed1003  (SUCCESS, 2026-11-08T08:30:17Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S2_B1_seed1003/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B1_seed1004  (SUCCESS, 2026-11-08T09:15:05Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S2_B1_seed1004/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B1_seed1005  (SUCCESS, 2026-11-08T10:01:46Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S2_B1_seed1005/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B2_seed1001  (SUCCESS, 2026-11-08T06:45:13Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S2_B2_seed1001/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B2_seed1002  (SUCCESS, 2026-11-08T07:23:27Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S2_B2_seed1002/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B2_seed1003  (SUCCESS, 2026-11-08T08:35:25Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S2_B2_seed1003/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B2_seed1004  (SUCCESS, 2026-11-08T09:19:58Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S2_B2_seed1004/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B2_seed1005  (SUCCESS, 2026-11-08T10:06:30Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S2_B2_seed1005/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3_seed1001  (SUCCESS, 2026-11-08T06:45:19Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S2_B3_seed1001/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3_seed1002  (SUCCESS, 2026-11-08T07:24:14Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S2_B3_seed1002/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3_seed1003  (SUCCESS, 2026-11-08T08:35:44Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S2_B3_seed1003/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3_seed1004  (SUCCESS, 2026-11-08T09:20:38Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S2_B3_seed1004/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3_seed1005  (SUCCESS, 2026-11-08T10:07:33Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S2_B3_seed1005/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S3_B0_seed1001  (SUCCESS, 2026-11-08T06:00:35Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S3_B0_seed1001/raw/action_schedule.csv --simTime=20'
# nr_S3_B0_seed1002  (SUCCESS, 2026-11-08T07:28:48Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S3_B0_seed1002/raw/action_schedule.csv --simTime=20'
# nr_S3_B0_seed1003  (SUCCESS, 2026-11-08T08:40:52Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S3_B0_seed1003/raw/action_schedule.csv --simTime=20'
# nr_S3_B0_seed1004  (SUCCESS, 2026-11-08T09:25:44Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S3_B0_seed1004/raw/action_schedule.csv --simTime=20'
# nr_S3_B0_seed1005  (SUCCESS, 2026-11-08T10:11:56Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S3_B0_seed1005/raw/action_schedule.csv --simTime=20'
# nr_S3_B1_seed1001  (SUCCESS, 2026-11-08T06:00:36Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S3_B1_seed1001/raw/action_schedule.csv --simTime=20'
# nr_S3_B1_seed1002  (SUCCESS, 2026-11-08T07:29:28Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S3_B1_seed1002/raw/action_schedule.csv --simTime=20'
# nr_S3_B1_seed1003  (SUCCESS, 2026-11-08T08:41:26Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S3_B1_seed1003/raw/action_schedule.csv --simTime=20'
# nr_S3_B1_seed1004  (SUCCESS, 2026-11-08T09:26:22Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S3_B1_seed1004/raw/action_schedule.csv --simTime=20'
# nr_S3_B1_seed1005  (SUCCESS, 2026-11-08T10:12:49Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S3_B1_seed1005/raw/action_schedule.csv --simTime=20'
# nr_S3_B2_seed1001  (SUCCESS, 2026-11-08T06:01:26Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S3_B2_seed1001/raw/action_schedule.csv --simTime=20'
# nr_S3_B2_seed1002  (SUCCESS, 2026-11-08T07:29:42Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S3_B2_seed1002/raw/action_schedule.csv --simTime=20'
# nr_S3_B2_seed1003  (SUCCESS, 2026-11-08T08:41:37Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S3_B2_seed1003/raw/action_schedule.csv --simTime=20'
# nr_S3_B2_seed1004  (SUCCESS, 2026-11-08T09:26:29Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S3_B2_seed1004/raw/action_schedule.csv --simTime=20'
# nr_S3_B2_seed1005  (SUCCESS, 2026-11-08T10:13:19Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S3_B2_seed1005/raw/action_schedule.csv --simTime=20'
# nr_S3_B3_seed1001  (SUCCESS, 2026-11-08T06:01:32Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S3_B3_seed1001/raw/action_schedule.csv --simTime=20'
# nr_S3_B3_seed1002  (SUCCESS, 2026-11-08T07:30:11Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S3_B3_seed1002/raw/action_schedule.csv --simTime=20'
# nr_S3_B3_seed1003  (SUCCESS, 2026-11-08T08:42:07Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S3_B3_seed1003/raw/action_schedule.csv --simTime=20'
# nr_S3_B3_seed1004  (SUCCESS, 2026-11-08T09:27:23Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S3_B3_seed1004/raw/action_schedule.csv --simTime=20'
# nr_S3_B3_seed1005  (SUCCESS, 2026-11-08T10:13:44Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_energy_vs_qos --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S3_B3_seed1005/raw/action_schedule.csv --simTime=20'
# nr_S4_B0_seed1001  (SUCCESS, 2026-11-08T06:52:25Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S4_B0_seed1001/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B0_seed1002  (SUCCESS, 2026-11-08T07:30:22Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S4_B0_seed1002/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B0_seed1003  (SUCCESS, 2026-11-08T08:42:17Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S4_B0_seed1003/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B0_seed1004  (SUCCESS, 2026-11-08T09:27:22Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S4_B0_seed1004/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B0_seed1005  (SUCCESS, 2026-11-08T10:14:09Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S4_B0_seed1005/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B1_seed1001  (SUCCESS, 2026-11-08T06:52:28Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S4_B1_seed1001/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B1_seed1002  (SUCCESS, 2026-11-08T07:30:52Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S4_B1_seed1002/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B1_seed1003  (SUCCESS, 2026-11-08T08:42:49Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S4_B1_seed1003/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B1_seed1004  (SUCCESS, 2026-11-08T09:28:29Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S4_B1_seed1004/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B1_seed1005  (SUCCESS, 2026-11-08T10:14:32Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S4_B1_seed1005/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B2_seed1001  (SUCCESS, 2026-11-08T06:55:53Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S4_B2_seed1001/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B2_seed1002  (SUCCESS, 2026-11-08T07:33:48Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S4_B2_seed1002/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B2_seed1003  (SUCCESS, 2026-11-08T08:46:06Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S4_B2_seed1003/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B2_seed1004  (SUCCESS, 2026-11-08T09:31:30Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S4_B2_seed1004/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B2_seed1005  (SUCCESS, 2026-11-08T10:17:42Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S4_B2_seed1005/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B3_seed1001  (SUCCESS, 2026-11-08T06:56:03Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S4_B3_seed1001/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B3_seed1002  (SUCCESS, 2026-11-08T07:34:18Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S4_B3_seed1002/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B3_seed1003  (SUCCESS, 2026-11-08T08:46:39Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S4_B3_seed1003/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B3_seed1004  (SUCCESS, 2026-11-08T09:32:44Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S4_B3_seed1004/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B3_seed1005  (SUCCESS, 2026-11-08T10:18:14Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S4_B3_seed1005/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B0_seed1001  (SUCCESS, 2026-11-08T06:59:18Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S5_B0_seed1001/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B0_seed1002  (SUCCESS, 2026-11-08T07:37:15Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S5_B0_seed1002/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B0_seed1003  (SUCCESS, 2026-11-08T08:49:42Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S5_B0_seed1003/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B0_seed1004  (SUCCESS, 2026-11-08T09:35:57Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S5_B0_seed1004/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B0_seed1005  (SUCCESS, 2026-11-08T10:21:31Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S5_B0_seed1005/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B1_seed1001  (SUCCESS, 2026-11-08T06:21:48Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S5_B1_seed1001/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B1_seed1002  (SUCCESS, 2026-11-08T07:37:41Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S5_B1_seed1002/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B1_seed1003  (SUCCESS, 2026-11-08T08:50:09Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S5_B1_seed1003/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B1_seed1004  (SUCCESS, 2026-11-08T09:37:00Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S5_B1_seed1004/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B1_seed1005  (SUCCESS, 2026-11-08T10:22:01Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S5_B1_seed1005/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B2_seed1001  (SUCCESS, 2026-11-08T07:58:29Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S5_B2_seed1001/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B2_seed1002  (SUCCESS, 2026-11-08T07:39:09Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S5_B2_seed1002/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B2_seed1003  (SUCCESS, 2026-11-08T08:51:19Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S5_B2_seed1003/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B2_seed1004  (SUCCESS, 2026-11-08T09:38:11Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S5_B2_seed1004/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B2_seed1005  (SUCCESS, 2026-11-08T10:23:32Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S5_B2_seed1005/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B3_seed1001  (SUCCESS, 2026-11-08T06:59:29Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S5_B3_seed1001/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B3_seed1002  (SUCCESS, 2026-11-08T07:39:35Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S5_B3_seed1002/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B3_seed1003  (SUCCESS, 2026-11-08T08:51:59Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S5_B3_seed1003/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B3_seed1004  (SUCCESS, 2026-11-08T09:39:15Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S5_B3_seed1004/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B3_seed1005  (SUCCESS, 2026-11-08T10:24:01Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S5_B3_seed1005/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S6_B0_seed1001  (SUCCESS, 2026-11-08T08:04:24Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S6_B0_seed1001/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B0_seed1002  (SUCCESS, 2026-11-08T08:04:24Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S6_B0_seed1002/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B0_seed1003  (SUCCESS, 2026-11-08T08:53:26Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S6_B0_seed1003/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B0_seed1004  (SUCCESS, 2026-11-08T09:40:20Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S6_B0_seed1004/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B0_seed1005  (SUCCESS, 2026-11-08T10:25:37Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S6_B0_seed1005/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B1_seed1001  (SUCCESS, 2026-11-08T07:01:09Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S6_B1_seed1001/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B1_seed1002  (SUCCESS, 2026-11-08T08:07:39Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S6_B1_seed1002/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B1_seed1003  (SUCCESS, 2026-11-08T08:53:57Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S6_B1_seed1003/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B1_seed1004  (SUCCESS, 2026-11-08T09:41:23Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S6_B1_seed1004/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B1_seed1005  (SUCCESS, 2026-11-08T10:26:11Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S6_B1_seed1005/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B2_seed1001  (SUCCESS, 2026-11-08T07:01:25Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S6_B2_seed1001/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B2_seed1002  (SUCCESS, 2026-11-08T08:07:58Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S6_B2_seed1002/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B2_seed1003  (SUCCESS, 2026-11-08T08:57:08Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S6_B2_seed1003/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B2_seed1004  (SUCCESS, 2026-11-08T09:43:25Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S6_B2_seed1004/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B2_seed1005  (SUCCESS, 2026-11-08T10:29:21Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S6_B2_seed1005/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B3_seed1001  (SUCCESS, 2026-11-08T07:05:03Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S6_B3_seed1001/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B3_seed1002  (SUCCESS, 2026-11-08T08:11:10Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S6_B3_seed1002/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B3_seed1003  (SUCCESS, 2026-11-08T08:57:39Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S6_B3_seed1003/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B3_seed1004  (SUCCESS, 2026-11-08T09:44:44Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S6_B3_seed1004/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S6_B3_seed1005  (SUCCESS, 2026-11-08T10:29:48Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_conflict_storm --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S6_B3_seed1005/raw/action_schedule.csv --simTime=20 --loadLevel=0'
# nr_S7_B0_seed1001  (SUCCESS, 2026-11-08T03:00:37Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S7_B0_seed1001/raw/action_schedule.csv --simTime=25'
# nr_S7_B0_seed1002  (SUCCESS, 2026-11-08T08:11:25Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S7_B0_seed1002/raw/action_schedule.csv --simTime=25'
# nr_S7_B0_seed1003  (SUCCESS, 2026-11-08T09:01:02Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S7_B0_seed1003/raw/action_schedule.csv --simTime=25'
# nr_S7_B0_seed1004  (SUCCESS, 2026-11-08T09:46:58Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S7_B0_seed1004/raw/action_schedule.csv --simTime=25'
# nr_S7_B0_seed1005  (SUCCESS, 2026-11-08T10:32:56Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S7_B0_seed1005/raw/action_schedule.csv --simTime=25'
# nr_S7_B1_seed1001  (SUCCESS, 2026-11-08T07:05:21Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S7_B1_seed1001/raw/action_schedule.csv --simTime=25'
# nr_S7_B1_seed1002  (SUCCESS, 2026-11-08T08:12:11Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S7_B1_seed1002/raw/action_schedule.csv --simTime=25'
# nr_S7_B1_seed1003  (SUCCESS, 2026-11-08T09:01:20Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S7_B1_seed1003/raw/action_schedule.csv --simTime=25'
# nr_S7_B1_seed1004  (SUCCESS, 2026-11-08T09:47:49Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S7_B1_seed1004/raw/action_schedule.csv --simTime=25'
# nr_S7_B1_seed1005  (SUCCESS, 2026-11-08T10:33:16Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S7_B1_seed1005/raw/action_schedule.csv --simTime=25'
# nr_S7_B2_seed1001  (SUCCESS, 2026-11-08T07:06:12Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S7_B2_seed1001/raw/action_schedule.csv --simTime=25'
# nr_S7_B2_seed1002  (SUCCESS, 2026-11-08T08:12:58Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S7_B2_seed1002/raw/action_schedule.csv --simTime=25'
# nr_S7_B2_seed1003  (SUCCESS, 2026-11-08T09:01:50Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S7_B2_seed1003/raw/action_schedule.csv --simTime=25'
# nr_S7_B2_seed1004  (SUCCESS, 2026-11-08T09:48:07Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S7_B2_seed1004/raw/action_schedule.csv --simTime=25'
# nr_S7_B2_seed1005  (SUCCESS, 2026-11-08T10:33:53Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S7_B2_seed1005/raw/action_schedule.csv --simTime=25'
# nr_S7_B3_seed1001  (SUCCESS, 2026-11-08T03:02:17Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1001 --actionSchedule=<repo>/experiments/runs/nr_S7_B3_seed1001/raw/action_schedule.csv --simTime=25'
# nr_S7_B3_seed1002  (SUCCESS, 2026-11-08T08:13:44Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1002 --actionSchedule=<repo>/experiments/runs/nr_S7_B3_seed1002/raw/action_schedule.csv --simTime=25'
# nr_S7_B3_seed1003  (SUCCESS, 2026-11-08T09:02:10Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1003 --actionSchedule=<repo>/experiments/runs/nr_S7_B3_seed1003/raw/action_schedule.csv --simTime=25'
# nr_S7_B3_seed1004  (SUCCESS, 2026-11-08T09:48:40Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1004 --actionSchedule=<repo>/experiments/runs/nr_S7_B3_seed1004/raw/action_schedule.csv --simTime=25'
# nr_S7_B3_seed1005  (SUCCESS, 2026-11-08T10:34:18Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_fault_injection --seed=1005 --actionSchedule=<repo>/experiments/runs/nr_S7_B3_seed1005/raw/action_schedule.csv --simTime=25'
```

