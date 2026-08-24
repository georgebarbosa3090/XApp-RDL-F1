from typing import Dict, Any, Optional
import json
import time
from src.observability.logging import setup_logger

logger = setup_logger("SdlRepository")

class SdlRepository:
    def __init__(self, xapp_instance=None):
        """
        Wrapper para o SDL (Shared Data Layer) do RIC.
        xapp_instance: instância da RDLxApp contendo a conexão sdl.
        """
        self.xapp = xapp_instance
        self.namespace = "iqos-xapp-rdl"
        self._local_cache = []

    def _set(self, key: str, value: Any):
        try:
            # Serializa para JSON se for dict/list
            if isinstance(value, (dict, list)):
                value = json.dumps(value).encode('utf-8')
            elif isinstance(value, str):
                value = value.encode('utf-8')
            
            if self.xapp is not None:
                self.xapp.sdl_set(self.namespace, key, value)
            else:
                logger.debug(f"[MOCK SDL] Set {key} = {value}")
        except Exception as e:
            logger.error(f"Falha ao persistir {key} no SDL: {e}")

    def _get(self, key: str) -> Optional[Any]:
        try:
            data = self.xapp.sdl_get(self.namespace, key)
            if data:
                try:
                    return json.loads(data.decode('utf-8'))
                except json.JSONDecodeError:
                    return data.decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Falha ao ler {key} do SDL: {e}")
            return None

    # Implementações RF-19
    def save_subscription(self, sub_id: str, data: dict):
        self._set(f"subscriptions:{sub_id}", data)

    def save_e2_node(self, node_id: str, data: dict):
        self._set(f"e2_nodes:{node_id}", data)

    def save_latest_kpm_state(self, node_id: str, state: dict):
        self._set(f"latest_kpm_state:{node_id}", state)

    def save_action_proposal(self, proposal_id: str, data: dict):
        self._set(f"action_proposals:{proposal_id}", data)

    def save_decision(self, decision_id: str, data: dict):
        self._set(f"decisions:{decision_id}", data)

    def save_control_request(self, control_id: str, data: dict):
        self._set(f"control_requests:{control_id}", data)

    def update_control_result(self, control_id: str, result: str):
        data = self._get(f"control_requests:{control_id}")
        if data and isinstance(data, dict):
            data["result"] = result
            self._set(f"control_results:{control_id}", data)

    # Alias para compatibilidade com o MemoryModule legado
    def add_action(self, action):
        self._local_cache.append(action)
        self.save_action_proposal(f"act_{time.time()}", {"parameter": action.parameter, "value": action.value})

    def add_conflict(self, conflict):
        self._local_cache.append(conflict)
        self._set(f"conflict_{conflict.conflict_id}", {"type": conflict.conflict_type.name})

    def add_resolution(self, resolution):
        self._local_cache.append(resolution)
        self.save_decision(f"res_{resolution.conflict_id}", {"strategy": resolution.strategy_used.name})

    def get_similar_resolutions(self, conflict) -> list:
        # Mock para busca histórica
        return []

    def get_recent_actions(self, n=50) -> list:
        return self._local_cache[-n:]

