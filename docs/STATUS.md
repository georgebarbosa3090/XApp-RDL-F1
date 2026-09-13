# Status de Conformidade e Maturidade Técnica/Científica — XApp-RDL-F1

> **Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL)  
> **Data de Atualização:** 13 de Setembro de 2026  
> **Modo de Operação:** `oran-strict` (Fail-Closed)  
> **Diretriz de Proveniência:** Zero Dados Sintéticos / Zero Mocks em Resultados Públicos

---

## 1. Visão Geral da Maturidade Multi-Backend

O sistema adota a arquitetura desacoplada onde o **H-RDL Core** gera apenas decisões canônicas (`CanonicalControlDecision`), enquanto a comunicação com o nó E2 é delegada ao `RANBackendAdapter`.

```text
                 Canonical H-RDL Core
                         │
           ┌─────────────┴──────────────┐
           │                            │
     NORI_NS3 Adapter          SRSRAN_OPEN5GS Adapter
  (E2AP v02.03, KPM v03.00,    (E2AP v03.00, KPM v03.00,
       RC v01.03)                   RC v03.00)
           │                            │
           └─────────────┬──────────────┘
                         │
                 Decisão Canônica
                         │
            Evidência Externa (RAW/PCAP)
```

### Matriz de Maturidade dos Backends

| Backend | Perfil / Protocolo | Estado Atual | Cobertura de Testes | Interoperabilidade Externa |
| :--- | :--- | :---: | :---: | :---: |
| `NORI_NS3` | ns-3.48 + 5G-LENA v5.1 + NORI (E2AP 2.03, KPM 3.00, RC 1.03) | `LOCALLY_INTEGRATED` | Unit + Codec + Scenarios (57/57 PASS) | Aguardando captura PCAP/RAW live |
| `SRSRAN_OPEN5GS` | srsRAN gNB + Open5GS (E2AP 3.00, KPM 3.00, RC 3.00 Style 2 / Action 6) | `LOCALLY_INTEGRATED` | Adapter Routing + APER Mapping PASS | Aguardando execução em testbed |
| `OPENRANBR_PHYSICAL` | OpenRAN@Brasil Physical Testbed (COTS UE + srsRAN + Near-RT RIC) | `DESIGNED` | Config/Profile Mapped | Requer validação prévia em TB0-TB6 |

---

## 2. Status dos Gates de Validação Científica (G0 a G6)

| Gate | Denominação | Estado | Critério de Aprovação | Evidência Exigida |
| :---: | :--- | :---: | :--- | :--- |
| **G0** | Baseline & Proveniência | **PASS** ✅ | `versions.lock` congelado + hashes SHA256 + CI limpa de mocks | `reproducibility/versions.lock`, `provenance_policy.yaml` |
| **G1** | Telemetria KPM Externa | **PENDING** ⏳ | Recepção e decodificação APER de `RICIndication` real | `e2_setup.pcap`, `kpm_indication.raw`, `hashes.sha256` |
| **G2** | Mediação H-RDL Interna | **PASS** ✅ | Detecção de conflito espacial/frequencial + Refinamento e Guardas | Testes unitários/integração (S0–S8) 100% verdes |
| **G3** | Controle E2SM-RC Externo | **PENDING** ⏳ | Emissão de `RICcontrolRequest` e recepção de `RICcontrolAcknowledge` / `Failure` | `ric_control_request.raw`, `ric_control_ack.raw`, `e2term.log` |
| **G4** | Closed-Loop Causal | **PENDING** ⏳ | Ciclo completo $KPM(t_0) \to H\text{-}RDL \to RC \to ACK \to RANStateChanged \to KPM(t_1)$ | `causal_event.jsonl` com correlação temporal $T_{\text{loop}}$ |
| **G5** | Campanha Multi-Run | **PENDING** ⏳ | $n \ge 30$ seeds pareadas (NORI) ou $N \ge 10$ runs (srsRAN) sem falhas de proveniência | Matriz estatística em `results/` com IC 95% |
| **G6** | Reprodutibilidade Independente | **PENDING** ⏳ | Reexecução integral por terceiro via container + scripts reproduzíveis | Pacote de artefatos com audit script verde |

---

## 3. Status dos Gates do Testbed OpenRAN@Brasil / srsRAN (TB0 a TB10)

| Gate Testbed | Descrição do Escopo | Estado | Condição Go/No-Go |
| :---: | :--- | :---: | :--- |
| **TB0** | Inventário & Versões Testbed | **PASS** ✅ | Perfil `deploy/openran-br-v3` e `versions.lock` [profile.srsran] definidos |
| **TB1** | Registro UE / Core / RAN Baseline | **PENDING** ⏳ | Sessão PDU ativa + `ping` e `iperf3` funcionais sem E2 |
| **TB2** | Conexão SCTP E2 Setup | **PENDING** ⏳ | `E2SetupRequest` / `E2SetupResponse` trocados com E2Term |
| **TB3** | KPM Reference xApp | **PENDING** ⏳ | Telemetria recebida por xApp de referência |
| **TB4** | KPM H-RDL xApp | **PENDING** ⏳ | Telemetria recebida e decodificada pelo H-RDL via `SrsRanBackendAdapter` |
| **TB5** | RC Reference xApp | **PENDING** ⏳ | Comando de controle executado por xApp de referência com ACK |
| **TB6** | RC H-RDL xApp | **PENDING** ⏳ | Comando de controle (Style 2 / Action 6) executado pelo H-RDL |
| **TB7** | Mediação Multi-xApp | **PENDING** ⏳ | Resolução de conflito entre 2+ xApps concorrentes no testbed |
| **TB8** | Closed Loop Testbed | **PENDING** ⏳ | Ciclo causal comprovado em hardware/srsRAN real |
| **TB9** | Validação Cross-Backend | **PENDING** ⏳ | Comparação de decisão H-RDL entre `NORI_NS3` e `SRSRAN_OPEN5GS` |
| **TB10** | Ilha Física OpenRAN@Brasil | **PENDING** ⏳ | Execução completa na infraestrutura física com COTS UE e USRP/RU |

---

## 4. Escala Formal de Maturidade de Recursos (5 Estados)

Conforme a regra de ouro do planejamento:

$$\text{DESIGNED} \neq \text{IMPLEMENTED} \neq \text{UNIT\_TESTED} \neq \text{LOCALLY\_INTEGRATED} \neq \text{EXTERNAL\_INTEROP} \neq \text{CLOSED\_LOOP\_VALIDATED} \neq \text{SCIENTIFICALLY\_VALIDATED}$$

| Funcionalidade / Componente | Código Estado | Descrição Curta |
| :--- | :---: | :--- |
| Core RDL (Perception/Reasoning/Refinement) | `LOCALLY_INTEGRATED` | Implementado, testado e integrado aos adapters locais |
| Security Safety Guard | `LOCALLY_INTEGRATED` | Limites fisiológicos e regras de controle validados |
| `RANBackendAdapter` Abstração & Factory | `LOCALLY_INTEGRATED` | Desacoplamento do runtime concluído com fail-closed |
| E2AP APER Codec (pycrate) | `LOCALLY_INTEGRATED` | Decodificação e codificação APER validadas via golden vectors |
| Capability Discovery Runtime | `LOCALLY_INTEGRATED` | Suporte a `RANFunctionDefinition` e fallback fail-closed |
| Politica de Proveniência & Fail-Closed Audit | `LOCALLY_INTEGRATED` | Firewall de publicação e validação de evidências brutas ativas |
| Live E2Term SCTP Capture | `DESIGNED` | Aguardando execução do stack O-RAN SC / srsRAN live |
| Closed-Loop Causal Tracking ($T_{\text{loop}}$) | `LOCALLY_INTEGRATED` | Estrutura de correlação $KPM \to RC \to ACK$ pronta |

---

## 5. Indicadores Numéricos Globais (KPIs Tecnológicos)

- **Suíte de Testes Locais (Software):** 57/57 PASS (100%)
- **Zero Synthetic Data Compliance:** 100% (Código e scripts auditados e isentos de geradores mock)
- **Fail-Closed Backend Check:** PASS (Backends não autorizados disparam `UnsupportedBackendError`)
- **Evidências Científicas Elegíveis Publicadas:** 0 (Bloqueadas até a conclusão dos Gates G1, G3, G4 com traces reais)
