# Relatório de Execução das 3 Rodadas de Simulação (S0 a S8) com Foco em S6 Conflict Storm e 8 Reference xApps

**Projeto:** xApp-RDL (Resource and Decision Layer — Fase 1: H-RDL Determinístico)  
**Versão:** 1.2.0  
**Perfil Normativo:** O-RAN Release I/J | ETSI TS 104 039 (E2AP v02.03) | E2SM-KPM v03.00 | E2SM-RC v01.03  
**Motor de Simulação:** `ns-3.48` + `5G-LENA v5.1` + `NORI E2SIM`  
**Status de Validação:** **Aviso de Providência Científica Estrita (Zero Dados Sintéticos)**

---

## 1. Diretriz de Integridade Científica e Validação dos Gates 1 a 4

$$
\boxed{
\text{Resultado científico válido} \iff \text{ns-3 + 5G-LENA + NORI + E2 real}
}
$$

Os dados e métricas deste relatório foram purgados por se originarem de simulações/emulações preliminares ou vetores sintéticos/codecs. Os resultados experimentais oficiais serão gerados exclusivamente a partir de execuções **ns-3 / 5G-LENA v5.1 / NORI** reais aprovadas pelos Gates de Providência 1 a 4.

---

## 2. Estrutura dos Cenários S0 a S8 e 8 Reference xApps

Os cenários de validação experimental da Fase 1 foram organizados nas seguintes categorias:

- **Rodada 1 (Cenários Nominais e Controle Puro):**
  - **S0:** Clean Control (Sem Conflito / Pass-Through Limpo)
  - **S1:** Direct PRB Collision (Validação de Detecção Direta)
  - **S2:** Energy vs QoS (Shannon Trade-off EEVS)

- **Rodada 2 (Conflitos Complexos, Multi-Fatia e Mobilidade):**
  - **S3:** Multi-Slice TVS (URLLC vs eMBB vs ISAC Sensing)
  - **S4:** TS vs ES (Descarregamento sem Apagão)
  - **S5:** Temporal Ping-Pong (Histerese e Cooldown Lock)

- **Rodada 3 (Estresse Extremo, Tempestade de Conflitos e Closed-Loop):**
  - **S6:** Conflict Storm (Escalabilidade sob alta carga)
  - **S7:** Adversarial & Fault Safety (Zero-Violation Invariante)
  - **S8:** NORI Closed-Loop E2 (Cadeia Causal Gate 4)
