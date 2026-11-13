#!/usr/bin/env python3
# Autor: George Barbosa
"""
Driver das xApps originais do FlexRIC na malha fechada (docs/16 §4.1, §4.2 e §7.1).

Lança o binário original da xApp ligado ao libe42_shim (xapps-originais/shim), conversa com ele pelo
protocolo de texto descrito em e42_shim.c e converte o RC Control que sai em propostas da RDL.

Mapeamento do controle (folhas da árvore de RAN Parameters do E2SM-RC, caminho de IDs = valor):
  - ES Orange, Handover Control (estilo 3, ação 1): a célula de destino vem na única folha octet string
    (NR CGI = caractere '1'..'9'). O UE vem como ID local da célula (o shim reporta IDs 0..19 por célula,
    limite do ES); a origem é a célula, diferente do destino, em que esse ID local foi reportado na última
    janela, com menos UEs (a única que pode ser candidata pelo critério do ES). Vira HANDOVER do UE global.
  - ES Orange, desligamento (estilo ENERGY_STATE): a célula vem na folha octet string. Vira CELL_STATE = 0.
  - xSlice, Slice-level PRB quota (estilo 2, ação 6): as listas RRM_Policy_Ratio trazem o PRB dedicado de cada
    fatia; vira PRB_QUOTA conforme o mapeamento fatia -> teto da célula do cenário (driver_config).
"""

from __future__ import annotations

import os
import re
import socket
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from scripts.closed_loop.drivers import XAppDriver

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CTRL_RE = re.compile(r"^CTRL (-?\d+) (-?\d+) (-?\d+) (\d+)(.*)$")


def parse_leaves(text: str) -> Dict[str, Tuple[str, Any]]:
    """' 1/2/3=s:31 7=i:40' -> {'1/2/3': ('s', '1'), '7': ('i', 40)}; octet strings em hexa viram texto."""
    out: Dict[str, Tuple[str, Any]] = {}
    for tok in text.split():
        path, _, val = tok.partition("=")
        kind, _, raw = val.partition(":")
        if kind == "i":
            out[path] = ("i", int(raw))
        elif kind == "r":
            out[path] = ("r", float(raw))
        elif kind == "b":
            out[path] = ("b", bool(int(raw)))
        elif kind == "s":
            out[path] = ("s", bytes.fromhex(raw).decode("latin-1"))
    return out


class EsIdMap:
    """IDs locais por célula que o shim reporta ao ES Orange (0..19, ordem do índice global do UE)."""

    LIMIT = 20

    def __init__(self):
        self.by_cell: Dict[int, List[int]] = {}

    def update(self, kpm: Dict[str, Any]) -> None:
        self.by_cell = {}
        for u in sorted(kpm.get("ues", []), key=lambda u: u["ue"]):
            if u.get("connected"):
                lst = self.by_cell.setdefault(int(u["cell_id"]), [])
                if len(lst) < self.LIMIT:
                    lst.append(int(u["ue"]))

    def resolve(self, local_id: int, target_cell: int) -> Optional[Tuple[int, int]]:
        """(UE global, célula de origem) do handover; None se ausente ou ambíguo."""
        cands = [(len(ues), cell, ues[local_id]) for cell, ues in self.by_cell.items()
                 if cell != target_cell and 0 <= local_id < len(ues)]
        if not cands:
            return None
        cands.sort()
        if len(cands) > 1 and cands[0][0] == cands[1][0]:
            return None
        _, cell, ue = cands[0]
        return ue, cell


class FlexricXAppDriver(XAppDriver):
    """Uma xApp original do FlexRIC (processo) ligada ao libe42_shim."""

    def __init__(self, name: str, xapp_id: str, binary: str, profile: str, priority: int,
                 workdir: str, extra_env: Optional[Dict[str, str]] = None, slice_map: Optional[Dict] = None):
        self.name = name
        self.xapp_id = xapp_id
        self.binary = binary
        self.profile = profile
        self.priority = priority
        self.workdir = workdir
        self.extra_env = extra_env or {}
        self.slice_map = slice_map or {}
        self.ids = EsIdMap()
        self.gnb_of_cell: Dict[int, int] = {}
        self.proc: Optional[subprocess.Popen] = None
        self.conn: Optional[socket.socket] = None
        self.rfile = None
        self.log: List[Dict[str, Any]] = []
        self._seq = 0

    # ------------------------------------------------------------------ ciclo de vida
    def on_hello(self, hello: Dict[str, Any]) -> None:
        sock_path = os.path.join(tempfile.gettempdir(), f"rdl_shim_{os.getpid()}_{self.name}.sock")
        if os.path.exists(sock_path):
            os.remove(sock_path)
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(sock_path)
        srv.listen(1)
        env = dict(os.environ, RDL_SHIM_SOCKET=sock_path, RDL_SHIM_PROFILE=self.profile, **self.extra_env)
        os.makedirs(self.workdir, exist_ok=True)
        self.proc = subprocess.Popen([self.binary], cwd=self.workdir, env=env,
                                     stdout=open(os.path.join(self.workdir, "xapp_stdout.log"), "w"),
                                     stderr=subprocess.STDOUT)
        srv.settimeout(60)
        self.conn, _ = srv.accept()
        srv.close()
        os.remove(sock_path)
        self.rfile = self.conn.makefile("r", encoding="latin-1")
        self.gnb_of_cell = {int(g["cell_id"]): int(g["gnb"]) for g in hello["gnbs"]}
        lines = [f"HELLO {len(hello['gnbs'])} {hello['window']}"]
        lines += [f"GNB {g['gnb']} {g['cell_id']}" for g in hello["gnbs"]]
        self.conn.sendall(("\n".join(lines + ["ENDHELLO"]) + "\n").encode())

    def close(self) -> None:
        try:
            if self.conn:
                self.conn.sendall(b"END\n")
        except OSError:
            pass
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    # ------------------------------------------------------------------ janela
    @staticmethod
    def _fmt(v) -> str:
        return "nan" if v is None else f"{float(v):.4f}"

    def on_kpm(self, kpm: Dict[str, Any]) -> List[Dict[str, Any]]:
        self.ids.update(kpm)
        lines = [f"WIN {kpm['t']}"]
        for u in kpm.get("ues", []):
            rsrp = u.get("rsrp_dbm", {})
            parts = [f"UE {u['ue']} {u['cell_id']} {1 if u.get('connected') else 0}", self._fmt(u.get("thp_mbps")),
                     self._fmt(u.get("delay_ms")), self._fmt(u.get("sinr_db")), str(len(rsrp))]
            parts += [f"{c} {self._fmt(r)}" for c, r in rsrp.items()]
            lines.append(" ".join(parts))
        self.conn.sendall(("\n".join(lines + ["ENDWIN"]) + "\n").encode())
        proposals: List[Dict[str, Any]] = []
        while True:
            line = self.rfile.readline()
            if not line:
                raise RuntimeError(f"xApp {self.name} encerrou (ver {self.workdir}/xapp_stdout.log)")
            line = line.rstrip("\n")
            if line == "DONE":
                break
            m = CTRL_RE.match(line)
            if not m:
                continue
            style, act, ue = int(m.group(1)), int(m.group(2)), int(m.group(3))
            leaves = parse_leaves(m.group(5))
            prop, note = self.map_control(style, act, ue, leaves, float(kpm["t"]))
            self.log.append({"t": kpm["t"], "ctrl": line, "proposal": prop, "note": note})
            if prop:
                proposals.append(prop)
        return proposals

    # ------------------------------------------------------------------ RC -> proposta
    def _proposal(self, t: float, gnb: int, parameter: str, value: float, ue: int = -1) -> Dict[str, Any]:
        self._seq += 1
        return {"t": t, "xapp_id": self.xapp_id, "gnb": gnb, "parameter": parameter, "value": float(value),
                "priority": self.priority, "ue": ue, "id": f"{self.xapp_id}-{parameter}-{t:.3f}-{self._seq}"}

    def map_control(self, style: int, act: int, ue: int, leaves: Dict[str, Tuple[str, Any]],
                    t: float) -> Tuple[Optional[Dict[str, Any]], str]:
        strings = [v for k, v in leaves.values() if k == "s"]
        if self.profile == "es":
            cell_txt = next((s for s in strings if len(s) == 1 and s.isdigit()), None)
            if cell_txt is None:
                return None, "sem célula no controle"
            cell = int(cell_txt)
            if cell not in self.gnb_of_cell:
                return None, f"célula {cell} inexistente"
            if style == 3 and act == 1:  # Connected Mode Mobility / Handover Control
                hit = self.ids.resolve(ue, cell)
                if hit is None:
                    return None, f"UE local {ue} ambíguo ou ausente"
                ue_global, src_cell = hit
                return self._proposal(t, self.gnb_of_cell[src_cell], "HANDOVER", self.gnb_of_cell[cell],
                                      ue=ue_global), f"UE local {ue} -> global {ue_global}"
            return self._proposal(t, self.gnb_of_cell[cell], "CELL_STATE", 0), f"estilo {style} ação {act}"
        if self.profile == "xslice" and style == 2 and act == 6:
            ded = sorted((k, v) for k, (kind, v) in leaves.items() if kind == "i" and k.endswith(
                str(self.slice_map.get("dedicated_param_id", 12))))
            idx = int(self.slice_map.get("slice_index", 0))
            if idx >= len(ded):
                return None, "fatia ausente no controle"
            gnb = int(self.slice_map.get("gnb", 0))
            return self._proposal(t, gnb, "PRB_QUOTA", ded[idx][1]), f"fatia {idx} dedicado {ded[idx][1]}"
        return None, f"controle sem mapeamento (estilo {style}, ação {act})"
