# Painel da campanha cl_s0s7_ (semente 16905)

- **Execuções:** 16 (16 com SUCCESS); cenários ['S0', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7']; baselines ['B0', 'B3']; sementes [16905]
- **Commits:** ['ce3fef8']; tempo total de execução: 58 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 428; gNBs: 34
- Handovers observados no KPM: 0; ping-pong (volta à célula em ≤ 5 s): 0
- Janelas com célula dormindo: 0; mudanças de potência: 12

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 3866
- Propostas das xApps (RMR 30000): 86; recusas devolvidas às xApps: 21
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 38, 21000 → RANSlicer-GreenRAN (intenção de fatia): 38, 21001 → EnergySaver-GreenRAN (limiares de energia): 38

## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)

| e2_setup | subscription | kpm_t0 | decision | control_request | control_ack | control_failure | control_timeout | kpm_t1 |
|---|---|---|---|---|---|---|---|---|
| 34 | 92 | 3866 | 1834 | 65 | 65 | 9 | 0 | 65 |

- Veredito da cadeia: {'CADEIA_COMPLETA': 16}

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 12
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 3
- Pares e recursos: isac_radar × load_balancer [PRB]: 12
- Resoluções da RDL por estratégia: EEVS: 15, TVS: 3
- Tipos de conflito: DIRECT: 3, INDIRECT: 15

## Controle da RAN

- Ações por status: APPLIED: 65
- Ações por parâmetro: PRB_QUOTA:APPLIED: 43, TX_POWER:APPLIED: 22

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 24, hrdl-pipeline: 24
- Consultas ao grafo de conhecimento: 0; escritas: 42

## Traffic Steering original (ric-app-ts)

- a1_20008: 4, anomalias_AD_30003: 194, handoff_REST: 0, mantidos_na_servidora: 1560, predicoes_QP_30002: 1560

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | B0 | 16905 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 3.072 | 6.118 |
| S0 | B3 | 16905 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 3.072 | 6.118 |
| S1 | B0 | 16905 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 366.563 | 7.683 |
| S1 | B3 | 16905 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 366.563 | 7.683 |
| S2 | B0 | 16905 | SUCCESS | 1 | 0/0 | 0 | 1 | 0 | 199.0 | 13.178 |
| S2 | B3 | 16905 | SUCCESS | 1 | 0/0 | 0 | 1 | 0 | 199.0 | 13.178 |
| S3 | B0 | 16905 | SUCCESS | 4 | 0/0 | 0 | 4 | 0 | 7.094 | 32.335 |
| S3 | B3 | 16905 | SUCCESS | 4 | 0/0 | 0 | 4 | 0 | 7.094 | 32.335 |
| S4 | B0 | 16905 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 32.354 | 5.392 |
| S4 | B3 | 16905 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 32.354 | 5.392 |
| S5 | B0 | 16905 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 7.82 | 103.383 |
| S5 | B3 | 16905 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 7.82 | 103.383 |
| S6 | B0 | 16905 | SUCCESS | 26 | 0/6 | 3 | 26 | 0 | 15.271 | 141.56 |
| S6 | B3 | 16905 | SUCCESS | 24 | 0/6 | 0 | 21 | 0 | 17.689 | 138.085 |
| S7 | B0 | 16905 | SUCCESS | 13 | 0/0 | 0 | 4 | 0 | 5.396 | 12.25 |
| S7 | B3 | 16905 | SUCCESS | 13 | 0/0 | 0 | 4 | 0 | 5.396 | 12.25 |
