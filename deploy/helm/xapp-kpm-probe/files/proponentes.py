#!/usr/bin/env python3
# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
xApps proponentes na bancada NORI (docs/16 §10.2, opção C do híbrido): RANSlicer-GreenRAN, derivada do xSlice e
``embb_throughput``, sem alteração na regra de decisão, lendo o KPM real do gNB do NORI pelo Near-RT RIC.

Fluxo:
  1. registra o pod no AppMgr (o RtMgr cria as rotas: RIC_INDICATION para cá, 30000 daqui para a kpm-probe e
     30001 da kpm-probe para cá);
  2. a cada nó E2 CONNECTED no E2Mgr, uma subscrição KPM no SubMgr (a mesma da kpm-probe), repartida entre as
     três xApps (um endpoint RMR para as três: o SubMgr funde subscrições iguais do mesmo endpoint);
  3. cada Indication (E2AP + E2SM-KPM v3) vira amostra da célula (``normalize_kpm``) para cada xApp; depois da
     Indication de UEs, cada xApp decide e as propostas vão à RDL da kpm-probe pelo RMR 30000;
  4. ``RDL_ACTION_RESULT`` (30001) com a recusa volta à xApp de origem (``on_result``).

No RtMgr do Release I, 30000 e 30001 têm os nomes TS_UE_LIST e TS_QOE_PRED_REQ (colisão do docs/16 §4.3).
Cada evento vai para stdout e para EVENTS_FILE (JSON Lines).
"""

import hashlib
import importlib
import json
import os
import queue
import signal
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ENV = os.environ
NAME = ENV.get("XAPP_NAME", "nori-proponentes")
VERSION = ENV.get("XAPP_VERSION", "0.1.0")
HTTP_HOST, RMR_HOST = ENV["XAPP_HTTP_HOST"], ENV["XAPP_RMR_HOST"]
HTTP_PORT, RMR_PORT = 8080, 4560
E2MGR, SUBMGR, APPMGR = ENV["E2MGR_URL"], ENV["SUBMGR_URL"], ENV["APPMGR_URL"]
RAN_FUNCTION_ID = int(ENV.get("KPM_RAN_FUNCTION_ID", "200"))
REPORT_STYLE = int(ENV.get("KPM_REPORT_STYLE", "1"))
REPORTING_PERIOD_MS = int(ENV.get("KPM_REPORTING_PERIOD_MS", "1000"))
GRANULARITY_MS = int(ENV.get("KPM_GRANULARITY_PERIOD_MS", "1000"))
MEAS_NAMES = [n for n in ENV.get("KPM_MEAS_NAMES", "").split(",") if n]
ASN_DIR = ENV.get("ASN_DIR", "/data/asn")
EVENTS_FILE = ENV.get("EVENTS_FILE", "/data/logs/proponentes_events.jsonl")
APP_DIR = ENV.get("XAPP_RDL_APP_DIR", "/data/app")
SRC_COMMIT = ENV.get("XAPP_RDL_SRC_COMMIT", "")
XAPPS = [x for x in ENV.get("PROPONENTES", "ranslicer,xslice,embb_throughput").split(",") if x]
PROPOSAL, RESULT = 30000, 30001
CLASSES = {"ranslicer": ("src.greenran.ranslicer_greenran", "RanSlicer"),
           "xslice": ("src.xapps.derivadas", "XSliceDerivada"),
           "embb_throughput": ("src.xapps.proprias", "EmbbThroughput")}
RX = ["RIC_SUB_RESP", "RIC_SUB_FAILURE", "RIC_SUB_DEL_RESP", "RIC_INDICATION", "TS_QOE_PRED_REQ"]
TX = ["RIC_SUB_REQ", "RIC_SUB_DEL_REQ", "TS_UE_LIST"]

sys.path.insert(0, APP_DIR)
from src.e2.v3 import codec  # noqa: E402

STOP, READY = threading.Event(), threading.Event()
OUTBOX: "queue.Queue[dict]" = queue.Queue()
_lock = threading.Lock()
os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
_events = open(EVENTS_FILE, "a", encoding="utf-8")
T0 = time.monotonic()


def event(kind: str, **fields) -> None:
    rec = {"t_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
           "event": kind, **fields}
    line = json.dumps(rec, ensure_ascii=False, default=str)
    with _lock:
        _events.write(line + "\n")
        _events.flush()
        print(line, flush=True)


def http(method, url, body=None, timeout=5.0):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw, status = resp.read().decode("utf-8", "replace"), resp.status
    except urllib.error.HTTPError as exc:
        raw, status = exc.read().decode("utf-8", "replace"), exc.code
    except (urllib.error.URLError, OSError) as exc:
        return None, str(exc)
    try:
        return status, json.loads(raw) if raw.strip() else None
    except ValueError:
        return status, raw


class Handler(BaseHTTPRequestHandler):
    def _reply(self, code, body=b"{}"):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/ric/v1/health/alive":
            self._reply(200)
        elif self.path == "/ric/v1/health/ready":
            self._reply(200 if READY.is_set() else 503)
        elif self.path.startswith("/ric/v1/config"):
            self._reply(200, json.dumps([xapp_config()]).encode())
        else:
            self._reply(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        event("submgr_notification", path=self.path, body=self.rfile.read(length).decode("utf-8", "replace") if length else "")
        self._reply(200)

    def log_message(self, *args):
        pass


def xapp_config():
    return {"name": NAME, "version": VERSION, "containers": [{"name": NAME}],
            "messaging": {"ports": [
                {"name": "http", "container": NAME, "port": HTTP_PORT, "description": "http"},
                {"name": "rmr-data", "container": NAME, "port": RMR_PORT, "rxMessages": RX, "txMessages": TX,
                 "policies": [], "description": "rmr data"},
                {"name": "rmr-route", "container": NAME, "port": 4561, "description": "rmr route"}]},
            "rmr": {"protPort": f"tcp:{RMR_PORT}", "maxSize": 65536, "numWorkers": 1, "rxMessages": RX, "txMessages": TX,
                    "policies": []}}


def register():
    body = {"appName": NAME, "appVersion": VERSION, "configPath": "", "appInstanceName": NAME,
            "httpEndpoint": f"{HTTP_HOST}:{HTTP_PORT}", "rmrEndpoint": f"{RMR_HOST}:{RMR_PORT}",
            "config": json.dumps(xapp_config())}
    delay = 2.0
    while not STOP.is_set():
        status, resp = http("POST", f"{APPMGR}/ric/v1/register", body)
        event("appmgr_register", status=status, response=resp)
        if status and 200 <= status < 300:
            return
        STOP.wait(delay)
        delay = min(delay * 2, 30.0)


class QueueTransport:
    """Transporte das xApps no pod: a proposta entra na fila e a thread RMR a envia (30000)."""

    def __init__(self, xapp_id):
        self.xapp_id, self.on_result = xapp_id, None

    def send(self, proposal):
        OUTBOX.put(dict(proposal, xapp_id=proposal.get("xapp_id", self.xapp_id)))
        return True

    def start(self):
        return "rmr-compartilhado"

    def stop(self):
        pass


APPS = {}       # xapp_id -> instância


def build_apps():
    global APPS
    fresh = {}
    for name in XAPPS:
        module, cls = CLASSES[name]
        klass = getattr(importlib.import_module(module), cls)
        app = klass(transport=QueueTransport(klass.XAPP_ID), clock=lambda: time.monotonic() - T0)
        fresh[app.XAPP_ID] = app
    APPS = fresh                      # troca atômica: a thread RMR nunca vê o dicionário pela metade
    event("xapps", xapps={k: type(v).__name__ for k, v in APPS.items()}, src_commit=SRC_COMMIT)


E2SM = None


def kpm_subscription():
    global E2SM
    E2SM = codec.E2smCodec(ASN_DIR, download=False)
    return E2SM.kpm_event_trigger(REPORTING_PERIOD_MS), E2SM.kpm_action_definition(MEAS_NAMES, GRANULARITY_MS, REPORT_STYLE)


_instance = [2000]


def subscribe(meid, trigger, action):
    _instance[0] += 1
    body = {"SubscriptionId": "", "ClientEndpoint": {"Host": HTTP_HOST, "HTTPPort": HTTP_PORT, "RMRPort": RMR_PORT},
            "Meid": meid, "RANFunctionID": RAN_FUNCTION_ID,
            "SubscriptionDetails": [{"XappEventInstanceId": _instance[0], "EventTriggers": list(trigger),
                                     "ActionToBeSetupList": [{"ActionID": 1, "ActionType": "report",
                                                              "ActionDefinition": list(action),
                                                              "SubsequentAction": {"SubsequentActionType": "continue",
                                                                                   "TimeToWait": "zero"}}]}]}
    status, resp = http("POST", f"{SUBMGR}/ric/v1/subscriptions", body, timeout=10)
    event("subscription_request", meid=meid, status=status, response=resp, xapps=list(APPS))
    return resp.get("SubscriptionId") if status and 200 <= status < 300 and isinstance(resp, dict) else None


def unsubscribe(sub_id, meid):
    status, resp = http("DELETE", f"{SUBMGR}/ric/v1/subscriptions/{sub_id}", timeout=10)
    event("subscription_delete", meid=meid, subscription_id=sub_id, status=status)


def on_indication(meid, payload, sha):
    try:
        pdu = codec.decode_e2ap_pdu(payload)
        kpm = E2SM.kpm_decode_indication(pdu["indication_header"], pdu["indication_message"])
    except Exception as exc:  # noqa: BLE001
        event("kpm_decode_error", meid=meid, sha256=sha, detail=f"{type(exc).__name__}: {exc}")
        return
    report = {"node": kpm["node"]} if kpm["format"] == 1 else {"ues": kpm.get("ues") or []}
    event("kpm", meid=meid, format=kpm["format"], sha256=sha, n_ues=len(report.get("ues", [])) or None)
    for xid, app in APPS.items():
        sample = app.observe_kpm(meid, report)
        if kpm["format"] != 1:      # depois da Indication de UEs: amostra da célula completa, cada xApp decide
            props = app.step(now=time.monotonic() - T0)
            event("decision", xapp_id=xid, meid=meid, load_pct=sample.load_pct, proposals=len(props),
                  slices={k: {"ues": v.ues, "thp_mbps": v.thp_mbps, "delay_ms": v.delay_ms} for k, v in sample.slices.items()})


def on_result(payload):
    try:
        result = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        event("result_decode_error", length=len(payload))
        return
    app = APPS.get(result.get("xapp_id"))
    event("result", accepted_by=bool(app), **{k: result.get(k) for k in ("xapp_id", "action_id", "parameter", "reason")})
    if app is not None:
        app.on_result(result)


def rmr_loop():
    from ricxappframe.rmr import rmr
    ctx = rmr.rmr_init(str(RMR_PORT).encode(), rmr.RMR_MAX_RCV_BYTES, 0x00)
    for _ in range(60):
        if rmr.rmr_ready(ctx) or STOP.is_set():
            break
        time.sleep(1)
    event("rmr_ready", ready=bool(rmr.rmr_ready(ctx)), port=RMR_PORT)
    READY.set()
    mbuf = rmr.rmr_alloc_msg(ctx, 4096)
    while not STOP.is_set():
        while not OUTBOX.empty():
            p = OUTBOX.get_nowait()
            body = json.dumps(p).encode("utf-8")
            sbuf = rmr.rmr_alloc_msg(ctx, len(body), payload=body, gen_transaction_id=True, mtype=PROPOSAL)
            state = None
            for _ in range(10):
                sbuf = rmr.rmr_send_msg(ctx, sbuf)
                state = sbuf.contents.state
                if state != rmr.RMR_ERR_RETRY:
                    break
                time.sleep(0.05)
            rmr.rmr_free_msg(sbuf)
            if "relay_control_outcome" in p:
                event("control_outcome_relayed", rmr_ok=state == rmr.RMR_OK, rmr_state=state,
                      mtype=p["relay_control_outcome"]["mtype"], sha256=p["relay_control_outcome"]["sha256"])
                continue
            event("proposal", rmr_ok=state == rmr.RMR_OK, rmr_state=state, sha256=hashlib.sha256(body).hexdigest(),
                  **{k: p.get(k) for k in ("xapp_id", "node_id", "parameter", "value", "priority")})
        mbuf = rmr.rmr_torcv_msg(ctx, mbuf, 100)
        if not mbuf:
            mbuf = rmr.rmr_alloc_msg(ctx, 4096)
            continue
        s = rmr.message_summary(mbuf)
        if s[rmr.RMR_MS_MSG_STATE] != rmr.RMR_OK:
            continue
        payload, mtype = s[rmr.RMR_MS_PAYLOAD] or b"", s[rmr.RMR_MS_MSG_TYPE]
        meid = s[rmr.RMR_MS_MEID]
        meid = meid.decode("utf-8", "replace") if isinstance(meid, bytes) else meid
        if mtype == 12050 and meid:
            on_indication(meid, payload, hashlib.sha256(payload).hexdigest())
        elif mtype == RESULT:
            on_result(payload)
        elif mtype in (12041, 12042):
            # Com duas xApps registradas, o RtMgr do Release I gera uma linha mse|12041|-1 (e 12042) por xApp e o
            # E2Term entrega cada ACK/Failure a uma delas. O que cai aqui é da kpm-probe: repassa os bytes
            # originais pela rota 30000 (o sha256 continua casando com o PCAP).
            sha = hashlib.sha256(payload).hexdigest()
            OUTBOX.put({"relay_control_outcome": {"mtype": mtype, "meid": meid, "payload_hex": payload.hex(),
                                                   "sha256": sha, "relayed_by": NAME}})
            event("control_outcome_misrouted", mtype=mtype, meid=meid, sha256=sha, length=len(payload))
        else:
            event("rmr_message", mtype=mtype, length=len(payload), meid=meid)
    rmr.rmr_close(ctx)


def main():
    signal.signal(signal.SIGTERM, lambda *_: STOP.set())
    event("start", name=NAME, src_commit=SRC_COMMIT, xapps=XAPPS, ran_function_id=RAN_FUNCTION_ID, rx=RX, tx=TX)
    build_apps()
    threading.Thread(target=ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), Handler).serve_forever, daemon=True).start()
    trigger, action = kpm_subscription()

    def guard():
        try:
            rmr_loop()
        except Exception as exc:  # noqa: BLE001
            event("rmr_error", detail=f"{type(exc).__name__}: {exc}")
            STOP.set()
    threading.Thread(target=guard, daemon=True).start()
    register()
    subs, seen = {}, {}
    while not STOP.is_set():
        code, nodes = http("GET", f"{E2MGR}/v1/nodeb/states")
        if code == 200 and isinstance(nodes, list):
            for node in nodes:
                meid, state = node.get("inventoryName"), node.get("connectionStatus")
                if not meid:
                    continue
                if seen.get(meid) != state:
                    event("e2_node_status", meid=meid, status=state)
                    seen[meid] = state
                if state == "CONNECTED" and meid not in subs:
                    sub = subscribe(meid, trigger, action)
                    if sub:
                        subs[meid] = sub
                elif state != "CONNECTED" and meid in subs:
                    unsubscribe(subs.pop(meid), meid)
                    build_apps()      # nova execução: xApps sem estado da anterior
        STOP.wait(1)
    for meid, sub in subs.items():
        unsubscribe(sub, meid)
    event("stop")
    return 0


if __name__ == "__main__":
    sys.exit(main())
