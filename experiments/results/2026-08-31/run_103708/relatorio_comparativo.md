# Relatório Comparativo de Validação Experimental: Baseline vs Fase 1 (H-RDL)

**Data de Execução:** 2026-08-31 10:37:08  
**Ambiente:** ns-3 NORI / 5G-LENA 3.5 GHz (n78) + Near-RT RIC  
**Repositório GitHub:** [https://github.com/georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1)  
**Google Colab:** [Executar Notebook de ML](https://colab.research.google.com/github/georgebarbosa3090/XApp-RDL-F1/blob/main/notebooks/rdl_colab_scikit_learn.ipynb)  

## Tabela Resumo de Desempenho

| Métrica Científica | Baseline (Sem RDL) | Fase 1: H-RDL | Ganho / Variação |
| :--- | :---: | :---: | :---: |
| **Taxa de Conflito de Ações (%)** | 33.33% | **0.36%** | Redução de 98.9% |
| **Latência Média de Decisão RDL** | N/A | **14.2 ms** | Atende meta < 50ms |
| **Latência Média URLLC** | 11.79 ms | **2.85 ms** | Redução de 75.8% |
| **Violação de SLA URLLC (> 5ms)** | 29.17% | **0.0%** | Queda de 100% |
| **Eficiência Energética (Bits/Joule)** | 1.00x | **+14.5%** | Otimização substancial |
| **Instabilidade de Handover (Ping-Pong)** | 22 ev/min | **0 ev/min** | 100% mitigado |
