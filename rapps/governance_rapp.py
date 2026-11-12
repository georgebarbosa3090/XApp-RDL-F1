#!/usr/bin/env python3
"""
rApp de governança (nível 4 da governança hierárquica; doc 11).

Lê o relatório da RDL (``GET /governance``: recusas por motivo e por xApp, conflitos implícitos,
rebaixamentos de ações críticas, registro de xApps) e decide, por regras fixas:

| Evidência no relatório | Ação |
| :-- | :-- |
| xApp com ``SAFETY`` ≥ ``--quarantine-safety`` recusas (ex.: Rogue propondo fora dos limites) | ``QUARANTINED`` por A1 |
| xApp com ``UNAUTHORIZED`` ≥ ``--quarantine-unauthorized`` (origem que não confere) | ``QUARANTINED`` por A1 |
| xApp com ≥ ``--critical-abuse`` ações críticas rebaixadas pela cota | teto de prioridade 94 por A1 (deixa de ser crítica pela prioridade) |
| xApp registrada suspeita em conflito implícito | ``QUARANTINED`` por A1 e recomendação de retirada |
| xApp não registrada suspeita, ou conflito ``out-of-band`` | recomendação: retirar a xApp ou investigar (operador) |
| dois rApps escrevendo o mesmo campo da A1 com valores diferentes (``rapp_conflicts``) | recomendação ao operador; a RDL já aplica a precedência por campo |

As ações sobre a RDL saem como **uma** instância da política A1 20000 (``rdl-governance``, campos
``xapp_modes`` e ``xapp_priority_caps``) publicada no A1-PMS. Retirar uma xApp (undeploy) só
acontece com ``--undeploy`` e ``--appmgr-url`` (``DELETE /ric/v1/xapps/{nome}`` do AppMgr do O-RAN SC);
sem isso, a recomendação é só impressa. Sair da quarentena é decisão do operador: o rApp não
libera sozinho uma xApp que já colocou em quarentena.

Uso:
    python rapps/governance_rapp.py --rdl-url http://service-ricxapp-iqos-xapp-rdl-http.ricxapp:8080 \\
        --pms-url http://policymanagementservice.nonrtric:8081 --once
    python rapps/governance_rapp.py --report relatorio.json --dry-run       # decide a partir de um arquivo
"""
import argparse
import json
import time
from typing import Any, Dict, List, Optional

POLICY_TYPE = "20000"
NON_CRITICAL_CAP = 94


def decide(report: Dict[str, Any], quarantine_safety: int = 5, quarantine_unauthorized: int = 20,
           critical_abuse: int = 10, previous: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Política A1 e recomendações a partir do relatório da RDL. ``previous``: decisão anterior
    (as quarentenas e tetos já aplicados se mantêm)."""
    modes: Dict[str, str] = dict((previous or {}).get("modes", {}))
    caps: Dict[str, int] = dict((previous or {}).get("caps", {}))
    reasons: Dict[str, List[str]] = {}
    recommendations: List[Dict[str, Any]] = []
    registered = set((report.get("xapps") or {}).get("xapps", {}))

    def quarantine(xapp: str, why: str) -> None:
        modes[xapp] = "QUARANTINED"
        reasons.setdefault(xapp, []).append(why)

    for xapp, counts in ((report.get("rejections") or {}).get("by_xapp") or {}).items():
        if counts.get("SAFETY", 0) >= quarantine_safety:
            quarantine(xapp, f"{counts['SAFETY']} propostas barradas pelo Safety Guard")
        if counts.get("UNAUTHORIZED", 0) >= quarantine_unauthorized:
            quarantine(xapp, f"{counts['UNAUTHORIZED']} propostas não autorizadas")

    for xapp, n in (report.get("critical_downgrades_by_xapp") or {}).items():
        if n >= critical_abuse and modes.get(xapp) != "QUARANTINED":
            caps[xapp] = min(caps.get(xapp, 100), NON_CRITICAL_CAP)
            reasons.setdefault(xapp, []).append(f"{n} ações críticas acima da cota")

    for finding in report.get("implicit_conflicts") or []:
        where = f"{finding.get('node_id')}/{finding.get('parameter')}"
        for suspect in finding.get("suspects") or []:
            if suspect == "out-of-band":
                recommendations.append({"action": "INVESTIGATE_OUT_OF_BAND", "target": where,
                                        "detail": finding.get("detail")})
            elif suspect in registered:
                quarantine(suspect, f"suspeita de conflito implícito em {where}")
                recommendations.append({"action": "UNDEPLOY_CANDIDATE", "xapp": suspect, "target": where})
            else:
                recommendations.append({"action": "UNDEPLOY", "xapp": suspect, "target": where,
                                        "detail": "xApp fora do registro agindo sobre o nó"})

    for c in report.get("rapp_conflicts") or []:
        # Conflito entre rApps na A1: a RDL já aplica a precedência; a decisão de quem fica é do operador
        recommendations.append({"action": "RESOLVE_A1_FIELD_CONFLICT", "field": c.get("field"),
                                "rule": c.get("rule"), "winner": c.get("winner"),
                                "writers": [w.get("policy") for w in c.get("writers") or []]})

    policy_data = {"xapp_modes": sorted(f"{x}:{m}" for x, m in modes.items()),
                   "xapp_priority_caps": sorted(f"{x}:{c}" for x, c in caps.items())}
    return {"modes": modes, "caps": caps, "policy_data": policy_data,
            "reasons": reasons, "recommendations": recommendations}


def policy_body(ric_id: str, service_id: str, policy_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {"ric_id": ric_id, "policy_id": policy_id, "service_id": service_id,
            "policytype_id": POLICY_TYPE, "policy_data": data}


def fetch_report(rdl_url: str) -> Dict[str, Any]:
    import requests
    resp = requests.get(f"{rdl_url.rstrip('/')}/governance", timeout=10)
    resp.raise_for_status()
    return resp.json()


def publish(pms_url: str, body: Dict[str, Any]) -> int:
    import requests
    base = pms_url.rstrip("/")
    requests.put(f"{base}/a1-policy/v2/services",
                 json={"service_id": body["service_id"], "keep_alive_interval_seconds": 0, "callback_url": ""},
                 timeout=10)
    resp = requests.put(f"{base}/a1-policy/v2/policies", json=body, timeout=10)
    print(f"A1-PMS: HTTP {resp.status_code} {resp.text[:200]}")
    return resp.status_code


def undeploy(appmgr_url: str, xapp: str) -> int:
    import requests
    resp = requests.delete(f"{appmgr_url.rstrip('/')}/ric/v1/xapps/{xapp}", timeout=30)
    print(f"AppMgr: undeploy {xapp}: HTTP {resp.status_code}")
    return resp.status_code


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rdl-url", default="http://service-ricxapp-iqos-xapp-rdl-http.ricxapp:8080")
    p.add_argument("--report", help="lê o relatório de um arquivo em vez da RDL")
    p.add_argument("--pms-url", default="http://policymanagementservice.nonrtric:8081")
    p.add_argument("--ric-id", default="ric1")
    p.add_argument("--service-id", default="rdl-governance-rapp")
    p.add_argument("--policy-id", default="rdl-governance")
    p.add_argument("--quarantine-safety", type=int, default=5)
    p.add_argument("--quarantine-unauthorized", type=int, default=20)
    p.add_argument("--critical-abuse", type=int, default=10)
    p.add_argument("--appmgr-url", default="")
    p.add_argument("--undeploy", action="store_true", help="retira as xApps recomendadas (exige --appmgr-url)")
    p.add_argument("--interval-s", type=float, default=30.0)
    p.add_argument("--once", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    previous: Dict[str, Any] = {}
    last_policy: Optional[Dict[str, Any]] = None
    while True:
        if args.report:
            with open(args.report, "r", encoding="utf-8") as fh:
                report = json.load(fh)
        else:
            report = fetch_report(args.rdl_url)
        decision = decide(report, args.quarantine_safety, args.quarantine_unauthorized, args.critical_abuse, previous)
        previous = decision
        body = policy_body(args.ric_id, args.service_id, args.policy_id, decision["policy_data"])
        if args.dry_run:
            print(json.dumps({"policy": body, "reasons": decision["reasons"],
                              "recommendations": decision["recommendations"]}, indent=2, ensure_ascii=False))
            return 0
        if decision["policy_data"] != last_policy:
            status = publish(args.pms_url, body)
            if status not in (200, 201):
                return 1
            last_policy = decision["policy_data"]
        for rec in decision["recommendations"]:
            print("Recomendação:", json.dumps(rec, ensure_ascii=False))
            if args.undeploy and args.appmgr_url and rec["action"] in ("UNDEPLOY", "UNDEPLOY_CANDIDATE"):
                undeploy(args.appmgr_url, rec["xapp"])
        if args.once:
            return 0
        time.sleep(args.interval_s)


if __name__ == "__main__":
    raise SystemExit(main())
