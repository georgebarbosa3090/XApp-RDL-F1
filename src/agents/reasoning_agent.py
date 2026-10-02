"""
Módulo de compatibilidade retroativa.
O núcleo do sistema foi movido para `src.core.reasoning`.
"""
from src.core.reasoning import Reasoning, ReasoningAgent

__all__ = ["Reasoning", "ReasoningAgent"]
