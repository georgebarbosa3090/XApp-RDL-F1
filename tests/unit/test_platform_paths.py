"""Caminhos de plataforma da xApp RDL: SDL, subscrição E2 (SubMgr/RMR) e servidor de saúde."""
import json
import types

import pytest

from src.conflict_types import ConflictEvent, ConflictSeverity, ConflictType, ResolutionAction, ResolutionStrategy, XAppAction
from src.infrastructure.sdl_repository import SdlRepository
from src.observability.health_server import AppState, HealthServer


class FakeSdl:
    def __init__(self, fail=False):
        self.data = {}
        self.fail = fail

    def sdl_set(self, ns, key, value):
        if self.fail:
            raise OSError("redis down")
        self.data[(ns, key)] = value

    def sdl_get(self, ns, key):
        if self.fail:
            raise OSError("redis down")
        return self.data.get((ns, key))


# ---------------------------------------------------------------- SDL (dbaas)

def test_sdl_roundtrip_and_typed_records():
    sdl = FakeSdl()
    repo = SdlRepository()
    repo.bind_xapp(sdl, required=True)
    repo.save_control_request("c1", {"node": "gnb_0", "value": 80})
    repo.update_control_result("c1", "ACK")
    assert json.loads(sdl.data[("iqos-xapp-rdl", "control_results:c1")])["result"] == "ACK"
    repo.save_rejection("a1", {"reason": "HYSTERESIS"})
    assert repo._get("rejection:a1") == {"reason": "HYSTERESIS"}
    repo._set("plain", "texto")
    assert repo._get("plain") == "texto"                       # não-JSON volta como texto
    assert repo._get("missing") is None
    repo.record_rollback("c1", details={"why": "timeout"})
    assert repo._get("control_rollbacks:c1")["details"] == {"why": "timeout"}

    act = XAppAction("xslice", "gnb_0", "PRB_QUOTA", 80.0, 90)
    conflict = ConflictEvent(ConflictType.DIRECT, ConflictSeverity.HIGH, [act])
    repo.add_action(act)
    repo.add_conflict(conflict)
    repo.add_resolution(ResolutionAction(conflict.conflict_id, ResolutionStrategy.TVS, [act], None, 0.9, 2))
    assert repo.get_recent_actions(3)[0] is act and repo.get_similar_resolutions(conflict) == []


def test_sdl_required_fails_closed():
    repo = SdlRepository()
    with pytest.raises(RuntimeError):
        repo.bind_xapp(object(), required=True)              # cliente sem sdl_set/sdl_get
    repo._required = True
    with pytest.raises(RuntimeError):
        repo._set("k", {"v": 1})
    with pytest.raises(RuntimeError):
        repo._get("k")
    repo.bind_xapp(FakeSdl(fail=True), required=True)
    with pytest.raises(RuntimeError):
        repo._set("k", {"v": 1})
    with pytest.raises(RuntimeError):
        repo._get("k")


def test_sdl_optional_degrades_silently():
    repo = SdlRepository()
    repo._set("k", {"v": 1})                                   # sem cliente e não obrigatório: só registra
    assert repo._get("k") is None
    repo.bind_xapp(FakeSdl(fail=True), required=False)
    repo._set("k", "v")
    assert repo._get("k") is None


# ---------------------------------------------------------------- subscrição E2

@pytest.fixture
def app():
    from src.rdl_xapp import RDLxApp
    instance = RDLxApp()
    yield instance
    instance.stop()


def test_submgr_notification_success_and_failure(app):
    ctx = types.SimpleNamespace(meid="gnb_0", subscription_id="s1", error_cause="cause")
    results = iter([(ctx, True), (ctx, False), None])
    app.subscription_manager = types.SimpleNamespace(handle_notification=lambda body: next(results))
    assert app._subscription_notification_handler({}) is True
    assert app.active_subscriptions == {"gnb_0": True} and app.health.state == AppState.READY
    assert app.decision_loop_started
    assert app._subscription_notification_handler({}) is False
    assert app.active_subscriptions == {} and app.health.state == AppState.DEGRADED
    assert app._subscription_notification_handler({}) is None
    app.subscription_manager = None
    assert app._subscription_notification_handler({}) is None


def test_rmr_subscription_response_and_failure(app):
    app.decision_loop_started = True                           # não abre o laço de decisão no teste
    app._subscription_response_handler(None, {"meid": "unknown"}, None)
    assert app.health.state != AppState.READY
    app.active_subscriptions = {"gnb_0": False, "gnb_1": False}
    app._subscription_response_handler(None, {"meid": "gnb_0"}, None)
    assert app.active_subscriptions["gnb_0"] is True and app.health.state == AppState.READY
    app._subscription_failure_handler(None, {"meid": "gnb_1"}, None)
    assert "gnb_1" not in app.active_subscriptions and app.health.state == AppState.READY
    app._subscription_failure_handler(None, {}, None)          # sem meid: invalida todas
    assert app.active_subscriptions == {} and app.health.state == AppState.DEGRADED


def test_send_subscription_request_paths(app):
    accepted = types.SimpleNamespace(subscription_id="s9")
    calls = iter([accepted, None])
    app.subscription_manager = types.SimpleNamespace(
        request_kpm_subscription=lambda meid, ran_function_id, period_ms: next(calls))
    assert app.send_subscription_request("gnb_0", ran_function_id=2) is True
    assert app.active_subscriptions == {"gnb_0": False}
    assert app.send_subscription_request("gnb_1", ran_function_id=2) is False

    def boom(**_):
        raise RuntimeError("submgr down")
    app.subscription_manager = types.SimpleNamespace(request_kpm_subscription=boom)
    assert app.send_subscription_request("gnb_2", ran_function_id=2) is False


# ---------------------------------------------------------------- servidor de saúde

def test_health_endpoints():
    from fastapi.testclient import TestClient
    server = HealthServer(port=0)
    client = TestClient(server.app)
    assert client.get("/health").json()["status"] == "UP"
    assert client.get("/ready").status_code == 503
    server.set_state(AppState.READY)
    assert client.get("/ready").json()["status"] == "READY"
    assert client.get("/status").json()["state"] == "READY"
    assert client.get("/kg").status_code == 404
    assert client.get("/rejections").status_code == 404
    assert client.post("/ric/v1/subscriptions/response", content=b"{not json").status_code == 400
    assert client.post("/ric/v1/subscriptions/response", json={"x": 1}).status_code == 404
    server.subscription_callback = lambda body: True
    assert client.post("/ric/v1/subscriptions/response", json={"x": 1}).status_code == 200
    server.knowledge_graph_provider = lambda full=False: {"full": full}
    assert client.get("/kg", params={"full": "true"}).json() == {"full": True}


# ---------------------------------------------------------------- coletor de KPM bruto

def test_kpm_raw_collector_session_and_metadata(tmp_path):
    from src.e2.kpm_raw_collector import KpmRawCollector
    collector = KpmRawCollector(base_exp_dir=str(tmp_path))
    kpm_dir = collector.create_run_session("run-x", seed=7)
    req, resp = collector.save_subscription_artifacts(kpm_dir, b"\x00req", b"\x20resp")
    collector.decoder = types.SimpleNamespace(decode_indication=lambda raw: [] if raw == b"bad" else [{"ue": 1}])
    _, ok_json = collector.save_indication(kpm_dir, 1, b"good")
    _, bad_json = collector.save_indication(kpm_dir, 2, b"bad")
    assert json.loads(open(ok_json, encoding="utf-8").read())["decode_ok"] is True
    assert json.loads(open(bad_json, encoding="utf-8").read())["decode_ok"] is False
    meta = json.loads(open(collector.finalize_run_metadata(kpm_dir, seed=7, node_id="gnb_9"), encoding="utf-8").read())
    assert meta["total_indications"] == 2 and meta["node_id"] == "gnb_9" and "5g_lena_version" in meta
    assert set(meta["sha256_checksums"]) == {"subscription_request.raw", "subscription_response.raw",
                                             "indication_0001.raw", "indication_0002.raw"}
