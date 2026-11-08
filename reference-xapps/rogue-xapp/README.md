# Rogue (teste de segurança)

Injeta propostas fora dos limites e com alternância rápida para verificar que o Safety Guard as bloqueia.

- **`TX_POWER`:** valores extremos (por exemplo 45 dBm, acima do limite configurado) em intervalos menores que 500 ms.
- **`PRB_QUOTA`:** cotas inválidas (acima de 100 % ou negativas).

O comportamento equivalente na simulação é o cenário S7 (proposta insegura de `TX_POWER`); ver [`docs/03_taxonomia_de_conflitos_e_cenarios.md`](../../docs/03_taxonomia_de_conflitos_e_cenarios.md).
