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
