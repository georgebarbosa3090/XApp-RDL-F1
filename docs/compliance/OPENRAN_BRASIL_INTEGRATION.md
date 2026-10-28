# Guia de Integração e Validação no Testbed OpenRAN@Brasil — OpenRAN@Brasil Integration

**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL Determinística)  
**Documento:** `OPENRAN_BRASIL_INTEGRATION.md`  
**Escopo:** Diretrizes metodológicas, arquitetura de implantação, matriz de portões experimentais (TB0 a TB10) e primeiro cenário de validação para o testbed OpenRAN@Brasil.

---

## 1. Arquitetura de Implantação e Fluxo E2E

A integração do H-RDL no ambiente do **OpenRAN@Brasil** posiciona a xApp RDL sobre a plataforma de referência Near-RT RIC (O-RAN SC), gerenciando nós srsRAN gNB acoplados ao núcleo Open5GS:

```text
               ┌────────────────────────────────────────────────────────┐
               │           OpenRAN@Brasil Testbed Cluster               │
               │                                                        │
               │   ┌───────────────────┐        ┌───────────────────┐   │
               │   │    Open5GS AMF    │        │    Open5GS UPF    │   │
               │   │   (Plano Control) │        │   (Plano Dados)   │   │
               │   └─────────▲─────────┘        └─────────▲─────────┘   │
               └─────────────┼────────────────────────────┼─────────────┘
                             │ N2                         │ N3
                             ▼                            ▼
               ┌────────────────────────────────────────────────────────┐
               │                     srsRAN gNB                         │
               │   - E2 Agent (E2AP v03.00 / KPM v03.00 / RC v03.00)    │
               └─────────────────────────▲──────────────────────────────┘
                                         │ E2 (SCTP / RMR)
                                         ▼
               ┌────────────────────────────────────────────────────────┐
               │            Plataforma Near-RT RIC (O-RAN SC)           │
               │  - SubMgr REST Client (:8088)                          │
               │  - E2Term (SCTP :36422 / RMR :38000)                   │
               └─────────────────────────▲──────────────────────────────┘
                                         │ RMR / REST
                                         ▼
               ┌────────────────────────────────────────────────────────┐
               │                   xApp RDL (H-RDL)                     │
               │  - SrsRanBackendAdapter                                │
               │  - Perception / Reasoning / Safety Guards              │
               └────────────────────────────────────────────────────────┘
```

---

## 2. Matriz de Portões Experimentais de Testbed (Gates TB0 a TB10)

Para garantir que a integração no testbed ocorra de forma incremental e segura, o projeto estabelece 11 portões formais de validação (*Definition of Done*):

| Gate | Experimento / Etapa | Critério de Aceite (PASS) | Nível de Evidência |
| :---: | :--- | :--- | :---: |
| **TB0** | Congelamento da Infraestrutura | Registrados commits de `srsRAN`, `Open5GS`, `O-RAN SC` e hashes SHA-256. | Meta-Manifest |
| **TB1** | Baseline Open5GS + srsRAN | UE se registra no AMF, estabelece PDU Session e trafega ICMP/iperf3. | `open5gs_amf.log`, `ping.log` |
| **TB2** | Conectividade E2 srsRAN $\leftrightarrow$ RIC | `E2SetupRequest` e `E2SetupResponse` concluídos com sucesso no E2Term. | `e2_setup.pcap`, `e2term.log` |
| **TB3** | Telemetria KPM Referência | xApp de referência recebe indicações E2SM-KPM válidas do srsRAN gNB. | `kpm_reference.json` |
| **TB4** | H-RDL KPM Observer | `SrsRanBackendAdapter` decodifica telemetria KPM real enviada pelo srsRAN. | `hrdl_kpm_observer.jsonl` |
| **TB5** | Controle RC Baseline | xApp de referência envia controle de PRB e srsRAN responde com ACK. | `e2_rc_ack.pcap` |
| **TB6** | Controle H-RDL RC | `SrsRanBackendAdapter` envia `RICcontrolRequest` (Style 2 / Action 6) com ACK. | `hrdl_rc_control.jsonl` |
| **TB7** | Arbitragem Multi-xApp | H-RDL recebe propostas conflitantes de 2 xApps em lote e resolve deterministicamente. | `conflicts.jsonl`, `decisions.jsonl` |
| **TB8** | Malha Fechada Causual (Closed Loop) | $KPM(t_0) \rightarrow \text{RDL} \rightarrow \text{RC} \rightarrow \text{ACK} \rightarrow KPM(t_1, t_2, t_3)$ comprovado em 3 amostras. | `causal.jsonl`, `iperf.json` |
| **TB9** | Validação Cruzada (Cross-Backend) | Comportamento de decisão idêntico verificado entre `NORI_NS3` e `SRSRAN_OPEN5GS`. | `cross_backend_report.json` |
| **TB10** | Validação em Ilha Física | Execução bem-sucedida em O-RU + COTS UE na infraestrutura do OpenRAN@Brasil. | `physical_testbed_manifest.json` |

---

## 3. Primeiro Cenário Experimental Recomendado: Cenário S1 (Direct PRB Conflict)

Para a primeira demonstração física no testbed, recomenda-se iniciar com o **Cenário S1 (Direct PRB Conflict)**, evitando dependências de controle de potência TX (que pode variar entre versões de firmware):

$$\text{Conflito Direto de Cotas PRB: } \text{Slice}_{\text{URLLC}} (\text{PRB-QUOTA} = 80\%) \quad \times \quad \text{Slice}_{\text{eMBB}} (\text{PRB-QUOTA} = 40\%) \implies \Sigma = 120\% > 100\%$$

1. **xApp A (xSlice URLLC):** Requisita aumento de cota de PRBs para $80\%$ para manter latência $< 5\text{ms}$.
2. **xApp B (Energy Saving / eMBB):** Requisita cota de $40\%$ de PRBs.
3. **Mediação H-RDL:** O H-RDL detecta o conflito na janela de 200 ms, prioriza o SLA URLLC, aplica os *Safety Guards* (limitando a $70\% / 30\%$) e despacha a ordem E2SM-RC Style 2 / Action 6 para o srsRAN.
4. **Validação no Testbed:** O srsRAN ajusta o scheduler e confirma a estabilização do P99 de latência via 3 amostras KPM consecutivas.
