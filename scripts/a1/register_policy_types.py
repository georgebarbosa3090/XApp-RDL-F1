#!/usr/bin/env python3
"""
Registra no A1 Mediator do Near-RT RIC os tipos de política que a xApp RDL trata (doc 10 §1).

Uso (de dentro do cluster ou com port-forward do A1 Mediator):
    python scripts/a1/register_policy_types.py --a1-url http://service-ricplt-a1mediator-http.ricplt:10000
    python scripts/a1/register_policy_types.py --dry-run      # só imprime as definições

Os esquemas vêm de ``src/interfaces/a1_policy_receiver.py`` (fonte única); a definição segue o
formato do A1 Mediator do O-RAN SC: ``PUT /A1-P/v2/policytypes/{policy_type_id}``.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.interfaces.a1_policy_receiver import A1PolicyManager  # noqa: E402
from src.interfaces.a1_rmr import policy_type_definitions  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--a1-url", default="http://service-ricplt-a1mediator-http.ricplt:10000")
    p.add_argument("--types", nargs="*", help="só estes tipos (padrão: todos)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    definitions = policy_type_definitions(A1PolicyManager())
    if args.types:
        definitions = [d for d in definitions if str(d["policy_type_id"]) in set(args.types)]
    if args.dry_run:
        print(json.dumps(definitions, indent=2, ensure_ascii=False))
        return 0

    import requests

    failures = 0
    for definition in definitions:
        url = f"{args.a1_url.rstrip('/')}/A1-P/v2/policytypes/{definition['policy_type_id']}"
        current = requests.get(url, timeout=10)
        if current.status_code == 200:
            stored = current.json()
            if stored.get("create_schema") == definition["create_schema"] and stored.get("name") == definition["name"]:
                print(f"OK   {definition['policy_type_id']} {definition['name']}: já registrado, igual")
                continue
            # Tipo diferente do esquema atual: o mediador só aceita substituir sem instâncias
            requests.delete(url, timeout=10)
        resp = requests.put(url, json=definition, timeout=10)
        ok = resp.status_code in (200, 201)
        failures += 0 if ok else 1
        print(f"{'OK  ' if ok else 'ERRO'} {definition['policy_type_id']} {definition['name']}: HTTP {resp.status_code} {resp.text[:200]}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
