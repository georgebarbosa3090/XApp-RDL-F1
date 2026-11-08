# Pré-registro — fase 4, desenho v4: curva teto → vazão e previsão deixa-um-fora

Registrado em 2026-11-08, **antes** das execuções descritas aqui, no mesmo commit do código de decisão, da curva e da análise que elas usam. Qualquer desvio deste roteiro será relatado junto com os resultados.

## 1. Contexto: v1 a v3

- **v1:** a cadeia E2 completa funcionou com o Control decidido pelo H-RDL (cotas eMBB 40 / URLLC 60), mas nenhuma fatia mudou (efeito `INCONSISTENT`).
- **v2 e v3:** pararam em calibrações inválidas. Um teto de 30 % não restringiu nenhuma fatia, nem com as cotas somando 60 % (30/30) nem 100 % (30/70 e 70/30).
- **Todas as configurações observadas:** só a URLLC a 20 % foi restringida (~50 %). A relação entre teto e vazão é não linear, e uma calibração num nível que não restringe não prevê nada.
- **A soma das cotas é irrelevante:** 30/30, 30/70 e 70/30 deram o mesmo resultado. É isso que permite medir as duas fatias no mesmo teto numa única execução.

## 2. Desenho v4

- **Curva teto → vazão:** quatro execuções com o **mesmo** teto nas duas fatias, por RIC Control com cota fixa:
  - `nori_curve10_seed301` (10/10)
  - `nori_curve15_seed302` (15/15)
  - `nori_curve20_seed303` (20/20)
  - `nori_curve25_seed304` (25/25)

  Os pontos a 30 % vêm das calibrações v3 (`nori_cal3070_seed201` para a eMBB e `nori_cal7030_seed202` para a URLLC). `scripts/certification/slice_cap_curve.py` gera `experiments/calibration/slice_cap_curve_v4.json`.
- **Validade da curva:** por fatia, a vazão depois do Control não pode crescer quando o teto baixa (tolerância de 5 %), e ao menos uma fatia precisa ter um nível que restringe.
- **Previsão (regra `v4-curve`, `slice_effect.py --curve`):** para o teto c que o H-RDL decidir, por fatia:
  - se c ≥ o menor nível sem restrição acima de todos os níveis que restringem, espera-se que a fatia **não perca** mais que 5 %;
  - se c está entre dois níveis medidos (**excluído o próprio nível c**, deixa-um-fora), a previsão é a interpolação linear da vazão depois. Se ela ficar abaixo de 95 % da vazão antes, a fatia é restrita: deve cair ao menos 5 % e ficar a no máximo 20 % da previsão. Caso contrário, não pode perder mais que 5 %;
  - fora do intervalo medido, a fatia não é testável, e a execução fica `NOT_TESTABLE`.
- **Decisão:** igual à v2 e à v3. As políticas `xapp-qos-xslice` (25 %) e `xapp-embb-throughput` (80 %) vão ao pipeline real do H-RDL. A previsão é a política de vazão da eMBB, com cotas eMBB 80 / URLLC 20 (teste `test_real_hrdl_pipeline_resolves_the_direct_conflict`).

## 3. Hipóteses e critérios

- **H4.1 (cadeia):** cada avaliação tem, no PCAP, E2 Setup, Subscription, KPM_t0, RIC Control, ACK correlacionado e KPM_t1. O Control tem `decision_source=H_RDL`, os mesmos bytes do registro da xApp e foi disparado pelo KPM_t0. O tshark concorda com o dissecador em todas as mensagens.
- **H4.2 (decisão):** o H-RDL seleciona `xapp-embb-throughput`, com cotas eMBB 80 / URLLC 20.
- **H4.3 (efeito, regra `v4-curve`):** a URLLC a 20 % é prevista pela interpolação entre os pontos de 15 % e 25 % da sua curva. Se a previsão a restringe, a vazão deve cair ao menos 5 % e ficar a no máximo 20 % da previsão. A eMBB a 80 % não pode perder mais que 5 %.

## 4. Procedimento

Bancada NORI com o patch `0001-rc-control-ack` do lock e a variante `nori-rc-slicing-flowmon`, com `--simTime=30 --ns3::E2Interface::E2Periodicity=1 --trafficRate=300Mb/s`. O Control sai depois da 12.ª Indication. Todas as execuções rodam ao vivo, em primeiro plano, com a xApp usando o `src/` deste commit.

1. **Curva:** as quatro execuções `nori_curve*` (`rc.decision: fixed`, cotas `1:c:0:0,2:c:0:0`). Depois, `slice_cap_curve.py --run nori_curve10_seed301 --run nori_curve15_seed302 --run nori_curve20_seed303 --run nori_curve25_seed304 --run nori_cal3070_seed201 --run nori_cal7030_seed202`. Se a curva for inválida, as avaliações não são rodadas e isso é relatado.
2. **Avaliação:** `nori_hrdl_v4_seed1`, `_seed2` e `_seed3` (sementes 1, 2 e 3), `rc.decision: hrdl`.
3. **Análise:** `scripts/collect_nori_run.sh` (dissecação com tshark e `slice_effect.py --curve experiments/calibration/slice_cap_curve_v4.json`) e `scripts/certification/certify_chain.py`.

Constantes: janela de 4 s antes do Control e 4 s depois de 2 s de acomodação; queda mínima de 5 %; tolerância de 20 % na previsão.

## 5. Como os resultados serão relatados

- Todas as execuções entram no relatório, inclusive as que falharem ou forem inválidas.
- O efeito causal só é afirmado se as **três** avaliações forem `CONSISTENT`. Com uma ou duas, o relatório diz exatamente isso. O G4 segue a regra do certificador (ao menos uma execução elegível e `CONSISTENT` por regra calibrada), e o relatório informa quantas cumprem.
- Políticas, constantes e regras não serão ajustadas depois de ver os resultados. Um novo ajuste exige um novo pré-registro.
- Análises exploratórias, rotuladas como tais e sem efeito sobre o G4:
  - a execução v1 (eMBB 40 / URLLC 60) pela regra `v4-curve`;
  - a vazão da URLLC a 20 % da execução exploratória 80/20 (~76,5 Mb/s, console do cenário) comparada com o ponto de 20 % da curva.

## 6. Ameaças à validade conhecidas

- **Cenário único:** um gNB, dois UEs a 20 m e 40 m, carga UDP saturada.
- **Curva:** uma execução por nível e semente diferente para cada nível. A suposição de que a soma das cotas é irrelevante vem de três execuções a 30 %.
- **Interpolação linear** entre níveis medidos de 5 em 5 pontos percentuais.
- **Limite por UE (~151,5 Mb/s):** pode mascarar ganhos da fatia não restrita.
- **Sinal de congestionamento:** vem do `RRU.PrbUsedDl` do nó, que no NORI fica sempre acima dos PRBs disponíveis.
- **Tempo real:** a simulação atrasa em relação ao relógio. A conversão do instante do Control usa a série com os dois relógios.

## 7. Resultado (registrado depois das execuções, 2026-11-08)

O pré-registro foi publicado no commit `d9e046c`; a xApp rodou o `src/` desse commit.

**Resultado oficial: curva inválida; avaliações não executadas.** As quatro execuções da curva rodaram ao vivo. Em todas, o Control saiu e o ACK voltou correlacionado, e o tshark concordou nas 66 mensagens. Pela regra pré-registrada (janela de 2 s a 6 s depois do Control), nenhum nível restringiu nenhuma fatia, e [`slice_cap_curve_v4.json`](../experiments/calibration/slice_cap_curve_v4.json) registra `valid: false`. Conforme a seção 4, passo 1, as execuções `nori_hrdl_v4_seed1..3` **não foram rodadas**. Em `nori_curve25_seed304` houve um desvio de procedimento: o pod da xApp foi trocado durante a execução, a subscrição ficou com o pod anterior, e o novo pod só enviou o Control em t_sim = 21,8 s (28 de 60 Indications recebidas).

**Análise exploratória (post hoc, fora do pré-registro): a cota funciona, e o efeito atrasa.** Na série inteira de cada execução, a vazão da fatia restrita cai para um patamar estável, mas só a partir de t_sim ≈ 17–19 s, cerca de 12 s simulados depois do Control. O início do efeito coincide, dentro da resolução de 0,5 s, com o tempo de **relógio de parede** decorrido desde o início da simulação no instante em que o Control chegou:

| Execução | Teto da fatia restrita | Control (t_sim) | Relógio de parede decorrido no Control | Início do efeito (t_sim) | Vazão estável depois (t 22–28 s) |
| :-- | --: | --: | --: | --: | --: |
| [`nori_curve10_seed301`](../experiments/runs/nori_curve10_seed301/execution_manifest.json) | 10 % (as duas) | 5,70 | 19,30 s | 19,0 | 37,46 Mb/s |
| [`nori_curve15_seed302`](../experiments/runs/nori_curve15_seed302/execution_manifest.json) | 15 % (as duas) | 5,12 | 17,40 s | 17,0 | 56,25 Mb/s |
| [`nori_curve20_seed303`](../experiments/runs/nori_curve20_seed303/execution_manifest.json) | 20 % (as duas) | 5,67 | 18,89 s | 18,5 | 76,45 Mb/s |
| [`nori_cal30_seed101`](../experiments/runs/nori_cal30_seed101/execution_manifest.json) | 30 % (as duas) | 5,26 | 17,28 s | 17,0 | 113,98 Mb/s |
| [`nori_cal3070_seed201`](../experiments/runs/nori_cal3070_seed201/execution_manifest.json) | 30 % (eMBB) | 5,43 | 18,28 s | 18,0 | 113,98 Mb/s (URLLC 151,49) |
| [`nori_cal7030_seed202`](../experiments/runs/nori_cal7030_seed202/execution_manifest.json) | 30 % (URLLC) | 5,06 | 18,70 s | 18,5 | 113,98 Mb/s (eMBB 151,49) |

- **Mecanismo provável:** o NORI recebe o Control na thread do E2 e o agenda com `Simulator::ScheduleWithContext(MicroSeconds(0), ...)`. No `RealtimeSimulatorImpl`, um evento vindo de outra thread é posicionado pelo relógio de tempo real, que fica 3 a 4 vezes à frente da simulação atrasada pela carga.
- **Relação teto → vazão:** linear, ~3,75–3,82 Mb/s por ponto percentual de PRB, igual para as duas fatias e independente da soma das cotas. Com teto de 40 %, a previsão (~152 Mb/s) fica acima do limite por UE (151,5 Mb/s), o que é coerente com a v1: o Control dela chegou com 26,3 s de relógio decorrido, e a partir de t_sim ≈ 26 s a série continua em 151,5 Mb/s até o fim (29,5 s).
- **O que isso revisa:** as leituras "relação não linear" e "soma das cotas" das seções 7 da v2 e da v3 estavam erradas. Os nulos vieram da janela de análise, não da RAN. Os resultados oficiais da v2 e da v3 (calibração inválida pela regra deles) não mudam.
- **Para um próximo desenho:** a janela precisa ser ancorada no instante de aplicação (o tempo de parede decorrido no Control, mapeado pela série), e a simulação precisa durar o bastante depois disso; o roteiro de execução precisa esperar o pod antigo da xApp terminar antes de iniciar o cenário.
