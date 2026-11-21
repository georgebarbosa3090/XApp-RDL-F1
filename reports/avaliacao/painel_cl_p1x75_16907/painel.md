# Painel da campanha cl_p1x75_ (semente 16907)

- **Execuções:** 1 (1 com SUCCESS); cenários ['S5']; baselines ['B0']; sementes [16907]
- **Commits:** ['fdfc9e9']; tempo total de execução: 29 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 24; gNBs: 2
- Handovers observados no KPM: 24; ping-pong (volta à célula em ≤ 5 s): 21
- Janelas com célula dormindo: 0; mudanças de potência: 0

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 298
- Propostas das xApps (RMR 30000): 13; recusas devolvidas às xApps: 0
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 3, 21000 → RANSlicer-GreenRAN (intenção de fatia): 3, 21001 → EnergySaver-GreenRAN (limiares de energia): 3

## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)

| e2_setup | subscription | kpm_t0 | decision | control_request | control_ack | control_failure | control_timeout | kpm_t1 |
|---|---|---|---|---|---|---|---|---|
| 2 | 4 | 298 | 149 | 13 | 13 | 0 | 0 | 13 |

- Veredito da cadeia: {'CADEIA_COMPLETA': 1}

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 12
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 0
- Pares e recursos: load_balancer × traffic_steering [associação de UE]: 12
- Resoluções da RDL por estratégia: nenhuma
- Tipos de conflito: nenhum

## Controle da RAN

- Ações por status: APPLIED: 13
- Ações por parâmetro: HANDOVER:APPLIED: 13

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 11
- Consultas ao grafo de conhecimento: não registrado; escritas: não registrado

## Traffic Steering original (ric-app-ts)

- a1_20008: 1, anomalias_AD_30003: 15, handoff_REST: 5, mantidos_na_servidora: 10, predicoes_QP_30002: 15

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| S5 | B0 | 16907 | SUCCESS | 13 | 0/12 | 0 | 13 | 24 | 94.425 | 5.775 |
