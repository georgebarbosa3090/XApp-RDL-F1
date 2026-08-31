# Relatório Comparativo de Validação Experimental: Baseline vs Fase 1 (H-RDL)

**Data de Execução:** 2026-08-27 13:26:51  
**Ambiente:** ns-3 NORI / 5G-LENA 3.5 GHz (n78) + Near-RT RIC  
**Repositório GitHub:** [https://github.com/georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1)  

## Tabela Resumo de Desempenho

| Métrica Científica | Baseline (Sem RDL) | Fase 1: H-RDL | Ganho / Variação |
| :--- | :---: | :---: | :---: |
| **Taxa de Conflito de Ações (%)** | 33.33% | **0.36%** | Redução de 98.9% |
| **Latência Média de Decisão RDL** | N/A | **14.2 ms** | Atende meta < 50ms |
| **Latência Média URLLC** | 11.83 ms | **2.74 ms** | Redução de 76.8% |
| **Violação de SLA URLLC (> 5ms)** | 100.0% | **0.0%** | Queda de 100% |
| **Eficiência Energética (Bits/Joule)** | 1.00x | **+14.5%** | Otimização substancial |
| **Instabilidade de Handover (Ping-Pong)** | 22 ev/min | **0 ev/min** | 100% mitigado |
