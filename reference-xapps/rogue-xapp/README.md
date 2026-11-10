# Rogue (teste de segurança)

Injeta propostas fora dos limites e com alternância rápida para verificar que o Safety Guard as bloqueia.

- **`TX_POWER`:** alterna 45 dBm (acima do limite) e 5 dBm a cada 500 ms.
- **`PRB_QUOTA` inválida:** não é gerada por esta xApp; a proposta insegura de PRB está no cenário S7 do catálogo.
- **Limitação:** a xApp só gera e registra as propostas; não as envia à RDL.

O comportamento equivalente na simulação é o cenário S7 (proposta insegura de `TX_POWER`); ver [`docs/03_cenarios_e_conflitos.md`](../../docs/03_cenarios_e_conflitos.md).
