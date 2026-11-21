# Painel da campanha cl_p1x85_ (semente 16907)

- **Execuções:** 2 (2 com SUCCESS); cenários ['S5']; baselines ['B0', 'B3']; sementes [16907]
- **Commits:** ['fdfc9e9']; tempo total de execução: 61 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 48; gNBs: 4
- Handovers observados no KPM: 25; ping-pong (volta à célula em ≤ 5 s): 7
- Janelas com célula dormindo: 0; mudanças de potência: 0

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 596
- Propostas das xApps (RMR 30000): 27; recusas devolvidas às xApps: 3
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 6, 21000 → RANSlicer-GreenRAN (intenção de fatia): 6, 21001 → EnergySaver-GreenRAN (limiares de energia): 6

## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)

| e2_setup | subscription | kpm_t0 | decision | control_request | control_ack | control_failure | control_timeout | kpm_t1 |
|---|---|---|---|---|---|---|---|---|
| 4 | 8 | 596 | 298 | 24 | 24 | 0 | 0 | 24 |

- Veredito da cadeia: {'CADEIA_COMPLETA': 2}

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 2
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 0
- Pares e recursos: load_balancer × traffic_steering [associação de UE]: 2
- Resoluções da RDL por estratégia: EEVS: 1, PINGPONG_GUARD: 2
- Tipos de conflito: INDIRECT: 1, INTER_CELL: 2

## Controle da RAN

- Ações por status: APPLIED: 24
- Ações por parâmetro: HANDOVER:APPLIED: 22, PRB_QUOTA:APPLIED: 2

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 12, hrdl-pipeline: 8
- Consultas ao grafo de conhecimento: 0; escritas: 11

## Traffic Steering original (ric-app-ts)

- a1_20008: 2, anomalias_AD_30003: 257, handoff_REST: 12, mantidos_na_servidora: 271, predicoes_QP_30002: 283

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| S5 | B0 | 16907 | SUCCESS | 15 | 0/1 | 0 | 15 | 14 | 92.057 | 6.643 |
| S5 | B3 | 16907 | SUCCESS | 12 | 0/1 | 0 | 9 | 11 | 93.049 | 6.441 |
