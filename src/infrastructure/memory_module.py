import time
from typing import List, Dict, Any
from src.observability.logging import setup_logger

logger = setup_logger("MemoryModule")

class MemoryModule:
    """
    Fallback em memória para o SDL. Usado para desenvolvimento, 
    testes e apresentações (quando USE_FAKE_SDL=true).
    Implementa as interfaces estritas exigidas pela RDL.
    """
    def __init__(self):
        self._actions = []
        self._conflicts = []
        self._resolutions = []
        logger.info("MemoryModule (Fallback) inicializado. Dados serão perdidos no restart.")

    def add_action(self, action):
        logger.debug(f"[MEMORY] Salvando Ação: {action.parameter}={action.value}")
        self._actions.append(action)

    def add_conflict(self, conflict):
        logger.debug(f"[MEMORY] Registrando Conflito: {conflict.conflict_type.name}")
        self._conflicts.append(conflict)

    def add_resolution(self, resolution):
        logger.debug(f"[MEMORY] Registrando Resolução (Estratégia: {resolution.strategy_used.name})")
        self._resolutions.append(resolution)

    def get_similar_resolutions(self, conflict) -> list:
        # Mock para busca histórica: sempre retorna vazio para forçar as políticas SLA/MARL
        return []

    def get_recent_actions(self, n=50) -> list:
        return self._actions[-n:]
