#!/usr/bin/env python3
# Autor: George Barbosa
"""
Driver do Traffic Steering original (o-ran-sc/ric-app-ts, sem alteração) na malha fechada (docs/16 §4.3, E3).

O TS roda como processo, compilado contra o RMR e o xapp-frame-cpp do O-RAN SC (xapps-originais/ts/build.sh),
com o descritor original (controle por REST, ``ts_control_api: rest``) apontando para este adaptador. O adaptador
faz os papéis que, no RIC, são de outras xApps (decisão D3 do docs/16):

- **AD (anomalia, RMR 30003):** UEs conectados com vazão abaixo de ``anomaly_thp_mbps`` na janela;
- **QP (predição, RMR 30002):** para cada UE da lista que o TS envia (``TS_UE_LIST``, 30000), a vazão
  prevista por célula: na servidora, a vazão medida; nas vizinhas, a medida escalada pela capacidade de
  Shannon, com o SINR da vizinha estimado por SINR servidor + (RSRP vizinha − RSRP servidora);
- **destino do controle:** servidor HTTP que recebe o ``HandOff`` do TS e o converte em proposta HANDOVER
  do UE para a RDL;
- **A1 20008:** a política de limiar (``threshold``) é enviada ao TS no início (RMR 20010).

Rotas RMR separadas por processo (``RMR_SEED_RT``): o 30000 do TS vai só para o adaptador; a RDL da malha
fechada não usa RMR, então não há colisão com o 30000 dela (RDL_ACTION_PROPOSAL).
"""

from __future__ import annotations

import ctypes
import json
import math
import os
import queue
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.closed_loop.drivers import XAppDriver

TS_PORT = 4560
TS_ANOMALY_UPDATE, TS_QOE_PREDICTION, A1_POLICY_REQ, TS_UE_LIST, TS_ANOMALY_ACK = 30003, 30002, 20010, 30000, 30004


class _Mbuf(ctypes.Structure):
    _fields_ = [("state", ctypes.c_int), ("mtype", ctypes.c_int), ("len", ctypes.c_int),
                ("payload", ctypes.POINTER(ctypes.c_ubyte)), ("xaction", ctypes.POINTER(ctypes.c_ubyte)),
                ("sub_id", ctypes.c_int), ("tp_state", ctypes.c_int), ("tp_buf", ctypes.c_void_p),
                ("header", ctypes.c_void_p), ("id", ctypes.POINTER(ctypes.c_ubyte)), ("flags", ctypes.c_int),
                ("alloc_len", ctypes.c_int), ("ring", ctypes.c_void_p), ("rts_fd", ctypes.c_int),
                ("cookie", ctypes.c_int)]


class Rmr:
    """RMR do O-RAN SC (librmr_si) por ctypes: envio e recepção com tabela de rotas estática."""

    def __init__(self, lib: str, port: int, seed_rt: str):
        os.environ["RMR_SEED_RT"] = seed_rt
        os.environ["RMR_RTG_SVC"] = "-1"
        self.lib = ctypes.CDLL(lib)
        L = self.lib
        L.rmr_init.restype = ctypes.c_void_p
        L.rmr_init.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
        L.rmr_ready.argtypes = [ctypes.c_void_p]
        L.rmr_alloc_msg.restype = ctypes.POINTER(_Mbuf)
        L.rmr_alloc_msg.argtypes = [ctypes.c_void_p, ctypes.c_int]
        L.rmr_send_msg.restype = ctypes.POINTER(_Mbuf)
        L.rmr_send_msg.argtypes = [ctypes.c_void_p, ctypes.POINTER(_Mbuf)]
        L.rmr_torcv_msg.restype = ctypes.POINTER(_Mbuf)
        L.rmr_torcv_msg.argtypes = [ctypes.c_void_p, ctypes.POINTER(_Mbuf), ctypes.c_int]
        L.rmr_free_msg.argtypes = [ctypes.POINTER(_Mbuf)]
        L.rmr_close.argtypes = [ctypes.c_void_p]
        self.ctx = L.rmr_init(f"{port}".encode(), 4096, 0)
        if not self.ctx:
            raise RuntimeError("rmr_init falhou")
        t0 = time.time()
        while not L.rmr_ready(self.ctx):
            if time.time() - t0 > 20:
                raise RuntimeError("RMR não ficou pronto (tabela de rotas)")
            time.sleep(0.1)

    def send(self, mtype: int, payload: bytes, retries: int = 50) -> bool:
        L = self.lib
        m = L.rmr_alloc_msg(self.ctx, max(len(payload), 64) + 16)
        m.contents.mtype, m.contents.sub_id = mtype, -1
        ctypes.memmove(m.contents.payload, payload, len(payload))
        m.contents.len = len(payload)
        for _ in range(retries):
            m = L.rmr_send_msg(self.ctx, m)
            if m and m.contents.state == 0:
                L.rmr_free_msg(m)
                return True
            if not m or m.contents.state != 10:    # 10 = RMR_ERR_RETRY
                break
            time.sleep(0.02)
        if m:
            L.rmr_free_msg(m)
        return False

    def recv(self, timeout_ms: int):
        m = self.lib.rmr_torcv_msg(self.ctx, None, timeout_ms)
        if not m:
            return None
        out = None
        if m.contents.state == 0:
            out = (m.contents.mtype, bytes(ctypes.string_at(m.contents.payload, m.contents.len)))
        self.lib.rmr_free_msg(m)
        return out

    def close(self) -> None:
        self.lib.rmr_close(self.ctx)


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class TsOriginalDriver(XAppDriver):
    """O ric-app-ts original no laço, com o adaptador fazendo AD, QP e o destino REST do controle."""

    name = "original:traffic_steering"

    def __init__(self, workdir: str, prefix: Optional[str] = None, threshold_pct: int = 5,
                 anomaly_thp_mbps: float = 0.2, priority: int = 80, wait_s: float = 0.25,
                 min_observation_s: float = 1.0):
        base = Path(os.environ.get("XAPPS_ORIGINAIS", os.path.expanduser("~/xapps-originais")))
        self.prefix = Path(prefix or base / "install")
        self.binary = base / "build-ts" / "src" / "ts_xapp" / "ts_xapp"
        self.workdir = Path(workdir)
        self.threshold_pct, self.anomaly_thp, self.priority, self.wait_s = threshold_pct, anomaly_thp_mbps, priority, wait_s
        self.min_observation_s = min_observation_s   # antes disso não há tráfego: todo UE pareceria anômalo
        self.posts: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self.log: List[Dict[str, Any]] = []
        self.proc = None
        self.rmr: Optional[Rmr] = None
        self.http: Optional[HTTPServer] = None
        self.gnb_of_cell: Dict[int, int] = {}
        self._seq = 0

    # ------------------------------------------------------------------ ciclo de vida
    def on_hello(self, hello: Dict[str, Any]) -> None:
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.gnb_of_cell = {int(g["cell_id"]): int(g["gnb"]) for g in hello["gnbs"]}
        posts = self.posts

        class H(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                try:
                    posts.put(json.loads(body))
                except ValueError:
                    pass
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "accepted"}')

            def log_message(self, *a):
                pass

        http_port, rmr_port = _free_port(), _free_port()
        self.http = HTTPServer(("127.0.0.1", http_port), H)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        # descritor original com o destino do controle REST apontando para o adaptador
        desc = json.loads((Path(__file__).resolve().parents[2] / "third_party" / "xapps" / "ric-app-ts" /
                           "xapp-descriptor" / "config-file.json").read_text(encoding="utf-8"))
        desc["controls"] = {"ts_control_api": "rest", "ts_control_ep": f"http://127.0.0.1:{http_port}/handoff"}
        (self.workdir / "config-file.json").write_text(json.dumps(desc, indent=2), encoding="utf-8")
        ts_rt = self.workdir / "ts_routes.rt"
        ts_rt.write_text(f"newrt|start\nrte|{TS_UE_LIST}|127.0.0.1:{rmr_port}\nnewrt|end\n", encoding="utf-8")
        ad_rt = self.workdir / "adapter_routes.rt"
        ad_rt.write_text("newrt|start\n" + "".join(f"rte|{m}|127.0.0.1:{TS_PORT}\n" for m in
                                                   (TS_ANOMALY_UPDATE, TS_QOE_PREDICTION, A1_POLICY_REQ)) +
                         "newrt|end\n", encoding="utf-8")
        env = dict(os.environ, RMR_SEED_RT=str(ts_rt), RMR_RTG_SVC="-1", XAPP_DESCRIPTOR_PATH=str(self.workdir),
                   LD_LIBRARY_PATH=f"{self.prefix / 'lib'}:{os.environ.get('LD_LIBRARY_PATH', '')}")
        self.proc = subprocess.Popen([str(self.binary)], cwd=self.workdir, env=env,
                                     stdout=open(self.workdir / "ts_stdout.log", "w"), stderr=subprocess.STDOUT)
        lib = next((p for p in (self.prefix / "lib" / "librmr_si.so", self.binary.parents[3] / "build-rmr" / "librmr_si.so")
                    if p.exists()), None)
        if lib is None:
            raise FileNotFoundError("librmr_si.so não encontrada (rode xapps-originais/ts/build.sh)")
        self.rmr = Rmr(str(lib), rmr_port, str(ad_rt))
        time.sleep(1.0)  # o TS sobe o listener RMR
        policy = {"operation": "CREATE", "policy_type_id": 20008, "policy_instance_id": "ts-limiar",
                  "payload": {"threshold": self.threshold_pct}}
        self.rmr.send(A1_POLICY_REQ, json.dumps(policy).encode())

    def close(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self.http:
            self.http.shutdown()
        if self.rmr:
            self.rmr.close()

    # ------------------------------------------------------------------ janela
    @staticmethod
    def _cap(sinr_db: float) -> float:
        return math.log2(1.0 + 10 ** (sinr_db / 10.0))

    def _prediction(self, u: Dict[str, Any]) -> Dict[str, Any]:
        serv = str(u["cell_id"])
        rsrp = {str(c): float(v) for c, v in (u.get("rsrp_dbm") or {}).items() if v is not None}
        thp_kbps = max(1, int(round(float(u.get("thp_mbps") or 0.0) * 1000)))
        cells = {serv: [thp_kbps, 0]}                     # a primeira célula é a servidora (regra do TS)
        sinr = u.get("sinr_db")
        if sinr is not None and serv in rsrp:
            base = self._cap(float(sinr))
            for c, r in rsrp.items():
                if c != serv and base > 0:
                    cells[c] = [max(0, int(round(thp_kbps * self._cap(float(sinr) + r - rsrp[serv]) / base))), 0]
        return {str(u["ue"]): cells}

    def on_kpm(self, kpm: Dict[str, Any]) -> List[Dict[str, Any]]:
        t = float(kpm["t"])
        props: List[Dict[str, Any]] = []
        if self.proc is None or self.proc.poll() is not None:
            raise RuntimeError(f"ts_xapp não está rodando (ver {self.workdir / 'ts_stdout.log'})")
        if t < self.min_observation_s:
            return props
        ues = {str(u["ue"]): u for u in kpm.get("ues", []) if u.get("connected")}
        anomalous = [uid for uid, u in ues.items()
                     if u.get("thp_mbps") is not None and float(u["thp_mbps"]) < self.anomaly_thp]
        if not anomalous:
            return props
        ad = [{"du-id": 1010, "ue-id": uid, "measTimeStampRf": int(t * 1000), "Degradation": "RSRP RSSINR"}
              for uid in anomalous]
        self.rmr.send(TS_ANOMALY_UPDATE, json.dumps(ad).encode())
        deadline = time.time() + 2.0
        answered = False
        while time.time() < deadline:
            got = self.rmr.recv(100)
            if got is None:
                if answered:
                    break
                continue
            mtype, payload = got
            if mtype == TS_UE_LIST:
                for uid in json.loads(payload.decode()).get("UEPredictionSet", []):
                    if uid in ues:
                        self.rmr.send(TS_QOE_PREDICTION, json.dumps(self._prediction(ues[uid])).encode())
                answered = True
                deadline = time.time() + self.wait_s       # tempo para o TS decidir e chamar o REST
        while True:
            try:
                post = self.posts.get(timeout=self.wait_s if answered else 0.0)
            except queue.Empty:
                break
            prop = self._to_proposal(post, t)
            self.log.append({"t": t, "ctrl": post, "proposal": prop})
            if prop:
                props.append(prop)
        return props

    def _to_proposal(self, post: Dict[str, Any], t: float) -> Optional[Dict[str, Any]]:
        try:
            src, dst, ue = int(post["fromCell"]), int(post["toCell"]), int(post["ue"])
        except (KeyError, ValueError, TypeError):
            return None
        if src not in self.gnb_of_cell or dst not in self.gnb_of_cell:
            return None
        self._seq += 1
        return {"t": t, "xapp_id": "traffic_steering", "gnb": self.gnb_of_cell[src], "parameter": "HANDOVER",
                "value": float(self.gnb_of_cell[dst]), "priority": self.priority, "ue": ue,
                "id": f"traffic_steering-g{self.gnb_of_cell[src]}-HANDOVER-{t:.3f}-{self._seq}", "xapp_impl": "original"}
