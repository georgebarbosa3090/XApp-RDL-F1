# Pré-registro — fase 4, desenho v2: efeito causal da decisão H-RDL na RAN

Registrado em 2026-11-08, **antes** das execuções descritas aqui, no mesmo commit do código de decisão e de análise que elas usam. Qualquer desvio deste roteiro será relatado junto com os resultados.

## 1. Contexto: o que a v1 mostrou

Na execução [`nori_hrdl_loop_seed1`](../experiments/runs/nori_hrdl_loop_seed1/execution_manifest.json) (commit `b48473d`), a cadeia E2 completa funcionou com o Control decidido pelo H-RDL sobre o KPM_t0. O teto escolhido (eMBB 40 %) não restringiu a fatia e a expectativa pré-registrada falhou (efeito `INCONSISTENT`, G4 `NOT_CERTIFIED`). A causa está na regra v1, que tomou a parte da vazão (50/50) como parte dos PRBs. A vazão de cada UE para em ~151,5 Mb/s por um limite próprio do UE, e a execução exploratória com teto de 20 % indicou ~3,8 Mb/s por ponto percentual de PRB, ou seja, ~40 % dos PRBs por UE. Esse resultado continua relatado como está.

## 2. O que muda na v2

| Item | v1 | v2 |
| :-- | :-- | :-- |
| Parte dos PRBs que cada fatia usa | parte da vazão | vazão ÷ k_s, com k_s (Mb/s por % de PRB) de uma execução de calibração separada |
| Critério nas fatias restritas | queda ≥ 5 % | queda ≥ 5 % **e** vazão depois a no máximo 20 % da previsão teto × k_s |
| Proposta da `xapp-qos-xslice` | teto eMBB 40 % | teto eMBB 25 % |
| Proposta da `xapp-embb-throughput` | teto eMBB 80 % | igual |
| Regra aceita pelo certificador para G4 | qualquer veredito `CONSISTENT` | só `CONSISTENT` da regra v2, com a calibração conferida por hash |

As duas políticas continuam fixas e independentes do resultado: a decisão é do H-RDL. Com 25 contra 80, o pipeline real (`RDLxApp._process_action_group`, TVS) escolhe a política de vazão da eMBB; o teste `tests/unit/test_hrdl_slice_loop.py::test_real_hrdl_pipeline_resolves_the_direct_conflict` fixa essa previsão.

## 3. Hipóteses e critérios

- **H4.1 (cadeia):** cada execução de avaliação tem, no PCAP, E2 Setup, Subscription, KPM_t0, RIC Control, ACK correlacionado e KPM_t1. O Control tem `decision_source=H_RDL`, os mesmos bytes do registro da xApp e foi disparado pelo KPM_t0. O tshark concorda com o dissecador em todas as mensagens.
- **H4.2 (decisão):** com o KPM_t0 congestionado e as duas fatias presentes, o H-RDL seleciona `xapp-embb-throughput`, com cotas eMBB 80 % / URLLC 20 %.
- **H4.3 (efeito, regra v2):** a fatia URLLC fica restrita (teto 20 % < PRB usado estimado − 5 p.p.). Sua vazão deve cair ao menos 5 % e ficar a no máximo 20 % de 20 × k_URLLC. A eMBB (teto 80 %) não fica restrita e não pode perder mais que 5 %.

## 4. Procedimento

Todas as execuções usam a bancada NORI com o patch `0001-rc-control-ack` do lock e a variante `nori-rc-slicing-flowmon`, com `--simTime=30 --ns3::E2Interface::E2Periodicity=1 --trafficRate=300Mb/s`. O Control sai depois da 12.ª Indication. As execuções rodam ao vivo, em primeiro plano.

1. **Calibração:** `nori_cal30_seed101` (semente 101), xApp com `rc.decision: fixed` e cotas 30/30 nas duas fatias. `scripts/certification/calibrate_slice_capacity.py` calcula k_s = vazão depois ÷ 30 e grava `experiments/calibration/slice_capacity_v2.json`. A calibração só vale se as duas fatias caírem ao menos 5 %. Se for inválida, as avaliações não são rodadas e isso é relatado.
2. **Avaliação:** `nori_hrdl_v2_seed1`, `_seed2` e `_seed3` (sementes 1, 2 e 3), xApp com `rc.decision: hrdl` e o `src/` deste commit (`scripts/deploy_kpm_probe.sh`).
3. **Análise:** `scripts/collect_nori_run.sh` (dissecação com tshark e `slice_effect.py --calibration`) e `scripts/certification/certify_chain.py`.

Constantes da análise: janela de 4 s antes do Control e 4 s depois de 2 s de acomodação; margem de 5 p.p.; queda mínima de 5 %; tolerância de 20 % na previsão.

## 5. Como os resultados serão relatados

- Todas as execuções entram no relatório, inclusive as que falharem ou forem inválidas.
- O efeito causal só é afirmado se as **três** avaliações forem `CONSISTENT`. Com uma ou duas, o relatório diz exatamente isso. O G4 segue a regra do certificador (ao menos uma execução elegível e `CONSISTENT`), e o relatório informa quantas cumprem.
- Políticas, constantes e regra não serão ajustadas depois de ver os resultados. Um novo ajuste exige um novo pré-registro.
- Como análise exploratória, a execução v1 será reavaliada pela regra v2 depois da calibração. A expectativa é `NOT_TESTABLE`, porque o teto de 40 % fica dentro da margem do que a eMBB usava. O resultado oficial da v1 não muda.

## 6. Ameaças à validade conhecidas

- **Cenário único:** um gNB, dois UEs a 20 m e 40 m, carga UDP saturada.
- **Calibração em uma execução**, com modelo linear entre teto e vazão.
- **Limite por UE (~151,5 Mb/s):** pode mascarar ganhos da fatia não restrita; por isso só se exige que ela não perca.
- **Sinal de congestionamento:** vem do `RRU.PrbUsedDl` do nó, que no NORI fica sempre acima dos PRBs disponíveis.
- **Tempo real:** a simulação atrasa em relação ao relógio. A conversão do instante do Control usa a série com os dois relógios.

## 7. Resultado (registrado depois das execuções, 2026-11-08)

O pré-registro foi publicado no commit `3962e97`; a xApp rodou o `src/` desse commit.

**Calibração inválida; avaliações não executadas.** Em [`nori_cal30_seed101`](../experiments/runs/nori_cal30_seed101/execution_manifest.json), o Control com teto de 30 % nas duas fatias saiu e foi confirmado (ACK correlacionado em 3,6 ms, tshark de acordo). Mas nenhuma fatia perdeu vazão: as duas ficaram em 151,49 Mb/s nas janelas antes e depois (t_sim do Control = 5,26 s). [`slice_capacity_v2.json`](../experiments/calibration/slice_capacity_v2.json) registra `valid: false`. Conforme a seção 4, passo 1, as execuções `nori_hrdl_v2_seed1..3` **não foram rodadas**, e a reanálise exploratória da v1 pela regra v2 ficou sem calibração.

**O que os dados sugerem, como hipótese para um próximo desenho (não como conclusão).** As três execuções com cotas, todas a 300 Mb/s por UE:

| Cotas eMBB / URLLC | Soma | Efeito observado |
| :-- | --: | :-- |
| 80 / 20 (exploratória) | 100 % | URLLC 151 → ~76 Mb/s; eMBB inalterada |
| 40 / 60 (v1, decidida pelo H-RDL) | 100 % | nenhuma fatia muda |
| 30 / 30 (calibração v2) | 60 % | nenhuma fatia muda |

Um modelo linear calibrado no ponto 80/20 (~3,8 Mb/s por ponto percentual de PRB) previa ~115 Mb/s com teto de 30 %. O 30/30 contradiz isso. Os dados combinam com um escalonador que reaproveita os PRBs não usados: o teto só limita quando as cotas somam 100 % e não sobra capacidade para redistribuir. Testar isso exige calibração com cotas complementares (por exemplo, 20/80 e 80/20) e um novo pré-registro.

> **Errata (2026-11-08, depois da v4):** a leitura acima foi superada. A cota tem efeito, e linear; o efeito só começa quando o tempo simulado alcança o relógio de parede do instante em que o Control chegou (~12 s simulados depois, fora da janela). Ver o [pré-registro v4, seção 7](07_preregistro_fase4_v4.md#7-resultado-registrado-depois-das-execuções-2026-11-08). O resultado oficial (calibração inválida, avaliações não rodadas) não muda.
