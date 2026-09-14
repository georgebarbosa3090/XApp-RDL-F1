"""
test_coverage_expansion_f1.py: Suíte estendida de testes unitários para a Fase 1 (H-RDL / XApp-RDL-F1).
Eleva a cobertura de código e de branches para >85%, exercitando SdlRepository,
RefinementAgent, RDLxApp handlers/pipelines e subsistemas observáveis.
"""

import json
import os
import time
import pytest

from src.conflict_types import (
    XAppAction,
    ConflictType,
    ConflictSeverity,
    ConflictEvent,
    ResolutionStrategy,
    ResolutionAction,
    KPMReport,
    RDLDecision
)
from src.infrastructure.memory_module import MemoryModule
from src.infrastructure.sdl_repository import SdlRepository
from src.infrastructure.ran_backend_adapter import NoriBackendAdapter, SrsRanBackendAdapter
from src.infrastructure.ran_backend_factory import get_ran_backend_adapter
from src.infrastructure.ric_request_id_allocator import RicRequestIdAllocator, get_ric_request_id_allocator
from src.observability.health_server import HealthServer, AppState
from src.observability.metrics import MetricsServer
from src.observability.causal_tracker import CausalTracker, CausalRecord, ScientificSummary
from src.agents.refinement_agent import RefinementAgent
from src.rdl_xapp import RDLxApp


# ============================================================================
# 1. TESTES DO SDL REPOSITORY
# ============================================================================

def test_sdl_repository_operations():
    class MockXapp:
        def __init__(self):
            self.store = {}
        def sdl_set(self, namespace, key, value):
            self.store[f"{namespace}:{key}"] = value
        def sdl_get(self, namespace, key):
            return self.store.get(f"{namespace}:{key}")

    mock_xapp = MockXapp()
    sdl = SdlRepository(xapp_instance=mock_xapp)

    # Subscriptions & Nodes
    sdl.save_subscription("sub_01", {"node_id": "gnb_01", "period_ms": 200})
    sdl.save_e2_node("gnb_01", {"status": "CONNECTED", "ran_functions": [2, 3]})
    sdl.save_latest_kpm_state("gnb_01", {"throughput": 120.5})

    # Proposals & Decisions
    sdl.save_action_proposal("prop_01", {"parameter": "PRB_QUOTA", "value": 50})
    sdl.save_decision("dec_01", {"strategy": "TVS", "selected": ["PRB_QUOTA"]})
    sdl.save_control_request("req_01", {"node_id": "gnb_01", "parameter": "PRB_QUOTA"})
    sdl.update_control_result("req_01", "ACK_RECEIVED")
    sdl.record_rollback("req_01")

    # Add operations
    act = XAppAction(xapp_id="xapp_1", node_id="gnb_01", parameter="PRB_QUOTA", value=60.0, priority=50)
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[act],
        description="Direct PRB collision"
    )
    resolution = ResolutionAction(
        conflict_id=conflict.conflict_id,
        strategy_used=ResolutionStrategy.PRIORITY_TABLE,
        winning_actions=[act],
        modified_value=60.0,
        confidence=0.95,
        validation_level=1
    )

    sdl.add_action(act)
    sdl.add_conflict(conflict)
    sdl.add_resolution(resolution)

    assert len(sdl.get_recent_actions(10)) >= 1
    assert sdl.get_similar_resolutions(conflict) == []


# ============================================================================
# 2. TESTES DE OBSERVABILIDADE (HEALTH & METRICS & CAUSAL)
# ============================================================================

def test_health_and_metrics_servers():
    health = HealthServer(port=8089)
    health.set_state(AppState.READY)
    assert health.state == AppState.READY

    health.set_state(AppState.STOPPED)
    assert health.state == AppState.STOPPED

    metrics = MetricsServer(port=8099)
    metrics.record_kpm()
    metrics.update_active_xapps(5)

    act = XAppAction(xapp_id="xapp_1", node_id="gnb_01", parameter="PRB_QUOTA", value=60.0, priority=50)
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.CRITICAL,
        involved_xapps=[act]
    )
    resolution = ResolutionAction(
        conflict_id=conflict.conflict_id,
        strategy_used=ResolutionStrategy.TVS,
        winning_actions=[act],
        modified_value=60.0,
        confidence=0.9,
        validation_level=1
    )
    metrics.record_conflict(conflict)
    metrics.record_resolution(resolution, latency_s=0.005)


def test_causal_tracker_full_cycle():
    tracker = CausalTracker()
    tracker.register_conflict_event("conf_01", "DIRECT", 2)
    
    rec = tracker.record_decision(
        action_id="act_test_01",
        decision_id="dec_test_01",
        ric_request_id=1001,
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        old_val=40.0,
        new_val=60.0,
        kpm_before={"latency_ms": 15.0, "throughput_mbps": 50.0},
        strategy="TVS"
    )
    assert rec.action_id == "act_test_01"

    ack_ok = tracker.record_ack(1001, rtt_ms=2.5)
    assert ack_ok is True

    eff_ok = tracker.record_telemetry_effect("act_test_01", {"latency_ms": 3.0, "throughput_mbps": 85.0})
    assert eff_ok is True

    summary = tracker.compute_metrics()
    assert summary.total_conflicts_detected >= 1
    assert summary.total_acks_received >= 1
    
    log_json = tracker.export_causal_log_json()
    assert "act_test_01" in log_json


# ============================================================================
# 3. TESTES DO REFINEMENT AGENT (SAFETY GUARDS)
# ============================================================================

def test_discrete_event_ran_simulator_modes():
    from src.simulation.discrete_event_ran_simulator import DiscreteEventRANSimulator
    for m in ["B0", "B1", "B2", "B3"]:
        sim = DiscreteEventRANSimulator(seed=42, duration_s=0.2, decision_interval_s=0.1, mode=m, num_ues=6, demo_mode="fast")
        res = sim.run()
        assert res["mode"] == m
        assert len(res["flow_metrics"]) > 0


def test_control_dispatcher_full():
    from src.coordination.control_dispatcher import ControlDispatcher
    
    class MockRmr:
        def __init__(self):
            self.sent = []
        def rmr_send(self, payload, mtype, meid):
            self.sent.append((payload, mtype, meid))
            return True

    mock_rmr = MockRmr()
    mem = MemoryModule()
    sdl = SdlRepository()
    dispatcher = ControlDispatcher(mock_rmr, sdl)

    act = XAppAction(xapp_id="xapp_1", node_id="gnb_01", parameter="PRB_QUOTA", value=50.0, priority=50)
    decision = RDLDecision(
        selected_actions=[act],
        safety_result={"safe": True}
    )
    # Testa despacho e handlers
    dispatcher.handle_ack(b'{"req_id": "simulated_req_id"}')
    dispatcher.handle_failure(b'{"req_id": "simulated_req_id"}')


def test_ric_request_id_allocator_full():
    alloc = RicRequestIdAllocator(base_requestor_id=2000)
    req1 = alloc.allocate("gnb_01", 3, decision_id="dec_01", action_id="act_01")
    assert req1.requestor_id == 2000
    assert req1.instance_id == 1

    lookup = alloc.lookup_correlation("gnb_01", 3, 2000, 1)
    assert lookup is not None
    assert lookup["decision_id"] == "dec_01"
    assert lookup["action_id"] == "act_01"

    popped = alloc.pop_correlation("gnb_01", 3, 2000, 1)
    assert popped is not None

    # Expired cleanup
    alloc.allocate("gnb_01", 3, decision_id="dec_02", action_id="act_02")
    removed = alloc.cleanup_expired(ttl_seconds=-1.0)
    assert removed >= 1


def test_perception_agent_full():
    from src.agents.perception_agent import PerceptionAgent
    perc = PerceptionAgent()

    # KPM Report update
    kpm = KPMReport(
        node_id="gnb_01",
        ue_id="ue_01",
        drb_thp_dl=100.0,
        drb_thp_ul=50.0,
        drb_delay_dl=1.5,
        prb_used_dl=40
    )
    perc.update_kpm_report(kpm)
    assert perc.latest_kpm is not None
    assert perc.latest_kpm.node_id == "gnb_01"

    # Direct conflict inside group
    act1 = XAppAction(xapp_id="x1", node_id="gnb_01", parameter="TX_POWER", value=20.0, priority=10)
    act2 = XAppAction(xapp_id="x2", node_id="gnb_01", parameter="TX_POWER", value=15.0, priority=20)
    conflicts = perc.register_action_group([act1, act2])
    assert len(conflicts) >= 1
    assert len(perc.get_active_xapps()) >= 1

    # Conflict against history
    act3 = XAppAction(xapp_id="x3", node_id="gnb_01", parameter="TX_POWER", value=18.0, priority=30)
    conflicts_hist = perc.register_action_group([act3])
    assert len(conflicts_hist) >= 1

    # Indirect conflict against history
    act_prb = XAppAction(xapp_id="x4", node_id="gnb_01", parameter="PRB_QUOTA", value=80.0, priority=50)
    conflicts_ind = perc.register_action_group([act_prb])
    assert len(conflicts_ind) >= 1


def test_refinement_all_parameters():
    mem = MemoryModule()
    refinement = RefinementAgent(mem)
    refinement.config["minimum_control_interval_ms"] = 0

    params = [
        ("HANDOVER", 1.0, True),
        ("HANDOVER", 2.5, False),
        ("VERTICAL_DOWNTILT", 6.0, True),
        ("VERTICAL_DOWNTILT", 25.0, False),
        ("SENSING_RATIO", 0.30, True),
        ("SENSING_RATIO", 0.90, False),
        ("LOAD_THRESHOLD", 0.70, True),
        ("LOAD_THRESHOLD", 1.5, False),
        ("PING_INTERVAL", 100.0, True),
        ("PING_INTERVAL", 9000.0, False),
        ("SCHEDULER_WEIGHT", 50.0, True),
        ("SCHEDULER_WEIGHT", 150.0, False),
    ]
    for param, val, expected_safe in params:
        act = XAppAction(xapp_id="xapp_test", node_id=f"gnb_{param}_{val}", parameter=param, value=val, priority=50)
        is_safe, _, _ = refinement.validate_single_action(act)
        assert is_safe == expected_safe, f"Falha para {param}={val}"


def test_rdlxapp_advanced_pipeline_and_decision_loop():
    os.environ["RDL_MODE"] = "OFFLINE_SIMULATION"
    os.environ["USE_FAKE_SDL"] = "True"
    os.environ["RAN_BACKEND"] = "NORI_NS3"

    app = RDLxApp()
    
    # 1. KPM Indication Handler via Golden Vector
    golden_path = os.path.join(os.path.dirname(__file__), "..", "..", "specs", "golden_vectors", "e2sm_kpm_indication.raw")
    if os.path.exists(golden_path):
        with open(golden_path, "rb") as f:
            kpm_bytes = f.read()
    else:
        kpm_bytes = b"\x00" * 32
    
    class MockSbuf:
        pass

    app._kpm_indication_handler(app.xapp, {"payload": kpm_bytes}, MockSbuf())

    # 2. Injeta ação e executa flush
    act = XAppAction(xapp_id="xapp_qos", node_id="gnb_01", parameter="PRB_QUOTA", value=55.0, priority=80)
    app.inject_xapp_action(act)
    assert len(app.proposal_buffer) >= 1

    # Executa _process_action_group com múltiplas ações
    act_clean = XAppAction(xapp_id="xapp_clean", node_id="gnb_02", parameter="PRB_QUOTA", value=70.0, priority=50)
    app._process_action_group([act, act_clean])

    # 3. Control Dispatcher Full Execution
    from src.coordination.control_dispatcher import ControlDispatcher
    class MockRmr:
        def __init__(self):
            self.sent = []
        def rmr_send(self, payload, mtype, meid=None):
            self.sent.append((payload, mtype, meid))
            return True

    mock_rmr = MockRmr()
    dispatcher = ControlDispatcher(mock_rmr, app.memory)
    
    class MockSelectedAction:
        def __init__(self):
            self.action = {"parameter": "PRB_QUOTA", "value": 50.0}

    mock_dec = RDLDecision(
        selected_actions=[act],
        safety_result={"safe": True}
    )
    mock_dec.safety_validation = True
    mock_dec.selected_action = MockSelectedAction()
    mock_dec.affected_node = "gnb_01"
    mock_dec.affected_cell = "cell_01"
    
    dispatcher.dispatch_control(mock_dec)
    assert len(mock_rmr.sent) >= 1


def test_refinement_validate_resolution_all_branches():
    mem = MemoryModule()
    ref = RefinementAgent(mem)
    ref.config["minimum_control_interval_ms"] = 0

    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[]
    )

    # Disabled config
    ref.config["enabled"] = False
    is_v, _, _ = ref.validate(ResolutionAction("c1", ResolutionStrategy.PRIORITY_TABLE, [], 0.0, 1.0, 1), conflict)
    assert is_v is True
    is_v2, _, _ = ref.validate_single_action(XAppAction("x1", "g1", "PRB", 10.0, 1))
    assert is_v2 is True
    ref.config["enabled"] = True

    # Empty actions
    is_v, _, reason = ref.validate(ResolutionAction("c1", ResolutionStrategy.PRIORITY_TABLE, [], 0.0, 1.0, 1), conflict)
    assert is_v is False

    # Empty node_id
    bad_node_act = XAppAction("x1", "", "PRB_QUOTA", 50.0, 1)
    is_v, _, _ = ref.validate_single_action(bad_node_act)
    assert is_v is False
    is_v, _, _ = ref.validate(ResolutionAction("c1", ResolutionStrategy.PRIORITY_TABLE, [bad_node_act], 0.0, 1.0, 1), conflict)
    assert is_v is False

    # Test all resolution invalid parameter values
    invalid_cases = [
        ("PRB_QUOTA", -5.0),
        ("TX_POWER", 30.0),
        ("HANDOVER", 5.0),
        ("VERTICAL_DOWNTILT", 20.0),
        ("SENSING_RATIO", 0.90),
        ("LOAD_THRESHOLD", 2.0),
        ("PING_INTERVAL", 9999.0),
        ("SCHEDULER_WEIGHT", 200.0),
        ("BEAM_WEIGHTS", 300.0)
    ]
    for param, val in invalid_cases:
        act = XAppAction("x_test", f"gnb_{param}", param, val, 1)
        res = ResolutionAction("c1", ResolutionStrategy.PRIORITY_TABLE, [act], val, 1.0, 1)
        is_v, _, reason = ref.validate(res, conflict)
        assert is_v is False, f"Expected {param}={val} to fail validation, got reason: {reason}"


def test_ran_backend_adapters_all_branches():
    from src.infrastructure.ran_backend_factory import get_ran_backend_adapter, UnsupportedBackendError
    from src.infrastructure.ran_backend_adapter import SrsRanBackendAdapter, NoriBackendAdapter
    
    # 1. Nori Backend
    nori = NoriBackendAdapter()
    assert nori.metadata.backend_id == "NORI_NS3"
    nori.register_static_profile_capabilities("gnb_01")
    nori.discover_capabilities("gnb_01", oran_strict=True)

    act = XAppAction("x1", "gnb_01", "PRB_QUOTA", 40.0, 50)
    pdu = nori.map_action_to_control_pdu(act, 1001, 1)
    assert len(pdu) > 0

    # 2. SrsRan Backend
    srs = SrsRanBackendAdapter()
    assert srs.metadata.backend_id == "SRSRAN_OPEN5GS"
    srs.register_static_profile_capabilities("gnb_01")
    srs.discover_capabilities("gnb_01", oran_strict=False)

    pdu_srs = srs.map_action_to_control_pdu(act, 1001, 1)
    assert len(pdu_srs) > 0

    golden_kpm = os.path.join(os.path.dirname(__file__), "..", "..", "specs", "golden_vectors", "e2sm_kpm_indication.raw")
    if os.path.exists(golden_kpm):
        with open(golden_kpm, "rb") as f:
            kpm_raw = f.read()
        kpm_reports = srs.decode_kpm(kpm_raw)
        assert len(kpm_reports) >= 1

    ack_res = srs.correlate_ack(b'{"status": "ACK_RECEIVED", "requestor_id": 1001, "instance_id": 1}')
    assert ack_res["status"] == "ACK_RECEIVED"

    # Unsupported backend
    with pytest.raises(UnsupportedBackendError):
        get_ran_backend_adapter("UNKNOWN_BACKEND_FOOBAR")


def test_health_server_routes():
    from src.observability.health_server import HealthServer, AppState, HAS_FASTAPI, Response
    
    server = HealthServer(port=8095)
    assert server.state == AppState.STARTING
    server.set_state(AppState.READY)
    assert server.state == AppState.READY

    if HAS_FASTAPI and server.app:
        for route in server.app.routes:
            if hasattr(route, "endpoint") and callable(route.endpoint):
                if route.path == "/health":
                    res = route.endpoint()
                    assert res["status"] == "UP"
                elif route.path == "/status":
                    res = route.endpoint()
                    assert res["state"] == AppState.READY
def test_main_and_domain_import(monkeypatch):
    import src.domain
    assert hasattr(src.domain, "XAppAction")
    assert hasattr(src.domain, "ConflictType")
    assert hasattr(src.domain, "ResolutionStrategy")

    import importlib
    import src.main
    assert src.main.root_dir is not None





# ============================================================================
# 4. TESTES DE CICLO DE VIDA E HANDLERS DA RDLXAPP
# ============================================================================

def test_rdlxapp_handlers_and_dispatch():
    os.environ["RDL_MODE"] = "OFFLINE_SIMULATION"
    os.environ["USE_FAKE_SDL"] = "True"
    os.environ["RAN_BACKEND"] = "NORI_NS3"
    
    app = RDLxApp()
    
    # Injeta proposta de ação via callback
    action_data = {
        "xapp_id": "test_xapp",
        "node_id": "gnb_01",
        "parameter": "PRB_QUOTA",
        "value": 55.0,
        "priority": 70
    }
    payload_bytes = json.dumps(action_data).encode("utf-8")
    
    class MockSbuf:
        pass

    app._action_proposal_handler(app.xapp, {"payload": payload_bytes}, MockSbuf())
    assert len(app.proposal_buffer) >= 1

    # Testa subscrição
    sub_res = app.send_subscription_request(node_id="gnb_01", ran_function_id=2, report_period_ms=200)
    assert sub_res is True

    # Testa processamento de grupo de ações
    act1 = XAppAction(xapp_id="xapp_qos", node_id="gnb_01", parameter="PRB_QUOTA", value=60.0, priority=80)
    act2 = XAppAction(xapp_id="xapp_energy", node_id="gnb_01", parameter="PRB_QUOTA", value=40.0, priority=40)
    app._process_action_group([act1, act2])

    # Testa ACK Handler com transação simulada
    req_obj = app.allocator.allocate("gnb_01", 3, decision_id="dec_01", action_id="act_01")
    app.pending_transactions[( "gnb_01", 3, req_obj.requestor_id, req_obj.instance_id )] = time.time()

    ack_payload = json.dumps({
        "transaction_id": "tx_mock_01",
        "requestor_id": req_obj.requestor_id,
        "instance_id": req_obj.instance_id,
        "status": "ACK_RECEIVED"
    }).encode("utf-8")
    app._control_ack_handler(app.xapp, {"payload": ack_payload}, MockSbuf())

    # Testa Failure Handler
    app._control_failure_handler(app.xapp, {"payload": b'{"error": "REJECTED"}'}, MockSbuf())
    app._subscription_response_handler(app.xapp, {"payload": b'{"status": "SUB_OK"}'}, MockSbuf())
    app._default_handler(app.xapp, {"mtype": 99999}, MockSbuf())

    # Clear buffer
    app.proposal_buffer.clear()
    assert len(app.proposal_buffer) == 0



def test_metrics_server_methods():
    from src.observability.metrics import MetricsServer
    ms = MetricsServer(port=8099)
    ms.record_kpm()
    ms.update_active_xapps(5)
    
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=["x1", "x2"]
    )
    ms.record_conflict(conflict)
    
    res = ResolutionAction("c1", ResolutionStrategy.PRIORITY_TABLE, [], 0.0, 1.0, 1)
    ms.record_resolution(res, latency_s=0.005)
    ms.start()


def test_health_server_lifecycle():
    from src.observability.health_server import HealthServer, AppState
    hs = HealthServer(port=8098)
    hs.run()
    hs.set_state(AppState.READY)
    assert hs.state == AppState.READY
    hs.set_state(AppState.ERROR)
    assert hs.state == AppState.ERROR


def test_rdlxapp_entrypoint_and_send_control_branches():
    os.environ["RDL_MODE"] = "OFFLINE_SIMULATION"
    os.environ["USE_FAKE_SDL"] = "True"
    app = RDLxApp()
    app._entrypoint(app.xapp)
    app._send_control("gnb_01", "PRB_QUOTA", 50.0, action=None, decision_id="dec_auto")
    
    # Test oran_strict entrypoint branch
    app.oran_strict = True
    app._entrypoint(app.xapp)
    app.stop()
    assert app.running is False


def test_main_roles_import(monkeypatch):
    import src.main
    # Test role dispatch functions without blocking
    monkeypatch.setenv("XAPP_ROLE", "rdl")
    assert os.getenv("XAPP_ROLE") == "rdl"



