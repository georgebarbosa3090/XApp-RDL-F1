# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
xApp1-RANSlicer (GreenRAN, atividade A1.5): cota de PRB por fatia guiada por intenção.

Fatias do GreenRAN: eMBB das câmeras de vigilância (SST 1; App1: 25 Mb/s por câmera, atraso < 100 ms) e
mMTC dos sensores (SST 2; App2). A cada período, por célula:

1. **Eficiência medida:** Mb/s por ponto percentual de PRB da fatia eMBB (média móvel do KPM). Sem
   medida, usa ``ranslicer_default_eff``.
2. **Necessidade:** teto eMBB = vazão-alvo × (1 + margem) ÷ eficiência. Se o atraso passou do limite,
   sobe pelo menos ``ranslicer_delay_step`` pontos acima do teto atual.
3. **Escudo de segurança (safe RL):** uma política aprendida opcional (por exemplo, o ator MAPPO da
   CA-RDL) pode propor o teto, mas a saída é recortada ao intervalo seguro [necessidade, 100 − piso mMTC].
   Sem política, vale a necessidade.
4. **Proposta à RDL:** ``PRB_QUOTA`` = teto da fatia eMBB (convenção da RDL: eMBB recebe v, a outra
   fatia 100 − v), prioridade 90 com SLA em risco e 75 sem risco. Mudanças menores que
   ``ranslicer_min_change`` pontos não são propostas (evita oscilação).

A intenção chega pela política A1 21000 (``GreenRAN_RANSlicer_Intent``), publicada pelo
rApp-ResourceOptimizer.
"""

import math
from typing import Any, Callable, Dict, List, Optional

from src.greenran.common import CellSample, GreenRanXApp

EMBB_SST, MMTC_SST = 1, 2


class RanSlicer(GreenRanXApp):
    XAPP_ID = "xapp1_ranslicer"
    A1_TYPE = "21000"
    DEFAULTS: Dict[str, Any] = {
        "embb_min_thp_mbps": 30.0,       # alvo agregado da fatia de câmeras na célula
        "embb_max_delay_ms": 100.0,
        "mmtc_min_prb_pct": 10.0,        # piso garantido aos sensores
        "slice_safety_margin": 0.15,
        "ranslicer_learned_policy": False,
        "ranslicer_default_eff": 1.0,    # Mb/s por ponto de PRB sem medida
        "ranslicer_delay_step": 10.0,
        "ranslicer_min_change": 2.0,
    }

    def __init__(self, *args, learned_policy: Optional[Callable[[Dict[str, float]], float]] = None,
                 eff_alpha: float = 0.3, **kwargs):
        super().__init__(*args, **kwargs)
        self.learned_policy = learned_policy
        self.eff_alpha = eff_alpha
        self.efficiency: Dict[str, float] = {}
        self.last_cap: Dict[str, float] = {}

    def observe(self, sample: CellSample) -> None:
        super().observe(sample)
        embb = sample.slices.get(EMBB_SST)
        if embb and embb.prb_used > 0 and sample.load_pct:
            # fração de PRB da fatia (% da célula) estimada pela participação da fatia nos PRBs dos UEs
            total_prb = sum(s.prb_used for s in sample.slices.values()) or embb.prb_used
            share_pct = sample.load_pct * embb.prb_used / total_prb
            if share_pct > 1.0:
                eff = embb.thp_mbps / share_pct
                old = self.efficiency.get(sample.cell_id)
                self.efficiency[sample.cell_id] = eff if old is None else (1 - self.eff_alpha) * old + self.eff_alpha * eff

    def safe_interval(self, need_pct: float, policy: Dict[str, Any]) -> tuple:
        upper = 100.0 - float(policy["mmtc_min_prb_pct"])
        return min(max(need_pct, 1.0), upper), upper

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol = self.policy()
        out = []
        for cell, s in sorted(self.samples.items()):
            embb = s.slices.get(EMBB_SST)
            eff = self.efficiency.get(cell, float(pol["ranslicer_default_eff"]))
            target = float(pol["embb_min_thp_mbps"])
            need = target * (1 + float(pol["slice_safety_margin"])) / max(eff, 1e-6)
            current = self.last_cap.get(cell)
            delay = embb.delay_ms if embb else None
            delay_risk = delay is not None and delay > float(pol["embb_max_delay_ms"])
            thp_risk = embb is not None and embb.ues > 0 and embb.thp_mbps < target
            if delay_risk:
                need = max(need, (current or need) + float(pol["ranslicer_delay_step"]))
            low, high = self.safe_interval(need, pol)
            cap = low
            if pol.get("ranslicer_learned_policy") and self.learned_policy is not None:
                state = {"thp_mbps": embb.thp_mbps if embb else 0.0, "delay_ms": delay or 0.0,
                         "load_pct": s.load_pct or 0.0, "efficiency": eff, "need_pct": need}
                cap = min(max(float(self.learned_policy(state)), low), high)   # escudo de segurança
            cap = float(math.ceil(min(cap, high)))
            at_risk = delay_risk or thp_risk
            if current is not None and abs(cap - current) < float(pol["ranslicer_min_change"]) and not at_risk:
                continue
            self.last_cap[cell] = cap
            out.append({"xapp_id": self.XAPP_ID, "node_id": cell, "parameter": "PRB_QUOTA", "value": cap,
                        "priority": 90 if at_risk else 75, "defer_ok": True, "ttl_ms": 2000})
        return out


def main() -> int:  # pragma: no cover - execução no RIC
    import os
    import time
    app = RanSlicer(rmr_port=int(os.getenv("RMR_PORT", "4560")))
    app.start()
    while app.running:
        time.sleep(1)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
