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

def get_ran_backend_adapter(backend_name: Optional[str] = None) -> RANBackendAdapter:
    """
    Retorna a instância concreta de RANBackendAdapter.
    Prioriza o parâmetro backend_name se informado, depois a variável de ambiente RAN_BACKEND
    e recorre a 'NORI_NS3' como padrão seguro de simulação.
    """
    selected = (backend_name or os.getenv("RAN_BACKEND", "NORI_NS3")).upper().strip()

    if selected in ("SRSRAN_OPEN5GS", "SRSRAN", "OPEN5GS", "OPENRANBR", "OPENRANBR_PHYSICAL"):
        return SrsRanBackendAdapter()
    else:
        return NoriBackendAdapter()
