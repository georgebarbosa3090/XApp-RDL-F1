# Rogue Stress Reference xApp (Security & Fault Injection)

## Visão Geral
A **Rogue xApp** atua na injeção controlada de comandos descalibrados, agressivos e com alta taxa de oscilação (*parameter flipping*), validando se o H-RDL bloqueia 100% das ações perigosas (*Zero Unsafe Actions Executed*).

## Parâmetros de Teste
- `TX_POWER`: Injeção de valores extremos (e.g. 45 dBm vs limite de 23 dBm) em alta frequência (< 500ms).
- `PRB_QUOTA`: Injeção de quotas inválidas (> 100% ou negativas).
