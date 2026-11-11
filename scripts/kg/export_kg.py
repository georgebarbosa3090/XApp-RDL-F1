#!/usr/bin/env python3
"""
Exporta o grafo de conhecimento da RDL (doc 11 §5).

Fonte: ``GET /kg?full=true`` da RDL (``--rdl-url``) ou um arquivo JSON (``--input``).
Saída: JSON, Cypher (``.cypher``, para ``cypher-shell``), GraphML (via NetworkX) ou gravação direta
no Neo4j (``--neo4j-uri``; usuário em ``--neo4j-user``, senha só pela variável ``NEO4J_PASSWORD``).

Exemplos:
    python scripts/kg/export_kg.py --rdl-url http://localhost:8080 --format cypher --out kg.cypher
    python scripts/kg/export_kg.py --input kg.json --format graphml --out kg.graphml
    NEO4J_PASSWORD=... python scripts/kg/export_kg.py --rdl-url http://localhost:8080 --neo4j-uri bolt://neo4j.smo:7687
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.core.kg_export import push_neo4j, to_cypher, to_networkx  # noqa: E402


def load(args) -> dict:
    if args.input:
        return json.loads(Path(args.input).read_text(encoding="utf-8"))
    with urllib.request.urlopen(f"{args.rdl_url.rstrip('/')}/kg?full=true", timeout=15) as resp:
        return json.load(resp)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--rdl-url")
    src.add_argument("--input")
    p.add_argument("--format", choices=("json", "cypher", "graphml"), default="json")
    p.add_argument("--out", help="arquivo de saída (padrão: saída padrão)")
    p.add_argument("--neo4j-uri")
    p.add_argument("--neo4j-user", default="neo4j")
    p.add_argument("--neo4j-database", default="neo4j")
    args = p.parse_args(argv)

    data = load(args)
    print(f"grafo: {len(data.get('nodes', []))} nós, {len(data.get('edges', []))} arestas", file=sys.stderr)
    if args.neo4j_uri:
        password = os.environ.get("NEO4J_PASSWORD")
        if not password:
            p.error("defina NEO4J_PASSWORD para gravar no Neo4j")
        n = push_neo4j(data, args.neo4j_uri, args.neo4j_user, password, args.neo4j_database)
        print(f"Neo4j: {n} comandos executados", file=sys.stderr)
        return 0
    if args.format == "graphml":
        import networkx as nx
        g = to_networkx(data)
        for _, _, attrs in g.edges(data=True):          # GraphML não aceita listas
            for k, v in list(attrs.items()):
                if isinstance(v, list):
                    attrs[k] = json.dumps(v)
        for _, attrs in g.nodes(data=True):
            for k, v in list(attrs.items()):
                if isinstance(v, list):
                    attrs[k] = json.dumps(v)
        if not args.out:
            p.error("--format graphml exige --out")
        nx.write_graphml(g, args.out)
        return 0
    text = "\n".join(to_cypher(data)) + "\n" if args.format == "cypher" else json.dumps(data, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
