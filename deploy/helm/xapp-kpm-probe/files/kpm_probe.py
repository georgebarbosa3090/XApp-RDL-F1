#!/usr/bin/env python3
"""
xApp kpm-probe — assina E2SM-KPM v3.00 pelo SubMgr do Near-RT RIC Release I.

Fluxo:
  1. registra a xApp no AppMgr (o RtMgr passa a conhecer o endpoint RMR);
  2. acompanha os nós E2 no E2Mgr; a cada nó que fica CONNECTED, envia ao SubMgr (REST)
     uma subscrição REPORT com Event Trigger Format 1 e Action Definition Format 1,
     codificados em APER com asn1tools a partir do ASN.1 do NORI no commit fixado;
  3. recebe por RMR as RIC Indications (12050) e registra tipo, subscription id,
     tamanho e sha256 do payload — o sha256 permite casar cada Indication recebida com a
     mensagem correspondente no PCAP da execução.

Cada evento vai para stdout e para EVENTS_FILE (JSON Lines). A xApp não decide nada:
é a sonda que materializa os elos Subscription e KPM da cadeia closed-loop.
"""

import hashlib
import json
import os
import signal
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ENV = os.environ
NAME = ENV.get("XAPP_NAME", "kpm-probe")
VERSION = ENV.get("XAPP_VERSION", "0.1.0")
HTTP_HOST = ENV["XAPP_HTTP_HOST"]
RMR_HOST = ENV["XAPP_RMR_HOST"]
HTTP_PORT, RMR_PORT = 8080, 4560
E2MGR, SUBMGR, APPMGR = ENV["E2MGR_URL"], ENV["SUBMGR_URL"], ENV["APPMGR_URL"]
RAN_FUNCTION_ID = int(ENV.get("KPM_RAN_FUNCTION_ID", "200"))
REPORT_STYLE = int(ENV.get("KPM_REPORT_STYLE", "1"))
REPORTING_PERIOD_MS = int(ENV.get("KPM_REPORTING_PERIOD_MS", "1000"))
GRANULARITY_MS = int(ENV.get("KPM_GRANULARITY_PERIOD_MS", "1000"))
MEAS_NAMES = [n for n in ENV.get("KPM_MEAS_NAMES", "").split(",") if n]
ASN_DIR = ENV.get("ASN_DIR", "/data/asn")
EVENTS_FILE = ENV.get("EVENTS_FILE", "/data/logs/kpm_probe_events.jsonl")

RMR_TYPES = {12010: "RIC_SUB_REQ", 12011: "RIC_SUB_RESP", 12012: "RIC_SUB_FAILURE",
             12020: "RIC_SUB_DEL_REQ", 12021: "RIC_SUB_DEL_RESP", 12050: "RIC_INDICATION",
             12040: "RIC_CONTROL_REQ", 12041: "RIC_CONTROL_ACK", 12042: "RIC_CONTROL_FAILURE"}
RX = ["RIC_SUB_RESP", "RIC_SUB_FAILURE", "RIC_SUB_DEL_RESP", "RIC_INDICATION",
      "RIC_CONTROL_ACK", "RIC_CONTROL_FAILURE"]
TX = ["RIC_SUB_REQ", "RIC_SUB_DEL_REQ", "RIC_CONTROL_REQ"]

STOP = threading.Event()
READY = threading.Event()
_lock = threading.Lock()
os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
_events = open(EVENTS_FILE, "a", encoding="utf-8")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def event(kind: str, **fields) -> None:
    rec = {"t_utc": now(), "event": kind, **fields}
    line = json.dumps(rec, ensure_ascii=False, default=str)
    with _lock:
        _events.write(line + "\n")
        _events.flush()
        print(line, flush=True)


def http(method: str, url: str, body=None, timeout: float = 5.0):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw, status = exc.read().decode("utf-8", "replace"), exc.code
    except (urllib.error.URLError, OSError) as exc:
        return None, str(exc)
    try:
        return status, json.loads(raw) if raw.strip() else None
    except ValueError:
        return status, raw


# ---------------------------------------------------------------------------
# HTTP: saúde e notificações do SubMgr
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    def _reply(self, code: int, body=b"{}"):
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
        raw = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        try:
            body = json.loads(raw) if raw else None
        except ValueError:
            body = raw
        event("submgr_notification", path=self.path, body=body)
        self._reply(200)

    def log_message(self, *args):  # silencia o log padrão do http.server
        pass


# ---------------------------------------------------------------------------
# Registro no AppMgr
# ---------------------------------------------------------------------------

def xapp_config() -> dict:
    return {
        "name": NAME, "version": VERSION, "containers": [{"name": NAME}],
        "messaging": {"ports": [
            {"name": "http", "container": NAME, "port": HTTP_PORT, "description": "http"},
            {"name": "rmr-data", "container": NAME, "port": RMR_PORT, "rxMessages": RX, "txMessages": TX,
             "policies": [], "description": "rmr data"},
            {"name": "rmr-route", "container": NAME, "port": 4561, "description": "rmr route"},
        ]},
        "rmr": {"protPort": f"tcp:{RMR_PORT}", "maxSize": 65536, "numWorkers": 1,
                "rxMessages": RX, "txMessages": TX, "policies": []},
    }


def register() -> None:
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


def deregister() -> None:
    status, resp = http("POST", f"{APPMGR}/ric/v1/deregister", {"appName": NAME, "appInstanceName": NAME})
    event("appmgr_deregister", status=status, response=resp)


# ---------------------------------------------------------------------------
# E2SM-KPM v3.00 (ASN.1 do NORI)
# ---------------------------------------------------------------------------

def encode_kpm():
    import asn1tools
    files = [os.path.join(ASN_DIR, f) for f in ("e2sm-v03.01.asn", "e2sm-kpm-v03.00.asn")]
    spec = asn1tools.compile_files(files, "per")
    trigger = spec.encode("E2SM-KPM-EventTriggerDefinition", {
        "eventDefinition-formats": ("eventDefinition-Format1", {"reportingPeriod": REPORTING_PERIOD_MS})})
    action = spec.encode("E2SM-KPM-ActionDefinition", {
        "ric-Style-Type": REPORT_STYLE,
        "actionDefinition-formats": ("actionDefinition-Format1", {
            "measInfoList": [{"measType": ("measName", n), "labelInfoList": [{"measLabel": {"noLabel": "true"}}]}
                             for n in MEAS_NAMES],
            "granulPeriod": GRANULARITY_MS})})
    asn_hashes = {os.path.basename(f): hashlib.sha256(open(f, "rb").read()).hexdigest() for f in files}
    event("kpm_encoded", event_trigger_hex=trigger.hex(), action_definition_hex=action.hex(),
          meas_names=MEAS_NAMES, reporting_period_ms=REPORTING_PERIOD_MS, asn1_sha256=asn_hashes)
    return trigger, action


# ---------------------------------------------------------------------------
# Subscrição REST no SubMgr
# ---------------------------------------------------------------------------

_instance = [1000]


def subscribe(meid: str, trigger: bytes, action: bytes):
    _instance[0] += 1
    body = {
        "SubscriptionId": "",
        "ClientEndpoint": {"Host": HTTP_HOST, "HTTPPort": HTTP_PORT, "RMRPort": RMR_PORT},
        "Meid": meid,
        "RANFunctionID": RAN_FUNCTION_ID,
        "SubscriptionDetails": [{
            "XappEventInstanceId": _instance[0],
            "EventTriggers": list(trigger),
            "ActionToBeSetupList": [{
                "ActionID": 1, "ActionType": "report", "ActionDefinition": list(action),
                "SubsequentAction": {"SubsequentActionType": "continue", "TimeToWait": "zero"},
            }],
        }],
    }
    status, resp = http("POST", f"{SUBMGR}/ric/v1/subscriptions", body, timeout=10)
    event("subscription_request", meid=meid, ran_function_id=RAN_FUNCTION_ID,
          xapp_event_instance_id=_instance[0], status=status, response=resp)
    if status and 200 <= status < 300 and isinstance(resp, dict):
        return resp.get("SubscriptionId")
    return None


def unsubscribe(sub_id: str, meid: str) -> None:
    status, resp = http("DELETE", f"{SUBMGR}/ric/v1/subscriptions/{sub_id}", timeout=10)
    event("subscription_delete", meid=meid, subscription_id=sub_id, status=status, response=resp)


# ---------------------------------------------------------------------------
# RMR
# ---------------------------------------------------------------------------

COUNTS = {}


def rmr_loop() -> None:
    from ricxappframe.rmr import rmr
    ctx = rmr.rmr_init(str(RMR_PORT).encode(), rmr.RMR_MAX_RCV_BYTES, 0x00)
    if not ctx:
        event("rmr_error", detail="rmr_init falhou")
        STOP.set()
        return
    for _ in range(60):
        if rmr.rmr_ready(ctx) or STOP.is_set():
            break
        time.sleep(1)
    event("rmr_ready", ready=bool(rmr.rmr_ready(ctx)), port=RMR_PORT)
    READY.set()
    # rmr_torcv_msg precisa de um buffer alocado (com None devolve ponteiro nulo); o mesmo
    # buffer é reaproveitado a cada recepção, como no laço do ricxappframe.
    mbuf = rmr.rmr_alloc_msg(ctx, 4096)
    while not STOP.is_set():
        mbuf = rmr.rmr_torcv_msg(ctx, mbuf, 1000)
        if not mbuf:
            event("rmr_error", detail="rmr_torcv_msg devolveu buffer nulo; realocando")
            mbuf = rmr.rmr_alloc_msg(ctx, 4096)
            continue
        s = rmr.message_summary(mbuf)
        if s[rmr.RMR_MS_MSG_STATE] != rmr.RMR_OK:
            continue
        payload = s[rmr.RMR_MS_PAYLOAD] or b""
        mtype, sub_id = s[rmr.RMR_MS_MSG_TYPE], s[rmr.RMR_MS_SUB_ID]
        COUNTS[(mtype, sub_id)] = COUNTS.get((mtype, sub_id), 0) + 1
        meid = s[rmr.RMR_MS_MEID]
        event("rmr_message", mtype=mtype, mtype_name=RMR_TYPES.get(mtype, "?"), sub_id=sub_id,
              meid=meid.decode("utf-8", "replace") if isinstance(meid, bytes) else meid,
              length=len(payload), sha256=hashlib.sha256(payload).hexdigest(),
              seq=COUNTS[(mtype, sub_id)], source=s[rmr.RMR_MS_MSG_SOURCE])
    rmr.rmr_free_msg(mbuf)
    rmr.rmr_close(ctx)


# ---------------------------------------------------------------------------
# Laço principal: nós E2 no E2Mgr
# ---------------------------------------------------------------------------

def main() -> int:
    signal.signal(signal.SIGTERM, lambda *_: STOP.set())
    signal.signal(signal.SIGINT, lambda *_: STOP.set())
    event("start", name=NAME, version=VERSION, http_host=HTTP_HOST, rmr_host=RMR_HOST,
          e2mgr=E2MGR, submgr=SUBMGR, appmgr=APPMGR, ran_function_id=RAN_FUNCTION_ID)
    server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    def rmr_guard():
        try:
            rmr_loop()
        except Exception as exc:  # noqa: BLE001 - sem RMR a sonda não serve: encerra e o k8s reinicia
            event("rmr_error", detail=f"{type(exc).__name__}: {exc}")
            STOP.set()

    threading.Thread(target=rmr_guard, daemon=True).start()
    trigger, action = encode_kpm()
    register()

    subs = {}      # meid -> subscription id
    attempts = {}  # meid -> tentativas na conexão atual
    status_seen = {}
    while not STOP.is_set():
        code, nodes = http("GET", f"{E2MGR}/v1/nodeb/states")
        if code != 200 or not isinstance(nodes, list):
            STOP.wait(2)
            continue
        for node in nodes:
            meid, state = node.get("inventoryName"), node.get("connectionStatus")
            if not meid:
                continue
            if status_seen.get(meid) != state:
                event("e2_node_status", meid=meid, status=state, global_nb_id=node.get("globalNbId"))
                status_seen[meid] = state
            if state == "CONNECTED" and meid not in subs and attempts.get(meid, 0) < 5:
                attempts[meid] = attempts.get(meid, 0) + 1
                sub_id = subscribe(meid, trigger, action)
                if sub_id:
                    subs[meid] = sub_id
            elif state != "CONNECTED":
                attempts.pop(meid, None)
                if meid in subs:
                    indications = {str(k[1]): v for k, v in COUNTS.items() if k[0] == 12050}
                    event("e2_node_disconnected", meid=meid, subscription_id=subs[meid],
                          indications_by_sub_id=indications)
                    unsubscribe(subs.pop(meid), meid)
        STOP.wait(1)

    for meid, sub_id in subs.items():
        unsubscribe(sub_id, meid)
    deregister()
    server.shutdown()
    event("stop")
    return 0


if __name__ == "__main__":
    sys.exit(main())
