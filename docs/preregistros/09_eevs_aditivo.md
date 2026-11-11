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
