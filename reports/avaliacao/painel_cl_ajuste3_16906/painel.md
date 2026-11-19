# Painel da campanha cl_ajuste3_ (semente 16906)

- **Execuções:** 2 (2 com SUCCESS); cenários ['S5']; baselines ['B0', 'B3']; sementes [16906]
- **Commits:** ['69e241b']; tempo total de execução: 72 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 48; gNBs: 4
- Handovers observados no KPM: 130; ping-pong (volta à célula em ≤ 5 s): 18
- Janelas com célula dormindo: 0; mudanças de potência: 0

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 596
- Propostas das xApps (RMR 30000): 263; recusas devolvidas às xApps: 237
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 6, 21000 → RANSlicer-GreenRAN (intenção de fatia): 6, 21001 → EnergySaver-GreenRAN (limiares de energia): 6

## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)

| e2_setup | subscription | kpm_t0 | decision | control_request | control_ack | control_failure | control_timeout | kpm_t1 |
|---|---|---|---|---|---|---|---|---|
| 4 | 8 | 596 | 298 | 26 | 26 | 0 | 0 | 26 |

- Veredito da cadeia: {'CADEIA_COMPLETA': 2}

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 2
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 0
- Pares e recursos: load_balancer × traffic_steering [associação de UE]: 2
- Resoluções da RDL por estratégia: EEVS: 178
- Tipos de conflito: INDIRECT: 178

## Controle da RAN

- Ações por status: APPLIED: 26
- Ações por parâmetro: HANDOVER:APPLIED: 19, PRB_QUOTA:APPLIED: 7

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 8, hrdl-pipeline: 49
- Consultas ao grafo de conhecimento: 0; escritas: 270

## Traffic Steering original (ric-app-ts)

- a1_20008: 2, anomalias_AD_30003: 282, handoff_REST: 250, mantidos_na_servidora: 1235, predicoes_QP_30002: 1485

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| S5 | B0 | 16906 | SUCCESS | 17 | 0/1 | 0 | 17 | 23 | 79.878 | 8.862 |
| S5 | B3 | 16906 | SUCCESS | 246 | 0/1 | 0 | 9 | 107 | 73.101 | 10.345 |
