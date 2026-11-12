# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
Base comum das xApps do GreenRAN: amostra KPM normalizada por célula e fatia, perfil sazonal de carga,
política A1 da própria xApp e envio das propostas à RDL.

Entrada de KPM:
- ``normalize_kpm``: converte uma Indication KPM v3 decodificada (formato do ``src/e2/v3/codec.py``:
  ``{"node": {...}}`` ou ``{"ues": [...]}``) numa ``CellSample``. Os nomes das métricas vêm do perfil do
  backend (NORI, srsRAN ou OAI; ``src/e2/backends/testbed_profiles.py``).
- ``RicKpmSource``: subscrição E2SM-KPM pelo SubMgr do O-RAN SC e decodificação das Indications que
  chegam pelo RMR (12050). Escrito para o testbed; **não verificado** com RAN real.
"""

import json
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.interfaces.a1_policy_receiver import A1PolicyManager
from src.interfaces.a1_rmr import A1_POLICY_REQUEST, A1_POLICY_RESPONSE, handle_policy_request

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "reference-xapps" / "common") not in sys.path:
    sys.path.insert(0, str(_ROOT / "reference-xapps" / "common"))
from rdl_transport import RdlTransport  # noqa: E402  RMR 30000 / 30001

RIC_INDICATION = 12050

# Nomes das métricas KPM no NORI (ns-3 + 5G-LENA); srsRAN e OAI sobrepõem pelo perfil do backend
DEFAULT_METRICS = {
    "prb_used": "RRU.PrbUsedDl", "prb_avail": "RRU.PrbAvailDl", "ue_thp_kbps": "DRB.UEThpDl",
    "ue_delay_ms": "DRB.RlcSduDelayDl", "ue_sst": "DRB.NetworkSlicing.SST", "ue_prb": "RRU.PrbUsedDl",
}


@dataclass
class SliceKpi:
    thp_mbps: float = 0.0
    delay_ms: Optional[float] = None
    prb_used: float = 0.0
    ues: int = 0


@dataclass
class CellSample:
    cell_id: str
    t: float
    load_pct: Optional[float] = None          # PRBs em uso / disponíveis, em %
    slices: Dict[int, SliceKpi] = field(default_factory=dict)

    @property
    def total_ues(self) -> int:
        return sum(s.ues for s in self.slices.values())


def normalize_kpm(cell_id: str, kpm: Dict[str, Any], t: Optional[float] = None,
                  metrics: Optional[Dict[str, str]] = None, previous: Optional[CellSample] = None) -> CellSample:
    """Funde uma Indication (formato 1 de nó ou 3 de UEs) na amostra da célula."""
    m = {**DEFAULT_METRICS, **(metrics or {})}
    sample = CellSample(cell_id, t if t is not None else time.time(),
                        load_pct=previous.load_pct if previous else None,
                        slices=dict(previous.slices) if previous else {})
    node = kpm.get("node")
    if node:
        used, avail = node.get(m["prb_used"]), node.get(m["prb_avail"])
        if isinstance(used, (int, float)) and isinstance(avail, (int, float)) and avail > 0:
            # PrbAvail no NORI é o número de PRBs livres; uso = usados / (usados + livres)
            sample.load_pct = round(100.0 * used / (used + avail), 2)
    ues = kpm.get("ues")
    if ues is not None:
        slices: Dict[int, SliceKpi] = {}
        for ue in ues:
            meas = ue.get("measurements") or {}
            sst = int(meas.get(m["ue_sst"]) or 1)
            s = slices.setdefault(sst, SliceKpi())
            s.ues += 1
            s.thp_mbps += float(meas.get(m["ue_thp_kbps"]) or 0.0) / 1000.0
            s.prb_used += float(meas.get(m["ue_prb"]) or 0.0)
            d = meas.get(m["ue_delay_ms"])
            if isinstance(d, (int, float)):
                s.delay_ms = max(s.delay_ms or 0.0, float(d))
        sample.slices = slices
    return sample


class SeasonalProfile:
    """Carga esperada por hora do dia (24 faixas), média móvel exponencial por chave (célula)."""

    def __init__(self, alpha: float = 0.2):
        self.alpha = alpha
        self.bins: Dict[str, List[Optional[float]]] = {}

    def update(self, key: str, hour: int, value: float) -> None:
        b = self.bins.setdefault(key, [None] * 24)
        old = b[hour % 24]
        b[hour % 24] = value if old is None else (1 - self.alpha) * old + self.alpha * value

    def expected(self, key: str, hour: int, default: Optional[float] = None) -> Optional[float]:
        b = self.bins.get(key)
        return default if b is None or b[hour % 24] is None else b[hour % 24]

    def to_dict(self) -> Dict[str, List[Optional[float]]]:
        return {k: list(v) for k, v in self.bins.items()}


class GreenRanXApp:
    """Ciclo comum: observar KPM, ler a política A1 do próprio tipo, propor à RDL a cada período."""

    XAPP_ID = "greenran"
    A1_TYPE = ""
    DEFAULTS: Dict[str, Any] = {}

    def __init__(self, transport: Optional[RdlTransport] = None, period_s: float = 1.0,
                 clock: Callable[[], float] = time.time, rmr_port: int = 4560):
        self.transport = transport or RdlTransport(self.XAPP_ID, rmr_port=rmr_port)
        self.transport.on_result = self.on_result
        self.a1 = A1PolicyManager()
        self.period_s = period_s
        self.clock = clock
        self.samples: Dict[str, CellSample] = {}
        self.sent: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self.running = False
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------ política A1 do próprio tipo
    def policy(self) -> Dict[str, Any]:
        merged = dict(self.DEFAULTS)
        for key, body in self.a1.active_policies.items():
            if key.startswith(f"{self.A1_TYPE}:"):
                merged.update(body)
        return merged

    def handle_a1(self, payload: bytes) -> Dict[str, Any]:
        response, _ = handle_policy_request(self.a1, payload, handler_id=self.XAPP_ID)
        return response

    # ------------------------------------------------------------------ entrada e saída
    def observe(self, sample: CellSample) -> None:
        self.samples[sample.cell_id] = sample

    def observe_kpm(self, cell_id: str, kpm: Dict[str, Any], metrics: Optional[Dict[str, str]] = None) -> CellSample:
        sample = normalize_kpm(cell_id, kpm, self.clock(), metrics, self.samples.get(cell_id))
        self.observe(sample)
        return sample

    def decide(self, now: float) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def on_result(self, result: Dict[str, Any]) -> None:
        self.results.append(result)

    def step(self, now: Optional[float] = None) -> List[Dict[str, Any]]:
        proposals = self.decide(self.clock() if now is None else now)
        for p in proposals:
            self.transport.send(p)
            self.sent.append(p)
        return proposals

    # ------------------------------------------------------------------ execução
    def start(self) -> None:
        mode = self.transport.start()
        rmr = getattr(self.transport, "_rmr", None)
        if mode == "rmr" and rmr is not None:
            def a1_handler(rmr_xapp, summary, sbuf):
                try:
                    body = json.dumps(self.handle_a1(summary.get("payload") or b"")).encode()
                    rmr_xapp.rmr_send(body, A1_POLICY_RESPONSE)
                finally:
                    rmr_xapp.rmr_free(sbuf)
            rmr.register_callback(a1_handler, A1_POLICY_REQUEST)
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while self.running:
            self.step()
            time.sleep(self.period_s)

    def stop(self) -> None:
        self.running = False
        self.transport.stop()

    def status(self) -> Dict[str, Any]:
        return {"xapp_id": self.XAPP_ID, "policy": self.policy(), "cells": sorted(self.samples),
                "sent": len(self.sent), "rejections": len(self.results), "transport": self.transport.stats()}


class RicKpmSource:
    """Subscrição E2SM-KPM pelo SubMgr e decodificação das Indications que chegam à xApp (12050).

    Não verificado com RAN real: segue o mesmo caminho da kpm-probe (SubMgr REST + codec v3)."""

    def __init__(self, xapp: GreenRanXApp, submgr_url: str, nodes: List[str], ran_function_id: int,
                 period_ms: int = 1000, metrics: Optional[Dict[str, str]] = None):
        from src.infrastructure.subscription_manager import SubscriptionManager
        from src.e2.v3 import codec as v3
        self.xapp, self.nodes, self.ran_function_id, self.period_ms = xapp, nodes, ran_function_id, period_ms
        self.metrics = metrics
        self.submgr = SubscriptionManager(submgr_url=submgr_url)
        self.v3 = v3
        self.codec = v3.E2smCodec(download=os.getenv("XAPP_RDL_ASN1_DOWNLOAD", "false").lower() == "true")

    def subscribe(self) -> int:
        ok = 0
        for node in self.nodes:
            if self.submgr.request_kpm_subscription(meid=node, ran_function_id=self.ran_function_id,
                                                    period_ms=self.period_ms):
                ok += 1
        return ok

    def on_indication(self, rmr_xapp, summary, sbuf) -> None:
        try:
            meid = summary.get("meid") or "unknown"
            meid = meid.decode() if isinstance(meid, bytes) else meid
            pdu = self.v3.decode_e2ap_pdu(summary.get("payload") or b"")
            kpm = self.codec.kpm_decode_indication(pdu["indication_header"], pdu["indication_message"])
            self.xapp.observe_kpm(meid, kpm, self.metrics)
        except Exception:
            pass
        finally:
            rmr_xapp.rmr_free(sbuf)

    def attach(self) -> bool:
        rmr = getattr(self.xapp.transport, "_rmr", None)
        if rmr is None:
            return False
        rmr.register_callback(self.on_indication, RIC_INDICATION)
        return True


def load_neighbors(path: Optional[str] = None) -> Dict[str, List[str]]:
    """Vizinhança das células (mesmo formato de ``RDL_TOPOLOGY_FILE``)."""
    path = path or os.getenv("RDL_TOPOLOGY_FILE", "")
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out: Dict[str, List[str]] = {}
    for a, bs in (data.get("neighbors") or {}).items():
        for b in bs:
            out.setdefault(a, []).append(b)
            out.setdefault(b, []).append(a)
    return {k: sorted(set(v)) for k, v in out.items()}
