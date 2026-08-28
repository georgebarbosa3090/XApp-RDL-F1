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
