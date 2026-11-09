#!/usr/bin/env python3
"""Gera deploy/helm/observability/dashboards/rdl_simulacoes.json (dashboard do Grafana, consultas Flux).
Uso: python scripts/observe/make_grafana_dashboard.py  (depois: bash scripts/observe/deploy_observability.sh)"""
import json
from pathlib import Path

DS = {"type": "influxdb", "uid": "influxdb-rdl"}
B = 'from(bucket: "simulacoes")'


def ts(pid, title, query, x, y, w=12, h=8, unit=None, desc=None, kind="timeseries", extra=None):
    p = {"id": pid, "type": kind, "title": title, "datasource": DS, "gridPos": {"x": x, "y": y, "w": w, "h": h},
         "targets": [{"refId": "A", "datasource": DS, "query": query}],
         "fieldConfig": {"defaults": {**({"unit": unit} if unit else {}), "custom": {}}, "overrides": []},
         "options": {"legend": {"displayMode": "table", "placement": "bottom", "calcs": ["lastNotNull", "max"]},
                     "tooltip": {"mode": "multi"}}}
    if desc:
        p["description"] = desc
    if extra:
        p.update(extra)
    return p


def row(pid, title, y):
    return {"id": pid, "type": "row", "title": title, "collapsed": False, "gridPos": {"x": 0, "y": y, "w": 24, "h": 1}, "panels": []}


panels = [
    row(1, "Execução NORI ao vivo (FlowMonitor, a cada 0,5 s simulado)", 0),
    ts(2, "Vazão por fatia — execuções recentes",
       f'{B}\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == "nori_slice" and r._field == "throughput_mbps")\n'
       '  |> group(columns: ["run", "slice"])\n  |> keep(columns: ["_time", "_value", "run", "slice"])',
       0, 1, unit="Mbits", desc="Vazão por UE/fatia calculada dos contadores acumulados do FlowMonitor da execução NORI em andamento."),
    ts(3, "Atraso médio por fatia",
       f'{B}\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == "nori_slice" and r._field == "delay_ms")\n'
       '  |> group(columns: ["run", "slice"])\n  |> keep(columns: ["_time", "_value", "run", "slice"])', 12, 1, unit="ms"),
    ts(4, "Vazão por fatia × tempo simulado — execução escolhida (${run})",
       f'{B}\n  |> range(start: -365d)\n  |> filter(fn: (r) => r._measurement == "nori_slice" and r.run == "${{run}}" and (r._field == "throughput_mbps" or r._field == "sim_time_s"))\n'
       '  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")\n  |> group()\n'
       '  |> pivot(rowKey: ["sim_time_s"], columnKey: ["slice"], valueColumn: "throughput_mbps")\n'
       '  |> keep(columns: ["sim_time_s", "eMBB", "URLLC"])\n  |> sort(columns: ["sim_time_s"])',
       0, 9, w=24, kind="trend",
       desc="Eixo X: tempo simulado (s). O Control é aplicado pelo NORI no instante de aplicação (docs/07 v5); a queda da fatia restrita aparece alguns segundos simulados depois.",
       extra={"options": {"xField": "sim_time_s", "legend": {"showLegend": True, "displayMode": "list", "placement": "bottom"},
                          "tooltip": {"mode": "multi"}},
              "fieldConfig": {"defaults": {"unit": "Mbits", "custom": {"drawStyle": "line", "lineWidth": 2, "showPoints": "never"}},
                              "overrides": [{"matcher": {"id": "byName", "options": "sim_time_s"}, "properties": [{"id": "unit", "value": "s"}]}]}}),
    row(5, "xApp kpm-probe (E2: KPM, decisão, RIC Control, ACK)", 17),
    ts(6, "KPM do nó: PRBs usados e disponíveis",
       f'{B}\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == "xapp_kpm_node" and (r._field == "prb_used_dl" or r._field == "prb_avail_dl"))\n'
       '  |> group(columns: ["_field"])\n  |> keep(columns: ["_time", "_value", "_field"])', 0, 18, w=8),
    ts(7, "Indications KPM recebidas (por 10 s)",
       f'{B}\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == "xapp_indication" and r._field == "count")\n'
       '  |> group()\n  |> aggregateWindow(every: 10s, fn: sum, createEmpty: false)', 8, 18, w=8),
    ts(8, "Latência do ACK do RIC Control",
       f'{B}\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == "xapp_control_outcome" and r._field == "latency_ms")\n'
       '  |> group(columns: ["outcome"])', 16, 18, w=8, unit="ms",
       extra={"fieldConfig": {"defaults": {"unit": "ms", "custom": {"drawStyle": "points", "pointSize": 8}}, "overrides": []}}),
    ts(9, "RIC Control enviados (cotas por fatia, fonte da decisão)",
       f'{B}\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == "xapp_control")\n'
       '  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")\n  |> group()\n'
       '  |> keep(columns: ["_time", "run", "baseline", "source", "order", "embb_cap_pct", "urllc_cap_pct", "pair_gap_ms", "decision_ms"])\n'
       '  |> sort(columns: ["_time"], desc: true)\n  |> limit(n: 50)', 0, 26, w=24, h=8, kind="table"),
    row(10, "Campanhas e certificação (evidência no repositório)", 34),
    ts(11, "Gates do certificado mais recente",
       f'{B}\n  |> range(start: -365d)\n  |> filter(fn: (r) => r._measurement == "certificado" and r._field == "verdict_code")\n'
       '  |> group(columns: ["gate"])\n  |> last()\n  |> keep(columns: ["_time", "gate", "_value"])',
       0, 35, w=24, h=4, kind="stat",
       extra={"options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "colorMode": "background",
                          "textMode": "value_and_name", "graphMode": "none"},
              "fieldConfig": {"defaults": {"mappings": [{"type": "value", "options": {
                  "3": {"text": "CERTIFIED", "color": "green"}, "2": {"text": "LOCAL_ONLY", "color": "blue"},
                  "1": {"text": "NOT_CERTIFIED", "color": "orange"}, "0": {"text": "BLOCKED", "color": "red"}}}],
                                           "displayName": "${__field.labels.gate}"}, "overrides": []}}),
    ts(12, "Vereditos de efeito por baseline e regra (todas as execuções NORI)",
       f'{B}\n  |> range(start: -365d)\n  |> filter(fn: (r) => r._measurement == "campanha_execucao" and r._field == "verdict_code")\n'
       '  |> group(columns: ["baseline", "rule", "verdict"])\n  |> count()\n  |> group()\n'
       '  |> keep(columns: ["baseline", "rule", "verdict", "_value"])\n  |> rename(columns: {_value: "execuções"})\n  |> sort(columns: ["rule", "baseline", "verdict"])',
       0, 39, w=12, h=10, kind="table"),
    ts(13, "URLLC antes e depois do Control, por execução (regra v6)",
       f'{B}\n  |> range(start: -365d)\n  |> filter(fn: (r) => r._measurement == "campanha_execucao" and r.rule == "v6-ratio-apply" and (r._field == "urllc_before_mbps" or r._field == "urllc_after_mbps" or r._field == "urllc_predicted_mbps"))\n'
       '  |> map(fn: (r) => ({r with serie: if r._field == "urllc_before_mbps" then "antes" else if r._field == "urllc_after_mbps" then "depois" else "previsto (v6)"}))\n'
       '  |> group(columns: ["serie"])\n  |> keep(columns: ["_time", "_value", "serie"])\n  |> sort(columns: ["_time"])', 12, 39, w=12, h=10, unit="Mbits",
       extra={"timeFrom": "30d", "fieldConfig": {"defaults": {"unit": "Mbits", "custom": {"drawStyle": "points", "pointSize": 6}},
                                                 "overrides": []}}),
    ts(14, "Execuções mais recentes",
       f'{B}\n  |> range(start: -365d)\n  |> filter(fn: (r) => r._measurement == "campanha_execucao")\n'
       '  |> pivot(rowKey: ["_time", "run", "rule"], columnKey: ["_field"], valueColumn: "_value")\n  |> group()\n'
       '  |> keep(columns: ["_time", "run", "rule", "verdict", "source", "embb_cap_pct", "urllc_cap_pct", "urllc_before_mbps", "urllc_after_mbps", "urllc_predicted_mbps", "trigger_is_kpm_t0"])\n'
       '  |> sort(columns: ["_time"], desc: true)\n  |> limit(n: 60)', 0, 49, w=24, h=10, kind="table"),
]
for p in panels:
    if p["type"] in ("table", "stat", "row"):
        p.get("options", {}).pop("legend", None)
        p.get("options", {}).pop("tooltip", None)

dash = {
    "uid": "xapp-rdl-sim", "title": "xApp RDL — simulações", "tags": ["xapp-rdl", "nori", "o-ran"],
    "schemaVersion": 39, "version": 1, "editable": False, "refresh": "5s",
    "time": {"from": "now-30m", "to": "now"}, "timezone": "browser",
    "description": "Execução NORI ao vivo, eventos E2 da xApp kpm-probe e vereditos das campanhas (alimentado por scripts/observe/influx_feeder.py).",
    "templating": {"list": [{
        "name": "run", "label": "Execução", "type": "query", "datasource": DS, "refresh": 2, "sort": 2,
        "query": 'import "influxdata/influxdb/schema"\nschema.tagValues(bucket: "simulacoes", tag: "run", predicate: (r) => r._measurement == "nori_slice", start: -30d)',
        "definition": "tagValues run (nori_slice)", "current": {}, "options": [], "includeAll": False, "multi": False}]},
    "annotations": {"list": [{
        "name": "RIC Control", "datasource": DS, "enable": True, "iconColor": "orange",
        "target": {"refId": "Anno", "query": f'{B}\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == "xapp_control" and r._field == "embb_cap_pct")\n  |> map(fn: (r) => ({{r with _value: "Control " + string(v: r.source) + " eMBB " + string(v: r._value) + " %"}}))'}}]},
    "panels": panels,
}
out = Path(__file__).resolve().parents[2] / "deploy" / "helm" / "observability" / "dashboards" / "rdl_simulacoes.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(dash, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("ok", len(panels))
