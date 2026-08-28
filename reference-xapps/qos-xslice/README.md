# xSlice Reference xApp (QoS & Slicing Optimizer)

## Referência Científica e Projeto Base
* **Repositório Oficial:** [`peihaoY/xslice-oran`](https://github.com/peihaoY/xslice-oran)
* **Artigo / Trabalho:** *xSlice: Near-Real-Time Resource Slicing for QoS Optimization in 5G O-RAN*
* **Ambiente Original:** Near-RT RIC FlexRIC / OAI RAN / Testbed com UEs reais.

---

## Papel no Projeto XApp-RDL-F1
* **Categoria:** Workload Concorrente / Controlador de QoS.
* **Objetivo de Controle:** Ajusta cotas de blocos de recursos (`PRB_QUOTA`) no nível MAC para garantir latência ultrabaixa e alta taxa para fatias críticas (`URLLC` / `eMBB`).
* **Comportamento Conflitante:** Solicita até 80-90% de alocação de PRB em células macro, entrando em colisão direta com a xApp de *Energy Saving* (que tenta reduzir PRBs e desligar canais).

---

## Interface de Interceptação RDL
* **MsgType:** `RDL_ACTION_PROPOSAL` (30000)
* **Parâmetros Emitidos:**
  ```json
  {
    "xapp_id": "xslice_oran",
    "node_id": "gnb_01",
    "parameter": "PRB_QUOTA",
    "value": 80.0,
    "priority": 90,
    "slice_type": "URLLC"
  }
  ```
* **Endpoints HTTP / Métricas:**
  * Liveness: `GET :8082/health`
  * Readiness: `GET :8082/ready`
  * Prometheus: `GET :8083/metrics` (`xslice_proposals_total`, `xslice_prb_quota_requested_ratio`)
