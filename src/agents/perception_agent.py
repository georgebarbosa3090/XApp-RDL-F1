"""
Módulo de compatibilidade retroativa.
O núcleo do sistema foi movido para `src.core.perception`.
"""
from src.core.perception import Perception, PerceptionAgent

__all__ = ["Perception", "PerceptionAgent"]
