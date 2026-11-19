# Painel da campanha cl_ajuste4_ (semente 16906)

- **Execuções:** 2 (2 com SUCCESS); cenários ['S5']; baselines ['B0', 'B3']; sementes [16906]
- **Commits:** ['93e4c31']; tempo total de execução: 77 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 48; gNBs: 4
- Handovers observados no KPM: 21; ping-pong (volta à célula em ≤ 5 s): 0
- Janelas com célula dormindo: 0; mudanças de potência: 0

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 596
- Propostas das xApps (RMR 30000): 44; recusas devolvidas às xApps: 24
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 6, 21000 → RANSlicer-GreenRAN (intenção de fatia): 6, 21001 → EnergySaver-GreenRAN (limiares de energia): 6

## Cadeia E2 (ciclo NORI S8: setup → subscrição → KPM_t0 → Control → ACK → KPM_t1)

| e2_setup | subscription | kpm_t0 | decision | control_request | control_ack | control_failure | control_timeout | kpm_t1 |
|---|---|---|---|---|---|---|---|---|
| 4 | 8 | 596 | 298 | 20 | 20 | 0 | 0 | 20 |

- Veredito da cadeia: {'CADEIA_COMPLETA': 2}

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 0
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 0
- Pares e recursos: nenhum
- Resoluções da RDL por estratégia: nenhuma
- Tipos de conflito: nenhum

## Controle da RAN

- Ações por status: APPLIED: 20
- Ações por parâmetro: HANDOVER:APPLIED: 19, PRB_QUOTA:APPLIED: 1

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 3, hrdl-pipeline: 14
- Consultas ao grafo de conhecimento: 0; escritas: 25

## Traffic Steering original (ric-app-ts)

- a1_20008: 2, anomalias_AD_30003: 281, handoff_REST: 27, mantidos_na_servidora: 929, predicoes_QP_30002: 956

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| S5 | B0 | 16906 | SUCCESS | 11 | 0/0 | 0 | 11 | 11 | 84.043 | 10.93 |
| S5 | B3 | 16906 | SUCCESS | 33 | 0/0 | 0 | 9 | 10 | 84.303 | 11.129 |
