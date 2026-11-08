"""
Testes do dissecador E2AP de PCAP (scripts/certification/e2_pcap_dissect.py) e da sua
integração com o certificador (R14/R11/R12 e gate G1).

Os PCAPs sintéticos montados aqui são fixtures de teste do parser; nunca são evidência.
O único PCAP real usado é o da execução NORI da fase 1 (experiments/runs/nori_rc_demo_seed1).
"""

import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


dis = _load("e2_pcap_dissect", "scripts/certification/e2_pcap_dissect.py")
cert = _load("certify_chain", "scripts/certification/certify_chain.py")

NODE, RIC = "10.42.0.51", "10.43.143.195"
KPM_OID = b"1.3.6.1.4.1.53148.1.3.2.2"
RC_OID = b"1.3.6.1.4.1.53148.1.3.2.3"


# ---------------------------------------------------------------------------
# Codificação APER mínima (espelha o layout do E2AP v3.01 para as fixtures)
# ---------------------------------------------------------------------------

def _len(n):
    return bytes([n]) if n < 128 else struct.pack("!H", 0x8000 | n)


def _ie(ie_id, value):
    return struct.pack("!H", ie_id) + b"\x00" + _len(len(value)) + value


def _pdu(kind, code, ies):
    body = b"\x00" + struct.pack("!H", len(ies)) + b"".join(ies)
    return bytes([kind << 5, code, 0x00]) + _len(len(body)) + body


def _req(requestor, instance):
    return _ie(29, b"\x00" + struct.pack("!HH", requestor, instance))


def _fn(fid):
    return _ie(5, struct.pack("!H", fid))


def _tx(tx):
    return _ie(49, b"\x00" + bytes([tx]))


def _octets(ie_id, data):
    return _ie(ie_id, _len(len(data)) + data)


def _ran_functions_added(items):
    out = bytes([len(items) - 1])
    for fid, oid in items:
        definition = b"\xAA" * 40
        item = b"\x00" + struct.pack("!H", fid) + _len(len(definition)) + definition + struct.pack("!H", 3)
        item += b"\x00" + struct.pack("!H", len(oid) - 1) + oid
        out += struct.pack("!H", 8) + b"\x00" + _len(len(item)) + item
    return _ie(10, out)


def setup_request():
    return _pdu(0, 1, [_tx(1), _ran_functions_added([(200, KPM_OID), (300, RC_OID)])])


def setup_response():
    return _pdu(1, 1, [_tx(1)])


def closed_loop_pdus():
    """Sequência completa: Setup, Subscription KPM, KPM_t0, Control RC, ACK, KPM_t1."""
    return [
        ("up", setup_request()),
        ("down", setup_response()),
        ("down", _pdu(0, 8, [_req(1001, 1), _fn(200), _octets(30, b"\x01\x02")])),
        ("up", _pdu(1, 8, [_req(1001, 1), _fn(200)])),
        ("up", _pdu(0, 5, [_req(1001, 1), _fn(200), _octets(25, b"h0"), _octets(26, b"kpm-t0")])),
        ("down", _pdu(0, 4, [_req(2002, 7), _fn(300), _octets(22, b"ch"), _octets(23, b"prb=40")])),
        ("up", _pdu(1, 4, [_req(2002, 7), _fn(300)])),
        ("up", _pdu(0, 5, [_req(1001, 1), _fn(200), _octets(25, b"h1"), _octets(26, b"kpm-t1")])),
    ]


# ---------------------------------------------------------------------------
# PCAP (SLL / IPv4 / SCTP)
# ---------------------------------------------------------------------------

def _ip(addr):
    return bytes(int(x) for x in addr.split("."))


def _frame(src, dst, sport, dport, chunks):
    sctp = struct.pack("!HHII", sport, dport, 0x1234, 0) + b"".join(chunks)
    ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + len(sctp), 0, 0x4000, 64, 132, 0, _ip(src), _ip(dst)) + sctp
    return b"\x00\x04\x00\x01\x00\x06" + b"\x00" * 8 + b"\x08\x00" + ip


def _data_chunk(tsn, payload, begin=True, end=True, ssn=0, ppid=70):
    flags = (0x02 if begin else 0) | (0x01 if end else 0)
    body = struct.pack("!IHHI", tsn, 0, ssn, ppid) + payload
    chunk = bytes([0, flags]) + struct.pack("!H", 4 + len(body)) + body
    return chunk + b"\x00" * ((4 - len(chunk) % 4) % 4)


def _pcap(frames):
    out = struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 262144, 113)
    for i, frame in enumerate(frames):
        out += struct.pack("<IIII", 1794146159 + i, 0, len(frame), len(frame)) + frame
    return out


def _closed_loop_pcap():
    frames, tsn = [], {"up": 100, "down": 500}
    for direction, pdu in closed_loop_pdus():
        tsn[direction] += 1
        if direction == "up":
            frames.append(_frame(NODE, RIC, 38470, 36422, [_data_chunk(tsn["up"], pdu)]))
        else:
            frames.append(_frame(RIC, NODE, 36422, 38470, [_data_chunk(tsn["down"], pdu)]))
    return _pcap(frames)


# ---------------------------------------------------------------------------
# Dissecador
# ---------------------------------------------------------------------------

def test_closed_loop_chain_is_identified_in_order():
    result = dis.extract_messages(_closed_loop_pcap())
    msgs = result["messages"]
    assert not result["errors"]
    assert [m["role"] for m in msgs] == [
        "e2_setup_request", "e2_setup_response", "subscription_request", "subscription_response",
        "indication", "control_request", "control_ack", "indication"]
    assert msgs[2]["direction"] == "RIC->E2_NODE" and msgs[4]["direction"] == "E2_NODE->RIC"
    kinds = dis.ran_function_kinds(msgs)
    assert kinds == {200: "KPM", 300: "RC"}
    roles = dis.assign_chain_roles(msgs, kinds)
    assert roles == {"e2_setup": 2, "subscription": 4, "kpm_t0": 5, "control_request": 6,
                     "control_ack": 7, "kpm_t1": 8}
    assert dis.ie_value(msgs[5], dis.IE_RIC_REQUEST_ID) == {"requestor": 2002, "instance": 7}
    assert dis.ie_value(msgs[4], dis.IE_RIC_INDICATION_MESSAGE)["len"] == 6


def test_fragmented_and_retransmitted_chunks_are_reassembled_once():
    pdu = setup_request()
    half = len(pdu) // 2
    frames = [
        _frame(NODE, RIC, 38470, 36422, [_data_chunk(1, pdu[:half], end=False)]),
        _frame(NODE, RIC, 38470, 36422, [_data_chunk(1, pdu[:half], end=False)]),  # retransmissão
        _frame(NODE, RIC, 38470, 36422, [_data_chunk(2, pdu[half:], begin=False)]),
    ]
    result = dis.extract_messages(_pcap(frames))
    assert not result["errors"]
    assert len(result["messages"]) == 1
    assert result["messages"][0]["role"] == "e2_setup_request"
    assert result["messages"][0]["frame"] == 3
    assert result["stats"]["retransmissions"] == 1


def test_control_ack_must_match_request_ids():
    pdus = closed_loop_pdus()
    pdus[6] = ("up", _pdu(1, 4, [_req(2002, 8), _fn(300)]))  # instância diferente
    frames = [_frame(*((NODE, RIC, 38470, 36422) if d == "up" else (RIC, NODE, 36422, 38470)),
                     [_data_chunk(i + 1, p)]) for i, (d, p) in enumerate(pdus)]
    msgs = dis.extract_messages(_pcap(frames))["messages"]
    roles = dis.assign_chain_roles(msgs, dis.ran_function_kinds(msgs))
    assert roles["control_request"] == 6
    assert roles["control_ack"] is None and roles["kpm_t1"] is None


def test_trailing_bytes_are_reported_as_undecoded():
    frames = [_frame(NODE, RIC, 38470, 36422, [_data_chunk(1, setup_request() + b"\x00\x00")])]
    result = dis.extract_messages(_pcap(frames))
    assert result["messages"][0]["role"] == "undecoded"
    assert result["errors"]


def test_pcapng_is_rejected_explicitly():
    with pytest.raises(dis.DissectError, match="pcapng"):
        dis.read_pcap(b"\x0a\x0d\x0d\x0a" + b"\x00" * 40)


def test_real_nori_pcap_from_phase1():
    pcap = ROOT / "experiments" / "runs" / "nori_rc_demo_seed1" / "raw" / "e2_sctp.pcap"
    result = dis.extract_messages(pcap.read_bytes())
    msgs = result["messages"]
    assert not result["errors"]
    assert [(m["frame"], m["role"], m["direction"]) for m in msgs] == [
        (5, "e2_setup_request", "E2_NODE->RIC"), (8, "e2_setup_response", "RIC->E2_NODE")]
    added = dis.ie_value(msgs[0], dis.IE_RAN_FUNCTIONS_ADDED)
    assert sorted(i["ran_function_id"] for i in added) == [4, 200, 300]
    accepted = dis.ie_value(msgs[1], dis.IE_RAN_FUNCTIONS_ACCEPTED)
    assert sorted(i["ran_function_id"] for i in accepted) == [4, 200, 300]
    assert dis.assign_chain_roles(msgs, dis.ran_function_kinds(msgs))["e2_setup"] == 2


def test_compare_with_tshark_detects_divergence():
    msgs = dis.extract_messages(_closed_loop_pcap())["messages"]
    rows = [{"frame": m["frame"], "pdu_type_index": dis.PDU_KINDS.index(m["pdu_type"]),
             "procedure_code": m["procedure_code"]} for m in msgs]
    assert dis.compare_with_tshark(msgs, {"available": True, "messages": rows})["agreement"] is True
    rows[5]["procedure_code"] = 5
    cmp_ = dis.compare_with_tshark(msgs, {"available": True, "messages": rows})
    assert cmp_["agreement"] is False and cmp_["mismatches"][0]["position"] == 6
    assert dis.compare_with_tshark(msgs, {"available": False})["checked"] is False


# ---------------------------------------------------------------------------
# Integração com o certificador
# ---------------------------------------------------------------------------

FLOWMONITOR = """<?xml version="1.0" ?>
<FlowMonitor><FlowStats>
<Flow flowId="1" txPackets="10" rxPackets="10" rxBytes="1000" txBytes="1000" lostPackets="0"/>
</FlowStats></FlowMonitor>
"""


@pytest.fixture(scope="module")
def policy():
    return cert.load_policy()


@pytest.fixture(scope="module")
def lock():
    return cert.load_versions_lock()


def _nori_run(base, lock, pcap_bytes, _run_id="nori_closed_loop_seed1", **extra):
    nori = lock["profile.nori"]
    run_dir = base / "runs" / _run_id
    (run_dir / "raw").mkdir(parents=True)
    (run_dir / "raw" / "flowmonitor.xml").write_text(FLOWMONITOR, encoding="utf-8")
    (run_dir / "raw" / "e2_sctp.pcap").write_bytes(pcap_bytes)
    manifest = {
        "scenario": "nori-rc-slicing-flowmon", "seed": 1, "command": "./ns3 run ...",
        "run_status": "SUCCESS", "exit_code": 0, "backend": "NORI_NS3",
        "source": ["NS3_FLOWMONITOR", "NORI_E2", "E2_PCAP"],
        "started_at_utc": "2026-11-08T02:00:00Z", "finished_at_utc": "2026-11-08T02:00:30Z",
        "environment": {"os": "Ubuntu 22.04 LTS"}, "ns3_version": "3.42", "fiveg_lena_version": "78b7179",
        "ns3_commit": nori["ns3_commit"], "nr_commit": nori["nr_commit"],
        "nori_commit": nori["nori_commit"], "e2sim_commit": nori["e2sim_commit"],
    }
    manifest.update(extra)
    (run_dir / "execution_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(run_dir).as_posix()}"
             for p in sorted(run_dir.rglob("*")) if p.is_file()]
    (run_dir / "hashes.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return run_dir


def _fake_tshark_agreeing(monkeypatch):
    def fake(pcap_path, ports, exe=None):
        msgs = dis.extract_messages(Path(pcap_path).read_bytes())["messages"]
        rows = [{"frame": m["frame"], "pdu_type_index": dis.PDU_KINDS.index(m["pdu_type"]),
                 "procedure_code": m["procedure_code"]} for m in msgs]
        return {"available": True, "version": "TShark (Wireshark) 4.2.2 [fixture]", "messages": rows, "tsv": ""}
    monkeypatch.setattr(dis, "run_tshark", fake)


def _rules(report):
    return {c.rule: c for c in report.checks}


def test_certifier_uses_confirmed_dissection_for_e2_gates(tmp_path, policy, lock, monkeypatch):
    _fake_tshark_agreeing(monkeypatch)
    run_dir = _nori_run(tmp_path, lock, _closed_loop_pcap())
    droot = tmp_path / "e2_dissection"
    summary = dis.dissect(run_dir / "raw" / "e2_sctp.pcap", droot / run_dir.name, run_dir.name)
    assert summary["independent_confirmation"] is True

    report = cert.certify_run(run_dir, policy, lock, [], droot)
    rules = _rules(report)
    assert rules["R14.pcap"].status == cert.PASS, rules["R14.pcap"].detail
    assert rules["R11.e2_artifacts"].status == cert.PASS
    assert rules["R12.rc_correlation"].status == cert.PASS
    assert report.classification == "ELIGIBLE", report.failed()
    gates = cert.evaluate_gates([report], lock)
    assert gates["G1"]["verdict"] == cert.CERTIFIED
    assert gates["G3"]["verdict"] == cert.CERTIFIED


def test_dissection_without_tshark_does_not_certify(tmp_path, policy, lock):
    run_dir = _nori_run(tmp_path, lock, _closed_loop_pcap())
    droot = tmp_path / "e2_dissection"
    dis.dissect(run_dir / "raw" / "e2_sctp.pcap", droot / run_dir.name, run_dir.name, use_tshark=False)
    report = cert.certify_run(run_dir, policy, lock, [], droot)
    rules = _rules(report)
    assert rules["R14.pcap"].status == cert.WARN
    assert rules["R12.rc_correlation"].status == cert.WARN
    assert cert.evaluate_gates([report], lock)["G1"]["verdict"] == cert.NOT_CERTIFIED


def test_dissection_of_another_pcap_is_rejected(tmp_path, policy, lock, monkeypatch):
    _fake_tshark_agreeing(monkeypatch)
    run_dir = _nori_run(tmp_path, lock, _closed_loop_pcap())
    other = tmp_path / "other.pcap"
    other.write_bytes(_pcap([_frame(NODE, RIC, 38470, 36422, [_data_chunk(1, setup_request())])]))
    droot = tmp_path / "e2_dissection"
    dis.dissect(other, droot / run_dir.name, run_dir.name)
    rules = _rules(cert.certify_run(run_dir, policy, lock, [], droot))
    assert rules["R14.pcap"].status == cert.FAIL
    assert "hash" in rules["R14.pcap"].detail


def test_tampered_message_file_fails_r14(tmp_path, policy, lock, monkeypatch):
    _fake_tshark_agreeing(monkeypatch)
    run_dir = _nori_run(tmp_path, lock, _closed_loop_pcap())
    droot = tmp_path / "e2_dissection"
    summary = dis.dissect(run_dir / "raw" / "e2_sctp.pcap", droot / run_dir.name, run_dir.name)
    (droot / run_dir.name / summary["messages"][4]["file"]).write_bytes(b"forjado")
    rules = _rules(cert.certify_run(run_dir, policy, lock, [], droot))
    assert rules["R14.pcap"].status == cert.FAIL


def _many_indications_pcap(n):
    pdus = closed_loop_pdus()[:5]  # setup, subscription, KPM_t0
    pdus += [("up", _pdu(0, 5, [_req(1001, 1), _fn(200), _octets(25, b"h"), _octets(26, b"kpm-%d" % i)]))
             for i in range(n)]
    frames = [_frame(*((NODE, RIC, 38470, 36422) if d == "up" else (RIC, NODE, 36422, 38470)),
                     [_data_chunk(i + 1, p)]) for i, (d, p) in enumerate(pdus)]
    return _pcap(frames)


def test_compact_output_keeps_bytes_only_for_notable_messages(tmp_path):
    pcap = tmp_path / "e2.pcap"
    pcap.write_bytes(_many_indications_pcap(50))
    summary = dis.dissect(pcap, tmp_path / "out", "r", use_tshark=False)
    files = sorted(p.name for p in (tmp_path / "out" / "messages").iterdir())
    # setup req/resp, subscription req/resp, KPM_t0 (= primeira Indication) e a última Indication
    assert files == ["00001_e2_setup_request.aper", "00002_e2_setup_response.aper",
                     "00003_subscription_request.aper", "00004_subscription_response.aper",
                     "00005_indication.aper", "00055_indication.aper"]
    tsv = (tmp_path / "out" / "messages.tsv").read_text(encoding="utf-8").splitlines()
    assert len(tsv) == 1 + 55 and tsv[0].split("\t") == list(dis.MESSAGE_TSV_COLUMNS)
    assert summary["role_counts"]["indication"] == 51
    assert len(summary["messages"]) == 6


def test_xapp_crosscheck_matches_indications_by_sha256(tmp_path):
    pcap = tmp_path / "e2.pcap"
    pcap.write_bytes(_many_indications_pcap(3))
    msgs = dis.extract_messages(pcap.read_bytes())["messages"]
    inds = [m for m in msgs if m["role"] == "indication"]
    events = tmp_path / "events.jsonl"
    lines = [{"t_utc": "2026-11-08T17:15:49.900Z", "event": "subscription_request", "status": 201}]
    lines += [{"t_utc": "2026-11-08T17:15:50Z", "event": "rmr_message", "mtype": 12050, "sha256": m["sha256"]}
              for m in inds[:3]]  # a última Indication não chegou à xApp
    lines.append({"t_utc": "2026-11-08T17:15:51Z", "event": "rmr_message", "mtype": 12050, "sha256": "0" * 64})
    events.write_text("\n".join(json.dumps(l) for l in lines) + "\n", encoding="utf-8")
    summary = dis.dissect(pcap, tmp_path / "out", "r", use_tshark=False, xapp_events=events)
    x = summary["xapp_crosscheck"]
    assert x["pcap_indications"] == 4 and x["xapp_indications"] == 4
    assert x["pcap_indications_received_by_xapp"] == 3
    assert x["xapp_indications_not_in_pcap"] == 1
    assert x["chain_roles_received_by_xapp"] == {"kpm_t0": True}
    last = (tmp_path / "out" / "messages.tsv").read_text(encoding="utf-8").splitlines()[-1].split("\t")
    assert last[-1] == "0"


def test_kpm_t0_is_the_last_kpm_before_the_control():
    pdus = closed_loop_pdus()
    extra = [("up", _pdu(0, 5, [_req(1001, 1), _fn(200), _octets(25, b"h"), _octets(26, b"kpm-%d" % i)]))
             for i in range(3)]
    pdus = pdus[:5] + extra + pdus[5:]   # 4 KPM antes do Control
    frames = [_frame(*((NODE, RIC, 38470, 36422) if d == "up" else (RIC, NODE, 36422, 38470)),
                     [_data_chunk(i + 1, p)]) for i, (d, p) in enumerate(pdus)]
    msgs = dis.extract_messages(_pcap(frames))["messages"]
    roles = dis.assign_chain_roles(msgs, dis.ran_function_kinds(msgs))
    assert roles["kpm_t0"] == 8 and roles["control_request"] == 9 and roles["control_ack"] == 10
    assert roles["kpm_t1"] == 11


def _closed_loop_with_xapp_events(tmp_path, source):
    pcap = tmp_path / "e2.pcap"
    pcap.write_bytes(_closed_loop_pcap())
    msgs = dis.extract_messages(pcap.read_bytes())["messages"]
    by_role = {}
    for m in msgs:
        by_role.setdefault(m["role"], []).append(m)
    t0, ctrl, ack = by_role["indication"][0], by_role["control_request"][0], by_role["control_ack"][0]
    events = [{"t_utc": "2026-11-08T02:00:01Z", "event": "rmr_message", "mtype": 12050, "sha256": m["sha256"]}
              for m in by_role["indication"]]
    events.append({"t_utc": "2026-11-08T02:00:02Z", "event": "control_request", "sha256": ctrl["sha256"],
                   "decision_source": source, "trigger_kpm_sha256": t0["sha256"], "quotas": []})
    events.append({"t_utc": "2026-11-08T02:00:03Z", "event": "control_outcome", "sha256": ack["sha256"],
                   "outcome": "ACK", "correlated_with_request": True, "latency_ms": 4.2})
    path = tmp_path / "events.jsonl"
    path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    return path


@pytest.mark.parametrize("source,reason", [("FIXED_PROBE", "FIXED_PROBE"), ("H_RDL", "efeito na RAN")])
def test_g4_requires_an_h_rdl_decision_on_kpm_t0(tmp_path, policy, lock, monkeypatch, source, reason):
    _fake_tshark_agreeing(monkeypatch)
    run_dir = _nori_run(tmp_path, lock, _closed_loop_pcap())
    droot = tmp_path / "e2_dissection"
    events = _closed_loop_with_xapp_events(tmp_path, source)
    summary = dis.dissect(run_dir / "raw" / "e2_sctp.pcap", droot / run_dir.name, run_dir.name, xapp_events=events)
    decision = summary["xapp_crosscheck"]["decision"]
    assert decision["pcap_control_sent_by_xapp"] and decision["trigger_is_kpm_t0"] and decision["ack_received_by_xapp"]
    report = cert.certify_run(run_dir, policy, lock, [], droot)
    gates = cert.evaluate_gates([report], lock)
    assert gates["G3"]["verdict"] == cert.CERTIFIED
    # Sem medida de efeito na RAN, nem a decisão do H-RDL certifica G4.
    assert gates["G4"]["verdict"] == cert.NOT_CERTIFIED
    assert reason in gates["G4"]["reason"], gates["G4"]["reason"]


def test_versions_lock_accepts_only_listed_nori_patches(tmp_path, policy, lock):
    allowed = lock["profile.nori"]["nori_patches"].split(",")[0]
    name, _, digest = allowed.partition(":")
    ok = _nori_run(tmp_path / "a", lock, b"", nori_patches=[{"file": name, "sha256": digest}])
    rules = _rules(cert.certify_run(ok, policy, lock, [], tmp_path / "e2_dissection"))
    assert rules["R6.versions_lock"].status == cert.PASS and name in rules["R6.versions_lock"].detail
    bad = _nori_run(tmp_path / "b", lock, b"", nori_patches=[{"file": name, "sha256": "0" * 64}])
    rules = _rules(cert.certify_run(bad, policy, lock, [], tmp_path / "e2_dissection"))
    assert rules["R6.versions_lock"].status == cert.FAIL


# ---------------------------------------------------------------------------
# Efeito do Control na RAN (scripts/certification/slice_effect.py) e G4
# ---------------------------------------------------------------------------

effect_mod = _load("slice_effect", "scripts/certification/slice_effect.py")


def _series_csv(t_change, embb_after, urllc_after, wall0=1794146159.0):
    """Série a cada 0,5 s com tempo real exato (parede = wall0 + t); 150 Mb/s por fatia antes de t_change."""
    rows = ["sim_time_s,wall_epoch_s,ue_index,sst,tx_packets,rx_packets,rx_bytes,delay_sum_s"]
    acc = {1: 0.0, 2: 0.0}
    for k in range(0, 31):
        t = k * 0.5
        if k:
            for sst, after in ((1, embb_after), (2, urllc_after)):
                rate = 150.0 if t <= t_change else after
                acc[sst] += rate * 1e6 / 8 * 0.5
        for ue, sst in ((0, 1), (1, 2)):
            rows.append(f"{t:.6f},{wall0 + t:.6f},{ue},{sst},0,0,{int(acc[sst])},0")
    return "\n".join(rows) + "\n"


def _calibration(tmp_path, k):
    path = tmp_path / "calibration.json"
    path.write_text(json.dumps({"valid": True, "k_mbps_per_prb_pct": {"1": k, "2": k}}), encoding="utf-8")
    return path


def _hrdl_closed_loop_run(tmp_path, lock, monkeypatch, embb_after, urllc_after, calibration_k=3.0):
    try:
        from src.e2.v3 import codec as c3
        e2sm = c3.E2smCodec()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"ASN.1 do NORI indisponível: {exc}")
    pdus = closed_loop_pdus()
    pdus[5] = ("down", c3.build_slice_quota_control(e2sm, 1003, 1, 300,
                                                    [c3.SlicePrbQuota(1, 40), c3.SlicePrbQuota(2, 60)]))
    pdus[6] = ("up", _pdu(1, 4, [_req(1003, 1), _fn(300)]))
    frames = [_frame(*((NODE, RIC, 38470, 36422) if d == "up" else (RIC, NODE, 36422, 38470)),
                     [_data_chunk(i + 1, p)]) for i, (d, p) in enumerate(pdus)]
    pcap = _pcap(frames)           # quadro 6 (Control) no instante wall0 + 5 s
    run_dir = _nori_run(tmp_path, lock, pcap)
    (run_dir / "raw" / "slice_series.csv").write_text(_series_csv(5.0, embb_after, urllc_after), encoding="utf-8")
    lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(run_dir).as_posix()}"
             for p in sorted(run_dir.rglob("*")) if p.is_file() and p.name != "hashes.sha256"]
    (run_dir / "hashes.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    droot = tmp_path / "e2_dissection"
    msgs = dis.extract_messages(pcap)["messages"]
    by_role = {}
    for m in msgs:
        by_role.setdefault(m["role"], []).append(m)
    events = [{"event": "rmr_message", "mtype": 12050, "sha256": m["sha256"]} for m in by_role["indication"]]
    events += [{"event": "control_request", "sha256": by_role["control_request"][0]["sha256"], "decision_source": "H_RDL",
                "trigger_kpm_sha256": by_role["indication"][0]["sha256"], "quotas": []},
               {"event": "control_outcome", "sha256": by_role["control_ack"][0]["sha256"], "outcome": "ACK",
                "correlated_with_request": True, "latency_ms": 2.0}]
    ev = tmp_path / "events.jsonl"
    ev.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    dis.dissect(run_dir / "raw" / "e2_sctp.pcap", droot / run_dir.name, run_dir.name, xapp_events=ev)
    cal = _calibration(tmp_path, calibration_k) if calibration_k else None
    effect = effect_mod.analyze(run_dir.name, tmp_path / "runs", droot, calibration=cal)
    if cal:
        # o certificador confere a calibração pelo caminho relativo à raiz do repositório
        monkeypatch.setattr(cert, "ROOT", tmp_path)
        data = json.loads((droot / run_dir.name / "slice_effect.json").read_text(encoding="utf-8"))
        data["calibration"] = "calibration.json"
        (droot / run_dir.name / "slice_effect.json").write_text(json.dumps(data), encoding="utf-8")
    return run_dir, droot, effect


def test_effect_consistent_with_quotas_certifies_g4(tmp_path, policy, lock, monkeypatch):
    _fake_tshark_agreeing(monkeypatch)
    run_dir, droot, effect = _hrdl_closed_loop_run(tmp_path, lock, monkeypatch, embb_after=100.0, urllc_after=150.0)
    assert effect["verdict"] == "CONSISTENT", effect
    assert abs(effect["control_sim_time_s"] - 5.0) < 1e-6
    assert effect["quotas_from_pcap"][0]["max_prb_ratio"] == 40
    # k = 3 Mb/s por % -> eMBB usava 50 % dos PRBs; teto 40 restringe; previsão 120 Mb/s, medido 100 (erro 16,7 %)
    assert effect["rule"] == "v2-calibrated"
    assert effect["slices"]["1"]["expectation"] == "decrease_to_prediction"
    assert effect["slices"]["1"]["predicted_after_mbps"] == 120.0
    assert effect["slices"]["2"]["expectation"] == "no_decrease"
    report = cert.certify_run(run_dir, policy, lock, [], droot)
    gates = cert.evaluate_gates([report], lock)
    assert gates["G4"]["verdict"] == cert.CERTIFIED, gates["G4"]["reason"]


def test_effect_contrary_to_quotas_blocks_g4(tmp_path, policy, lock, monkeypatch):
    _fake_tshark_agreeing(monkeypatch)
    run_dir, droot, effect = _hrdl_closed_loop_run(tmp_path, lock, monkeypatch, embb_after=150.0, urllc_after=150.0)
    assert effect["verdict"] == "INCONSISTENT"
    gates = cert.evaluate_gates([cert.certify_run(run_dir, policy, lock, [], droot)], lock)
    assert gates["G4"]["verdict"] == cert.NOT_CERTIFIED and "INCONSISTENT" in gates["G4"]["reason"]


def test_tampered_series_invalidates_effect(tmp_path, policy, lock, monkeypatch):
    _fake_tshark_agreeing(monkeypatch)
    run_dir, droot, _ = _hrdl_closed_loop_run(tmp_path, lock, monkeypatch, embb_after=100.0, urllc_after=150.0)
    csv_path = run_dir / "raw" / "slice_series.csv"
    csv_path.write_text(csv_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    report = cert.certify_run(run_dir, policy, lock, [], droot)
    assert report.facts["slice_effect"]["verdict"] == "INVALID"


def test_v1_rule_consistent_does_not_certify_g4(tmp_path, policy, lock, monkeypatch):
    _fake_tshark_agreeing(monkeypatch)
    run_dir, droot, effect = _hrdl_closed_loop_run(tmp_path, lock, monkeypatch, embb_after=100.0,
                                                   urllc_after=150.0, calibration_k=None)
    assert effect["rule"] == "v1-throughput-share" and effect["verdict"] == "CONSISTENT"
    gates = cert.evaluate_gates([cert.certify_run(run_dir, policy, lock, [], droot)], lock)
    assert gates["G4"]["verdict"] == cert.NOT_CERTIFIED


def test_v2_prediction_outside_tolerance_is_inconsistent(tmp_path, policy, lock, monkeypatch):
    _fake_tshark_agreeing(monkeypatch)
    # eMBB cai, mas para 60 Mb/s: previsão 40 % x 3 = 120 Mb/s, erro de 50 %
    _, _, effect = _hrdl_closed_loop_run(tmp_path, lock, monkeypatch, embb_after=60.0, urllc_after=150.0)
    assert effect["verdict"] == "INCONSISTENT"
    assert effect["slices"]["1"]["prediction_error"] == 0.5


cal_mod = _load("calibrate_slice_capacity", "scripts/certification/calibrate_slice_capacity.py")


@pytest.mark.parametrize("after,valid", [(90.0, True), (150.0, False)])
def test_calibration_requires_binding_caps(tmp_path, lock, monkeypatch, after, valid):
    try:
        from src.e2.v3 import codec as c3
        e2sm = c3.E2smCodec()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"ASN.1 do NORI indisponível: {exc}")
    pdus = closed_loop_pdus()
    pdus[5] = ("down", c3.build_slice_quota_control(e2sm, 1003, 1, 300,
                                                    [c3.SlicePrbQuota(1, 30), c3.SlicePrbQuota(2, 30)]))
    pdus[6] = ("up", _pdu(1, 4, [_req(1003, 1), _fn(300)]))
    frames = [_frame(*((NODE, RIC, 38470, 36422) if d == "up" else (RIC, NODE, 36422, 38470)),
                     [_data_chunk(i + 1, p)]) for i, (d, p) in enumerate(pdus)]
    pcap = _pcap(frames)
    run_dir = _nori_run(tmp_path, lock, pcap)
    (run_dir / "raw" / "slice_series.csv").write_text(_series_csv(5.0, after, after), encoding="utf-8")
    droot = tmp_path / "e2_dissection"
    dis.dissect(run_dir / "raw" / "e2_sctp.pcap", droot / run_dir.name, run_dir.name, use_tshark=False)
    out = cal_mod.calibrate(run_dir.name, tmp_path / "cal.json", tmp_path / "runs", droot)
    assert out["valid"] is valid
    if valid:
        assert out["k_mbps_per_prb_pct"] == {"1": 3.0, "2": 3.0}



def _calibration_run(tmp_path, lock, run_id, caps, after):
    from src.e2.v3 import codec as c3
    e2sm = c3.E2smCodec()
    pdus = closed_loop_pdus()
    pdus[5] = ("down", c3.build_slice_quota_control(e2sm, 1003, 1, 300,
                                                    [c3.SlicePrbQuota(1, caps[0]), c3.SlicePrbQuota(2, caps[1])]))
    pdus[6] = ("up", _pdu(1, 4, [_req(1003, 1), _fn(300)]))
    frames = [_frame(*((NODE, RIC, 38470, 36422) if d == "up" else (RIC, NODE, 36422, 38470)),
                     [_data_chunk(i + 1, p)]) for i, (d, p) in enumerate(pdus)]
    run_dir = _nori_run(tmp_path, lock, _pcap(frames), _run_id=run_id)
    (run_dir / "raw" / "slice_series.csv").write_text(_series_csv(5.0, after[0], after[1]), encoding="utf-8")
    dis.dissect(run_dir / "raw" / "e2_sctp.pcap", tmp_path / "e2_dissection" / run_id, run_id, use_tshark=False)


@pytest.mark.parametrize("afters,valid,k", [
    (((90.0, 150.0), (150.0, 96.0)), True, {"1": 3.0, "2": 3.2}),     # cada fatia restrita cai
    (((150.0, 150.0), (150.0, 96.0)), False, None),                   # a eMBB a 30 % não caiu
])
def test_complementary_calibration(tmp_path, lock, afters, valid, k):
    try:
        from src.e2.v3 import codec as c3
        c3.E2smCodec()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"ASN.1 do NORI indisponível: {exc}")
    _calibration_run(tmp_path, lock, "nori_cal3070", (30, 70), afters[0])
    _calibration_run(tmp_path, lock, "nori_cal7030", (70, 30), afters[1])
    out = cal_mod.calibrate_complementary(["nori_cal3070", "nori_cal7030"], tmp_path / "cal.json",
                                          tmp_path / "runs", tmp_path / "e2_dissection")
    assert out["valid"] is valid, out.get("reason")
    assert [r["restricted_sst"] for r in out["runs"]] == [1, 2]
    if valid:
        assert out["k_mbps_per_prb_pct"] == k
    assert not (tmp_path / "cal.part.json").exists()


def test_complementary_calibration_rejects_caps_not_summing_100(tmp_path, lock):
    try:
        from src.e2.v3 import codec as c3
        c3.E2smCodec()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"ASN.1 do NORI indisponível: {exc}")
    _calibration_run(tmp_path, lock, "nori_cal30", (30, 30), (90.0, 90.0))
    out = cal_mod.calibrate_complementary(["nori_cal30"], tmp_path / "cal.json", tmp_path / "runs",
                                          tmp_path / "e2_dissection")
    assert out["valid"] is False and "não somam 100" in out["reason"]


# ---------------------------------------------------------------------------
# Desenho v4: curva teto -> vazão e previsão por interpolação deixa-um-fora
# ---------------------------------------------------------------------------

curve_mod = _load("slice_cap_curve", "scripts/certification/slice_cap_curve.py")

CURVE_PTS = [  # URLLC: restringe até 25 %, livre a 30 %
    {"cap_max_prb_pct": 10.0, "throughput_after_mbps": 38.0, "binding": True},
    {"cap_max_prb_pct": 15.0, "throughput_after_mbps": 57.0, "binding": True},
    {"cap_max_prb_pct": 20.0, "throughput_after_mbps": 76.0, "binding": True},
    {"cap_max_prb_pct": 25.0, "throughput_after_mbps": 95.0, "binding": True},
    {"cap_max_prb_pct": 30.0, "throughput_after_mbps": 151.0, "binding": False},
]


def test_predict_leave_one_out_and_threshold():
    p = effect_mod.predict(CURVE_PTS, 20.0)
    assert p["kind"] == "interpolated" and p["from_levels"] == [15.0, 25.0]   # o nível 20 fica de fora
    assert abs(p["predicted_after_mbps"] - 76.0) < 1e-9
    assert effect_mod.predict(CURVE_PTS, 80.0)["kind"] == "no_decrease"
    assert effect_mod.predict(CURVE_PTS, 30.0)["kind"] == "no_decrease"
    assert effect_mod.predict(CURVE_PTS, 10.0)["kind"] == "not_testable"      # sem vizinho abaixo


def test_curve_v4_rule_certifies_g4_when_prediction_holds(tmp_path, policy, lock, monkeypatch):
    _fake_tshark_agreeing(monkeypatch)
    # eMBB com teto 40: série cai de 150 para 100; curva da eMBB prevê 100 a 40 % (entre 30 e 50)
    run_dir, droot, _ = _hrdl_closed_loop_run(tmp_path, lock, monkeypatch, embb_after=100.0,
                                              urllc_after=150.0, calibration_k=None)
    curve = {"valid": True, "curve": {
        "1": [{"cap_max_prb_pct": 30.0, "throughput_after_mbps": 80.0, "binding": True},
              {"cap_max_prb_pct": 40.0, "throughput_after_mbps": 99.0, "binding": True},
              {"cap_max_prb_pct": 50.0, "throughput_after_mbps": 120.0, "binding": True},
              {"cap_max_prb_pct": 70.0, "throughput_after_mbps": 150.0, "binding": False}],
        "2": [{"cap_max_prb_pct": 30.0, "throughput_after_mbps": 150.0, "binding": False}]}}
    cpath = tmp_path / "curve.json"
    cpath.write_text(json.dumps(curve), encoding="utf-8")
    effect = effect_mod.analyze(run_dir.name, tmp_path / "runs", droot, curve=cpath)
    assert effect["rule"] == "v4-curve" and effect["verdict"] == "CONSISTENT", effect
    assert effect["slices"]["1"]["predicted_after_mbps"] == 100.0          # interpolado entre 30 e 50
    monkeypatch.setattr(cert, "ROOT", tmp_path)
    data = json.loads((droot / run_dir.name / "slice_effect.json").read_text(encoding="utf-8"))
    data["calibration"] = "curve.json"
    (droot / run_dir.name / "slice_effect.json").write_text(json.dumps(data), encoding="utf-8")
    gates = cert.evaluate_gates([cert.certify_run(run_dir, policy, lock, [], droot)], lock)
    assert gates["G4"]["verdict"] == cert.CERTIFIED, gates["G4"]["reason"]


def test_curve_build_validity(tmp_path, lock):
    try:
        from src.e2.v3 import codec as c3
        c3.E2smCodec()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"ASN.1 do NORI indisponível: {exc}")
    _calibration_run(tmp_path, lock, "nori_curve10", (10, 10), (40.0, 30.0))
    _calibration_run(tmp_path, lock, "nori_curve20", (20, 20), (80.0, 60.0))
    out = curve_mod.build_curve(["nori_curve10", "nori_curve20"], tmp_path / "curve.json",
                                tmp_path / "runs", tmp_path / "e2_dissection")
    assert out["valid"] is True
    assert [p["cap_max_prb_pct"] for p in out["curve"]["1"]] == [10.0, 20.0]
    # não monotônica: mais vazão com teto menor
    _calibration_run(tmp_path, lock, "nori_curve15", (15, 15), (120.0, 45.0))
    bad = curve_mod.build_curve(["nori_curve10", "nori_curve15", "nori_curve20"], tmp_path / "curve2.json",
                                tmp_path / "runs", tmp_path / "e2_dissection")
    assert bad["valid"] is False and "monotônica" in bad["reason"]
