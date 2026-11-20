# Painel da campanha cl_lb3_ (semente 16907)

- **Execuções:** 2 (2 com SUCCESS); cenários ['S5']; baselines ['B0', 'B3']; sementes [16907]
- **Commits:** ['725889f']; tempo total de execução: 56 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 48; gNBs: 4
- Handovers observados no KPM: 4; ping-pong (volta à célula em ≤ 5 s): 0
- Janelas com célula dormindo: 0; mudanças de potência: 0

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 596
- Propostas das xApps (RMR 30000): 4; recusas devolvidas às xApps: 0
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 6, 21000 → RANSlicer-GreenRAN (intenção de fatia): 6, 21001 → EnergySaver-GreenRAN (limiares de energia): 6

## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)

| e2_setup | subscription | kpm_t0 | decision | control_request | control_ack | control_failure | control_timeout | kpm_t1 |
|---|---|---|---|---|---|---|---|---|
| 4 | 8 | 596 | 298 | 4 | 4 | 0 | 0 | 4 |

- Veredito da cadeia: {'CADEIA_COMPLETA': 2}

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 0
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 0
- Pares e recursos: nenhum
- Resoluções da RDL por estratégia: nenhuma
- Tipos de conflito: nenhum

## Controle da RAN

- Ações por status: APPLIED: 4
- Ações por parâmetro: HANDOVER:APPLIED: 4

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 1, hrdl-pipeline: 1
- Consultas ao grafo de conhecimento: 0; escritas: 1

## Traffic Steering original (ric-app-ts)

- a1_20008: 2, anomalias_AD_30003: 282, handoff_REST: 0, mantidos_na_servidora: 282, predicoes_QP_30002: 282

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| S5 | B0 | 16907 | SUCCESS | 2 | 0/0 | 0 | 2 | 2 | 94.771 | 5.429 |
| S5 | B3 | 16907 | SUCCESS | 2 | 0/0 | 0 | 2 | 2 | 94.771 | 5.429 |
