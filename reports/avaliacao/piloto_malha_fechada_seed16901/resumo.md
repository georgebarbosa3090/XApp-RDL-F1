# Piloto da malha fechada, semente 16901

Gerado por `scripts/closed_loop/analisar_piloto.py`. Exploratório (docs/16, E7): serve para fixar o pré-registro 11, não para conclusões.

| cenario | baseline | commit | propostas | janelas_com_conflito | conflitos_em_5s | nao_selecionadas | aplicadas | recusadas | reversoes_prb_quota | vazao_media_mbps | atraso_medio_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G1 | B0 | 9f31e26 | 151 | 0 | 0 | 0 | 151 | 0 | 131 | 30.087 | 6.935 |
| G1 | B3 | 9f31e26 | 58 | 0 | 0 | 40 | 18 | 0 | 11 | 30.136 | 7.357 |
| G2 | B0 | 9f31e26 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 1.802 | 5.477 |
| G2 | B3 | fd2cb0f | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 1.803 | 7.929 |
| S10 | B0 | 9f31e26 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 34.812 | 5.269 |
| S10 | B3 | 9f31e26 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 34.812 | 5.269 |
| S11 | B0 | 9f31e26 | 8 | 0 | 0 | 0 | 8 | 0 | 0 | 19.943 | 18.495 |
| S11 | B3 | 9f31e26 | 8 | 0 | 0 | 0 | 8 | 0 | 0 | 19.943 | 18.495 |
| S12 | B0 | 9f31e26 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 7.017 | 286.263 |
| S12 | B3 | 9f31e26 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 7.017 | 286.263 |
| S13 | B0 | 9f31e26 | 11 | 0 | 1 | 0 | 11 | 0 | 0 | 28.894 | 16.942 |
| S13 | B3 | 9f31e26 | 11 | 0 | 1 | 2 | 9 | 0 | 0 | 29.37 | 9.284 |
| S14 | B0 | 9f31e26 | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 49.142 | 7.823 |
| S14 | B3 | 9f31e26 | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 49.142 | 7.823 |
| S15 | B0 | 9f31e26 | 10 | 0 | 2 | 0 | 10 | 0 | 0 | 0.483 | 26.271 |
| S15 | B3 | 9f31e26 | 10 | 0 | 0 | 4 | 6 | 0 | 0 | 0.509 | 9.351 |
| S9 | B0 | 9f31e26 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.575 | 18.801 |
| S9 | B3 | 9f31e26 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.575 | 18.801 |

## Propostas por xApp

| cenario | baseline | xapp_id | parametro | propostas |
|---|---|---|---|---|
| G1 | B0 | energysaver_greenran | HANDOVER | 1 |
| G1 | B0 | ranslicer_greenran | PRB_QUOTA | 150 |
| G1 | B3 | energysaver_greenran | HANDOVER | 1 |
| G1 | B3 | ranslicer_greenran | PRB_QUOTA | 57 |
| G2 | B0 | energysaver_greenran | CELL_STATE | 1 |
| G2 | B0 | energysaver_greenran | HANDOVER | 1 |
| G2 | B3 | energysaver_greenran | HANDOVER | 2 |
| S11 | B0 | load_balancer | PRB_QUOTA | 6 |
| S11 | B0 | traffic_steering | HANDOVER | 2 |
| S11 | B3 | load_balancer | PRB_QUOTA | 6 |
| S11 | B3 | traffic_steering | HANDOVER | 2 |
| S12 | B0 | energysaver_greenran | TX_POWER | 1 |
| S12 | B0 | xslice | PRB_QUOTA | 1 |
| S12 | B3 | energysaver_greenran | TX_POWER | 1 |
| S12 | B3 | xslice | PRB_QUOTA | 1 |
| S13 | B0 | energysaver_greenran | CELL_STATE | 2 |
| S13 | B0 | energysaver_greenran | TX_POWER | 6 |
| S13 | B0 | fault_injector | CELL_STATE | 1 |
| S13 | B0 | traffic_steering | HANDOVER | 2 |
| S13 | B3 | energysaver_greenran | CELL_STATE | 1 |
| S13 | B3 | energysaver_greenran | TX_POWER | 7 |
| S13 | B3 | fault_injector | CELL_STATE | 1 |
| S13 | B3 | traffic_steering | HANDOVER | 2 |
| S14 | B0 | isac_radar | PRB_QUOTA | 5 |
| S14 | B3 | isac_radar | PRB_QUOTA | 5 |
| S15 | B0 | energysaver_greenran | CELL_STATE | 3 |
| S15 | B0 | energysaver_greenran | TX_POWER | 1 |
| S15 | B0 | rogue_xapp | PRB_QUOTA | 1 |
| S15 | B0 | rogue_xapp | TX_POWER | 4 |
| S15 | B0 | traffic_steering | HANDOVER | 1 |
| S15 | B3 | energysaver_greenran | CELL_STATE | 3 |
| S15 | B3 | rogue_xapp | PRB_QUOTA | 2 |
| S15 | B3 | rogue_xapp | TX_POWER | 4 |
| S15 | B3 | traffic_steering | HANDOVER | 1 |

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
