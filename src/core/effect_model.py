# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
Modelo de efeito por fatia e guarda de SLA (doc 18, Parte A: §4.2, §4.3 e §4.4).

Uma proposta ``PRB_QUOTA`` com ``scope = slice`` e ``ratio_kind = max`` vira a alocação depois da
decisão, a′: o valor é o teto da fatia ``slice_sst``, e a fatia complementar (SST 1 ↔ SST 2 no NORI,
como ``quotas_for``) recebe 100 − valor. A vazão prevista de cada fatia é

    T̂_s(a′) = T_s^livre · r(a′_s)

com r a curva teto → vazão relativa medida no NORI (``experiments/calibration/slice_cap_curve_v5.json``,
porte de ``CapCurve`` da Fase 2: interpolação só entre níveis que restringem, regra v6, achados 41 e 42).

Daí saem, como fixados no doc 18 §4.3:

- s_vazão(a) = Σ_s T̂_s(a′) ÷ Σ_s T_s^livre;
- s_SLA(a)   = mín, sobre as fatias com SLA, de mín(1, T̂_s(a′) ÷ T_s^req).

O s_energia do §4.3 depende do modelo do docs/17 (pré-registro 12) e não está aqui. Por isso estes
escores **não** entram na utilidade do TVS (gancho ``Reasoning._tvs_scores``; decisão no doc 18 §4.7):
hoje só a guarda de SLA os usa.

Guarda (§4.4), uma restrição e não um peso: entre as candidatas de um mesmo conflito direto, quem leva
uma fatia com SLA abaixo do requisito (s_SLA < 1) é inelegível se outra mantém s_SLA = 1; se todas
violam, só a(s) de maior s_SLA continua(m). As inelegíveis são recusadas com ``SLA_PROTECTION``.

**Validade:** o modelo só vale na condição em que a curva foi medida (NORI, 100 MHz, 300 Mb/s; o
pré-registro 06 refutou a transferência para 50 MHz). Ele fica desligado por padrão
(``RDL_EFFECT_MODEL=heuristic``): ligá-lo (``curve``) é declarar que a condição é a calibrada.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CURVE = ROOT / "experiments" / "calibration" / "slice_cap_curve_v5.json"
# sha256 do arquivo com finais de linha LF (o conteúdo no git); o checkout no Windows pode trazer CRLF.
EXPECTED_SHA256 = "d7c2f54ead0f51583a9b20c00eaa602f105b461a33d0ac44e2604015b0d8282d"
SLA_TOLERANCE = 1e-9
EFFECT_MODES = ("heuristic", "curve")


@dataclass(frozen=True)
class CapCurve:
    points: Tuple[Tuple[float, float], ...]  # (teto % de PRB, vazão depois / vazão antes), só binding
    base_throughput_mbps: float
    source: str
    sha256: str

    def ratio(self, cap_pct: float) -> float:
        """Vazão relativa à base para um teto de PRB (0–100 %)."""
        cap = max(0.0, min(100.0, float(cap_pct)))
        pts = self.points
        if cap <= pts[0][0]:
            return pts[0][1] * cap / pts[0][0]
        for (c0, r0), (c1, r1) in zip(pts, pts[1:]):
            if cap <= c1:
                return r0 + (r1 - r0) * (cap - c0) / (c1 - c0)
        (c0, r0), (c1, r1) = pts[-2], pts[-1]
        slope = (r1 - r0) / (c1 - c0)
        return min(1.0, r1 + slope * (cap - c1))

    def saturation_cap_pct(self) -> float:
        """Menor teto a partir do qual a vazão deixa de ser limitada."""
        (c0, r0), (c1, r1) = self.points[-2], self.points[-1]
        slope = (r1 - r0) / (c1 - c0)
        return min(100.0, c1 + (1.0 - r1) / slope)


def load_curve(path: Path = DEFAULT_CURVE, slice_key: str = "1", verify: bool = True) -> CapCurve:
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if verify and Path(path).resolve() == DEFAULT_CURVE.resolve() and digest != EXPECTED_SHA256:
        raise ValueError(f"curva de calibração alterada: sha256 {digest} != {EXPECTED_SHA256}")
    data = json.loads(raw.decode("utf-8"))
    if data.get("valid") is False:
        raise ValueError(f"curva inválida: {data.get('reason')}")
    entries = data["curve"][slice_key]
    binding: List[Tuple[float, float]] = sorted(
        (float(e["cap_max_prb_pct"]), float(e["throughput_after_mbps"]) / float(e["throughput_before_mbps"]))
        for e in entries if e.get("binding")
    )
    if len(binding) < 2:
        raise ValueError("a curva precisa de pelo menos dois pontos que restringem")
    base = float(entries[0]["throughput_before_mbps"])
    return CapCurve(points=tuple(binding), base_throughput_mbps=base, source=str(path), sha256=digest)


@dataclass
class SliceEffectModel:
    """Previsão de vazão por fatia para ``PRB_QUOTA`` com ``scope = slice`` (doc 18 §4.2)."""
    curve: CapCurve
    # T_s^livre por SST. No NORI o KPM não mede vazão por UE: vale a base da condição de calibração.
    free_mbps: Dict[int, float]
    # Fatias com SLA e o requisito T_s^req (Mb/s); sem requisito declarado, T_s^req = T_s^livre.
    sla_mbps: Dict[int, float]
    # Fatia que recebe 100 − valor quando a proposta fixa o teto de outra (NORI: 1 ↔ 2).
    complement: Dict[int, int] = field(default_factory=dict)

    @property
    def tag(self) -> str:
        return f"curve:{self.curve.sha256}"

    def applies(self, action: Any) -> bool:
        return (getattr(action, "parameter", None) == "PRB_QUOTA" and getattr(action, "scope", None) == "slice"
                and getattr(action, "ratio_kind", None) == "max" and getattr(action, "slice_sst", None) in self.free_mbps)

    def allocation(self, action: Any) -> Dict[int, float]:
        """a′: teto (%) de cada fatia depois da decisão; fatias fora do par ficam sem teto (100 %)."""
        caps = {sst: 100.0 for sst in self.free_mbps}
        value = max(0.0, min(100.0, float(action.value)))
        caps[int(action.slice_sst)] = value
        other = self.complement.get(int(action.slice_sst))
        if other is not None and other in caps:
            caps[other] = 100.0 - value
        return caps

    def predict(self, action: Any) -> Dict[int, float]:
        """T̂_s(a′) = T_s^livre · r(a′_s), em Mb/s."""
        return {sst: self.free_mbps[sst] * self.curve.ratio(cap) for sst, cap in self.allocation(action).items()}

    def scores(self, action: Any) -> Optional[Dict[str, float]]:
        """s_vazão e s_SLA do doc 18 §4.3, ou ``None`` se o modelo não se aplica à proposta."""
        if not self.applies(action):
            return None
        predicted = self.predict(action)
        throughput = sum(predicted.values()) / sum(self.free_mbps.values())
        sla = min((min(1.0, predicted[s] / req) for s, req in self.sla_mbps.items() if s in predicted and req > 0),
                  default=1.0)
        return {"throughput": throughput, "sla": sla}


def sla_guard(actions: Iterable[Any], model: Optional[SliceEffectModel]) -> Tuple[List[Any], Dict[str, str]]:
    """Guarda de SLA (doc 18 §4.4): (candidatas elegíveis, action_id → detalhe das inelegíveis).

    Sem modelo, ou se alguma candidata está fora do modelo (escopo não declarado, ``cell``, outro
    ``ratio_kind``), a guarda não age: comparar s_SLA previsto com o de uma candidata sem previsão
    não teria base.
    """
    actions = list(actions)
    if model is None or len(actions) < 2:
        return actions, {}
    predicted = [(a, model.scores(a)) for a in actions]
    if any(s is None for _, s in predicted):
        return actions, {}
    best = max(s["sla"] for _, s in predicted)
    floor = 1.0 if best >= 1.0 - SLA_TOLERANCE else best
    eligible = [a for a, s in predicted if s["sla"] >= floor - SLA_TOLERANCE]
    winners = ",".join(sorted(str(a.xapp_id) for a in eligible))
    slices = ",".join(str(s) for s in sorted(model.sla_mbps))
    excluded = {
        a.action_id: (f"SLA guard: predicted s_SLA {s['sla']:.4f} < {floor:.4f} on SLA slices SST {slices} "
                      f"(kept: {winners}; {model.tag[:14]})")
        for a, s in predicted if s["sla"] < floor - SLA_TOLERANCE
    }
    return eligible, excluded


def parse_sla_slices(text: str, free_mbps: Dict[int, float]) -> Dict[int, float]:
    """``"2"`` ou ``"2:120,1:40"`` → {SST: T_req em Mb/s}; sem requisito, T_req = T_s^livre."""
    out: Dict[int, float] = {}
    for item in (t.strip() for t in (text or "").split(",")):
        if not item:
            continue
        sst, _, req = item.partition(":")
        s = int(sst)
        out[s] = float(req) if req else float(free_mbps.get(s, 0.0))
        if out[s] <= 0:
            raise ValueError(f"requisito de SLA inválido para o SST {s}: {item}")
    return out


def build_effect_model(config: Optional[Dict[str, Any]] = None) -> Optional[SliceEffectModel]:
    """Modelo de efeito a partir da configuração da RDL e do ambiente, ou ``None`` (modo heurístico).

    - ``effect_model`` / ``RDL_EFFECT_MODEL``: ``heuristic`` (padrão) ou ``curve``;
    - ``effect_curve`` / ``RDL_EFFECT_CURVE``: caminho da curva (padrão: v5, com sha256 conferido);
    - ``sla_slices`` / ``RDL_SLA_SLICES``: fatias com SLA (padrão ``"2"``, a URLLC do NORI).

    T_s^livre é a base da curva para os SST 1 e 2, com complemento 1 ↔ 2 (perfil do NORI).
    """
    cfg = config or {}
    mode = str(cfg.get("effect_model") or os.getenv("RDL_EFFECT_MODEL", "heuristic")).strip().lower()
    if mode not in EFFECT_MODES:
        raise ValueError(f"RDL_EFFECT_MODEL inválido: {mode} (use {list(EFFECT_MODES)})")
    if mode == "heuristic":
        return None
    path = cfg.get("effect_curve") or os.getenv("RDL_EFFECT_CURVE") or DEFAULT_CURVE
    curve = load_curve(Path(path))
    free = {1: curve.base_throughput_mbps, 2: curve.base_throughput_mbps}
    sla = parse_sla_slices(str(cfg.get("sla_slices") or os.getenv("RDL_SLA_SLICES", "2")), free)
    return SliceEffectModel(curve=curve, free_mbps=free, sla_mbps=sla, complement={1: 2, 2: 1})
