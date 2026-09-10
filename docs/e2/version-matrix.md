# Matriz de Versionamento e Conformidade de Protocolos E2 — XApp-RDL-F1

**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL)  
**Referencial Normativo:** O-RAN Alliance, O-RAN Software Community, NORI e OpenRAN@Brasil Blueprint v3  
**Data de Atualização:** 10 de Setembro de 2026  

---

## 1. Matriz de Versões por Interface e Componente

| Protocolo / Interface | Versão Alvo | Especificação O-RAN | Release O-RAN SC | Módulo / Codec | Variante PER | Status no Projeto |
| :--- | :---: | :--- | :---: | :--- | :---: | :---: |
| **E2AP** | v02.03 / v03.00 | O-RAN.WG3.E2AP-v02.03 | Release J (Cherry/Dawn) | `pycrate_asn1rt` / APER | Unaligned PER (APER) | 🟢 Especificado e Implementado |
| **E2SM-KPM** | v02.00 / v03.00 | O-RAN.WG3.E2SM-KPM-v03.00 | Release J | `pycrate_asn1rt` / APER | Unaligned PER (APER) | 🟢 Estrito (Sem Mocks) |
| **E2SM-RC** | v01.00 / v01.03 | O-RAN.WG3.E2SM-RC-v01.03 | Release J (`ric-app-rc`) | `pycrate_asn1rt` / APER | Unaligned PER (APER) | 🟢 PDU Integrada (Header+Msg) |
| **RMR** | v4.9.4+ | N/A (Linux Foundation) | ric-plt/lib/rmr | Protocolo RMR / SI95 | N/A (TCP/IPC) | 🟢 Integrado via `ricxappframe` |
| **SDL (DBAAS)** | Redis Standalone | N/A | ric-plt/sdl | python3-redis / SDL C++ | N/A | 🟢 Suportado (Cluster & Fake) |
| **E2 Node (NORI)** | Commit `lasseufpa/nori` | N/A (Ponte Simulada) | O-RAN SC e2sim v2.0 | C++20 / SCTP E2AP v2.02 | APER ASN1C | 🟢 Validado em Simulação |
| **5G RAN Simulator** | 5G-LENA v5.1 | 3GPP Rel 16/17 NR | N/A (CTTC) | ns-3.48 / CMake / Ninja | N/A | 🟢 Modelos 3GPP TR 38.901 |
| **Infraestrutura** | Blueprint v3 | OpenRAN@Brasil | Ubuntu 22.04 / k3s / k3d | Helm Charts v3 / K8s 1.28+ | N/A | 🟢 Perfil `deploy/openran-br-v3` |

---

## 2. Parâmetros RAN Control Mapeados (E2SM-RC)

| Parâmetro RDL | RAN Parameter ID | Formato ASN.1 | Faixa Operacional | Ação O-RAN / 3GPP |
| :--- | :---: | :---: | :---: | :--- |
| `PRB_QUOTA` | `1` | `INTEGER (0..100)` | $0\% \le \omega \le 100\%$ | Alocação de fatias MAC / Slicing Ratio |
| `SCHEDULER_WEIGHT` | `2` | `INTEGER (1..100)` | $1 \le w \le 100$ | Peso no agendador Proportional Fair / Round Robin |
| `TX_POWER` | `3` | `INTEGER (-10..23)` | $-10\text{ dBm} \le P_{\text{tx}} \le 23\text{ dBm}$ | Controle de potência de transmissão do setor |
| `HANDOVER` | `4` | `INTEGER (0..65535)` | Cell ID destino | Comando de migração de terminal UE para célula vizinha |

---

## 3. Identificadores Globais e OIDs Padronizados

* **E2SM-KPM Service Model OID:** `1.3.6.1.4.1.53148.1.2.2.2` (RAN Function ID = 2)
* **E2SM-RC Service Model OID:** `1.3.6.1.4.1.53148.1.2.2.3` (RAN Function ID = 3)
* **PLMN ID Padrão Brasil (OpenRAN@Brasil):** `724 / 99` (MCC = 724, MNC = 99)
