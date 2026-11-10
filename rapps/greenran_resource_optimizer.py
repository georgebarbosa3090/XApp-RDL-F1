#!/usr/bin/env python3
"""
rApp de exemplo do GreenRAN (papel do rApp-ResourceOptimizer): publica a política A1 20001 no
A1-PMS do Non-RT RIC conforme o período do dia (doc 10 §3, passo 5).

Não substitui o rApp da UFRGS; serve para testar a integração SMO → A1-PMS → A1 Mediator → RDL.

- Período de baixa demanda (noite, padrão 22h–6h): mais peso de energia e sleep de vizinhas
  permitido.
- Período de alta demanda: mais peso de SLA e sleep de vizinhas proibido.

Uso:
    python rapps/greenran_resource_optimizer.py --pms-url http://<a1pms>:8081 --ric-id ric1 --once
    python rapps/greenran_resource_optimizer.py --pms-url ... --interval-s 300     # laço
    python rapps/greenran_resource_optimizer.py --dry-run --hour 3                  # só imprime
"""

import argparse
import json
import time
from datetime import datetime
from typing import Any, Dict

NIGHT = {"energy_weight": 0.45, "sla_weight": 0.35, "allow_neighbor_sleep": True, "low_power_threshold_dbm": 10}
DAY = {"energy_weight": 0.10, "sla_weight": 0.60, "allow_neighbor_sleep": False, "low_power_threshold_dbm": 10}


def objectives_for(hour: int, night_start: int = 22, night_end: int = 6) -> Dict[str, Any]:
    is_night = hour >= night_start or hour < night_end
    return dict(NIGHT if is_night else DAY)


def policy_body(ric_id: str, service_id: str, policy_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Corpo do PUT /a1-policy/v2/policies do A1-PMS."""
    return {"ric_id": ric_id, "policy_id": policy_id, "service_id": service_id,
            "policytype_id": "20001", "policy_data": data}


def publish(pms_url: str, body: Dict[str, Any]) -> int:
    import requests

    base = pms_url.rstrip("/")
    requests.put(f"{base}/a1-policy/v2/services",
                 json={"service_id": body["service_id"], "keep_alive_interval_seconds": 0, "callback_url": ""},
                 timeout=10)
    resp = requests.put(f"{base}/a1-policy/v2/policies", json=body, timeout=10)
    print(f"A1-PMS: HTTP {resp.status_code} {resp.text[:200]}")
    return resp.status_code


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pms-url", default="http://policymanagementservice.nonrtric:8081")
    p.add_argument("--ric-id", default="ric1")
    p.add_argument("--service-id", default="greenran-resource-optimizer")
    p.add_argument("--policy-id", default="greenran")
    p.add_argument("--interval-s", type=float, default=300.0)
    p.add_argument("--once", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--hour", type=int, help="força a hora (teste)")
    args = p.parse_args(argv)

    while True:
        hour = args.hour if args.hour is not None else datetime.now().hour
        body = policy_body(args.ric_id, args.service_id, args.policy_id, objectives_for(hour))
        if args.dry_run:
            print(json.dumps(body, indent=2, ensure_ascii=False))
            return 0
        status = publish(args.pms_url, body)
        if args.once:
            return 0 if status in (200, 201) else 1
        time.sleep(args.interval_s)


if __name__ == "__main__":
    raise SystemExit(main())
