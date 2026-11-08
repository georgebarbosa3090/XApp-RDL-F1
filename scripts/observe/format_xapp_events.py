#!/usr/bin/env python3
"""
Formata ao vivo os eventos da xApp kpm-probe (JSON Lines no stdout do pod) em linhas legíveis:
subscrição, KPM decodificado por UE (fatia, PRBs), decisão do H-RDL, RIC Control e ACK.

Uso:
    kubectl -n ricxapp logs -f deploy/kpm-probe --since=1s | python3 scripts/observe/format_xapp_events.py
    ... | python3 scripts/observe/format_xapp_events.py --indications   # também cada Indication RMR
"""

import json
import sys

RMR = {12050: "RIC_INDICATION", 12041: "RIC_CONTROL_ACK", 12042: "RIC_CONTROL_FAILURE"}
C = {"t": "\033[2m", "e2": "\033[36m", "kpm": "\033[32m", "dec": "\033[35m", "ctl": "\033[33m", "ok": "\033[1;32m",
     "err": "\033[1;31m", "x": "\033[0m"}


def out(color: str, ts: str, text: str) -> None:
    print(f"{C['t']}{ts[11:23]}{C['x']} {C[color]}{text}{C['x']}", flush=True)


def fmt(ev: dict, show_indications: bool) -> None:
    t, kind = ev.get("t_utc", ""), ev.get("event")
    if kind == "start":
        out("e2", t, f"xApp iniciada | modo {ev.get('rc_decision')} | src/ {str(ev.get('src_commit', ''))[:7]} | "
                     f"RAN function KPM {ev.get('ran_function_id')} / RC {ev.get('rc_ran_function_id')}")
    elif kind == "appmgr_register":
        out("e2", t, f"registro no AppMgr: HTTP {ev.get('status')}")
    elif kind == "rmr_ready":
        out("e2", t, f"RMR pronto (tabela de rotas do RtMgr recebida): {ev.get('ready')}")
    elif kind == "e2_node_status":
        out("e2", t, f"nó E2 {ev.get('meid')}: {ev.get('status')}")
    elif kind == "subscription_request":
        resp = ev.get("response") if isinstance(ev.get("response"), dict) else {}
        out("e2", t, f"RIC Subscription (KPM, função {ev.get('ran_function_id')}) -> SubMgr: HTTP {ev.get('status')} "
                     f"id {resp.get('SubscriptionId', '?')}")
    elif kind == "submgr_notification":
        for inst in (ev.get("body") or {}).get("SubscriptionInstances") or []:
            ok = inst.get("E2EventInstanceId", 0) != 0
            out("ok" if ok else "err", t, f"Subscription Response do nó: E2EventInstanceId {inst.get('E2EventInstanceId')}"
                                         f"{'' if ok else ' | erro: ' + str(inst.get('ErrorCause'))}")
    elif kind == "kpm" and ev.get("format") == 1:
        n = ev.get("node") or {}
        out("kpm", t, f"KPM nó: PRB usados {n.get('RRU.PrbUsedDl')} / disponíveis {n.get('RRU.PrbAvailDl')} | "
                      f"UEs ativos {n.get('DRB.MeanActiveUeDl')} | RRC conectados {n.get('RRC.ConnMean')} | "
                      f"TBs DL {n.get('TB.TotNbrDlInitial')}")
    elif kind == "kpm" and ev.get("format") == 3:
        parts = [f"UE {u.get('ue_id')} SST {u.get('DRB.NetworkSlicing.SST')} PRB {u.get('RRU.PrbUsedDl')} "
                 f"vazão {u.get('DRB.UEThpDl')} TBs {u.get('TB.TotNbrDl.1')}" for u in ev.get("ues") or []]
        out("kpm", t, "KPM UEs: " + " | ".join(parts))
    elif kind == "rmr_message" and (show_indications or ev.get("mtype") != 12050):
        out("e2", t, f"RMR {RMR.get(ev.get('mtype'), ev.get('mtype'))} sub {ev.get('sub_id')} #{ev.get('seq')} "
                     f"{ev.get('length')} B sha256 {str(ev.get('sha256'))[:12]}")
    elif kind in ("control_request", "control_decision"):
        d = ev.get("decision") or {}
        res = ", ".join(f"{r['conflict_type']}->{r['strategy']}" for r in d.get("resolutions", [])) or "sem conflito"
        sel = "; ".join(f"{s.get('xapp_id')} {s.get('parameter')} {s.get('value')} @{str(s.get('target', '')).rsplit('#', 1)[-1]}"
                        for s in d.get("selected") or []) if isinstance(d.get("selected"), list) else str(d.get("selected"))
        out("dec", t, f"decisão {ev.get('decision_source')} | cenário {d.get('scenario', '-')} | {res} | selecionadas: {sel or '—'}")
        for s in d.get("not_actuated") or []:
            out("dec", t, f"   não atuável no NORI: {s.get('xapp_id')} {s.get('parameter')} -> {s.get('reason')}")
        if d.get("not_selected"):
            out("dec", t, f"   não selecionadas (conflito ou Safety Guard): {', '.join(d['not_selected'])}")
        if kind == "control_request":
            q = " / ".join(f"SST {x['sst']} teto {x['max_prb_ratio']} %" for x in ev.get("quotas") or [])
            out("ctl", t, f"RIC Control -> nó: RICrequestID {ev.get('ric_requestor_id')}/{ev.get('ric_instance_id')} "
                          f"função {ev.get('ran_function_id')} | {q} | RMR ok {ev.get('rmr_ok')} | {ev.get('length')} B")
        else:
            out("ctl", t, f"sem RIC Control: {d.get('reason')}")
    elif kind == "control_outcome":
        out("ok" if ev.get("outcome") == "ACK" and ev.get("correlated_with_request") else "err", t,
            f"RIC Control {ev.get('outcome')} do nó: RICrequestID {ev.get('ric_requestor_id')}/{ev.get('ric_instance_id')} "
            f"correlacionado {ev.get('correlated_with_request')} | {ev.get('latency_ms')} ms")
    elif kind in ("e2_node_disconnected", "subscription_delete", "control_error", "kpm_decode_error", "rmr_error"):
        out("err" if "error" in kind else "e2", t, f"{kind}: " + json.dumps({k: v for k, v in ev.items() if k not in ('t_utc', 'event')},
                                                                          ensure_ascii=False)[:200])


def main() -> int:
    show = "--indications" in sys.argv
    for line in sys.stdin:
        line = line.strip()
        if not line.startswith("{"):
            continue        # linhas de estatística do RMR e afins
        try:
            fmt(json.loads(line), show)
        except (ValueError, KeyError, TypeError):
            continue
    return 0


if __name__ == "__main__":
    sys.exit(main())
