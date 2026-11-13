#!/usr/bin/env python3
"""
Modelos de potência da estação base aplicados a raw/rdl_cell_state.csv (docs/17 §4 e §5).

O ns-3 grava, por célula e janela, contadores de ocupação de REG e símbolos, somas de ocupação
ponderadas pela potência de TX e o sono emulado (RdlCellEnergySampler, rdl-nr-common.h). Aqui se
aplica o modelo de potência:

  - principal: 3GPP TR 38.864 V18.1.0, cláusula 5.1 (Cat. 1; Cat. 2 na robustez), em u.r.·s;
  - robustez: EARTH (Auer et al., 2011), um TRX de macro por célula, em J.

Por símbolo com transmissão DL, numa célula ativa, o TR dá P_static + A·Δ + (1 − A)·Δ·s_f·s_p/η,
com Δ = P4 − P_static; um símbolo sem transmissão consome P_static (micro sleep). A expressão é
afim em s_f·s_p, então a soma na janela usa só os contadores:

  E = (T_slot/N_sym)·[S_tx·(P_static + A·Δ) + (1 − A)·Δ·X·r_bw/η + (N_slot·N_sym − S_tx)·P_static]

  modo bw:   X = reg_ptx_mw ÷ (avail_rb × P_ref[mW])
  modo used: X = sym_ptx_mw ÷ P_ref[mW]

com S_tx = símbolos transmitidos fora do sono emulado e r_bw = banda do cenário ÷ banda do Set do
TR (≤ 1; 0,5 no S12, com 10 MHz contra o Set 2 de 20 MHz). Nos slots em sono emulado, a célula
consome o estado mais profundo cujo tempo total de transição é menor que a duração do episódio,
mais a energia de transição uma vez por episódio.

Os parâmetros ficam em simulations/ns3/energy/energy_models.json, conferido por sha256
(EXPECTED_SHA256). A energia é sempre "estimada pelo modelo X a partir da ocupação medida no
simulador", nunca "medida".
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODELS_PATH = ROOT / "simulations" / "ns3" / "energy" / "energy_models.json"
# sha256 do energy_models.json com finais de linha LF. Mudar um parâmetro é um commit com motivo,
# que atualiza este valor (como EXPECTED_SHA256 da curva de calibração da Fase 2).
EXPECTED_SHA256 = "81141d59a57b18872d57b31c75e1d26c2ceb414198b890aee76b200e9b7f1abc"

SleepEpisode = Tuple[int, float, float]  # (cell_id, início, fim) em segundos simulados


def file_sha256(path: Path) -> str:
    """sha256 do arquivo com CRLF normalizado para LF (o mesmo valor no Windows e no WSL)."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


@dataclass(frozen=True)
class Tr38864Model:
    """TR 38.864, cláusula 5.1: uma categoria (cat1 ou cat2) com os dois Sets de referência."""
    category: str
    states: Dict[str, Dict[str, float]]                 # Set -> estado -> u.r.
    transitions: Dict[str, Tuple[float, float]]         # estado de sono -> (tempo total s, energia u.r.·ms)
    set_by_bandwidth: Tuple[Tuple[float, str], ...]     # (banda máxima Hz, Set), em ordem crescente
    set_bandwidth_hz: Dict[str, float]                  # banda de referência de cada Set
    A: float = 0.4
    eta: float = 1.0
    static_factor: float = 1.0
    p_ref_dbm: float = 43.0

    def set_for(self, bandwidth_hz: float) -> str:
        for max_bw, name in self.set_by_bandwidth:
            if bandwidth_hz <= max_bw + 1e-6:
                return name
        return self.set_by_bandwidth[-1][1]

    def bandwidth_ratio(self, bandwidth_hz: float) -> float:
        return min(1.0, bandwidth_hz / self.set_bandwidth_hz[self.set_for(bandwidth_hz)])

    def power(self, bandwidth_hz: float, state: str) -> float:
        return float(self.states[self.set_for(bandwidth_hz)][state])

    def sleep_state(self, duration_s: float) -> str:
        """Estado mais profundo cujo tempo total de transição cabe no episódio (TR 38.864, 5.1)."""
        for state in ("deep_sleep", "light_sleep"):
            if state in self.transitions and self.transitions[state][0] < duration_s:
                return state
        return "micro_sleep"

    def transition_energy_ru_s(self, state: str) -> float:
        return self.transitions[state][1] / 1000.0 if state in self.transitions else 0.0


@dataclass(frozen=True)
class EarthModel:
    """EARTH: P_in = N_TRX·(P0 + Δp·P_out) com a célula ativa; N_TRX·P_sleep em sono."""
    n_trx: float
    p_max_w: float
    p0_w: float
    delta_p: float
    p_sleep_w: float


Model = Union[Tr38864Model, EarthModel]


def load_models(path: Path = DEFAULT_MODELS_PATH, expected_sha256: Optional[str] = EXPECTED_SHA256) -> Dict[str, Any]:
    """Lê os parâmetros; com expected_sha256, recusa um arquivo diferente do versionado."""
    path = Path(path)
    sha = file_sha256(path)
    if expected_sha256 is not None and sha != expected_sha256:
        raise ValueError(f"{path.name}: sha256 {sha} difere do esperado {expected_sha256} "
                         "(parâmetro alterado sem atualizar EXPECTED_SHA256)")
    data = json.loads(path.read_text(encoding="utf-8"))
    tr = data["tr38864"]
    scaling, mapping = tr["scaling"], tr["mapping"]
    set_by_bw = tuple(sorted((float(e["max_bandwidth_hz"]), e["set"]) for e in mapping["set_by_bandwidth"]))
    set_bw = {name: float(spec["bandwidth_hz"]) for name, spec in tr["reference_sets"].items() if name.startswith("set")}

    def tr_model(category: str) -> Tr38864Model:
        return Tr38864Model(
            category=category,
            states={s: {k: float(v) for k, v in st.items()} for s, st in tr["states"][category].items()},
            transitions={k: (float(v["time_s"]), float(v["energy_ru_ms"])) for k, v in tr["transitions"][category].items()},
            set_by_bandwidth=set_by_bw, set_bandwidth_hz=set_bw,
            A=float(scaling["A"]), eta=float(scaling["eta"]), static_factor=float(scaling["static_factor"]),
            p_ref_dbm=float(mapping["p_ref_dbm"]))

    earth = data["earth"]
    etype = earth["types"][earth["mapping"]["type"]]
    return {
        "tr1": tr_model("cat1"),
        "tr2": tr_model("cat2"),
        "earth": EarthModel(n_trx=float(earth["mapping"]["n_trx_per_cell"]), p_max_w=float(etype["p_max_w"]),
                            p0_w=float(etype["p0_w"]), delta_p=float(etype["delta_p"]), p_sleep_w=float(etype["p_sleep_w"])),
        "sha256": sha,
        "path": path,
    }


# ------------------------------------------------------------------------------- episódios de sono

def sleep_episodes_from_actuation(actuation_rows: Iterable[Dict[str, str]], end_s: float) -> List[SleepEpisode]:
    """Episódios de sono emulado a partir de CELL_STATE APPLIED no rdl_actuation_log.csv."""
    open_at: Dict[int, float] = {}
    episodes: List[SleepEpisode] = []
    for a in actuation_rows:
        if a.get("parameter") != "CELL_STATE" or a.get("status") != "APPLIED":
            continue
        cell, t, value = int(a["cell_id"]), float(a["time_s"]), float(a["value"])
        if value == 0.0:
            open_at.setdefault(cell, t)  # reaplicar o desligamento não abre outro episódio
        elif cell in open_at:
            episodes.append((cell, open_at.pop(cell), t))
    episodes += [(cell, t, max(t, end_s)) for cell, t in open_at.items()]
    return sorted(episodes, key=lambda e: (e[1], e[0]))


def sleep_episodes_from_rows(cell_rows: Sequence[Dict[str, str]]) -> List[SleepEpisode]:
    """Episódios estimados das janelas com sleep_slots > 0 (quando não há log de atuação)."""
    by_cell: Dict[int, List[Dict[str, str]]] = {}
    for r in cell_rows:
        by_cell.setdefault(int(r["cell_id"]), []).append(r)
    episodes: List[SleepEpisode] = []
    for cell, rows in by_cell.items():
        rows.sort(key=lambda r: float(r["t_end_s"]))
        start: Optional[float] = None
        end = 0.0
        for r in rows:
            sleep, slots, slot_s, t = int(r["sleep_slots"]), int(r["slots"]), float(r["slot_s"]), float(r["t_end_s"])
            if sleep > 0 and start is None:
                start, end = t - sleep * slot_s, t        # janela parcial no início: sono no fim da janela
            elif sleep > 0:
                end = t - (slots - sleep) * slot_s        # janela parcial no fim: sono no começo da janela
                if sleep < slots:
                    episodes.append((cell, start, end))
                    start = None
            elif start is not None:
                episodes.append((cell, start, end))
                start = None
        if start is not None:
            episodes.append((cell, start, end))
    return sorted(episodes, key=lambda e: (e[1], e[0]))


def merge_episodes(cell_rows: Sequence[Dict[str, str]], from_actuation: List[SleepEpisode]) -> List[SleepEpisode]:
    """Episódios do log de atuação; células com sono no CSV e sem episódio no log usam a estimativa."""
    known = {e[0] for e in from_actuation}
    fallback = [e for e in sleep_episodes_from_rows(cell_rows) if e[0] not in known]
    return sorted(from_actuation + fallback, key=lambda e: (e[1], e[0]))


# ------------------------------------------------------------------------------- energia na janela

def _in_window(rows: Iterable[Dict[str, str]], t0: float, t1: float) -> List[Dict[str, str]]:
    return [r for r in rows if t0 < float(r["t_end_s"]) <= t1]


def _episode_for(episodes: Sequence[SleepEpisode], cell: int, t_end: float, window_s: float) -> Optional[SleepEpisode]:
    t_start = t_end - window_s
    for e in episodes:
        if e[0] == cell and e[1] < t_end + 1e-9 and e[2] > t_start - 1e-9:
            return e
    return None


def _p_ref_mw(model: Tr38864Model) -> float:
    return 10.0 ** (model.p_ref_dbm / 10.0)


def energy_row_tr(r: Dict[str, str], model: Tr38864Model, bandwidth_hz: float, sleep_state: str = "deep_sleep") -> float:
    """Energia de uma linha (célula × janela) pelo TR 38.864, em u.r.·s, sem a energia de transição."""
    slot_s, n_sym = float(r["slot_s"]), int(r["sym_per_slot"])
    slots, sleep_slots = int(r["slots"]), int(r.get("sleep_slots", 0) or 0)
    p3 = model.power(bandwidth_hz, "micro_sleep")
    p4 = model.power(bandwidth_hz, "active_dl")
    p_static = model.static_factor * p3
    delta = p4 - p_static
    s_tx = int(r["data_sym"]) + int(r["ctrl_sym"]) - int(r.get("sleep_sym", 0) or 0)
    n_act = slots - sleep_slots
    if r.get("power_alloc", "used") == "bw":
        x = float(r["reg_ptx_mw"]) / (int(r["avail_rb"]) * _p_ref_mw(model))
    else:
        x = float(r["sym_ptx_mw"]) / _p_ref_mw(model)
    active = (slot_s / n_sym) * (s_tx * (p_static + model.A * delta)
                                 + (1.0 - model.A) * delta * x * model.bandwidth_ratio(bandwidth_hz) / model.eta
                                 + (n_act * n_sym - s_tx) * p_static)
    asleep = sleep_slots * slot_s * model.power(bandwidth_hz, sleep_state) if sleep_slots else 0.0
    return active + asleep


def energy_row_earth(r: Dict[str, str], model: EarthModel) -> float:
    """Energia de uma linha pelo EARTH, em J (sem energia de transição, que o EARTH não define)."""
    slot_s, n_sym = float(r["slot_s"]), int(r["sym_per_slot"])
    slots, sleep_slots = int(r["slots"]), int(r.get("sleep_slots", 0) or 0)
    n_act = slots - sleep_slots
    p_out_w = 0.0
    if n_act > 0:
        if r.get("power_alloc", "used") == "bw":
            p_out_w = float(r["reg_ptx_mw"]) / (int(r["avail_rb"]) * n_sym * n_act) / 1000.0
        else:
            p_out_w = float(r["sym_ptx_mw"]) / (n_sym * n_act) / 1000.0
    return model.n_trx * ((model.p0_w + model.delta_p * p_out_w) * n_act * slot_s + model.p_sleep_w * sleep_slots * slot_s)


def energy_window(cell_rows: Sequence[Dict[str, str]], model: Model, t0: float, t1: float,
                  sleep_episodes: Sequence[SleepEpisode] = (), bandwidth_hz: float = 100e6) -> float:
    """Σ células Σ janelas com t0 < t_end ≤ t1 (convenção de window_stats): u.r.·s (TR) ou J (EARTH)."""
    rows = _in_window(cell_rows, t0, t1)
    if isinstance(model, EarthModel):
        return sum(energy_row_earth(r, model) for r in rows)
    total = 0.0
    for r in rows:
        state = "deep_sleep"
        if int(r.get("sleep_slots", 0) or 0) > 0:
            window_s = int(r["slots"]) * float(r["slot_s"])
            ep = _episode_for(sleep_episodes, int(r["cell_id"]), float(r["t_end_s"]), window_s)
            state = model.sleep_state(ep[2] - ep[1]) if ep else model.sleep_state(window_s)
        total += energy_row_tr(r, model, bandwidth_hz, state)
    # Energia de transição: uma vez por episódio que começa na janela (os slots de sono vêm depois do início).
    for cell, start, end in sleep_episodes:
        if t0 <= start < t1:
            total += model.transition_energy_ru_s(model.sleep_state(end - start))
    return total


# ------------------------------------------------------------------------------- métricas por execução

ENERGY_METRICS = ["energy_conflict_tr1", "energy_conflict_tr2", "energy_conflict_j", "energy_conflict_fullload_s",
                  "bits_conflict", "energy_per_bit_j", "energy_per_mbit_tr1", "prb_occupancy_conflict",
                  "sleep_time_s", "sleep_leak_reg", "ul_share", "energy_proxy_commanded"]


def commanded_proxy(actuation_rows: Sequence[Dict[str, str]], n_gnbs: int, t0: float, t1: float) -> Optional[float]:
    """Nível 0, só com o log de atuação (proxy, não energia): média no tempo de Σ gNBs ligada × cota de PRB.

    A cota é o último PRB_QUOTA aplicado (÷ 100; 1 sem ação) e "ligada" vem de CELL_STATE. Unidade:
    células-equivalentes a plena cota, entre 0 e o número de gNBs. Serve só às campanhas sem
    rdl_cell_state.csv e é sempre rotulado como proxy.
    """
    if n_gnbs <= 0 or t1 <= t0:
        return None
    quota = {g: 1.0 for g in range(n_gnbs)}
    on = {g: 1.0 for g in range(n_gnbs)}
    events = sorted(((float(a["time_s"]), a) for a in actuation_rows if a.get("status") == "APPLIED"
                     and a.get("parameter") in ("PRB_QUOTA", "CELL_STATE")), key=lambda e: e[0])
    level = lambda: sum(on[g] * quota[g] for g in range(n_gnbs))
    area, t_prev, i = 0.0, t0, 0
    while i < len(events) and events[i][0] <= t0:
        _apply_proxy_event(events[i][1], quota, on)
        i += 1
    for t, a in events[i:]:
        if t >= t1:
            break
        area += level() * (t - t_prev)
        t_prev = t
        _apply_proxy_event(a, quota, on)
    area += level() * (t1 - t_prev)
    return area / (t1 - t0)


def _apply_proxy_event(a: Dict[str, str], quota: Dict[int, float], on: Dict[int, float]) -> None:
    g = int(a["gnb"])
    if g not in quota:
        return
    if a["parameter"] == "PRB_QUOTA":
        quota[g] = min(100.0, max(0.0, float(a["value"]))) / 100.0
    else:
        on[g] = 0.0 if float(a["value"]) == 0.0 else 1.0


def energy_metrics(cell_rows: Optional[Sequence[Dict[str, str]]], kpi_rows: Sequence[Dict[str, str]],
                   actuation_rows: Sequence[Dict[str, str]], models: Dict[str, Any], t0: float, t1: float,
                   bandwidth_hz: float, sim_end_s: float, n_gnbs: int) -> Dict[str, Any]:
    """Métricas da tabela 5.1 do docs/17. Sem rdl_cell_state.csv (cell_rows None), as de energia são None."""
    out: Dict[str, Any] = {k: None for k in ENERGY_METRICS}
    out["energy_proxy_commanded"] = commanded_proxy(actuation_rows, n_gnbs, t0, t1)
    out["power_alloc"] = None
    if cell_rows is None:
        return out
    episodes = merge_episodes(cell_rows, sleep_episodes_from_actuation(actuation_rows, sim_end_s))
    rows = _in_window(cell_rows, t0, t1)
    tr1, tr2, earth = models["tr1"], models["tr2"], models["earth"]
    e_tr1 = energy_window(cell_rows, tr1, t0, t1, episodes, bandwidth_hz)
    e_j = energy_window(cell_rows, earth, t0, t1, episodes, bandwidth_hz)
    bits = 8 * sum(int(r["rx_bytes"]) for r in _in_window(kpi_rows, t0, t1))
    occ_den = sum(int(r["avail_rb"]) * int(r["sym_per_slot"]) * (int(r["slots"]) - int(r["sleep_slots"])) for r in rows)
    ul = sum(int(r["ul_tb_bytes"]) for r in rows)
    dl = sum(int(r["dl_tb_bytes"]) for r in rows)
    allocs = sorted({r.get("power_alloc", "used") for r in rows})
    out.update({
        "energy_conflict_tr1": e_tr1,
        "energy_conflict_tr2": energy_window(cell_rows, tr2, t0, t1, episodes, bandwidth_hz),
        "energy_conflict_j": e_j,
        "energy_conflict_fullload_s": e_tr1 / tr1.power(bandwidth_hz, "active_dl"),
        "bits_conflict": bits,
        "energy_per_bit_j": e_j / bits if bits else None,
        "energy_per_mbit_tr1": e_tr1 / (bits / 1e6) if bits else None,
        "prb_occupancy_conflict": (sum(int(r["data_reg"]) - int(r["sleep_data_reg"]) for r in rows) / occ_den
                                   if occ_den else None),
        "sleep_time_s": sum(int(r["sleep_slots"]) * float(r["slot_s"]) for r in rows),
        "sleep_leak_reg": sum(int(r["sleep_data_reg"]) for r in rows),
        "ul_share": ul / (ul + dl) if ul + dl else None,
        "power_alloc": allocs[0] if len(allocs) == 1 else ("mixed" if allocs else None),
    })
    return out
