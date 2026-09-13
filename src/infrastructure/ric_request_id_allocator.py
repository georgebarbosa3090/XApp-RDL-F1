import threading
from dataclasses import dataclass
from typing import Dict, Tuple, Optional

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
        self._correlation_map: Dict[Tuple[str, int, int, int], Dict[str, str]] = {}

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
                    "action_id": action_id or ""
                }
                
            return RicRequestId(requestor_id=requestor_id, instance_id=instance_id)

    def lookup_correlation(
        self,
        node_id: str,
        ran_function_id: int,
        requestor_id: int,
        instance_id: int
    ) -> Optional[Dict[str, str]]:
        with self._lock:
            corr_key = (node_id, ran_function_id, requestor_id, instance_id)
            return self._correlation_map.get(corr_key)

_global_allocator = RicRequestIdAllocator()

def get_ric_request_id_allocator() -> RicRequestIdAllocator:
    return _global_allocator
