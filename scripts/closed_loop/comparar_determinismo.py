#!/usr/bin/env python3
# Autor: George Barbosa
"""
Teste de determinismo da malha fechada (pré-registro 11, item 5; docs/16 §9): compara cada execução com a sua
repetição na mesma semente (``<run_id>`` × ``<run_id com _rep2>``), camada por camada:

1. KPM que o ns-3 entregou em cada janela;
2. propostas das xApps;
3. decisão do baseline (ids selecionados e resoluções; ``decision_wall_ms`` é tempo de parede e fica de fora);
4. ações despachadas;
5. cadeia E2 (``e2_chain.jsonl``);
6. log de atuação e série de KPI do ns-3.

Para cada par: idêntico ou não, e a primeira janela e a camada em que divergiu (a primeira camada a divergir
indica a origem: KPM = ns-3; propostas com KPM igual = xApp; decisão com propostas iguais = RDL).

Uso: python scripts/closed_loop/comparar_determinismo.py --seed 16904 [--prefix cl_piloto_] [--out reports/avaliacao/...]
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
WALL_FIELDS = {"decision_wall_ms", "control_latency_s"}
LAYERS = ("kpm", "proposals", "decision", "actions")


def _clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items() if k not in WALL_FIELDS}
    if isinstance(obj, list):
        return [_clean(x) for x in obj]
    return obj


def _windows(run: Path) -> List[Dict[str, Any]]:
    f = run / "raw" / "closed_loop_log.jsonl"
    if not f.exists():
        return []
    return [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if '"type": "window"' in line]


def _lines(path: Path) -> Optional[List[str]]:
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else None


def compare(a: Path, b: Path) -> Dict[str, Any]:
    wa, wb = _windows(a), _windows(b)
    out: Dict[str, Any] = {"execucao": a.name, "repeticao": b.name, "janelas": (len(wa), len(wb))}
    first: Optional[Dict[str, Any]] = None
    diverged = {k: 0 for k in LAYERS}
    for i, (x, y) in enumerate(zip(wa, wb)):
        for layer in LAYERS:
            if _clean(x.get(layer)) != _clean(y.get(layer)):
                diverged[layer] += 1
                if first is None:
                    first = {"janela": i, "t": x.get("t"), "camada": layer}
    if len(wa) != len(wb) and first is None:
        first = {"janela": min(len(wa), len(wb)), "t": None, "camada": "numero_de_janelas"}
    out["janelas_divergentes"] = diverged
    out["primeira_divergencia"] = first
    for name, rel in (("cadeia_e2", "raw/e2_chain.jsonl"), ("atuacao", "raw/rdl_actuation_log.csv"),
                      ("kpi", "raw/rdl_kpi_timeseries.csv")):
        la, lb = _lines(a / rel), _lines(b / rel)
        if la is None or lb is None:
            out[name] = "ausente"
        elif name == "cadeia_e2":
            ra = [_clean(json.loads(x)) for x in la]
            rb = [_clean(json.loads(x)) for x in lb]
            out[name] = "igual" if ra == rb else f"difere ({sum(1 for p, q in zip(ra, rb) if p != q)} registros)"
        else:
            out[name] = "igual" if la == lb else f"difere ({sum(1 for p, q in zip(la, lb) if p != q)} linhas)"
    out["identico"] = (first is None and all(out[k] in ("igual", "ausente") for k in ("cadeia_e2", "atuacao", "kpi")))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", required=True)
    ap.add_argument("--prefix", default="cl_piloto_")
    ap.add_argument("--rep", default="_rep2")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    runs = ROOT / "experiments" / "runs"
    pairs = []
    for rep in sorted(runs.glob(f"{a.prefix}*{a.rep}_seed{a.seed}")):
        base = runs / rep.name.replace(a.rep, "")
        if base.exists():
            pairs.append((base, rep))
    if not pairs:
        print("nenhum par execução × repetição encontrado")
        return 1
    rows = [compare(x, y) for x, y in pairs]
    out = Path(a.out) if a.out else ROOT / "reports" / "avaliacao" / f"determinismo_seed{a.seed}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "determinismo.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [f"# Determinismo da malha fechada (semente {a.seed})", "",
          "Gerado por `scripts/closed_loop/comparar_determinismo.py`: cada execução contra a sua repetição na mesma "
          "semente. Camadas por janela: KPM, propostas, decisão (sem tempo de parede) e ações; e os arquivos da cadeia "
          "E2, da atuação e da série de KPI.", "",
          "| execução | idêntico | primeira divergência | janelas divergentes (KPM/propostas/decisão/ações) | cadeia E2 | atuação | KPI |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        f = r["primeira_divergencia"]
        fd = "—" if f is None else f"janela {f['janela']} (t={f['t']}), {f['camada']}"
        d = r["janelas_divergentes"]
        md.append(f"| {r['execucao']} | {'sim' if r['identico'] else 'não'} | {fd} | "
                  f"{d['kpm']}/{d['proposals']}/{d['decision']}/{d['actions']} | {r['cadeia_e2']} | {r['atuacao']} | {r['kpi']} |")
    ok = sum(1 for r in rows if r["identico"])
    md += ["", f"**{ok} de {len(rows)} pares idênticos.**"]
    (out / "determinismo.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
