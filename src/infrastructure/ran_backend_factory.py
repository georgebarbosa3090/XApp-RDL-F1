"""
Fábrica de Adaptadores RAN Backend (RANBackendFactory)
Instancia dinamicamente a implementação apropriada de RANBackendAdapter
com base no parâmetro de configuração ou variável de ambiente RAN_BACKEND.
"""

import os
from typing import Optional
from src.infrastructure.ran_backend_adapter import (
    RANBackendAdapter,
    NoriBackendAdapter,
    SrsRanBackendAdapter
)

SUPPORTED_BACKENDS = {
    "NORI_NS3": NoriBackendAdapter,
    "NORI": NoriBackendAdapter,
    "NS3": NoriBackendAdapter,
    "SRSRAN_OPEN5GS": SrsRanBackendAdapter,
    "SRSRAN": SrsRanBackendAdapter,
    "OPEN5GS": SrsRanBackendAdapter,
    "OPENRANBR": SrsRanBackendAdapter,
    "OPENRANBR_PHYSICAL": SrsRanBackendAdapter,
}

from src.infrastructure.ran_backend_adapter import UnsupportedBackendError

def get_ran_backend_adapter(backend_name: Optional[str] = None) -> RANBackendAdapter:
    """
    Retorna a instância concreta de RANBackendAdapter.
    Prioriza o parâmetro backend_name se informado, depois a variável de ambiente RAN_BACKEND.
    Em modo O_RAN_INTEROP / ORAN-STRICT, exige a especificação explícita de RAN_BACKEND.
    Lança UnsupportedBackendError se o backend for desconhecido ou não especificado em modo estrito.
    """
    rdl_mode = os.getenv("RDL_MODE", "").upper().strip()
    env_backend = os.getenv("RAN_BACKEND", "").strip()

    if rdl_mode in ("O_RAN_INTEROP", "ORAN-STRICT", "ORAN_STRICT", "STRICT") and not backend_name and not env_backend:
        raise UnsupportedBackendError(
            "Em modo O_RAN_INTEROP / ORAN-STRICT, a variável de ambiente RAN_BACKEND deve ser "
            "explicitamente definida (ex: 'SRSRAN_OPEN5GS' ou 'NORI_NS3'). O fallback padrão é proibido."
        )

    selected = (backend_name or env_backend or "NORI_NS3").upper().strip()

    if selected not in SUPPORTED_BACKENDS:
        raise UnsupportedBackendError(
            f"Backend RAN não suportado: '{selected}'. "
            f"Valores suportados: {list(set(SUPPORTED_BACKENDS.keys()))}"
        )

    adapter_cls = SUPPORTED_BACKENDS[selected]
    return adapter_cls()

