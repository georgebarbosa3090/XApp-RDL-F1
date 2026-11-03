"""Tests for run-scoped telemetry consumed by the six terminal monitors."""

import json
import os

from src.observability.real_data_telemetry_provider import RealDataTelemetryProvider

FLOWMONITOR_XML = (
    '<FlowMonitor><FlowStats><Flow flowId="1" '
    'timeFirstRxPacket="+1000000000ns" timeLastRxPacket="+2000000000ns" '
    'delaySum="+4000000ns" rxBytes="1000" txPackets="2" rxPackets="2" '
    'lostPackets="0"/></FlowStats><Ipv4FlowClassifier><Flow flowId="1" '
    'sourceAddress="10.0.0.1" destinationAddress="10.0.0.2" '
    'destinationPort="5000"/></Ipv4FlowClassifier></FlowMonitor>'
)


def _create_run(workspace, name, status, log=""):
    run_dir = workspace / "experiments" / "results" / "ns3_runs" / name
    run_dir.mkdir(parents=True)
    (run_dir / "run_status.json").write_text(
        json.dumps({"status": status, "updated_at_utc": "2026-01-01T00:00:00Z"}),
        encoding="utf-8",
    )
    (run_dir / "execution.log").write_text(log, encoding="utf-8")
    return run_dir


def test_provider_returns_all_six_blocks_without_a_run(tmp_path):
    state = RealDataTelemetryProvider(workspace_dir=str(tmp_path)).get_full_real_state()

    assert state["run_status"] == "not_found"
    assert state["evidence"]["flowmonitor"] is False
    assert state["evidence"]["kpm"] is False
    assert state["evidence"]["rdl_decision"] is False
    assert state["evidence"]["control_request"] is False
    assert state["evidence"]["control_ack"] is False
    assert state["block1_ran_registration"]["total_connected_ues"] is None
    assert {
        key for key in state if key.startswith("block")
    } == {
        "block1_ran_registration",
        "block2_protocol_signaling",
        "block3_perception_module",
        "block4_knowledge_graph",
        "block5_refinement_module",
        "block6_ran_control_action",
    }


def test_latest_run_tracks_log_and_parses_small_flowmonitor(tmp_path):
    runs_dir = tmp_path / "experiments" / "results" / "ns3_runs"
    runs_dir.mkdir(parents=True)
    older = _create_run(
        tmp_path,
        "20261029T161743Z_scenario_rdl_tvs_conflict_older",
        "completed",
    )
    old_flowmonitor = older / "flowmonitor.xml"
    old_flowmonitor.write_text(FLOWMONITOR_XML + (" " * 200), encoding="utf-8")
    assert old_flowmonitor.stat().st_size > 500
    (older / "kpm.jsonl").write_text('{"stale":true}\n', encoding="utf-8")
    (older / "control_request.json").write_text('{"stale":true}\n', encoding="utf-8")
    latest = _create_run(
        tmp_path,
        "20261029T161800Z_scenario_rdl_tvs_conflict_latest",
        "running",
        "Starting simulation\n",
    )
    os.utime(older, (2000, 2000))
    os.utime(latest, (2000, 2000))

    provider = RealDataTelemetryProvider(workspace_dir=str(tmp_path))
    state = provider.get_full_real_state()
    assert state["active_run_dir"] == latest.name
    assert state["run_status"] == "running"
    assert state["evidence"]["flowmonitor"] is False
    assert state["block1_ran_registration"]["prb_utilization_pct"] is None
    assert state["block2_protocol_signaling"]["recent_execution_log"] == [
        "Starting simulation"
    ]
    scenario_state = RealDataTelemetryProvider(
        workspace_dir=str(tmp_path),
        target_scenario="S3",
    ).get_full_real_state()
    assert scenario_state["active_run_dir"] == latest.name
    assert scenario_state["evidence"]["kpm"] is False
    assert scenario_state["evidence"]["control_request"] is False

    with (latest / "execution.log").open("a", encoding="utf-8") as log:
        log.write("Traffic generation started\n")
    state = provider.get_full_real_state()
    assert state["block2_protocol_signaling"]["recent_execution_log"] == [
        "Starting simulation",
        "Traffic generation started",
    ]

    (latest / "kpm.csv").write_text("metric,value\n", encoding="utf-8")
    (latest / "control_request.json").write_text('{"run":"latest"}\n', encoding="utf-8")
    state = provider.get_full_real_state()
    assert state["evidence"]["kpm"] is True
    assert state["evidence"]["control_request"] is True
    assert state["evidence"]["control_ack"] is False

    (latest / "flowmonitor.xml").write_text(FLOWMONITOR_XML, encoding="utf-8")
    (latest / "run_status.json").write_text(
        json.dumps({"status": "completed", "updated_at_utc": "2026-01-01T00:01:00Z"}),
        encoding="utf-8",
    )
    state = provider.get_full_real_state()

    assert state["active_run_dir"] == latest.name
    assert state["run_status"] == "completed"
    assert state["evidence"]["flowmonitor"] is True
    assert state["block1_ran_registration"]["active_data_flows"] == 1
    assert state["block1_ran_registration"]["total_packets_rx"] == 2
    flow = state["block1_ran_registration"]["flows"][0]
    assert flow["src_ip"] == "10.0.0.1"
    assert flow["dst_ip"] == "10.0.0.2"
    assert "ue_id" not in flow
    assert "slice" not in flow
    assert "sla_violation" not in flow
    assert state["block3_perception_module"]["mean_delay_ms"] == 2.0
    assert state["block4_knowledge_graph"]["nodes_count"] == 2
    assert state["block1_ran_registration"]["total_connected_ues"] is None
    assert state["block1_ran_registration"]["prb_utilization_pct"] is None
    assert state["block3_perception_module"]["sla_evaluation"] == (
        "unavailable_without_per_flow_qos_configuration"
    )
    assert state["evidence"]["kpm"] is True
    assert state["evidence"]["rdl_decision"] is False
    assert state["evidence"]["control_request"] is True
    assert state["evidence"]["control_ack"] is False


def test_small_valid_flowmonitor_is_not_discarded(tmp_path):
    run_dir = _create_run(tmp_path, "small_scenario_no_conflict", "completed")
    flowmonitor = run_dir / "flowmonitor.xml"
    flowmonitor.write_text("<FlowMonitor />", encoding="utf-8")
    assert flowmonitor.stat().st_size < 100

    state = RealDataTelemetryProvider(workspace_dir=str(tmp_path)).get_full_real_state()

    assert state["evidence"]["flowmonitor"] is True
    assert state["block1_ran_registration"]["active_data_flows"] == 0


def test_explicit_run_filter_does_not_fall_back_to_another_run(tmp_path):
    _create_run(tmp_path, "available_scenario_direct_prb", "completed")
    provider = RealDataTelemetryProvider(
        workspace_dir=str(tmp_path),
        target_run="missing-run",
    )

    state = provider.get_full_real_state()

    assert state["run_status"] == "not_found"
    assert state["active_run_dir"] == "sem_execucao"
    assert "missing-run" in state["run_status_message"]
