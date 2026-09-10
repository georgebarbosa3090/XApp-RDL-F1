from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
import uuid
import time

class ConflictType(Enum):
    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"

class ConflictSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ResolutionStrategy(Enum):
    PRIORITY_TABLE = "PRIORITY_TABLE"
    ROLLBACK = "ROLLBACK"
    TVS = "TVS"
    EEVS = "EEVS"
    MARL_AGENT = "MARL_AGENT"

@dataclass
class XAppAction:
    xapp_id: str
    node_id: str
    parameter: str
    value: float
    priority: int
    timestamp: float = field(default_factory=time.time)
    t_arrival: float = 0.0
    t_selection: float = 0.0
    t_encode_start: float = 0.0
    t_dispatch_start: float = 0.0
    t_dispatch_end: float = 0.0
    t_ack: float = 0.0
    arrival_monotonic: float = 0.0

    def __post_init__(self):
        if self.t_arrival == 0.0:
            now = time.perf_counter()
            self.t_arrival = now
            self.arrival_monotonic = now

    @property
    def queue_delay_ms(self) -> float:
        if self.t_selection > 0 and self.t_arrival > 0:
            return max(0.0, (self.t_selection - self.t_arrival) * 1000.0)
        return 0.0

    @property
    def processing_delay_ms(self) -> float:
        if self.t_dispatch_end > 0 and self.t_selection > 0:
            return max(0.0, (self.t_dispatch_end - self.t_selection) * 1000.0)
        return 0.0

    @property
    def rtt_ack_ms(self) -> Optional[float]:
        if self.t_ack > 0 and self.t_dispatch_start > 0:
            return max(0.0, (self.t_ack - self.t_dispatch_start) * 1000.0)
        return None


@dataclass
class ConflictEvent:
    conflict_type: ConflictType
    severity: ConflictSeverity
    involved_xapps: List[XAppAction]
    affected_kpis: List[str] = field(default_factory=list)
    description: str = ""
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    detected_at: float = field(default_factory=time.time)


@dataclass
class ResolutionAction:
    conflict_id: str
    strategy_used: ResolutionStrategy
    winning_actions: List[XAppAction]
    modified_value: Optional[float]
    confidence: float
    validation_level: int
    resolved_at: float = field(default_factory=time.time)

@dataclass
class KPMReport:
    node_id: str
    ue_id: str
    drb_thp_dl: float
    drb_thp_ul: float
    drb_delay_dl: float
    prb_used_dl: int
    timestamp: float = field(default_factory=time.time)

@dataclass
class RDLDecision:
    """
    Contrato formal de saída da Camada de Decisão (H-RDL).
    Separa estritamente a inteligência determinística/analítica da camada de transporte E2.
    """
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    state: dict = field(default_factory=dict)
    proposals: List[XAppAction] = field(default_factory=list)
    conflicts: List[ConflictEvent] = field(default_factory=list)
    safety_result: dict = field(default_factory=dict)
    selected_actions: List[XAppAction] = field(default_factory=list)
    reason: str = "PASS_THROUGH_CLEAN"
    strategy_used: str = "DETERMINISTIC_H_RDL"
    timestamp: float = field(default_factory=time.time)

