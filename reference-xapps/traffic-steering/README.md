# Traffic Steering Reference xApp (O-RAN SC)

## Referência Científica e Projeto Base
* **Repositório Oficial:** [`o-ran-sc/ric-app-ts`](https://github.com/o-ran-sc/ric-app-ts)
* **Implementação Simplificada / Testbed:** [`natanzi/ts-xapp`](https://github.com/natanzi/ts-xapp) (OAIC Testbed)
* **Ambiente Original:** O-RAN Software Community (O-RAN SC) Near-RT RIC / App Manager / xApp Onboarder.

---

## Papel no Projeto XApp-RDL-F1
* **Categoria:** Workload Concorrente / Controlador de Mobilidade e Steering.
* **Objetivo de Controle:** Avalia métricas de sinal (RSRP/RSRQ) e predição de QoE, emitindo comandos de handover e balanceamento de tráfego entre estações rádio-base (`HANDOVER`).
* **Comportamento Conflitante:** Tenta direcionar UEs para células secundárias ou aumentar potência para manter cobertura contínua, colidindo com políticas de economia de energia (`Energy Saving`) que visam manter essas mesmas células desligadas ou com potência mínima.

---

## Interface de Interceptação RDL
* **MsgType:** `RDL_ACTION_PROPOSAL` (30000)
* **Parâmetros Emitidos:**
  ```json
  {
    "xapp_id": "traffic_steering_oransc",
    "node_id": "gnb_01",
    "parameter": "HANDOVER",
    "value": 1.0,
    "target_node": "gnb_02",
    "target_ue": "UE-07",
    "priority": 80
  }
  ```
* **Endpoints HTTP / Métricas:**
  * Liveness: `GET :8086/health`
  * Readiness: `GET :8086/ready`
  * Prometheus: `GET :8087/metrics` (`ts_proposals_total`, `ts_handovers_triggered_total`, `ts_cell_load_ratio`)
