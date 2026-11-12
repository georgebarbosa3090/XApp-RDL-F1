"""
Exportação periódica do grafo de conhecimento da RDL para o Neo4j (CronJob do chart kg-neo4j; doc 11 §6).

Só biblioteca padrão: lê ``GET $SOURCE_URL/kg?full=true`` e grava pela API HTTP transacional do Neo4j
(``POST /db/<banco>/tx/commit``), com o mesmo esquema de ``src/core/kg_export.py``: nós ``RdlNode``
com ``kind`` e arestas com o nome da relação, por ``MERGE`` (idempotente; nada é apagado, então o que
a RDL descarta da memória continua no Neo4j). Um teste (``tests/unit/test_kg_export.py``) garante que
os comandos daqui e de ``kg_export.neo4j_batches`` são os mesmos.

Variáveis: SOURCE_URL, NEO4J_HTTP, NEO4J_DATABASE, NEO4J_USER, NEO4J_PASSWORD.
"""
import base64
import json
import os
import re
import sys
import time
import urllib.request
from typing import Any, Dict, Iterable, List, Tuple

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CONSTRAINT = "CREATE CONSTRAINT rdl_node_id IF NOT EXISTS FOR (n:RdlNode) REQUIRE n.id IS UNIQUE"


def _props(item: Dict[str, Any], skip: Iterable[str]) -> Dict[str, Any]:
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


def neo4j_batches(data: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
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


def _post(url: str, user: str, password: str, statements: List[Dict[str, Any]], timeout: float = 20.0) -> Dict[str, Any]:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = urllib.request.Request(url, data=json.dumps({"statements": statements}).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "Accept": "application/json",
                                          "Authorization": f"Basic {token}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.load(resp)
    if body.get("errors"):
        raise RuntimeError(f"Neo4j recusou o comando: {body['errors'][0]}")
    return body


def export_once(source_url: str, neo4j_http: str, database: str, user: str, password: str) -> Dict[str, Any]:
    with urllib.request.urlopen(f"{source_url.rstrip('/')}/kg?full=true", timeout=15) as resp:
        data = json.load(resp)
    url = f"{neo4j_http.rstrip('/')}/db/{database}/tx/commit"
    _post(url, user, password, [{"statement": CONSTRAINT}])          # esquema em transação própria
    batches = neo4j_batches(data)
    _post(url, user, password, [{"statement": q, "parameters": p} for q, p in batches])
    return {"nodes": len(data.get("nodes", [])), "edges": len(data.get("edges", [])), "statements": len(batches)}


def main() -> int:
    env = os.environ
    started = time.time()
    try:
        summary = export_once(env.get("SOURCE_URL", "http://service-ricxapp-iqos-xapp-rdl-http.ricxapp:8080"),
                              env.get("NEO4J_HTTP", "http://kg-neo4j:7474"), env.get("NEO4J_DATABASE", "neo4j"),
                              env.get("NEO4J_USER", "neo4j"), env["NEO4J_PASSWORD"])
    except Exception as exc:
        print(json.dumps({"status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}), flush=True)
        return 1
    print(json.dumps({"status": "OK", **summary, "seconds": round(time.time() - started, 2)}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
