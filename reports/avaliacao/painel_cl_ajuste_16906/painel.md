# Painel da campanha cl_ajuste_ (semente 16906)

- **Execuções:** 4 (4 com SUCCESS); cenários ['S1', 'S2', 'S4', 'S5']; baselines ['B0']; sementes [16906]
- **Commits:** ['53d4eb1']; tempo total de execução: 285 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 114; gNBs: 7
- Handovers observados no KPM: 29; ping-pong (volta à célula em ≤ 5 s): 0
- Janelas com célula dormindo: 0; mudanças de potência: 2

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 1193
- Propostas das xApps (RMR 30000): 25; recusas devolvidas às xApps: 0
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 13, 21000 → RANSlicer-GreenRAN (intenção de fatia): 13, 21001 → EnergySaver-GreenRAN (limiares de energia): 13

## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)

| e2_setup | subscription | kpm_t0 | decision | control_request | control_ack | control_failure | control_timeout | kpm_t1 |
|---|---|---|---|---|---|---|---|---|
| 7 | 14 | 1193 | 646 | 25 | 25 | 0 | 0 | 25 |

- Veredito da cadeia: {'CADEIA_COMPLETA': 4}

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 0
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 2
- Pares e recursos: nenhum
- Resoluções da RDL por estratégia: nenhuma
- Tipos de conflito: nenhum

## Controle da RAN

- Ações por status: APPLIED: 25
- Ações por parâmetro: HANDOVER:APPLIED: 17, PRB_QUOTA:APPLIED: 6, TX_POWER:APPLIED: 2

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 15
- Consultas ao grafo de conhecimento: não registrado; escritas: não registrado

## Traffic Steering original (ric-app-ts)

- a1_20008: 3, anomalias_AD_30003: 523, handoff_REST: 17, mantidos_na_servidora: 2507, predicoes_QP_30002: 2524

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 | B0 | 16906 | SUCCESS | 3 | 0/0 | 0 | 3 | 0 | 165.873 | 12.966 |
| S2 | B0 | 16906 | SUCCESS | 7 | 0/0 | 2 | 7 | 4 | 114.217 | 6.675 |
| S4 | B0 | 16906 | SUCCESS | 10 | 0/0 | 0 | 10 | 20 | 193.001 | 9.59 |
| S5 | B0 | 16906 | SUCCESS | 5 | 0/0 | 0 | 5 | 5 | 86.066 | 10.61 |
