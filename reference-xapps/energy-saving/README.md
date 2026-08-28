# Energy Saving Reference xApp (Orange / FlexRIC)

## Referência Científica e Projeto Base
* **Repositório Oficial:** [`Orange-OpenSource/ns-O-RAN-flexric`](https://github.com/Orange-OpenSource/ns-O-RAN-flexric)
* **Aplicação Original:** `xapp_es_with_cell_util` (Energy Saving under Cell Utilization)
* **Ambiente Original:** Near-RT RIC FlexRIC / Simulação ns-3 / O-RAN SC E2.

---

## Papel no Projeto XApp-RDL-F1
* **Categoria:** Workload Concorrente / Controlador de Eficiência Energética (Green RAN).
* **Objetivo de Controle:** Monitora a taxa de ocupação de PRBs e carga de tráfego, propondo desligamento de portadoras/células secundárias (*Micro-Sleep*) e redução forçada de potência de transmissão (`TX_POWER`).
* **Comportamento Conflitante:** Ao cortar potência e desativar células, degrada o throughput de usuários e eleva a latência, colidindo diretamente com `xSlice` (QoS) e `Traffic Steering`.

---

## Interface de Interceptação RDL
* **MsgType:** `RDL_ACTION_PROPOSAL` (30000)
* **Parâmetros Emitidos:**
  ```json
  {
    "xapp_id": "energy_saving_orange",
    "node_id": "gnb_01",
    "parameter": "TX_POWER",
    "value": 20.0,
    "priority": 65,
    "energy_target_kwh": 0.35
  }
  ```
* **Endpoints HTTP / Métricas:**
  * Liveness: `GET :8084/health`
  * Readiness: `GET :8084/ready`
  * Prometheus: `GET :8085/metrics` (`es_proposals_total`, `es_tx_power_target_dbm`, `es_estimated_energy_saved_ratio`)
