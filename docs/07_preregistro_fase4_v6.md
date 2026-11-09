# Pré-registro — fase 4, desenho v6: efeito da cota relativo à vazão sem restrição

Registrado em 2026-11-09, **antes** das execuções de avaliação descritas aqui, no mesmo commit da regra de análise que elas usam (`slice_effect.py --rule v6`). Qualquer desvio deste roteiro será relatado junto com os resultados.

## 1. Contexto

A campanha NORI S0–S8 × 1001–1005 ([docs/11, seção 8](11_observabilidade_e_campanhas.md)) levantou dois problemas na regra v5. Os dois aparecem nos achados 41 e 42 de [docs/05](05_auditoria_e_conformidade_oran.md):

- **Achado 41:** no teto de 30 %, a regra v5 deixa o próprio nível de fora e interpola até 70 %, nível em que a vazão já está saturada. A previsão sai 91,45 Mb/s; o medido é 113,98 Mb/s, igual ao ponto de 30 % da curva.
- **Achado 42:** com a semente 1005, a vazão máxima por UE cai pela metade (75,74 Mb/s). A curva v5 está em Mb/s absolutos e deixa de valer. Já a razão depois/antes do Control, para cada teto, foi a mesma nas duas vazões de base.

Os dois achados vieram de dados já vistos. Este desenho os transforma em hipóteses e as testa em **execuções novas**, com sementes que ainda não foram rodadas.

## 2. Desenho v6

- **Calibração:** a mesma curva da v5, sem nenhuma alteração ([`slice_cap_curve_v5.json`](../experiments/calibration/slice_cap_curve_v5.json)). Ela vem das cinco execuções de calibração, não da campanha. De cada nível que restringe sai a razão r(teto) = vazão_depois / vazão_antes:

  | Teto | r(teto) | Origem |
  | --: | --: | :-- |
  | 10 % | 0,2473 | `nori_curve10_seed301` |
  | 15 % | 0,3713 | `nori_curve15_seed302` |
  | 20 % | 0,5046 | `nori_curve20_seed303` |
  | 30 % | 0,7524 | `nori_cal3070_seed201` (eMBB) e `nori_cal7030_seed202` (URLLC) |
  | 70 % | não restringe | nível livre |

- **Previsão (regra `v6-ratio-apply`):** as janelas e a âncora no instante de aplicação são as da v5. Para cada fatia, com teto c:
  - c ≥ menor nível livre acima dos que restringem (70 %): sem queda esperada; a vazão não pode cair mais que 5 %;
  - c igual a um nível que restringe: previsão = vazão_antes × r(c). As avaliações são execuções novas, fora da curva, então não há deixa-um-fora;
  - c entre dois níveis que restringem: r interpolada linearmente entre esses dois níveis. Níveis livres não entram na interpolação;
  - qualquer outro c (abaixo de 10 % ou entre 30 % e 70 %, onde o joelho da saturação não foi medido): `NOT_TESTABLE`;
  - fatia com previsão abaixo de 95 % da vazão antes: a vazão deve cair ≥ 5 % e ficar a no máximo **10 %** da previsão. A v5 tolerava 20 %.
- **Veredito por execução:** igual à v5. `CONSISTENT` se há ao menos uma fatia com queda prevista e todas as expectativas se cumprem; `INCONSISTENT` se alguma falha; `NOT_TESTABLE` se nenhuma fatia tem queda prevista, se algum teto cai fora dos níveis ou se a série não cobre as janelas.
- **Onde fica:** `experiments/e2_dissection/<run>/slice_effect_v6.json`, gravado por `scripts/collect_nori_run.sh`. O `slice_effect.json` continua com a regra v5 e é ele que o certificador usa no G4. Esta v6 não muda o certificador.
- **Decisão:** a mesma da campanha. A xApp kpm-probe roda em modo `catalog`, com o `src/` deste commit, e decide uma vez por execução, na 12.ª Indication.
- **Avaliação:** cenários S0, S1, S2, S6, S7 e S8 (os que atuam cota de PRB) × sementes **2001, 2002, 2003, 2004 e 2005**, nunca rodadas: 30 execuções, com a mesma configuração da campanha (`--simTime=40 --ns3::E2Interface::E2Periodicity=1 --trafficRate=300Mb/s`).

  Previsões fixadas agora, para a URLLC (a eMBB fica com teto ≥ 70 % em todos os cenários, sem queda esperada):

  | Cenário | Cotas eMBB/URLLC | r(teto da URLLC) | Previsão da URLLC |
  | :-: | :-: | --: | :-- |
  | S0, S2, S8 | 80/20 | 0,5046 | 0,5046 × vazão antes |
  | S1 | 75/25 | 0,6285 (interpolação 20–30 %) | 0,6285 × vazão antes |
  | S6 | 85/15 | 0,3713 | 0,3713 × vazão antes |
  | S7 | 70/30 | 0,7524 | 0,7524 × vazão antes |

## 3. Hipóteses e critérios

- **H6.1 (cadeia):** em cada avaliação há E2 Setup, Subscription, KPM_t0, RIC Control, ACK correlacionado e KPM_t1 no PCAP. A decisão é `H_RDL`, com o KPM_t0 entre as entradas, e o tshark concorda com o dissecador.
- **H6.2 (efeito relativo):** ao menos **27 das 30** avaliações (90 %) são `CONSISTENT` pela regra v6. Das execuções que ficarem `NOT_TESTABLE` por falha de procedimento, nenhuma é repetida em silêncio (seção 5).
- **H6.3 (teto de 30 %, achado 41):** as cinco avaliações do S7 são `CONSISTENT` pela regra v6.
- **H6.4 (invariância à vazão de base, achado 42):** toda avaliação cuja vazão de base da URLLC difere ≥ 20 % de 151,49 Mb/s é `CONSISTENT` pela regra v6. Se nenhuma das 30 tiver vazão de base diferente, H6.4 é relatada como **não testada**. Não se escolhe semente para provocar isso.

Os vereditos da regra v5 dessas mesmas execuções também entram no relatório, lado a lado.

## 4. Procedimento

1. **Pré-registro:** este documento, a regra v6 (`slice_effect.py --rule v6`, `tests/unit/test_slice_effect_v6.py`) e a coleta (`collect_nori_run.sh`) entram no mesmo commit, antes de qualquer avaliação.
2. **Avaliação:** ao vivo, em primeiro plano, na bancada NORI (patch `0001-rc-control-ack` do lock):

   ```bash
   bash scripts/run_nori_campaign.sh --scenarios "S0 S1 S2 S6 S7 S8" --seeds "2001 2002 2003 2004 2005"
   ```

3. **Análise:** a campanha roda a coleta (dissecação com tshark, `slice_effect.json` v5 e `slice_effect_v6.json`), o certificador e o resumo (`nori_campaign_summary.py --seeds 2001-2005`, com a coluna v6).

## 5. Como os resultados serão relatados

- Todas as execuções entram no relatório, inclusive as que falharem ou forem inválidas.
- H6.2 a H6.4 são avaliadas exatamente pelos critérios da seção 3. Resultado parcial é relatado como parcial.
- Uma avaliação com falha técnica de procedimento (série que não cobre as janelas, Control fora da série, pod da xApp reiniciado) fica `NOT_TESTABLE`, é relatada e conta como não `CONSISTENT` em H6.2. Repetição só com nova semente, declarada como desvio.
- Regra, constantes, curva e tolerância não serão ajustadas depois de ver os resultados.
- Se H6.2 for confirmada, a adoção da v6 no certificador (G4) será uma mudança separada e declarada, não retroativa.

## 6. Ameaças à validade conhecidas

- **Regra desenhada sobre dados já vistos:** a forma relativa e a interpolação só entre níveis que restringem saíram da campanha 1001–1005. Aplicada retrospectivamente a essas 30 execuções com Control, a v6 dá 30 `CONSISTENT`, com erro ≤ 0,2 %. Isso foi checado em memória, sem gravar evidência, e **não é evidência**: o teste é só nas sementes 2001–2005.
- **Saturação:** a razão relativa supõe carga acima da capacidade da fatia (300 Mb/s oferecidos contra ≤ 151,5 Mb/s por UE). Com carga abaixo da capacidade, o teto limitaria em termos absolutos e a razão mudaria. Carga variável está fora deste desenho.
- **Vazão de base:** só o NORI decide se uma semente nova muda a vazão de base, e não sabemos de antemão quais mudam. Por isso H6.4 pode ficar não testada.
- **Mesmas limitações da v5:** cenário único (um gNB, dois UEs), efeito medido no FlowMonitor (o KPM do NORI não mede vazão por UE), NORI com o patch do ACK, decisão única por execução e sinal de congestionamento do NORI sempre verdadeiro.
- **Tolerância mais estreita (10 %):** a v6 é mais exigente que a v5 (20 %). Um erro sistemático pequeno da curva pode fazer a v6 falhar onde a v5 passaria.
