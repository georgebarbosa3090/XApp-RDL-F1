#!/usr/bin/env python3
"""
Efeito do RIC Control na RAN (fase 4): vazão por fatia antes e depois do Control.

O KPM do NORI não mede vazão por UE (``DRB.UEThpDl`` sai sempre 0) e calcula PRB por UE a partir
de símbolos. O efeito é medido na referência da simulação: ``raw/slice_series.csv``, gravado pela
variante ``nori-rc-slicing-flowmon`` a cada 0,5 s simulado com os contadores acumulados do
FlowMonitor por UE/fatia, o tempo simulado e o relógio de parede.

Procedimento (constantes fixadas antes das execuções):

1. O instante do RIC Control no PCAP (relógio de parede do pod, o mesmo do ns-3) é convertido em
   tempo simulado por interpolação na série (simulação em tempo real).
2. Vazão por fatia na janela ANTES = [t_c - W, t_c] e DEPOIS = [t_c + S, t_c + S + W].
3. As cotas são lidas dos bytes do Control no PCAP (decodificados com src/e2/v3/codec.py), não do
   registro da xApp.
4. Expectativa por fatia, a partir da parte que cada fatia usava antes (p_s = vazão_s / total):
   - teto < 100·p_s − MARGEM_PP: a vazão deve cair ao menos QUEDA_MIN;
   - caso contrário: a vazão não pode cair mais que QUEDA_MIN.
5. Veredito: CONSISTENT se há ao menos uma fatia com queda esperada e todas as expectativas se
   cumprem; INCONSISTENT se alguma falha; NOT_TESTABLE se nenhuma fatia tem teto abaixo da parte
   que usava ou se a série não cobre as janelas.

Regra v2 (com ``--calibration``, pré-registro docs/07_preregistro_fase4_v2.md): a parte dos PRBs que
cada fatia usava vem da calibração (k_s, Mb/s por ponto percentual de PRB), não da parte da vazão:

   - p_s = vazão_antes_s / k_s (% de PRB);
   - teto < p_s − MARGEM_PP: fatia restrita; a vazão deve cair ao menos QUEDA_MIN e ficar a no máximo
     TOLERÂNCIA (relativa) da previsão teto·k_s;
   - caso contrário: a vazão não pode cair mais que QUEDA_MIN.

Regra v6 (com ``--rule v6 --curve <curva v5>``, pré-registro docs/07_preregistro_fase4_v6.md): a curva da
calibração vira razão r(teto) = vazão_depois / vazão_antes, e a previsão é vazão_antes × r(teto):

   - teto >= menor nível livre acima dos que restringem: sem queda esperada;
   - teto igual a um nível que restringe: r desse nível (as avaliações são execuções novas, fora da curva);
   - teto entre dois níveis que restringem: r por interpolação linear entre eles (níveis livres não entram);
   - outro teto (abaixo do menor nível ou entre o maior nível que restringe e o nível livre): não testável;
   - fatia com previsão abaixo de (1 − QUEDA_MIN)·antes: deve cair ≥ QUEDA_MIN e ficar a no máximo
     TOLERÂNCIA_V6 (10 %) da previsão.

   A saída vai para ``slice_effect_v6.json`` (o ``slice_effect.json`` continua com a regra do certificador).

Saída: ``experiments/e2_dissection/<run>/slice_effect.json`` (hashes do CSV, da dissecação e, na
regra v2, da calibração).

Uso:
    python scripts/certification/slice_effect.py --run nori_hrdl_loop_seed1
    python scripts/certification/slice_effect.py --run nori_hrdl_v2_seed1 --calibration experiments/calibration/slice_capacity_v2.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WINDOW_S = 4.0       # W
SETTLE_S = 2.0       # S
MARGIN_PP = 5.0      # pontos percentuais
MIN_DROP = 0.05      # 5 %
TOLERANCE = 0.20     # regra v2: |vazão_depois − teto·k| / (teto·k) <= 20 % nas fatias restritas
TOLERANCE_V6 = 0.10  # regra v6: |vazão_depois − antes·r(teto)| / (antes·r(teto)) <= 10 %
SCHEMA = "xapp-rdl/slice-effect/v1"


def load_series(path: Path) -> Dict[int, List[Tuple[float, float, float]]]:
    """sst -> [(sim_time_s, wall_epoch_s, rx_bytes acumulado)] somando os UEs de cada fatia."""
    per_sample: Dict[Tuple[float, int], List[float]] = {}
    walls: Dict[float, float] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t, sst = float(row["sim_time_s"]), int(row["sst"])
            walls[t] = float(row["wall_epoch_s"])
            per_sample.setdefault((t, sst), []).append(float(row["rx_bytes"]))
    series: Dict[int, List[Tuple[float, float, float]]] = {}
    for (t, sst), values in sorted(per_sample.items()):
        series.setdefault(sst, []).append((t, walls[t], sum(values)))
    return series


def wall_to_sim(series: Dict[int, List[Tuple[float, float, float]]], wall: float) -> Optional[float]:
    points = sorted({(w, t) for rows in series.values() for t, w, _ in rows})
    for (w0, t0), (w1, t1) in zip(points, points[1:]):
        if w0 <= wall <= w1:
            return t0 if w1 == w0 else t0 + (wall - w0) * (t1 - t0) / (w1 - w0)
    return None


def apply_time(series: Dict[int, List[Tuple[float, float, float]]], wall: float) -> Optional[float]:
    """Instante simulado em que o NORI aplica o Control (desenho v5).

    O NORI agenda o Control a partir da thread do E2 com ``ScheduleWithContext(MicroSeconds(0))``; no
    ``RealtimeSimulatorImpl`` o evento cai no tempo de relógio decorrido desde o início da simulação,
    à frente do tempo simulado atrasado. O início da simulação no relógio de parede vem da primeira
    amostra da série (quando a simulação ainda não atrasou): t_aplic = parede_Control − (parede_0 − t_0).
    """
    first = min((r for rows in series.values() for r in rows), key=lambda r: r[0], default=None)
    if first is None:
        return None
    return wall - (first[1] - first[0])


def throughput_mbps(rows: List[Tuple[float, float, float]], start: float, end: float) -> Optional[float]:
    """Vazão média (Mb/s) entre as amostras mais próximas dentro de [start, end]."""
    inside = [r for r in rows if start - 1e-9 <= r[0] <= end + 1e-9]
    if len(inside) < 2 or inside[-1][0] - inside[0][0] < 0.5 * (end - start):
        return None
    (t0, _, b0), (t1, _, b1) = inside[0], inside[-1]
    return (b1 - b0) * 8.0 / (t1 - t0) / 1e6


def control_quotas(dissection: Dict[str, Any], ddir: Path) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    roles = dissection.get("chain_roles") or {}
    by_index = {m["index"]: m for m in dissection.get("messages", [])}
    ctrl = by_index.get(roles.get("control_request") or -1)
    if not ctrl or not ctrl.get("file"):
        return None, []
    from src.e2.v3 import codec
    pdu = codec.decode_e2ap_pdu((ddir / ctrl["file"]).read_bytes())
    quotas = codec.E2smCodec().rc_decode_slice_quotas(pdu["control_message"])
    return ctrl, [q.__dict__ for q in quotas]


def evaluate(series: Dict[int, List[Tuple[float, float, float]]], t_control: float,
             quotas: List[Dict[str, Any]]) -> Dict[str, Any]:
    before_w = (t_control - WINDOW_S, t_control)
    after_w = (t_control + SETTLE_S, t_control + SETTLE_S + WINDOW_S)
    caps = {int(q["sst"]): float(q["max_prb_ratio"]) for q in quotas}
    stats: Dict[str, Dict[str, Any]] = {}
    before = {sst: throughput_mbps(rows, *before_w) for sst, rows in series.items()}
    after = {sst: throughput_mbps(rows, *after_w) for sst, rows in series.items()}
    if any(v is None for v in list(before.values()) + list(after.values())) or not caps:
        return {"verdict": "NOT_TESTABLE", "reason": "série não cobre as janelas ou Control sem cotas",
                "window_before": before_w, "window_after": after_w}
    total = sum(before.values())
    decrease_expected = False
    all_ok = True
    for sst in sorted(series):
        share = 100.0 * before[sst] / total if total > 0 else 0.0
        cap = caps.get(sst, 100.0)
        expect = "decrease" if cap < share - MARGIN_PP else "no_decrease"
        change = (after[sst] - before[sst]) / before[sst] if before[sst] > 0 else 0.0
        ok = change <= -MIN_DROP if expect == "decrease" else change >= -MIN_DROP
        decrease_expected |= expect == "decrease"
        all_ok &= ok
        stats[str(sst)] = {"cap_max_prb_pct": cap, "share_before_pct": round(share, 2),
                           "throughput_before_mbps": round(before[sst], 3), "throughput_after_mbps": round(after[sst], 3),
                           "relative_change": round(change, 4), "expectation": expect, "met": ok}
    verdict = "NOT_TESTABLE" if not decrease_expected else ("CONSISTENT" if all_ok else "INCONSISTENT")
    return {"verdict": verdict, "window_before": before_w, "window_after": after_w, "slices": stats}


def evaluate_v2(series: Dict[int, List[Tuple[float, float, float]]], t_control: float,
                quotas: List[Dict[str, Any]], k: Dict[int, float]) -> Dict[str, Any]:
    """Regra v2: fatia restrita decidida pela parte de PRB calibrada (k_s em Mb/s por % de PRB)."""
    before_w = (t_control - WINDOW_S, t_control)
    after_w = (t_control + SETTLE_S, t_control + SETTLE_S + WINDOW_S)
    caps = {int(q["sst"]): float(q["max_prb_ratio"]) for q in quotas}
    before = {sst: throughput_mbps(rows, *before_w) for sst, rows in series.items()}
    after = {sst: throughput_mbps(rows, *after_w) for sst, rows in series.items()}
    if any(v is None for v in list(before.values()) + list(after.values())) or not caps:
        return {"verdict": "NOT_TESTABLE", "reason": "série não cobre as janelas ou Control sem cotas",
                "window_before": before_w, "window_after": after_w}
    if any(sst not in k for sst in series):
        return {"verdict": "NOT_TESTABLE", "reason": "calibração sem k para alguma fatia"}
    stats: Dict[str, Dict[str, Any]] = {}
    binding_any, all_ok = False, True
    for sst in sorted(series):
        cap = caps.get(sst, 100.0)
        prb_used = before[sst] / k[sst]
        change = (after[sst] - before[sst]) / before[sst] if before[sst] > 0 else 0.0
        entry = {"cap_max_prb_pct": cap, "k_mbps_per_prb_pct": round(k[sst], 4),
                 "prb_used_before_pct_est": round(prb_used, 2),
                 "throughput_before_mbps": round(before[sst], 3), "throughput_after_mbps": round(after[sst], 3),
                 "relative_change": round(change, 4)}
        if cap < prb_used - MARGIN_PP:
            predicted = cap * k[sst]
            error = abs(after[sst] - predicted) / predicted
            ok = change <= -MIN_DROP and error <= TOLERANCE
            entry.update(expectation="decrease_to_prediction", predicted_after_mbps=round(predicted, 3),
                         prediction_error=round(error, 4), met=ok)
            binding_any = True
        else:
            ok = change >= -MIN_DROP
            entry.update(expectation="no_decrease", met=ok)
        all_ok &= ok
        stats[str(sst)] = entry
    verdict = "NOT_TESTABLE" if not binding_any else ("CONSISTENT" if all_ok else "INCONSISTENT")
    return {"verdict": verdict, "window_before": before_w, "window_after": after_w, "slices": stats}


def predict(curve_pts: List[Dict[str, Any]], cap: float) -> Dict[str, Any]:
    """Previsão da vazão depois do Control para um teto, deixando de fora o próprio nível (se medido).

    - teto >= maior nível medido que NÃO restringiu: sem queda esperada (``no_decrease``);
    - teto entre dois níveis medidos (excluído o próprio): interpolação linear da vazão depois;
    - fora do intervalo medido: ``not_testable``.
    """
    pts = [p for p in curve_pts if abs(p["cap_max_prb_pct"] - cap) > 1e-9]
    # limiar: menor nível sem restrição acima de todos os níveis que restringem
    highest_binding = max((p["cap_max_prb_pct"] for p in curve_pts if p["binding"]), default=float("-inf"))
    free = [p["cap_max_prb_pct"] for p in curve_pts if not p["binding"] and p["cap_max_prb_pct"] > highest_binding]
    if free and cap >= min(free):
        return {"kind": "no_decrease", "threshold_free_pct": min(free)}
    lower = [p for p in pts if p["cap_max_prb_pct"] < cap]
    upper = [p for p in pts if p["cap_max_prb_pct"] > cap]
    if not lower or not upper:
        return {"kind": "not_testable", "reason": f"teto {cap:.0f} % fora do intervalo medido (deixa-um-fora)"}
    lo, hi = lower[-1], upper[0]
    w = (cap - lo["cap_max_prb_pct"]) / (hi["cap_max_prb_pct"] - lo["cap_max_prb_pct"])
    value = lo["throughput_after_mbps"] + w * (hi["throughput_after_mbps"] - lo["throughput_after_mbps"])
    return {"kind": "interpolated", "predicted_after_mbps": value,
            "from_levels": [lo["cap_max_prb_pct"], hi["cap_max_prb_pct"]]}


def predict_ratio(curve_pts: List[Dict[str, Any]], cap: float) -> Dict[str, Any]:
    """Regra v6: razão r(teto) = depois/antes da curva, interpolada só entre níveis que restringem."""
    binding = sorted((p for p in curve_pts if p["binding"] and p["throughput_before_mbps"] > 0),
                     key=lambda p: p["cap_max_prb_pct"])
    highest_binding = binding[-1]["cap_max_prb_pct"] if binding else float("-inf")
    free = [p["cap_max_prb_pct"] for p in curve_pts if not p["binding"] and p["cap_max_prb_pct"] > highest_binding]
    if free and cap >= min(free):
        return {"kind": "no_decrease", "threshold_free_pct": min(free)}
    ratio = {p["cap_max_prb_pct"]: p["throughput_after_mbps"] / p["throughput_before_mbps"] for p in binding}
    for level, r in ratio.items():
        if abs(level - cap) < 1e-9:
            return {"kind": "ratio", "ratio": r, "from_levels": [level]}
    lower = [lv for lv in ratio if lv < cap]
    upper = [lv for lv in ratio if lv > cap]
    if not lower or not upper:
        levels = ", ".join(f"{lv:.0f}" for lv in ratio)
        return {"kind": "not_testable", "reason": f"teto {cap:.0f} % fora dos níveis que restringem ({levels} %)"}
    lo, hi = max(lower), min(upper)
    r = ratio[lo] + (cap - lo) / (hi - lo) * (ratio[hi] - ratio[lo])
    return {"kind": "ratio", "ratio": r, "from_levels": [lo, hi]}


def evaluate_ratio(series: Dict[int, List[Tuple[float, float, float]]], t_control: float,
                   quotas: List[Dict[str, Any]], curve: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Regra v6: previsão relativa à vazão antes do Control (janelas ancoradas na aplicação)."""
    before_w = (t_control - WINDOW_S, t_control)
    after_w = (t_control + SETTLE_S, t_control + SETTLE_S + WINDOW_S)
    caps = {int(q["sst"]): float(q["max_prb_ratio"]) for q in quotas}
    before = {sst: throughput_mbps(rows, *before_w) for sst, rows in series.items()}
    after = {sst: throughput_mbps(rows, *after_w) for sst, rows in series.items()}
    if any(v is None for v in list(before.values()) + list(after.values())) or not caps:
        return {"verdict": "NOT_TESTABLE", "reason": "série não cobre as janelas ou Control sem cotas",
                "window_before": before_w, "window_after": after_w}
    stats: Dict[str, Dict[str, Any]] = {}
    binding_any, all_ok, untestable = False, True, []
    for sst in sorted(series):
        cap = caps.get(sst, 100.0)
        change = (after[sst] - before[sst]) / before[sst] if before[sst] > 0 else 0.0
        pred = predict_ratio(curve.get(str(sst), []), cap)
        entry = {"cap_max_prb_pct": cap, "throughput_before_mbps": round(before[sst], 3),
                 "throughput_after_mbps": round(after[sst], 3), "relative_change": round(change, 4),
                 "curve_prediction": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in pred.items()}}
        if pred["kind"] == "not_testable":
            untestable.append(sst)
            entry.update(expectation="not_testable", met=None)
        elif pred["kind"] == "ratio" and pred["ratio"] < 1 - MIN_DROP:
            predicted = before[sst] * pred["ratio"]
            error = abs(after[sst] - predicted) / predicted if predicted > 0 else float("inf")
            ok = change <= -MIN_DROP and error <= TOLERANCE_V6
            entry.update(expectation="decrease_to_prediction", predicted_after_mbps=round(predicted, 3),
                         prediction_error=round(error, 4), met=ok)
            binding_any = True
            all_ok &= ok
        else:
            ok = change >= -MIN_DROP
            entry.update(expectation="no_decrease", met=ok)
            all_ok &= ok
        stats[str(sst)] = entry
    if untestable:
        verdict = "NOT_TESTABLE"
    else:
        verdict = "NOT_TESTABLE" if not binding_any else ("CONSISTENT" if all_ok else "INCONSISTENT")
    return {"verdict": verdict, "window_before": before_w, "window_after": after_w, "slices": stats}


def evaluate_curve(series: Dict[int, List[Tuple[float, float, float]]], t_control: float,
                   quotas: List[Dict[str, Any]], curve: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Regra v4: previsão pela curva teto -> vazão medida (interpolação deixando de fora o próprio nível)."""
    before_w = (t_control - WINDOW_S, t_control)
    after_w = (t_control + SETTLE_S, t_control + SETTLE_S + WINDOW_S)
    caps = {int(q["sst"]): float(q["max_prb_ratio"]) for q in quotas}
    before = {sst: throughput_mbps(rows, *before_w) for sst, rows in series.items()}
    after = {sst: throughput_mbps(rows, *after_w) for sst, rows in series.items()}
    if any(v is None for v in list(before.values()) + list(after.values())) or not caps:
        return {"verdict": "NOT_TESTABLE", "reason": "série não cobre as janelas ou Control sem cotas",
                "window_before": before_w, "window_after": after_w}
    stats: Dict[str, Dict[str, Any]] = {}
    binding_any, all_ok, untestable = False, True, []
    for sst in sorted(series):
        cap = caps.get(sst, 100.0)
        change = (after[sst] - before[sst]) / before[sst] if before[sst] > 0 else 0.0
        pred = predict(curve.get(str(sst), []), cap)
        entry = {"cap_max_prb_pct": cap, "throughput_before_mbps": round(before[sst], 3),
                 "throughput_after_mbps": round(after[sst], 3), "relative_change": round(change, 4),
                 "curve_prediction": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in pred.items()}}
        if pred["kind"] == "not_testable":
            untestable.append(sst)
            entry.update(expectation="not_testable", met=None)
        elif pred["kind"] == "interpolated" and pred["predicted_after_mbps"] < before[sst] * (1 - MIN_DROP):
            error = abs(after[sst] - pred["predicted_after_mbps"]) / pred["predicted_after_mbps"]
            ok = change <= -MIN_DROP and error <= TOLERANCE
            entry.update(expectation="decrease_to_prediction", predicted_after_mbps=round(pred["predicted_after_mbps"], 3),
                         prediction_error=round(error, 4), met=ok)
            binding_any = True
            all_ok &= ok
        else:
            ok = change >= -MIN_DROP
            entry.update(expectation="no_decrease", met=ok)
            all_ok &= ok
        stats[str(sst)] = entry
    if untestable:
        verdict = "NOT_TESTABLE"
    else:
        verdict = "NOT_TESTABLE" if not binding_any else ("CONSISTENT" if all_ok else "INCONSISTENT")
    return {"verdict": verdict, "window_before": before_w, "window_after": after_w, "slices": stats}


def analyze(run_id: str, runs_dir: Path = ROOT / "experiments" / "runs",
            dissection_root: Path = ROOT / "experiments" / "e2_dissection",
            calibration: Optional[Path] = None, curve: Optional[Path] = None,
            rule: Optional[str] = None) -> Dict[str, Any]:
    if rule == "v6" and not curve:
        raise ValueError("a regra v6 exige --curve (curva v5, âncora apply)")
    run_dir, ddir = runs_dir / run_id, dissection_root / run_id
    csv_path = run_dir / "raw" / "slice_series.csv"
    dissection = json.loads((ddir / "e2_messages.json").read_text(encoding="utf-8"))
    out: Dict[str, Any] = {
        "schema": SCHEMA, "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scripts/certification/slice_effect.py",
        "rule": "v4-curve" if curve else ("v2-calibrated" if calibration else "v1-throughput-share"),
        "anchor": "control",
        "constants": {"window_s": WINDOW_S, "settle_s": SETTLE_S, "margin_pp": MARGIN_PP, "min_drop": MIN_DROP,
                      **({"tolerance": TOLERANCE} if (calibration or curve) else {})},
        "source_csv": f"raw/slice_series.csv",
        "source_csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest() if csv_path.exists() else None,
        "source_dissection_sha256": hashlib.sha256((ddir / "e2_messages.json").read_bytes()).hexdigest(),
    }
    if not csv_path.exists():
        out.update(verdict="NOT_TESTABLE", reason="execução sem raw/slice_series.csv")
    else:
        ctrl, quotas = control_quotas(dissection, ddir)
        series = load_series(csv_path)
        if not ctrl:
            out.update(verdict="NOT_TESTABLE", reason="nenhum RIC Control na cadeia do PCAP")
        else:
            t_c = wall_to_sim(series, float(ctrl["time_epoch"]))
            out.update(control_frame=ctrl["frame"], control_wall_epoch=ctrl["time_epoch"], control_sim_time_s=t_c,
                       quotas_from_pcap=quotas)
            if t_c is None:
                out.update(verdict="NOT_TESTABLE", reason="instante do Control fora da série (relógio de parede)")
            elif curve:
                cv = json.loads(Path(curve).read_text(encoding="utf-8"))
                if cv.get("anchor") == "apply":
                    # v5: janelas ancoradas no instante de aplicação do Control (docs/07_preregistro_fase4_v5.md)
                    t_c = apply_time(series, float(ctrl["time_epoch"]))
                    out.update(rule="v5-curve-apply", anchor="apply", control_apply_time_s=t_c)
                try:
                    cv_rel = Path(curve).resolve().relative_to(ROOT).as_posix()
                except ValueError:
                    cv_rel = str(curve)
                out.update(calibration=cv_rel, calibration_sha256=hashlib.sha256(Path(curve).read_bytes()).hexdigest())
                if cv.get("valid") is not True:
                    out.update(verdict="NOT_TESTABLE", reason="curva teto -> vazão inválida")
                else:
                    if rule == "v6":
                        out.update(rule="v6-ratio-apply", constants={**out["constants"], "tolerance": TOLERANCE_V6})
                        out.update(evaluate_ratio(series, t_c, quotas, cv["curve"]))
                    else:
                        out.update(evaluate_curve(series, t_c, quotas, cv["curve"]))
            elif calibration:
                cal = json.loads(Path(calibration).read_text(encoding="utf-8"))
                try:
                    cal_rel = Path(calibration).resolve().relative_to(ROOT).as_posix()
                except ValueError:
                    cal_rel = str(calibration)
                out.update(calibration=cal_rel, calibration_sha256=hashlib.sha256(Path(calibration).read_bytes()).hexdigest())
                if cal.get("valid") is not True:
                    out.update(verdict="NOT_TESTABLE", reason="calibração inválida (teto não restringiu na calibração)")
                else:
                    k = {int(sst): float(v) for sst, v in cal["k_mbps_per_prb_pct"].items()}
                    out.update(evaluate_v2(series, t_c, quotas, k))
            else:
                out.update(evaluate(series, t_c, quotas))
    if rule == "v6" and not out["rule"].startswith("v6"):
        out["rule"] = "v6-ratio-apply"   # sem Control ou sem série: o arquivo v6 registra o motivo
    name = "slice_effect_v6.json" if rule == "v6" else "slice_effect.json"
    data = (json.dumps(out, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    (ddir / name).write_bytes(data)
    # Mantém o hashes.sha256 da dissecação completo (a dissecação o grava antes desta análise).
    hashes = ddir / "hashes.sha256"
    if hashes.exists():
        lines = [l for l in hashes.read_text(encoding="utf-8").splitlines() if not l.endswith(f"  {name}")]
        lines.append(f"{hashlib.sha256(data).hexdigest()}  {name}")
        hashes.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    return out


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True)
    parser.add_argument("--calibration", help="calibração (calibrate_slice_capacity.py): ativa a regra v2")
    parser.add_argument("--curve", help="curva teto -> vazão (slice_cap_curve.py): ativa a regra v4 (v5 com âncora apply)")
    parser.add_argument("--rule", choices=["v6"], help="v6: previsão relativa (razão da curva); grava slice_effect_v6.json")
    args = parser.parse_args(argv)
    r = analyze(args.run, calibration=Path(args.calibration) if args.calibration else None,
                curve=Path(args.curve) if args.curve else None, rule=args.rule)
    print(f"Efeito do Control ({args.run}, regra {r['rule']}): {r['verdict']}" + (f" — {r['reason']}" if r.get("reason") else ""))
    if r.get("control_sim_time_s") is not None:
        print(f"  Control no quadro {r['control_frame']}, t_sim = {r['control_sim_time_s']:.2f} s; cotas do PCAP: {r['quotas_from_pcap']}")
    for sst, s in (r.get("slices") or {}).items():
        share = (f"parte antes {s['share_before_pct']:.1f} %" if "share_before_pct" in s
                 else f"PRB usado (calibrado) {s['prb_used_before_pct_est']:.1f} %" if "prb_used_before_pct_est" in s
                 else f"curva: {s['curve_prediction']}")
        pred = (f"; previsto {s['predicted_after_mbps']:.2f} Mb/s (erro {100 * s['prediction_error']:.1f} %)"
                if "predicted_after_mbps" in s else "")
        print(f"  SST {sst}: teto {s['cap_max_prb_pct']:.0f} %, {share}; "
              f"{s['throughput_before_mbps']:.2f} -> {s['throughput_after_mbps']:.2f} Mb/s "
              f"({100 * s['relative_change']:+.1f} %){pred}; esperado {s['expectation']}: {'cumprido' if s['met'] else 'NÃO cumprido'}")
    return 0 if r["verdict"] == "CONSISTENT" else 1


if __name__ == "__main__":
    sys.exit(main())
