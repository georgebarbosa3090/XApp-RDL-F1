# Traffic Steering (implementação local)

Gerador de propostas de mobilidade escrito para este projeto. Inspira-se no papel da xApp `o-ran-sc/ric-app-ts`, mas não contém código dela.

- **Parâmetro:** `HANDOVER` (valor = índice da célula de destino, extraído de `target_node`), prioridade 80. Até 2026-11-10 o valor era fixo em 1,0 (disparo), o que não batia com o contrato da RDL.
- **Conflito típico:** desloca UEs para células que a Energy Saving quer manter com potência reduzida.
- **Proposta (mtype 30000):**

```json
{"xapp_id": "traffic_steering_oransc", "node_id": "gnb_01", "parameter": "HANDOVER", "value": 2.0, "target_node": "gnb_02", "target_ue": "UE-07", "priority": 80}
```

- **HTTP:** `GET :8086/health`, `GET :8086/ready`; Prometheus em `:8087/metrics` (`ts_proposals_total`, `ts_handovers_triggered_total`, `ts_cell_load_ratio`).
