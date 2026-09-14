# Relatório Científico de Avaliação Experimental — Baseline sem RDL ($B_0$) vs. H-RDL ($B_1$)

**Projeto:** xApp-RDL Fase 1 (H-RDL — Resource and Decision Layer Determinística e Segura)  
**Autor:** George Alexandro Ferreira Barbosa (PPGC / UFPA)  
**Ambiente de Co-Simulação:** Ubuntu 22.04 LTS (WSL2), ns-3.48, CTTC 5G-LENA v5.1, ns-O-RAN / NORI E2SIM  
**Padrões O-RAN:** E2AP v02.03, E2SM-KPM v03.00, E2SM-RC v01.03  
**Status de Validação:** **Aviso de Providência Científica Estrita (Zero Dados Sintéticos)**

---

## 1. Diretriz de Integridade Científica e Validação dos Gates 1 a 4

$$
\boxed{
\text{Resultado científico válido} \iff \text{ns-3 + 5G-LENA + NORI + E2 real}
}
$$

Os dados e métricas deste relatório foram purgados por se originarem de simulações/emulações preliminares ou vetores sintéticos/codecs. Os resultados experimentais oficiais serão gerados exclusivamente a partir de execuções **ns-3 / 5G-LENA v5.1 / NORI** reais aprovadas pelos Gates de Providência 1 a 4:

- **Gate 1:** Interoperabilidade KPM Real com captura de `.raw` via SCTP e validação semântica com FlowMonitor XML ($\epsilon < 5\%$).
- **Gate 2:** Providência de Hashes SHA256 de binários, cenários `.cc`, sementes e manifestos de execução (`execution_manifest.json`).
- **Gate 3:** Controle E2SM-RC em Malha Fechada sobre transporte SCTP real.
- **Gate 4:** Fechamento da Cadeia Causal RAN $\text{KPM}(t_0) \to \text{H-RDL} \to \text{Control} \to \text{NORI} \to \text{ns-3} \to \text{KPM}(t_1)$.

---

## 2. Metodologia de Co-Simulação e Protocolo Experimental

Para a campanha experimental com dados reais, o protocolo de comparação entre o Baseline ($B_0$) e o H-RDL ($B_1$) observará:

1. **Topologia 3GPP TR 38.901 UMi:** 2 gNodeBs (Macro 43 dBm e Micro 30 dBm) com 30 UEs sob tráfego misto URLLC / eMBB / mMTC em Banda n78 (3.5 GHz, 100 MHz BWP).
2. **xApps Concorrentes Instanciadas:** `qos-xslice`, `energy-saving` e `traffic-steering`.
3. **Métricas Físicas de Verificação:** Extraídas diretamente do `FlowMonitor` do ns-3 e sincronizadas com a telemetria `E2SM-KPM v03.00`.
4. **Isolamento de Ambientes:** Testes funcionais e codecs de software em `tests/` são mantidos isolados da geração de tabelas e figuras científicas.
