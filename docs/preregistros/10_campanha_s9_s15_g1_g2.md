# Pré-registro — campanha pareada S9–S15, G1 e G2 × B0–B3 na pilha nativa

Registrado em 2026-11-11, **antes** das execuções descritas aqui. Agendado para 2026-11-12 às 9h (horário local), a pedido. Qualquer desvio será relatado junto com os resultados.

## 1. Objetivo

Os cenários S9–S15 e os GreenRAN G1 e G2 foram reconstruídos sobre o rádio NR do 5G-LENA em 2026-11-10. Até agora só tiveram uma rodada curta (uma semente, B0 e B3; [03 §2.4](../03_cenarios_e_conflitos.md)). Esta campanha mede, com réplicas e os quatro baselines, o efeito da decisão H-RDL na RAN simulada (ns-3.48 + 5G-LENA v5.1, sem E2).

## 2. Estado do código

- Commit em que este pré-registro entra (o mesmo da execução; o executor grava `repo_git_sha` em cada manifesto).
- **S12 e S14:** portadora reduzida em 2026-11-11 (S12 10 MHz, S14 50 MHz; `load_note` no catálogo), para o teto de PRB restringir (achado 57b). Uma rodada curta (semente 9102, B0 e B3) roda antes, em 2026-11-11. O critério de exclusão foi fixado antes do resultado: o teto não restringe se a vazão do B3 na janela de conflito (`thp_conflict`) diferir da do B0 em menos de 1 %. Nesse caso, o cenário sai desta campanha. Se a rodada curta de um cenário não terminar, ele também sai. A exclusão é registrada como desvio neste arquivo, num commit feito antes do início da campanha.
- O B3 usa o EEVS com agregação `mean` (o padrão; o pré-registro 09 testa a aditiva à parte).
- **Desvio (registrado em 2026-11-12 às 10h05, antes do início da campanha):** as quatro execuções curtas da semente 9102 terminaram com `SUCCESS` e hashes. A vazão na janela de conflito (`thp_conflict`, `scripts/certification/analyze_conflict_runs.py`) foi a seguinte:

  | Cenário | B0 (Mb/s) | B3 (Mb/s) | Diferença | Decisão |
  | :-- | :-: | :-: | :-: | :-- |
  | S12 | 9,406 | 18,254 | +94,1 % | **fica na campanha** |
  | S14 | 49,152 | 49,152 | 0,0 % | **sai da campanha** (o teto não restringe) |

  A campanha roda com S9, S10, S11, S12, S13, S15, G1 e G2. O início também atrasou cerca de uma hora em relação às 9h previstas: a tarefa agendada apontava para a pasta antiga do repositório, removida depois da mudança para `C:\Users\georg\RDL`. Nada do que este pré-registro fixa foi alterado.

## 3. Desenho

- **Cenários:** S9, S10, S11, S12, S13, S14, S15, G1 e G2 (`simulations/ns3/conflicts/catalog.json`).
- **Baselines:** B0, B1, B2 e B3.
- **Sementes:** 11001 a 11005, nunca rodadas, as mesmas para os quatro baselines. São 180 execuções.
- **Duração estimada:** pela rodada curta (S12 ≈ 37 min, S10 e S13 ≈ 25 min, S14 ≈ 19 min, S11 ≈ 11 min, G1 ≈ 6,5 min, S9, S15 e G2 < 2 min por execução), ≈ 43 h de CPU. Com 2 execuções em paralelo, ≈ 22 h de relógio. O executor retoma de onde parou: execuções concluídas são puladas.
- **Comando** (Ubuntu do WSL, em primeiro plano, no painel Terminal):

  ```bash
  bash scripts/run_native_campaign.sh --scenarios "S9 S10 S11 S12 S13 S14 S15 G1 G2" --baselines "B0 B1 B2 B3" --seeds 11001-11005 --jobs 2
  ```

## 4. Hipóteses e critérios

Por cenário, comparação pareada por semente, na janela de conflito do catálogo:

| Hipótese | Cenário | Critério (B3 contra B0, pareado; confirmada se valer em ≥ 4 das 5 sementes) |
| :-- | :-- | :-- |
| H11.1 | G2 | `thp_conflict` maior no B3 (o B0 desliga as duas RUs vizinhas) |
| H11.2 | G1 | `delay_conflict_ms` menor no B3 (teto de 80 % protege as câmeras) |
| H11.3 | S11 | número de handovers aplicados menor no B3 (ping-pong suprimido) |
| H11.4 | S15 | nenhuma ação insegura aplicada no B3 (`unsafe_applied = 0`) e pelo menos uma no B0 |
| H11.5 | S12, S14 | se mantidos (seção 2): `thp_conflict` do B3 diferente do B0 em ≥ 4/5 sementes (o teto restringe) |

- **Sem hipótese de direção, só descritivo:** S9, S10 e S13. Na rodada curta, o B3 piorou o atraso no S10 e não evacuou a célula no S13 (achado 55); o S9 depende da reconexão por RLF.
- **Descritivo em todos:** `thp_pre`, `thp_conflict`, `thp_post`, `delay_conflict_ms`, ações aplicadas e oscilações por cenário × baseline, com IC 95 %; diferenças pareadas B3 − Bx.

## 5. Regras de relato

- Execução com falha do ns-3 é repetida uma vez com a mesma semente (`--retry-failed`); se falhar de novo, entra como falha.
- Interrupção (desligamento, falta de disco ou de memória): a campanha é retomada com o mesmo comando; execuções incompletas são refeitas desde o início.
- Os números da rodada curta (semente 9101) não entram nesta análise.
- Nada fixado aqui é alterado depois de ver os dados.
