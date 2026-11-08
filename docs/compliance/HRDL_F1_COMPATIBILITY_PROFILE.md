# Perfil de Compatibilidade Congelado — H-RDL F1 Compatibility Profile

**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL Determinística)  
**Documento:** `HRDL_F1_COMPATIBILITY_PROFILE.md`  
**Status:** **CONGELADO (Fase 1 Release Candidate)**  
**Escopo:** Definição formal das versões normativas, especificações O-RAN ALLIANCE, emparelhamento O-RAN SC e pilha experimental ns-3/NORI para a Fase 1.

---

## 1. Visão Geral da Hierarquia do Projeto

O projeto estabelece uma hierarquia rigorosa em 5 camadas para evitar ambiguidades entre especificações teóricas, softwares de referência e o motor de simulação:

| Camada | Autoridade / Entidade | Componentes / Escopo no XApp-RDL-F1 |
| :--- | :--- | :--- |
| **1. Normativa** | **O-RAN ALLIANCE** | Especificações E2AP v02.03, E2SM-KPM v03.00, E2SM-RC v01.03, Near-RT RIC Architecture. |
| **2. Implementação de Referência** | **O-RAN Software Community (O-RAN SC)** | Release J: E2Term (SCTP/RMR), Subscription Manager (REST API), RMR Router, DBAAS (Redis). |
| **3. Ambiente Experimental** | **ns-3 + 5G-LENA (+ NORI)** | Duas pilhas: nativa ns-3.48 + 5G-LENA v5.1 (sem E2) e NORI oficial ns-3.42 + 5G-LENA `78b7179` + NORI `8a30867` (E2 v3.01, via Helm). |
| **4. Contribuição Científica** | **H-RDL Core (Fase 1)** | Algoritmos de Percepção (200ms), Raciocínio TVS/EEVS, Safety Guards e Causal Tracker. |
| **5. Reprodutibilidade & Evidência** | **Metodologia ACM / IEEE** | Rastreabilidade de seeds, hashes SHA-256, logs brutos read-only e 7 Gates formais (G0 a G6). |

---

## 2. Parâmetros Congelados do H-RDL F1 Profile

$$\boxed{\text{H-RDL F1 Compatibility Profile (Frozen)}}$$

```yaml
profile_name: "H-RDL F1 Compatibility Profile"
status: "FROZEN"
e2ap_version: "v02.03"
e2sm_kpm_version: "v03.00"
e2sm_rc_version: "v01.03"
oran_sc_release: "Release J"
native_stack:              # backend NS3_5GLENA: FlowMonitor dos cenários S0-S7, sem E2
  ns3_version: "3.48"      # d2add90
  lena_version: "v5.1"     # cedcead
nori_stack:                # backend NORI_NS3: única pilha com E2 real
  ns3_version: "3.42"      # ab4cce0 (fixado pelo Dockerfile oficial do NORI)
  lena_commit: "78b7179"
  nori_commit: "8a30867"
  e2sim_commit: "da6f82f"
  nori_e2ap: "v03.01"
  nori_e2sm_kpm: "v03.00"
  nori_e2sm_rc: "v03.01"
  oran_sc_release: "Release I"
decision_window_ms: 200
conflict_cooldown_s: 10.0
kpm_reporting_period_s: 0.20
```

### Tabela Canônica de Componentes

| Componente | Versão Congelada | Função no Projeto |
| :--- | :---: | :--- |
| **E2AP** | `v02.03` | Protocolo de aplicação E2 (Setup, Control, Indication, Subscription). |
| **E2SM-KPM** | `v03.00` | Modelo de serviço de medições de desempenho (Formato 1 Event Trigger / Action). |
| **E2SM-RC** | `v01.03` | Modelo de serviço de controle de rádio (Formato 1, Estilo 1 - Control Header/Message). |
| **O-RAN SC Platform** | `Release J` | Plataforma Near-RT RIC de referência (RMR mtypes 12010, 12040, 12050). |
| **ns-3 (nativa)** | `3.48` (`d2add90`) | Motor de simulação dos cenários de conflito S0–S7 (sem E2). |
| **5G-LENA (nativa)** | `v5.1` (`cedcead`) | Módulo 3GPP NR NR-MAC/NR-PHY da pilha nativa. |
| **ns-3 (NORI)** | `3.42` (`ab4cce0`) | Versão exigida pelo NORI oficial. |
| **5G-LENA (NORI)** | `78b7179` | Commit fixado pelo NORI. |
| **NORI** | `8a30867` | Módulo E2 (E2AP/E2SM v3.01) para 5G-LENA; implantado via `deploy/helm/nori-ns3`. |
| **H-RDL Core** | `1.1.x` | Camada de governança e mediação determinística de conflitos multi-xApp. |

---

> **Revisão de 2026-11-07.** O commit NORI `9b64c12` congelado anteriormente não existe no repositório oficial (`github.com/lasseufpa/nori`), e o NORI não compila sobre ns-3.48 / 5G-LENA v5.1: seu Dockerfile fixa ns-3.42, 5G-LENA `78b7179`, E2SIM `da6f82f` e ASN.1 E2AP v3.01 / E2SM-KPM v3.00 / E2SM-RC v3.01 (Near-RT RIC Release I). Execuções que declaram `9b64c12` não correspondem a nenhuma versão real do NORI. O perfil E2 da xApp RDL (v02.03 / RC v01.03 local) difere do NORI; a interoperabilidade E2 exige alinhar a xApp ao v3.01.

## 3. Formato Oficial de Citação Científica

Nas publicações científicas (SBRC, SBrT, IEEE WCNC, IEEE TNSM), o perfil de compatibilidade deve ser citado utilizando estritamente o enunciado formal:

> *"H-RDL F1 implements an explicitly defined O-RAN compatibility profile based on E2AP v02.03, E2SM-KPM v03.00, and E2SM-RC v01.03, selected as the target interoperability profile for the experimental O-RAN SC/NORI stack."*

---

## 4. Diretriz de Não-Contaminação com Versões Futuras

Embora a O-RAN ALLIANCE tenha publicado revisões recentes (como E2SM-KPM v8.00 e E2SM-RC v10.00 no Release 5), a Fase 1 do XApp-RDL mantém seu perfil **estritamente congelado** em `E2AP v02.03`, `E2SM-KPM v03.00` e `E2SM-RC v01.03`.

Evoluções para o O-RAN Release 5 serão conduzidas em uma branch isolada (`feature/oran-release5-profile`) e tratadas exclusivamente em fases futuras do projeto, sem alterar os benchmarks ou os experimentos da Fase 1.
