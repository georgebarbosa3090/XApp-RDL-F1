#!/usr/bin/env python3
"""
Curva teto -> vazão por fatia (desenho v4, docs/07_preregistro_fase4_v4.md).

Cada execução da curva aplica, por RIC Control, o MESMO teto às duas fatias (ex.: 10/10). A soma das
cotas não alterou o efeito nas calibrações v2/v3 (30/30, 30/70 e 70/30 deram o mesmo resultado), então
cada execução mede um ponto da curva para as duas fatias. Execuções com tetos diferentes por fatia
(como as calibrações v3) contribuem só com o ponto de cada fatia no seu próprio teto.

Para cada fatia e nível: vazão antes e depois do Control (janelas de ``slice_effect.py``, tetos lidos
dos bytes do Control no PCAP). A curva é válida se, por fatia, a vazão depois não cresce ao baixar o
teto (monotonicidade, com tolerância de QUEDA_MIN) e se ao menos uma fatia tem um nível que restringe.

Saída: ``experiments/calibration/slice_cap_curve_v4.json`` com hashes das séries e dissecações.

Uso:
    python scripts/certification/slice_cap_curve.py --run nori_curve10_seed301 --run nori_curve15_seed302 \\
        --run nori_curve20_seed303 --run nori_curve25_seed304 --run nori_cal3070_seed201 \\
        --run nori_cal7030_seed202 --out experiments/calibration/slice_cap_curve_v4.json
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("slice_effect", Path(__file__).with_name("slice_effect.py"))
fx = importlib.util.module_from_spec(_spec)
sys.modules["slice_effect"] = fx
_spec.loader.exec_module(fx)


def run_points(run_id: str, runs_dir: Path, dissection_root: Path) -> Dict[str, Any]:
    run_dir, ddir = runs_dir / run_id, dissection_root / run_id
    csv_path, diss_path = run_dir / "raw" / "slice_series.csv", ddir / "e2_messages.json"
    entry: Dict[str, Any] = {"run_id": run_id, "source_csv": f"experiments/runs/{run_id}/raw/slice_series.csv",
                             "source_csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
                             "source_dissection_sha256": hashlib.sha256(diss_path.read_bytes()).hexdigest(),
                             "points": {}}
    ctrl, quotas = fx.control_quotas(json.loads(diss_path.read_text(encoding="utf-8")), ddir)
    if not ctrl:
        entry["error"] = "sem RIC Control na cadeia do PCAP"
        return entry
    series = fx.load_series(csv_path)
    t_c = fx.wall_to_sim(series, float(ctrl["time_epoch"]))
    if t_c is None:
        entry["error"] = "instante do Control fora da série"
        return entry
    caps = {int(q["sst"]): float(q["max_prb_ratio"]) for q in quotas}
    before_w = (t_c - fx.WINDOW_S, t_c)
    after_w = (t_c + fx.SETTLE_S, t_c + fx.SETTLE_S + fx.WINDOW_S)
    entry.update(quotas_from_pcap=quotas, control_sim_time_s=t_c, window_before=before_w, window_after=after_w)
    for sst, rows in sorted(series.items()):
        b, a = fx.throughput_mbps(rows, *before_w), fx.throughput_mbps(rows, *after_w)
        if b is None or a is None or sst not in caps:
            continue
        entry["points"][str(sst)] = {"cap_max_prb_pct": caps[sst], "throughput_before_mbps": round(b, 3),
                                     "throughput_after_mbps": round(a, 3), "relative_change": round((a - b) / b, 4),
                                     "binding": (a - b) / b <= -fx.MIN_DROP}
    return entry


def build_curve(run_ids: List[str], out: Path, runs_dir: Path = ROOT / "experiments" / "runs",
                dissection_root: Path = ROOT / "experiments" / "e2_dissection") -> Dict[str, Any]:
    runs = [run_points(r, runs_dir, dissection_root) for r in run_ids]
    curve: Dict[str, List[Dict[str, Any]]] = {}
    problems: List[str] = [f"{r['run_id']}: {r['error']}" for r in runs if r.get("error")]
    for r in runs:
        for sst, p in r["points"].items():
            curve.setdefault(sst, []).append({"run_id": r["run_id"], **p})
    for sst, pts in curve.items():
        pts.sort(key=lambda p: p["cap_max_prb_pct"])
        caps = [p["cap_max_prb_pct"] for p in pts]
        if len(set(caps)) != len(caps):
            problems.append(f"SST {sst}: nível de teto repetido {caps}")
        for lo, hi in zip(pts, pts[1:]):
            if lo["throughput_after_mbps"] > hi["throughput_after_mbps"] * (1 + fx.MIN_DROP):
                problems.append(f"SST {sst}: curva não monotônica entre {lo['cap_max_prb_pct']:.0f} % e "
                                f"{hi['cap_max_prb_pct']:.0f} %")
    if not any(p["binding"] for pts in curve.values() for p in pts):
        problems.append("nenhum nível restringe nenhuma fatia")
    result: Dict[str, Any] = {
        "schema": "xapp-rdl/slice-cap-curve/v1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scripts/certification/slice_cap_curve.py",
        "constants": {"window_s": fx.WINDOW_S, "settle_s": fx.SETTLE_S, "min_drop": fx.MIN_DROP},
        "runs": runs, "curve": curve, "valid": not problems,
    }
    if problems:
        result["reason"] = "; ".join(problems)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True, action="append")
    parser.add_argument("--out", default=str(ROOT / "experiments" / "calibration" / "slice_cap_curve_v4.json"))
    args = parser.parse_args(argv)
    r = build_curve(args.run, Path(args.out))
    print(f"Curva teto -> vazão: {'VÁLIDA' if r['valid'] else 'INVÁLIDA'}" + (f" — {r['reason']}" if r.get("reason") else ""))
    for sst, pts in sorted(r["curve"].items()):
        print(f"  SST {sst}: " + "; ".join(f"{p['cap_max_prb_pct']:.0f} % -> {p['throughput_after_mbps']:.2f} Mb/s"
                                          f"{' (restringe)' if p['binding'] else ''}" for p in pts))
    print(f"Saída: {args.out}")
    return 0 if r["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
