# Pré-registro — conflitos entre células: S4 e S5 × B0–B3 na pilha nativa

Registrado em 2026-11-10, **antes** das execuções descritas aqui, no mesmo commit que põe a Percepção no relógio simulado do experimento nativo e faz o handover confirmado proteger a célula de destino até ser substituído. Qualquer desvio será relatado junto com os resultados.

## 1. Objetivo

Até 2026-11-10 a H-RDL não detectava conflitos entre células (achado 11), e as campanhas de S4 e S5 registradas até então refletem isso. O achado 52 introduziu `ConflictType.INTER_CELL` ([02 §4.1](../02_modelo_de_decisao_h_rdl.md#41-percepção-conflitos-agrupados-por-alvo)). Esta campanha mede a decisão nova na RAN simulada (ns-3.48 + 5G-LENA v5.1, sem E2) e o efeito na vazão e no atraso, contra os baselines B0–B2 nas mesmas sementes.

## 2. O que muda no código (neste commit)

- **Experimento nativo:** no B3, a Percepção passa a usar o relógio simulado, como o Refinement já usava, e cada proposta recebe o instante simulado do fechamento da janela (`run_conflict_experiment.py`). Sem isso, a janela de ping-pong seria medida em tempo de parede: todas as janelas são decididas em milissegundos.
- **Regra `HANDOVER_INTO_REDUCED_CELL`:** um handover confirmado protege a célula de destino até ser substituído por outro handover do mesmo nó de origem (`handover_hold_s` opcional). Antes deste commit, a proteção valia só por `pingpong_window_s` (5 s). Na simulação offline do cronograma do S4, isso deixava o Energy Saving zerar a potência da gNB1 nos últimos 5 s do conflito, com os UEs já nela.

## 3. Desenho

- **Cenários:** S4 (Traffic Steering move UEs da gNB0 para a gNB1 em 15,0 s, prioridade 80; Energy Saving pede 0 dBm na gNB1 a cada 1 s de 15,05 a 24,05 s, prioridade 65) e S5 (Traffic Steering gNB0 → gNB1 a cada 2 s de 18 a 24 s, prioridade 80; Load Balancer gNB1 → gNB0 a cada 2 s de 19 a 25 s, prioridade 70). Catálogo: `simulations/ns3/conflicts/catalog.json`.
- **Baselines:** B0, B1, B2 e B3.
- **Sementes:** **1006 a 1010**, nunca rodadas; as mesmas para os quatro baselines, o que dá 40 execuções. As sementes 1001–1005 já têm execuções (de antes da mudança) e o executor pula execuções concluídas.
- **Comando** (Ubuntu do WSL, em primeiro plano):

  ```bash
  bash scripts/run_native_campaign.sh --scenarios "S4 S5" --seeds 1006-1010 --jobs 2
  ```

## 4. Hipóteses e critérios

- **H9.1 (decisão, determinística):** o cronograma do B3 (`decisions.json`), em todas as sementes, é:
  - **S4:** um único handover gNB0 → gNB1 (15,2 s) e **nenhum** `TX_POWER` na gNB1. Os B0–B2 aplicam os 10 `TX_POWER` de 0 dBm.
  - **S5:** os 4 handovers do Traffic Steering (18,2; 20,2; 22,2; 24,2 s) e **nenhum** do Load Balancer. Os B0–B2 aplicam os 8 handovers.
- **H9.2 (aplicação):** em cada execução, o número de ações aplicadas na RAN (`actions_applied` da análise) é igual ao do cronograma do baseline.
- **H9.3 (efeito, direcional, só S4):** vazão agregada na janela de conflito (`thp_conflict`) maior no B3 que no B0 em pelo menos 4 das 5 sementes, pareadas. Justificativa: no B3 a gNB1 mantém a potência com os UEs recebidos.
- **Descritivo, sem hipótese:** `thp_conflict`, `thp_post` e `delay_conflict_ms` por cenário × baseline, com IC 95 %; diferenças pareadas B3 − Bx por semente; no S5, nenhuma hipótese de direção (menos handovers pode ajudar ou atrapalhar a vazão). As execuções B3 das sementes 1001–1005, de antes da mudança, são citadas só como histórico; não são pareadas com estas.

## 5. Regras de relato

- Execução com falha do ns-3 é repetida uma vez com a mesma semente; se falhar de novo, entra como falha no relato.
- H9.1 e H9.2 se aplicam por execução; o relato lista as que não cumprirem.
- Nada fixado aqui é alterado depois de ver os dados.
