# Relatório da campanha de conflitos multi-xApp (ns-3.48 + 5G-LENA v5.1)

Gerado em 2026-11-13T05:19:28Z por [`generate_campaign_report.py`](../../scripts/certification/generate_campaign_report.py) a partir de [`conflict_analysis_20261113T051808Z.json`](conflict_analysis_20261113T051808Z.json) (análise gerada em 2026-11-13T05:18:08Z), dos manifestos das execuções e do catálogo de cenários. Nenhum valor foi digitado à mão.

## 1. Resumo

- **Desenho:** 17 cenários (S0–S15) × 5 baselines (B0, B1, B2, B3, B3A) × 22 sementes (1001–12005) = 412 execuções.
- **Status:** 412 `SUCCESS`; 0 execução(ões) ignorada(s) pela análise.
- **Avaliação em malha aberta:** as propostas das xApps vêm do catálogo, cada baseline decide e as ações decididas são aplicadas na RAN simulada. Não há E2 nem realimentação de KPM.
- **Hipóteses:** inconclusiva: H2, H3; refutada: H4, H5; suportada: H0, H1, H6, H7 (seção 9).
- **Certificação:** G0 CERTIFIED, G1 CERTIFIED, G2 LOCAL_ONLY, G3 CERTIFIED, G4 CERTIFIED, G5 CERTIFIED, G6 NOT_CERTIFIED ([`certificate_20261113T051926Z.json`](../certification/certificate_20261113T051926Z.json)).

## 2. Pergunta e hipóteses

**Pergunta.** Quando várias xApps propõem controles conflitantes, a decisão da H-RDL (B3) leva a um desempenho de rede melhor ou mais seguro que não coordenar (B0), FIFO por janela e alvo (B1) ou prioridade estática por janela e alvo (B2)?

As hipóteses abaixo foram derivadas do tratamento esperado de cada tipo de conflito na [taxonomia](../../docs/03_cenarios_e_conflitos.md), escrita antes desta campanha. Não houve pré-registro formal. H4 e H5 descrevem limitações conhecidas: "suportada" significa que a limitação se confirmou.

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
- `=0`: atendido se o IC contém zero. Isso indica ausência de diferença detectável com n = 22, não equivalência.
- Hipótese **suportada** se todos os critérios forem atendidos, **refutada** se algum não for, **inconclusiva** nos demais casos.

## 3. Desenho, cenários e ambiente

| Cenário | Programa ns-3 | Janela de conflito | Argumentos | Conflito |
| :-- | :-- | :-- | :-- | :-- |
| S0 | `scenario_rdl_no_conflict` | 10,0–15,0 s | `--simTime=20` | Ações independentes em gNBs distintos: não há conflito; serve de controle (pass-through). |
| S1 | `scenario_rdl_direct_prb_conflict` | 10,0–15,0 s | `--simTime=20` `--udpIntervalUs=200` | Conflito direto de PRB na mesma célula: xApp-QoS pede 75%, xApp-Energy pede 30%. |
| G1 | `scenario_rdl_multicell` | 15,0–25,0 s | `--simTime=30` `--channel=UMi` `--bandwidth=20e6` `--gnbs=0,0,10;150,0,10` `--ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5` `--packetSize=1250` | GreenRAN campus (App1-Vigilância × App2-Monitoramento), em escala reduzida: 6 câmeras HD a 5 Mb/s numa portadora de 20 MHz (as câmeras 4K a 25 Mb/s da proposta custariam mais de 45 min de parede por execução) e 30 sensores de baixa taxa; o RANSlicer reserva 80 % de PRB na RU 0 e o EnergySaver pede 30 % (economia de PRBs ativos) — conflito direto na fatia de câmeras. |
| S2 | `scenario_rdl_tvs_conflict` | 10,0–15,0 s | `--simTime=20` `--disableSrs=true` | Conflito indireto TVS: xSlice reserva PRB na célula macro enquanto o Traffic Steering move os UEs dela para a small cell. |
| G2 | `scenario_rdl_multicell` | 15,0–25,0 s | `--simTime=30` `--channel=UMi` `--gnbs=0,0,10;150,0,10` `--ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5` | GreenRAN noite (baixa demanda, UEs na borda entre duas RUs): o EnergySaver da RU 0 e o da RU 1 querem desligar as duas células vizinhas, e o Traffic Steering move os UEs da RU 0 para a RU 1 — sleep de vizinhas e handover para célula desligada. |
| S3 | `scenario_rdl_energy_vs_qos` | 10,0–15,0 s | `--simTime=20` | Conflito direto de potência: Energy Saving reduz para 10 dBm, xSlice exige 40 dBm na mesma célula. |
| S4 | `scenario_rdl_ts_vs_energy` | 15,0–25,0 s | `--simTime=30` `--disableSrs=true` | Conflito entre células: Traffic Steering move UEs da gNB0 congestionada para a gNB1 enquanto o Energy Saving coloca a gNB1 em baixa potência. |
| S5 | `scenario_rdl_temporal_pingpong` | 18,0–26,0 s | `--simTime=30` `--disableSrs=true` | Ping-pong temporal: Traffic Steering move UEs para a gNB1 e o Load Balancer os devolve à gNB0, alternadamente. |
| S6 | `scenario_rdl_conflict_storm` | 10,0–15,0 s | `--simTime=20` `--loadLevel=0` | Tempestade de conflitos: seis xApps disputam PRB e potência nas quatro gNBs a cada 0,5 s. |
| S7 | `scenario_rdl_fault_injection` | 10,0–15,0 s | `--simTime=25` | Injeção de falhas: uma xApp maliciosa pede potência fora do limite físico (60 dBm) e cota de PRB inválida (150%), concorrendo com ações legítimas. |
| S9 | `scenario_rdl_multicell` | 15,0–25,0 s | `--simTime=30` `--channel=NTN-Rural` `--centralFreq=2e9` `--bandwidth=20e6` `--txPowerDbm=77` `--packetSize=200` `--gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000` `--ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5` | NTN direct-to-cell (GreenRAN: sensores rurais via satélite LEO a 600 km, canal 3GPP NTN-Rural, 2 GHz, feixes sobre Belém em posições geocêntricas): Traffic Steering move os sensores do feixe 0 para o feixe 1 enquanto o Energy Saving desliga o feixe 1 (CELL_STATE=0) — conflito entre células. |
| S10 | `scenario_rdl_multicell` | 15,0–25,0 s | `--simTime=30` `--channel=UMa` `--gnbs=0,0,25;300,0,100` `--ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5` | gNB em UAV a 100 m com bateria limitada: Energy Saving reduz a potência do UAV a 5 dBm para poupar bateria enquanto o Traffic Steering descarrega a macro congestionada no UAV — conflito entre células. |
| S11 | `scenario_rdl_multicell` | 15,0–25,0 s | `--simTime=30` `--channel=RMa` `--gnbs=0,0,35;600,0,35;1200,0,35` `--ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5` | Rodovia (V2X por Uu, 120 km/h): veículos andam da gNB0 para a gNB1; Traffic Steering antecipa o handover 0→1 e o Load Balancer devolve 1→0 a cada 2 s — ping-pong entre células. Sem sidelink (o NR V2X do 5G-LENA é outro ramo). |
| S12 | `scenario_rdl_multicell` | 12,0–20,0 s | `--simTime=25` `--bandwidth=10e6` `--channel=InH-OfficeMixed` `--gnbs=0,0,3` `--ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0` `--packetSize=128` | Fábrica (IIoT, canal InH): sensores críticos a 2 ms e câmeras a 1 ms disputam PRBs; xSlice reserva 80 % e o Energy Saving pede 30 % na mesma célula — conflito direto. Mede-se o atraso dos sensores; TSN não é modelado. |
| S13 | `scenario_rdl_multicell` | 15,0–25,0 s | `--simTime=30` `--channel=RMa` `--gnbs=0,0,30;800,0,30;400,700,30` `--ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5` | Desastre rural: a gNB0 falha (CELL_STATE=0 pelo injetor de falhas, prioridade 100); o Traffic Steering move os UEs dela para a gNB1 enquanto o Energy Saving quer desligar a gNB1 por baixa carga — conflito entre células com prioridade de emergência. |
| S14 | `scenario_rdl_multicell` | 12,0–20,0 s | `--simTime=25` `--bandwidth=50e6` `--channel=UMi` `--gnbs=0,0,10` `--ueGroups=30,0,0,10,100,5,0,0,1.5` | ISAC como disputa de recursos: a xApp de sensoriamento pede teto de 40 % de PRB para comunicação (reservando o resto ao radar) e a xSlice pede 80 % — conflito direto. O sensoriamento em si não é modelado no 5G-LENA; só a perda de recursos de comunicação. |
| S15 | `scenario_rdl_multicell` | 15,0–25,0 s | `--simTime=30` `--channel=NTN-Rural` `--centralFreq=2e9` `--bandwidth=20e6` `--txPowerDbm=77` `--packetSize=200` `--gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000` `--ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5` | xApp maliciosa em NTN: pede handover para um feixe inexistente (célula 7) e potência fora dos limites (90 dBm), junto com propostas legítimas de Traffic Steering e Energy Saving. O Safety Guard e a topologia devem barrar as maliciosas sem vetar as legítimas. |

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
| commit do repositório | `083c8e6`; `08a6747`; `35eded2`; `48fab8e`; `5ae0232`; `8fbbf98`; `c18760b`; `cddf572`; `d0cbd8f`; `dedae21`; `dfe8b1f`; `ee72885` |

Execuções entre 2026-11-08T02:47:45Z e 2026-11-13T05:14:47Z (UTC).

## 4. Comandos de execução (terminal WSL/Ubuntu)

Todos os comandos abaixo rodam direto no terminal do Ubuntu (WSL), sem passar pelo Windows. O ns-3.48 + 5G-LENA v5.1 compilado fica em `~/ns3-oran-workspace/ns-3-oran` (variável `NS3_DIR`); a saída `[RDL-ACT]`/`[RDL-KPI]` de cada execução aparece ao vivo. Detalhes do ambiente no [guia operacional](../../docs/04_instalacao_e_operacao.md).

**Preparação (uma vez).** O driver usa a `RDLxApp` real no B3 e precisa das dependências do projeto. Sem `sudo` (o Ubuntu 24.04 não traz `python3-venv`), o venv é criado sem pip e as dependências são instaladas com o pip do sistema:

```bash
python3 -m venv --without-pip ~/.venvs/xapp-rdl
python3 -m pip --python ~/.venvs/xapp-rdl/bin/python install "pydantic>=2.0.0" "structlog>=23.1.0" "prometheus-client>=0.19.0" "pycrate>=0.7.0" "requests>=2.31.0" "numpy>=1.24.0" "fastapi>=0.100.0" "uvicorn>=0.20.0" "PyYAML>=6.0.1"
```

**Em cada terminal novo:**

```bash
cd <raiz-do-repositório>
source ~/.venvs/xapp-rdl/bin/activate
```

Campanha completa (retomável: execuções com `hashes.sha256` são puladas; interrompidas são removidas e refeitas):

```bash
python scripts/certification/run_conflict_campaign.py \
    --scenarios S0 S1 G1 S2 G2 S3 S4 S5 S6 S7 S9 S10 S11 S12 S13 S14 S15 --baselines B0 B1 B2 B3 B3A --seeds 1001 1002 1003 1004 1005 1006 1007 1008 1009 1010 9101 9102 11001 11002 11003 11004 11005 12001 12002 12003 12004 12005 --jobs 2
```

Uma semente por vez (cada semente concluída forma um conjunto pareado completo):

```bash
for s in 1001 1002 1003 1004 1005 1006 1007 1008 1009 1010 9101 9102 11001 11002 11003 11004 11005 12001 12002 12003 12004 12005; do
  python scripts/certification/run_conflict_campaign.py --scenarios S0 S1 G1 S2 G2 S3 S4 S5 S6 S7 S9 S10 S11 S12 S13 S14 S15 --baselines B0 B1 B2 B3 B3A --seeds $s --jobs 2 --skip-analysis
done
```

Refazer execuções com falha (as originais vão para `experiments/runs_failed/<run_id>__<UTC>`):

```bash
python scripts/certification/run_conflict_campaign.py \
    --scenarios S0 S1 G1 S2 G2 S3 S4 S5 S6 S7 S9 S10 S11 S12 S13 S14 S15 --baselines B0 B1 B2 B3 B3A --seeds 1001 1002 1003 1004 1005 1006 1007 1008 1009 1010 9101 9102 11001 11002 11003 11004 11005 12001 12002 12003 12004 12005 --jobs 2 --retry-failed
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
| G1 | B0 | 6 | 30,30 ± 0,01 | 23,30 ± 0,02 | 22,39 ± 0,02 | 22,98 ± 0,15 | 20,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 19,00 ± 0,00 |
| G1 | B1 | 5 | 30,29 ± 0,01 | 30,30 ± 0,0011 | 30,33 ± 0,00 | 5,64 ± 0,10 | 10,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| G1 | B2 | 5 | 30,29 ± 0,01 | 30,30 ± 0,0011 | 30,33 ± 0,00 | 5,64 ± 0,10 | 10,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| G1 | B3 | 6 | 30,30 ± 0,01 | 30,30 ± 0,0009 | 30,33 ± 0,00 | 5,62 ± 0,10 | 9,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| G2 | B0 | 6 | 1,73 ± 0,06 | 0,20 ± 0,09 | 0,18 ± 0,08 | 25,95 ± 20,08 | 21,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| G2 | B1 | 5 | 1,75 ± 0,05 | 0,29 ± 0,11 | 0,23 ± 0,14 | 24,13 ± 18,12 | 21,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| G2 | B2 | 5 | 1,75 ± 0,05 | 0,29 ± 0,11 | 0,23 ± 0,14 | 24,13 ± 18,12 | 21,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| G2 | B3 | 6 | 1,73 ± 0,06 | 1,79 ± 0,0034 | 1,81 ± 0,00 | 4,86 ± 0,15 | 10,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S0 | B0 | 5 | 3,07 ± 0,00 | 2,63 ± 0,47 | 2,28 ± 0,59 | 34,50 ± 12,26 | 2,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S0 | B1 | 5 | 3,07 ± 0,00 | 2,68 ± 0,49 | 2,38 ± 0,68 | 29,45 ± 10,93 | 2,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S0 | B2 | 5 | 3,07 ± 0,00 | 2,68 ± 0,49 | 2,38 ± 0,68 | 29,45 ± 10,93 | 2,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S0 | B3 | 5 | 3,07 ± 0,00 | 2,68 ± 0,49 | 2,38 ± 0,68 | 29,45 ± 10,93 | 2,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S1 | B0 | 5 | 366,77 ± 0,02 | 118,04 ± 0,02 | 109,68 ± 0,0044 | 17,05 ± 0,0017 | 10,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 9,00 ± 0,00 |
| S1 | B1 | 5 | 366,77 ± 0,02 | 278,97 ± 0,02 | 275,30 ± 0,01 | 9,14 ± 0,0004 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S1 | B2 | 5 | 366,77 ± 0,02 | 278,97 ± 0,02 | 275,30 ± 0,01 | 9,14 ± 0,0004 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S1 | B3 | 5 | 366,77 ± 0,02 | 278,97 ± 0,02 | 275,30 ± 0,01 | 9,14 ± 0,0004 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S10 | B0 | 6 | 34,82 ± 0,00 | 31,23 ± 0,15 | 34,79 ± 0,0010 | 9,10 ± 0,69 | 11,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S10 | B1 | 5 | 34,82 ± 0,00 | 31,26 ± 0,08 | 34,79 ± 0,0012 | 9,06 ± 0,45 | 11,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S10 | B2 | 5 | 34,82 ± 0,00 | 31,26 ± 0,08 | 34,79 ± 0,0012 | 9,06 ± 0,45 | 11,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S10 | B3 | 6 | 34,82 ± 0,00 | 31,86 ± 0,58 | 32,40 ± 0,70 | 33,55 ± 2,22 | 1,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S11 | B0 | 6 | 20,48 ± 0,0021 | 19,56 ± 0,16 | 20,24 ± 0,57 | 22,27 ± 1,73 | 8,00 ± 0,00 | 8,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S11 | B1 | 5 | 20,48 ± 0,0023 | 19,42 ± 0,65 | 20,50 ± 0,08 | 24,08 ± 8,40 | 8,00 ± 0,00 | 8,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S11 | B2 | 5 | 20,48 ± 0,0023 | 19,42 ± 0,65 | 20,50 ± 0,08 | 24,08 ± 8,40 | 8,00 ± 0,00 | 8,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S11 | B3 | 6 | 20,48 ± 0,0021 | 20,19 ± 0,19 | 20,24 ± 0,42 | 9,94 ± 2,07 | 2,00 ± 0,00 | 2,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S12 | B0 | 7 | 20,37 ± 0,04 | 10,99 ± 3,87 | 10,37 ± 4,12 | 178,40 ± 70,55 | 16,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 15,00 ± 0,00 |
| S12 | B1 | 5 | 20,35 ± 0,00 | 18,25 ± 0,00 | 18,20 ± 0,00 | 40,92 ± 0,00 | 8,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S12 | B2 | 5 | 20,35 ± 0,00 | 18,25 ± 0,00 | 18,20 ± 0,00 | 40,92 ± 0,00 | 8,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S12 | B3 | 7 | 20,37 ± 0,04 | 18,57 ± 0,78 | 18,53 ± 0,80 | 35,85 ± 12,41 | 7,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S13 | B0 | 6 | 30,72 ± 0,0014 | 23,56 ± 0,60 | 29,72 ± 0,76 | 10,49 ± 4,70 | 12,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S13 | B1 | 5 | 30,72 ± 0,0006 | 23,50 ± 0,62 | 29,61 ± 0,81 | 10,90 ± 5,63 | 12,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S13 | B2 | 5 | 30,72 ± 0,0006 | 23,50 ± 0,62 | 29,61 ± 0,81 | 10,90 ± 5,63 | 12,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S13 | B3 | 11 | 30,72 ± 0,0007 | 25,73 ± 0,15 | 30,58 ± 0,17 | 7,17 ± 1,11 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S13 | B3A | 5 | 30,72 ± 0,0009 | 27,84 ± 0,42 | 30,44 ± 0,49 | 7,24 ± 3,44 | 2,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S14 | B0 | 2 | 49,15 ± 0,00 | 49,15 ± 0,00 | 49,15 ± 0,00 | 5,46 ± 0,77 | 16,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 15,00 ± 0,00 |
| S14 | B3 | 2 | 49,15 ± 0,00 | 49,15 ± 0,00 | 49,15 ± 0,00 | 5,39 ± 0,01 | 7,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S15 | B0 | 6 | 0,58 ± 0,01 | 0,64 ± 0,0006 | 0,64 ± 0,00 | 7,62 ± 0,66 | 21,00 ± 0,00 | 1,00 ± 0,00 | 10,00 ± 0,00 | 0,00 ± 0,00 |
| S15 | B1 | 5 | 0,58 ± 0,01 | 0,64 ± 0,0010 | 0,64 ± 6,2e-17 | 12,40 ± 1,52 | 20,00 ± 0,00 | 0,00 ± 0,00 | 10,00 ± 0,00 | 0,00 ± 0,00 |
| S15 | B2 | 5 | 0,58 ± 0,01 | 0,64 ± 0,0010 | 0,64 ± 6,2e-17 | 12,40 ± 1,52 | 20,00 ± 0,00 | 0,00 ± 0,00 | 10,00 ± 0,00 | 0,00 ± 0,00 |
| S15 | B3 | 11 | 0,57 ± 0,01 | 0,60 ± 0,02 | 0,57 ± 0,04 | 18,75 ± 1,65 | 1,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S15 | B3A | 5 | 0,57 ± 0,02 | 0,63 ± 0,02 | 0,62 ± 0,05 | 7,31 ± 0,36 | 10,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S2 | B0 | 5 | 194,94 ± 4,78 | 197,49 ± 0,06 | 197,52 ± 0,01 | 7,42 ± 0,84 | 5,80 ± 0,56 | 0,80 ± 0,56 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S2 | B1 | 5 | 194,94 ± 4,78 | 197,56 ± 0,09 | 197,51 ± 0,01 | 7,48 ± 0,90 | 5,80 ± 0,56 | 0,80 ± 0,56 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S2 | B2 | 5 | 194,94 ± 4,78 | 197,56 ± 0,09 | 197,51 ± 0,01 | 7,48 ± 0,90 | 5,80 ± 0,56 | 0,80 ± 0,56 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S2 | B3 | 10 | 192,71 ± 5,51 | 190,01 ± 7,50 | 194,22 ± 16,33 | 24,34 ± 10,44 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S2 | B3A | 5 | 190,48 ± 12,80 | 197,66 ± 0,80 | 197,51 ± 0,01 | 8,05 ± 0,94 | 6,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S3 | B0 | 5 | 1,93 ± 0,34 | 12,20 ± 0,09 | 12,21 ± 0,09 | 14,13 ± 12,72 | 10,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 9,00 ± 0,00 |
| S3 | B1 | 5 | 1,93 ± 0,34 | 11,86 ± 0,96 | 11,94 ± 0,85 | 27,86 ± 44,55 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S3 | B2 | 5 | 1,93 ± 0,34 | 11,86 ± 0,96 | 11,94 ± 0,85 | 27,86 ± 44,55 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S3 | B3 | 5 | 1,93 ± 0,34 | 11,86 ± 0,96 | 11,94 ± 0,85 | 27,86 ± 44,55 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S4 | B0 | 10 | 32,36 ± 0,00 | 23,87 ± 0,16 | 24,09 ± 0,20 | 153,24 ± 0,59 | 11,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S4 | B1 | 10 | 32,36 ± 0,00 | 23,80 ± 0,14 | 23,81 ± 0,19 | 150,44 ± 0,47 | 11,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S4 | B2 | 10 | 32,36 ± 0,00 | 23,80 ± 0,14 | 23,81 ± 0,19 | 150,44 ± 0,47 | 11,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S4 | B3 | 10 | 32,36 ± 0,00 | 22,82 ± 0,71 | 23,03 ± 0,56 | 150,33 ± 0,40 | 5,50 ± 3,39 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S5 | B0 | 10 | 8,60 ± 0,81 | 8,75 ± 0,46 | 8,53 ± 0,56 | 42,32 ± 18,90 | 8,00 ± 0,00 | 8,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S5 | B1 | 10 | 8,60 ± 0,81 | 8,75 ± 0,45 | 8,50 ± 0,56 | 42,21 ± 18,91 | 8,00 ± 0,00 | 8,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S5 | B2 | 10 | 8,60 ± 0,81 | 8,75 ± 0,45 | 8,50 ± 0,56 | 42,21 ± 18,91 | 8,00 ± 0,00 | 8,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S5 | B3 | 10 | 8,60 ± 0,81 | 9,35 ± 0,27 | 9,34 ± 0,38 | 21,62 ± 8,28 | 4,70 ± 2,50 | 4,70 ± 2,50 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S6 | B0 | 5 | 19,84 ± 0,37 | 18,97 ± 1,74 | 20,47 ± 3,23 | 94,38 ± 12,82 | 80,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 57,00 ± 0,00 |
| S6 | B1 | 5 | 19,84 ± 0,37 | 20,65 ± 2,14 | 22,22 ± 2,33 | 63,10 ± 14,90 | 55,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 9,00 ± 0,00 |
| S6 | B2 | 5 | 19,84 ± 0,37 | 20,74 ± 1,87 | 22,24 ± 2,02 | 67,69 ± 18,49 | 55,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 9,00 ± 0,00 |
| S6 | B3 | 5 | 19,84 ± 0,37 | 21,19 ± 1,41 | 23,03 ± 0,59 | 51,33 ± 6,67 | 25,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S7 | B0 | 5 | 4,17 ± 0,17 | 5,54 ± 0,01 | 5,46 ± 0,0010 | 10,54 ± 0,35 | 15,00 ± 0,00 | 0,00 ± 0,00 | 10,00 ± 0,00 | 0,00 ± 0,00 |
| S7 | B1 | 5 | 4,17 ± 0,17 | 5,49 ± 0,01 | 5,46 ± 0,0013 | 13,24 ± 0,77 | 15,00 ± 0,00 | 0,00 ± 0,00 | 10,00 ± 0,00 | 0,00 ± 0,00 |
| S7 | B2 | 5 | 4,17 ± 0,17 | 5,49 ± 0,01 | 5,46 ± 0,0013 | 13,24 ± 0,77 | 15,00 ± 0,00 | 0,00 ± 0,00 | 10,00 ± 0,00 | 0,00 ± 0,00 |
| S7 | B3 | 5 | 4,17 ± 0,17 | 5,48 ± 0,01 | 5,46 ± 0,0005 | 13,55 ± 0,73 | 5,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S9 | B0 | 6 | 0,58 ± 0,01 | 0,52 ± 0,01 | 0,64 ± 0,00 | 6,08 ± 0,08 | 11,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S9 | B1 | 5 | 0,58 ± 0,01 | 0,52 ± 0,01 | 0,64 ± 0,00 | 6,31 ± 0,26 | 11,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S9 | B2 | 5 | 0,58 ± 0,01 | 0,52 ± 0,01 | 0,64 ± 0,00 | 6,31 ± 0,26 | 11,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |
| S9 | B3 | 6 | 0,58 ± 0,01 | 0,61 ± 0,02 | 0,58 ± 0,06 | 17,71 ± 3,12 | 1,00 ± 0,00 | 1,00 ± 0,00 | 0,00 ± 0,00 | 0,00 ± 0,00 |

## 6. Resultados por semente

Valores de cada execução, como calculados pela análise a partir de `raw/rdl_kpi_timeseries.csv` e `raw/rdl_actuation_log.csv` da própria execução.

### 6.1 Semente 1001

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | 3,07 | 2,98 | 2,40 | 37,27 | 2 | 0 | 0 | 0 | `nr_S0_B0_seed1001` |
| S0 | B1 | 3,07 | 3,06 | 2,90 | 22,30 | 2 | 0 | 0 | 0 | `nr_S0_B1_seed1001` |
| S0 | B2 | 3,07 | 3,06 | 2,90 | 22,30 | 2 | 0 | 0 | 0 | `nr_S0_B2_seed1001` |
| S0 | B3 | 3,07 | 3,06 | 2,90 | 22,30 | 2 | 0 | 0 | 0 | `nr_S0_B3_seed1001` |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | 366,75 | 118,06 | 109,68 | 17,05 | 10 | 0 | 0 | 9 | `nr_S1_B0_seed1001` |
| S1 | B1 | 366,75 | 278,98 | 275,30 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B1_seed1001` |
| S1 | B2 | 366,75 | 278,98 | 275,30 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B2_seed1001` |
| S1 | B3 | 366,75 | 278,98 | 275,30 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B3_seed1001` |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | 197,51 | 197,49 | 197,52 | 6,71 | 6 | 1 | 0 | 0 | `nr_S2_B0_seed1001` |
| S2 | B1 | 197,51 | 197,49 | 197,52 | 6,71 | 6 | 1 | 0 | 0 | `nr_S2_B1_seed1001` |
| S2 | B2 | 197,51 | 197,49 | 197,52 | 6,71 | 6 | 1 | 0 | 0 | `nr_S2_B2_seed1001` |
| S2 | B3 | 197,51 | 197,49 | 197,52 | 6,72 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed1001` |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | 2,05 | 12,27 | 12,29 | 5,66 | 10 | 0 | 0 | 9 | `nr_S3_B0_seed1001` |
| S3 | B1 | 2,05 | 12,26 | 12,29 | 7,16 | 5 | 0 | 0 | 0 | `nr_S3_B1_seed1001` |
| S3 | B2 | 2,05 | 12,26 | 12,29 | 7,16 | 5 | 0 | 0 | 0 | `nr_S3_B2_seed1001` |
| S3 | B3 | 2,05 | 12,26 | 12,29 | 7,16 | 5 | 0 | 0 | 0 | `nr_S3_B3_seed1001` |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | 32,36 | 23,73 | 23,78 | 153,15 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1001` |
| S4 | B1 | 32,36 | 23,45 | 23,77 | 149,31 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1001` |
| S4 | B2 | 32,36 | 23,45 | 23,77 | 149,31 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1001` |
| S4 | B3 | 32,36 | 23,45 | 23,77 | 149,31 | 10 | 1 | 0 | 0 | `nr_S4_B3_seed1001` |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | 8,81 | 8,93 | 9,03 | 36,33 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1001` |
| S5 | B1 | 8,81 | 8,96 | 9,04 | 34,70 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1001` |
| S5 | B2 | 8,81 | 8,96 | 9,04 | 34,70 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1001` |
| S5 | B3 | 8,81 | 8,96 | 9,04 | 34,70 | 8 | 8 | 0 | 0 | `nr_S5_B3_seed1001` |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | 19,98 | 17,45 | 16,66 | 106,09 | 80 | 0 | 0 | 57 | `nr_S6_B0_seed1001` |
| S6 | B1 | 19,98 | 18,99 | 24,64 | 79,33 | 55 | 0 | 0 | 9 | `nr_S6_B1_seed1001` |
| S6 | B2 | 19,98 | 18,68 | 24,72 | 92,94 | 55 | 0 | 0 | 9 | `nr_S6_B2_seed1001` |
| S6 | B3 | 19,98 | 19,99 | 23,53 | 60,57 | 25 | 0 | 0 | 0 | `nr_S6_B3_seed1001` |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | 4,04 | 5,54 | 5,46 | 10,27 | 15 | 0 | 10 | 0 | `nr_S7_B0_seed1001` |
| S7 | B1 | 4,04 | 5,48 | 5,46 | 12,86 | 15 | 0 | 10 | 0 | `nr_S7_B1_seed1001` |
| S7 | B2 | 4,04 | 5,48 | 5,46 | 12,86 | 15 | 0 | 10 | 0 | `nr_S7_B2_seed1001` |
| S7 | B3 | 4,04 | 5,47 | 5,46 | 13,13 | 5 | 0 | 0 | 0 | `nr_S7_B3_seed1001` |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.2 Semente 1002

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | 3,07 | 2,31 | 1,98 | 42,24 | 2 | 0 | 0 | 0 | `nr_S0_B0_seed1002` |
| S0 | B1 | 3,07 | 2,24 | 1,97 | 38,27 | 2 | 0 | 0 | 0 | `nr_S0_B1_seed1002` |
| S0 | B2 | 3,07 | 2,24 | 1,97 | 38,27 | 2 | 0 | 0 | 0 | `nr_S0_B2_seed1002` |
| S0 | B3 | 3,07 | 2,24 | 1,97 | 38,27 | 2 | 0 | 0 | 0 | `nr_S0_B3_seed1002` |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | 366,76 | 118,03 | 109,68 | 17,05 | 10 | 0 | 0 | 9 | `nr_S1_B0_seed1002` |
| S1 | B1 | 366,76 | 278,98 | 275,29 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B1_seed1002` |
| S1 | B2 | 366,76 | 278,98 | 275,29 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B2_seed1002` |
| S1 | B3 | 366,76 | 278,98 | 275,29 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B3_seed1002` |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | 188,29 | 197,55 | 197,52 | 8,20 | 6 | 1 | 0 | 0 | `nr_S2_B0_seed1002` |
| S2 | B1 | 188,29 | 197,56 | 197,51 | 8,21 | 6 | 1 | 0 | 0 | `nr_S2_B1_seed1002` |
| S2 | B2 | 188,29 | 197,56 | 197,51 | 8,21 | 6 | 1 | 0 | 0 | `nr_S2_B2_seed1002` |
| S2 | B3 | 188,29 | 208,79 | 254,55 | 49,45 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed1002` |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | 2,05 | 12,20 | 12,21 | 17,32 | 10 | 0 | 0 | 9 | `nr_S3_B0_seed1002` |
| S3 | B1 | 2,05 | 12,09 | 12,17 | 25,71 | 5 | 0 | 0 | 0 | `nr_S3_B1_seed1002` |
| S3 | B2 | 2,05 | 12,09 | 12,17 | 25,71 | 5 | 0 | 0 | 0 | `nr_S3_B2_seed1002` |
| S3 | B3 | 2,05 | 12,09 | 12,17 | 25,71 | 5 | 0 | 0 | 0 | `nr_S3_B3_seed1002` |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | 32,36 | 24,02 | 24,35 | 152,84 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1002` |
| S4 | B1 | 32,36 | 23,90 | 24,04 | 149,59 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1002` |
| S4 | B2 | 32,36 | 23,90 | 24,04 | 149,59 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1002` |
| S4 | B3 | 32,36 | 23,90 | 24,04 | 149,59 | 10 | 1 | 0 | 0 | `nr_S4_B3_seed1002` |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | 8,81 | 8,97 | 8,81 | 33,89 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1002` |
| S5 | B1 | 8,81 | 8,94 | 8,82 | 34,59 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1002` |
| S5 | B2 | 8,81 | 8,94 | 8,82 | 34,59 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1002` |
| S5 | B3 | 8,81 | 8,94 | 8,82 | 34,59 | 8 | 8 | 0 | 0 | `nr_S5_B3_seed1002` |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | 19,48 | 20,73 | 22,50 | 90,55 | 80 | 0 | 0 | 57 | `nr_S6_B0_seed1002` |
| S6 | B1 | 19,48 | 22,30 | 23,76 | 50,03 | 55 | 0 | 0 | 9 | `nr_S6_B1_seed1002` |
| S6 | B2 | 19,48 | 22,06 | 21,62 | 54,32 | 55 | 0 | 0 | 9 | `nr_S6_B2_seed1002` |
| S6 | B3 | 19,48 | 22,10 | 23,25 | 47,40 | 25 | 0 | 0 | 0 | `nr_S6_B3_seed1002` |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | 4,19 | 5,54 | 5,46 | 10,73 | 15 | 0 | 10 | 0 | `nr_S7_B0_seed1002` |
| S7 | B1 | 4,19 | 5,49 | 5,46 | 13,59 | 15 | 0 | 10 | 0 | `nr_S7_B1_seed1002` |
| S7 | B2 | 4,19 | 5,49 | 5,46 | 13,59 | 15 | 0 | 10 | 0 | `nr_S7_B2_seed1002` |
| S7 | B3 | 4,19 | 5,48 | 5,46 | 13,64 | 5 | 0 | 0 | 0 | `nr_S7_B3_seed1002` |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.3 Semente 1003

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | 3,07 | 2,53 | 1,94 | 41,40 | 2 | 0 | 0 | 0 | `nr_S0_B0_seed1003` |
| S0 | B1 | 3,07 | 2,74 | 1,96 | 35,53 | 2 | 0 | 0 | 0 | `nr_S0_B1_seed1003` |
| S0 | B2 | 3,07 | 2,74 | 1,96 | 35,53 | 2 | 0 | 0 | 0 | `nr_S0_B2_seed1003` |
| S0 | B3 | 3,07 | 2,74 | 1,96 | 35,53 | 2 | 0 | 0 | 0 | `nr_S0_B3_seed1003` |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | 366,79 | 118,04 | 109,68 | 17,05 | 10 | 0 | 0 | 9 | `nr_S1_B0_seed1003` |
| S1 | B1 | 366,79 | 278,95 | 275,29 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B1_seed1003` |
| S1 | B2 | 366,79 | 278,95 | 275,29 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B2_seed1003` |
| S1 | B3 | 366,79 | 278,95 | 275,29 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B3_seed1003` |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | 195,04 | 197,42 | 197,51 | 7,63 | 6 | 1 | 0 | 0 | `nr_S2_B0_seed1003` |
| S2 | B1 | 195,04 | 197,65 | 197,50 | 7,79 | 6 | 1 | 0 | 0 | `nr_S2_B1_seed1003` |
| S2 | B2 | 195,04 | 197,65 | 197,50 | 7,79 | 6 | 1 | 0 | 0 | `nr_S2_B2_seed1003` |
| S2 | B3 | 195,04 | 183,22 | 182,85 | 34,61 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed1003` |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | 2,05 | 12,14 | 12,14 | 29,94 | 10 | 0 | 0 | 9 | `nr_S3_B0_seed1003` |
| S3 | B1 | 2,05 | 10,48 | 10,73 | 90,38 | 5 | 0 | 0 | 0 | `nr_S3_B1_seed1003` |
| S3 | B2 | 2,05 | 10,48 | 10,73 | 90,38 | 5 | 0 | 0 | 0 | `nr_S3_B2_seed1003` |
| S3 | B3 | 2,05 | 10,48 | 10,73 | 90,38 | 5 | 0 | 0 | 0 | `nr_S3_B3_seed1003` |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | 32,36 | 23,71 | 24,07 | 152,87 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1003` |
| S4 | B1 | 32,36 | 23,68 | 23,35 | 150,30 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1003` |
| S4 | B2 | 32,36 | 23,68 | 23,35 | 150,30 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1003` |
| S4 | B3 | 32,36 | 23,68 | 23,35 | 150,30 | 10 | 1 | 0 | 0 | `nr_S4_B3_seed1003` |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | 9,83 | 9,13 | 9,01 | 22,22 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1003` |
| S5 | B1 | 9,83 | 9,15 | 9,01 | 21,80 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1003` |
| S5 | B2 | 9,83 | 9,15 | 9,01 | 21,80 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1003` |
| S5 | B3 | 9,83 | 9,15 | 9,01 | 21,80 | 8 | 8 | 0 | 0 | `nr_S5_B3_seed1003` |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | 19,57 | 20,12 | 22,64 | 80,87 | 80 | 0 | 0 | 57 | `nr_S6_B0_seed1003` |
| S6 | B1 | 19,57 | 21,08 | 20,73 | 53,17 | 55 | 0 | 0 | 9 | `nr_S6_B1_seed1003` |
| S6 | B2 | 19,57 | 21,08 | 20,60 | 60,11 | 55 | 0 | 0 | 9 | `nr_S6_B2_seed1003` |
| S6 | B3 | 19,57 | 21,00 | 22,62 | 51,37 | 25 | 0 | 0 | 0 | `nr_S6_B3_seed1003` |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | 4,20 | 5,54 | 5,46 | 10,30 | 15 | 0 | 10 | 0 | `nr_S7_B0_seed1003` |
| S7 | B1 | 4,20 | 5,48 | 5,46 | 13,40 | 15 | 0 | 10 | 0 | `nr_S7_B1_seed1003` |
| S7 | B2 | 4,20 | 5,48 | 5,46 | 13,40 | 15 | 0 | 10 | 0 | `nr_S7_B2_seed1003` |
| S7 | B3 | 4,20 | 5,48 | 5,46 | 13,68 | 5 | 0 | 0 | 0 | `nr_S7_B3_seed1003` |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.4 Semente 1004

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | 3,07 | 3,06 | 3,06 | 17,95 | 2 | 0 | 0 | 0 | `nr_S0_B0_seed1004` |
| S0 | B1 | 3,07 | 3,05 | 3,06 | 18,02 | 2 | 0 | 0 | 0 | `nr_S0_B1_seed1004` |
| S0 | B2 | 3,07 | 3,05 | 3,06 | 18,02 | 2 | 0 | 0 | 0 | `nr_S0_B2_seed1004` |
| S0 | B3 | 3,07 | 3,05 | 3,06 | 18,02 | 2 | 0 | 0 | 0 | `nr_S0_B3_seed1004` |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | 366,78 | 118,04 | 109,67 | 17,05 | 10 | 0 | 0 | 9 | `nr_S1_B0_seed1004` |
| S1 | B1 | 366,78 | 278,95 | 275,30 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B1_seed1004` |
| S1 | B2 | 366,78 | 278,95 | 275,30 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B2_seed1004` |
| S1 | B3 | 366,78 | 278,95 | 275,30 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B3_seed1004` |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | 197,51 | 197,49 | 197,52 | 6,71 | 5 | 0 | 0 | 0 | `nr_S2_B0_seed1004` |
| S2 | B1 | 197,51 | 197,49 | 197,52 | 6,71 | 5 | 0 | 0 | 0 | `nr_S2_B1_seed1004` |
| S2 | B2 | 197,51 | 197,49 | 197,52 | 6,71 | 5 | 0 | 0 | 0 | `nr_S2_B2_seed1004` |
| S2 | B3 | 197,51 | 197,49 | 197,52 | 6,71 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed1004` |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | 2,05 | 12,27 | 12,28 | 4,84 | 10 | 0 | 0 | 9 | `nr_S3_B0_seed1004` |
| S3 | B1 | 2,05 | 12,27 | 12,29 | 4,80 | 5 | 0 | 0 | 0 | `nr_S3_B1_seed1004` |
| S3 | B2 | 2,05 | 12,27 | 12,29 | 4,80 | 5 | 0 | 0 | 0 | `nr_S3_B2_seed1004` |
| S3 | B3 | 2,05 | 12,27 | 12,29 | 4,80 | 5 | 0 | 0 | 0 | `nr_S3_B3_seed1004` |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | 32,36 | 24,04 | 24,09 | 151,94 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1004` |
| S4 | B1 | 32,36 | 23,71 | 23,67 | 150,55 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1004` |
| S4 | B2 | 32,36 | 23,71 | 23,67 | 150,55 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1004` |
| S4 | B3 | 32,36 | 23,71 | 23,67 | 150,55 | 10 | 1 | 0 | 0 | `nr_S4_B3_seed1004` |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | 8,81 | 9,02 | 9,03 | 32,49 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1004` |
| S5 | B1 | 8,81 | 8,96 | 8,80 | 33,62 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1004` |
| S5 | B2 | 8,81 | 8,96 | 8,80 | 33,62 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1004` |
| S5 | B3 | 8,81 | 8,96 | 8,80 | 33,62 | 8 | 8 | 0 | 0 | `nr_S5_B3_seed1004` |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | 20,00 | 17,98 | 18,93 | 103,38 | 80 | 0 | 0 | 57 | `nr_S6_B0_seed1004` |
| S6 | B1 | 20,00 | 22,17 | 21,47 | 63,33 | 55 | 0 | 0 | 9 | `nr_S6_B1_seed1004` |
| S6 | B2 | 20,00 | 22,12 | 21,31 | 67,04 | 55 | 0 | 0 | 9 | `nr_S6_B2_seed1004` |
| S6 | B3 | 20,00 | 22,59 | 23,33 | 49,10 | 25 | 0 | 0 | 0 | `nr_S6_B3_seed1004` |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | 4,37 | 5,53 | 5,46 | 10,46 | 15 | 0 | 10 | 0 | `nr_S7_B0_seed1004` |
| S7 | B1 | 4,37 | 5,49 | 5,46 | 12,38 | 15 | 0 | 10 | 0 | `nr_S7_B1_seed1004` |
| S7 | B2 | 4,37 | 5,49 | 5,46 | 12,38 | 15 | 0 | 10 | 0 | `nr_S7_B2_seed1004` |
| S7 | B3 | 4,37 | 5,48 | 5,46 | 12,88 | 5 | 0 | 0 | 0 | `nr_S7_B3_seed1004` |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.5 Semente 1005

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | 3,07 | 2,25 | 2,01 | 33,62 | 2 | 0 | 0 | 0 | `nr_S0_B0_seed1005` |
| S0 | B1 | 3,07 | 2,29 | 2,02 | 33,15 | 2 | 0 | 0 | 0 | `nr_S0_B1_seed1005` |
| S0 | B2 | 3,07 | 2,29 | 2,02 | 33,15 | 2 | 0 | 0 | 0 | `nr_S0_B2_seed1005` |
| S0 | B3 | 3,07 | 2,29 | 2,02 | 33,15 | 2 | 0 | 0 | 0 | `nr_S0_B3_seed1005` |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | 366,77 | 118,05 | 109,68 | 17,05 | 10 | 0 | 0 | 9 | `nr_S1_B0_seed1005` |
| S1 | B1 | 366,77 | 278,97 | 275,31 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B1_seed1005` |
| S1 | B2 | 366,77 | 278,97 | 275,31 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B2_seed1005` |
| S1 | B3 | 366,77 | 278,97 | 275,31 | 9,14 | 5 | 0 | 0 | 0 | `nr_S1_B3_seed1005` |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | 196,34 | 197,51 | 197,51 | 7,83 | 6 | 1 | 0 | 0 | `nr_S2_B0_seed1005` |
| S2 | B1 | 196,34 | 197,62 | 197,50 | 8,00 | 6 | 1 | 0 | 0 | `nr_S2_B1_seed1005` |
| S2 | B2 | 196,34 | 197,62 | 197,50 | 8,00 | 6 | 1 | 0 | 0 | `nr_S2_B2_seed1005` |
| S2 | B3 | 196,34 | 179,21 | 178,62 | 33,31 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed1005` |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | 1,43 | 12,13 | 12,13 | 12,88 | 10 | 0 | 0 | 9 | `nr_S3_B0_seed1005` |
| S3 | B1 | 1,43 | 12,18 | 12,25 | 11,23 | 5 | 0 | 0 | 0 | `nr_S3_B1_seed1005` |
| S3 | B2 | 1,43 | 12,18 | 12,25 | 11,23 | 5 | 0 | 0 | 0 | `nr_S3_B2_seed1005` |
| S3 | B3 | 1,43 | 12,18 | 12,25 | 11,23 | 5 | 0 | 0 | 0 | `nr_S3_B3_seed1005` |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | 32,36 | 23,86 | 24,17 | 153,70 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1005` |
| S4 | B1 | 32,36 | 23,98 | 23,94 | 151,39 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1005` |
| S4 | B2 | 32,36 | 23,98 | 23,94 | 151,39 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1005` |
| S4 | B3 | 32,36 | 23,98 | 23,94 | 151,39 | 10 | 1 | 0 | 0 | `nr_S4_B3_seed1005` |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | 8,81 | 9,02 | 8,60 | 30,51 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1005` |
| S5 | B1 | 8,81 | 9,04 | 8,61 | 28,68 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1005` |
| S5 | B2 | 8,81 | 9,04 | 8,61 | 28,68 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1005` |
| S5 | B3 | 8,81 | 9,04 | 8,61 | 28,68 | 8 | 8 | 0 | 0 | `nr_S5_B3_seed1005` |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | 20,18 | 18,59 | 21,63 | 91,02 | 80 | 0 | 0 | 57 | `nr_S6_B0_seed1005` |
| S6 | B1 | 20,18 | 18,69 | 20,48 | 69,66 | 55 | 0 | 0 | 9 | `nr_S6_B1_seed1005` |
| S6 | B2 | 20,18 | 19,74 | 22,94 | 64,06 | 55 | 0 | 0 | 9 | `nr_S6_B2_seed1005` |
| S6 | B3 | 20,18 | 20,25 | 22,45 | 48,21 | 25 | 0 | 0 | 0 | `nr_S6_B3_seed1005` |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | 4,04 | 5,55 | 5,46 | 10,93 | 15 | 0 | 10 | 0 | `nr_S7_B0_seed1005` |
| S7 | B1 | 4,04 | 5,49 | 5,46 | 13,95 | 15 | 0 | 10 | 0 | `nr_S7_B1_seed1005` |
| S7 | B2 | 4,04 | 5,49 | 5,46 | 13,95 | 15 | 0 | 10 | 0 | `nr_S7_B2_seed1005` |
| S7 | B3 | 4,04 | 5,49 | 5,46 | 14,41 | 5 | 0 | 0 | 0 | `nr_S7_B3_seed1005` |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.6 Semente 1006

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | 32,36 | 24,30 | 24,12 | 153,71 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1006` |
| S4 | B1 | 32,36 | 23,61 | 23,43 | 150,88 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1006` |
| S4 | B2 | 32,36 | 23,61 | 23,43 | 150,88 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1006` |
| S4 | B3 | 32,36 | 21,89 | 22,30 | 150,44 | 1 | 1 | 0 | 0 | `nr_S4_B3_seed1006` |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | 7,07 | 7,43 | 7,05 | 97,07 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1006` |
| S5 | B1 | 7,07 | 7,45 | 7,01 | 96,19 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1006` |
| S5 | B2 | 7,07 | 7,45 | 7,01 | 96,19 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1006` |
| S5 | B3 | 7,07 | 9,47 | 9,83 | 23,23 | 2 | 2 | 0 | 0 | `nr_S5_B3_seed1006` |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.7 Semente 1007

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | 32,36 | 23,60 | 23,76 | 154,92 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1007` |
| S4 | B1 | 32,36 | 23,73 | 23,96 | 149,98 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1007` |
| S4 | B2 | 32,36 | 23,73 | 23,96 | 149,98 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1007` |
| S4 | B3 | 32,36 | 21,89 | 22,30 | 150,44 | 1 | 1 | 0 | 0 | `nr_S4_B3_seed1007` |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | 9,83 | 9,01 | 8,60 | 31,04 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1007` |
| S5 | B1 | 9,83 | 9,04 | 8,60 | 29,93 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1007` |
| S5 | B2 | 9,83 | 9,04 | 8,60 | 29,93 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1007` |
| S5 | B3 | 9,83 | 9,81 | 9,83 | 5,35 | 1 | 1 | 0 | 0 | `nr_S5_B3_seed1007` |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.8 Semente 1008

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | 32,36 | 23,80 | 24,55 | 153,58 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1008` |
| S4 | B1 | 32,36 | 24,00 | 23,88 | 150,80 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1008` |
| S4 | B2 | 32,36 | 24,00 | 23,88 | 150,80 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1008` |
| S4 | B3 | 32,36 | 21,89 | 22,30 | 150,44 | 1 | 1 | 0 | 0 | `nr_S4_B3_seed1008` |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | 9,83 | 9,13 | 9,01 | 22,63 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1008` |
| S5 | B1 | 9,83 | 9,15 | 9,01 | 22,21 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1008` |
| S5 | B2 | 9,83 | 9,15 | 9,01 | 22,21 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1008` |
| S5 | B3 | 9,83 | 9,81 | 9,83 | 5,35 | 1 | 1 | 0 | 0 | `nr_S5_B3_seed1008` |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.9 Semente 1009

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | 32,36 | 23,60 | 23,69 | 153,34 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1009` |
| S4 | B1 | 32,36 | 24,06 | 23,90 | 151,02 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1009` |
| S4 | B2 | 32,36 | 24,06 | 23,90 | 151,02 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1009` |
| S4 | B3 | 32,36 | 21,89 | 22,30 | 150,44 | 1 | 1 | 0 | 0 | `nr_S4_B3_seed1009` |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | 7,07 | 9,16 | 9,01 | 31,17 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1009` |
| S5 | B1 | 7,07 | 9,07 | 9,01 | 33,80 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1009` |
| S5 | B2 | 7,07 | 9,07 | 9,01 | 33,80 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1009` |
| S5 | B3 | 7,07 | 9,82 | 9,83 | 10,21 | 1 | 1 | 0 | 0 | `nr_S5_B3_seed1009` |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.10 Semente 1010

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | 32,36 | 24,03 | 24,33 | 152,36 | 11 | 1 | 0 | 0 | `nr_S4_B0_seed1010` |
| S4 | B1 | 32,36 | 23,85 | 24,19 | 150,56 | 11 | 1 | 0 | 0 | `nr_S4_B1_seed1010` |
| S4 | B2 | 32,36 | 23,85 | 24,19 | 150,56 | 11 | 1 | 0 | 0 | `nr_S4_B2_seed1010` |
| S4 | B3 | 32,36 | 21,89 | 22,30 | 150,44 | 1 | 1 | 0 | 0 | `nr_S4_B3_seed1010` |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | 7,15 | 7,67 | 7,12 | 85,89 | 8 | 8 | 0 | 0 | `nr_S5_B0_seed1010` |
| S5 | B1 | 7,15 | 7,69 | 7,11 | 86,53 | 8 | 8 | 0 | 0 | `nr_S5_B1_seed1010` |
| S5 | B2 | 7,15 | 7,69 | 7,11 | 86,53 | 8 | 8 | 0 | 0 | `nr_S5_B2_seed1010` |
| S5 | B3 | 7,15 | 9,55 | 9,83 | 18,61 | 2 | 2 | 0 | 0 | `nr_S5_B3_seed1010` |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.11 Semente 9101

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | 30,30 | 23,30 | 22,40 | 22,81 | 20 | 0 | 0 | 19 | `nr_G1_B0_seed9101` |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | 30,30 | 30,30 | 30,33 | 5,49 | 9 | 0 | 0 | 0 | `nr_G1_B3_seed9101` |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | 1,65 | 0,10 | 0,08 | 14,23 | 21 | 1 | 0 | 0 | `nr_G2_B0_seed9101` |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | 1,65 | 1,80 | 1,81 | 5,06 | 10 | 1 | 0 | 0 | `nr_G2_B3_seed9101` |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | — | — | — | — | — | — | — | — | ausente |
| S4 | B1 | — | — | — | — | — | — | — | — | ausente |
| S4 | B2 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | — | — | — | — | — | — | — | — | ausente |
| S5 | B1 | — | — | — | — | — | — | — | — | ausente |
| S5 | B2 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | 0,57 | 0,51 | 0,64 | 6,18 | 11 | 1 | 0 | 0 | `nr_S9_B0_seed9101` |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | 0,57 | 0,61 | 0,54 | 15,48 | 1 | 1 | 0 | 0 | `nr_S9_B3_seed9101` |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | 34,82 | 31,03 | 34,79 | 7,91 | 11 | 1 | 0 | 0 | `nr_S10_B0_seed9101` |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | 34,82 | 31,53 | 31,98 | 36,73 | 1 | 1 | 0 | 0 | `nr_S10_B3_seed9101` |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | 20,48 | 19,63 | 19,14 | 22,40 | 8 | 8 | 0 | 0 | `nr_S11_B0_seed9101` |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | 20,48 | 20,03 | 20,47 | 11,08 | 2 | 2 | 0 | 0 | `nr_S11_B3_seed9101` |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | 20,48 | 20,48 | 20,48 | 5,42 | 16 | 0 | 0 | 15 | `nr_S12_B0_seed9101` |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | 20,48 | 20,48 | 20,48 | 5,42 | 7 | 0 | 0 | 0 | `nr_S12_B3_seed9101` |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | 30,72 | 23,71 | 29,75 | 7,84 | 12 | 1 | 0 | 0 | `nr_S13_B0_seed9101` |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | 30,72 | 26,00 | 30,68 | 6,31 | 1 | 0 | 0 | 0 | `nr_S13_B3_seed9101` |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | 49,15 | 49,15 | 49,15 | 5,40 | 16 | 0 | 0 | 15 | `nr_S14_B0_seed9101` |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | 49,15 | 49,15 | 49,15 | 5,39 | 7 | 0 | 0 | 0 | `nr_S14_B3_seed9101` |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | 0,57 | 0,64 | 0,64 | 6,86 | 21 | 1 | 10 | 0 | `nr_S15_B0_seed9101` |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | 0,57 | 0,61 | 0,54 | 15,48 | 1 | 1 | 0 | 0 | `nr_S15_B3_seed9101` |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.12 Semente 9102

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | — | — | — | — | — | — | — | — | ausente |
| S4 | B1 | — | — | — | — | — | — | — | — | ausente |
| S4 | B2 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | — | — | — | — | — | — | — | — | ausente |
| S5 | B1 | — | — | — | — | — | — | — | — | ausente |
| S5 | B2 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | 20,35 | 9,41 | 8,68 | 207,23 | 16 | 0 | 0 | 15 | `nr_S12_B0_seed9102` |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | 20,35 | 18,25 | 18,20 | 40,92 | 7 | 0 | 0 | 0 | `nr_S12_B3_seed9102` |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | 49,15 | 49,15 | 49,15 | 5,52 | 16 | 0 | 0 | 15 | `nr_S14_B0_seed9102` |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | 49,15 | 49,15 | 49,15 | 5,39 | 7 | 0 | 0 | 0 | `nr_S14_B3_seed9102` |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.13 Semente 11001

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | 30,29 | 23,32 | 22,43 | 22,92 | 20 | 0 | 0 | 19 | `nr_G1_B0_seed11001` |
| G1 | B1 | 30,29 | 30,30 | 30,33 | 5,59 | 10 | 0 | 0 | 0 | `nr_G1_B1_seed11001` |
| G1 | B2 | 30,29 | 30,30 | 30,33 | 5,59 | 10 | 0 | 0 | 0 | `nr_G1_B2_seed11001` |
| G1 | B3 | 30,29 | 30,30 | 30,33 | 5,59 | 9 | 0 | 0 | 0 | `nr_G1_B3_seed11001` |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | 1,77 | 0,25 | 0,25 | 24,75 | 21 | 1 | 0 | 0 | `nr_G2_B0_seed11001` |
| G2 | B1 | 1,77 | 0,32 | 0,25 | 21,92 | 21 | 1 | 0 | 0 | `nr_G2_B1_seed11001` |
| G2 | B2 | 1,77 | 0,32 | 0,25 | 21,92 | 21 | 1 | 0 | 0 | `nr_G2_B2_seed11001` |
| G2 | B3 | 1,77 | 1,79 | 1,81 | 4,83 | 10 | 1 | 0 | 0 | `nr_G2_B3_seed11001` |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | — | — | — | — | — | — | — | — | ausente |
| S4 | B1 | — | — | — | — | — | — | — | — | ausente |
| S4 | B2 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | — | — | — | — | — | — | — | — | ausente |
| S5 | B1 | — | — | — | — | — | — | — | — | ausente |
| S5 | B2 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | 0,58 | 0,52 | 0,64 | 6,01 | 11 | 1 | 0 | 0 | `nr_S9_B0_seed11001` |
| S9 | B1 | 0,58 | 0,52 | 0,64 | 6,18 | 11 | 1 | 0 | 0 | `nr_S9_B1_seed11001` |
| S9 | B2 | 0,58 | 0,52 | 0,64 | 6,18 | 11 | 1 | 0 | 0 | `nr_S9_B2_seed11001` |
| S9 | B3 | 0,58 | 0,64 | 0,64 | 15,43 | 1 | 1 | 0 | 0 | `nr_S9_B3_seed11001` |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | 34,82 | 31,19 | 34,79 | 9,36 | 11 | 1 | 0 | 0 | `nr_S10_B0_seed11001` |
| S10 | B1 | 34,82 | 31,17 | 34,79 | 9,06 | 11 | 1 | 0 | 0 | `nr_S10_B1_seed11001` |
| S10 | B2 | 34,82 | 31,17 | 34,79 | 9,06 | 11 | 1 | 0 | 0 | `nr_S10_B2_seed11001` |
| S10 | B3 | 34,82 | 31,26 | 32,47 | 33,56 | 1 | 1 | 0 | 0 | `nr_S10_B3_seed11001` |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | 20,48 | 19,42 | 20,48 | 24,13 | 8 | 8 | 0 | 0 | `nr_S11_B0_seed11001` |
| S11 | B1 | 20,48 | 19,74 | 20,47 | 19,62 | 8 | 8 | 0 | 0 | `nr_S11_B1_seed11001` |
| S11 | B2 | 20,48 | 19,74 | 20,47 | 19,62 | 8 | 8 | 0 | 0 | `nr_S11_B2_seed11001` |
| S11 | B3 | 20,48 | 20,02 | 20,48 | 10,94 | 2 | 2 | 0 | 0 | `nr_S11_B3_seed11001` |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | 20,35 | 9,41 | 8,68 | 207,23 | 16 | 0 | 0 | 15 | `nr_S12_B0_seed11001` |
| S12 | B1 | 20,35 | 18,25 | 18,20 | 40,92 | 8 | 0 | 0 | 0 | `nr_S12_B1_seed11001` |
| S12 | B2 | 20,35 | 18,25 | 18,20 | 40,92 | 8 | 0 | 0 | 0 | `nr_S12_B2_seed11001` |
| S12 | B3 | 20,35 | 18,25 | 18,20 | 40,92 | 7 | 0 | 0 | 0 | `nr_S12_B3_seed11001` |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | 30,72 | 23,05 | 29,39 | 8,10 | 12 | 1 | 0 | 0 | `nr_S13_B0_seed11001` |
| S13 | B1 | 30,72 | 23,14 | 29,39 | 8,49 | 12 | 1 | 0 | 0 | `nr_S13_B1_seed11001` |
| S13 | B2 | 30,72 | 23,14 | 29,39 | 8,49 | 12 | 1 | 0 | 0 | `nr_S13_B2_seed11001` |
| S13 | B3 | 30,72 | 25,50 | 30,55 | 7,73 | 1 | 0 | 0 | 0 | `nr_S13_B3_seed11001` |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | 0,58 | 0,64 | 0,64 | 7,69 | 21 | 1 | 10 | 0 | `nr_S15_B0_seed11001` |
| S15 | B1 | 0,58 | 0,64 | 0,64 | 13,36 | 20 | 0 | 10 | 0 | `nr_S15_B1_seed11001` |
| S15 | B2 | 0,58 | 0,64 | 0,64 | 13,36 | 20 | 0 | 10 | 0 | `nr_S15_B2_seed11001` |
| S15 | B3 | 0,58 | 0,64 | 0,64 | 15,43 | 1 | 1 | 0 | 0 | `nr_S15_B3_seed11001` |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.14 Semente 11002

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | 30,28 | 23,30 | 22,37 | 23,14 | 20 | 0 | 0 | 19 | `nr_G1_B0_seed11002` |
| G1 | B1 | 30,28 | 30,30 | 30,33 | 5,72 | 10 | 0 | 0 | 0 | `nr_G1_B1_seed11002` |
| G1 | B2 | 30,28 | 30,30 | 30,33 | 5,72 | 10 | 0 | 0 | 0 | `nr_G1_B2_seed11002` |
| G1 | B3 | 30,28 | 30,30 | 30,33 | 5,72 | 9 | 0 | 0 | 0 | `nr_G1_B3_seed11002` |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | 1,72 | 0,32 | 0,24 | 37,91 | 21 | 1 | 0 | 0 | `nr_G2_B0_seed11002` |
| G2 | B1 | 1,72 | 0,41 | 0,39 | 31,93 | 21 | 1 | 0 | 0 | `nr_G2_B1_seed11002` |
| G2 | B2 | 1,72 | 0,41 | 0,39 | 31,93 | 21 | 1 | 0 | 0 | `nr_G2_B2_seed11002` |
| G2 | B3 | 1,72 | 1,79 | 1,81 | 4,84 | 10 | 1 | 0 | 0 | `nr_G2_B3_seed11002` |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | — | — | — | — | — | — | — | — | ausente |
| S4 | B1 | — | — | — | — | — | — | — | — | ausente |
| S4 | B2 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | — | — | — | — | — | — | — | — | ausente |
| S5 | B1 | — | — | — | — | — | — | — | — | ausente |
| S5 | B2 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | 0,59 | 0,52 | 0,64 | 6,09 | 11 | 1 | 0 | 0 | `nr_S9_B0_seed11002` |
| S9 | B1 | 0,59 | 0,52 | 0,64 | 6,24 | 11 | 1 | 0 | 0 | `nr_S9_B1_seed11002` |
| S9 | B2 | 0,59 | 0,52 | 0,64 | 6,24 | 11 | 1 | 0 | 0 | `nr_S9_B2_seed11002` |
| S9 | B3 | 0,59 | 0,59 | 0,51 | 15,82 | 1 | 1 | 0 | 0 | `nr_S9_B3_seed11002` |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | 34,82 | 31,14 | 34,79 | 8,93 | 11 | 1 | 0 | 0 | `nr_S10_B0_seed11002` |
| S10 | B1 | 34,82 | 31,22 | 34,79 | 8,54 | 11 | 1 | 0 | 0 | `nr_S10_B1_seed11002` |
| S10 | B2 | 34,82 | 31,22 | 34,79 | 8,54 | 11 | 1 | 0 | 0 | `nr_S10_B2_seed11002` |
| S10 | B3 | 34,82 | 32,63 | 33,37 | 30,31 | 1 | 1 | 0 | 0 | `nr_S10_B3_seed11002` |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | 20,48 | 19,69 | 20,47 | 21,04 | 8 | 8 | 0 | 0 | `nr_S11_B0_seed11002` |
| S11 | B1 | 20,48 | 19,53 | 20,48 | 23,46 | 8 | 8 | 0 | 0 | `nr_S11_B1_seed11002` |
| S11 | B2 | 20,48 | 19,53 | 20,48 | 23,46 | 8 | 8 | 0 | 0 | `nr_S11_B2_seed11002` |
| S11 | B3 | 20,48 | 20,06 | 20,48 | 11,18 | 2 | 2 | 0 | 0 | `nr_S11_B3_seed11002` |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | 20,35 | 9,41 | 8,68 | 207,23 | 16 | 0 | 0 | 15 | `nr_S12_B0_seed11002` |
| S12 | B1 | 20,35 | 18,25 | 18,20 | 40,92 | 8 | 0 | 0 | 0 | `nr_S12_B1_seed11002` |
| S12 | B2 | 20,35 | 18,25 | 18,20 | 40,92 | 8 | 0 | 0 | 0 | `nr_S12_B2_seed11002` |
| S12 | B3 | 20,35 | 18,25 | 18,20 | 40,92 | 7 | 0 | 0 | 0 | `nr_S12_B3_seed11002` |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | 30,72 | 22,71 | 28,48 | 14,31 | 12 | 1 | 0 | 0 | `nr_S13_B0_seed11002` |
| S13 | B1 | 30,72 | 22,80 | 28,60 | 13,56 | 12 | 1 | 0 | 0 | `nr_S13_B1_seed11002` |
| S13 | B2 | 30,72 | 22,80 | 28,60 | 13,56 | 12 | 1 | 0 | 0 | `nr_S13_B2_seed11002` |
| S13 | B3 | 30,72 | 25,84 | 30,72 | 6,15 | 1 | 0 | 0 | 0 | `nr_S13_B3_seed11002` |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | 0,59 | 0,64 | 0,64 | 7,25 | 21 | 1 | 10 | 0 | `nr_S15_B0_seed11002` |
| S15 | B1 | 0,59 | 0,64 | 0,64 | 13,35 | 20 | 0 | 10 | 0 | `nr_S15_B1_seed11002` |
| S15 | B2 | 0,59 | 0,64 | 0,64 | 13,35 | 20 | 0 | 10 | 0 | `nr_S15_B2_seed11002` |
| S15 | B3 | 0,59 | 0,59 | 0,51 | 15,82 | 1 | 1 | 0 | 0 | `nr_S15_B3_seed11002` |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.15 Semente 11003

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | 30,30 | 23,30 | 22,37 | 22,83 | 20 | 0 | 0 | 19 | `nr_G1_B0_seed11003` |
| G1 | B1 | 30,30 | 30,30 | 30,33 | 5,52 | 10 | 0 | 0 | 0 | `nr_G1_B1_seed11003` |
| G1 | B2 | 30,30 | 30,30 | 30,33 | 5,52 | 10 | 0 | 0 | 0 | `nr_G1_B2_seed11003` |
| G1 | B3 | 30,30 | 30,30 | 30,33 | 5,52 | 9 | 0 | 0 | 0 | `nr_G1_B3_seed11003` |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | 1,72 | 0,25 | 0,25 | 9,02 | 21 | 1 | 0 | 0 | `nr_G2_B0_seed11003` |
| G2 | B1 | 1,72 | 0,32 | 0,25 | 9,14 | 21 | 1 | 0 | 0 | `nr_G2_B1_seed11003` |
| G2 | B2 | 1,72 | 0,32 | 0,25 | 9,14 | 21 | 1 | 0 | 0 | `nr_G2_B2_seed11003` |
| G2 | B3 | 1,72 | 1,79 | 1,81 | 4,87 | 10 | 1 | 0 | 0 | `nr_G2_B3_seed11003` |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | — | — | — | — | — | — | — | — | ausente |
| S4 | B1 | — | — | — | — | — | — | — | — | ausente |
| S4 | B2 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | — | — | — | — | — | — | — | — | ausente |
| S5 | B1 | — | — | — | — | — | — | — | — | ausente |
| S5 | B2 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | 0,57 | 0,53 | 0,64 | 5,97 | 11 | 1 | 0 | 0 | `nr_S9_B0_seed11003` |
| S9 | B1 | 0,57 | 0,53 | 0,64 | 6,13 | 11 | 1 | 0 | 0 | `nr_S9_B1_seed11003` |
| S9 | B2 | 0,57 | 0,53 | 0,64 | 6,13 | 11 | 1 | 0 | 0 | `nr_S9_B2_seed11003` |
| S9 | B3 | 0,57 | 0,58 | 0,55 | 17,87 | 1 | 1 | 0 | 0 | `nr_S9_B3_seed11003` |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | 34,82 | 31,29 | 34,79 | 9,11 | 11 | 1 | 0 | 0 | `nr_S10_B0_seed11003` |
| S10 | B1 | 34,82 | 31,25 | 34,79 | 9,28 | 11 | 1 | 0 | 0 | `nr_S10_B1_seed11003` |
| S10 | B2 | 34,82 | 31,25 | 34,79 | 9,28 | 11 | 1 | 0 | 0 | `nr_S10_B2_seed11003` |
| S10 | B3 | 34,82 | 31,90 | 32,17 | 32,87 | 1 | 1 | 0 | 0 | `nr_S10_B3_seed11003` |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | 20,48 | 19,37 | 20,47 | 22,40 | 8 | 8 | 0 | 0 | `nr_S11_B0_seed11003` |
| S11 | B1 | 20,48 | 19,47 | 20,47 | 23,51 | 8 | 8 | 0 | 0 | `nr_S11_B1_seed11003` |
| S11 | B2 | 20,48 | 19,47 | 20,47 | 23,51 | 8 | 8 | 0 | 0 | `nr_S11_B2_seed11003` |
| S11 | B3 | 20,48 | 20,25 | 19,51 | 11,56 | 2 | 2 | 0 | 0 | `nr_S11_B3_seed11003` |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | 20,35 | 9,41 | 8,68 | 207,23 | 16 | 0 | 0 | 15 | `nr_S12_B0_seed11003` |
| S12 | B1 | 20,35 | 18,25 | 18,20 | 40,92 | 8 | 0 | 0 | 0 | `nr_S12_B1_seed11003` |
| S12 | B2 | 20,35 | 18,25 | 18,20 | 40,92 | 8 | 0 | 0 | 0 | `nr_S12_B2_seed11003` |
| S12 | B3 | 20,35 | 18,25 | 18,20 | 40,92 | 7 | 0 | 0 | 0 | `nr_S12_B3_seed11003` |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | 30,72 | 23,76 | 29,88 | 17,78 | 12 | 1 | 0 | 0 | `nr_S13_B0_seed11003` |
| S13 | B1 | 30,72 | 23,79 | 30,00 | 17,54 | 12 | 1 | 0 | 0 | `nr_S13_B1_seed11003` |
| S13 | B2 | 30,72 | 23,79 | 30,00 | 17,54 | 12 | 1 | 0 | 0 | `nr_S13_B2_seed11003` |
| S13 | B3 | 30,72 | 25,91 | 30,70 | 7,09 | 1 | 0 | 0 | 0 | `nr_S13_B3_seed11003` |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | 0,57 | 0,64 | 0,64 | 8,74 | 21 | 1 | 10 | 0 | `nr_S15_B0_seed11003` |
| S15 | B1 | 0,57 | 0,64 | 0,64 | 10,84 | 20 | 0 | 10 | 0 | `nr_S15_B1_seed11003` |
| S15 | B2 | 0,57 | 0,64 | 0,64 | 10,84 | 20 | 0 | 10 | 0 | `nr_S15_B2_seed11003` |
| S15 | B3 | 0,57 | 0,58 | 0,55 | 17,87 | 1 | 1 | 0 | 0 | `nr_S15_B3_seed11003` |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.16 Semente 11004

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | 30,30 | 23,29 | 22,40 | 23,12 | 20 | 0 | 0 | 19 | `nr_G1_B0_seed11004` |
| G1 | B1 | 30,30 | 30,30 | 30,33 | 5,69 | 10 | 0 | 0 | 0 | `nr_G1_B1_seed11004` |
| G1 | B2 | 30,30 | 30,30 | 30,33 | 5,69 | 10 | 0 | 0 | 0 | `nr_G1_B2_seed11004` |
| G1 | B3 | 30,30 | 30,30 | 30,33 | 5,69 | 9 | 0 | 0 | 0 | `nr_G1_B3_seed11004` |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | 1,72 | 0,18 | 0,16 | 11,44 | 21 | 1 | 0 | 0 | `nr_G2_B0_seed11004` |
| G2 | B1 | 1,72 | 0,25 | 0,16 | 12,75 | 21 | 1 | 0 | 0 | `nr_G2_B1_seed11004` |
| G2 | B2 | 1,72 | 0,25 | 0,16 | 12,75 | 21 | 1 | 0 | 0 | `nr_G2_B2_seed11004` |
| G2 | B3 | 1,72 | 1,80 | 1,81 | 4,94 | 10 | 1 | 0 | 0 | `nr_G2_B3_seed11004` |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | — | — | — | — | — | — | — | — | ausente |
| S4 | B1 | — | — | — | — | — | — | — | — | ausente |
| S4 | B2 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | — | — | — | — | — | — | — | — | ausente |
| S5 | B1 | — | — | — | — | — | — | — | — | ausente |
| S5 | B2 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | 0,58 | 0,52 | 0,64 | 6,10 | 11 | 1 | 0 | 0 | `nr_S9_B0_seed11004` |
| S9 | B1 | 0,58 | 0,52 | 0,64 | 6,33 | 11 | 1 | 0 | 0 | `nr_S9_B1_seed11004` |
| S9 | B2 | 0,58 | 0,52 | 0,64 | 6,33 | 11 | 1 | 0 | 0 | `nr_S9_B2_seed11004` |
| S9 | B3 | 0,58 | 0,60 | 0,60 | 23,18 | 1 | 1 | 0 | 0 | `nr_S9_B3_seed11004` |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | 34,82 | 31,35 | 34,79 | 9,67 | 11 | 1 | 0 | 0 | `nr_S10_B0_seed11004` |
| S10 | B1 | 34,82 | 31,33 | 34,79 | 9,49 | 11 | 1 | 0 | 0 | `nr_S10_B1_seed11004` |
| S10 | B2 | 34,82 | 31,33 | 34,79 | 9,49 | 11 | 1 | 0 | 0 | `nr_S10_B2_seed11004` |
| S10 | B3 | 34,82 | 32,39 | 32,92 | 33,23 | 1 | 1 | 0 | 0 | `nr_S10_B3_seed11004` |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | 20,48 | 19,48 | 20,48 | 23,83 | 8 | 8 | 0 | 0 | `nr_S11_B0_seed11004` |
| S11 | B1 | 20,48 | 19,85 | 20,48 | 18,36 | 8 | 8 | 0 | 0 | `nr_S11_B1_seed11004` |
| S11 | B2 | 20,48 | 19,85 | 20,48 | 18,36 | 8 | 8 | 0 | 0 | `nr_S11_B2_seed11004` |
| S11 | B3 | 20,48 | 20,42 | 20,48 | 7,08 | 2 | 2 | 0 | 0 | `nr_S11_B3_seed11004` |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | 20,35 | 9,41 | 8,68 | 207,23 | 16 | 0 | 0 | 15 | `nr_S12_B0_seed11004` |
| S12 | B1 | 20,35 | 18,25 | 18,20 | 40,92 | 8 | 0 | 0 | 0 | `nr_S12_B1_seed11004` |
| S12 | B2 | 20,35 | 18,25 | 18,20 | 40,92 | 8 | 0 | 0 | 0 | `nr_S12_B2_seed11004` |
| S12 | B3 | 20,35 | 18,25 | 18,20 | 40,92 | 7 | 0 | 0 | 0 | `nr_S12_B3_seed11004` |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | 30,72 | 23,85 | 30,30 | 6,55 | 12 | 1 | 0 | 0 | `nr_S13_B0_seed11004` |
| S13 | B1 | 30,72 | 23,92 | 30,30 | 6,54 | 12 | 1 | 0 | 0 | `nr_S13_B1_seed11004` |
| S13 | B2 | 30,72 | 23,92 | 30,30 | 6,54 | 12 | 1 | 0 | 0 | `nr_S13_B2_seed11004` |
| S13 | B3 | 30,72 | 25,61 | 30,50 | 7,71 | 1 | 0 | 0 | 0 | `nr_S13_B3_seed11004` |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | 0,58 | 0,64 | 0,64 | 7,54 | 21 | 1 | 10 | 0 | `nr_S15_B0_seed11004` |
| S15 | B1 | 0,58 | 0,64 | 0,64 | 11,32 | 20 | 0 | 10 | 0 | `nr_S15_B1_seed11004` |
| S15 | B2 | 0,58 | 0,64 | 0,64 | 11,32 | 20 | 0 | 10 | 0 | `nr_S15_B2_seed11004` |
| S15 | B3 | 0,58 | 0,60 | 0,60 | 23,18 | 1 | 1 | 0 | 0 | `nr_S15_B3_seed11004` |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.17 Semente 11005

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | 30,30 | 23,28 | 22,38 | 23,06 | 20 | 0 | 0 | 19 | `nr_G1_B0_seed11005` |
| G1 | B1 | 30,30 | 30,30 | 30,33 | 5,68 | 10 | 0 | 0 | 0 | `nr_G1_B1_seed11005` |
| G1 | B2 | 30,30 | 30,30 | 30,33 | 5,68 | 10 | 0 | 0 | 0 | `nr_G1_B2_seed11005` |
| G1 | B3 | 30,30 | 30,30 | 30,33 | 5,68 | 9 | 0 | 0 | 0 | `nr_G1_B3_seed11005` |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3A | — | — | — | — | — | — | — | — | ausente |
| G2 | B0 | 1,80 | 0,12 | 0,08 | 58,37 | 21 | 1 | 0 | 0 | `nr_G2_B0_seed11005` |
| G2 | B1 | 1,80 | 0,18 | 0,08 | 44,92 | 21 | 1 | 0 | 0 | `nr_G2_B1_seed11005` |
| G2 | B2 | 1,80 | 0,18 | 0,08 | 44,92 | 21 | 1 | 0 | 0 | `nr_G2_B2_seed11005` |
| G2 | B3 | 1,80 | 1,80 | 1,81 | 4,63 | 10 | 1 | 0 | 0 | `nr_G2_B3_seed11005` |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | — | — | — | — | — | — | — | — | ausente |
| S4 | B1 | — | — | — | — | — | — | — | — | ausente |
| S4 | B2 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | — | — | — | — | — | — | — | — | ausente |
| S5 | B1 | — | — | — | — | — | — | — | — | ausente |
| S5 | B2 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | 0,57 | 0,52 | 0,64 | 6,14 | 11 | 1 | 0 | 0 | `nr_S9_B0_seed11005` |
| S9 | B1 | 0,57 | 0,51 | 0,64 | 6,65 | 11 | 1 | 0 | 0 | `nr_S9_B1_seed11005` |
| S9 | B2 | 0,57 | 0,51 | 0,64 | 6,65 | 11 | 1 | 0 | 0 | `nr_S9_B2_seed11005` |
| S9 | B3 | 0,57 | 0,64 | 0,64 | 18,48 | 1 | 1 | 0 | 0 | `nr_S9_B3_seed11005` |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | 34,82 | 31,40 | 34,79 | 9,64 | 11 | 1 | 0 | 0 | `nr_S10_B0_seed11005` |
| S10 | B1 | 34,82 | 31,31 | 34,79 | 8,93 | 11 | 1 | 0 | 0 | `nr_S10_B1_seed11005` |
| S10 | B2 | 34,82 | 31,31 | 34,79 | 8,93 | 11 | 1 | 0 | 0 | `nr_S10_B2_seed11005` |
| S10 | B3 | 34,82 | 31,43 | 31,52 | 34,62 | 1 | 1 | 0 | 0 | `nr_S10_B3_seed11005` |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | 20,48 | 19,75 | 20,42 | 19,79 | 8 | 8 | 0 | 0 | `nr_S11_B0_seed11005` |
| S11 | B1 | 20,48 | 18,52 | 20,62 | 35,47 | 8 | 8 | 0 | 0 | `nr_S11_B1_seed11005` |
| S11 | B2 | 20,48 | 18,52 | 20,62 | 35,47 | 8 | 8 | 0 | 0 | `nr_S11_B2_seed11005` |
| S11 | B3 | 20,48 | 20,38 | 20,03 | 7,76 | 2 | 2 | 0 | 0 | `nr_S11_B3_seed11005` |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | 20,35 | 9,41 | 8,68 | 207,23 | 16 | 0 | 0 | 15 | `nr_S12_B0_seed11005` |
| S12 | B1 | 20,35 | 18,25 | 18,20 | 40,92 | 8 | 0 | 0 | 0 | `nr_S12_B1_seed11005` |
| S12 | B2 | 20,35 | 18,25 | 18,20 | 40,92 | 8 | 0 | 0 | 0 | `nr_S12_B2_seed11005` |
| S12 | B3 | 20,35 | 18,25 | 18,20 | 40,92 | 7 | 0 | 0 | 0 | `nr_S12_B3_seed11005` |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | 30,72 | 24,29 | 30,50 | 8,37 | 12 | 1 | 0 | 0 | `nr_S13_B0_seed11005` |
| S13 | B1 | 30,72 | 23,86 | 29,76 | 8,38 | 12 | 1 | 0 | 0 | `nr_S13_B1_seed11005` |
| S13 | B2 | 30,72 | 23,86 | 29,76 | 8,38 | 12 | 1 | 0 | 0 | `nr_S13_B2_seed11005` |
| S13 | B3 | 30,72 | 25,81 | 30,72 | 5,82 | 1 | 0 | 0 | 0 | `nr_S13_B3_seed11005` |
| S13 | B3A | — | — | — | — | — | — | — | — | ausente |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | 0,57 | 0,64 | 0,64 | 7,63 | 21 | 1 | 10 | 0 | `nr_S15_B0_seed11005` |
| S15 | B1 | 0,57 | 0,64 | 0,64 | 13,16 | 20 | 0 | 10 | 0 | `nr_S15_B1_seed11005` |
| S15 | B2 | 0,57 | 0,64 | 0,64 | 13,16 | 20 | 0 | 10 | 0 | `nr_S15_B2_seed11005` |
| S15 | B3 | 0,57 | 0,64 | 0,64 | 18,48 | 1 | 1 | 0 | 0 | `nr_S15_B3_seed11005` |
| S15 | B3A | — | — | — | — | — | — | — | — | ausente |

### 6.18 Semente 12001

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | 184,48 | 179,53 | 178,85 | 24,93 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed12001` |
| S2 | B3A | 184,48 | 197,16 | 197,50 | 8,35 | 6 | 1 | 0 | 0 | `nr_S2_B3A_seed12001` |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | — | — | — | — | — | — | — | — | ausente |
| S4 | B1 | — | — | — | — | — | — | — | — | ausente |
| S4 | B2 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | — | — | — | — | — | — | — | — | ausente |
| S5 | B1 | — | — | — | — | — | — | — | — | ausente |
| S5 | B2 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | 30,72 | 25,26 | 29,90 | 6,26 | 1 | 0 | 0 | 0 | `nr_S13_B3_seed12001` |
| S13 | B3A | 30,72 | 27,40 | 29,90 | 5,99 | 2 | 1 | 0 | 0 | `nr_S13_B3A_seed12001` |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | 0,59 | 0,56 | 0,49 | 20,04 | 1 | 1 | 0 | 0 | `nr_S15_B3_seed12001` |
| S15 | B3A | 0,59 | 0,64 | 0,64 | 7,37 | 10 | 1 | 0 | 0 | `nr_S15_B3A_seed12001` |

### 6.19 Semente 12002

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | 196,78 | 195,05 | 194,92 | 23,00 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed12002` |
| S2 | B3A | 196,78 | 198,33 | 197,51 | 8,48 | 6 | 1 | 0 | 0 | `nr_S2_B3A_seed12002` |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | — | — | — | — | — | — | — | — | ausente |
| S4 | B1 | — | — | — | — | — | — | — | — | ausente |
| S4 | B2 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | — | — | — | — | — | — | — | — | ausente |
| S5 | B1 | — | — | — | — | — | — | — | — | ausente |
| S5 | B2 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | 30,72 | 25,67 | 30,72 | 7,47 | 1 | 0 | 0 | 0 | `nr_S13_B3_seed12002` |
| S13 | B3A | 30,72 | 28,03 | 30,72 | 5,68 | 2 | 1 | 0 | 0 | `nr_S13_B3A_seed12002` |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | 0,59 | 0,62 | 0,62 | 19,61 | 1 | 1 | 0 | 0 | `nr_S15_B3_seed12002` |
| S15 | B3A | 0,59 | 0,64 | 0,64 | 7,02 | 10 | 1 | 0 | 0 | `nr_S15_B3A_seed12002` |

### 6.20 Semente 12003

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | 197,51 | 197,49 | 197,52 | 6,72 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed12003` |
| S2 | B3A | 197,51 | 197,49 | 197,52 | 6,71 | 6 | 1 | 0 | 0 | `nr_S2_B3A_seed12003` |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | — | — | — | — | — | — | — | — | ausente |
| S4 | B1 | — | — | — | — | — | — | — | — | ausente |
| S4 | B2 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | — | — | — | — | — | — | — | — | ausente |
| S5 | B1 | — | — | — | — | — | — | — | — | ausente |
| S5 | B2 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | 30,72 | 25,58 | 30,44 | 11,61 | 1 | 0 | 0 | 0 | `nr_S13_B3_seed12003` |
| S13 | B3A | 30,72 | 28,15 | 30,72 | 6,82 | 2 | 1 | 0 | 0 | `nr_S13_B3A_seed12003` |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | 0,55 | 0,59 | 0,51 | 19,20 | 1 | 1 | 0 | 0 | `nr_S15_B3_seed12003` |
| S15 | B3A | 0,55 | 0,64 | 0,64 | 7,38 | 10 | 1 | 0 | 0 | `nr_S15_B3A_seed12003` |

### 6.21 Semente 12004

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | 175,12 | 179,55 | 179,65 | 21,10 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed12004` |
| S2 | B3A | 175,12 | 196,99 | 197,50 | 8,20 | 6 | 1 | 0 | 0 | `nr_S2_B3A_seed12004` |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | — | — | — | — | — | — | — | — | ausente |
| S4 | B1 | — | — | — | — | — | — | — | — | ausente |
| S4 | B2 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | — | — | — | — | — | — | — | — | ausente |
| S5 | B1 | — | — | — | — | — | — | — | — | ausente |
| S5 | B2 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | 30,72 | 25,86 | 30,71 | 5,52 | 1 | 0 | 0 | 0 | `nr_S13_B3_seed12004` |
| S13 | B3A | 30,72 | 28,06 | 30,72 | 5,61 | 2 | 1 | 0 | 0 | `nr_S13_B3A_seed12004` |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | 0,56 | 0,62 | 0,62 | 20,99 | 1 | 1 | 0 | 0 | `nr_S15_B3_seed12004` |
| S15 | B3A | 0,56 | 0,64 | 0,64 | 7,73 | 10 | 1 | 0 | 0 | `nr_S15_B3A_seed12004` |

### 6.22 Semente 12005

| Cenário | Baseline | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras | Oscilações | Execução |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | :-- |
| S0 | B0 | — | — | — | — | — | — | — | — | ausente |
| S0 | B1 | — | — | — | — | — | — | — | — | ausente |
| S0 | B2 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3 | — | — | — | — | — | — | — | — | ausente |
| S0 | B3A | — | — | — | — | — | — | — | — | ausente |
| S1 | B0 | — | — | — | — | — | — | — | — | ausente |
| S1 | B1 | — | — | — | — | — | — | — | — | ausente |
| S1 | B2 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3 | — | — | — | — | — | — | — | — | ausente |
| S1 | B3A | — | — | — | — | — | — | — | — | ausente |
| G1 | B0 | — | — | — | — | — | — | — | — | ausente |
| G1 | B1 | — | — | — | — | — | — | — | — | ausente |
| G1 | B2 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3 | — | — | — | — | — | — | — | — | ausente |
| G1 | B3A | — | — | — | — | — | — | — | — | ausente |
| S2 | B0 | — | — | — | — | — | — | — | — | ausente |
| S2 | B1 | — | — | — | — | — | — | — | — | ausente |
| S2 | B2 | — | — | — | — | — | — | — | — | ausente |
| S2 | B3 | 198,49 | 182,24 | 180,24 | 36,91 | 5 | 0 | 0 | 0 | `nr_S2_B3_seed12005` |
| S2 | B3A | 198,49 | 198,35 | 197,50 | 8,53 | 6 | 1 | 0 | 0 | `nr_S2_B3A_seed12005` |
| G2 | B0 | — | — | — | — | — | — | — | — | ausente |
| G2 | B1 | — | — | — | — | — | — | — | — | ausente |
| G2 | B2 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3 | — | — | — | — | — | — | — | — | ausente |
| G2 | B3A | — | — | — | — | — | — | — | — | ausente |
| S3 | B0 | — | — | — | — | — | — | — | — | ausente |
| S3 | B1 | — | — | — | — | — | — | — | — | ausente |
| S3 | B2 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3 | — | — | — | — | — | — | — | — | ausente |
| S3 | B3A | — | — | — | — | — | — | — | — | ausente |
| S4 | B0 | — | — | — | — | — | — | — | — | ausente |
| S4 | B1 | — | — | — | — | — | — | — | — | ausente |
| S4 | B2 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3 | — | — | — | — | — | — | — | — | ausente |
| S4 | B3A | — | — | — | — | — | — | — | — | ausente |
| S5 | B0 | — | — | — | — | — | — | — | — | ausente |
| S5 | B1 | — | — | — | — | — | — | — | — | ausente |
| S5 | B2 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3 | — | — | — | — | — | — | — | — | ausente |
| S5 | B3A | — | — | — | — | — | — | — | — | ausente |
| S6 | B0 | — | — | — | — | — | — | — | — | ausente |
| S6 | B1 | — | — | — | — | — | — | — | — | ausente |
| S6 | B2 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3 | — | — | — | — | — | — | — | — | ausente |
| S6 | B3A | — | — | — | — | — | — | — | — | ausente |
| S7 | B0 | — | — | — | — | — | — | — | — | ausente |
| S7 | B1 | — | — | — | — | — | — | — | — | ausente |
| S7 | B2 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3 | — | — | — | — | — | — | — | — | ausente |
| S7 | B3A | — | — | — | — | — | — | — | — | ausente |
| S9 | B0 | — | — | — | — | — | — | — | — | ausente |
| S9 | B1 | — | — | — | — | — | — | — | — | ausente |
| S9 | B2 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3 | — | — | — | — | — | — | — | — | ausente |
| S9 | B3A | — | — | — | — | — | — | — | — | ausente |
| S10 | B0 | — | — | — | — | — | — | — | — | ausente |
| S10 | B1 | — | — | — | — | — | — | — | — | ausente |
| S10 | B2 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3 | — | — | — | — | — | — | — | — | ausente |
| S10 | B3A | — | — | — | — | — | — | — | — | ausente |
| S11 | B0 | — | — | — | — | — | — | — | — | ausente |
| S11 | B1 | — | — | — | — | — | — | — | — | ausente |
| S11 | B2 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3 | — | — | — | — | — | — | — | — | ausente |
| S11 | B3A | — | — | — | — | — | — | — | — | ausente |
| S12 | B0 | — | — | — | — | — | — | — | — | ausente |
| S12 | B1 | — | — | — | — | — | — | — | — | ausente |
| S12 | B2 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3 | — | — | — | — | — | — | — | — | ausente |
| S12 | B3A | — | — | — | — | — | — | — | — | ausente |
| S13 | B0 | — | — | — | — | — | — | — | — | ausente |
| S13 | B1 | — | — | — | — | — | — | — | — | ausente |
| S13 | B2 | — | — | — | — | — | — | — | — | ausente |
| S13 | B3 | 30,72 | 25,94 | 30,71 | 7,21 | 1 | 0 | 0 | 0 | `nr_S13_B3_seed12005` |
| S13 | B3A | 30,72 | 27,56 | 30,13 | 12,12 | 2 | 1 | 0 | 0 | `nr_S13_B3A_seed12005` |
| S14 | B0 | — | — | — | — | — | — | — | — | ausente |
| S14 | B1 | — | — | — | — | — | — | — | — | ausente |
| S14 | B2 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3 | — | — | — | — | — | — | — | — | ausente |
| S14 | B3A | — | — | — | — | — | — | — | — | ausente |
| S15 | B0 | — | — | — | — | — | — | — | — | ausente |
| S15 | B1 | — | — | — | — | — | — | — | — | ausente |
| S15 | B2 | — | — | — | — | — | — | — | — | ausente |
| S15 | B3 | 0,56 | 0,58 | 0,51 | 20,11 | 1 | 1 | 0 | 0 | `nr_S15_B3_seed12005` |
| S15 | B3A | 0,56 | 0,61 | 0,54 | 7,04 | 10 | 1 | 0 | 0 | `nr_S15_B3A_seed12005` |

## 7. Diferenças pareadas B3 − Bx

Para cada semente, valor do B3 menos o do baseline de comparação, na mesma semente. Média ± IC 95 %; "melhor / pior / empate" conta as sementes em que o B3 teve vazão maior (atraso menor), menor (maior) ou igual. "IC exclui 0" marca diferenças distinguíveis de zero com n = 22.

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
| G1 | B3 − B0 | Vazão no conflito (Mbps) | 7,00 ± 0,02 | 6 / 0 / 0 | sim |
| G1 | B3 − B0 | Atraso no conflito (ms) | -17,36 ± 0,06 | 6 / 0 / 0 | sim |
| G1 | B3 − B1 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| G1 | B3 − B1 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| G1 | B3 − B2 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| G1 | B3 − B2 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S2 | B3 − B0 | Vazão no conflito (Mbps) | -4,25 ± 14,85 | 2 / 2 / 1 | não |
| S2 | B3 − B0 | Atraso no conflito (ms) | 18,74 ± 22,57 | 0 / 4 / 1 | não |
| S2 | B3 − B1 | Vazão no conflito (Mbps) | -4,32 ± 14,95 | 2 / 2 / 1 | não |
| S2 | B3 − B1 | Atraso no conflito (ms) | 18,67 ± 22,53 | 0 / 4 / 1 | não |
| S2 | B3 − B2 | Vazão no conflito (Mbps) | -4,32 ± 14,95 | 2 / 2 / 1 | não |
| S2 | B3 − B2 | Atraso no conflito (ms) | 18,67 ± 22,53 | 0 / 4 / 1 | não |
| S2 | B3 − B3A | Vazão no conflito (Mbps) | -10,89 ± 10,61 | 1 / 4 / 0 | sim |
| S2 | B3 − B3A | Atraso no conflito (ms) | 14,48 ± 12,57 | 0 / 5 / 0 | sim |
| G2 | B3 − B0 | Vazão no conflito (Mbps) | 1,59 ± 0,09 | 6 / 0 / 0 | sim |
| G2 | B3 − B0 | Atraso no conflito (ms) | -21,09 ± 20,20 | 6 / 0 / 0 | sim |
| G2 | B3 − B1 | Vazão no conflito (Mbps) | 1,50 ± 0,11 | 5 / 0 / 0 | sim |
| G2 | B3 − B1 | Atraso no conflito (ms) | -19,31 ± 18,25 | 5 / 0 / 0 | sim |
| G2 | B3 − B2 | Vazão no conflito (Mbps) | 1,50 ± 0,11 | 5 / 0 / 0 | sim |
| G2 | B3 − B2 | Atraso no conflito (ms) | -19,31 ± 18,25 | 5 / 0 / 0 | sim |
| S3 | B3 − B0 | Vazão no conflito (Mbps) | -0,34 ± 0,91 | 1 / 4 / 0 | não |
| S3 | B3 − B0 | Atraso no conflito (ms) | 13,73 ± 32,76 | 2 / 3 / 0 | não |
| S3 | B3 − B1 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S3 | B3 − B1 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S3 | B3 − B2 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S3 | B3 − B2 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S4 | B3 − B0 | Vazão no conflito (Mbps) | -1,05 ± 0,72 | 1 / 9 / 0 | sim |
| S4 | B3 − B0 | Atraso no conflito (ms) | -2,91 ± 0,65 | 10 / 0 / 0 | sim |
| S4 | B3 − B1 | Vazão no conflito (Mbps) | -0,98 ± 0,75 | 0 / 5 / 5 | sim |
| S4 | B3 − B1 | Atraso no conflito (ms) | -0,10 ± 0,21 | 4 / 1 / 5 | não |
| S4 | B3 − B2 | Vazão no conflito (Mbps) | -0,98 ± 0,75 | 0 / 5 / 5 | sim |
| S4 | B3 − B2 | Atraso no conflito (ms) | -0,10 ± 0,21 | 4 / 1 / 5 | não |
| S5 | B3 − B0 | Vazão no conflito (Mbps) | 0,60 ± 0,56 | 8 / 2 / 0 | sim |
| S5 | B3 − B0 | Atraso no conflito (ms) | -20,71 ± 20,08 | 8 / 2 / 0 | sim |
| S5 | B3 − B1 | Vazão no conflito (Mbps) | 0,61 ± 0,56 | 5 / 0 / 5 | sim |
| S5 | B3 − B1 | Atraso no conflito (ms) | -20,59 ± 20,15 | 5 / 0 / 5 | sim |
| S5 | B3 − B2 | Vazão no conflito (Mbps) | 0,61 ± 0,56 | 5 / 0 / 5 | sim |
| S5 | B3 − B2 | Atraso no conflito (ms) | -20,59 ± 20,15 | 5 / 0 / 5 | sim |
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
| S9 | B3 − B0 | Vazão no conflito (Mbps) | 0,09 ± 0,03 | 6 / 0 / 0 | sim |
| S9 | B3 − B0 | Atraso no conflito (ms) | 11,63 ± 3,12 | 0 / 6 / 0 | sim |
| S9 | B3 − B1 | Vazão no conflito (Mbps) | 0,09 ± 0,04 | 5 / 0 / 0 | sim |
| S9 | B3 − B1 | Atraso no conflito (ms) | 11,85 ± 3,77 | 0 / 5 / 0 | sim |
| S9 | B3 − B2 | Vazão no conflito (Mbps) | 0,09 ± 0,04 | 5 / 0 / 0 | sim |
| S9 | B3 − B2 | Atraso no conflito (ms) | 11,85 ± 3,77 | 0 / 5 / 0 | sim |
| S10 | B3 − B0 | Vazão no conflito (Mbps) | 0,63 ± 0,60 | 6 / 0 / 0 | sim |
| S10 | B3 − B0 | Atraso no conflito (ms) | 24,45 ± 2,58 | 0 / 6 / 0 | sim |
| S10 | B3 − B1 | Vazão no conflito (Mbps) | 0,67 ± 0,72 | 5 / 0 / 0 | não |
| S10 | B3 − B1 | Atraso no conflito (ms) | 23,85 ± 1,78 | 0 / 5 / 0 | sim |
| S10 | B3 − B2 | Vazão no conflito (Mbps) | 0,67 ± 0,72 | 5 / 0 / 0 | não |
| S10 | B3 − B2 | Atraso no conflito (ms) | 23,85 ± 1,78 | 0 / 5 / 0 | sim |
| S11 | B3 − B0 | Vazão no conflito (Mbps) | 0,64 ± 0,25 | 6 / 0 / 0 | sim |
| S11 | B3 − B0 | Atraso no conflito (ms) | -12,33 ± 2,56 | 6 / 0 / 0 | sim |
| S11 | B3 − B1 | Vazão no conflito (Mbps) | 0,80 ± 0,76 | 5 / 0 / 0 | sim |
| S11 | B3 − B1 | Atraso no conflito (ms) | -14,38 ± 9,42 | 5 / 0 / 0 | sim |
| S11 | B3 − B2 | Vazão no conflito (Mbps) | 0,80 ± 0,76 | 5 / 0 / 0 | sim |
| S11 | B3 − B2 | Atraso no conflito (ms) | -14,38 ± 9,42 | 5 / 0 / 0 | sim |
| S12 | B3 − B0 | Vazão no conflito (Mbps) | 7,58 ± 3,09 | 6 / 0 / 1 | sim |
| S12 | B3 − B0 | Atraso no conflito (ms) | -142,55 ± 58,14 | 6 / 0 / 1 | sim |
| S12 | B3 − B1 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S12 | B3 − B1 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S12 | B3 − B2 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S12 | B3 − B2 | Atraso no conflito (ms) | 0,00 ± 0,00 | 0 / 0 / 5 | não |
| S13 | B3 − B0 | Vazão no conflito (Mbps) | 2,22 ± 0,59 | 6 / 0 / 0 | sim |
| S13 | B3 − B0 | Atraso no conflito (ms) | -3,69 ± 4,91 | 5 / 1 / 0 | não |
| S13 | B3 − B1 | Vazão no conflito (Mbps) | 2,23 ± 0,63 | 5 / 0 / 0 | sim |
| S13 | B3 − B1 | Atraso no conflito (ms) | -4,00 ± 5,97 | 4 / 1 / 0 | não |
| S13 | B3 − B2 | Vazão no conflito (Mbps) | 2,23 ± 0,63 | 5 / 0 / 0 | sim |
| S13 | B3 − B2 | Atraso no conflito (ms) | -4,00 ± 5,97 | 4 / 1 / 0 | não |
| S13 | B3 − B3A | Vazão no conflito (Mbps) | -2,18 ± 0,44 | 0 / 5 / 0 | sim |
| S13 | B3 − B3A | Atraso no conflito (ms) | 0,37 ± 4,37 | 2 / 3 / 0 | não |
| S14 | B3 − B0 | Vazão no conflito (Mbps) | 0,00 ± 0,00 | 0 / 0 / 2 | não |
| S14 | B3 − B0 | Atraso no conflito (ms) | -0,06 ± 0,78 | 2 / 0 / 0 | não |
| S15 | B3 − B0 | Vazão no conflito (Mbps) | -0,03 ± 0,02 | 0 / 6 / 0 | sim |
| S15 | B3 − B0 | Atraso no conflito (ms) | 10,09 ± 3,05 | 0 / 6 / 0 | sim |
| S15 | B3 − B1 | Vazão no conflito (Mbps) | -0,03 ± 0,03 | 0 / 5 / 0 | não |
| S15 | B3 − B1 | Atraso no conflito (ms) | 5,75 ± 4,95 | 0 / 5 / 0 | sim |
| S15 | B3 − B2 | Vazão no conflito (Mbps) | -0,03 ± 0,03 | 0 / 5 / 0 | não |
| S15 | B3 − B2 | Atraso no conflito (ms) | 5,75 ± 4,95 | 0 / 5 / 0 | sim |
| S15 | B3 − B3A | Vazão no conflito (Mbps) | -0,04 ± 0,03 | 0 / 5 / 0 | sim |
| S15 | B3 − B3A | Atraso no conflito (ms) | 12,68 ± 0,69 | 0 / 5 / 0 | sim |

## 8. Cronogramas de ações idênticos entre baselines

Baselines com o mesmo `action_schedule_sha256` aplicaram exatamente as mesmas ações; com a mesma semente, a simulação é a mesma e os resultados coincidem por construção.

| Cenário | Grupos com cronograma idêntico | Mesmo padrão em todas as sementes |
| :-- | :-- | :-- |
| S0 | ; B0 · B1 = B2 = B3 | não |
| S1 | ; B0 · B1 = B2 = B3 | não |
| G1 | ; B0 · B1 = B2 · B3; B0 · B3 | não |
| S2 | ; B0 · B1 = B2 · B3; B3 · B3A | não |
| G2 | ; B0 · B1 = B2 · B3; B0 · B3 | não |
| S3 | ; B0 · B1 = B2 = B3 | não |
| S4 | ; B0 · B1 = B2 · B3 | não |
| S5 | ; B0 · B1 = B2 = B3; B0 · B1 = B2 · B3 | não |
| S6 | ; B0 · B1 · B2 · B3 | não |
| S7 | ; B0 · B1 = B2 · B3 | não |
| S9 | ; B0 · B1 = B2 · B3; B0 · B3 | não |
| S10 | ; B0 · B1 = B2 · B3; B0 · B3 | não |
| S11 | ; B0 · B1 = B2 · B3; B0 · B3 | não |
| S12 | ; B0 · B1 = B2 · B3; B0 · B3 | não |
| S13 | ; B0 · B1 = B2 · B3; B0 · B3; B3 · B3A | não |
| S14 | ; B0 · B3 | não |
| S15 | ; B0 · B1 = B2 · B3; B0 · B3; B3 · B3A | não |

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

### H4 (S4, entre células (limitação esperada)): REFUTADA

A H-RDL não detecta o conflito entre células: o handover acontece e B3 não difere do B1 em vazão nem em atraso.

- ATENDIDO: Handovers de B3 > 0 em todas as sementes: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
- NÃO ATENDIDO: Vazão no conflito (Mbps) B3 − B1 = -0,98 (IC 95 % [-1,73; -0,24], n = 10)
- ATENDIDO: Atraso no conflito (ms) B3 − B1 = -0,10 (IC 95 % [-0,31; 0,11], n = 10)

### H5 (S5, temporal entre células (limitação esperada)): REFUTADA

A H-RDL não detecta o ping-pong entre células: B3 aplica os mesmos handovers que o B0.

- NÃO ATENDIDO: Handovers B3 − B0 = -3,30 (IC 95 % [-5,80; -0,80], n = 10)
- NÃO ATENDIDO: Vazão no conflito (Mbps) B3 − B0 = 0,60 (IC 95 % [0,04; 1,17], n = 10)

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
- H6 (S6): Sob tempestade de conflitos, a H-RDL aplica menos ações, elimina as oscilações e reduz o atraso em relação a B0, B1 e B2.
- H7 (S7): O Safety Guard impede que ações inseguras cheguem à RAN no B3, enquanto B0, B1 e B2 as aplicam.

**Refutadas:**

- H4 (S4): A H-RDL não detecta o conflito entre células: o handover acontece e B3 não difere do B1 em vazão nem em atraso.
  - NÃO ATENDIDO: Vazão no conflito (Mbps) B3 − B1 = -0,98 (IC 95 % [-1,73; -0,24], n = 10)
- H5 (S5): A H-RDL não detecta o ping-pong entre células: B3 aplica os mesmos handovers que o B0.
  - NÃO ATENDIDO: Handovers B3 − B0 = -3,30 (IC 95 % [-5,80; -0,80], n = 10)
  - NÃO ATENDIDO: Vazão no conflito (Mbps) B3 − B0 = 0,60 (IC 95 % [0,04; 1,17], n = 10)

**Inconclusivas:**

- H2 (S2): Em conflito indireto, a H-RDL escolhe um subconjunto de ações que não piora vazão nem atraso em relação a B0, B1 e B2.
  - INCONCLUSIVO: Vazão no conflito (Mbps) B3 − B0 = -4,25 (IC 95 % [-19,11; 10,60], n = 5)
  - INCONCLUSIVO: Atraso no conflito (ms) B3 − B0 = 18,74 (IC 95 % [-3,83; 41,31], n = 5)
  - INCONCLUSIVO: Vazão no conflito (Mbps) B3 − B1 = -4,32 (IC 95 % [-19,27; 10,63], n = 5)
  - INCONCLUSIVO: Atraso no conflito (ms) B3 − B1 = 18,67 (IC 95 % [-3,85; 41,20], n = 5)
- H3 (S3): Em conflito direto de potência, a H-RDL elimina as oscilações sem perda de vazão em relação ao B0.
  - INCONCLUSIVO: Vazão no conflito (Mbps) B3 − B0 = -0,34 (IC 95 % [-1,25; 0,57], n = 5)

**Diferenças desfavoráveis ao B3 com IC 95 % excluindo zero** (fora ou além das hipóteses; seção 7):

- S2, B3 − B3A, Vazão no conflito (Mbps): -10,89 ± 10,61 (B3 pior em 4/5 sementes)
- S2, B3 − B3A, Atraso no conflito (ms): 14,48 ± 12,57 (B3 pior em 5/5 sementes)
- S4, B3 − B0, Vazão no conflito (Mbps): -1,05 ± 0,72 (B3 pior em 9/10 sementes)
- S4, B3 − B1, Vazão no conflito (Mbps): -0,98 ± 0,75 (B3 pior em 5/10 sementes)
- S4, B3 − B2, Vazão no conflito (Mbps): -0,98 ± 0,75 (B3 pior em 5/10 sementes)
- S7, B3 − B0, Vazão no conflito (Mbps): -0,06 ± 0,01 (B3 pior em 5/5 sementes)
- S7, B3 − B0, Atraso no conflito (ms): 3,01 ± 0,54 (B3 pior em 5/5 sementes)
- S7, B3 − B1, Vazão no conflito (Mbps): -0,0048 ± 0,0012 (B3 pior em 5/5 sementes)
- S7, B3 − B1, Atraso no conflito (ms): 0,31 ± 0,22 (B3 pior em 5/5 sementes)
- S7, B3 − B2, Vazão no conflito (Mbps): -0,0048 ± 0,0012 (B3 pior em 5/5 sementes)
- S7, B3 − B2, Atraso no conflito (ms): 0,31 ± 0,22 (B3 pior em 5/5 sementes)
- S9, B3 − B0, Atraso no conflito (ms): 11,63 ± 3,12 (B3 pior em 6/6 sementes)
- S9, B3 − B1, Atraso no conflito (ms): 11,85 ± 3,77 (B3 pior em 5/5 sementes)
- S9, B3 − B2, Atraso no conflito (ms): 11,85 ± 3,77 (B3 pior em 5/5 sementes)
- S10, B3 − B0, Atraso no conflito (ms): 24,45 ± 2,58 (B3 pior em 6/6 sementes)
- S10, B3 − B1, Atraso no conflito (ms): 23,85 ± 1,78 (B3 pior em 5/5 sementes)
- S10, B3 − B2, Atraso no conflito (ms): 23,85 ± 1,78 (B3 pior em 5/5 sementes)
- S13, B3 − B3A, Vazão no conflito (Mbps): -2,18 ± 0,44 (B3 pior em 5/5 sementes)
- S15, B3 − B0, Vazão no conflito (Mbps): -0,03 ± 0,02 (B3 pior em 6/6 sementes)
- S15, B3 − B0, Atraso no conflito (ms): 10,09 ± 3,05 (B3 pior em 6/6 sementes)
- S15, B3 − B1, Atraso no conflito (ms): 5,75 ± 4,95 (B3 pior em 5/5 sementes)
- S15, B3 − B2, Atraso no conflito (ms): 5,75 ± 4,95 (B3 pior em 5/5 sementes)
- S15, B3 − B3A, Vazão no conflito (Mbps): -0,04 ± 0,03 (B3 pior em 5/5 sementes)
- S15, B3 − B3A, Atraso no conflito (ms): 12,68 ± 0,69 (B3 pior em 5/5 sementes)

Nos cenários S0, S1, S3, B1, B2 e B3 aplicaram o mesmo cronograma em todas as sementes. Nesses cenários a campanha mede o efeito de coordenar versus não coordenar, não uma vantagem específica da H-RDL sobre FIFO ou prioridade estática.

## 11. Ameaças à validade e proveniência

- Malha aberta: a decisão não reage ao estado da RAN; o closed loop E2 (gates G1–G4) não é avaliado aqui.
- As propostas são estilizadas (valores e períodos fixos do catálogo), idênticas entre baselines e sementes.
- n = 22 sementes por célula: ICs largos em métricas com variância entre sementes; sobreposição de IC não é teste de hipótese, e as regras da seção 2 usam a diferença pareada.
- Contagens (ações, handovers, inseguras, oscilações) dependem só do cronograma e são constantes entre sementes.
- S2, S4 e S5 rodam com `--disableSrs=true` (contorno de falha do 5G-LENA v5.1 em handover), igual para todos os baselines.
- Fonte do cenário diferente dentro de um conjunto pareado: S0 semente 1001 (B0/B1/B2/B3 `38646996`; B3A `?`), S0 semente 1002 (B0/B1/B2/B3 `42a4c36a`; B3A `?`), S0 semente 1003 (B0/B1/B2/B3 `42a4c36a`; B3A `?`), S0 semente 1004 (B0/B1/B2/B3 `42a4c36a`; B3A `?`), S0 semente 1005 (B0/B1/B2/B3 `42a4c36a`; B3A `?`), S1 semente 1001 (B0/B1/B2/B3 `c6631888`; B3A `?`), S1 semente 1002 (B0/B1/B2/B3 `8b0b9b70`; B3A `?`), S1 semente 1003 (B0/B1/B2/B3 `8b0b9b70`; B3A `?`), S1 semente 1004 (B0/B1/B2/B3 `8b0b9b70`; B3A `?`), S1 semente 1005 (B0/B1/B2/B3 `8b0b9b70`; B3A `?`), G1 semente 9101 (B0/B3 `70498fc4`; B1/B2/B3A `?`), G1 semente 11001 (B0/B1/B2/B3 `70498fc4`; B3A `?`), G1 semente 11002 (B0/B1/B2/B3 `70498fc4`; B3A `?`), G1 semente 11003 (B0/B1/B2/B3 `70498fc4`; B3A `?`), G1 semente 11004 (B0/B1/B2/B3 `70498fc4`; B3A `?`), G1 semente 11005 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S2 semente 1001 (B0/B1/B2/B3 `12feead4`; B3A `?`), S2 semente 1002 (B0/B1/B2/B3 `12feead4`; B3A `?`), S2 semente 1003 (B0/B1/B2/B3 `12feead4`; B3A `?`), S2 semente 1004 (B0/B1/B2/B3 `12feead4`; B3A `?`), S2 semente 1005 (B0/B1/B2/B3 `12feead4`; B3A `?`), S2 semente 12001 (B0/B1/B2 `?`; B3/B3A `12feead4`), S2 semente 12002 (B0/B1/B2 `?`; B3/B3A `12feead4`), S2 semente 12003 (B0/B1/B2 `?`; B3/B3A `12feead4`), S2 semente 12004 (B0/B1/B2 `?`; B3/B3A `12feead4`), S2 semente 12005 (B0/B1/B2 `?`; B3/B3A `12feead4`), G2 semente 9101 (B0/B3 `70498fc4`; B1/B2/B3A `?`), G2 semente 11001 (B0/B1/B2/B3 `70498fc4`; B3A `?`), G2 semente 11002 (B0/B1/B2/B3 `70498fc4`; B3A `?`), G2 semente 11003 (B0/B1/B2/B3 `70498fc4`; B3A `?`), G2 semente 11004 (B0/B1/B2/B3 `70498fc4`; B3A `?`), G2 semente 11005 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S3 semente 1001 (B0/B1/B2/B3 `6d141018`; B3A `?`), S3 semente 1002 (B0/B1/B2/B3 `7d4a365d`; B3A `?`), S3 semente 1003 (B0/B1/B2/B3 `7d4a365d`; B3A `?`), S3 semente 1004 (B0/B1/B2/B3 `7d4a365d`; B3A `?`), S3 semente 1005 (B0/B1/B2/B3 `7d4a365d`; B3A `?`), S4 semente 1001 (B0/B1/B2/B3 `3daa8733`; B3A `?`), S4 semente 1002 (B0/B1/B2/B3 `3daa8733`; B3A `?`), S4 semente 1003 (B0/B1/B2/B3 `3daa8733`; B3A `?`), S4 semente 1004 (B0/B1/B2/B3 `3daa8733`; B3A `?`), S4 semente 1005 (B0/B1/B2/B3 `3daa8733`; B3A `?`), S4 semente 1006 (B0/B1/B2/B3 `3daa8733`; B3A `?`), S4 semente 1007 (B0/B1/B2/B3 `3daa8733`; B3A `?`), S4 semente 1008 (B0/B1/B2/B3 `3daa8733`; B3A `?`), S4 semente 1009 (B0/B1/B2/B3 `3daa8733`; B3A `?`), S4 semente 1010 (B0/B1/B2/B3 `3daa8733`; B3A `?`), S5 semente 1001 (B0/B1/B2/B3 `777408ad`; B3A `?`), S5 semente 1002 (B0/B1/B2/B3 `777408ad`; B3A `?`), S5 semente 1003 (B0/B1/B2/B3 `777408ad`; B3A `?`), S5 semente 1004 (B0/B1/B2/B3 `777408ad`; B3A `?`), S5 semente 1005 (B0/B1/B2/B3 `777408ad`; B3A `?`), S5 semente 1006 (B0/B1/B2/B3 `777408ad`; B3A `?`), S5 semente 1007 (B0/B1/B2/B3 `777408ad`; B3A `?`), S5 semente 1008 (B0/B1/B2/B3 `777408ad`; B3A `?`), S5 semente 1009 (B0/B1/B2/B3 `777408ad`; B3A `?`), S5 semente 1010 (B0/B1/B2/B3 `777408ad`; B3A `?`), S6 semente 1001 (B0/B1/B2/B3 `63b3fb97`; B3A `?`), S6 semente 1002 (B0/B1/B2/B3 `63b3fb97`; B3A `?`), S6 semente 1003 (B0/B1/B2/B3 `63b3fb97`; B3A `?`), S6 semente 1004 (B0/B1/B2/B3 `63b3fb97`; B3A `?`), S6 semente 1005 (B0/B1/B2/B3 `63b3fb97`; B3A `?`), S7 semente 1001 (B0/B3 `d40477f2`; B1/B2 `881dd752`; B3A `?`), S7 semente 1002 (B0/B1/B2/B3 `881dd752`; B3A `?`), S7 semente 1003 (B0/B1/B2/B3 `881dd752`; B3A `?`), S7 semente 1004 (B0/B1/B2/B3 `881dd752`; B3A `?`), S7 semente 1005 (B0/B1/B2/B3 `881dd752`; B3A `?`), S9 semente 9101 (B0/B3 `70498fc4`; B1/B2/B3A `?`), S9 semente 11001 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S9 semente 11002 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S9 semente 11003 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S9 semente 11004 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S9 semente 11005 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S10 semente 9101 (B0/B3 `70498fc4`; B1/B2/B3A `?`), S10 semente 11001 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S10 semente 11002 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S10 semente 11003 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S10 semente 11004 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S10 semente 11005 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S11 semente 9101 (B0/B3 `70498fc4`; B1/B2/B3A `?`), S11 semente 11001 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S11 semente 11002 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S11 semente 11003 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S11 semente 11004 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S11 semente 11005 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S12 semente 9101 (B0/B3 `70498fc4`; B1/B2/B3A `?`), S12 semente 9102 (B0/B3 `70498fc4`; B1/B2/B3A `?`), S12 semente 11001 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S12 semente 11002 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S12 semente 11003 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S12 semente 11004 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S12 semente 11005 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S13 semente 9101 (B0/B3 `70498fc4`; B1/B2/B3A `?`), S13 semente 11001 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S13 semente 11002 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S13 semente 11003 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S13 semente 11004 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S13 semente 11005 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S13 semente 12001 (B0/B1/B2 `?`; B3/B3A `70498fc4`), S13 semente 12002 (B0/B1/B2 `?`; B3/B3A `70498fc4`), S13 semente 12003 (B0/B1/B2 `?`; B3/B3A `70498fc4`), S13 semente 12004 (B0/B1/B2 `?`; B3/B3A `70498fc4`), S13 semente 12005 (B0/B1/B2 `?`; B3/B3A `70498fc4`), S14 semente 9101 (B0/B3 `70498fc4`; B1/B2/B3A `?`), S14 semente 9102 (B0/B3 `70498fc4`; B1/B2/B3A `?`), S15 semente 9101 (B0/B3 `70498fc4`; B1/B2/B3A `?`), S15 semente 11001 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S15 semente 11002 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S15 semente 11003 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S15 semente 11004 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S15 semente 11005 (B0/B1/B2/B3 `70498fc4`; B3A `?`), S15 semente 12001 (B0/B1/B2 `?`; B3/B3A `70498fc4`), S15 semente 12002 (B0/B1/B2 `?`; B3/B3A `70498fc4`), S15 semente 12003 (B0/B1/B2 `?`; B3/B3A `70498fc4`), S15 semente 12004 (B0/B1/B2 `?`; B3/B3A `70498fc4`), S15 semente 12005 (B0/B1/B2 `?`; B3/B3A `70498fc4`). A mudança entre as versões (opção `--disableSrs`, desligada por padrão, e escalonamento de handover) não afeta cenários sem `HANDOVER` no cronograma.

Execuções com falha preservadas em `experiments/runs_failed/` (não entram na análise):

| Execução | Status | Motivo (stderr) |
| :-- | :-- | :-- |
| `nori_S3_B3_smoke_seed9003__sem_rota_e2_20261109` | SUCCESS | exit_code 0; stderr vazio; última saída: `========================================================` (execução interrompida) |
| `nori_S8_B2_seed5029__interrompida_20261109` | ? | exit_code None; stderr vazio; última saída: `========================================================` (execução interrompida) |
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
# nr_G1_B0_seed11001  (SUCCESS, 2026-11-12T15:20:10Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_G1_B0_seed11001/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B0_seed11002  (SUCCESS, 2026-11-12T20:16:09Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_G1_B0_seed11002/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B0_seed11003  (SUCCESS, 2026-11-13T00:15:21Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_G1_B0_seed11003/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B0_seed11004  (SUCCESS, 2026-11-13T02:36:15Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_G1_B0_seed11004/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B0_seed11005  (SUCCESS, 2026-11-13T05:02:35Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_G1_B0_seed11005/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B0_seed9101  (SUCCESS, 2026-11-11T01:53:15Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_G1_B0_seed9101/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
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
# nr_G1_B1_seed11001  (SUCCESS, 2026-11-12T15:20:42Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_G1_B1_seed11001/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B1_seed11002  (SUCCESS, 2026-11-12T20:17:05Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_G1_B1_seed11002/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B1_seed11003  (SUCCESS, 2026-11-13T00:16:03Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_G1_B1_seed11003/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B1_seed11004  (SUCCESS, 2026-11-13T02:36:32Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_G1_B1_seed11004/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B1_seed11005  (SUCCESS, 2026-11-13T05:03:42Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_G1_B1_seed11005/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
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
# nr_G1_B2_seed11001  (SUCCESS, 2026-11-12T15:25:26Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_G1_B2_seed11001/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B2_seed11002  (SUCCESS, 2026-11-12T21:48:47Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_G1_B2_seed11002/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B2_seed11003  (SUCCESS, 2026-11-13T00:20:31Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_G1_B2_seed11003/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B2_seed11004  (SUCCESS, 2026-11-13T02:41:14Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_G1_B2_seed11004/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B2_seed11005  (SUCCESS, 2026-11-13T05:07:31Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_G1_B2_seed11005/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
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
# nr_G1_B3_seed11001  (SUCCESS, 2026-11-12T15:26:03Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_G1_B3_seed11001/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B3_seed11002  (SUCCESS, 2026-11-12T21:48:49Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_G1_B3_seed11002/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B3_seed11003  (SUCCESS, 2026-11-13T00:21:04Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_G1_B3_seed11003/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B3_seed11004  (SUCCESS, 2026-11-13T02:41:43Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_G1_B3_seed11004/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B3_seed11005  (SUCCESS, 2026-11-13T05:08:51Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_G1_B3_seed11005/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
# nr_G1_B3_seed9101  (SUCCESS, 2026-11-11T01:53:27Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_G1_B3_seed9101/raw/action_schedule.csv --simTime=30 --channel=UMi --bandwidth=20e6 --gnbs=0,0,10;150,0,10 --ueGroups=6,0,0,20,60,2,0,0,3;30,75,0,10,120,1000,0,0,1.5 --packetSize=1250'
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
# nr_G2_B0_seed11001  (SUCCESS, 2026-11-12T15:30:47Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_G2_B0_seed11001/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B0_seed11002  (SUCCESS, 2026-11-12T21:54:48Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_G2_B0_seed11002/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B0_seed11003  (SUCCESS, 2026-11-13T00:25:45Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_G2_B0_seed11003/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B0_seed11004  (SUCCESS, 2026-11-13T02:46:17Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_G2_B0_seed11004/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B0_seed11005  (SUCCESS, 2026-11-13T05:12:34Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_G2_B0_seed11005/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B0_seed9101  (SUCCESS, 2026-11-11T01:59:52Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_G2_B0_seed9101/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
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
# nr_G2_B1_seed11001  (SUCCESS, 2026-11-12T15:31:32Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_G2_B1_seed11001/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B1_seed11002  (SUCCESS, 2026-11-12T21:54:49Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_G2_B1_seed11002/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B1_seed11003  (SUCCESS, 2026-11-13T00:26:14Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_G2_B1_seed11003/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B1_seed11004  (SUCCESS, 2026-11-13T02:46:58Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_G2_B1_seed11004/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B1_seed11005  (SUCCESS, 2026-11-13T05:13:14Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_G2_B1_seed11005/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
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
# nr_G2_B2_seed11001  (SUCCESS, 2026-11-12T15:31:34Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_G2_B2_seed11001/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B2_seed11002  (SUCCESS, 2026-11-12T21:55:41Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_G2_B2_seed11002/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B2_seed11003  (SUCCESS, 2026-11-13T00:26:26Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_G2_B2_seed11003/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B2_seed11004  (SUCCESS, 2026-11-13T02:46:59Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_G2_B2_seed11004/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B2_seed11005  (SUCCESS, 2026-11-13T05:13:56Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_G2_B2_seed11005/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
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
# nr_G2_B3_seed11001  (SUCCESS, 2026-11-12T15:32:19Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_G2_B3_seed11001/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B3_seed11002  (SUCCESS, 2026-11-12T21:55:47Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_G2_B3_seed11002/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B3_seed11003  (SUCCESS, 2026-11-13T00:26:55Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_G2_B3_seed11003/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B3_seed11004  (SUCCESS, 2026-11-13T02:47:43Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_G2_B3_seed11004/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B3_seed11005  (SUCCESS, 2026-11-13T05:14:03Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_G2_B3_seed11005/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
# nr_G2_B3_seed9101  (SUCCESS, 2026-11-11T01:59:59Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_G2_B3_seed9101/raw/action_schedule.csv --simTime=30 --channel=UMi --gnbs=0,0,10;150,0,10 --ueGroups=10,75,0,0,30,50,0,0,1.5;4,0,0,10,40,200,0,0,1.5'
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
# nr_S2_B3_seed12001  (SUCCESS, 2026-11-11T15:11:28Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=12001 --actionSchedule=<repo>/experiments/runs/nr_S2_B3_seed12001/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3_seed12002  (SUCCESS, 2026-11-11T15:43:00Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=12002 --actionSchedule=<repo>/experiments/runs/nr_S2_B3_seed12002/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3_seed12003  (SUCCESS, 2026-11-11T16:13:49Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=12003 --actionSchedule=<repo>/experiments/runs/nr_S2_B3_seed12003/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3_seed12004  (SUCCESS, 2026-11-12T01:04:24Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=12004 --actionSchedule=<repo>/experiments/runs/nr_S2_B3_seed12004/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3_seed12005  (SUCCESS, 2026-11-12T01:39:08Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=12005 --actionSchedule=<repo>/experiments/runs/nr_S2_B3_seed12005/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3A_seed12001  (SUCCESS, 2026-11-11T15:11:28Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=12001 --actionSchedule=<repo>/experiments/runs/nr_S2_B3A_seed12001/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3A_seed12002  (SUCCESS, 2026-11-11T15:44:03Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=12002 --actionSchedule=<repo>/experiments/runs/nr_S2_B3A_seed12002/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3A_seed12003  (SUCCESS, 2026-11-11T16:14:22Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=12003 --actionSchedule=<repo>/experiments/runs/nr_S2_B3A_seed12003/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3A_seed12004  (SUCCESS, 2026-11-12T01:04:37Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=12004 --actionSchedule=<repo>/experiments/runs/nr_S2_B3A_seed12004/raw/action_schedule.csv --simTime=20 --disableSrs=true'
# nr_S2_B3A_seed12005  (SUCCESS, 2026-11-12T01:40:17Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_tvs_conflict --seed=12005 --actionSchedule=<repo>/experiments/runs/nr_S2_B3A_seed12005/raw/action_schedule.csv --simTime=20 --disableSrs=true'
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
# nr_S4_B0_seed1006  (SUCCESS, 2026-11-10T20:43:45Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1006 --actionSchedule=<repo>/experiments/runs/nr_S4_B0_seed1006/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B0_seed1007  (SUCCESS, 2026-11-10T21:00:52Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1007 --actionSchedule=<repo>/experiments/runs/nr_S4_B0_seed1007/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B0_seed1008  (SUCCESS, 2026-11-10T21:18:00Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1008 --actionSchedule=<repo>/experiments/runs/nr_S4_B0_seed1008/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B0_seed1009  (SUCCESS, 2026-11-10T21:38:55Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1009 --actionSchedule=<repo>/experiments/runs/nr_S4_B0_seed1009/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B0_seed1010  (SUCCESS, 2026-11-10T22:09:53Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1010 --actionSchedule=<repo>/experiments/runs/nr_S4_B0_seed1010/raw/action_schedule.csv --simTime=30 --disableSrs=true'
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
# nr_S4_B1_seed1006  (SUCCESS, 2026-11-10T20:43:45Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1006 --actionSchedule=<repo>/experiments/runs/nr_S4_B1_seed1006/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B1_seed1007  (SUCCESS, 2026-11-10T21:01:03Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1007 --actionSchedule=<repo>/experiments/runs/nr_S4_B1_seed1007/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B1_seed1008  (SUCCESS, 2026-11-10T21:18:13Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1008 --actionSchedule=<repo>/experiments/runs/nr_S4_B1_seed1008/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B1_seed1009  (SUCCESS, 2026-11-10T21:39:17Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1009 --actionSchedule=<repo>/experiments/runs/nr_S4_B1_seed1009/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B1_seed1010  (SUCCESS, 2026-11-10T22:09:55Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1010 --actionSchedule=<repo>/experiments/runs/nr_S4_B1_seed1010/raw/action_schedule.csv --simTime=30 --disableSrs=true'
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
# nr_S4_B2_seed1006  (SUCCESS, 2026-11-10T20:50:27Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1006 --actionSchedule=<repo>/experiments/runs/nr_S4_B2_seed1006/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B2_seed1007  (SUCCESS, 2026-11-10T21:05:56Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1007 --actionSchedule=<repo>/experiments/runs/nr_S4_B2_seed1007/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B2_seed1008  (SUCCESS, 2026-11-10T21:25:14Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1008 --actionSchedule=<repo>/experiments/runs/nr_S4_B2_seed1008/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B2_seed1009  (SUCCESS, 2026-11-10T21:49:21Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1009 --actionSchedule=<repo>/experiments/runs/nr_S4_B2_seed1009/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B2_seed1010  (SUCCESS, 2026-11-10T22:13:33Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1010 --actionSchedule=<repo>/experiments/runs/nr_S4_B2_seed1010/raw/action_schedule.csv --simTime=30 --disableSrs=true'
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
# nr_S4_B3_seed1006  (SUCCESS, 2026-11-10T20:50:39Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1006 --actionSchedule=<repo>/experiments/runs/nr_S4_B3_seed1006/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B3_seed1007  (SUCCESS, 2026-11-10T21:06:11Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1007 --actionSchedule=<repo>/experiments/runs/nr_S4_B3_seed1007/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B3_seed1008  (SUCCESS, 2026-11-10T21:25:32Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1008 --actionSchedule=<repo>/experiments/runs/nr_S4_B3_seed1008/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B3_seed1009  (SUCCESS, 2026-11-10T21:49:42Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1009 --actionSchedule=<repo>/experiments/runs/nr_S4_B3_seed1009/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S4_B3_seed1010  (SUCCESS, 2026-11-10T22:13:34Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_ts_vs_energy --seed=1010 --actionSchedule=<repo>/experiments/runs/nr_S4_B3_seed1010/raw/action_schedule.csv --simTime=30 --disableSrs=true'
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
# nr_S5_B0_seed1006  (SUCCESS, 2026-11-10T20:55:22Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1006 --actionSchedule=<repo>/experiments/runs/nr_S5_B0_seed1006/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B0_seed1007  (SUCCESS, 2026-11-10T21:12:23Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1007 --actionSchedule=<repo>/experiments/runs/nr_S5_B0_seed1007/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B0_seed1008  (SUCCESS, 2026-11-10T21:32:23Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1008 --actionSchedule=<repo>/experiments/runs/nr_S5_B0_seed1008/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B0_seed1009  (SUCCESS, 2026-11-10T22:05:10Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1009 --actionSchedule=<repo>/experiments/runs/nr_S5_B0_seed1009/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B0_seed1010  (SUCCESS, 2026-11-10T22:16:46Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1010 --actionSchedule=<repo>/experiments/runs/nr_S5_B0_seed1010/raw/action_schedule.csv --simTime=30 --disableSrs=true'
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
# nr_S5_B1_seed1006  (SUCCESS, 2026-11-10T20:55:37Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1006 --actionSchedule=<repo>/experiments/runs/nr_S5_B1_seed1006/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B1_seed1007  (SUCCESS, 2026-11-10T21:12:39Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1007 --actionSchedule=<repo>/experiments/runs/nr_S5_B1_seed1007/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B1_seed1008  (SUCCESS, 2026-11-10T21:32:40Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1008 --actionSchedule=<repo>/experiments/runs/nr_S5_B1_seed1008/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B1_seed1009  (SUCCESS, 2026-11-10T22:05:26Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1009 --actionSchedule=<repo>/experiments/runs/nr_S5_B1_seed1009/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B1_seed1010  (SUCCESS, 2026-11-10T22:16:48Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1010 --actionSchedule=<repo>/experiments/runs/nr_S5_B1_seed1010/raw/action_schedule.csv --simTime=30 --disableSrs=true'
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
# nr_S5_B2_seed1006  (SUCCESS, 2026-11-10T20:58:11Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1006 --actionSchedule=<repo>/experiments/runs/nr_S5_B2_seed1006/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B2_seed1007  (SUCCESS, 2026-11-10T21:15:26Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1007 --actionSchedule=<repo>/experiments/runs/nr_S5_B2_seed1007/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B2_seed1008  (SUCCESS, 2026-11-10T21:35:47Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1008 --actionSchedule=<repo>/experiments/runs/nr_S5_B2_seed1008/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B2_seed1009  (SUCCESS, 2026-11-10T22:07:43Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1009 --actionSchedule=<repo>/experiments/runs/nr_S5_B2_seed1009/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B2_seed1010  (SUCCESS, 2026-11-10T22:19:09Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1010 --actionSchedule=<repo>/experiments/runs/nr_S5_B2_seed1010/raw/action_schedule.csv --simTime=30 --disableSrs=true'
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
# nr_S5_B3_seed1006  (SUCCESS, 2026-11-10T20:58:30Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1006 --actionSchedule=<repo>/experiments/runs/nr_S5_B3_seed1006/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B3_seed1007  (SUCCESS, 2026-11-10T21:15:43Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1007 --actionSchedule=<repo>/experiments/runs/nr_S5_B3_seed1007/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B3_seed1008  (SUCCESS, 2026-11-10T21:36:05Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1008 --actionSchedule=<repo>/experiments/runs/nr_S5_B3_seed1008/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B3_seed1009  (SUCCESS, 2026-11-10T22:08:01Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1009 --actionSchedule=<repo>/experiments/runs/nr_S5_B3_seed1009/raw/action_schedule.csv --simTime=30 --disableSrs=true'
# nr_S5_B3_seed1010  (SUCCESS, 2026-11-10T22:19:12Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_temporal_pingpong --seed=1010 --actionSchedule=<repo>/experiments/runs/nr_S5_B3_seed1010/raw/action_schedule.csv --simTime=30 --disableSrs=true'
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
# nr_S9_B0_seed11001  (SUCCESS, 2026-11-12T13:03:33Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S9_B0_seed11001/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B0_seed11002  (SUCCESS, 2026-11-12T15:32:19Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S9_B0_seed11002/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B0_seed11003  (SUCCESS, 2026-11-12T21:56:36Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S9_B0_seed11003/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B0_seed11004  (SUCCESS, 2026-11-13T00:27:07Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S9_B0_seed11004/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B0_seed11005  (SUCCESS, 2026-11-13T02:47:42Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S9_B0_seed11005/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B0_seed9101  (SUCCESS, 2026-11-10T23:51:12Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S9_B0_seed9101/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B1_seed11001  (SUCCESS, 2026-11-12T13:03:33Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S9_B1_seed11001/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B1_seed11002  (SUCCESS, 2026-11-12T15:33:05Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S9_B1_seed11002/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B1_seed11003  (SUCCESS, 2026-11-12T21:56:36Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S9_B1_seed11003/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B1_seed11004  (SUCCESS, 2026-11-13T00:27:39Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S9_B1_seed11004/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B1_seed11005  (SUCCESS, 2026-11-13T02:48:31Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S9_B1_seed11005/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B2_seed11001  (SUCCESS, 2026-11-12T13:04:56Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S9_B2_seed11001/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B2_seed11002  (SUCCESS, 2026-11-12T15:33:29Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S9_B2_seed11002/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B2_seed11003  (SUCCESS, 2026-11-12T21:57:52Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S9_B2_seed11003/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B2_seed11004  (SUCCESS, 2026-11-13T00:28:25Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S9_B2_seed11004/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B2_seed11005  (SUCCESS, 2026-11-13T02:48:59Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S9_B2_seed11005/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B3_seed11001  (SUCCESS, 2026-11-12T13:04:59Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S9_B3_seed11001/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B3_seed11002  (SUCCESS, 2026-11-12T15:34:16Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S9_B3_seed11002/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B3_seed11003  (SUCCESS, 2026-11-12T21:57:54Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S9_B3_seed11003/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B3_seed11004  (SUCCESS, 2026-11-13T00:28:54Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S9_B3_seed11004/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B3_seed11005  (SUCCESS, 2026-11-13T02:49:48Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S9_B3_seed11005/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S9_B3_seed9101  (SUCCESS, 2026-11-10T23:51:14Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S9_B3_seed9101/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S10_B0_seed11001  (SUCCESS, 2026-11-12T13:06:35Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S10_B0_seed11001/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B0_seed11002  (SUCCESS, 2026-11-12T15:34:40Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S10_B0_seed11002/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B0_seed11003  (SUCCESS, 2026-11-12T21:59:10Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S10_B0_seed11003/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B0_seed11004  (SUCCESS, 2026-11-13T00:29:43Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S10_B0_seed11004/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B0_seed11005  (SUCCESS, 2026-11-13T02:50:13Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S10_B0_seed11005/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B0_seed9101  (SUCCESS, 2026-11-10T23:52:46Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S10_B0_seed9101/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B1_seed11001  (SUCCESS, 2026-11-12T13:06:40Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S10_B1_seed11001/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B1_seed11002  (SUCCESS, 2026-11-12T15:35:29Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S10_B1_seed11002/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B1_seed11003  (SUCCESS, 2026-11-12T21:59:16Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S10_B1_seed11003/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B1_seed11004  (SUCCESS, 2026-11-13T00:30:24Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S10_B1_seed11004/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B1_seed11005  (SUCCESS, 2026-11-13T02:51:13Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S10_B1_seed11005/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B2_seed11001  (SUCCESS, 2026-11-12T13:30:46Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S10_B2_seed11001/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B2_seed11002  (SUCCESS, 2026-11-12T16:01:13Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S10_B2_seed11002/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B2_seed11003  (SUCCESS, 2026-11-12T22:22:18Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S10_B2_seed11003/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B2_seed11004  (SUCCESS, 2026-11-13T00:51:53Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S10_B2_seed11004/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B2_seed11005  (SUCCESS, 2026-11-13T03:12:33Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S10_B2_seed11005/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B3_seed11001  (SUCCESS, 2026-11-12T13:30:50Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S10_B3_seed11001/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B3_seed11002  (SUCCESS, 2026-11-12T16:02:13Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S10_B3_seed11002/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B3_seed11003  (SUCCESS, 2026-11-12T22:22:20Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S10_B3_seed11003/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B3_seed11004  (SUCCESS, 2026-11-13T00:52:10Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S10_B3_seed11004/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B3_seed11005  (SUCCESS, 2026-11-13T03:13:23Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S10_B3_seed11005/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S10_B3_seed9101  (SUCCESS, 2026-11-10T23:52:50Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S10_B3_seed9101/raw/action_schedule.csv --simTime=30 --channel=UMa --gnbs=0,0,25;300,0,100 --ueGroups=30,0,0,10,120,8,0,0,1.5;10,300,0,10,120,20,0,0,1.5'
# nr_S11_B0_seed11001  (SUCCESS, 2026-11-12T13:53:15Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S11_B0_seed11001/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B0_seed11002  (SUCCESS, 2026-11-12T16:26:00Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S11_B0_seed11002/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B0_seed11003  (SUCCESS, 2026-11-12T22:45:27Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S11_B0_seed11003/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B0_seed11004  (SUCCESS, 2026-11-13T01:13:39Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S11_B0_seed11004/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B0_seed11005  (SUCCESS, 2026-11-13T03:35:10Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S11_B0_seed11005/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B0_seed9101  (SUCCESS, 2026-11-11T00:17:07Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S11_B0_seed9101/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B1_seed11001  (SUCCESS, 2026-11-12T13:55:14Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S11_B1_seed11001/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B1_seed11002  (SUCCESS, 2026-11-12T16:31:15Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S11_B1_seed11002/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B1_seed11003  (SUCCESS, 2026-11-12T22:47:22Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S11_B1_seed11003/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B1_seed11004  (SUCCESS, 2026-11-13T01:16:59Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S11_B1_seed11004/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B1_seed11005  (SUCCESS, 2026-11-13T03:39:22Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S11_B1_seed11005/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B2_seed11001  (SUCCESS, 2026-11-12T14:03:08Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S11_B2_seed11001/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B2_seed11002  (SUCCESS, 2026-11-12T16:39:05Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S11_B2_seed11002/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B2_seed11003  (SUCCESS, 2026-11-12T22:55:45Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S11_B2_seed11003/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B2_seed11004  (SUCCESS, 2026-11-13T01:23:17Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S11_B2_seed11004/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B2_seed11005  (SUCCESS, 2026-11-13T03:45:02Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S11_B2_seed11005/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B3_seed11001  (SUCCESS, 2026-11-12T14:05:01Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S11_B3_seed11001/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B3_seed11002  (SUCCESS, 2026-11-12T16:44:06Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S11_B3_seed11002/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B3_seed11003  (SUCCESS, 2026-11-12T22:57:33Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S11_B3_seed11003/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B3_seed11004  (SUCCESS, 2026-11-13T01:26:45Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S11_B3_seed11004/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B3_seed11005  (SUCCESS, 2026-11-13T03:49:41Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S11_B3_seed11005/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S11_B3_seed9101  (SUCCESS, 2026-11-11T00:20:33Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S11_B3_seed9101/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,35;600,0,35;1200,0,35 --ueGroups=20,0,0,0,50,10,33,0,1.5;10,1200,0,10,100,20,0,0,1.5'
# nr_S12_B0_seed11001  (SUCCESS, 2026-11-12T14:14:08Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S12_B0_seed11001/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B0_seed11002  (SUCCESS, 2026-11-12T16:51:33Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S12_B0_seed11002/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B0_seed11003  (SUCCESS, 2026-11-12T23:05:41Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S12_B0_seed11003/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B0_seed11004  (SUCCESS, 2026-11-13T01:32:58Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S12_B0_seed11004/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B0_seed11005  (SUCCESS, 2026-11-13T03:55:04Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S12_B0_seed11005/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B0_seed9101  (SUCCESS, 2026-11-11T00:28:29Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S12_B0_seed9101/raw/action_schedule.csv --simTime=25 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B0_seed9102  (SUCCESS, 2026-11-11T14:43:28Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9102 --actionSchedule=<repo>/experiments/runs/nr_S12_B0_seed9102/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B1_seed11001  (SUCCESS, 2026-11-12T14:15:36Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S12_B1_seed11001/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B1_seed11002  (SUCCESS, 2026-11-12T16:55:17Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S12_B1_seed11002/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B1_seed11003  (SUCCESS, 2026-11-12T23:07:05Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S12_B1_seed11003/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B1_seed11004  (SUCCESS, 2026-11-13T01:35:59Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S12_B1_seed11004/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B1_seed11005  (SUCCESS, 2026-11-13T03:59:13Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S12_B1_seed11005/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B2_seed11001  (SUCCESS, 2026-11-12T14:22:47Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S12_B2_seed11001/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B2_seed11002  (SUCCESS, 2026-11-12T17:00:49Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S12_B2_seed11002/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B2_seed11003  (SUCCESS, 2026-11-12T23:13:27Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S12_B2_seed11003/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B2_seed11004  (SUCCESS, 2026-11-13T01:40:53Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S12_B2_seed11004/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B2_seed11005  (SUCCESS, 2026-11-13T04:03:04Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S12_B2_seed11005/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B3_seed11001  (SUCCESS, 2026-11-12T14:23:43Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S12_B3_seed11001/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B3_seed11002  (SUCCESS, 2026-11-12T17:04:28Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S12_B3_seed11002/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B3_seed11003  (SUCCESS, 2026-11-12T23:15:06Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S12_B3_seed11003/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B3_seed11004  (SUCCESS, 2026-11-13T01:43:46Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S12_B3_seed11004/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B3_seed11005  (SUCCESS, 2026-11-13T04:07:18Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S12_B3_seed11005/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B3_seed9101  (SUCCESS, 2026-11-11T00:31:02Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S12_B3_seed9101/raw/action_schedule.csv --simTime=25 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S12_B3_seed9102  (SUCCESS, 2026-11-11T14:43:31Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9102 --actionSchedule=<repo>/experiments/runs/nr_S12_B3_seed9102/raw/action_schedule.csv --simTime=25 --bandwidth=10e6 --channel=InH-OfficeMixed --gnbs=0,0,3 --ueGroups=20,0,0,2,30,2,0,0,1.0;10,0,0,2,30,1,0,0,1.0 --packetSize=128'
# nr_S13_B0_seed11001  (SUCCESS, 2026-11-12T14:30:56Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S13_B0_seed11001/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B0_seed11002  (SUCCESS, 2026-11-12T17:09:38Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S13_B0_seed11002/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B0_seed11003  (SUCCESS, 2026-11-12T23:21:03Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S13_B0_seed11003/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B0_seed11004  (SUCCESS, 2026-11-13T01:48:33Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S13_B0_seed11004/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B0_seed11005  (SUCCESS, 2026-11-13T04:10:57Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S13_B0_seed11005/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B0_seed9101  (SUCCESS, 2026-11-11T01:05:25Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S13_B0_seed9101/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B1_seed11001  (SUCCESS, 2026-11-12T14:31:56Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S13_B1_seed11001/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B1_seed11002  (SUCCESS, 2026-11-12T17:12:49Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S13_B1_seed11002/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B1_seed11003  (SUCCESS, 2026-11-12T23:22:58Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S13_B1_seed11003/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B1_seed11004  (SUCCESS, 2026-11-13T01:51:39Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S13_B1_seed11004/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B1_seed11005  (SUCCESS, 2026-11-13T04:15:29Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S13_B1_seed11005/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B2_seed11001  (SUCCESS, 2026-11-12T14:54:55Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S13_B2_seed11001/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B2_seed11002  (SUCCESS, 2026-11-12T17:34:22Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S13_B2_seed11002/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B2_seed11003  (SUCCESS, 2026-11-12T23:48:22Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S13_B2_seed11003/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B2_seed11004  (SUCCESS, 2026-11-13T02:10:43Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S13_B2_seed11004/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B2_seed11005  (SUCCESS, 2026-11-13T04:35:51Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S13_B2_seed11005/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3_seed11001  (SUCCESS, 2026-11-12T14:56:06Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S13_B3_seed11001/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3_seed11002  (SUCCESS, 2026-11-12T17:37:34Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S13_B3_seed11002/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3_seed11003  (SUCCESS, 2026-11-12T23:50:31Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S13_B3_seed11003/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3_seed11004  (SUCCESS, 2026-11-13T02:13:54Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S13_B3_seed11004/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3_seed11005  (SUCCESS, 2026-11-13T04:39:46Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S13_B3_seed11005/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3_seed12001  (SUCCESS, 2026-11-11T15:16:59Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12001 --actionSchedule=<repo>/experiments/runs/nr_S13_B3_seed12001/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3_seed12002  (SUCCESS, 2026-11-11T15:48:51Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12002 --actionSchedule=<repo>/experiments/runs/nr_S13_B3_seed12002/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3_seed12003  (SUCCESS, 2026-11-11T16:18:46Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12003 --actionSchedule=<repo>/experiments/runs/nr_S13_B3_seed12003/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3_seed12004  (SUCCESS, 2026-11-12T01:11:36Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12004 --actionSchedule=<repo>/experiments/runs/nr_S13_B3_seed12004/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3_seed12005  (SUCCESS, 2026-11-12T01:47:41Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12005 --actionSchedule=<repo>/experiments/runs/nr_S13_B3_seed12005/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3_seed9101  (SUCCESS, 2026-11-11T01:08:34Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S13_B3_seed9101/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3A_seed12001  (SUCCESS, 2026-11-11T15:17:19Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12001 --actionSchedule=<repo>/experiments/runs/nr_S13_B3A_seed12001/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3A_seed12002  (SUCCESS, 2026-11-11T15:49:33Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12002 --actionSchedule=<repo>/experiments/runs/nr_S13_B3A_seed12002/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3A_seed12003  (SUCCESS, 2026-11-11T16:19:25Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12003 --actionSchedule=<repo>/experiments/runs/nr_S13_B3A_seed12003/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3A_seed12004  (SUCCESS, 2026-11-12T01:11:41Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12004 --actionSchedule=<repo>/experiments/runs/nr_S13_B3A_seed12004/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S13_B3A_seed12005  (SUCCESS, 2026-11-12T01:48:35Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12005 --actionSchedule=<repo>/experiments/runs/nr_S13_B3A_seed12005/raw/action_schedule.csv --simTime=30 --channel=RMa --gnbs=0,0,30;800,0,30;400,700,30 --ueGroups=25,0,0,10,300,10,0,0,1.5;15,800,0,10,300,20,0,0,1.5;10,400,700,10,300,20,0,0,1.5'
# nr_S14_B0_seed9101  (SUCCESS, 2026-11-11T01:32:00Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S14_B0_seed9101/raw/action_schedule.csv --simTime=25 --channel=UMi --gnbs=0,0,10 --ueGroups=30,0,0,10,100,5,0,0,1.5'
# nr_S14_B0_seed9102  (SUCCESS, 2026-11-11T14:54:09Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9102 --actionSchedule=<repo>/experiments/runs/nr_S14_B0_seed9102/raw/action_schedule.csv --simTime=25 --bandwidth=50e6 --channel=UMi --gnbs=0,0,10 --ueGroups=30,0,0,10,100,5,0,0,1.5'
# nr_S14_B3_seed9101  (SUCCESS, 2026-11-11T01:32:16Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S14_B3_seed9101/raw/action_schedule.csv --simTime=25 --channel=UMi --gnbs=0,0,10 --ueGroups=30,0,0,10,100,5,0,0,1.5'
# nr_S14_B3_seed9102  (SUCCESS, 2026-11-11T14:54:31Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9102 --actionSchedule=<repo>/experiments/runs/nr_S14_B3_seed9102/raw/action_schedule.csv --simTime=25 --bandwidth=50e6 --channel=UMi --gnbs=0,0,10 --ueGroups=30,0,0,10,100,5,0,0,1.5'
# nr_S15_B0_seed11001  (SUCCESS, 2026-11-12T15:17:41Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S15_B0_seed11001/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B0_seed11002  (SUCCESS, 2026-11-12T20:11:32Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S15_B0_seed11002/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B0_seed11003  (SUCCESS, 2026-11-13T00:11:31Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S15_B0_seed11003/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B0_seed11004  (SUCCESS, 2026-11-13T02:32:39Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S15_B0_seed11004/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B0_seed11005  (SUCCESS, 2026-11-13T05:00:05Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S15_B0_seed11005/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B0_seed9101  (SUCCESS, 2026-11-11T01:51:28Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S15_B0_seed9101/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B1_seed11001  (SUCCESS, 2026-11-12T15:18:01Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S15_B1_seed11001/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B1_seed11002  (SUCCESS, 2026-11-12T20:13:12Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S15_B1_seed11002/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B1_seed11003  (SUCCESS, 2026-11-13T00:12:46Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S15_B1_seed11003/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B1_seed11004  (SUCCESS, 2026-11-13T02:33:49Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S15_B1_seed11004/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B1_seed11005  (SUCCESS, 2026-11-13T05:00:55Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S15_B1_seed11005/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B2_seed11001  (SUCCESS, 2026-11-12T15:18:53Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S15_B2_seed11001/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B2_seed11002  (SUCCESS, 2026-11-12T20:14:16Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S15_B2_seed11002/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B2_seed11003  (SUCCESS, 2026-11-13T00:14:03Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S15_B2_seed11003/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B2_seed11004  (SUCCESS, 2026-11-13T02:35:00Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S15_B2_seed11004/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B2_seed11005  (SUCCESS, 2026-11-13T05:01:17Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S15_B2_seed11005/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3_seed11001  (SUCCESS, 2026-11-12T15:19:20Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11001 --actionSchedule=<repo>/experiments/runs/nr_S15_B3_seed11001/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3_seed11002  (SUCCESS, 2026-11-12T20:14:59Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11002 --actionSchedule=<repo>/experiments/runs/nr_S15_B3_seed11002/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3_seed11003  (SUCCESS, 2026-11-13T00:14:39Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11003 --actionSchedule=<repo>/experiments/runs/nr_S15_B3_seed11003/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3_seed11004  (SUCCESS, 2026-11-13T02:35:04Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11004 --actionSchedule=<repo>/experiments/runs/nr_S15_B3_seed11004/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3_seed11005  (SUCCESS, 2026-11-13T05:02:17Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=11005 --actionSchedule=<repo>/experiments/runs/nr_S15_B3_seed11005/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3_seed12001  (SUCCESS, 2026-11-11T15:41:23Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12001 --actionSchedule=<repo>/experiments/runs/nr_S15_B3_seed12001/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3_seed12002  (SUCCESS, 2026-11-11T16:12:20Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12002 --actionSchedule=<repo>/experiments/runs/nr_S15_B3_seed12002/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3_seed12003  (SUCCESS, 2026-11-12T01:02:26Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12003 --actionSchedule=<repo>/experiments/runs/nr_S15_B3_seed12003/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3_seed12004  (SUCCESS, 2026-11-12T01:37:03Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12004 --actionSchedule=<repo>/experiments/runs/nr_S15_B3_seed12004/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3_seed12005  (SUCCESS, 2026-11-12T02:16:08Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12005 --actionSchedule=<repo>/experiments/runs/nr_S15_B3_seed12005/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3_seed9101  (SUCCESS, 2026-11-11T01:51:30Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=9101 --actionSchedule=<repo>/experiments/runs/nr_S15_B3_seed9101/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3A_seed12001  (SUCCESS, 2026-11-11T15:42:33Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12001 --actionSchedule=<repo>/experiments/runs/nr_S15_B3A_seed12001/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3A_seed12002  (SUCCESS, 2026-11-11T16:13:01Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12002 --actionSchedule=<repo>/experiments/runs/nr_S15_B3A_seed12002/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3A_seed12003  (SUCCESS, 2026-11-12T01:02:42Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12003 --actionSchedule=<repo>/experiments/runs/nr_S15_B3A_seed12003/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3A_seed12004  (SUCCESS, 2026-11-12T01:38:11Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12004 --actionSchedule=<repo>/experiments/runs/nr_S15_B3A_seed12004/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
# nr_S15_B3A_seed12005  (SUCCESS, 2026-11-12T02:18:10Z)
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scratch/scenario_rdl_multicell --seed=12005 --actionSchedule=<repo>/experiments/runs/nr_S15_B3A_seed12005/raw/action_schedule.csv --simTime=30 --channel=NTN-Rural --centralFreq=2e9 --bandwidth=20e6 --txPowerDbm=77 --packetSize=200 --gnbs=-1.45,-48.49,600000;-1.10,-48.49,600000 --ueGroups=20,-1.45,-48.49,0,15000,100,0,0,1.5;20,-1.10,-48.49,0,15000,100,0,0,1.5'
```

