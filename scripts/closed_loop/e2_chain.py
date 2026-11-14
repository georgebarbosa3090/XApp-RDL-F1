#!/usr/bin/env python3
# Autor: George Barbosa
"""
Ciclo da cadeia E2 na malha fechada, igual ao da bancada NORI S8 (docs/16 §10.1, opção A do híbrido).

O transporte continua sendo o socket Unix em passo travado com o ns-3.48; este módulo executa e registra as
mesmas etapas do NORI, na mesma ordem, em ``raw/e2_chain.jsonl``:

1. ``e2_setup``: um E2SetupRequest/Response por gNB do HELLO, com as RAN Functions KPM (2) e RC (3);
2. ``subscription``: cada xApp assina o KPM de cada nó (período = janela de decisão), com RICrequestID próprio;
3. ``indication`` (``kpm_t0``): uma Indication por nó a cada janela, numerada;
4. ``decision``: a RDLDecision com o identificador de correlação, gravada antes do despacho;
5. ``control_request``: uma RIC Control Request por ação, com cabeçalho e mensagem E2SM-RC e a PDU E2AP
   codificados pelo codec da RDL (hex e sha256 dos bytes; decodificada de volta antes de ir ao ns-3). Ação que
   o codec não consegue codificar (fora da faixa do perfil RC) não é despachada: vira ``control_failure``;
6. ``control_ack`` / ``control_failure`` / ``control_timeout``: o resultado que o ns-3 devolve por controle
   (APPLIED e NO_EFFECT -> ACK; REJECTED_* e UNSUPPORTED -> Failure); sem resultado em ``timeout_s`` simulados
   -> timeout. RICrequestID duplicado com controle pendente é recusado;
7. ``kpm_t1``: a primeira Indication do nó em que o estado aplicado aparece no KPM (ou o fim do prazo), com
   a verificação do efeito por parâmetro.

Os bytes são do codec local (src/e2), que não foi validado contra o ASN.1 oficial: provam autoconsistência,
não interoperabilidade (a mesma ressalva do NORI).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, IO, List, Optional, Tuple

RAN_FUNCTION_KPM, RAN_FUNCTION_RC = 2, 3
RDL_REQUESTOR_ID = 1
RC_PARAMETERS = ("PRB_QUOTA", "TX_POWER", "HANDOVER", "CELL_STATE")
ACK_STATUSES = {"APPLIED", "NO_EFFECT"}
CHAIN_ROLES = ("e2_setup", "subscription", "kpm_t0", "control_request", "control_ack", "kpm_t1")


def _hex(b: bytes) -> Dict[str, Any]:
    return {"len": len(b), "sha256": hashlib.sha256(b).hexdigest(), "hex": b.hex()}


def node_of(gnb: int) -> str:
    return f"gnb_{int(gnb)}"


class E2Chain:
    """Executa e registra o ciclo E2 por janela. Uma instância por execução."""

    def __init__(self, out: IO[str], window_s: float, timeout_s: float = 5.0, encode: bool = True):
        self.out, self.window_s, self.timeout_s, self.encode = out, window_s, timeout_s, encode
        self.nodes: Dict[int, int] = {}                 # gnb -> cell_id
        self.subs: Dict[Tuple[str, str], Dict[str, int]] = {}
        self.ind_seq: Dict[str, int] = {}
        self.instance = 0
        self.pending: Dict[str, Dict[str, Any]] = {}    # id da ação -> controle aguardando resultado
        self.awaiting_t1: Dict[str, Dict[str, Any]] = {}  # id da ação -> ACK aguardando o estado no KPM
        self.counts: Dict[str, int] = {}
        self._rc = None

    # ------------------------------------------------------------------ registro
    def _emit(self, role: str, t: float, **fields: Any) -> Dict[str, Any]:
        rec = {"role": role, "t": round(float(t), 3), **fields}
        self.counts[role] = self.counts.get(role, 0) + 1
        self.out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    @property
    def rc(self):
        if self._rc is None:
            from src.e2.rc_encoder import RCEncoder
            self._rc = RCEncoder()
        return self._rc

    # ------------------------------------------------------------------ 1–3: setup, subscrição, indication
    def setup(self, hello: Dict[str, Any]) -> None:
        for g in hello.get("gnbs", []):
            gnb, cell = int(g["gnb"]), int(g["cell_id"])
            self.nodes[gnb] = cell
            funcs = [{"ran_function_id": RAN_FUNCTION_KPM, "oid": "E2SM-KPM", "styles": [1, 4]},
                     {"ran_function_id": RAN_FUNCTION_RC, "oid": "E2SM-RC", "control_parameters": list(RC_PARAMETERS)}]
            self._emit("e2_setup_request", 0.0, node=node_of(gnb), cell_id=cell, ran_functions=funcs)
            self._emit("e2_setup", 0.0, node=node_of(gnb), cell_id=cell, accepted=[f["ran_function_id"] for f in funcs])

    def subscribe(self, xapps: List[str]) -> None:
        for k, xapp in enumerate(xapps):
            for gnb in sorted(self.nodes):
                self.instance += 1
                rid = {"ricRequestorID": 100 + k, "ricInstanceID": self.instance}
                self.subs[(xapp, node_of(gnb))] = rid
                self._emit("subscription_request", 0.0, xapp=xapp, node=node_of(gnb), ric_request_id=rid,
                           ran_function_id=RAN_FUNCTION_KPM, period_ms=int(round(self.window_s * 1000)))
                self._emit("subscription", 0.0, xapp=xapp, node=node_of(gnb), ric_request_id=rid, admitted=True)

    def indication(self, kpm: Dict[str, Any]) -> None:
        t = float(kpm["t"])
        for c in kpm.get("cells", []):
            node = node_of(c["gnb"])
            self.ind_seq[node] = self.ind_seq.get(node, 0) + 1
            subscribers = sorted(x for (x, n) in self.subs if n == node)
            self._emit("kpm_t0", t, node=node, seq=self.ind_seq[node], subscribers=subscribers,
                       n_ues=c.get("n_ues"), prb_util=c.get("prb_util"), thp_mbps=c.get("thp_mbps"))
        self._resolve_outcomes(kpm.get("control_outcomes") or [], t)
        self._check_t1(kpm, t)
        self._check_timeouts(t)

    # ------------------------------------------------------------------ 4–5: decisão e Control Request
    def dispatch(self, t: float, actions: List[Dict[str, Any]], decision: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Grava a decisão e uma Control Request por ação. Devolve só as ações codificadas (a despachar)."""
        self._emit("decision", t, rule=(decision or {}).get("rule"), selected=[a["id"] for a in actions],
                   correlation=[{"action_id": a["id"], "xapp_id": a["xapp_id"], "node": node_of(a["gnb"]),
                                 "parameter": a["parameter"], "value": a["value"], "ue": a.get("ue", -1)}
                                for a in actions])
        out = []
        for a in actions:
            if a["id"] in self.pending:
                self._emit("control_rejected_duplicate", t, action_id=a["id"])
                continue
            self.instance += 1
            rid = {"ricRequestorID": RDL_REQUESTOR_ID, "ricInstanceID": self.instance}
            rec = {"action_id": a["id"], "node": node_of(a["gnb"]), "parameter": a["parameter"], "value": a["value"],
                   "ue": a.get("ue", -1), "ric_request_id": rid, "ran_function_id": RAN_FUNCTION_RC}
            if self.encode:
                try:
                    rec.update(self._encode(a, rid))
                except (ValueError, KeyError) as exc:
                    self._emit("control_failure", t, cause="codec", detail=str(exc), dispatched=False, **rec)
                    continue
            self._emit("control_request", t, **rec)
            self.pending[a["id"]] = dict(rec, t_sent=t)
            out.append(a)
        return out

    def _encode(self, a: Dict[str, Any], rid: Dict[str, int]) -> Dict[str, Any]:
        from src.e2.e2ap.control import build_ric_control_request
        header, message = self.rc.encode_control_pdu(node_of(a["gnb"]), a["parameter"], float(a["value"]))
        ctx = build_ric_control_request(node_of(a["gnb"]), RAN_FUNCTION_RC, header, message,
                                        requestor_id=rid["ricRequestorID"], instance_id=rid["ricInstanceID"])
        decoded = self.rc.decode_control_request(message, a["parameter"])
        if abs(decoded - float(a["value"])) > 0.051:
            raise ValueError(f"ida e volta do codec divergiu: {a['value']} -> {decoded}")
        return {"e2sm_rc_header": _hex(header), "e2sm_rc_message": _hex(message), "e2ap_pdu": _hex(ctx.pdu_aper),
                "decoded_value": decoded}

    # ------------------------------------------------------------------ 6: ACK / Failure / timeout
    def _resolve_outcomes(self, outcomes: List[Dict[str, Any]], t: float) -> None:
        from src.e2.e2ap.control import RICcontrolAcknowledge, RICcontrolFailure
        from src.e2.e2ap.constants import PROC_RIC_CONTROL
        from src.e2.e2ap.pdu import wrap_successful_outcome, wrap_unsuccessful_outcome
        for o in outcomes:
            ctl = self.pending.pop(str(o.get("id")), None)
            if ctl is None:
                self._emit("control_outcome_unmatched", t, action_id=o.get("id"), status=o.get("status"))
                continue
            status = str(o.get("status"))
            base = {"action_id": ctl["action_id"], "node": ctl["node"], "parameter": ctl["parameter"],
                    "ric_request_id": ctl["ric_request_id"], "status": status, "detail": o.get("detail", ""),
                    "control_latency_s": round(t - ctl["t_sent"], 3)}
            if status in ACK_STATUSES:
                if self.encode:
                    ack = RICcontrolAcknowledge()
                    ack.set_val({"ricRequestID": ctl["ric_request_id"], "ranFunctionID": RAN_FUNCTION_RC})
                    base["e2ap_pdu"] = _hex(wrap_successful_outcome(PROC_RIC_CONTROL, ack.to_aper()))
                self._emit("control_ack", t, **base)
                if status == "APPLIED":
                    self.awaiting_t1[ctl["action_id"]] = dict(ctl, t_ack=t)
            else:
                if self.encode:
                    fail = RICcontrolFailure()
                    fail.set_val({"ricRequestID": ctl["ric_request_id"], "ranFunctionID": RAN_FUNCTION_RC})
                    base["e2ap_pdu"] = _hex(wrap_unsuccessful_outcome(PROC_RIC_CONTROL, fail.to_aper()))
                self._emit("control_failure", t, cause="ran", dispatched=True, **base)

    def _check_timeouts(self, t: float) -> None:
        for aid, ctl in list(self.pending.items()):
            if t - ctl["t_sent"] > self.timeout_s:
                del self.pending[aid]
                self._emit("control_timeout", t, action_id=aid, node=ctl["node"], parameter=ctl["parameter"],
                           ric_request_id=ctl["ric_request_id"])

    # ------------------------------------------------------------------ 7: KPM_t1 e efeito
    def _state(self, kpm: Dict[str, Any], ctl: Dict[str, Any]) -> Tuple[Optional[float], bool]:
        gnb = int(ctl["node"].split("_")[1])
        cell = next((c for c in kpm.get("cells", []) if int(c["gnb"]) == gnb), {})
        p, v = ctl["parameter"], float(ctl["value"])
        if p == "TX_POWER":
            obs = cell.get("tx_power_dbm")
            return obs, obs is not None and abs(float(obs) - v) <= 0.1
        if p == "CELL_STATE":
            obs = cell.get("sleeping")
            return obs, obs is not None and bool(obs) == (v == 0)
        if p == "PRB_QUOTA":
            obs = cell.get("prb_quota")
            return obs, obs is not None and abs(float(obs) - v) <= 1.0
        if p == "HANDOVER":
            target = self.nodes.get(int(v))
            ues = [u for u in kpm.get("ues", []) if ctl.get("ue", -1) in (-1, u.get("ue"))]
            if ctl.get("ue", -1) >= 0:
                obs = next((u.get("cell_id") for u in ues), None)
                return obs, obs is not None and obs == target
            obs = sum(1 for u in ues if u.get("cell_id") == target)
            return obs, obs > 0
        return None, False

    def _check_t1(self, kpm: Dict[str, Any], t: float) -> None:
        for aid, ctl in list(self.awaiting_t1.items()):
            if t <= ctl["t_ack"] - 1e-9:
                continue
            observed, ok = self._state(kpm, ctl)
            late = t - ctl["t_ack"] > self.timeout_s
            if ok or late:
                del self.awaiting_t1[aid]
                self._emit("kpm_t1", t, action_id=aid, node=ctl["node"], parameter=ctl["parameter"],
                           expected=ctl["value"], observed=observed, effect_ok=ok,
                           effect_latency_s=round(t - ctl["t_sent"], 3))

    # ------------------------------------------------------------------ encerramento
    def close(self, t_end: float) -> Dict[str, Any]:
        for aid, ctl in list(self.pending.items()):
            self._emit("control_timeout", t_end, action_id=aid, node=ctl["node"], parameter=ctl["parameter"],
                       ric_request_id=ctl["ric_request_id"], at_end=True)
        self.pending.clear()
        for aid, ctl in list(self.awaiting_t1.items()):
            self._emit("kpm_t1", t_end, action_id=aid, node=ctl["node"], parameter=ctl["parameter"],
                       expected=ctl["value"], observed=None, effect_ok=False, at_end=True)
        self.awaiting_t1.clear()
        summary = {r: self.counts.get(r, 0) for r in CHAIN_ROLES}
        summary.update({k: self.counts.get(k, 0) for k in ("control_failure", "control_timeout", "decision")})
        self._emit("chain_summary", t_end, counts=summary)
        return summary
