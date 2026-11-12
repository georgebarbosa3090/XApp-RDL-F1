# Pré-registro — EEVS com agregação aditiva (B3A) contra o B3 atual

Registrado em 2026-11-11, **antes** das execuções descritas aqui, no mesmo commit que cria a opção `RDL_EEVS_AGGREGATION=additive` e o baseline `B3A` do driver nativo. Qualquer desvio será relatado junto com os resultados.

## 1. Objetivo

O achado 55 ([07](../07_certificacao_e_achados.md)) mostrou que o EEVS divide QoS e energia pelo tamanho do subconjunto avaliado. Assim, acrescentar uma ação compatível com energia menor baixa a média, e o EEVS prefere o subconjunto menor. No S13 (desastre), o B3 desliga a célula em falha mas não admite o handover que evacua os UEs dela.

A agregação aditiva divide pelos alvos do conflito. Com ela, acrescentar uma ação compatível nunca baixa esses termos. O padrão continua `mean`, porque as campanhas já medidas usaram essa agregação.

## 2. O que muda (neste commit)

- `src/core/reasoning.py`: `eevs_aggregation` (`mean` | `additive`; configuração ou `RDL_EEVS_AGGREGATION`). No modo `additive`:
  - QoS = Σ(sla × prioridade) ÷ Σ(maior prioridade de cada alvo do conflito);
  - energia = Σ energia ÷ número de alvos do conflito.
- `scripts/certification/run_conflict_experiment.py`: baseline `B3A` = o mesmo pipeline da RDL com `additive`. O `B3` fixa `mean`.

**Verificação de decisão (cronograma, sem ns-3, feita antes deste registro).** Nos 17 cenários do catálogo, o B3A só difere do B3 em S2, S13 e S15:

| Cenário | B3 (mean) | B3A (additive) |
| :-- | :-- | :-- |
| S2 | cota de PRB do xSlice | cota de PRB do xSlice **e** o handover do Traffic Steering (10,2 s) |
| S13 | só `CELL_STATE = 0` na célula em falha | `CELL_STATE = 0` **e** o handover de evacuação (15,2 s) |
| S15 | só o handover | handover **e** cota de 50 % do Energy Saving (15,2 a 24,2 s) |

## 3. Desenho

- **Cenários:** S2, S13 e S15 (os únicos em que a decisão muda).
- **Baselines:** B3 e B3A.
- **Sementes:** 12001 a 12005, nunca rodadas, as mesmas para os dois baselines. São 30 execuções.
- **Comando** (Ubuntu do WSL, em primeiro plano, no painel Terminal):

  ```bash
  bash scripts/run_native_campaign.sh --scenarios "S2 S13 S15" --baselines "B3 B3A" --seeds 12001-12005 --jobs 2
  ```

## 4. Hipóteses e critérios

- **H10.1 (decisão, determinística):** em todas as sementes, os cronogramas do B3 e do B3A são os da tabela da seção 2.
- **H10.2 (S13, efeito):** vazão agregada na janela de conflito (`thp_conflict`) maior no B3A que no B3 em pelo menos 4 das 5 sementes pareadas. Justificativa: os UEs da célula desligada passam à vizinha por handover, em vez de esperar a falha de enlace (RLF) e o restabelecimento.
- **H10.3 (S2 e S15, não inferioridade):** em cada cenário, a média pareada de `thp_conflict` do B3A não fica mais de 5 % abaixo da do B3, e a de `delay_conflict_ms` não fica mais de 10 % acima.
- **Descritivo:** `thp_conflict`, `thp_post`, `delay_conflict_ms` e ações aplicadas, com IC 95 %.

## 5. Regras de relato

- Execução com falha do ns-3 é repetida uma vez com a mesma semente; se falhar de novo, entra como falha.
- A troca do padrão de `mean` para `additive` só é proposta se H10.2 e H10.3 forem confirmadas. Mesmo nesse caso, as campanhas anteriores continuam valendo com `mean`, e a troca exige um novo commit com o motivo.
- Nada fixado aqui é alterado depois de ver os dados.

## 6. Resultados (anexados em 2026-11-11, depois das execuções)

Execuções: `experiments/runs/nr_{S2,S13,S15}_{B3,B3A}_seed12001..12005` (30, todas `SUCCESS`).

**Desvio:** houve commits durante a campanha, e o executor grava o HEAD no início de cada execução. Por isso os manifestos registram quatro commits: `5ae0232` (2), `cddf572` (4), `35eded2` (18) e `083c8e6` (6). Entre eles mudaram:

- o chart do Neo4j e as figuras;
- um teste do CI;
- a precedência por campo da política A1 (`_apply_a1_policy` e o relatório `/governance`), que o harness não usa, porque não há política A1 nas execuções nativas.

O pipeline de decisão (Percepção, TVS/EEVS, Refinement), o harness e os cenários não mudaram. Análise: métricas de `scripts/certification/analyze_conflict_runs.py` por execução, na janela de conflito do catálogo.

| Hipótese | Resultado |
| :-- | :-- |
| **H10.1** (cronogramas) | **Confirmada em 30/30**: os cronogramas do B3 e do B3A são os da seção 2 em todas as sementes. |
| **H10.2** (S13, `thp_conflict` B3A > B3 em ≥ 4/5) | **Confirmada (5/5).** B3 25,26–25,94 Mb/s; B3A 27,40–28,15 Mb/s. O handover de evacuação leva os UEs da célula em falha à vizinha antes da RLF. |
| **H10.3** (S2 e S15, não inferioridade) | **Confirmada nos dois.** S2: vazão +5,8 % (186,77 → 197,66 Mb/s) e atraso −64 % (22,53 → 8,05 ms). S15: vazão +6,0 % (0,595 → 0,630 Mb/s) e atraso −63 % (19,99 → 7,31 ms). |

Descritivo (sem hipótese):

| Cenário | Baseline | Vazão na janela de conflito (Mb/s) | Atraso (ms) | Ações aplicadas |
| :-- | :-- | :-- | :-- | :-: |
| S2 | B3 | 179,5–197,5 | 6,7–36,9 | 5 |
| S2 | B3A | 197,0–198,3 | 6,7–8,5 | 6 |
| S13 | B3 | 25,3–25,9 | 5,5–11,6 | 1 |
| S13 | B3A | 27,4–28,1 | 5,6–12,1 | 2 |
| S15 | B3 | 0,56–0,62 | 19,2–21,0 | 1 |
| S15 | B3A | 0,61–0,64 | 7,0–7,7 | 10 |

**Consequência (regra da seção 5).** H10.2 e H10.3 foram confirmadas, então a troca do padrão de `mean` para `additive` pode ser **proposta**. Ela não foi feita aqui, por três motivos:

1. A regra exige um commit próprio com o motivo.
2. A campanha pré-registrada 10, agendada para 2026-11-12, fixa o B3 com `mean`.
3. As campanhas anteriores continuam valendo com `mean`.

Resultado em ambiente simulado (ns-3/5G-LENA, sem E2), com cinco sementes por par cenário × baseline.
