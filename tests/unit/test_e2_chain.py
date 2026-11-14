"""Ciclo da cadeia E2 na malha fechada (docs/16 §10.1): etapas, desfechos, KPM_t1 e verificador."""
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.closed_loop.e2_chain import E2Chain  # noqa: E402
from scripts.closed_loop.verificar_cadeia import verify  # noqa: E402

HELLO = {"gnbs": [{"gnb": 0, "cell_id": 1}, {"gnb": 1, "cell_id": 2}]}


def kpm(t, tx=(43.0, 43.0), sleeping=(False, False), quota=(None, None), ue_cell=1, outcomes=()):
    return {"t": t, "cells": [{"gnb": g, "cell_id": g + 1, "tx_power_dbm": tx[g], "sleeping": sleeping[g],
                               "prb_quota": quota[g], "n_ues": 1, "prb_util": 0.1, "thp_mbps": 1.0} for g in (0, 1)],
            "ues": [{"ue": 0, "cell_id": ue_cell, "gnb": ue_cell - 1}], "control_outcomes": list(outcomes)}


def act(i, gnb, p, v, ue=-1):
    return {"id": f"a{i}", "xapp_id": "x", "gnb": gnb, "parameter": p, "value": v, "ue": ue}


def run_chain():
    buf = io.StringIO()
    ch = E2Chain(buf, window_s=0.2, timeout_s=1.0)
    ch.setup(HELLO)
    ch.subscribe(["energysaver_greenran", "traffic_steering"])
    ch.indication(kpm(0.2))
    sent = ch.dispatch(0.2, [act(1, 0, "TX_POWER", 30.0), act(2, 1, "TX_POWER", 45.0),   # 45 dBm: fora do perfil RC
                             act(3, 0, "HANDOVER", 1, ue=0), act(4, 1, "CELL_STATE", 0)], {"rule": "tvs"})
    ch.indication(kpm(0.4, tx=(30.0, 43.0), ue_cell=1, outcomes=[
        {"id": "a1", "status": "APPLIED"}, {"id": "a3", "status": "APPLIED"},
        {"id": "a4", "status": "REJECTED_BY_TOPOLOGY", "detail": "x"}]))
    ch.indication(kpm(0.6, tx=(30.0, 43.0), ue_cell=2))                 # o handover aparece uma janela depois
    ch.close(0.6)
    return buf.getvalue(), sent


def test_chain_follows_nori_cycle_and_codec_bounds():
    text, sent = run_chain()
    recs = [json.loads(line) for line in text.splitlines()]
    roles = [r["role"] for r in recs]
    assert roles.count("e2_setup") == 2 and roles.count("subscription") == 4 and roles.count("kpm_t0") == 6
    assert [a["id"] for a in sent] == ["a1", "a3", "a4"]                # a2 não é despachada
    fail_codec = next(r for r in recs if r["role"] == "control_failure" and r["cause"] == "codec")
    assert fail_codec["action_id"] == "a2" and fail_codec["dispatched"] is False
    req = next(r for r in recs if r["role"] == "control_request" and r["action_id"] == "a1")
    assert req["ran_function_id"] == 3 and req["decoded_value"] == 30.0 and len(req["e2ap_pdu"]["sha256"]) == 64
    assert roles.index("decision") < roles.index("control_request")    # decisão gravada antes do despacho
    acks = {r["action_id"]: r for r in recs if r["role"] == "control_ack"}
    assert set(acks) == {"a1", "a3"} and "e2ap_pdu" in acks["a1"]
    assert next(r for r in recs if r["role"] == "control_failure" and r["cause"] == "ran")["action_id"] == "a4"
    t1 = {r["action_id"]: r for r in recs if r["role"] == "kpm_t1"}
    assert t1["a1"]["effect_ok"] and t1["a1"]["t"] == 0.4
    assert t1["a3"]["effect_ok"] and t1["a3"]["t"] == 0.6                # estado do handover na janela seguinte
    assert recs[-1]["role"] == "chain_summary" and recs[-1]["counts"]["control_request"] == 3


def test_timeout_and_duplicate_request():
    buf = io.StringIO()
    ch = E2Chain(buf, window_s=0.2, timeout_s=0.5, encode=False)
    ch.setup(HELLO)
    ch.dispatch(0.2, [act(1, 0, "PRB_QUOTA", 50)], {})
    assert ch.dispatch(0.4, [act(1, 0, "PRB_QUOTA", 50)], {}) == []      # mesmo id pendente: recusado
    for t in (0.4, 0.6, 0.8):
        ch.indication(kpm(t))
    roles = [json.loads(line)["role"] for line in buf.getvalue().splitlines()]
    assert "control_rejected_duplicate" in roles and roles.count("control_timeout") == 1


def test_verifier_passes_complete_chain_and_fails_closed(tmp_path):
    text, _ = run_chain()
    run = tmp_path / "cl_x"
    (run / "raw").mkdir(parents=True)
    (run / "raw" / "e2_chain.jsonl").write_text(text, encoding="utf-8")
    (run / "raw" / "closed_loop_log.jsonl").write_text(
        "\n".join(json.dumps({"type": "window", "t": t}) for t in (0.2, 0.4, 0.6)) + "\n", encoding="utf-8")
    r = verify(run)
    assert r["verdict"] == "CADEIA_COMPLETA", r["reasons"]
    assert r["counts"]["control_ack"] == 2 and r["efeito_confirmado"] == 2
    lines = [line for line in text.splitlines() if '"role": "control_ack"' not in line]   # ACKs perdidos
    (run / "raw" / "e2_chain.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert verify(run)["verdict"] == "CADEIA_INCOMPLETA"
    assert verify(tmp_path / "nada")["verdict"] == "SEM_CADEIA"
