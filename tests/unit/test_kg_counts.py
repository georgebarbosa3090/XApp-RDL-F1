"""Contagem de consultas e escritas no grafo de conhecimento (painel de campanha, docs/16 §10.4)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "certification"))

from src.core.knowledge_graph import KnowledgeGraph  # noqa: E402


def test_public_calls_are_counted_once():
    g = KnowledgeGraph()
    g.add_cell("c1")                    # escrita pública (add_node interno não conta de novo)
    g.add_neighbors("c1", "c2")
    g.neighbors("c1")
    g.context_features("c1", "TX_POWER")
    assert g.op_totals() == {"queries": 2, "writes": 2}


def test_decision_entry_reports_kg_delta():
    import run_conflict_experiment as rce
    s = rce.HrdlStream()
    try:
        _, entry = s.decide([{"xapp_id": "a", "gnb": 0, "parameter": "TX_POWER", "value": 30, "priority": 80, "id": "x1"},
                             {"xapp_id": "b", "gnb": 0, "parameter": "PRB_QUOTA", "value": 40, "priority": 70, "id": "x2"}], 1.0)
    finally:
        s.close()
    assert entry["kg_writes"] > 0 and entry["kg_queries"] >= 0
