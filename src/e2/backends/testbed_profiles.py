# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
Perfis de backend do testbed UFPA (doc 12 §4): NORI (referência verificada), srsRAN Project (laboratório
GERCOM) e OpenAirInterface com agente E2 do FlexRIC (laboratório LACIS).

Os dois laboratórios usam pilhas diferentes; a escolha final fica para depois da implantação do projeto.
O código da RDL, da kpm-probe e das xApps do GreenRAN não muda entre eles: muda o perfil
(``configs/testbed_ufpa/backends/*.yaml``):

- nomes das métricas KPM (``kpm_metrics``), usados por ``src/greenran/common.normalize_kpm``;
- RAN Function IDs e IDs dos RAN Parameters da cota de PRB (``rc_slice_param_ids``), usados pelo codec
  (``E2smCodec.rc_slice_quota_message(..., param_ids=...)``);
- canais de potência e de desligamento de célula, ainda sem definição nas atividades A1.2/A1.3.

``pending_fields`` lista o que está ``A_CONFIRMAR``: com qualquer pendência o gate TB0 (perfil congelado)
não passa.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

PROFILE_DIR = Path(__file__).resolve().parents[3] / "configs" / "testbed_ufpa" / "backends"
PROFILES = {"NORI_NS3": "nori_ns3.yaml", "SRSRAN_PROJECT": "srsran_gercom.yaml", "OAI_FLEXRIC": "oai_lacis.yaml"}
PENDING = "A_CONFIRMAR"
SUPPORTED_LAYOUTS = ("nori_flat",)


def load_profile(name_or_path: str) -> Dict[str, Any]:
    path = Path(name_or_path)
    if not path.is_file():
        key = name_or_path.upper()
        if key not in PROFILES:
            raise ValueError(f"perfil de backend desconhecido: {name_or_path} (use {sorted(PROFILES)} ou um caminho)")
        path = PROFILE_DIR / PROFILES[key]
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "backend" not in data:
        raise ValueError(f"perfil inválido: {path}")
    return data


def pending_fields(profile: Dict[str, Any], prefix: str = "") -> List[str]:
    """Caminhos dos campos ainda ``A_CONFIRMAR`` (gate TB0)."""
    out: List[str] = []
    for key, value in profile.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            out += pending_fields(value, path + ".")
        elif value == PENDING:
            out.append(path)
    return out


def tb0_ready(profile: Dict[str, Any]) -> bool:
    return not pending_fields(profile)


def kpm_metrics(profile: Dict[str, Any]) -> Dict[str, str]:
    """Mapa de métricas para ``normalize_kpm``; campos pendentes ficam de fora (vale o padrão do NORI)."""
    return {k: v for k, v in ((profile.get("kpm") or {}).get("metrics") or {}).items() if v != PENDING}


def rc_slice_param_ids(profile: Dict[str, Any]) -> Optional[Dict[str, int]]:
    """IDs dos RAN Parameters da cota de PRB, ou ``None`` se ainda não confirmados (o despacho deve falhar fechado)."""
    quota = (profile.get("rc") or {}).get("prb_quota") or {}
    layout, ids = quota.get("layout"), quota.get("param_ids")
    if layout == PENDING or ids == PENDING or not isinstance(ids, dict):
        return None
    if layout not in SUPPORTED_LAYOUTS:
        raise ValueError(f"leiaute de cota de PRB ainda não implementado no codec: {layout}")
    return {k: int(v) for k, v in ids.items()}


def summary(profile: Dict[str, Any]) -> Dict[str, Any]:
    pend = pending_fields(profile)
    return {"backend": profile["backend"], "lab": profile.get("lab"), "verified": bool(profile.get("verified")),
            "tb0_ready": not pend, "pending": pend, "rc_slice_param_ids": rc_slice_param_ids(profile)}
