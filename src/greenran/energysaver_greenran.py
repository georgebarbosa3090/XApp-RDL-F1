# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
xApp2-EnergySaver (GreenRAN, atividade A1.6): desligamento de RUs em baixa demanda com padrão sazonal.

Por célula, um perfil de carga por hora do dia (``SeasonalProfile``) aprende os padrões sazonais. A cada
período, dentro da janela de economia da política A1 21001 (``GreenRAN_EnergySaver_Policy``):

1. **Religar primeiro:** uma célula desligada volta (``CELL_STATE = 1``, prioridade 85) se a janela
   acabou ou se a carga esperada para a próxima hora passa do limiar, respeitado o tempo mínimo de
   permanência (``es_min_dwell_s``). Se uma vizinha passou de ``es_wake_threshold_pct``, religa na hora,
   sem esperar a permanência: é proteção de capacidade.
2. **Desligar com segurança (borda entre duas RUs):** a célula ativa menos carregada é candidata se a
   carga atual e a esperada para a próxima hora estão abaixo de ``es_sleep_threshold_pct``, se restam mais
   que ``es_min_active_cells`` células ativas, se está no estado atual há pelo menos ``es_min_dwell_s`` e se
   uma vizinha ativa absorve a carga sem passar de ``es_wake_threshold_pct``. Em dois passos:
   - com UEs na célula: ``HANDOVER`` para a vizinha (evacuação, prioridade 65). **Cobertura:** quando o KPM
     traz a RSRP das vizinhas por UE, o destino é a vizinha que cobre **todos** os UEs da célula com RSRP de
     pelo menos ``es_min_target_rsrp_dbm`` (a de maior RSRP mínima); se nenhuma cobre todos, a célula não é
     evacuada. Sem essa medida, vale a vizinha menos carregada, e o motivo fica registrado em ``decisions``;
   - **confirmação:** ``CELL_STATE = 0`` só sai quando a célula está vazia no KPM. Se ainda houver UEs depois
     de ``es_evacuation_timeout_s``, a evacuação é abortada (a célula volta a ``ACTIVE``).
   Uma célula por período.
3. **Potência com histerese:** com carga moderada (entre o limiar e o dobro), propõe uma vez reduzir
   ``TX_POWER`` para ``es_reduced_tx_power_dbm``. Se a carga passar do dobro do limiar mais
   ``es_tx_power_hysteresis_pct`` e ``es_nominal_tx_power_dbm`` estiver definido, propõe restaurar.

Se a RDL recusar o desligamento ou a evacuação (por exemplo, pela regra ``HANDOVER_INTO_REDUCED_CELL`` ou
pela política A1), a célula volta a ``ACTIVE`` e a permanência recomeça.

Hora do dia: ``hour_of(t)`` usa UTC mais ``es_utc_offset_h`` (padrão −3, Belém), e não o fuso do
computador, para a decisão ser a mesma em qualquer máquina. Na malha fechada, ``t`` é o tempo simulado.
"""

import re
import time
from typing import Any, Dict, List, Optional

from src.greenran.common import CellSample, GreenRanXApp, SeasonalProfile, load_neighbors

ACTIVE, EVACUATING, SLEEP = "ACTIVE", "EVACUATING", "SLEEP"


def _index(cell_id: str) -> Optional[int]:
    m = re.search(r"(\d+)$", cell_id)
    return int(m.group(1)) if m else None


class EnergySaver(GreenRanXApp):
    XAPP_ID = "xapp2_energysaver"
    A1_TYPE = "21001"
    DEFAULTS: Dict[str, Any] = {
        "es_sleep_threshold_pct": 15.0,
        "es_wake_threshold_pct": 60.0,
        "es_min_active_cells": 1,
        "es_sleep_start_hour": 22,
        "es_sleep_end_hour": 6,
        "es_tx_power_reduction": True,
        "es_reduced_tx_power_dbm": 30.0,
        # melhorias de 2026-11-13 (docs/16, comparação com o ES Orange; docs/12 §3)
        "es_min_target_rsrp_dbm": -110.0,
        "es_evacuation_timeout_s": 5.0,
        "es_min_dwell_s": 30.0,
        "es_tx_power_hysteresis_pct": 5.0,
        "es_nominal_tx_power_dbm": None,
        "es_utc_offset_h": -3,
    }

    def __init__(self, *args, neighbors: Optional[Dict[str, List[str]]] = None, hour_of=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.neighbors = neighbors if neighbors is not None else load_neighbors()
        self.profile = SeasonalProfile()
        self.state: Dict[str, str] = {}
        self.since: Dict[str, float] = {}          # instante da última mudança de estado da célula
        self.evac_deadline: Dict[str, float] = {}
        self.retry_after: Dict[str, float] = {}       # espera depois de uma evacuação abortada
        self.tx_reduced: Dict[str, bool] = {}
        self.decisions: List[Dict[str, Any]] = []  # motivos (auditoria e testes)
        self._now: Optional[float] = None           # último instante de decisão (simulado na malha fechada)
        self.hour_of = hour_of or self._hour_utc_offset

    # ------------------------------------------------------------------ tempo
    def _hour_utc_offset(self, t: float) -> int:
        return (time.gmtime(t).tm_hour + int(self.policy().get("es_utc_offset_h", -3))) % 24

    def _set_state(self, cell: str, state: str, now: float) -> None:
        if self.state.get(cell) != state:
            self.state[cell] = state
            self.since[cell] = now

    def _dwell_ok(self, cell: str, now: float, pol: Dict[str, Any]) -> bool:
        return now - self.since.get(cell, float("-inf")) >= float(pol["es_min_dwell_s"])

    def _note(self, now: float, cell: str, what: str, reason: str) -> None:
        self.decisions.append({"t": now, "cell": cell, "decision": what, "reason": reason})

    # ------------------------------------------------------------------ entrada
    def observe(self, sample: CellSample) -> None:
        super().observe(sample)
        self.state.setdefault(sample.cell_id, ACTIVE)
        if sample.load_pct is not None and self.state[sample.cell_id] == ACTIVE:
            self.profile.update(sample.cell_id, self.hour_of(sample.t), sample.load_pct)

    def _in_window(self, hour: int, pol: Dict[str, Any]) -> bool:
        start, end = int(pol["es_sleep_start_hour"]), int(pol["es_sleep_end_hour"])
        return (start <= hour or hour < end) if start > end else (start <= hour < end)

    def _load(self, cell: str) -> float:
        s = self.samples.get(cell)
        return float(s.load_pct) if s and s.load_pct is not None else 0.0

    def _ues(self, cell: str) -> int:
        s = self.samples.get(cell)
        return s.total_ues if s else 0

    def on_result(self, result: Dict[str, Any]) -> None:
        super().on_result(result)
        cell = result.get("node_id")
        if result.get("parameter") in ("CELL_STATE", "HANDOVER") and cell in self.state:
            now = self._now if self._now is not None else self.clock()  # mesmo relógio da decisão
            self._set_state(cell, ACTIVE, now)              # recusado pela RDL: volta a ativo
            self.evac_deadline.pop(cell, None)
            self._note(now, cell, "ACTIVE", f"recusa da RDL: {result.get('reason')}")

    # ------------------------------------------------------------------ destino pela cobertura
    def _coverage_host(self, cell: str, hosts: List[str], pol: Dict[str, Any], now: float) -> Optional[str]:
        sample = self.samples.get(cell)
        if sample is None or not sample.has_ue_signal:
            self._note(now, cell, "host-by-load", "KPM sem RSRP das vizinhas por UE: destino pela menor carga")
            return min(hosts, key=self._load)
        floor = float(pol["es_min_target_rsrp_dbm"])
        best, best_min = None, float("-inf")
        for h in hosts:
            vals = [u.rsrp_dbm.get(h) for u in sample.ues]
            if any(v is None for v in vals):
                continue                                     # algum UE não mede esta vizinha
            worst = min(vals) if vals else float("inf")
            if worst >= floor and (worst > best_min or (worst == best_min and self._load(h) < self._load(best))):
                best, best_min = h, worst
        if best is None:
            self._note(now, cell, "keep", f"nenhuma vizinha cobre todos os UEs com RSRP >= {floor:g} dBm")
        else:
            self._note(now, cell, "host-by-coverage", f"{best}: menor RSRP entre os UEs {best_min:.1f} dBm")
        return best

    # ------------------------------------------------------------------ decisão
    def decide(self, now: float) -> List[Dict[str, Any]]:
        self._now = now
        pol = self.policy()
        hour = self.hour_of(now)
        nxt = (hour + 1) % 24
        sleep_thr, wake_thr = float(pol["es_sleep_threshold_pct"]), float(pol["es_wake_threshold_pct"])
        in_window = self._in_window(hour, pol)
        out: List[Dict[str, Any]] = []
        cells = sorted(set(self.samples) | set(self.state))
        active = [c for c in cells if self.state.get(c, ACTIVE) != SLEEP]

        # 1. religar (vizinha quente religa na hora; os demais motivos respeitam a permanência)
        for cell in [c for c in cells if self.state.get(c) == SLEEP]:
            neigh_hot = any(self._load(n) > wake_thr for n in self.neighbors.get(cell, []))
            expected = self.profile.expected(cell, nxt, default=0.0) or 0.0
            planned = not in_window or expected > sleep_thr
            if neigh_hot or (planned and self._dwell_ok(cell, now, pol)):
                self._set_state(cell, ACTIVE, now)
                self._note(now, cell, "wake", "vizinha acima do limiar" if neigh_hot else "fim da janela ou carga esperada")
                out.append(self._proposal(cell, "CELL_STATE", 1, 85))
        if out:
            return out

        # 2a. evacuação em curso: confirma (célula vazia) ou aborta (prazo)
        for cell in [c for c in cells if self.state.get(c) == EVACUATING]:
            if self._ues(cell) == 0:
                self._set_state(cell, SLEEP, now)
                self.evac_deadline.pop(cell, None)
                self._note(now, cell, "sleep", "evacuação confirmada: célula vazia no KPM")
                return [self._proposal(cell, "CELL_STATE", 0, 65)]
            if now >= self.evac_deadline.get(cell, float("inf")):
                self._set_state(cell, ACTIVE, now)
                self.evac_deadline.pop(cell, None)
                # nova tentativa só depois da permanência e do prazo: evita laço de evacuações frustradas
                self.retry_after[cell] = now + max(float(pol["es_min_dwell_s"]), float(pol["es_evacuation_timeout_s"]))
                self._note(now, cell, "abort", f"{self._ues(cell)} UE(s) ainda na célula depois do prazo")
            return []                                        # aguardando os handovers, ou abortou agora

        # 2b. desligar (uma célula por período)
        if in_window and len(active) > int(pol["es_min_active_cells"]):
            for cell in sorted(active, key=self._load):
                if self.state.get(cell) != ACTIVE or not self._dwell_ok(cell, now, pol) \
                        or now < self.retry_after.get(cell, float("-inf")):
                    continue
                load = self._load(cell)
                expected = self.profile.expected(cell, nxt, default=load) or 0.0
                if load >= sleep_thr or expected >= sleep_thr:
                    continue
                hosts = [n for n in self.neighbors.get(cell, []) if self.state.get(n, ACTIVE) == ACTIVE
                         and self._load(n) + load < wake_thr and _index(n) is not None]
                if not hosts:
                    continue
                if self._ues(cell) > 0:
                    host = self._coverage_host(cell, hosts, pol, now)
                    if host is None:
                        continue
                    self._set_state(cell, EVACUATING, now)
                    self.evac_deadline[cell] = now + float(pol["es_evacuation_timeout_s"])
                    return [self._proposal(cell, "HANDOVER", _index(host), 65)]
                self._set_state(cell, SLEEP, now)
                self._note(now, cell, "sleep", "célula vazia")
                return [self._proposal(cell, "CELL_STATE", 0, 65)]

        # 3. potência com histerese: uma proposta ao entrar na faixa moderada, outra (opcional) ao sair
        if pol.get("es_tx_power_reduction"):
            hyst = float(pol["es_tx_power_hysteresis_pct"])
            nominal = pol.get("es_nominal_tx_power_dbm")
            for cell in active:
                if self.state.get(cell) != ACTIVE:
                    continue
                load = self._load(cell)
                if not self.tx_reduced.get(cell) and sleep_thr <= load < 2 * sleep_thr:
                    self.tx_reduced[cell] = True
                    out.append(self._proposal(cell, "TX_POWER", float(pol["es_reduced_tx_power_dbm"]), 60))
                elif self.tx_reduced.get(cell) and load >= 2 * sleep_thr + hyst:
                    self.tx_reduced[cell] = False
                    if nominal is not None:
                        out.append(self._proposal(cell, "TX_POWER", float(nominal), 60))
        return out

    def _proposal(self, cell: str, parameter: str, value: Any, priority: int) -> Dict[str, Any]:
        return {"xapp_id": self.XAPP_ID, "node_id": cell, "parameter": parameter, "value": float(value),
                "priority": priority, "defer_ok": parameter != "HANDOVER", "ttl_ms": 2000}


def main() -> int:  # pragma: no cover - execução no RIC
    import os
    app = EnergySaver(rmr_port=int(os.getenv("RMR_PORT", "4560")))
    app.start()
    while app.running:
        time.sleep(1)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
