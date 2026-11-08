# Análise dos experimentos de conflito (ns-3.48 + 5G-LENA v5.1)

Gerado em 2026-11-08T03:08:45Z por `scripts/certification/analyze_conflict_runs.py` a partir de 4 execução(ões) elegível(is) em `experiments/runs/nr_*`.

Avaliação em malha aberta: as propostas das xApps são decididas pelo baseline e aplicadas na RAN simulada; não há E2 nem realimentação de KPM. Valores: média ± IC 95% (t de Student) quando n ≥ 2.

| Cenário | Baseline | n | Vazão antes (Mbps) | Vazão no conflito (Mbps) | Vazão depois (Mbps) | Atraso no conflito (ms) | Ações aplicadas | Handovers | Ações inseguras aplicadas | Oscilações |
| :-- | :-- | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| S1 | B0 | 1 | 366.75 | 118.06 | 109.68 | 17.05 | 10.00 | 0.00 | 0.00 | 9.00 |
| S1 | B3 | 1 | 366.75 | 278.98 | 275.30 | 9.14 | 5.00 | 0.00 | 0.00 | 0.00 |
| S7 | B0 | 1 | 4.04 | 5.54 | 5.46 | 10.27 | 15.00 | 0.00 | 10.00 | 0.00 |
| S7 | B3 | 1 | 4.04 | 5.47 | 5.46 | 13.13 | 5.00 | 0.00 | 0.00 | 0.00 |

## Execuções

| run_id | seed | vazão no conflito | atraso | ações | inseguras | oscilações |
| :-- | --: | --: | --: | --: | --: | --: |
| `nr_S1_B0_seed1001` | 1001 | 118.06 | 17.05 | 10 | 0 | 9 |
| `nr_S1_B3_seed1001` | 1001 | 278.98 | 9.14 | 5 | 0 | 0 |
| `nr_S7_B0_seed1001` | 1001 | 5.54 | 10.27 | 15 | 10 | 0 |
| `nr_S7_B3_seed1001` | 1001 | 5.47 | 13.13 | 5 | 0 | 0 |
