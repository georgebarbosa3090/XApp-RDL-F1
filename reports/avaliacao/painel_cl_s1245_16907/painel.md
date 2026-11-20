# Painel da campanha cl_s1245_ (semente 16907)

- **Execuções:** 8 (8 com SUCCESS); cenários ['S1', 'S2', 'S4', 'S5']; baselines ['B0', 'B3']; sementes [16907]
- **Commits:** ['725889f']; tempo total de execução: 1703 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 228; gNBs: 14
- Handovers observados no KPM: 80; ping-pong (volta à célula em ≤ 5 s): 25
- Janelas com célula dormindo: 0; mudanças de potência: 2

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 2386
- Propostas das xApps (RMR 30000): 186; recusas devolvidas às xApps: 115
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 26, 21000 → RANSlicer-GreenRAN (intenção de fatia): 26, 21001 → EnergySaver-GreenRAN (limiares de energia): 26

## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)

| e2_setup | subscription | kpm_t0 | decision | control_request | control_ack | control_failure | control_timeout | kpm_t1 |
|---|---|---|---|---|---|---|---|---|
| 14 | 28 | 2386 | 1292 | 71 | 71 | 0 | 0 | 71 |

- Veredito da cadeia: {'CADEIA_COMPLETA': 8}

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 0
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 0
- Pares e recursos: nenhum
- Resoluções da RDL por estratégia: EEVS: 7, PINGPONG_GUARD: 64
- Tipos de conflito: INDIRECT: 7, INTER_CELL: 64

## Controle da RAN

- Ações por status: APPLIED: 71
- Ações por parâmetro: HANDOVER:APPLIED: 59, PRB_QUOTA:APPLIED: 10, TX_POWER:APPLIED: 2

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 22, hrdl-pipeline: 80
- Consultas ao grafo de conhecimento: 0; escritas: 151

## Traffic Steering original (ric-app-ts)

- a1_20008: 6, anomalias_AD_30003: 1040, handoff_REST: 146, mantidos_na_servidora: 5617, predicoes_QP_30002: 5763

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 | B0 | 16907 | SUCCESS | 3 | 0/0 | 0 | 3 | 0 | 140.703 | 10.982 |
| S1 | B3 | 16907 | SUCCESS | 3 | 0/0 | 0 | 3 | 0 | 140.703 | 10.982 |
| S2 | B0 | 16907 | SUCCESS | 8 | 0/0 | 0 | 8 | 7 | 131.024 | 12.508 |
| S2 | B3 | 16907 | SUCCESS | 8 | 0/0 | 0 | 8 | 7 | 131.024 | 12.508 |
| S4 | B0 | 16907 | SUCCESS | 7 | 0/0 | 0 | 7 | 7 | 167.411 | 8.11 |
| S4 | B3 | 16907 | SUCCESS | 7 | 0/0 | 0 | 7 | 7 | 167.411 | 8.11 |
| S5 | B0 | 16907 | SUCCESS | 21 | 0/0 | 0 | 21 | 26 | 93.385 | 7.569 |
| S5 | B3 | 16907 | SUCCESS | 129 | 0/0 | 0 | 14 | 26 | 93.173 | 9.092 |
