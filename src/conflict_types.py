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

@dataclass
class ConflictEvent:
    conflict_type: ConflictType
    severity: ConflictSeverity
    involved_xapps: List[XAppAction]
    affected_kpis: List[str]
    description: str
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

