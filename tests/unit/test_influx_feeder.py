"""
Testes do alimentador do InfluxDB (scripts/observe/influx_feeder.py): line protocol, vazão a partir dos contadores
acumulados do FlowMonitor, conversão dos eventos da xApp e pontos de campanha a partir da evidência.
"""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("influx_feeder", ROOT / "scripts" / "observe" / "influx_feeder.py")
fd = importlib.util.module_from_spec(SPEC)
sys.modules["influx_feeder"] = fd
SPEC.loader.exec_module(fd)


def test_line_protocol_escapes_and_types():
    ln = fd.line("m x", {"run": "a b", "z": None, "k": "v,1"}, {"f": 1.5, "i": 3, "s": 'say "hi"', "n": None, "b": True}, 10)
    assert ln == 'm\\ x,k=v\\,1,run=a\\ b f=1.5,i=3i,s="say \\"hi\\"",b=true 10'
    assert fd.line("m", {}, {"n": None}, 1) is None


def test_run_tags():
    assert fd.run_tags("nori_S8_B0_pairfix_seed9101") == {"run": "nori_S8_B0_pairfix_seed9101", "scenario": "S8",
                                                          "baseline": "B0", "condition": "pairfix", "seed": "9101"}
    assert fd.run_tags("nori_S1_B3_seed1001")["condition"] == "padrao"
    assert fd.run_tags("nori_rc_demo_seed1") == {"run": "nori_rc_demo_seed1"}


def test_slice_points_compute_throughput_and_do_not_repeat():
    csv = ("sim_time_s,wall_epoch_s,ue_index,sst,tx_packets,rx_packets,rx_bytes,delay_sum_s\n"
           "1.0,1000.0,0,1,10,10,0,0.0\n"
           "1.5,1001.5,0,1,20,20,9468000,0.03\n"     # 9,468 MB em 0,5 s = 151,488 Mb/s; atraso 3 ms
           "1.0,1000.0,1,2,10,10,0,0.0\n")
    sent = {}
    pts = fd.slice_points("nori_S8_B3_seed5001", csv, sent)
    assert len(pts) == 1
    assert pts[0].startswith("nori_slice,baseline=B3,condition=padrao,run=nori_S8_B3_seed5001,scenario=S8,seed=5001,"
                             "slice=eMBB,sst=1,ue=0 throughput_mbps=151.488,delay_ms=3.0,sim_time_s=1.5 1001500000000")
    assert fd.slice_points("nori_S8_B3_seed5001", csv, sent) == []   # já enviado


def test_event_points():
    ctx = fd.run_tags("nori_S8_B0_seed5001")
    ctl = {"t_utc": "2026-11-09T12:00:00.500Z", "event": "control_request", "decision_source": "BASELINE_B0", "rmr_ok": True,
           "quotas": [{"sst": 1, "max_prb_ratio": 25}, {"sst": 2, "max_prb_ratio": 75}], "ric_instance_id": 7,
           "control_order": 2, "decision": {"kpm_pair_gap_ms": 3.9}, "trigger_kpm_seq": 12}
    [p] = fd.event_points(ctl, ctx)
    assert p.startswith("xapp_control,baseline=B0,condition=padrao,rmr_ok=True,run=nori_S8_B0_seed5001,scenario=S8,source=BASELINE_B0 ")
    assert "embb_cap_pct=25i" in p and "urllc_cap_pct=75i" in p and "order=2i" in p and "pair_gap_ms=3.9" in p
    assert p.endswith(" 1794225600500000000")
    kpm = {"t_utc": "2026-11-09T12:00:00Z", "event": "kpm", "format": 3,
           "ues": [{"ue_id": 1, "DRB.NetworkSlicing.SST": 1, "RRU.PrbUsedDl": 119}, {"ue_id": 2, "DRB.NetworkSlicing.SST": 2,
                                                                                      "RRU.PrbUsedDl": 119},
                   {"ue_id": 3, "DRB.NetworkSlicing.SST": 1}]}           # UE sem métrica: sem ponto
    assert len(fd.event_points(kpm, ctx)) == 2
    ack = {"t_utc": "2026-11-09T12:00:01Z", "event": "control_outcome", "outcome": "ACK", "latency_ms": 2.1,
           "correlated_with_request": True}
    assert "correlated=1i" in fd.event_points(ack, ctx)[0]
    assert fd.event_points({"event": "start", "t_utc": "2026-11-09T12:00:00Z"}, ctx) == []


def test_campaign_points_from_evidence(tmp_path):
    run = "nori_S8_B2_seed5001"
    (tmp_path / "experiments" / "runs" / run).mkdir(parents=True)
    (tmp_path / "experiments" / "runs" / run / "execution_manifest.json").write_text(
        json.dumps({"started_at_utc": "2026-11-09T07:10:00Z"}), encoding="utf-8")
    d = tmp_path / "experiments" / "e2_dissection" / run
    d.mkdir(parents=True)
    (d / "slice_effect_v6.json").write_text(json.dumps({"rule": "v6-ratio-apply", "verdict": "CONSISTENT", "slices": {
        "1": {"throughput_before_mbps": 151.488, "throughput_after_mbps": 95.24, "cap_max_prb_pct": 25.0},
        "2": {"throughput_before_mbps": 151.488, "throughput_after_mbps": 151.488, "cap_max_prb_pct": 75.0}}}), encoding="utf-8")
    (d / "e2_messages.json").write_text(json.dumps({"message_count": 88, "xapp_crosscheck": {"decision": {
        "source": "BASELINE_B2", "trigger_is_kpm_t0": True}}}), encoding="utf-8")
    done = set()
    [p] = fd.campaign_points(tmp_path, done)
    assert "rule=v6-ratio-apply" in p and "verdict=CONSISTENT" in p and "source=BASELINE_B2" in p
    assert "verdict_code=1i" in p and "embb_after_mbps=95.24" in p and "trigger_is_kpm_t0=1i" in p
    assert fd.campaign_points(tmp_path, done) == []     # não repete
