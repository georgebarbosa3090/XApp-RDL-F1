"""
Módulo de compatibilidade retroativa.
O núcleo do sistema foi movido para `src.core.refinement`.
"""
from src.core.refinement import Refinement, RefinementAgent

__all__ = ["Refinement", "RefinementAgent"]
