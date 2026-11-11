"""
Exportação do grafo de conhecimento da RDL (``KnowledgeGraph.to_dict`` ou ``GET /kg?full=true``).

Onde cada ferramenta atua (doc 11 §5):

- **No Near-RT RIC, dentro da RDL:** o grafo próprio, em memória e sem dependência externa
  (``src/core/knowledge_graph.py``), consultado a cada decisão. Nada aqui entra no caminho de decisão.
- **NetworkX** (``to_networkx``): análise fora do laço — centralidade das células, componentes,
  caminhos de conflito — num notebook, num teste ou no rApp. Opcional (``pip install networkx``).
- **Neo4j** (``to_cypher`` / ``push_neo4j``): histórico persistente no SMO/Non-RT RIC, que sobrevive
  ao reinício da RDL e é consultado pelos rApps. Opcional (``pip install neo4j``).

Todos os nós recebem o rótulo ``RdlNode`` e a propriedade ``kind`` (cell, xapp, action, conflict,
decision, policy, parameter); as arestas mantêm o nome da relação (TARGETS, PROPOSED, INVOLVES,
RESOLVED_BY, SELECTED, GOVERNS, NEIGHBOR...).
"""

import json
import re
from typing import Any, Dict, Iterable, List, Tuple

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _props(item: Dict[str, Any], skip: Iterable[str]) -> Dict[str, Any]:
    """Propriedades primitivas (listas de primitivos são aceitas; o resto vira texto JSON)."""
    out: Dict[str, Any] = {}
    for key, value in item.items():
        if key in skip:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            out[key] = value
        elif isinstance(value, (list, tuple)) and all(isinstance(v, (str, int, float, bool)) for v in value):
            out[key] = list(value)
        else:
            out[key] = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return out


def to_networkx(data: Dict[str, Any]):
    """``networkx.MultiDiGraph`` com os atributos dos nós e o nome da relação em ``relation``."""
    try:
        import networkx as nx
    except ImportError as exc:  # dependência opcional
        raise ImportError("networkx não instalado: pip install networkx") from exc
    g = nx.MultiDiGraph(schema=data.get("schema"))
    for node in data.get("nodes", []):
        g.add_node(node["id"], **_props(node, ("id",)))
    for edge in data.get("edges", []):
        g.add_edge(edge["src"], edge["dst"], key=edge["relation"], relation=edge["relation"],
                   **_props(edge, ("src", "dst", "relation")))
    return g


def _literal(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(_literal(v) for v in value) + "]"
    return json.dumps(str(value), ensure_ascii=False)


def _map(props: Dict[str, Any]) -> str:
    parts = []
    for key, value in sorted(props.items()):
        name = key if _IDENT.match(key) else "`" + key.replace("`", "") + "`"
        parts.append(f"{name}: {_literal(value)}")
    return "{" + ", ".join(parts) + "}"


def to_cypher(data: Dict[str, Any]) -> List[str]:
    """Comandos Cypher idempotentes (MERGE) que reproduzem o grafo no Neo4j."""
    stmts = ["CREATE CONSTRAINT rdl_node_id IF NOT EXISTS FOR (n:RdlNode) REQUIRE n.id IS UNIQUE;"]
    for node in sorted(data.get("nodes", []), key=lambda n: n["id"]):
        stmts.append(f"MERGE (n:RdlNode {{id: {_literal(node['id'])}}}) SET n += {_map(_props(node, ('id',)))};")
    for edge in sorted(data.get("edges", []), key=lambda e: (e["relation"], e["src"], e["dst"])):
        rel = edge["relation"] if _IDENT.match(edge["relation"]) else "RELATED"
        stmts.append(
            f"MATCH (a:RdlNode {{id: {_literal(edge['src'])}}}), (b:RdlNode {{id: {_literal(edge['dst'])}}}) "
            f"MERGE (a)-[e:{rel}]->(b) SET e += {_map(_props(edge, ('src', 'dst', 'relation')))};")
    return stmts


def neo4j_batches(data: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """Comandos parametrizados (UNWIND) para o driver do Neo4j: um para os nós e um por relação."""
    nodes = [{"id": n["id"], "props": _props(n, ("id",))} for n in data.get("nodes", [])]
    out = [("UNWIND $rows AS r MERGE (n:RdlNode {id: r.id}) SET n += r.props", {"rows": nodes})]
    by_rel: Dict[str, List[Dict[str, Any]]] = {}
    for e in data.get("edges", []):
        rel = e["relation"] if _IDENT.match(e["relation"]) else "RELATED"
        by_rel.setdefault(rel, []).append({"src": e["src"], "dst": e["dst"],
                                           "props": _props(e, ("src", "dst", "relation"))})
    for rel, rows in sorted(by_rel.items()):
        out.append((f"UNWIND $rows AS r MATCH (a:RdlNode {{id: r.src}}), (b:RdlNode {{id: r.dst}}) "
                    f"MERGE (a)-[e:{rel}]->(b) SET e += r.props", {"rows": rows}))
    return out


def push_neo4j(data: Dict[str, Any], uri: str, user: str, password: str, database: str = "neo4j") -> int:
    """Grava o grafo no Neo4j; devolve o número de comandos executados."""
    try:
        from neo4j import GraphDatabase
    except ImportError as exc:  # dependência opcional
        raise ImportError("driver neo4j não instalado: pip install neo4j") from exc
    batches = neo4j_batches(data)
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        with driver.session(database=database) as session:
            session.run("CREATE CONSTRAINT rdl_node_id IF NOT EXISTS FOR (n:RdlNode) REQUIRE n.id IS UNIQUE")
            for query, params in batches:
                session.run(query, params)
    return len(batches) + 1
