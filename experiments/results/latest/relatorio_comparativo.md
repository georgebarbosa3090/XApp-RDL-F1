# Relatório Comparativo de Validação Experimental: Baseline vs Fase 1 (H-RDL) vs Fase 2 (CA-RDL)

**Data de Execução:** 2026-08-31 12:50:56  
**Ambiente:** ns-3 NORI / 5G-LENA 3.5 GHz (n78) + Near-RT RIC  
**Repositório Fase 1:** [https://github.com/georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1)  
**Repositório Fase 2:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  
**Google Colab:** [Executar Notebook de ML](https://colab.research.google.com/github/georgebarbosa3090/XApp-RDL-F1/blob/main/notebooks/rdl_colab_scikit_learn.ipynb)  

## Tabela Resumo de Desempenho Multi-Fases

| Métrica Científica | Baseline (Sem RDL) | Fase 1: H-RDL | Fase 2: CA-RDL (MARL) | Ganho Fase 2 vs Baseline |
| :--- | :---: | :---: | :---: | :---: |
| **Taxa de Conflito de Ações (%)** | 33.33% | 0.36% | **0.09%** | Redução de 99.7% |
| **Latência Média de Decisão RDL** | N/A | 14.2 ms | **12.5 ms** | Meta Near-RT < 50ms |
| **Latência Média URLLC** | 11.79 ms | 2.85 ms | **1.82 ms** | Redução de 84.6% |
| **Violação de SLA URLLC (> 5ms)** | 29.17% | 0.0% | **0.0%** | Queda de 100% |
| **Eficiência Energética (Bits/Joule)** | 1.00x | +14.5% | **+18.2%** | Otimização Cognitiva |
| **Instabilidade de Handover (Ping-Pong)** | 22 ev/min | 0 ev/min | **0 ev/min** | 100% mitigado |
