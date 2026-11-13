#!/usr/bin/env python3
"""
Resumo da campanha dos cenários de conflito na bancada NORI (``scripts/run_nori_campaign.sh``).

Para cada execução ``nori_S<k>_B3_seed<N>``: cadeia E2 identificada no PCAP (papéis), concordância
do tshark, Indications casadas com a xApp, decisão do RDL-N1 (estratégias, ações selecionadas,
atuadas e não atuáveis no NORI), Control/ACK, efeito na RAN (``slice_effect.json``) e o veredito
do certificador por execução. Saída: ``reports/nori/resumo_campanha_nori_<UTC>.md``.

Com ``slice_effect_v6.json`` (regra v6, docs/preregistros/05_fase4_v6.md), mostra também o veredito v6.

Uso:
    python scripts/certification/nori_campaign_summary.py
    python scripts/certification/nori_campaign_summary.py --seeds 2001-2005    # só essas sementes
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
RUN_RE = re.compile(r"^nori_(S[0-8])_(B[0-3])((?:_[a-z0-9]+)*)_seed(\d+)$")
ROLES = ("e2_setup", "subscription", "kpm_t0", "control_request", "control_ack", "kpm_t1")


def load(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def control_decision(run_id: str) -> Optional[Dict[str, Any]]:
    events = ROOT / "experiments" / "xapp_logs" / run_id / "kpm_probe_events.jsonl"
    if not events.exists():
        return None
    found = None
    for line in events.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("event") in ("control_request", "control_decision") and ev.get("decision"):
            found = ev
    return found


def row(run_id: str, scenario: str, seed: str, baseline: str = "B3") -> Dict[str, Any]:
    ddir = ROOT / "experiments" / "e2_dissection" / run_id
    diss = load(ddir / "e2_messages.json") or {}
    eff = load(ddir / "slice_effect.json") or {}
    eff6 = load(ddir / "slice_effect_v6.json") or {}
    ev = control_decision(run_id) or {}
    dec = ev.get("decision") or {}
    roles = diss.get("chain_roles") or {}
    x = diss.get("xapp_crosscheck") or {}
    return {
        "run": run_id, "scenario": scenario, "seed": int(seed), "baseline": baseline,
        "source": ev.get("decision_source") or dec.get("decision_source") or "—",
        "roles": "".join("✓" if roles.get(r) else "·" for r in ROLES),
        "tshark": (diss.get("tshark_comparison") or {}).get("agreement"),
        "messages": diss.get("message_count"),
        "ind": f"{x.get('pcap_indications_received_by_xapp')}/{x.get('pcap_indications')}" if x else "—",
        "strategies": ",".join(r["strategy"] for r in dec.get("resolutions", [])) or "PASS_THROUGH",
        "actuated": (f"{dec['actuated']['xapp_id']} → eMBB {dec['quotas'][0]['max_prb_ratio']} / URLLC "
                     f"{dec['quotas'][1]['max_prb_ratio']}" if dec.get("actuated") else "—"),
        "not_actuated": "; ".join(f"{s['xapp_id']} {s['parameter']} {s['target'].rsplit('#', 1)[-1]}"
                                  for s in dec.get("not_actuated", [])) or "—",
        "blocked": ", ".join(dec.get("not_selected", [])) or "—",
        "effect": eff.get("verdict", "—"),
        "effect_v6": eff6.get("verdict", "—"),
    }


def parse_seeds(spec: Optional[str]) -> Optional[set]:
    if not spec:
        return None
    out = set()
    for part in spec.replace(",", " ").split():
        lo, _, hi = part.partition("-")
        out.update(range(int(lo), int(hi or lo) + 1))
    return out


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", help="sementes a incluir, ex.: 2001-2005 ou '1001 1003'")
    ap.add_argument("--tag", default="", help="condição do run_id (ex.: _bw50); vazio = condição padrão")
    ap.add_argument("--baselines", default="B3", help="baselines a incluir, ex.: 'B0 B1 B2 B3' (padrão: B3)")
    args = ap.parse_args(argv)
    seeds = parse_seeds(args.seeds)
    runs = []
    for d in sorted((ROOT / "experiments" / "runs").iterdir()):
        m = RUN_RE.match(d.name)
        if (m and (d / "hashes.sha256").exists() and m.group(3) == args.tag
                and m.group(2) in args.baselines.replace(",", " ").split()
                and (seeds is None or int(m.group(4)) in seeds)):
            runs.append(row(d.name, m.group(1), m.group(4), m.group(2)))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [f"# Campanha NORI: cenários de conflito com E2 real ({stamp})", "",
             "Gerado por `scripts/certification/nori_campaign_summary.py`. Papéis da cadeia na ordem "
             "E2 Setup, Subscription, KPM_t0, Control, ACK, KPM_t1 (✓ presente no PCAP, · ausente). "
             "Só PRB_QUOTA no gNB 0 é atuável no NORI; potência, handover e ações em outros gNBs são decididas "
             "pelo RDL-N1 e registradas, sem Control.", "",
             "| Execução | Baseline (fonte da decisão) | Cadeia | tshark | Msgs | Indications xApp | Estratégias RDL-N1 | "
             "Atuado (E2SM-RC) | Decidido, não atuável no NORI | Não selecionadas | Efeito (certificador) | Efeito v6 |",
             "| :-- | :-: | :-: | :-: | --: | :-: | :-- | :-- | :-- | :-- | :-: | :-: |"]
    for r in runs:
        lines.append(f"| `{r['run']}` | {r['baseline']} ({r['source']}) | {r['roles']} | {'✓' if r['tshark'] else '✗'} | "
                     f"{r['messages']} | {r['ind']} | {r['strategies'] if r['baseline'] == 'B3' else '—'} | {r['actuated']} | "
                     f"{r['not_actuated']} | {r['blocked']} | {r['effect']} | {r['effect_v6']} |")
    by_sc: Dict[str, List[Dict[str, Any]]] = {}
    for r in runs:
        by_sc.setdefault(r["scenario"], []).append(r)
    lines += ["", "## Por cenário", "", "| Cenário | Execuções | Cadeia completa | Efeito CONSISTENT | Efeito v6 CONSISTENT |", "| :-: | --: | --: | --: | --: |"]
    for sc, rs in sorted(by_sc.items()):
        lines.append(f"| {sc} | {len(rs)} | {sum(r['roles'] == '✓' * 6 for r in rs)} | "
                     f"{sum(r['effect'] == 'CONSISTENT' for r in rs)} | {sum(r['effect_v6'] == 'CONSISTENT' for r in rs)} |")
    by_b: Dict[str, List[Dict[str, Any]]] = {}
    for r in runs:
        by_b.setdefault(r["baseline"], []).append(r)
    if len(by_b) > 1:
        lines += ["", "## Por baseline", "", "| Baseline | Execuções | Cadeia completa | Efeito CONSISTENT | Efeito v6 CONSISTENT |",
                  "| :-: | --: | --: | --: | --: |"]
        for b, rs in sorted(by_b.items()):
            lines.append(f"| {b} | {len(rs)} | {sum(r['roles'] == '✓' * 6 for r in rs)} | "
                         f"{sum(r['effect'] == 'CONSISTENT' for r in rs)} | {sum(r['effect_v6'] == 'CONSISTENT' for r in rs)} |")
    out = ROOT / "reports" / "nori" / f"resumo_campanha_nori_{stamp}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    print("\n".join(lines[-(len(by_sc) + 2 + ((len(by_b) + 4) if len(by_b) > 1 else 0)):]))
    print(f"Resumo: {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
