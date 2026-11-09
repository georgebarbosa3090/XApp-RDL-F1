# Pré-registro — fase 4, desenho v7: a razão da cota com outra vazão de base (teste da H6.4)

Registrado em 2026-11-09, **antes** das execuções de avaliação descritas aqui. Qualquer desvio deste roteiro será relatado junto com os resultados.

## 1. Contexto

O desenho v6 ([pré-registro](07_preregistro_fase4_v6.md)) confirmou a regra relativa nas sementes 2001–2005: previsão = vazão_antes × r(teto). Ficou sem testar a H6.4: a razão r(teto) não depende da vazão de base. Nenhuma semente nova mudou a vazão de base. A única evidência continua exploratória: a semente 1005 deu, por acaso, 75,74 Mb/s para os dois UEs, e as razões coincidiram.

Este desenho muda a vazão de base **de propósito**. Em vez de esperar que uma semente a altere, ele reduz a banda da portadora.

## 2. Piloto (registrado antes deste documento, sem Control)

Para escolher a condição, rodei um piloto que não envia Control: o S3, cuja decisão não é atuável no NORI. Ele usou banda de 50 MHz e a semente 3901, que não pertence a nenhuma faixa de avaliação. A execução é [`nori_S3_B3_bw50_seed3901`](../experiments/runs/nori_S3_B3_bw50_seed3901/execution_manifest.json). O piloto mede só a vazão de base, e nenhum efeito de cota foi visto.

| Condição | eMBB (UE 0, 20 m) | URLLC (UE 1, 40 m) |
| :-- | --: | --: |
| 100 MHz (calibração e v6) | 151,49 Mb/s | 151,49 Mb/s |
| **50 MHz (piloto)** | **151,49 Mb/s** | **40,0 Mb/s** |

Com 50 MHz, só a URLLC muda: a vazão de base cai 74 %, estável do segundo 4 ao 36.

## 3. Desenho v7

- **Condição:** `--bandwidth=50e6`; o resto é igual à v6: `--simTime=40 --ns3::E2Interface::E2Periodicity=1 --trafficRate=300Mb/s`, a xApp kpm-probe em modo `catalog` e a decisão na 12.ª Indication.
- **Regra:** `v6-ratio-apply`, **sem nenhuma alteração**. Mesma curva v5 ([`slice_cap_curve_v5.json`](../experiments/calibration/slice_cap_curve_v5.json), medida a 100 MHz), mesmas razões r(teto), mesmas janelas e tolerância de 10 %. A regra v5 (Mb/s absolutos) também é registrada, lado a lado.
- **Avaliação:** cenários S0, S1, S2, S6, S7 e S8 × sementes **4001, 4002, 4003, 4004 e 4005**, nunca rodadas: 30 execuções, com `run_id` `nori_<S>_B3_bw50_seed<N>`.

  Previsões fixadas agora para a URLLC (base ≈ 40 Mb/s, pelo piloto). A previsão efetiva usa a vazão antes medida em cada execução.

  | Cenário | Cotas eMBB/URLLC | r(teto da URLLC) | Previsão v6 da URLLC (base 40,0) |
  | :-: | :-: | --: | --: |
  | S0, S2, S8 | 80/20 | 0,5046 | ~20,2 Mb/s |
  | S1 | 75/25 | 0,6285 | ~25,1 Mb/s |
  | S6 | 85/15 | 0,3713 | ~14,9 Mb/s |
  | S7 | 70/30 | 0,7524 | ~30,1 Mb/s |

  A eMBB fica com teto ≥ 70 % em todos os cenários, então não se espera queda dela.

## 4. Hipóteses e critérios

- **H7.1 (cadeia):** em cada avaliação, cadeia E2 completa no PCAP, decisão `H_RDL` com o KPM_t0 entre as entradas, ACK correlacionado e tshark de acordo com o dissecador.
- **H7.2 (= H6.4, invariância da razão):** com a vazão de base da URLLC ≥ 20 % abaixo de 151,49 Mb/s, ao menos **27 das 30** avaliações são `CONSISTENT` pela regra v6.
- **Desfechos possíveis, declarados agora:**
  - H7.2 cumprida: a razão vale para uma vazão de base reduzida pela banda;
  - H7.2 refutada: a razão calibrada a 100 MHz não transfere para 50 MHz. O relatório traz as razões depois/antes medidas por teto, como dado exploratório, sem ajustar a regra.

  Uma explicação física possível para a refutação, registrada antes de ver os dados: a 50 MHz, a eMBB mantém 151,49 Mb/s ocupando uma fração maior dos PRBs. A URLLC, então, não usaria ~40 % dos PRBs como na calibração, e o teto restringiria de outro modo.

## 5. Procedimento

1. **Pré-registro:** este documento, o piloto e o suporte a condições nos roteiros (`RUN_TAG`, `SCENARIO_ARGS`; `run_nori_campaign.sh --tag --args`; `nori_campaign_summary.py --tag`) entram no mesmo commit, antes das avaliações.
2. **Avaliação:** ao vivo, em primeiro plano, com a xApp implantada a partir do commit deste pré-registro:

   ```bash
   bash scripts/run_nori_campaign.sh --scenarios "S0 S1 S2 S6 S7 S8" --seeds "4001 4002 4003 4004 4005" --tag _bw50 --args "--bandwidth=50e6"
   ```

3. **Análise:** a coleta grava `slice_effect.json` (v5) e `slice_effect_v6.json` (v6). Depois rodam o certificador e o resumo (`--tag _bw50`).

## 6. Como os resultados serão relatados

- Todas as execuções entram no relatório, inclusive as que falharem.
- H7.2 é julgada só pelo critério da seção 4. Uma refutação é relatada como refutação.
- Uma falha técnica de procedimento fica `NOT_TESTABLE` e conta como não `CONSISTENT`. Repetição só com nova semente, declarada.
- Regra, curva, constantes e tolerância não serão ajustadas depois de ver os resultados.
- O certificador aplica a regra que já está em vigor para execuções novas (v6). Execuções `INCONSISTENT` não entram no G4.

## 7. Ameaças à validade conhecidas

- **Uma única condição de banda (50 MHz):** se H7.2 se cumprir, a invariância está mostrada para essa redução de banda, não para qualquer variação da vazão de base.
- **Só a URLLC muda de vazão de base:** a eMBB fica igual. A invariância é testada numa fatia.
- **Mesmas limitações da v6:** um gNB, dois UEs, saturação, FlowMonitor como medida, NORI com o patch do ACK, decisão única por execução e sinal de congestionamento do NORI sempre verdadeiro.
