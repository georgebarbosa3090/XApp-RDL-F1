# Painel da campanha cl_piloto_ (semente 16904)

- **Execuções:** 18 (18 com SUCCESS); cenários ['G1', 'G2', 'S10', 'S11', 'S12', 'S13', 'S14', 'S15', 'S9']; baselines ['B3']; sementes [16904]
- **Commits:** ['18cb0ba']; tempo total de execução: 170 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 620; gNBs: 36
- Handovers observados no KPM: 144; ping-pong (volta à célula em ≤ 5 s): 2
- Janelas com célula dormindo: 628; mudanças de potência: 22

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 5264
- Propostas das xApps (RMR 30000): 866; recusas devolvidas às xApps: 778
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 54, 21000 → RANSlicer-GreenRAN (intenção de fatia): 54, 21001 → EnergySaver-GreenRAN (limiares de energia): 54

## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)

| e2_setup | subscription | kpm_t0 | decision | control_request | control_ack | control_failure | control_timeout | kpm_t1 |
|---|---|---|---|---|---|---|---|---|
| 36 | 82 | 5264 | 2582 | 88 | 88 | 0 | 0 | 88 |

- Veredito da cadeia: {'CADEIA_COMPLETA': 18}

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 2
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 8
- Pares e recursos: energysaver_greenran × fault_injector [estado da célula]: 2
- Resoluções da RDL por estratégia: EEVS: 78
- Tipos de conflito: INDIRECT: 66, INTER_CELL: 12

## Controle da RAN

- Ações por status: APPLIED: 88
- Ações por parâmetro: CELL_STATE:APPLIED: 10, HANDOVER:APPLIED: 24, PRB_QUOTA:APPLIED: 40, TX_POWER:APPLIED: 14

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: hrdl-pipeline: 128
- Consultas ao grafo de conhecimento: 0; escritas: 244

## Traffic Steering original (ric-app-ts)

- a1_20008: 6, anomalias_AD_30003: 104, handoff_REST: 788, mantidos_na_servidora: 862, predicoes_QP_30002: 1650

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| G1 | B3 | 16904 | SUCCESS | 9 | 0/0 | 4 | 9 | 13 | 30.057 | 7.072 |
| G1 | B3 | 16904 | SUCCESS | 9 | 0/0 | 4 | 9 | 13 | 30.057 | 7.072 |
| G2 | B3 | 16904 | SUCCESS | 2 | 0/0 | 0 | 2 | 7 | 1.79 | 6.274 |
| G2 | B3 | 16904 | SUCCESS | 2 | 0/0 | 0 | 2 | 7 | 1.79 | 6.274 |
| S10 | B3 | 16904 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 34.812 | 5.629 |
| S10 | B3 | 16904 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 34.812 | 5.629 |
| S11 | B3 | 16904 | SUCCESS | 6 | 0/0 | 0 | 6 | 0 | 20.479 | 5.393 |
| S11 | B3 | 16904 | SUCCESS | 6 | 0/0 | 0 | 6 | 0 | 20.479 | 5.393 |
| S12 | B3 | 16904 | SUCCESS | 2 | 0/0 | 0 | 2 | 0 | 7.017 | 286.263 |
| S12 | B3 | 16904 | SUCCESS | 2 | 0/0 | 0 | 2 | 0 | 7.017 | 286.263 |
| S13 | B3 | 16904 | SUCCESS | 216 | 0/1 | 0 | 7 | 25 | 28.992 | 8.08 |
| S13 | B3 | 16904 | SUCCESS | 216 | 0/1 | 0 | 7 | 25 | 28.992 | 8.08 |
| S14 | B3 | 16904 | SUCCESS | 5 | 0/0 | 0 | 5 | 0 | 49.142 | 7.883 |
| S14 | B3 | 16904 | SUCCESS | 5 | 0/0 | 0 | 5 | 0 | 49.142 | 7.883 |
| S15 | B3 | 16904 | SUCCESS | 184 | 0/0 | 0 | 8 | 22 | 0.532 | 7.821 |
| S15 | B3 | 16904 | SUCCESS | 184 | 0/0 | 0 | 8 | 22 | 0.532 | 7.821 |
| S9 | B3 | 16904 | SUCCESS | 9 | 0/0 | 0 | 5 | 5 | 0.585 | 24.903 |
| S9 | B3 | 16904 | SUCCESS | 9 | 0/0 | 0 | 5 | 5 | 0.585 | 24.903 |
