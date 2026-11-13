#!/usr/bin/env python3
# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
rApp-ResourceOptimizer do GreenRAN (atividade A1.7): coordena o RANSlicer-GreenRAN e o EnergySaver-GreenRAN
na escala Non-RT (> 1 s), por políticas A1 publicadas no A1-PMS (doc 12).

Entradas:
- **Intenção do operador:** arquivo JSON (``--intents``) ou texto (``--intent-text``), traduzido por um
  analisador de palavras-chave. A tradução de linguagem natural do GreenRAN (Agent-AI, UNICAMP) é outro
  entregável; este analisador é só o ponto de entrada mínimo.
- **Estado da rede:** relatório da RDL (``GET /governance``: recusas por xApp, conflitos implícitos e
  entre rApps) e indicadores de SLA e carga (``--kpi-url`` ou ``--kpi-file``, JSON com ``embb_thp_mbps``,
  ``embb_delay_ms`` e ``cell_load_pct``).
- **Período do dia:** noite (padrão 22h–6h) ou dia.

Saídas, três políticas A1 (instâncias ``greenran-*``, donos no mapa ``RDL_A1_FIELD_OWNERS``):

| Tipo | Destino | Conteúdo |
| :-- | :-- | :-- |
| 20001 ``GreenRAN_Intent_Policy`` | RDL | pesos de energia e SLA na arbitragem, desligamento de vizinhas |
| 21000 ``GreenRAN_RANSlicer_Intent`` | RANSlicer-GreenRAN | vazão e atraso-alvo da fatia de câmeras, piso mMTC, margem |
| 21001 ``GreenRAN_EnergySaver_Policy`` | EnergySaver-GreenRAN | janela de economia, limiares, células mínimas ativas |

Regras de coordenação:
1. **SLA em risco** (atraso eMBB acima do alvo ou vazão abaixo): prioriza SLA. Sobe o peso de SLA, proíbe
   desligar vizinhas, amplia a margem do RANSlicer e deixa o EnergySaver mais conservador (limiar de
   desligamento menor, mais células ativas).
2. **Noite sem risco:** prioriza energia, dentro dos limites do esquema A1.
3. **EnergySaver perdendo a arbitragem à noite sem risco de SLA** (≥ 70 % das propostas dele recusadas
   como ``LOST_ARBITRATION``): sobe mais o peso de energia na RDL.
4. **Conflito implícito** reportado pela RDL: suspende os desligamentos até o operador analisar.

Uso:
    python rapps/greenran_resource_optimizer.py --pms-url http://<a1pms>:8081 --rdl-url http://<rdl>:8080 --once
    python rapps/greenran_resource_optimizer.py --intent-text "priorizar câmeras de dia e economizar energia à noite" --dry-run --hour 3
"""
import argparse
import json
import re
import time
from datetime import datetime
from typing import Any, Dict, Optional

NIGHT = {"energy_weight": 0.45, "sla_weight": 0.35, "allow_neighbor_sleep": True, "low_power_threshold_dbm": 10}
DAY = {"energy_weight": 0.10, "sla_weight": 0.60, "allow_neighbor_sleep": False, "low_power_threshold_dbm": 10}
DEFAULT_INTENT = {"cameras": 6, "camera_mbps": 5.0, "max_delay_ms": 100.0, "mmtc_min_prb_pct": 10.0,
                  "night_start": 22, "night_end": 6, "min_active_cells": 1, "energy_priority": "normal"}
INSTANCES = {"20001": "greenran-rdl", "21000": "greenran-ranslicer", "21001": "greenran-energysaver"}


def objectives_for(hour: int, night_start: int = 22, night_end: int = 6) -> Dict[str, Any]:
    is_night = hour >= night_start or hour < night_end
    return dict(NIGHT if is_night else DAY)


def parse_intent_text(text: str) -> Dict[str, Any]:
    """Palavras-chave em português → campos da intenção (ponto de entrada mínimo; ver docstring)."""
    t = text.lower()
    intent: Dict[str, Any] = {}
    if m := re.search(r"(\d+)\s*c[aâ]meras?", t):
        intent["cameras"] = int(m.group(1))
    if m := re.search(r"(\d+(?:[.,]\d+)?)\s*mb/?s", t):
        intent["camera_mbps"] = float(m.group(1).replace(",", "."))
    if m := re.search(r"(\d+)\s*ms", t):
        intent["max_delay_ms"] = float(m.group(1))
    if "economizar" in t or "energia" in t:
        intent["energy_priority"] = "high" if any(w in t for w in ("máxim", "maxim", "agressiv")) else "normal"
    if any(w in t for w in ("priorizar câmeras", "priorizar cameras", "vigilância primeiro", "sla primeiro")):
        intent["energy_priority"] = "low" if "energia" not in t else intent.get("energy_priority", "normal")
    if m := re.search(r"(\d+)\s*c[eé]lulas?\s*(?:ativas|m[ií]nimas)", t):
        intent["min_active_cells"] = int(m.group(1))
    return intent


def sla_at_risk(kpi: Dict[str, Any], intent: Dict[str, Any]) -> bool:
    delay, thp = kpi.get("embb_delay_ms"), kpi.get("embb_thp_mbps")
    target = float(intent["cameras"]) * float(intent["camera_mbps"])
    return (isinstance(delay, (int, float)) and delay > float(intent["max_delay_ms"])) or \
        (isinstance(thp, (int, float)) and thp < target)


def plan(intent: Dict[str, Any], hour: int, report: Optional[Dict[str, Any]] = None,
         kpi: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """As três políticas A1 e o porquê de cada ajuste."""
    intent = {**DEFAULT_INTENT, **(intent or {})}
    report, kpi = report or {}, kpi or {}
    night = hour >= int(intent["night_start"]) or hour < int(intent["night_end"])
    rdl = dict(NIGHT if night else DAY)
    target = float(intent["cameras"]) * float(intent["camera_mbps"])
    slicer = {"embb_min_thp_mbps": max(1.0, target), "embb_max_delay_ms": float(intent["max_delay_ms"]),
              "mmtc_min_prb_pct": float(intent["mmtc_min_prb_pct"]), "slice_safety_margin": 0.15,
              "ranslicer_learned_policy": False}
    saver = {"es_sleep_threshold_pct": 15.0, "es_wake_threshold_pct": 60.0,
             "es_min_active_cells": int(intent["min_active_cells"]), "es_sleep_start_hour": int(intent["night_start"]),
             "es_sleep_end_hour": int(intent["night_end"]), "es_tx_power_reduction": True, "es_reduced_tx_power_dbm": 30.0}
    reasons = [f"período: {'noite' if night else 'dia'}"]

    if intent["energy_priority"] == "high" and night:
        rdl["energy_weight"] = 0.55
        saver["es_sleep_threshold_pct"] = 25.0
        reasons.append("intenção: energia prioritária")
    elif intent["energy_priority"] == "low":
        rdl.update(energy_weight=0.05, allow_neighbor_sleep=False)
        saver["es_sleep_threshold_pct"] = 5.0
        reasons.append("intenção: SLA prioritário")

    risk = sla_at_risk(kpi, intent)
    if risk:
        rdl.update(sla_weight=0.75, energy_weight=min(rdl["energy_weight"], 0.10), allow_neighbor_sleep=False)
        slicer["slice_safety_margin"] = 0.30
        saver.update(es_sleep_threshold_pct=min(saver["es_sleep_threshold_pct"], 5.0),
                     es_min_active_cells=max(saver["es_min_active_cells"], 2))
        reasons.append("SLA da fatia de câmeras em risco: prioriza SLA")
    else:
        lost = ((report.get("rejections") or {}).get("by_xapp") or {}).get("energysaver_greenran") or {}
        total = sum(lost.values())
        if night and total >= 10 and lost.get("LOST_ARBITRATION", 0) >= 0.7 * total:
            rdl["energy_weight"] = min(0.6, rdl["energy_weight"] + 0.1)
            reasons.append("EnergySaver perde a arbitragem à noite sem risco de SLA: mais peso de energia")
    if report.get("implicit_conflicts"):
        saver.update(es_sleep_threshold_pct=0.0, es_tx_power_reduction=False)
        rdl["allow_neighbor_sleep"] = False
        reasons.append("conflito implícito reportado pela RDL: desligamentos suspensos")
    return {"policies": {"20001": rdl, "21000": slicer, "21001": saver}, "sla_at_risk": risk, "reasons": reasons}


def policy_body(ric_id: str, service_id: str, policy_id: str, data: Dict[str, Any], policy_type: str = "20001") -> Dict[str, Any]:
    """Corpo do PUT /a1-policy/v2/policies do A1-PMS."""
    return {"ric_id": ric_id, "policy_id": policy_id, "service_id": service_id,
            "policytype_id": policy_type, "policy_data": data}


def _get_json(url: str) -> Dict[str, Any]:
    import requests
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def publish(pms_url: str, body: Dict[str, Any]) -> int:
    import requests
    base = pms_url.rstrip("/")
    requests.put(f"{base}/a1-policy/v2/services",
                 json={"service_id": body["service_id"], "keep_alive_interval_seconds": 0, "callback_url": ""},
                 timeout=10)
    resp = requests.put(f"{base}/a1-policy/v2/policies", json=body, timeout=10)
    print(f"A1-PMS {body['policytype_id']}/{body['policy_id']}: HTTP {resp.status_code} {resp.text[:160]}")
    return resp.status_code


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pms-url", default="http://policymanagementservice.nonrtric:8081")
    p.add_argument("--rdl-url", default="", help="RDL (GET /governance); vazio = sem relatório")
    p.add_argument("--kpi-url", default="")
    p.add_argument("--kpi-file", default="")
    p.add_argument("--intents", default="", help="arquivo JSON de intenção")
    p.add_argument("--intent-text", default="")
    p.add_argument("--ric-id", default="ric1")
    p.add_argument("--service-id", default="greenran-resource-optimizer")
    p.add_argument("--interval-s", type=float, default=60.0)
    p.add_argument("--once", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--hour", type=int, help="força a hora (teste)")
    args = p.parse_args(argv)

    intent: Dict[str, Any] = {}
    if args.intents:
        with open(args.intents, "r", encoding="utf-8") as fh:
            intent.update(json.load(fh))
    if args.intent_text:
        intent.update(parse_intent_text(args.intent_text))
    last: Dict[str, Any] = {}
    while True:
        hour = args.hour if args.hour is not None else datetime.now().hour
        report = _get_json(f"{args.rdl_url.rstrip('/')}/governance") if args.rdl_url else {}
        kpi: Dict[str, Any] = {}
        if args.kpi_url:
            kpi = _get_json(args.kpi_url)
        elif args.kpi_file:
            with open(args.kpi_file, "r", encoding="utf-8") as fh:
                kpi = json.load(fh)
        result = plan(intent, hour, report, kpi)
        bodies = [policy_body(args.ric_id, args.service_id, INSTANCES[t], data, t) for t, data in result["policies"].items()]
        if args.dry_run:
            print(json.dumps({"reasons": result["reasons"], "sla_at_risk": result["sla_at_risk"], "policies": bodies},
                             indent=2, ensure_ascii=False))
            return 0
        for body in bodies:
            if last.get(body["policytype_id"]) != body["policy_data"]:
                if publish(args.pms_url, body) not in (200, 201):
                    return 1
                last[body["policytype_id"]] = body["policy_data"]
        if args.once:
            return 0
        time.sleep(args.interval_s)


if __name__ == "__main__":
    raise SystemExit(main())
