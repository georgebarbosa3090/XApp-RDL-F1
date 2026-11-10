#!/usr/bin/env python3
"""
Adaptador A1 entre o A1-PMS (Non-RT RIC) e o A1 Mediator do O-RAN SC (Near-RT RIC).

O A1 Mediator 3.2.2 (Release I) expõe os caminhos do A1AP v2 (``/A1-P/v2/...``), mas devolve o
tipo de política no formato OSC (``create_schema``). O A1-PMS 2.8.0, ao detectar esses caminhos,
usa o cliente A1AP v2 e procura ``policySchema``; sem ele, a sincronização com o RIC falha
("JSONObject["policySchema"] not found") e o RIC fica UNAVAILABLE.

Este adaptador repassa todas as requisições ao mediador sem alterá-las e só acrescenta
``policySchema`` (cópia de ``create_schema``) na resposta de ``GET /A1-P/v2/policytypes/{id}``.
Só usa a biblioteca padrão.
"""

import json
import os
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = os.environ.get("A1_UPSTREAM", "http://service-ricplt-a1mediator-http.ricplt:10000").rstrip("/")
TYPE_PATH = re.compile(r"^/A1-P/v2/policytypes/[^/]+/?$")


class Handler(BaseHTTPRequestHandler):
    def _forward(self, method: str) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        req = urllib.request.Request(UPSTREAM + self.path, data=body, method=method)
        if self.headers.get("Content-Type"):
            req.add_header("Content-Type", self.headers["Content-Type"])
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status, payload, ctype = resp.status, resp.read(), resp.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as err:
            status, payload, ctype = err.code, err.read(), err.headers.get("Content-Type", "application/json")
        except Exception as exc:  # mediador fora do ar
            status, payload, ctype = 502, json.dumps({"error": str(exc)}).encode(), "application/json"

        if method == "GET" and status == 200 and TYPE_PATH.match(self.path):
            try:
                doc = json.loads(payload)
                if "create_schema" in doc and "policySchema" not in doc:
                    doc["policySchema"] = doc["create_schema"]
                    payload = json.dumps(doc).encode()
            except ValueError:
                pass

        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if payload:
            self.wfile.write(payload)

    def do_GET(self):
        self._forward("GET")

    def do_PUT(self):
        self._forward("PUT")

    def do_POST(self):
        self._forward("POST")

    def do_DELETE(self):
        self._forward("DELETE")

    def log_message(self, fmt, *args):
        print(f"{self.command} {self.path} -> {args[1] if len(args) > 1 else ''}", flush=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print(f"a1-osc-adapter: :{port} -> {UPSTREAM}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
