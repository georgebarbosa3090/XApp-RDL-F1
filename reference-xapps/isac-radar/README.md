# ISAC Radar Reference xApp (6G Integrated Sensing and Communication)

## Visão Geral
A **ISAC Radar xApp** gerencia a alocação de recursos de rádio compartilhados entre comunicações móveis e sensoriamento de radar ambiental (estimativa de velocidade, posição e rastreamento de alvos).

## Parâmetros de Controle
- `SENSING_RATIO`: Fração de recursos PRB / subportadoras alocadas para pulsos de radar (faixa: 0.0 a 0.60, padrão: 0.35).
- `RADAR_BURST_PERIOD`: Periodicidade dos disparos de sensoriamento.

## Métricas Expostas
- Endpoint HTTP `/metrics`
- Métricas: `isac_radar_proposals_total`, `isac_radar_sensing_ratio`
