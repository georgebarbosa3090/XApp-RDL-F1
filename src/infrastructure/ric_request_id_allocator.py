import time
import threading
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any

@dataclass
class RicRequestId:
    requestor_id: int
    instance_id: int

class RicRequestIdAllocator:
    """
    Gerenciador thread-safe e atômico de identificadores RICrequestID para mensagens E2AP Control Request.
    Chave primária de correlação: (node_id, ran_function_id, requestor_id, instance_id).
    Permite correlação bidirecional com decision_id e action_id em cenários concorrentes multi-xApp/multi-gNB.
    """

    def __init__(self, base_requestor_id: int = 1001):
        self._base_requestor_id = base_requestor_id
        self._lock = threading.Lock()
        self._instance_counters: Dict[Tuple[str, int], int] = {}
        self._correlation_map: Dict[Tuple[str, int, int, int], Dict[str, Any]] = {}

    def allocate(
        self,
        node_id: str,
        ran_function_id: int,
        decision_id: Optional[str] = None,
        action_id: Optional[str] = None
    ) -> RicRequestId:
        with self._lock:
            key = (node_id, ran_function_id)
            current_counter = self._instance_counters.get(key, 0) + 1
            self._instance_counters[key] = current_counter
            
            requestor_id = self._base_requestor_id
            instance_id = current_counter
            
            if decision_id or action_id:
                corr_key = (node_id, ran_function_id, requestor_id, instance_id)
                self._correlation_map[corr_key] = {
                    "decision_id": decision_id or "",
                    "action_id": action_id or "",
                    "allocated_at": time.time()
                }
                
            return RicRequestId(requestor_id=requestor_id, instance_id=instance_id)

    def lookup_correlation(
        self,
        node_id: str,
        ran_function_id: int,
        requestor_id: int,
        instance_id: int
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            corr_key = (node_id, ran_function_id, requestor_id, instance_id)
            return self._correlation_map.get(corr_key)

    def pop_correlation(
        self,
        node_id: str,
        ran_function_id: int,
        requestor_id: int,
        instance_id: int
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            corr_key = (node_id, ran_function_id, requestor_id, instance_id)
            return self._correlation_map.pop(corr_key, None)

    def cleanup_expired(self, ttl_seconds: float = 300.0) -> int:
        now = time.time()
        removed = 0
        with self._lock:
            keys_to_remove = [
                key for key, val in self._correlation_map.items()
                if now - val.get("allocated_at", now) > ttl_seconds
            ]
            for key in keys_to_remove:
                del self._correlation_map[key]
                removed += 1
        return removed

_global_allocator = RicRequestIdAllocator()

def get_ric_request_id_allocator() -> RicRequestIdAllocator:
    return _global_allocator

