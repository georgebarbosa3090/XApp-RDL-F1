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
    Lança UnsupportedBackendError se o backend for desconhecido.
    """
    selected = (backend_name or os.getenv("RAN_BACKEND", "NORI_NS3")).upper().strip()

    if selected not in SUPPORTED_BACKENDS:
        raise UnsupportedBackendError(
            f"Backend RAN não suportado: '{selected}'. "
            f"Valores suportados: {list(set(SUPPORTED_BACKENDS.keys()))}"
        )

    adapter_cls = SUPPORTED_BACKENDS[selected]
    return adapter_cls()
