#!/usr/bin/env python3
"""
Pós-renderizador Helm para os charts ric-dep da Release I em Kubernetes >= 1.22 (k3s 1.26).

Os charts da Release I ainda usam APIs removidas no Kubernetes 1.22:
  - rbac.authorization.k8s.io/v1beta1 -> trocado por rbac.authorization.k8s.io/v1 (mesmo esquema);
  - Ingress networking.k8s.io/v1beta1 -> removido: só expõe as APIs pelo Kong, que não é implantado
    e não participa da cadeia E2 (os componentes se falam por Services internos e RMR).
Os charts oficiais não são alterados. Cada alteração é registrada em stderr.

Empacotado como plugin postrenderer/v1 do Helm 4 (plugin.yaml ao lado), usado por
scripts/deploy_ric_i_release.sh:
  helm plugin install deploy/ric/helm-postrenderer
  helm upgrade --install ... --post-renderer ric-k8s122
Só usa a biblioteca padrão (roda com o python3 do sistema).
"""

import re
import sys

RBAC_OLD = "rbac.authorization.k8s.io/v1beta1"
RBAC_NEW = "rbac.authorization.k8s.io/v1"


def transform(manifest: str):
    kept, log = [], []
    for doc in re.split(r"(?m)^---[ \t]*$", manifest):
        body = doc.strip("\n")
        if not body.strip():
            continue
        kind = re.search(r"(?m)^kind:\s*(\S+)", body)
        name = re.search(r"(?m)^  name:\s*(\S+)", body)
        label = f"{kind.group(1) if kind else '?'}/{name.group(1) if name else '?'}"
        if kind and kind.group(1) == "Ingress":
            log.append(f"removido {label} (Ingress v1beta1; Kong não implantado)")
            continue
        if RBAC_OLD in body:
            body = body.replace(RBAC_OLD, RBAC_NEW)
            log.append(f"apiVersion {RBAC_OLD} -> {RBAC_NEW} em {label}")
        kept.append(body)
    return "".join(f"---\n{b}\n" for b in kept), log


def main() -> int:
    out, log = transform(sys.stdin.read())
    for line in log:
        print(f"[post-renderer] {line}", file=sys.stderr)
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
