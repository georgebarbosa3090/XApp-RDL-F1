"""
Módulo de Adaptadores de Backend de Rádio para a xApp-RDL.
"""

from src.e2.backends.backend_interface import (
    RadioBackendAdapter,
    KpmMetrics,
    ControlResult,
    RanPhysicalState
)
from src.e2.backends.srsran_e2_adapter import SrsranE2Adapter
from src.e2.backends.zmq_virtual_adapter import ZmqVirtualAdapter

__all__ = [
    "RadioBackendAdapter",
    "KpmMetrics",
    "ControlResult",
    "RanPhysicalState",
    "SrsranE2Adapter",
    "ZmqVirtualAdapter"
]
