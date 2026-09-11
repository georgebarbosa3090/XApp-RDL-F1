# Beamformer Reference xApp (Massive MIMO & Downtilt Optimizer)

## Visão Geral
A **Beamformer xApp** atua na otimização de cobertura e SINR em ambientes 5G-Advanced através do ajuste dinâmico do ângulo de inclinação elétrica vertical (*Vertical Downtilt*) e pesos de feixe MIMO.

## Parâmetros de Controle
- `VERTICAL_DOWNTILT`: Ângulo de inclinação vertical (faixa: 0.0° a 15.0°, padrão: 6.0°).
- `BEAM_WEIGHTS`: Matriz de pré-codificação e conformação de feixe.

## Métricas Expostas
- Endpoint HTTP `/metrics` (Prometheus)
- Métricas: `beamformer_proposals_total`, `beamformer_downtilt_degrees`
