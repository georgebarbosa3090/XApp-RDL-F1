# Painel da campanha cl_piloto_ (semente 16901)

- **Execuções:** 18 (18 com SUCCESS); cenários ['G1', 'G2', 'S10', 'S11', 'S12', 'S13', 'S14', 'S15', 'S9']; baselines ['B0', 'B3']; sementes [16901]
- **Commits:** ['9f31e26', 'fd2cb0f']; tempo total de execução: 169 min

## Rede (gNBs, UEs e interações)

- UEs registrados (máximo conectado por execução, somado): 620; gNBs: 36
- Handovers observados no KPM: 193; ping-pong (volta à célula em ≤ 5 s): 0
- Janelas com célula dormindo: 459; mudanças de potência: 26

## Mensagens (RAN, Near-RT RIC e Non-RT RIC)

- Indications KPM (janela × gNB): 5264
- Propostas das xApps (RMR 30000): 285; recusas devolvidas às xApps: 48
- Políticas A1 (Non-RT RIC → A1 → destino): 20001 → RDL (pesos e limites): 51, 21000 → RANSlicer-GreenRAN (intenção de fatia): 51, 21001 → EnergySaver-GreenRAN (limiares de energia): 51

## Cadeia E2

- não registrado (execuções anteriores ao ciclo do docs/16 §10.1)

## Conflitos e oscilações

- Janelas com conflito (mesmo gNB e recurso): 0; em sequência (≤ 5 s): 4
- Oscilações (inversões de sentido em TX_POWER e PRB_QUOTA aplicados): 142
- Pares e recursos: energysaver_greenran × fault_injector [estado da célula]: 2; energysaver_greenran × rogue_xapp [potência]: 2
- Resoluções da RDL por estratégia: EEVS: 20
- Tipos de conflito: INDIRECT: 17, INTER_CELL: 3

## Controle da RAN

- Ações por status: APPLIED: 237
- Ações por parâmetro: CELL_STATE:APPLIED: 11, HANDOVER:APPLIED: 12, PRB_QUOTA:APPLIED: 192, TX_POWER:APPLIED: 22

## Regras, políticas e grafo de conhecimento

- Janelas decididas por regra: apply-all-at-window-close: 187, hrdl-pipeline: 93
- Consultas ao grafo de conhecimento: não registrado; escritas: não registrado

## Por execução

| cenário | baseline | semente | status | propostas | conflitos (janela/seq.) | oscilações | ações aplicadas | HO | vazão Mb/s | atraso ms |
|---|---|---|---|---|---|---|---|---|---|---|
| G1 | B0 | 16901 | SUCCESS | 151 | 0/0 | 131 | 151 | 14 | 30.087 | 6.935 |
| G1 | B3 | 16901 | SUCCESS | 58 | 0/0 | 11 | 18 | 14 | 30.136 | 7.357 |
| G2 | B0 | 16901 | SUCCESS | 2 | 0/0 | 0 | 2 | 5 | 1.802 | 5.477 |
| G2 | B3 | 16901 | SUCCESS | 2 | 0/0 | 0 | 0 | 0 | 1.803 | 7.929 |
| S10 | B0 | 16901 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 34.812 | 5.269 |
| S10 | B3 | 16901 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 34.812 | 5.269 |
| S11 | B0 | 16901 | SUCCESS | 8 | 0/0 | 0 | 8 | 20 | 19.943 | 18.495 |
| S11 | B3 | 16901 | SUCCESS | 8 | 0/0 | 0 | 8 | 20 | 19.943 | 18.495 |
| S12 | B0 | 16901 | SUCCESS | 2 | 0/0 | 0 | 2 | 0 | 7.017 | 286.263 |
| S12 | B3 | 16901 | SUCCESS | 2 | 0/0 | 0 | 2 | 0 | 7.017 | 286.263 |
| S13 | B0 | 16901 | SUCCESS | 11 | 0/1 | 0 | 11 | 44 | 28.894 | 16.942 |
| S13 | B3 | 16901 | SUCCESS | 11 | 0/1 | 0 | 9 | 36 | 29.37 | 9.284 |
| S14 | B0 | 16901 | SUCCESS | 5 | 0/0 | 0 | 5 | 0 | 49.142 | 7.823 |
| S14 | B3 | 16901 | SUCCESS | 5 | 0/0 | 0 | 5 | 0 | 49.142 | 7.823 |
| S15 | B0 | 16901 | SUCCESS | 10 | 0/2 | 0 | 10 | 20 | 0.483 | 26.271 |
| S15 | B3 | 16901 | SUCCESS | 10 | 0/0 | 0 | 6 | 20 | 0.509 | 9.351 |
| S9 | B0 | 16901 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 0.575 | 18.801 |
| S9 | B3 | 16901 | SUCCESS | 0 | 0/0 | 0 | 0 | 0 | 0.575 | 18.801 |
