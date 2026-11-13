import time
from typing import List, Dict, Any, Optional
from src.observability.logging import setup_logger

logger = setup_logger("MemoryModule")


class MemoryModule:
    """
    Fallback em memória para o SDL. Usado para desenvolvimento,
    testes e apresentações (quando USE_FAKE_SDL=true).
    Implementa as interfaces estritas exigidas pela RDL com janela limitada anti-leak.
    """
    MAX_HISTORY = 5000

    def __init__(self):
        self._actions: List[Any] = []
        self._conflicts: List[Any] = []
        self._resolutions: List[Any] = []
        self._control_requests: Dict[str, Dict[str, Any]] = {}
        self._rollbacks: Dict[str, Dict[str, Any]] = {}
        logger.info("MemoryModule (Fallback) inicializado. Dados serão perdidos no restart.")

    def add_action(self, action):
        logger.debug(f"[MEMORY] Salvando Ação: {action.parameter}={action.value}")
        self._actions.append(action)
        if len(self._actions) > self.MAX_HISTORY:
            self._actions = self._actions[-self.MAX_HISTORY:]

    def add_conflict(self, conflict):
        logger.debug(f"[MEMORY] Registrando Conflito: {conflict.conflict_type.name}")
        self._conflicts.append(conflict)
        if len(self._conflicts) > self.MAX_HISTORY:
            self._conflicts = self._conflicts[-self.MAX_HISTORY:]

    def add_resolution(self, resolution):
        logger.debug(f"[MEMORY] Registrando Resolução (Estratégia: {resolution.strategy_used.name})")
        self._resolutions.append(resolution)
        if len(self._resolutions) > self.MAX_HISTORY:
            self._resolutions = self._resolutions[-self.MAX_HISTORY:]

    def get_similar_resolutions(self, conflict) -> list:
        # Retorna vazio por padrão para acionar as regras TVS/EEVS
        return []

    def save_rejection(self, rejection_id: str, data: dict):
        """Proposta não atendida (registro de recusas); janela limitada como o restante."""
        rejections = getattr(self, "_rejections", None)
        if rejections is None:
            rejections = self._rejections = {}
        rejections[rejection_id] = dict(data)
        while len(rejections) > self.MAX_HISTORY:
            rejections.pop(next(iter(rejections)))

    def get_recent_actions(self, n=50) -> list:
        return self._actions[-n:]

    def save_control_request(self, control_id: str, data: dict):
        logger.debug(f"[MEMORY] Salvando Control Request {control_id}: {data}")
        self._control_requests[control_id] = dict(data) if isinstance(data, dict) else {"raw": data}

    def update_control_result(self, control_id: str, result: str):
        logger.debug(f"[MEMORY] Atualizando Control Result {control_id} -> {result}")
        if control_id in self._control_requests:
            self._control_requests[control_id]["status"] = result
            self._control_requests[control_id]["updated_at"] = time.time()

    def record_rollback(
        self,
        control_id: str,
        status: str = "ROLLBACK_SENT_UNCONFIRMED",
        details: Optional[dict] = None,
    ):
        logger.warning(
            "[MEMORY] Registrando status de rollback",
            control_request_id=control_id,
            status=status,
            details=details or {},
        )
        self._rollbacks[control_id] = {
            "status": status,
            "details": details or {},
            "timestamp": time.time(),
        }
