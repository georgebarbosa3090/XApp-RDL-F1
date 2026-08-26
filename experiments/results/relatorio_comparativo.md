# Relatório Comparativo de Validação Experimental: Baseline vs Fase 1 (H-RDL)

**Data de Execução:** 26/08/2026  
**Ambiente:** ns-3 NORI (5G-LENA 3.5 GHz n78) + Near-RT RIC (E2AP/SCTP 36422)  

## Tabela Resumo de Desempenho

| Métrica Científica | Baseline (Sem RDL) | Fase 1: H-RDL | Ganho / Variação |
| :--- | :---: | :---: | :---: |
| **Taxa de Conflito de Ações (%)** | 33.33% | **0.45%** | Redução de 96.8% |
| **Latência Média de Decisão RDL** | N/A | **14.2 ms** | Atende meta < 50ms |
| **Latência Média URLLC** | 11.41 ms | **2.82 ms** | Redução de 75.6% |
| **Violação de SLA URLLC (> 5ms)** | 93.33% | **0.0%** | Queda de 93.7% |
| **Eficiência Energética (Bits/Joule)** | 1.00x | **+14.5%** | Otimização substancial |
| **Instabilidade de Handover (Ping-Pong)** | 22 ev/min | **0 ev/min** | 100% mitigado |
