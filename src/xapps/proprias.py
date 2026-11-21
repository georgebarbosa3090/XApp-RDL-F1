# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
xApps próprias para os papéis do catálogo sem original público (docs/16, decisão D2), guiadas por KPM:

- ``LoadBalancer``: se a carga de uma célula passa da vizinha menos carregada em ``lb_imbalance_pct``
  pontos, propõe o handover de **parte** dos UEs dela para essa vizinha: os de menor diferença de RSRP
  entre a servidora e a vizinha (a vizinha no máximo ``lb_max_rsrp_gap_db`` = 3 dB pior que a servidora,
  docs/16 §10.13), em quantidade proporcional à metade
  da diferença de carga e no máximo ``lb_max_ues``, com um pedido por UE (docs/16 §10.11). Sem RSRP por UE
  no KPM, propõe o handover da célula, como antes. Cada UE só é transferido depois de cumprir a condição
  por ``lb_ttt_s`` (tempo de disparo, como no evento A3). O ramo que abre a cota de PRB com desequilíbrio
  moderado fica desligado por padrão (``lb_open_cap_enabled``; docs/16 §10.16).
- ``Beamformer``: se o SINR médio dos UEs da célula cai abaixo de ``bf_min_sinr_db``, propõe subir a
  potência em ``bf_step_db`` (até a nominal medida mais ``bf_max_boost_db``, e no máximo ``bf_max_tx_dbm``);
  com SINR folgado, propõe voltar à nominal. A potência em vigor vem do KPM quando ele a traz.
- ``IsacRadar``: reserva recursos de sensoriamento: em intervalos de ``isac_period_s``, propõe a cota de
  PRB ``isac_sensing_cap_pct`` na célula de sensoriamento, exceto quando a carga passa de
  ``isac_max_load_pct`` (cede ao tráfego).
- ``EmbbThroughput``: se a vazão da fatia eMBB fica abaixo de ``embb_target_mbps``, propõe abrir a cota de
  PRB da célula para ``embb_cap_pct``.
- ``UrllcSliceGuard`` (URLLC Slice Guard): protege a fatia URLLC limitando a fatia eMBB da célula quando o
  atraso da URLLC passa do limite; faz o papel do xSlice no catálogo (até 2026-11-21, ``XSliceDerivada``).
"""

import math
from typing import Any, Dict, List, Optional

from src.xapps.derivadas import _Kpm, _index


class LoadBalancer(_Kpm):
    XAPP_ID = "load_balancer"
    A1_TYPE = ""
    """Balanceamento de carga por handover, no estilo do MLB do 3GPP (docs/16 §10.16).

    A condição de transferência de um UE é a do evento A3 com deslocamento de célula (CIO):
    ``RSRP_vizinha + lb_max_rsrp_gap_db >= RSRP_servidora``, mantida por ``lb_ttt_s`` (tempo de disparo, um dos
    valores de ``TimeToTrigger`` do 3GPP TS 38.331: 640 ms), enquanto o desequilíbrio de carga persistir. Os
    parâmetros ficam fixos antes da rodada valendo. O ramo que abre o teto de PRB com desequilíbrio moderado não
    tem relação com balanceamento por handover e gerava conflitos espúrios com o TS (13 resoluções no N12 do P3;
    comparativo das xApps, seção 4.1). Por isso fica desligado por padrão (``lb_open_cap_enabled``)."""

    XAPP_ID = "load_balancer"
    A1_TYPE = ""
    DEFAULTS: Dict[str, Any] = {"lb_imbalance_pct": 30.0, "lb_moderate_pct": 15.0, "lb_open_cap_pct": 90.0,
                                "lb_open_cap_enabled": False, "lb_cooldown_s": 5.0, "lb_priority": 70,
                                "lb_max_ues": 4, "lb_max_rsrp_gap_db": 3.0, "lb_ttt_s": 0.64}

    def __init__(self, *a, neighbors: Optional[Dict[str, List[str]]] = None, **k):
        super().__init__(*a, **k)
        self.neighbors = neighbors or {}
        self.last: Dict[str, float] = {}
        self.a3_since: Dict[str, Dict[str, float]] = {}   # célula -> UE -> início da condição A3 (TTT)

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol, out = self.policy(), []
        loads = {c: s.load_pct for c, s in self.samples.items() if s.load_pct is not None}
        for cell, load in sorted(loads.items()):
            if now - self.last.get(cell, float("-inf")) < float(pol["lb_cooldown_s"]):
                continue
            neigh = [n for n in (self.neighbors.get(cell) or [c for c in loads if c != cell]) if n in loads]
            if not neigh:
                continue
            light = min(neigh, key=lambda n: loads[n])
            gap = load - loads[light]
            if gap >= float(pol["lb_imbalance_pct"]) and _index(light) is not None:
                moves = self._ues_to_move(cell, light, load, gap, pol, now)
                if moves is None:          # sem RSRP por UE: handover da célula (comportamento anterior)
                    self.last[cell] = now
                    out.append(self._proposal(cell, "HANDOVER", _index(light), pol["lb_priority"]))
                elif moves:
                    self.last[cell] = now
                    self.a3_since.pop(cell, None)
                    out += [self._proposal(cell, "HANDOVER", _index(light), pol["lb_priority"], ue=ue)
                            for ue in moves]
                continue
            self.a3_since.pop(cell, None)                  # sem desequilíbrio: o TTT recomeça
            if pol.get("lb_open_cap_enabled") and gap >= float(pol["lb_moderate_pct"]):
                self.last[cell] = now
                out.append(self._proposal(cell, "PRB_QUOTA", pol["lb_open_cap_pct"], pol["lb_priority"]))
        return out

    def _ues_to_move(self, cell: str, light: str, load: float, gap: float,
                     pol: Dict[str, Any], now: float = 0.0) -> Optional[List[int]]:
        """UEs a transferir da célula carregada para a vizinha: os que cumprem a condição A3 com CIO (a vizinha no
        máximo ``lb_max_rsrp_gap_db`` pior que a servidora; docs/16 §10.12 e §10.13) há pelo menos ``lb_ttt_s``, em
        ordem de menor diferença de RSRP; quantos: a fração ``gap / (2 load)`` dos UEs da célula, ao menos um e no
        máximo ``lb_max_ues``. ``None`` quando o KPM não traz RSRP por UE; lista vazia quando nenhum UE ouve a
        vizinha o bastante pelo tempo de disparo."""
        ues = [u for u in self.samples[cell].ues if light in u.rsrp_dbm and cell in u.rsrp_dbm]
        if not ues:
            return None
        deficit = lambda u: u.rsrp_dbm[cell] - u.rsrp_dbm[light]  # noqa: E731
        cond = [u for u in ues if deficit(u) <= float(pol["lb_max_rsrp_gap_db"])]
        since = self.a3_since.setdefault(cell, {})
        for ue_id in list(since):
            if ue_id not in {u.ue_id for u in cond}:
                del since[ue_id]                           # a condição caiu: o TTT recomeça
        for u in cond:
            since.setdefault(u.ue_id, now)
        ttt = float(pol["lb_ttt_s"])
        ok = sorted((u for u in cond if now - since[u.ue_id] >= ttt - 1e-9),
                    key=lambda u: (deficit(u), u.ue_id))
        share = gap / (2.0 * load) if load > 0 else 0.0
        k = min(int(pol["lb_max_ues"]), max(1, math.ceil(share * len(self.samples[cell].ues))))
        out = []
        for u in ok[:k]:
            try:
                out.append(int(u.ue_id))
            except (TypeError, ValueError):
                continue
        return out


class Beamformer(_Kpm):
    XAPP_ID = "beamformer"
    A1_TYPE = ""
    """Potência de referência (docs/16 §10.16): a nominal é a primeira potência medida da célula no KPM (sem a
    medida, ``bf_nominal_tx_dbm``), e o máximo é a nominal mais ``bf_max_boost_db``, limitado a ``bf_max_tx_dbm``.
    A potência atual é a medida no KPM; sem ela, a última proposta. Antes, nominal e máximo eram ambos 43 dBm e a
    potência de referência começava na nominal: nenhuma das duas condições podia ser verdadeira e a xApp nunca
    propunha (S6, docs/16 §10.7)."""

    DEFAULTS: Dict[str, Any] = {"bf_min_sinr_db": 10.0, "bf_ok_sinr_db": 20.0, "bf_step_db": 3.0,
                                "bf_nominal_tx_dbm": 37.0, "bf_max_tx_dbm": 43.0, "bf_max_boost_db": 6.0,
                                "bf_priority": 70}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.tx: Dict[str, float] = {}
        self.nominal: Dict[str, float] = {}

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol, out = self.policy(), []
        for cell, s in sorted(self.samples.items()):
            sinrs = [u.sinr_db for u in s.ues if u.sinr_db is not None]
            if not sinrs:
                continue
            mean = sum(sinrs) / len(sinrs)
            nominal = self.nominal.setdefault(
                cell, float(s.tx_power_dbm) if s.tx_power_dbm is not None else float(pol["bf_nominal_tx_dbm"]))
            top = min(nominal + float(pol["bf_max_boost_db"]), float(pol["bf_max_tx_dbm"]))
            cur = float(s.tx_power_dbm) if s.tx_power_dbm is not None else self.tx.get(cell, nominal)
            if mean < float(pol["bf_min_sinr_db"]) and cur < top:
                new = min(cur + float(pol["bf_step_db"]), top)
            elif mean > float(pol["bf_ok_sinr_db"]) and cur > nominal:
                new = nominal
            else:
                continue
            self.tx[cell] = new
            out.append(self._proposal(cell, "TX_POWER", new, pol["bf_priority"]))
        return out


class IsacRadar(_Kpm):
    XAPP_ID = "isac_radar"
    A1_TYPE = ""
    DEFAULTS: Dict[str, Any] = {"isac_period_s": 5.0, "isac_sensing_cap_pct": 40.0, "isac_max_load_pct": 80.0,
                                "isac_cells": None, "isac_priority": 85}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.next_t: Dict[str, float] = {}

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol, out = self.policy(), []
        cells = pol.get("isac_cells") or sorted(self.samples)
        for cell in cells:
            s = self.samples.get(cell)
            if s is None or now < self.next_t.get(cell, float("-inf")):
                continue
            self.next_t[cell] = now + float(pol["isac_period_s"])
            if (s.load_pct or 0.0) <= float(pol["isac_max_load_pct"]):
                out.append(self._proposal(cell, "PRB_QUOTA", pol["isac_sensing_cap_pct"], pol["isac_priority"]))
        return out


class EmbbThroughput(_Kpm):
    XAPP_ID = "embb_throughput"
    A1_TYPE = ""
    DEFAULTS: Dict[str, Any] = {"embb_sst": 1, "embb_target_mbps": 20.0, "embb_cap_pct": 80.0, "embb_priority": 60}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.open: Dict[str, bool] = {}

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol, out = self.policy(), []
        for cell, s in sorted(self.samples.items()):
            embb = s.slices.get(int(pol["embb_sst"]))
            if embb is None or embb.ues == 0:
                continue
            short = embb.thp_mbps < float(pol["embb_target_mbps"])
            if short and not self.open.get(cell):
                self.open[cell] = True
                out.append(self._proposal(cell, "PRB_QUOTA", pol["embb_cap_pct"], pol["embb_priority"]))
            elif not short:
                self.open[cell] = False
        return out


class UrllcSliceGuard(_Kpm):
    """URLLC Slice Guard: protege a fatia URLLC (SST ``usg_urllc_sst``) limitando a fatia eMBB da célula.

    Entradas, todas medidas no KPM da célula: o atraso por UE (``DRB.RlcSduDelayDl``) agregado por fatia pelo SST
    que o próprio KPM informa (``DRB.NetworkSlicing.SST``; na malha fechada, o campo ``sst`` do ns-3). Não há
    componente emulado: a xApp não depende de modelo treinado, de predição nem de outra xApp.

    Regra:
    - **proteger:** atraso máximo da URLLC acima de ``usg_max_delay_ms`` -> teto eMBB ``usg_protect_cap_pct``
      (convenção da RDL: ``PRB_QUOTA`` = parcela da eMBB), prioridade ``usg_priority``;
    - **relaxar (histerese):** depois de ``usg_relax_windows`` janelas seguidas com o atraso abaixo de
      ``usg_relax_delay_frac`` do limite -> teto ``usg_relax_cap_pct``, prioridade ``usg_relax_priority``. Se a
      proteção volta em até ``usg_relax_windows`` janelas depois de relaxar, o número de janelas exigido dobra,
      até ``usg_relax_windows_max``. No S2 (semente 16908), o atraso protegido ficava em ~9 ms com limite de
      10 ms: sem histerese, o teto oscilava 25 -> 80 -> 25 % a cada ~1,4 s (comparativo das xApps, seção 3.2);
    - **recusa** (``on_result``): a proposta não aplicada devolve a célula ao estado anterior, e a xApp volta a
      propor enquanto a condição durar.

    Origem: até 2026-11-21 era ``XSliceDerivada`` (``xapp_id`` ``xslice``), uma reimplementação inspirada no xSlice
    (``peihaoY/xslice-oran``). Ela não reproduzia o xSlice, cuja decisão é de um agente PPO com GCN; por isso
    passou a ser declarada como xApp própria, com nome próprio. Faz o papel ``xslice`` do catálogo de cenários.
    """

    XAPP_ID = "urllc_slice_guard"
    A1_TYPE = ""  # sem tipo A1 próprio: usa os padrões
    DEFAULTS: Dict[str, Any] = {"usg_urllc_sst": 2, "usg_max_delay_ms": 10.0, "usg_protect_cap_pct": 25.0,
                                "usg_relax_cap_pct": 80.0, "usg_relax_windows": 5, "usg_relax_delay_frac": 0.7,
                                "usg_relax_windows_max": 40, "usg_priority": 90, "usg_relax_priority": 60}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.protecting: Dict[str, bool] = {}
        self.ok_windows: Dict[str, int] = {}
        self.need_windows: Dict[str, int] = {}
        self.since_relax: Dict[str, int] = {}      # janelas desde o último relaxamento
        self.pending: Dict[str, bool] = {}         # estado anterior à última proposta, até o resultado
        self.last_delay_ms: Dict[str, float] = {}  # atraso URLLC medido (para as métricas da xApp)
        self.cap_pct: Dict[str, float] = {}        # último teto proposto por célula

    def decide(self, now: float) -> List[Dict[str, Any]]:
        pol, out = self.policy(), []
        base = int(pol["usg_relax_windows"])
        limit = float(pol["usg_max_delay_ms"])
        for cell, s in sorted(self.samples.items()):
            urllc = s.slices.get(int(pol["usg_urllc_sst"]))
            if urllc is None or urllc.ues == 0 or urllc.delay_ms is None:
                continue
            self.last_delay_ms[cell] = urllc.delay_ms
            need = self.need_windows.setdefault(cell, base)
            if cell in self.since_relax:
                self.since_relax[cell] += 1
            if urllc.delay_ms > limit:
                self.ok_windows[cell] = 0
                if not self.protecting.get(cell):
                    if self.since_relax.get(cell, base + 1) <= base:      # relaxar recriou o risco
                        self.need_windows[cell] = min(2 * need, int(pol["usg_relax_windows_max"]))
                    self.pending[cell] = False
                    self.protecting[cell] = True
                    self.cap_pct[cell] = float(pol["usg_protect_cap_pct"])
                    out.append(self._proposal(cell, "PRB_QUOTA", pol["usg_protect_cap_pct"], pol["usg_priority"]))
            elif self.protecting.get(cell):
                calm = urllc.delay_ms <= float(pol["usg_relax_delay_frac"]) * limit
                self.ok_windows[cell] = self.ok_windows.get(cell, 0) + 1 if calm else 0
                if self.ok_windows[cell] >= need:
                    self.pending[cell] = True
                    self.protecting[cell] = False
                    self.ok_windows[cell] = 0
                    self.since_relax[cell] = 0
                    self.cap_pct[cell] = float(pol["usg_relax_cap_pct"])
                    out.append(self._proposal(cell, "PRB_QUOTA", pol["usg_relax_cap_pct"],
                                              pol["usg_relax_priority"]))
        return out

    def on_result(self, result: Dict[str, Any]) -> None:
        super().on_result(result)
        cell = result.get("node_id")
        if result.get("parameter") == "PRB_QUOTA" and cell in self.pending:
            self.protecting[cell] = self.pending.pop(cell)           # recusada: o teto em vigor é o anterior
            self.since_relax.pop(cell, None)
            self.ok_windows[cell] = 0
            self.cap_pct.pop(cell, None)
