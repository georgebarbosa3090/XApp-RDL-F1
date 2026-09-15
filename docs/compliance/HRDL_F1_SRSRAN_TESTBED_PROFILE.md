# Perfil de Validação em Testbed srsRAN — H-RDL F1 srsRAN Testbed Profile

**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL Determinística)  
**Documento:** `HRDL_F1_SRSRAN_TESTBED_PROFILE.md`  
**Status:** **ATIVO / INTEGRADO (Perfil Complementar de Testbed)**  
**Escopo:** Definição formal do perfil de compatibilidade para execução em pilhas de software real (srsRAN gNB / Open5GS 5GC / O-RAN SC Near-RT RIC) no ambiente experimental do programa OpenRAN@Brasil.

---

## 1. Visão Geral da Estratégia Dual-Backend

Para garantir o máximo rigor científico e a reprodutibilidade dos resultados do H-RDL, a Fase 1 adota uma **estratégia dual-backend complementar**:

$$\boxed{\begin{array}{ccc}
\text{\textbf{Backend 1: Simulação ns-3/NORI}} & \Longleftrightarrow & \text{\textbf{Backend 2: Software RAN srsRAN/Open5GS}} \\
\text{(Controle Experimental, 30 Seeds, Estudo de Ablação)} & & \text{(Interoperabilidade E2 Real, Software de Produção)}
\end{array}}$$

1. **`HRDL_F1_NORI_PROFILE` (Congelado):** Ancorado em `E2AP v02.03`, `E2SM-KPM v03.00` e `E2SM-RC v01.03` no simulador ns-3.48 / 5G-LENA v5.1.
2. **`HRDL_F1_SRSRAN_TESTBED_PROFILE` (Testbed Real):** Ancorado em `E2AP v03.00`, `E2SM-KPM v03.00` e `E2SM-RC v03.00` na pilha srsRAN gNB + Open5GS 5GC + O-RAN SC.

---

## 2. Especificação Normativa do Perfil srsRAN Testbed

```yaml
profile_name: "H-RDL F1 srsRAN Testbed Profile"
status: "ACTIVE_TESTBED"
e2ap_version: "v03.00"
e2sm_kpm_version: "v03.00"
e2sm_rc_version: "v03.00"
oran_sc_release: "Release J / N"
target_ran: "srsRAN Project (gNB / CU / DU)"
target_core: "Open5GS 5GC (AMF / SMF / UPF)"
decision_window_ms: 200
kpm_reporting_period_ms: 1000
testbed_stabilization_samples: 3
```

### Tabela Canônica de Mapeamento de Protocolo

| Componente | Especificação srsRAN / Open5GS | Mapeamento no H-RDL Core | Função na Arquitetura |
| :--- | :---: | :--- | :--- |
| **E2AP** | `v03.00` | `E2APHeaderDecoder` / `PDUWrapper` | Sinalização de aplicação E2 (Setup, Control, Indication, Sub). |
| **E2SM-KPM** | `v03.00` | `KpmDecoder` / `SrsRanBackendAdapter` | Relatórios de medições de desempenho rádio e de fatias. |
| **E2SM-RC** | `v03.00` | `SrsRanRCEncoder` / `RCMapper` | Controle de rádio (Style 2 / Action 6 para PRB Quota). |
| **RAN Node** | `srsRAN gNB` | `E2NodeAdapter` | Nó gNodeB 5G NR com suporte a E2 Agent nativo. |
| **5G Core** | `Open5GS` | `CoreObserver` | Núcleo 5G (N2 AMF / N3 UPF) para registro e sessões PDU. |

---

## 3. Mapeamento de Controle E2SM-RC para srsRAN

Diferente da simulação NORI (Style 1 / Action 1), a implementação nativa do srsRAN mapeia o controle de cotas de PRB por fatia (*Slice-Level PRB Quota*) no **Control Service Style 2 / Action 6**:

$$\boxed{\text{Ação H-RDL } (\text{PRB-QUOTA}) \longrightarrow \text{E2SM-RC Style 2} \longrightarrow \text{Control Action 6} \longrightarrow \text{RAN Parameter ID 1}}$$

| Parâmetro H-RDL | Control Style (`srsRAN`) | Control Action (`srsRAN`) | Parameter ID | Unidade / Faixa |
| :--- | :---: | :---: | :---: | :---: |
| **`PRB_QUOTA`** | `2` (Slice Level Control) | `6` (PRB Allocation) | `1` | `0.0` a `100.0%` |
| **`HANDOVER`** | `3` (Mobility Control) | `1` (Directed Handover) | `5` | `Cell ID (int)` |

---

## 4. Separação de Relógios e Critério de Estabilização Testbed

No testbed srsRAN, o período de emissão de telemetria KPM é configurado em $T_{\text{KPM}} = 1000\text{ms}$ (1 segundo). Para conciliar a janela de decisão em lote do H-RDL ($W_{\text{decision}} = 200\text{ms}$) com a observabilidade do testbed:

1. **Janela de Agrupamento RDL ($W_{\text{decision}} = 200\text{ms}$):** As propostas emitidas pelas xApps concorrentes continuam sendo agregadas e arbitradas em lotes determinísticos de 200 ms.
2. **Janela de Observação Testbed ($T_{\text{KPM}} = 1000\text{ms}$):** A recuperação da rede e a melhoria dos KPIs após uma ação de controle exigem **3 amostras KPM consecutivas estáveis** ($T_{\text{stable}} \approx 3.0\text{s}$) para encerramento de evento no `CausalTracker`.

$$\boxed{T_{\text{observação}}^{\text{srsRAN}} = 3 \times T_{\text{KPM}} = 3.0\text{ s}}$$
