#!/usr/bin/env python3
"""
Grafo de conhecimento produzido pelo H-RDL real (B3, ``RDLxApp._process_action_group``) ao decidir as
propostas dos cenários do catálogo, gravado em JSON (formato de ``GET /kg?full=true``).

Serve de fonte de teste para a exportação ao Neo4j na bancada sem RDL implantada (chart kg-neo4j,
``testSource``). Não é evidência experimental: os cenários são decididos em sequência, sem ns-3, e
as células de cenários diferentes têm os mesmos nomes (``gnb_0``...), então se fundem no grafo.

Uso:
    python scripts/kg/dump_catalog_kg.py --out kg_catalogo.json                # todos os cenários com ns-3
    python scripts/kg/dump_catalog_kg.py --scenarios S2 S4 S13 G2 --out kg.json
"""
import argparse
import importlib.util
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _driver():
    spec = importlib.util.spec_from_file_location("run_conflict_experiment",
                                                  ROOT / "scripts/certification/run_conflict_experiment.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_conflict_experiment"] = mod
    spec.loader.exec_module(mod)
    return mod


def dump(scenarios, catalog) -> dict:
    import src.rdl_xapp as rx
    drv = _driver()
    captured = []
    original = rx.RDLxApp

    class Capturing(original):  # registra cada RDLxApp criada pelo B3 para ler o grafo depois
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            captured.append(self)

    rx.RDLxApp = Capturing
    try:
        for sid in scenarios:
            drv.decide(sid, "B3", catalog)
    finally:
        rx.RDLxApp = original
    nodes, edges = {}, {}
    for app in captured:
        data = app.knowledge_graph.to_dict()
        for n in data["nodes"]:
            nodes.setdefault(n["id"], {}).update(n)
        for e in data["edges"]:
            edges[(e["src"], e["relation"], e["dst"])] = e
    return {"schema": "xapp-rdl/knowledge-graph/v1", "source": "scripts/kg/dump_catalog_kg.py (B3 sobre o catálogo)",
            "scenarios": list(scenarios), "nodes": list(nodes.values()), "edges": list(edges.values())}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scenarios", nargs="+")
    p.add_argument("--out", required=True)
    args = p.parse_args(argv)
    catalog = json.loads((ROOT / "simulations/ns3/conflicts/catalog.json").read_text(encoding="utf-8"))
    scenarios = args.scenarios or sorted(s for s, spec in catalog["scenarios"].items() if spec.get("ns3"))
    logging.disable(logging.WARNING)
    data = dump(scenarios, catalog)
    logging.disable(logging.NOTSET)
    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"{args.out}: {len(data['nodes'])} nós, {len(data['edges'])} arestas, cenários {', '.join(scenarios)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
