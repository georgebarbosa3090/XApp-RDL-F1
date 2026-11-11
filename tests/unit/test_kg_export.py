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
    assert to_cypher(data) == stmts                                          # determinístico
    assert _literal('aspas "e" \ barra') == json.dumps('aspas "e" \ barra')
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
