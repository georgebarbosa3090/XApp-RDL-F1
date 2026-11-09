# Pré-registro — campanha do G5: S8 × B0–B3 × 30 sementes com E2 real

Registrado em 2026-11-09, **antes** das execuções descritas aqui, no mesmo commit dos baselines na xApp e do critério do G5 no certificador. Qualquer desvio será relatado junto com os resultados.

## 1. Objetivo

O gate G5 (docs/05) exige uma campanha com E2 real e pelo menos 30 sementes pareadas por baseline B0–B3, com o RIC Control decidido por cada baseline. Até aqui, a bancada NORI só tinha o B3 (H-RDL), e os baselines B0–B2 existiam só na pilha nativa, sem E2.

## 2. O que muda no código (neste commit)

- **Baselines na xApp kpm-probe**, em modo `catalog`: o baseline é lido de `/data/rdl_baseline`. A implementação é `src/closed_loop/catalog_loop.decide_baseline`, com a mesma semântica da pilha nativa (`run_conflict_experiment.py`), numa janela única por execução:
  - **B0** (sem coordenação): toda proposta atuável vai à RAN na ordem de chegada (instante e, no empate, o identificador da proposta); vale a última.
  - **B1** (FIFO): por alvo, a primeira a chegar.
  - **B2** (prioridade estática): por alvo, a de maior prioridade.
  - **B3:** o H-RDL, como na campanha S0–S8.
- **Fonte da decisão** registrada pela xApp: `BASELINE_B0`, `BASELINE_B1`, `BASELINE_B2` ou `H_RDL`. O B0 envia um Control por proposta, em sequência, e o ACK de cada um é correlacionado pelo `RICInstanceID`.
- **Efeito na RAN:** quando há mais de um Control antes do KPM_t1 (só no B0), vale o último, que é o que fica aplicado. Com um único Control, nada muda.
- **G5 no certificador:** passa a seguir a definição do docs/05. Conta só execuções da bancada NORI que cumprem as três condições:
  - cadeia E2 completa no PCAP;
  - Control decidido pelo próprio baseline do manifesto (fonte registrada pela xApp, ligada ao PCAP por sha256);
  - disparo pelo KPM_t0.

  O par é (cenário, semente, condição) presente nos quatro baselines, e o mínimo é 30 pares. Antes, o certificador contava execuções de qualquer pilha, sem exigir E2.

## 3. Desenho

- **Cenário:** S8, o closed loop do NORI. A xslice pede cota de PRB 25 % (prioridade 90) e a embb_throughput pede 80 % (prioridade 60), no mesmo alvo.
- **Baselines:** B0, B1, B2 e B3.
- **Sementes:** **5001 a 5030**, nunca rodadas; as mesmas para os quatro baselines, o que dá 120 execuções.
- **Condição:** a padrão, 100 MHz: `--simTime=40 --ns3::E2Interface::E2Periodicity=1 --trafficRate=300Mb/s`.
- **Ordem:** por semente, os quatro baselines em sequência (B0, B1, B2, B3). Cada semente concluída forma um conjunto pareado.
- **Regra de efeito:** a que o certificador aplica a execuções novas, `v6-ratio-apply` (previsão relativa, curva v5 a 100 MHz).

  Ressalva: o desenho v7 está em andamento e indica que, com outra banda, o teto age em PRBs absolutos. Esta campanha roda na banda da calibração.

## 4. Hipóteses e critérios

- **H8.1 (cadeia e fonte):** em cada uma das 120 execuções há E2 Setup, Subscription, KPM_t0, RIC Control, ACK correlacionado e KPM_t1. A fonte da decisão corresponde ao baseline e o tshark concorda com o dissecador.
- **H8.2 (decisões):**

  | Baseline | Controls (eMBB/URLLC) | Cota final |
  | :-: | :-- | :-: |
  | B0 | 80/20, depois 25/75 | 25/75 |
  | B1 | 80/20 (embb_throughput chega primeiro pelo identificador) | 80/20 |
  | B2 | 25/75 (xslice tem prioridade maior) | 25/75 |
  | B3 | 80/20 (H-RDL, TVS) | 80/20 |

- **H8.3 (efeito, regra v6):** em cada baseline, pelo menos 27 das 30 execuções são `CONSISTENT`. As previsões:
  - **B1 e B3:** URLLC = 0,5046 × vazão antes, e a eMBB sem queda.
  - **B0 e B2:** eMBB = 0,6285 × vazão antes (teto de 25 %), e a URLLC sem queda (teto de 75 %, acima do nível livre).
- **G5:** `CERTIFIED` se o certificador encontrar pelo menos 30 (cenário, semente, condição) pareados nos quatro baselines com G4 certificado.
- **Comparação descritiva, sem hipótese de superioridade:** vazão por fatia e vazão total depois do Control, por baseline, e diferenças pareadas B3 − Bx por semente.

## 5. Procedimento

1. **Pré-registro:** este documento, os baselines na xApp, o efeito com mais de um Control, o G5 no certificador, os roteiros com `--baselines` e os testes entram no mesmo commit.
2. **Execução:** ao vivo, em primeiro plano, com a xApp implantada a partir desse commit:

   ```bash
   bash scripts/run_nori_campaign.sh --scenarios "S8" --baselines "B0 B1 B2 B3" --seeds "$(seq -s ' ' 5001 5030)"
   ```

3. **Análise:** a coleta por execução, depois o certificador e o resumo, com `--baselines "B0 B1 B2 B3"`.

## 6. Como os resultados serão relatados

- Todas as execuções entram no relatório. Uma falha técnica fica registrada e não é repetida em silêncio; repetição só com nova semente, declarada.
- O G5 é relatado como o certificador o calcular. Se faltarem pares por falha, o relatório diz quantos faltam.
- Regras e critérios não serão ajustados depois de ver os resultados.

## 7. Ameaças à validade conhecidas

- **Um cenário (S8) e uma condição (100 MHz):** o G5 certifica a campanha com E2 real, mas não generaliza para outros cenários.
- **Baselines numa janela única:** a pilha nativa repete as propostas periodicamente; na bancada NORI, a decisão é única por execução.
- **Regra de efeito v6:** confirmada a 100 MHz (desenho v6). Uma semente que mude a vazão de base, como a 1005, pode cair fora do que a regra cobre (desenho v7).
- **Mesmas limitações das campanhas anteriores:** um gNB, dois UEs, saturação, FlowMonitor como medida, NORI com o patch do ACK e sinal de congestionamento sempre verdadeiro.

## 8. Desvios declarados durante a campanha (2026-11-09, antes das execuções de reposição)

- **Semente 5012, B0:** o B0 decide em ~1 ms e disparou na Indication de formato 1, antes de processar a de formato 3 do mesmo período, que chegou 0,5 ms depois. As duas chegaram antes do Control, no fio. A decisão usou os UEs do período anterior, e o KPM_t0 não está entre as entradas. Cadeia E2 completa, ACKs correlacionados e efeito `CONSISTENT`, mas o par não conta para o G5. Correção futura, fora desta campanha: decidir só com o par de formatos do período.
- **Sementes 5028 (B3) e 5029 (B0, B1, B2, B3):** a partir das 12:01 UTC, o E2Mgr perdeu o registro da instância do E2Term na RNIB ("E2TInstance not found"). Sem rota para o E2 Setup, o NORI enviou o E2 Setup Request sem resposta. As execuções afetadas ficaram com cadeia vazia (`NOT_TESTABLE`) e não contam:
  - o B3 da 5028, o B0 e o B1 da 5029 e o B3 da 5029 foram coletados e ficam no repositório;
  - o B2 da 5029 foi interrompido e está em `experiments/runs_failed/`.

  A plataforma foi recuperada reiniciando o E2Mgr e o E2Term, com o E2Term registrado de novo e conferido em `/v1/e2t/list`. Uma execução curta de verificação da plataforma, `nori_S3_B3_smoke_seed9001` (S3, sem Control), confirma E2 Setup, Subscription e Indications antes da retomada. Durante a recuperação, o laço da campanha chegou a iniciar o B0 da semente 5030 no pod. Essa execução foi encerrada e apagada antes de qualquer coleta, e nenhum dado dela foi visto.
- **Reposição:** a semente 5030, que ainda não tinha rodado, roda normalmente, com os quatro baselines. Os três pares perdidos (5012, 5028 e 5029) são repostos pelas sementes **5031, 5032 e 5033**, com os quatro baselines e o mesmo código, sem nenhuma alteração. Se outro par falhar, a próxima semente (5034, 5035...) é declarada aqui antes de rodar.

## 9. Resultado (registrado depois das execuções, 2026-11-09)

A xApp kpm-probe foi implantada a partir do commit do pré-registro (`87d5282`) e rodou o `src/` dele em todas as execuções, inclusive nas de reposição. Resumo completo em [`reports/nori/resumo_campanha_nori_20261109T130646Z.md`](../reports/nori/resumo_campanha_nori_20261109T130646Z.md) e certificado `reports/certification/certificate_20261109T130613Z.md`.

**G5 `CERTIFIED`:** 30 (cenário, semente) pareados nos quatro baselines com E2 real. São as sementes 5001–5033, menos 5012, 5028 e 5029 (seção 8). O certificador contou execuções com cadeia E2 e decisão do próprio baseline: B0 31, B1 32, B2 32 e B3 121 (as de B3 incluem as campanhas anteriores). O G6 passou de `BLOCKED` para `NOT_CERTIFIED` e agora depende só de uma reprodução independente.

- **H8.1 cumprida em todas as execuções válidas.** Cadeia completa, fonte da decisão igual ao baseline, disparo pelo KPM_t0, ACK correlacionado e tshark de acordo. As exceções são as 6 execuções dos desvios declarados na seção 8: a corrida no B0 da 5012 e a perda de registro do E2Term no RIC (5028 B3 e 5029 inteira).
- **H8.2 cumprida nos 30 pares.**

  | Baseline | Controls no PCAP | Cotas aplicadas |
  | :-: | :-: | :-: |
  | B0 | 2 | 25/75 |
  | B1 | 1 | 80/20 |
  | B2 | 1 | 25/75 |
  | B3 | 1 | 80/20 |

- **H8.3 cumprida:** todas as execuções válidas saíram `CONSISTENT` pela regra v6 (B0 31/31, B1 32/32, B2 32/32 e B3 31/31). A regra v5 deu o mesmo resultado.

**Comparação descritiva (30 pares, vazão depois do Control).** O desvio-padrão entre sementes ficou abaixo de 0,01 Mb/s.

| Baseline | eMBB (Mb/s) | URLLC (Mb/s) | Total (Mb/s) |
| :-: | --: | --: | --: |
| B0 (sem coordenação) | 95,24 | 151,49 | 246,73 |
| B1 (FIFO) | 151,49 | 76,45 | 227,93 |
| B2 (prioridade estática) | 95,24 | 151,49 | 246,73 |
| B3 (H-RDL) | 151,49 | 76,45 | 227,93 |

Diferença pareada B3 − Bx na vazão total: −18,79 Mb/s contra B0 e B2, e 0,00 contra B1, igual em todas as 30 sementes.

**Leitura.** No S8, o H-RDL escolheu a proposta da embb_throughput (80 %) por utilidade TVS, embora a xslice (25 %) tenha prioridade maior. Isso preserva a vazão da eMBB e restringe a URLLC. A vazão total fica 18,8 Mb/s abaixo da que o B0 e o B2 entregam, porque esses aplicam o teto de 25 % na eMBB e deixam a URLLC livre. O pré-registro não fixou nenhuma hipótese de superioridade, e o resultado não mostra que o H-RDL seja melhor em vazão total neste cenário. O que a campanha certifica é a cadeia closed-loop com E2 real em cada baseline, com 30 sementes pareadas.
