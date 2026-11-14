# Piloto da malha fechada, semente 16902

Gerado por `scripts/closed_loop/analisar_piloto.py`. Exploratório (docs/16, E7): serve para fixar o pré-registro 11, não para conclusões.

| cenario | baseline | commit | propostas | janelas_com_conflito | conflitos_em_5s | nao_selecionadas | aplicadas | recusadas | reversoes_prb_quota | vazao_media_mbps | atraso_medio_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G1 | B0 | 46d89b0 | 16 | 0 | 0 | 0 | 16 | 0 | 11 | 30.052 | 8.622 |
| G1 | B3 | 46d89b0 | 16 | 0 | 0 | 0 | 16 | 0 | 11 | 30.052 | 8.622 |
| G2 | B0 | 46d89b0 | 3 | 0 | 0 | 0 | 3 | 0 | 0 | 1.797 | 5.547 |
| G2 | B3 | 46d89b0 | 2 | 0 | 0 | 1 | 1 | 0 | 0 | 1.797 | 6.039 |
| S10 | B0 | 46d89b0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 34.804 | 5.591 |
| S10 | B3 | 46d89b0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 34.804 | 5.591 |
| S11 | B0 | 46d89b0 | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 20.479 | 5.398 |
| S11 | B3 | 46d89b0 | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 20.479 | 5.398 |
| S12 | B0 | 46d89b0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 7.017 | 286.263 |
| S12 | B3 | 46d89b0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 7.017 | 286.263 |
| S13 | B0 | 46d89b0 | 35 | 0 | 1 | 0 | 35 | 0 | 0 | 30.094 | 8.372 |
| S13 | B3 | 46d89b0 | 197 | 0 | 1 | 189 | 8 | 0 | 0 | 28.497 | 8.025 |
| S14 | B0 | 46d89b0 | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 49.142 | 7.883 |
| S14 | B3 | 46d89b0 | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 49.142 | 7.883 |
| S15 | B0 | 46d89b0 | 33 | 0 | 2 | 0 | 33 | 0 | 0 | 0.5 | 51.91 |
| S15 | B3 | 46d89b0 | 162 | 0 | 0 | 155 | 7 | 0 | 0 | 0.531 | 10.38 |
| S9 | B0 | 46d89b0 | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0.594 | 23.071 |
| S9 | B3 | 46d89b0 | 7 | 0 | 0 | 2 | 5 | 0 | 0 | 0.578 | 24.729 |

## Propostas por xApp

| cenario | baseline | xapp_id | parametro | propostas |
|---|---|---|---|---|
| G1 | B0 | ranslicer_greenran | PRB_QUOTA | 16 |
| G1 | B3 | ranslicer_greenran | PRB_QUOTA | 16 |
| G2 | B0 | energysaver_greenran | CELL_STATE | 1 |
| G2 | B0 | energysaver_greenran | HANDOVER | 1 |
| G2 | B0 | traffic_steering | HANDOVER | 1 |
| G2 | B3 | energysaver_greenran | HANDOVER | 1 |
| G2 | B3 | traffic_steering | HANDOVER | 1 |
| S10 | B0 | traffic_steering | HANDOVER | 1 |
| S10 | B3 | traffic_steering | HANDOVER | 1 |
| S11 | B0 | load_balancer | PRB_QUOTA | 6 |
| S11 | B3 | load_balancer | PRB_QUOTA | 6 |
| S12 | B0 | energysaver_greenran | TX_POWER | 1 |
| S12 | B0 | xslice | PRB_QUOTA | 1 |
| S12 | B3 | energysaver_greenran | TX_POWER | 1 |
| S12 | B3 | xslice | PRB_QUOTA | 1 |
| S13 | B0 | energysaver_greenran | CELL_STATE | 2 |
| S13 | B0 | energysaver_greenran | TX_POWER | 4 |
| S13 | B0 | fault_injector | CELL_STATE | 1 |
| S13 | B0 | traffic_steering | HANDOVER | 28 |
| S13 | B3 | energysaver_greenran | CELL_STATE | 1 |
| S13 | B3 | energysaver_greenran | TX_POWER | 4 |
| S13 | B3 | fault_injector | CELL_STATE | 1 |
| S13 | B3 | traffic_steering | HANDOVER | 191 |
| S14 | B0 | isac_radar | PRB_QUOTA | 5 |
| S14 | B3 | isac_radar | PRB_QUOTA | 5 |
| S15 | B0 | energysaver_greenran | CELL_STATE | 1 |
| S15 | B0 | energysaver_greenran | TX_POWER | 1 |
| S15 | B0 | rogue_xapp | PRB_QUOTA | 1 |
| S15 | B0 | rogue_xapp | TX_POWER | 4 |
| S15 | B0 | traffic_steering | HANDOVER | 26 |
| S15 | B3 | energysaver_greenran | CELL_STATE | 3 |
| S15 | B3 | rogue_xapp | PRB_QUOTA | 2 |
| S15 | B3 | rogue_xapp | TX_POWER | 4 |
| S15 | B3 | traffic_steering | HANDOVER | 153 |
| S9 | B0 | traffic_steering | HANDOVER | 6 |
| S9 | B3 | traffic_steering | HANDOVER | 7 |

## Pares de xApps em conflito (janelas)

- G1/B0: mesma janela: nenhum; em sequência (5 s): nenhum
- G1/B3: mesma janela: nenhum; em sequência (5 s): nenhum
- G2/B0: mesma janela: nenhum; em sequência (5 s): nenhum
- G2/B3: mesma janela: nenhum; em sequência (5 s): nenhum
- S10/B0: mesma janela: nenhum; em sequência (5 s): nenhum
- S10/B3: mesma janela: nenhum; em sequência (5 s): nenhum
- S11/B0: mesma janela: nenhum; em sequência (5 s): nenhum
- S11/B3: mesma janela: nenhum; em sequência (5 s): nenhum
- S12/B0: mesma janela: nenhum; em sequência (5 s): nenhum
- S12/B3: mesma janela: nenhum; em sequência (5 s): nenhum
- S13/B0: mesma janela: nenhum; em sequência (5 s): energysaver_greenran x fault_injector [estado_celula]=1
- S13/B3: mesma janela: nenhum; em sequência (5 s): energysaver_greenran x fault_injector [estado_celula]=1
- S14/B0: mesma janela: nenhum; em sequência (5 s): nenhum
- S14/B3: mesma janela: nenhum; em sequência (5 s): nenhum
- S15/B0: mesma janela: nenhum; em sequência (5 s): energysaver_greenran x rogue_xapp [potencia]=2
- S15/B3: mesma janela: nenhum; em sequência (5 s): nenhum
- S9/B0: mesma janela: nenhum; em sequência (5 s): nenhum
- S9/B3: mesma janela: nenhum; em sequência (5 s): nenhum
