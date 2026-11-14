# Piloto da malha fechada, semente 16901

Gerado por `scripts/closed_loop/analisar_piloto.py`. Exploratório (docs/16, E7): serve para fixar o pré-registro 11, não para conclusões.

| cenario | baseline | commit | propostas | janelas_com_conflito | conflitos_em_5s | nao_selecionadas | aplicadas | recusadas | reversoes_prb_quota | vazao_media_mbps | atraso_medio_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S9 | B3 | b4593e8 | 22 | 0 | 0 | 17 | 5 | 0 | 0 | 0.592 | 23.233 |

## Propostas por xApp

| cenario | baseline | xapp_id | parametro | propostas |
|---|---|---|---|---|
| S9 | B3 | traffic_steering | HANDOVER | 22 |

## Pares de xApps em conflito (janelas)

- S9/B3: mesma janela: nenhum; em sequência (5 s): nenhum
