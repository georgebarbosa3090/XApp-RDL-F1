# Pré-registro — fase 4, desenho v3: calibração por cotas complementares

Registrado em 2026-11-08, **antes** das execuções descritas aqui, no mesmo commit do código de decisão, de calibração e de análise que elas usam. Qualquer desvio deste roteiro será relatado junto com os resultados.

## 1. Contexto: v1 e v2

- **v1** ([`nori_hrdl_loop_seed1`](../experiments/runs/nori_hrdl_loop_seed1/execution_manifest.json)): a cadeia E2 completa funcionou com o Control decidido pelo H-RDL sobre o KPM_t0 (cotas eMBB 40 / URLLC 60). Nenhuma fatia mudou; efeito `INCONSISTENT`, G4 `NOT_CERTIFIED`.
- **v2** ([pré-registro](07_preregistro_fase4_v2.md), commit `3962e97`): a calibração com tetos 30/30 (soma 60 %) não restringiu nenhuma fatia. A calibração foi inválida e as avaliações não foram rodadas.
- **Observação que motiva a v3:** as três execuções com cotas (80/20, 40/60 e 30/30) combinam com um escalonador que reaproveita os PRBs não usados. O teto só restringiria quando as cotas somam 100 % e não sobra capacidade para redistribuir.

## 2. O que muda na v3

| Item | v2 | v3 |
| :-- | :-- | :-- |
| Calibração | uma execução, tetos 30/30 (soma 60 %), as duas fatias calibradas juntas | duas execuções com cotas que somam 100 %: `nori_cal3070_seed201` (eMBB 30 / URLLC 70) calibra só a eMBB; `nori_cal7030_seed202` (70 / 30) calibra só a URLLC |
| Validade da calibração | as duas fatias caem ≥ 5 % | em cada execução, a fatia com teto de 30 % cai ≥ 5 %; cada fatia recebe exatamente um k |
| Nível calibrado × nível avaliado | — | calibrado a 30 %, avaliado no teto decidido pelo H-RDL (previsão: 20 % na URLLC), o que testa a linearidade fora do ponto de calibração |
| Regra de efeito, constantes, políticas, regra do certificador | — | iguais às da v2 (`slice_effect.py --calibration`, regra `v2-calibrated`) |

As políticas continuam: `xapp-qos-xslice` (prioridade 90) propõe teto eMBB de 25 %, e `xapp-embb-throughput` (prioridade 60) propõe 80 %. A decisão é do H-RDL; a previsão do pipeline real é a política de vazão da eMBB, com cotas eMBB 80 / URLLC 20 (teste `test_real_hrdl_pipeline_resolves_the_direct_conflict`).

## 3. Hipóteses e critérios

- **H4.0 (escalonador):** com cotas que somam 100 %, a fatia de teto 30 % perde ao menos 5 % de vazão. Isso é verificado pela validade das duas calibrações. Se falhar, a hipótese do escalonador que reaproveita PRBs não se sustenta como explicação, e as avaliações não são rodadas.
- **H4.1 (cadeia):** cada execução de avaliação tem, no PCAP, E2 Setup, Subscription, KPM_t0, RIC Control, ACK correlacionado e KPM_t1. O Control tem `decision_source=H_RDL`, os mesmos bytes do registro da xApp e foi disparado pelo KPM_t0. O tshark concorda com o dissecador em todas as mensagens.
- **H4.2 (decisão):** com o KPM_t0 congestionado e as duas fatias presentes, o H-RDL seleciona `xapp-embb-throughput`, com cotas eMBB 80 / URLLC 20.
- **H4.3 (efeito, regra calibrada):** a URLLC fica restrita (teto 20 % < PRB usado estimado − 5 p.p.). Sua vazão deve cair ao menos 5 % e ficar a no máximo 20 % de 20 × k_URLLC. A eMBB (teto 80 %) não pode perder mais que 5 %.

## 4. Procedimento

Bancada NORI com o patch `0001-rc-control-ack` do lock e a variante `nori-rc-slicing-flowmon`, com `--simTime=30 --ns3::E2Interface::E2Periodicity=1 --trafficRate=300Mb/s`. O Control sai depois da 12.ª Indication. Todas as execuções rodam ao vivo, em primeiro plano, com a xApp usando o `src/` deste commit (`scripts/deploy_kpm_probe.sh`).

1. **Calibração:** `nori_cal3070_seed201` (semente 201, `rc.decision: fixed`, cotas `1:30:0:0,2:70:0:0`) e `nori_cal7030_seed202` (semente 202, cotas `1:70:0:0,2:30:0:0`). Depois, `calibrate_slice_capacity.py --complementary --run nori_cal3070_seed201 --run nori_cal7030_seed202 --out experiments/calibration/slice_capacity_v3.json`. Se a calibração for inválida, as avaliações não são rodadas e isso é relatado.
2. **Avaliação:** `nori_hrdl_v3_seed1`, `_seed2` e `_seed3` (sementes 1, 2 e 3), `rc.decision: hrdl`.
3. **Análise:** `scripts/collect_nori_run.sh` (dissecação com tshark e `slice_effect.py --calibration experiments/calibration/slice_capacity_v3.json`) e `scripts/certification/certify_chain.py`.

Constantes da análise: janela de 4 s antes do Control e 4 s depois de 2 s de acomodação; margem de 5 p.p.; queda mínima de 5 %; tolerância de 20 % na previsão.

## 5. Como os resultados serão relatados

- Todas as execuções entram no relatório, inclusive as que falharem ou forem inválidas.
- O efeito causal só é afirmado se as **três** avaliações forem `CONSISTENT`. Com uma ou duas, o relatório diz exatamente isso. O G4 segue a regra do certificador (ao menos uma execução elegível e `CONSISTENT` pela regra calibrada), e o relatório informa quantas cumprem.
- Políticas, constantes e regras não serão ajustadas depois de ver os resultados. Um novo ajuste exige um novo pré-registro.
- Análises exploratórias, rotuladas como tais e sem efeito sobre o G4:
  - a execução v1 (teto 40 % na eMBB) pela regra calibrada;
  - a execução exploratória [`nori_rc_effect_load300_seed1`](../experiments/runs/nori_rc_effect_load300_seed1/execution_manifest.json) (URLLC a 20 %, ~76,5 Mb/s pelo console do cenário, sem série CSV) como comparação com a previsão 20 × k_URLLC.

## 6. Ameaças à validade conhecidas

- **Cenário único:** um gNB, dois UEs a 20 m e 40 m, carga UDP saturada.
- **Calibração:** uma execução por fatia, com modelo linear entre teto e vazão (calibrado a 30 %, usado a 20 %).
- **Limite por UE (~151,5 Mb/s):** pode mascarar ganhos da fatia não restrita; por isso só se exige que ela não perca.
- **Sinal de congestionamento:** vem do `RRU.PrbUsedDl` do nó, que no NORI fica sempre acima dos PRBs disponíveis.
- **Tempo real:** a simulação atrasa em relação ao relógio. A conversão do instante do Control usa a série com os dois relógios.

## 7. Resultado (registrado depois das execuções, 2026-11-08)

O pré-registro foi publicado no commit `7ded3b2`; a xApp rodou o `src/` desse commit.

**H4.0 refutada; calibração inválida; avaliações não executadas.** Nas duas calibrações o Control saiu e foi confirmado (ACK correlacionado, tshark de acordo nas 66 mensagens, 60/60 Indications casadas com a xApp). Mesmo assim, a fatia com teto de 30 % não perdeu vazão em nenhuma das duas, com as cotas somando 100 %:

| Execução | Cotas eMBB / URLLC | Fatia de teto 30 % | Vazão antes → depois |
| :-- | :-- | :-- | :-- |
| [`nori_cal3070_seed201`](../experiments/runs/nori_cal3070_seed201/execution_manifest.json) | 30 / 70 | eMBB | 151,49 → 151,49 Mb/s |
| [`nori_cal7030_seed202`](../experiments/runs/nori_cal7030_seed202/execution_manifest.json) | 70 / 30 | URLLC | 151,49 → 151,49 Mb/s |

[`slice_capacity_v3.json`](../experiments/calibration/slice_capacity_v3.json) registra `valid: false`. Conforme a seção 4, passo 1, as execuções `nori_hrdl_v3_seed1..3` **não foram rodadas**, e as análises exploratórias da seção 5 ficaram sem calibração.

**Todas as configurações de cota observadas** (300 Mb/s por UE, mesma bancada):

| Cotas eMBB / URLLC | Soma | eMBB | URLLC | Fonte |
| :-- | --: | :-- | :-- | :-- |
| 80 / 20 | 100 % | inalterada | 151 → ~76 Mb/s | exploratória (console do cenário) |
| 40 / 60 | 100 % | inalterada | inalterada | v1 |
| 30 / 30 | 60 % | inalterada | inalterada | calibração v2 |
| 30 / 70 | 100 % | inalterada (teto 30 %) | inalterada | calibração v3 |
| 70 / 30 | 100 % | inalterada | inalterada (teto 30 %) | calibração v3 |

**Leitura (hipótese, não conclusão).** A soma das cotas não explica os dados: com soma 100 %, um teto de 30 % não restringe nenhuma das fatias. O único efeito observado é a URLLC com teto de 20 %, e ele foi grande (~50 %). A relação entre teto e vazão no escalonador do NORI é, portanto, não linear, com um limiar entre 20 % e 30 % para cada UE a 151,5 Mb/s, ou depende da granularidade de alocação (grupos de blocos de recurso). Nenhum modelo linear calibrado num ponto que não restringe pode prever o efeito. Um próximo desenho precisaria medir a curva teto → vazão em vários níveis abaixo de 30 % (por exemplo 10, 15, 20 e 25 %, por fatia) antes de qualquer previsão, com novo pré-registro.
