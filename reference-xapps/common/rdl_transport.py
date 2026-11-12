# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
Entrega das propostas das xApps de referência à xApp RDL.

- ``rmr`` (padrão quando o ``ricxappframe`` está instalado): envia ``RDL_ACTION_PROPOSAL`` (RMR 30000) e
  recebe ``RDL_ACTION_RESULT`` (30001: motivo da recusa e ``retry_after_ms``), filtrando pelo próprio
  ``xapp_id``. As rotas vêm do RtMgr ou de ``RMR_SEED_RT`` (``deploy/helm/ric-governance``).
- ``http``: POST para ``RDL_HTTP_URL``. A RDL **não** recebe propostas por HTTP; o modo existe só para
  um coletor externo de testes.
- ``none``: só registra localmente (testes).

``RDL_TRANSPORT`` escolhe o modo (``auto`` = ``rmr`` se possível, senão ``none``).
"""

import json
import logging
import os
import threading
from collections import deque
from typing import Any, Callable, Deque, Dict, Optional

RDL_ACTION_PROPOSAL = 30000
RDL_ACTION_RESULT = 30001

logger = logging.getLogger("rdl_transport")


class RdlTransport:
    def __init__(self, xapp_id: str, rmr_port: int = 4560, mode: Optional[str] = None):
        self.xapp_id = xapp_id
        self.rmr_port = int(rmr_port)
        self.mode = (mode or os.getenv("RDL_TRANSPORT", "auto")).lower()
        self.http_url = os.getenv("RDL_HTTP_URL", "")
        self.results: Deque[Dict[str, Any]] = deque(maxlen=200)
        self.sent = 0
        self.failed = 0
        self.on_result: Optional[Callable[[Dict[str, Any]], None]] = None
        self._rmr = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ ciclo de vida
    def start(self) -> str:
        """Abre o transporte; devolve o modo efetivo."""
        if self.mode in ("auto", "rmr"):
            try:
                from ricxappframe.xapp_frame import RMRXapp
                self._rmr = RMRXapp(self._default_handler, rmr_port=self.rmr_port,
                                    rmr_wait_for_ready=False, use_fake_sdl=True)
                self._rmr.register_callback(self._result_handler, RDL_ACTION_RESULT)
                self._rmr.run(thread=True)
                self.mode = "rmr"
            except Exception as exc:
                if self.mode == "rmr":
                    raise RuntimeError(f"RMR indisponível para {self.xapp_id}: {exc}") from exc
                logger.warning("ricxappframe/RMR indisponível; propostas só registradas localmente (%s)", exc)
                self.mode = "none"
        return self.mode

    def stop(self) -> None:
        if self._rmr is not None:
            try:
                self._rmr.stop()
            except Exception:
                pass

    # ------------------------------------------------------------------ envio e resultado
    def send(self, proposal: Dict[str, Any]) -> bool:
        payload = json.dumps(proposal).encode("utf-8")
        ok = False
        if self.mode == "rmr" and self._rmr is not None:
            ok = bool(self._rmr.rmr_send(payload, RDL_ACTION_PROPOSAL))
        elif self.mode == "http" and self.http_url:
            try:
                import urllib.request
                req = urllib.request.Request(self.http_url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=1.0):
                    ok = True
            except Exception as exc:
                logger.debug("Falha no POST para %s: %s", self.http_url, exc)
        with self._lock:
            if ok:
                self.sent += 1
            else:
                self.failed += 1
        return ok

    def handle_result(self, payload: bytes) -> Optional[Dict[str, Any]]:
        """Trata um RDL_ACTION_RESULT; ignora os de outras xApps."""
        try:
            result = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            return None
        if not isinstance(result, dict) or result.get("xapp_id") != self.xapp_id:
            return None
        self.results.append(result)
        logger.info("Proposta %s recusada pela RDL: %s (retry_after_ms=%s, deferred=%s)",
                    result.get("action_id"), result.get("reason"), result.get("retry_after_ms"), result.get("deferred"))
        if self.on_result is not None:
            self.on_result(result)
        return result

    def _result_handler(self, rmr_xapp, summary, sbuf):
        try:
            self.handle_result(summary.get("payload") or b"")
        finally:
            rmr_xapp.rmr_free(sbuf)

    @staticmethod
    def _default_handler(rmr_xapp, summary, sbuf):
        rmr_xapp.rmr_free(sbuf)

    def stats(self) -> Dict[str, Any]:
        return {"mode": self.mode, "sent": self.sent, "failed": self.failed,
                "last_results": list(self.results)[-10:]}


def transport_for(xapp_id: str, rmr_port: int) -> RdlTransport:
    return RdlTransport(xapp_id, rmr_port=rmr_port)
