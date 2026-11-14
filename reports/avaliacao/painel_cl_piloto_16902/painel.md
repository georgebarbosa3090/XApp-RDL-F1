# Painel da campanha cl_piloto_ (semente 16902)

- **Execuções:** 18 (18 com SUCCESS); cenários ['G1', 'G2', 'S10', 'S11', 'S12', 'S13', 'S14', 'S15', 'S9']; baselines ['B0', 'B3']; sementes [16902]
- **Commits:** ['46d89b0']; tempo total de execução: 154 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 620; gNBs: 36
- Handovers observados no KPM: 125; ping-pong (volta à célula em ≤ 5 s): 0
- Janelas com célula dormindo: 449; mudanças de potência: 23

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 5264
- Propostas das xApps (RMR 30000): 505; recusas devolvidas às xApps: 347
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 54, 21000 → RANSlicer-GreenRAN (intenção de fatia): 54, 21001 → EnergySaver-GreenRAN (limiares de energia): 54

## Cadeia E2

- não registrado (execuções anteriores ao ciclo do docs/16 §10.1)

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 4
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 22
- Pares e recursos: energysaver_greenran × fault_injector [estado da célula]: 2; energysaver_greenran × rogue_xapp [potência]: 2
- Resoluções da RDL por estratégia: EEVS: 32
- Tipos de conflito: INDIRECT: 29, INTER_CELL: 3

## Controle da RAN

- Ações por status: APPLIED: 158
- Ações por parâmetro: CELL_STATE:APPLIED: 9, HANDOVER:APPLIED: 75, PRB_QUOTA:APPLIED: 57, TX_POWER:APPLIED: 17

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 57, hrdl-pipeline: 68
- Consultas ao grafo de conhecimento: não registrado; escritas: não registrado

## Traffic Steering original (ric-app-ts)

- a1_20008: 10, anomalias_AD_30003: 91, handoff_REST: 415, mantidos_na_servidora: 909, predicoes_QP_30002: 1324

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| G1 | B0 | 16902 | SUCCESS | 16 | 0/0 | 11 | 16 | 1 | 30.052 | 8.622 |
| G1 | B3 | 16902 | SUCCESS | 16 | 0/0 | 11 | 16 | 1 | 30.052 | 8.622 |
| G2 | B0 | 16902 | SUCCESS | 3 | 0/0 | 0 | 3 | 6 | 1.797 | 5.547 |
| G2 | B3 | 16902 | SUCCESS | 2 | 0/0 | 0 | 1 | 2 | 1.797 | 6.039 |
| S10 | B0 | 16902 | SUCCESS | 1 | 0/0 | 0 | 1 | 1 | 34.804 | 5.591 |
| S10 | B3 | 16902 | SUCCESS | 1 | 0/0 | 0 | 1 | 1 | 34.804 | 5.591 |
| S11 | B0 | 16902 | SUCCESS | 6 | 0/0 | 0 | 6 | 0 | 20.479 | 5.398 |
| S11 | B3 | 16902 | SUCCESS | 6 | 0/0 | 0 | 6 | 0 | 20.479 | 5.398 |
| S12 | B0 | 16902 | SUCCESS | 2 | 0/0 | 0 | 2 | 0 | 7.017 | 286.263 |
| S12 | B3 | 16902 | SUCCESS | 2 | 0/0 | 0 | 2 | 0 | 7.017 | 286.263 |
| S13 | B0 | 16902 | SUCCESS | 35 | 0/1 | 0 | 35 | 36 | 30.094 | 8.372 |
| S13 | B3 | 16902 | SUCCESS | 197 | 0/1 | 0 | 8 | 26 | 28.497 | 8.025 |
| S14 | B0 | 16902 | SUCCESS | 5 | 0/0 | 0 | 5 | 0 | 49.142 | 7.883 |
| S14 | B3 | 16902 | SUCCESS | 5 | 0/0 | 0 | 5 | 0 | 49.142 | 7.883 |
| S15 | B0 | 16902 | SUCCESS | 33 | 0/2 | 0 | 33 | 20 | 0.5 | 51.91 |
| S15 | B3 | 16902 | SUCCESS | 162 | 0/0 | 0 | 7 | 20 | 0.531 | 10.38 |
| S9 | B0 | 16902 | SUCCESS | 6 | 0/0 | 0 | 6 | 6 | 0.594 | 23.071 |
| S9 | B3 | 16902 | SUCCESS | 7 | 0/0 | 0 | 5 | 5 | 0.578 | 24.729 |
