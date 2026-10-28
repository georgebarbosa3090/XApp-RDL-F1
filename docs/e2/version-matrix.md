# Matriz de Versionamento e Perfil de Interoperabilidade E2 — XApp-RDL-F1

**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL Determinística)  
**Target Interoperability Profile:** O-RAN SC Release I/J + NORI E2SIM (E2AP v02.03, E2SM-KPM v03.00, E2SM-RC v01.03)  
**Ambiente de Referência:** O-RAN Software Community (Release J Dawn/Cherry), 5G-LENA v5.1 / ns-3.48 e OpenRAN@Brasil Blueprint v3  
**Data de Atualização:** 10 de Setembro de 2026  

---

## 1. Perfil Normativo Alvo vs Roadmap O-RAN Release 5 (2026)

> [!IMPORTANT]
> **Definição de Perfil de Interoperabilidade:**
> A Fase 1 do projeto adota deliberadamente o **Perfil O-RAN SC Release I/J + NORI**, garantindo compatibilidade binária comprovada com a suíte de emulação `lasseufpa/nori`, com o `e2sim` e com a pilha de microserviços Near-RT RIC oficial (`ricplt`).
> As versões normativas mais recentes publicadas pelo WG3 da O-RAN Alliance em 2026 (tais como *E2SM-KPM v8.00*, *E2SM-RC v10.00* e *E2SM-CCC v7.00*) constituem o referencial de evolução e pesquisa da **Fase 3 (RDL Autônoma e Zero-Touch 6G)**.

| Protocolo / Interface | Versão Alvo (Fase 1) | Especificação O-RAN SC / WG3 | Módulo Python / Codec | Variante PER | Status Técnico e Validação |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **E2AP** | `v02.03` | O-RAN.WG3.E2AP-v02.03 | `src/e2/e2ap/pdu.py` | Unaligned PER (APER) | 🟢 PDU Canônica (`InitiatingMessage` / `Outcome` com `ProtocolIEs`) |
| **E2SM-KPM** | `v03.00` | O-RAN.WG3.E2SM-KPM-v03.00 | `src/e2/kpm/` | Unaligned PER (APER) | 🟢 Codec APER Estrutural / 🟡 Interoperabilidade E2 Node em Validação |
| **E2SM-RC** | `v01.03` | O-RAN.WG3.E2SM-RC-v01.03 | `src/e2/rc/` | Unaligned PER (APER) | 🟢 Header + Message + `RanFunctionCapabilityRegistry` / 🟡 Interoperabilidade |
| **RMR** | `v4.9.4+` | O-RAN SC `ric-plt/lib/rmr` | `ricxappframe` / SI95 | N/A (TCP/IPC) | 🟢 Integrado nativamente no ciclo de vida xApp |
| **SDL (DBAAS)** | Redis 6/7 | O-RAN SC `ric-plt/sdl` | `redis-py` / SDL C++ | N/A | 🟢 Suportado (Redis Cluster e Standalone) |
| **E2 Node (NORI)** | Commit `lasseufpa/nori` | SBrT 2025 / ns-O-RAN | C++20 / SCTP E2AP v02.03 | APER ASN1C | 🟢 Cenários Closed-Loop Prontos / 🟡 Testes em Ambiente Real |
| **5G RAN Simulator** | 5G-LENA v5.1 | 3GPP Rel 16/17 NR | ns-3.48 / CMake / Ninja | N/A | 🟢 Modelagem analítica Shannon, M/G/1 e Earth Model |
| **Infraestrutura** | Blueprint v3 | OpenRAN@Brasil (LABORA/UFG) | Kubernetes 1.28+ / k3d / Rancher | N/A | 🟢 Manifestos `deploy/openran-br-v3/` para namespace `ricxapp` |

---

## 2. Descoberta Dinâmica de Capacidades RAN Control (E2SM-RC)

O mapeamento de controle não assume IDs arbitrários fixos. A resolução de ações segue a ontologia:

$$\text{RDL Logical Action} \xrightarrow{\text{Capability Registry}} (\text{RIC-Style-Type},\, \text{RIC-ControlAction-ID},\, \text{RANParameter-ID}) \xrightarrow{\text{ASN.1 APER}} \text{E2AP-PDU}$$

| Parâmetro Lógico RDL | Style Type Padrão | Control Action ID | RAN Parameter ID | Formato ASN.1 | Faixa Operacional | Ação de Rádio Controlada |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `PRB_QUOTA` | `1` (Resource Alloc) | `1` (Slicing) | `1` | `INTEGER (0..100)` | $0\% \le \omega \le 100\%$ | Alocação de cotas de PRBs para fatias URLLC/eMBB |
| `SCHEDULER_WEIGHT` | `1` (Resource Alloc) | `2` (Weighting) | `2` | `INTEGER (1..100)` | $1 \le w \le 100$ | Ponderação no escalonador MAC Proportional Fair |
| `TX_POWER` | `2` (Power Control) | `1` (Sector Power) | `3` | `INTEGER (-10..23)` | $-10 \le P_{\text{tx}} \le 23\text{ dBm}$ | Ajuste dinâmico de potência de transmissão do setor |
| `HANDOVER` | `3` (Mobility Control) | `1` (Handover) | `4` | `INTEGER (0..65535)` | Target Cell ID | Migração direcionada de UE para mitigação de carga |

---

## 3. Identificadores Globais e OIDs Padronizados

* **E2SM-KPM Service Model OID:** `1.3.6.1.4.1.53148.1.2.2.2` (RAN Function ID = 2)
* **E2SM-RC Service Model OID:** `1.3.6.1.4.1.53148.1.2.2.3` (RAN Function ID = 3)
* **PLMN ID Padrão Brasil (OpenRAN@Brasil):** `724 / 99` (MCC = 724, MNC = 99)
