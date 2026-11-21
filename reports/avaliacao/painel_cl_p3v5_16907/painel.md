# Painel da campanha cl_p3v5_ (semente 16907)

- **Execuções:** 3 (3 com SUCCESS); cenários ['S5']; baselines ['B0', 'B3', 'N12']; sementes [16907]
- **Commits:** ['fdfc9e9']; tempo total de execução: 96 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 72; gNBs: 6
- Handovers observados no KPM: 75; ping-pong (volta à célula em ≤ 5 s): 19
- Janelas com célula dormindo: 0; mudanças de potência: 0

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 894
- Propostas das xApps (RMR 30000): 84; recusas devolvidas às xApps: 2
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 9, 21000 → RANSlicer-GreenRAN (intenção de fatia): 9, 21001 → EnergySaver-GreenRAN (limiares de energia): 9

## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)

| e2_setup | subscription | kpm_t0 | decision | control_request | control_ack | control_failure | control_timeout | kpm_t1 |
|---|---|---|---|---|---|---|---|---|
| 6 | 12 | 894 | 447 | 82 | 81 | 0 | 1 | 81 |

- Veredito da cadeia: {'CADEIA_COMPLETA': 3}

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 3
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 0
- Pares e recursos: load_balancer × traffic_steering [associação de UE]: 3
- Resoluções da RDL por estratégia: EEVS: 26
- Tipos de conflito: INDIRECT: 26

## Controle da RAN

- Ações por status: APPLIED: 82
- Ações por parâmetro: HANDOVER:APPLIED: 72, PRB_QUOTA:APPLIED: 10

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 29, hrdl-pipeline: 48
- Consultas ao grafo de conhecimento: 223; escritas: 87

## Traffic Steering original (ric-app-ts)

- a1_20008: 3, anomalias_AD_30003: 423, handoff_REST: 71, mantidos_na_servidora: 731, predicoes_QP_30002: 802

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| S5 | B0 | 16907 | SUCCESS | 32 | 0/1 | 0 | 32 | 29 | 90.039 | 10.317 |
| S5 | B3 | 16907 | SUCCESS | 26 | 0/1 | 0 | 25 | 23 | 90.32 | 9.227 |
| S5 | N12 | 16907 | SUCCESS | 26 | 0/1 | 0 | 25 | 23 | 90.32 | 9.227 |
