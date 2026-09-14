# Modelagem Arquitetural, Especificação Técnica e Cenários das xApps de Terceiros

Este documento apresenta a especificação técnica, componentes internos, Service Models E2SM, parâmetros de controle e métricas de simulação física para as **4 xApps de Terceiros** integradas ao ambiente de testes e arbitragem do middleware **H-RDL (Resource and Decision Layer)**.

---

## 1. Visão Geral do Cenário de Interação das xApps de Terceiros

No ecossistema **O-RAN Near-RT RIC**, diferentes xApps de terceiros (comunidade O-RAN SC e trabalhos da literatura) operam de forma autônoma. Suas decisões concorrentes sobre os mesmos nós de rádio (`gNodeB`) geram colisões de alocação de blocos de recursos físicos (`PRB_QUOTA`), ajuste de potência (`TX_POWER`) e mobilidade (`HANDOVER`).

![S1: Energy Saving vs QoS](figures/02_cenarios_e_topologias/s1_eevs_energy_vs_qos_dark.png)
![S2: Traffic Steering vs QoS Slicing](figures/02_cenarios_e_topologias/s2_tvs_traffic_steering_dark.png)

---

## 2. Especificações Técnicas das xApps de Terceiros

### 2.1. Traffic Steering (`ric-app-ts`)
* **Tipo de Origem (`origin_type`):** `ORAN_SC_OFFICIAL`
* **Fonte Upstream:** [O-RAN SC `ric-app-ts` (Release J)](https://github.com/o-ran-sc/ric-app-ts)
* **Função:** Otimização proativa de mobilidade e transferência de célula (Handover) com base em métricas de QoE/RSRP.
* **Service Models:** `E2SM-KPM v3` (Telemetria) e `E2SM-RC v2` (Controle).
* **Mensagens RMR:** `20000` (`TS_UE_LIST`), `20001` (`TS_QOE_PRED_REQ`), `20002` (`TS_CONTROL_ACK`).
* **Parâmetro Controlado:** `HANDOVER` (Target Cell ID). Prioridade: 80.

### 2.2. KPIMON (`ric-app-kpimon`)
* **Tipo de Origem (`origin_type`):** `ORAN_SC_OFFICIAL`
* **Fonte Upstream:** [O-RAN SC `ric-app-kpimon`](https://github.com/o-ran-sc/ric-app-kpimon)
* **Função:** Coleta passiva e monitoramento contínuo de KPIs de rádio (vazão, perda de pacotes, ocupação PRB).
* **Service Model:** `E2SM-KPM v3`.
* **Mensagem RMR:** `12010` (`RIC_INDICATION`).
* **Métricas Exportadas:** `DRB.UEThpDl`, `RRU.PrbTotUsed`, `RRC.ConnMean`. Prioridade: Passivo.

### 2.3. xSlice / QoS Slicing (`qos-xslice`)
* **Tipo de Origem (`origin_type`):** `ACADEMIC_REIMPLEMENTATION`
* **Fonte Upstream:** [peihaoY/xslice-oran](https://github.com/peihaoY/xslice-oran) (Yan et al., 2025 / CAMAD)
* **Função:** Alocação dinâmica de recursos de espectro para fatias de rede eMBB e URLLC.
* **Service Models:** `E2SM-KPM v3` e `E2SM-RC v2`.
* **Parâmetro Controlado:** `PRB_QUOTA` ($0\%$ a $100\%$). Prioridade: 70.

### 2.4. Energy Saving (`energy-saving`)
* **Tipo de Origem (`origin_type`):** `LITERATURE_INSPIRED`
* **Fonte Upstream:** [Orange-OpenSource/ns-O-RAN-flexric](https://github.com/Orange-OpenSource/ns-O-RAN-flexric) (Wadud et al., 2024)
* **Função:** Otimização da eficiência energética por meio de escalonamento de potência e sono micro-desconectado.
* **Service Models:** `E2SM-KPM v3` e `E2SM-RC v2`.
* **Parâmetro Controlado:** `TX_POWER` (Faixa segura: $-10\text{ dBm}$ a $23\text{ dBm}$). Prioridade: 40–60.

---

## 3. Matriz Comparativa de Especificações

| xApp | Tipo de Origem (`origin_type`) | Parâmetro Controlado | Faixa Válida | Prioridade | Service Model E2 |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **Traffic Steering** | `ORAN_SC_OFFICIAL` | `HANDOVER` | Target Cell ID | 80 | E2SM-KPM v3 / E2SM-RC v2 |
| **KPIMON** | `ORAN_SC_OFFICIAL` | *Nenhum (Passivo)* | N/A | Passivo | E2SM-KPM v3 |
| **xSlice / QoS Slicing** | `ACADEMIC_REIMPLEMENTATION` | `PRB_QUOTA` | $0.0\% \text{ a } 100.0\%$ | 70 | E2SM-KPM v3 / E2SM-RC v2 |
| **Energy Saving** | `LITERATURE_INSPIRED` | `TX_POWER` | $-10\text{ dBm a } 23\text{ dBm}$ | 40–60 | E2SM-KPM v3 / E2SM-RC v2 |
