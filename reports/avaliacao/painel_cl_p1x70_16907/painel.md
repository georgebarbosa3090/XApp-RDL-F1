# Painel da campanha cl_p1x70_ (semente 16907)

- **Execuções:** 1 (1 com SUCCESS); cenários ['S5']; baselines ['B0']; sementes [16907]
- **Commits:** ['fdfc9e9']; tempo total de execução: 32 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 24; gNBs: 2
- Handovers observados no KPM: 5; ping-pong (volta à célula em ≤ 5 s): 2
- Janelas com célula dormindo: 0; mudanças de potência: 0

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 298
- Propostas das xApps (RMR 30000): 3; recusas devolvidas às xApps: 0
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 3, 21000 → RANSlicer-GreenRAN (intenção de fatia): 3, 21001 → EnergySaver-GreenRAN (limiares de energia): 3

## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)

| e2_setup | subscription | kpm_t0 | decision | control_request | control_ack | control_failure | control_timeout | kpm_t1 |
|---|---|---|---|---|---|---|---|---|
| 2 | 4 | 298 | 149 | 3 | 3 | 0 | 0 | 3 |

- Veredito da cadeia: {'CADEIA_COMPLETA': 1}

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 0
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 0
- Pares e recursos: nenhum
- Resoluções da RDL por estratégia: nenhuma
- Tipos de conflito: nenhum

## Controle da RAN

- Ações por status: APPLIED: 3
- Ações por parâmetro: HANDOVER:APPLIED: 3

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 1
- Consultas ao grafo de conhecimento: não registrado; escritas: não registrado

## Traffic Steering original (ric-app-ts)

- a1_20008: 1, anomalias_AD_30003: 11, handoff_REST: 0, mantidos_na_servidora: 11, predicoes_QP_30002: 11

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| S5 | B0 | 16907 | SUCCESS | 3 | 0/0 | 0 | 3 | 5 | 95.472 | 5.741 |
