#!/usr/bin/env python3
"""
Calibração da capacidade por fatia (pré-registro docs/07_preregistro_fase4_v2.md).

A partir de uma execução de calibração (Control com teto fixo e RESTRITIVO nas fatias, ex. 30/30),
estima k_s = vazão_depois_s / teto_s, em Mb/s por ponto percentual de PRB. Usa as mesmas janelas e
a mesma conversão de tempo de ``slice_effect.py`` e lê os tetos dos bytes do Control no PCAP.

A calibração só é válida se o teto restringiu cada fatia: a vazão de todas caiu ao menos QUEDA_MIN
entre as janelas. Sem isso, k_s não mede a capacidade por PRB e a regra v2 não pode ser aplicada.

Saída: ``experiments/calibration/<nome>.json`` com hashes da série e da dissecação de origem.

Modo de cotas complementares (desenho v3, docs/07_preregistro_fase4_v3.md): várias execuções, cada uma
com cotas que somam 100 % (ex.: 30/70 e 70/30). Em cada execução só a fatia de MENOR teto é calibrada
(k_s = vazão depois ÷ teto), e ela precisa ter caído ao menos QUEDA_MIN; a de teto maior não entra. A
calibração é válida quando cada fatia recebe exatamente um k válido.

Uso:
    python scripts/certification/calibrate_slice_capacity.py --run nori_cal30_seed101 \\
        --out experiments/calibration/slice_capacity_v2.json
    python scripts/certification/calibrate_slice_capacity.py --complementary \\
        --run nori_cal3070_seed201 --run nori_cal7030_seed202 --out experiments/calibration/slice_capacity_v3.json
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


def calibrate(run_id: str, out: Path, runs_dir: Path = ROOT / "experiments" / "runs",
              dissection_root: Path = ROOT / "experiments" / "e2_dissection") -> Dict[str, Any]:
    run_dir, ddir = runs_dir / run_id, dissection_root / run_id
    csv_path = run_dir / "raw" / "slice_series.csv"
    diss_path = ddir / "e2_messages.json"
    dissection = json.loads(diss_path.read_text(encoding="utf-8"))
    ctrl, quotas = fx.control_quotas(dissection, ddir)
    result: Dict[str, Any] = {
        "schema": "xapp-rdl/slice-capacity-calibration/v1", "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scripts/certification/calibrate_slice_capacity.py",
        "constants": {"window_s": fx.WINDOW_S, "settle_s": fx.SETTLE_S, "min_drop": fx.MIN_DROP},
        "source_csv": f"experiments/runs/{run_id}/raw/slice_series.csv",
        "source_csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "source_dissection_sha256": hashlib.sha256(diss_path.read_bytes()).hexdigest(),
        "quotas_from_pcap": quotas, "valid": False,
    }
    if not ctrl:
        result["reason"] = "execução sem RIC Control na cadeia do PCAP"
    else:
        series = fx.load_series(csv_path)
        t_c = fx.wall_to_sim(series, float(ctrl["time_epoch"]))
        result["control_sim_time_s"] = t_c
        caps = {int(q["sst"]): float(q["max_prb_ratio"]) for q in quotas}
        if t_c is None:
            result["reason"] = "instante do Control fora da série"
        else:
            before_w = (t_c - fx.WINDOW_S, t_c)
            after_w = (t_c + fx.SETTLE_S, t_c + fx.SETTLE_S + fx.WINDOW_S)
            slices: Dict[str, Dict[str, Any]] = {}
            k: Dict[str, float] = {}
            valid = True
            for sst, rows in sorted(series.items()):
                b, a = fx.throughput_mbps(rows, *before_w), fx.throughput_mbps(rows, *after_w)
                cap = caps.get(sst)
                if b is None or a is None or not cap:
                    valid = False
                    slices[str(sst)] = {"cap_max_prb_pct": cap, "binding": False, "reason": "janela ou teto ausente"}
                    continue
                binding = (a - b) / b <= -fx.MIN_DROP
                valid &= binding
                slices[str(sst)] = {"cap_max_prb_pct": cap, "throughput_before_mbps": round(b, 3),
                                    "throughput_after_mbps": round(a, 3), "relative_change": round((a - b) / b, 4),
                                    "binding": binding}
                k[str(sst)] = a / cap
            result.update(window_before=before_w, window_after=after_w, slices=slices,
                          k_mbps_per_prb_pct={s: round(v, 6) for s, v in k.items()}, valid=valid)
            if not valid:
                result["reason"] = "o teto não restringiu todas as fatias: k não mede capacidade por PRB"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return result


def calibrate_complementary(run_ids: List[str], out: Path, runs_dir: Path = ROOT / "experiments" / "runs",
                            dissection_root: Path = ROOT / "experiments" / "e2_dissection") -> Dict[str, Any]:
    """Uma execução por fatia, com cotas somando 100 %; calibra só a fatia de menor teto de cada uma."""
    tmp = out.with_name(out.stem + ".part.json")
    runs: List[Dict[str, Any]] = []
    k: Dict[str, float] = {}
    problems: List[str] = []
    for run_id in run_ids:
        single = calibrate(run_id, tmp, runs_dir, dissection_root)
        caps = {int(q["sst"]): float(q["max_prb_ratio"]) for q in single.get("quotas_from_pcap") or []}
        entry = {key: single.get(key) for key in ("run_id", "source_csv", "source_csv_sha256", "source_dissection_sha256",
                                                  "quotas_from_pcap", "control_sim_time_s", "window_before",
                                                  "window_after", "slices")}
        if not caps or abs(sum(caps.values()) - 100.0) > 1e-6:
            problems.append(f"{run_id}: cotas não somam 100 % ({caps})")
            runs.append(entry)
            continue
        restricted = min(caps, key=lambda sst: (caps[sst], sst))
        info = (single.get("slices") or {}).get(str(restricted), {})
        entry["restricted_sst"] = restricted
        if not info.get("binding"):
            problems.append(f"{run_id}: a fatia SST {restricted} (teto {caps[restricted]:.0f} %) "
                            f"não caiu {100 * fx.MIN_DROP:.0f} %")
        elif str(restricted) in k:
            problems.append(f"{run_id}: SST {restricted} já calibrada por outra execução")
        else:
            k[str(restricted)] = float(info["throughput_after_mbps"]) / caps[restricted]
        runs.append(entry)
    if tmp.exists():
        tmp.unlink()
    slices_seen = {str(int(q["sst"])) for r in runs for q in (r.get("quotas_from_pcap") or [])}
    missing = sorted(slices_seen - set(k))
    if missing:
        problems.append(f"fatias sem k válido: {missing}")
    result: Dict[str, Any] = {
        "schema": "xapp-rdl/slice-capacity-calibration/v2-complementary",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scripts/certification/calibrate_slice_capacity.py --complementary",
        "constants": {"window_s": fx.WINDOW_S, "settle_s": fx.SETTLE_S, "min_drop": fx.MIN_DROP},
        "runs": runs, "k_mbps_per_prb_pct": {s: round(v, 6) for s, v in sorted(k.items())},
        "valid": not problems,
    }
    if problems:
        result["reason"] = "; ".join(problems)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True, action="append")
    parser.add_argument("--complementary", action="store_true", help="cotas somando 100 %%, uma execução por fatia")
    parser.add_argument("--out", default=str(ROOT / "experiments" / "calibration" / "slice_capacity_v2.json"))
    args = parser.parse_args(argv)
    if args.complementary:
        r = calibrate_complementary(args.run, Path(args.out))
        print(f"Calibração complementar ({', '.join(args.run)}): {'VÁLIDA' if r['valid'] else 'INVÁLIDA'}"
              + (f" — {r['reason']}" if r.get("reason") else ""))
        for run in r["runs"]:
            sst = run.get("restricted_sst")
            s = (run.get("slices") or {}).get(str(sst), {})
            if s.get("throughput_after_mbps") is not None:
                print(f"  {run['run_id']}: SST {sst} teto {s['cap_max_prb_pct']:.0f} %; "
                      f"{s['throughput_before_mbps']:.2f} -> {s['throughput_after_mbps']:.2f} Mb/s; "
                      f"restringiu={s['binding']}")
        print(f"  k = {r['k_mbps_per_prb_pct']} Mb/s por % de PRB")
        print(f"Saída: {args.out}")
        return 0 if r["valid"] else 1
    if len(args.run) != 1:
        parser.error("sem --complementary, informe uma única --run")
    args.run = args.run[0]
    r = calibrate(args.run, Path(args.out))
    print(f"Calibração ({args.run}): {'VÁLIDA' if r['valid'] else 'INVÁLIDA'}" + (f" — {r['reason']}" if r.get("reason") else ""))
    for sst, s in (r.get("slices") or {}).items():
        if "throughput_after_mbps" in s:
            print(f"  SST {sst}: teto {s['cap_max_prb_pct']:.0f} %; {s['throughput_before_mbps']:.2f} -> "
                  f"{s['throughput_after_mbps']:.2f} Mb/s; restringiu={s['binding']}; "
                  f"k = {r['k_mbps_per_prb_pct'].get(sst, float('nan')):.4f} Mb/s por % de PRB")
    print(f"Saída: {args.out}")
    return 0 if r["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
