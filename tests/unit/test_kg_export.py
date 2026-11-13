"""Exportação do grafo de conhecimento (NetworkX e Neo4j/Cypher; doc 11 §5)."""
import json

import pytest

from src.conflict_types import ConflictEvent, ConflictSeverity, ConflictType, XAppAction
from src.core.kg_export import _literal, neo4j_batches, push_neo4j, to_cypher, to_networkx
from src.core.knowledge_graph import KnowledgeGraph


def sample():
    kg = KnowledgeGraph()
    kg.add_neighbors("gnb_0", "gnb_1")
    a = XAppAction("xslice", "gnb_0", "PRB_QUOTA", 80.0, 90)
    b = XAppAction("es", "gnb_0", "PRB_QUOTA", 30.0, 65)
    c = ConflictEvent(ConflictType.DIRECT, ConflictSeverity.HIGH, [a, b])
    kg.record_conflict(c)
    kg.record_decision("d1", "TVS", [a], [c.conflict_id], policy={"energy_weight": 0.3, "critical_targets": ["es:CELL_STATE"]})
    return kg.to_dict()


def test_cypher_is_idempotent_and_complete():
    data = sample()
    stmts = to_cypher(data)
    assert stmts[0].startswith("CREATE CONSTRAINT")
    assert sum(s.startswith("MERGE (n:RdlNode") for s in stmts) == len(data["nodes"])
    assert sum(s.startswith("MATCH (a:RdlNode") for s in stmts) == len(data["edges"])
    assert any("MERGE (a)-[e:RESOLVED_BY]->(b)" in s for s in stmts)
    assert to_cypher(data) == stmts                                          # reprodutível
    assert _literal('aspas "e" \\ barra') == json.dumps('aspas "e" \\ barra')
    assert _literal(None) == "null" and _literal(True) == "true" and _literal([1, "a"]) == '[1, "a"]'


def test_neo4j_batches_group_by_relation():
    data = sample()
    batches = neo4j_batches(data)
    assert len(batches[0][1]["rows"]) == len(data["nodes"])
    rels = {q.split("[e:")[1].split("]")[0] for q, _ in batches[1:]}
    assert rels == {e["relation"] for e in data["edges"]}
    policy_rows = [r for r in batches[0][1]["rows"] if r["id"].startswith("policy:")]
    assert policy_rows[0]["props"]["critical_targets"] == ["es:CELL_STATE"]


def test_networkx_view():
    pytest.importorskip("networkx")
    data = sample()
    g = to_networkx(data)
    assert g.number_of_nodes() == len(data["nodes"]) and g.number_of_edges() == len(data["edges"])
    decision = "decision:d1"
    assert any(attrs["relation"] == "RESOLVED_BY" for _, _, attrs in g.in_edges(decision, data=True))


def test_push_neo4j_requires_driver(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "neo4j":
            raise ImportError("no neo4j")
        return real_import(name, *a, **k)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError):
        push_neo4j(sample(), "bolt://x", "u", "p")


def test_export_script_writes_cypher(tmp_path):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("export_kg", Path(__file__).resolve().parents[2] / "scripts" / "kg" / "export_kg.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    src = tmp_path / "kg.json"
    src.write_text(json.dumps(sample()), encoding="utf-8")
    out = tmp_path / "kg.cypher"
    assert mod.main(["--input", str(src), "--format", "cypher", "--out", str(out)]) == 0
    assert out.read_text(encoding="utf-8").count("MERGE") > 5
    gml = tmp_path / "kg.graphml"
    if pytest.importorskip("networkx"):
        assert mod.main(["--input", str(src), "--format", "graphml", "--out", str(gml)]) == 0 and gml.stat().st_size > 0


def _job_module():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "deploy" / "helm" / "kg-neo4j" / "files" / "export_kg_job.py"
    spec = importlib.util.spec_from_file_location("export_kg_job", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cronjob_exporter_matches_library_schema():
    """O exportador do CronJob (só stdlib) gera os mesmos comandos que src/core/kg_export.py."""
    job = _job_module()
    data = sample()
    assert job.neo4j_batches(data) == neo4j_batches(data)


def test_cronjob_exporter_posts_to_neo4j_http_api():
    import base64
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    job = _job_module()
    data = sample()
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = json.dumps(data).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append((self.path, self.headers["Authorization"], payload))
            fail = any("BOOM" in s["statement"] for s in payload["statements"])
            body = json.dumps({"results": [], "errors": [{"message": "x"}] if fail else []}).encode()
            self.send_response(200); self.end_headers(); self.wfile.write(body)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    try:
        summary = job.export_once(base, base, "neo4j", "neo4j", "segredo")
        assert summary == {"nodes": len(data["nodes"]), "edges": len(data["edges"]), "statements": len(neo4j_batches(data))}
        (p1, auth, first), (p2, _, second) = seen
        assert p1 == p2 == "/db/neo4j/tx/commit"
        assert auth == "Basic " + base64.b64encode(b"neo4j:segredo").decode()
        assert first["statements"] == [{"statement": job.CONSTRAINT}]          # esquema em transação própria
        assert len(second["statements"]) == len(neo4j_batches(data))
        with pytest.raises(RuntimeError):
            job._post(f"{base}/db/neo4j/tx/commit", "neo4j", "x", [{"statement": "BOOM"}])
    finally:
        srv.shutdown()


def test_cronjob_exporter_main_reports_failure(monkeypatch, capsys):
    job = _job_module()
    monkeypatch.setenv("SOURCE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("NEO4J_PASSWORD", "x")
    assert job.main() == 1
    assert '"status": "FAILED"' in capsys.readouterr().out
