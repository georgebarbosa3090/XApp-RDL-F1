# Relatório de Simulações Contínuas no Simulador ns-3 (5G-LENA v5.1 / ns-O-RAN NORI)

**Projeto:** xApp-RDL (Resource and Decision Layer — Fase 1: H-RDL Determinístico)  
**Perfil Normativo:** O-RAN Release I/J | E2AP v02.03 | E2SM-KPM v03.00 | E2SM-RC v01.03  
**Motor de Simulação:** `ns-3.48` / `5G-LENA v5.1` / `NORI Framework`  
**Status de Validação:** **Aviso de Providência Científica Estrita (Zero Dados Sintéticos)**

---

## 1. Diretriz de Integridade Científica

$$
\boxed{
\text{Resultado científico válido} \iff \text{ns-3 + 5G-LENA + NORI + E2 real}
}
$$

Este documento alinha a execução das simulações contínuas à diretriz estrita de **Zero Dados Sintéticos**. Todas as métricas de rede e decisões RDL devem provir da captura bruta dos arquivos XML do FlowMonitor do ns-3 e dos artefatos `.raw` de telemetria E2SM-KPM.

---

## 2. Validação da Infraestrutura Experimental

1. **Simulação 1 (TVS Conflict):** Avaliação de concorrência direta de recursos PRB entre fatias URLLC e eMBB.
2. **Simulação 2 (EEVS Trade-off):** Avaliação de modulação de potência de transmissão vs garantia de SLA.
3. **Simulação 3 (Multi-Semente & Closed-Loop):** Coleta de amostras independentes com rastreamento completo de proveniência (`validate_provenance.py`).
