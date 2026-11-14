# Gate da cadeia E2 (semente 16903)

- **Execuções:** 2 (2 com SUCCESS); cenários ['G2', 'S15']; baselines ['B0', 'B3']; sementes [16903]
- **Commits:** ['c9b136b']; tempo total de execução: 2 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 54; gNBs: 4
- Handovers observados no KPM: 27; ping-pong (volta à célula em ≤ 5 s): 2
- Janelas com célula dormindo: 244; mudanças de potência: 6

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 596
- Propostas das xApps (RMR 30000): 51; recusas devolvidas às xApps: 4
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 6, 21000 → RANSlicer-GreenRAN (intenção de fatia): 6, 21001 → EnergySaver-GreenRAN (limiares de energia): 6

## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)

| e2_setup | subscription | kpm_t0 | decision | control_request | control_ack | control_failure | control_timeout | kpm_t1 |
|---|---|---|---|---|---|---|---|---|
| 4 | 10 | 596 | 298 | 47 | 47 | 4 | 0 | 47 |

- Veredito da cadeia: {'CADEIA_COMPLETA': 2}

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 0
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 0
- Pares e recursos: nenhum
- Resoluções da RDL por estratégia: nenhuma
- Tipos de conflito: nenhum

## Controle da RAN

- Ações por status: APPLIED: 47
- Ações por parâmetro: CELL_STATE:APPLIED: 4, HANDOVER:APPLIED: 41, TX_POWER:APPLIED: 2

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 15, hrdl-pipeline: 2
- Consultas ao grafo de conhecimento: 0; escritas: 2

## Traffic Steering original (ric-app-ts)

- a1_20008: 1, anomalias_AD_30003: 17, handoff_REST: 40, mantidos_na_servidora: 396, predicoes_QP_30002: 436

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| G2 | B3 | 16903 | SUCCESS | 2 | 0/0 | 0 | 2 | 3 | 1.802 | 4.904 |
| S15 | B0 | 16903 | SUCCESS | 49 | 0/0 | 0 | 45 | 24 | 0.595 | 9.594 |
