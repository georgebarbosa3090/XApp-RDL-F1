# Pré-registro — fase 4, desenho v5: janela ancorada no instante de aplicação do Control

Registrado em 2026-11-08, **antes** das execuções de avaliação descritas aqui, no mesmo commit do código de decisão, da curva e da análise que elas usam. Qualquer desvio deste roteiro será relatado junto com os resultados.

## 1. Contexto

As versões v1 a v4 não confirmaram efeito. A análise exploratória da v4 ([seção 7](07_preregistro_fase4_v4.md#7-resultado-registrado-depois-das-execuções-2026-11-08)) mostrou a causa:

- **A cota funciona e é linear:** ~3,8 Mb/s por ponto percentual de PRB.
- **O efeito atrasa:** só começa quando o tempo simulado alcança o relógio de parede decorrido no instante em que o Control chegou, cerca de 12 s simulados depois. O NORI agenda o Control a partir da thread do E2 no simulador em tempo real.
- **A janela estava errada:** a janela de análise, ancorada no instante do Control, terminava antes do efeito.

A curva da v4 já foi medida, e eu já vi seus valores (exploratórios). Por isso, nesta v5 ela é tratada só como **calibração**. O teste é prospectivo apenas nas três execuções de avaliação, que ainda não foram rodadas.

## 2. Desenho v5

- **Âncora da janela:** o instante de aplicação, t_aplic = parede_Control − (parede_0 − t_0). A primeira amostra da série dá parede_0 e t_0, quando a simulação ainda não atrasou (`slice_effect.apply_time`). As janelas ficam em [t_aplic − 4 s, t_aplic] (antes) e [t_aplic + 2 s, t_aplic + 6 s] (depois).
- **Curva (calibração):** recalculada com a âncora de aplicação, a partir de execuções já existentes, com um nível único por fatia (`slice_cap_curve.py --anchor apply`, saída `experiments/calibration/slice_cap_curve_v5.json`):

  | Execução | Fatia e teto |
  | :-- | :-- |
  | `nori_curve10_seed301` | as duas fatias a 10 % |
  | `nori_curve15_seed302` | as duas fatias a 15 % |
  | `nori_curve20_seed303` | as duas fatias a 20 % |
  | `nori_cal3070_seed201` | eMBB a 30 % e URLLC a 70 % |
  | `nori_cal7030_seed202` | eMBB a 70 % e URLLC a 30 % |

  Ficam de fora a `nori_curve25_seed304` (Control tardio por troca de pod; o efeito cairia depois do fim da simulação) e a `nori_cal30_seed101` (repetiria o nível de 30 %).
- **Validade da curva:** igual à v4. Monotonicidade com tolerância de 5 % por fatia, e ao menos um nível que restringe.
- **Previsão (regra `v5-curve-apply`):** igual à regra v4, com a âncora de aplicação. Uma fatia com teto ≥ o menor nível livre acima dos que restringem não pode perder mais que 5 %. Uma fatia com teto entre dois níveis medidos (excluído o próprio nível, deixa-um-fora) recebe a previsão por interpolação linear; se a previsão a restringe, a vazão deve cair ≥ 5 % e ficar a no máximo 20 % da previsão.
- **Decisão:** igual à v2–v4. As políticas `xapp-qos-xslice` (25 %) e `xapp-embb-throughput` (80 %) vão ao pipeline real do H-RDL. A previsão é a política de vazão da eMBB, com cotas eMBB 80 / URLLC 20.
- **Avaliação:** `nori_hrdl_v5_seed1`, `_seed2` e `_seed3` (sementes 1, 2 e 3). A simulação passa a durar **40 s**, para cobrir t_aplic + 6 s. O roteiro de execução só inicia o cenário quando há **um único** pod da xApp, pronto, com o commit e o modo `hrdl` no evento `start`.

## 3. Hipóteses e critérios

- **H4.1 (cadeia):** cada avaliação tem, no PCAP, E2 Setup, Subscription, KPM_t0, RIC Control, ACK correlacionado e KPM_t1. O Control tem `decision_source=H_RDL`, os mesmos bytes do registro da xApp e foi disparado pelo KPM_t0. O tshark concorda com o dissecador em todas as mensagens.
- **H4.2 (decisão):** o H-RDL seleciona `xapp-embb-throughput`, com cotas eMBB 80 / URLLC 20.
- **H4.3 (efeito, regra `v5-curve-apply`):** a URLLC a 20 % recebe a previsão interpolada entre os níveis de 15 % e 30 % da sua curva. Pelos valores exploratórios, ~56,2 e ~114,0 Mb/s, a previsão seria ~75,5 Mb/s; o valor efetivo é o que sair do arquivo da curva. A URLLC deve cair ≥ 5 % e ficar a no máximo 20 % da previsão. A eMBB a 80 % fica acima do nível livre (70 %) e não pode perder mais que 5 %.

## 4. Procedimento

1. **Curva:** `slice_cap_curve.py --anchor apply --run nori_curve10_seed301 --run nori_curve15_seed302 --run nori_curve20_seed303 --run nori_cal3070_seed201 --run nori_cal7030_seed202 --out experiments/calibration/slice_cap_curve_v5.json`. Se a curva for inválida, as avaliações não são rodadas.
2. **Avaliação:** as três execuções, ao vivo e em primeiro plano, com a bancada NORI (patch `0001-rc-control-ack` do lock) e a variante `nori-rc-slicing-flowmon`, com `--simTime=40 --ns3::E2Interface::E2Periodicity=1 --trafficRate=300Mb/s`. O Control sai depois da 12.ª Indication, e a xApp usa o `src/` deste commit.
3. **Análise:** `scripts/collect_nori_run.sh` (dissecação com tshark e `slice_effect.py --curve experiments/calibration/slice_cap_curve_v5.json`) e `scripts/certification/certify_chain.py`.

## 5. Como os resultados serão relatados

- Todas as execuções entram no relatório, inclusive as que falharem ou forem inválidas.
- O efeito causal só é afirmado se as **três** avaliações forem `CONSISTENT`. Com uma ou duas, o relatório diz exatamente isso. O G4 segue a regra do certificador.
- Uma avaliação com falha técnica de procedimento (por exemplo, janelas fora da série) fica `NOT_TESTABLE` e é relatada. Ela não é repetida em silêncio. Uma repetição só acontece com nova semente, declarada como desvio.
- Políticas, constantes e regras não serão ajustadas depois de ver os resultados.

## 6. Ameaças à validade conhecidas

- **Calibração já vista:** a curva vem de execuções cujos valores já eram conhecidos. A predição da URLLC a 20 % ainda é deixa-um-fora, mas o ponto de 20 % da curva (76,45 Mb/s) já mostrava o valor esperado. O teste prospectivo está na replicação com o Control decidido pelo H-RDL, em sementes e configurações novas (eMBB 80 / URLLC 20 em vez de 20/20).
- **Estimativa do instante de aplicação:** depende de a primeira amostra não ter atraso. Na v4, essa estimativa coincidiu com o início do efeito com resolução de 0,5 s.
- **Cenário único, limite por UE (~151,5 Mb/s) e sinal de congestionamento:** as mesmas limitações das versões anteriores.

## 7. Resultado (registrado depois das execuções, 2026-11-08)

O pré-registro foi publicado no commit `6bb7773`; a xApp rodou o `src/` desse commit.

**Curva (passo 1):** [`slice_cap_curve_v5.json`](../experiments/calibration/slice_cap_curve_v5.json) saiu válida. Para as duas fatias: 10 % → 37,46; 15 % → 56,25; 20 % → 76,45; 30 % → ~113,98; 70 % → 151,49 Mb/s (sem restrição). Previsões fixadas antes das avaliações: URLLC a 20 % → **75,49 Mb/s** (interpolação entre 15 % e 30 %); eMBB a 80 % → sem queda (acima do nível livre de 70 %).

**Avaliações (passo 2): as três `CONSISTENT`.**

| Execução | Decisão do H-RDL | Control → ACK | Aplicação (t_sim) | URLLC (teto 20 %) | eMBB (teto 80 %) |
| :-- | :-- | :-- | --: | :-- | :-- |
| [`nori_hrdl_v5_seed1`](../experiments/runs/nori_hrdl_v5_seed1/execution_manifest.json) | `xapp-embb-throughput` (TVS, 0,92), 80/20 | correlacionado, 8,1 ms | 19,43 s | 151,49 → 76,45 Mb/s (prevista 75,49; erro 1,3 %) | 151,49 → 151,49 Mb/s |
| [`nori_hrdl_v5_seed2`](../experiments/runs/nori_hrdl_v5_seed2/execution_manifest.json) | idem | correlacionado, 2,0 ms | 18,26 s | 151,49 → 76,44 Mb/s (erro 1,3 %) | 151,49 → 151,49 Mb/s |
| [`nori_hrdl_v5_seed3`](../experiments/runs/nori_hrdl_v5_seed3/execution_manifest.json) | idem | correlacionado, 18,1 ms | 18,05 s | 151,49 → 76,44 Mb/s (erro 1,3 %) | 151,49 → 151,49 Mb/s |

- **H4.1 cumprida nas três:** 86 mensagens E2AP, com o tshark de acordo em todas; 80/80 Indications casadas com a xApp; Control com `decision_source=H_RDL`, disparado pelo KPM_t0 e com os mesmos bytes do registro.
- **H4.2 cumprida:** o H-RDL selecionou `xapp-embb-throughput` (cotas 80/20) nas três, em 1 a 5 ms.
- **H4.3 cumprida:** a URLLC caiu 49,5 % e ficou a 1,3 % da previsão; a eMBB não perdeu vazão.
- **Certificador:** **G4 `CERTIFIED`** (3 cadeias), "cadeia closed-loop validada: SIM".

**Desvio de procedimento.** O roteiro de execução abortou a semente 3 **antes de iniciá-la**: a verificação de prontidão da xApp procurava o evento `start` no `kubectl logs`, que o k3s rotacionou depois de duas execuções. O pod estava saudável (único, sem reinício). Nenhum dado da semente 3 foi gerado nem visto antes da correção. A semente 3 foi executada em seguida, com a mesma semente pré-registrada e a verificação corrigida para ler o arquivo de eventos persistente da xApp.

**O que esta certificação afirma, e o que não afirma.**

- **Afirma:** numa bancada NORI + Near-RT RIC Release I real, o H-RDL decidiu cotas de PRB a partir do KPM_t0 recebido por E2. O Control E2SM-RC chegou ao nó, foi confirmado por ACK correlacionado e produziu na RAN o efeito previsto antes das execuções, nas três sementes.
- **Não afirma:**
  - que a decisão responde a variações do KPM: o sinal de congestionamento do NORI fica sempre verdadeiro nesse cenário, então a decisão foi a mesma nas três. A dependência KPM → decisão está coberta só pelos testes unitários (sem congestionamento, sem Control);
  - que o efeito aparece no KPM: o NORI não mede vazão por UE, e o efeito foi medido no FlowMonitor;
  - nada além do cenário único (um gNB, dois UEs, carga saturada);
  - que o NORI está intacto: o G3/G4 usa o patch `0001-rc-control-ack` do lock;
  - que a calibração é cega: ela vem de execuções cujos valores já eram conhecidos (seção 6).
