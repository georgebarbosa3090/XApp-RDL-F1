from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import uuid
import time

class ConflictType(Enum):
    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"
    # Entre células: handover para célula desligada/reduzida, ping-pong, vizinhas dormindo
    INTER_CELL = "INTER_CELL"
    # Implícito: o KPM contradiz a ação confirmada (alguém agiu por fora da RDL)
    IMPLICIT = "IMPLICIT"

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


# Escopo do efeito de uma proposta (doc 18 §4.1). ``None`` = não declarado: vale o padrão do backend,
# e sem padrão a RDL usa os escores heurísticos de sempre.
SCOPES = ("cell", "slice")
# Os três campos do RRM Policy Ratio (``SlicePrbQuota`` em src/e2/v3/codec.py) que o valor ocupa.
RATIO_KINDS = ("max", "min", "dedicated")
SLICE_SCOPED_PARAMETERS = ("PRB_QUOTA",)


def validate_scope_fields(parameter: str, scope: Optional[str], slice_sst: Optional[int],
                          ratio_kind: Optional[str]) -> None:
    """Valida ``scope``, ``slice_sst`` e ``ratio_kind`` de uma proposta (ValueError se inválidos).

    - ``scope``: ``cell`` (qualquer parâmetro) ou ``slice`` (só ``PRB_QUOTA``);
    - ``slice_sst``: inteiro em [0, 255], só com ``scope = slice`` ou sem ``scope`` em ``PRB_QUOTA``;
    - ``ratio_kind``: ``max``, ``min`` ou ``dedicated``, com as mesmas condições do ``slice_sst``.
    """
    if scope is not None and scope not in SCOPES:
        raise ValueError(f"scope must be one of {list(SCOPES)}")
    if slice_sst is not None and (isinstance(slice_sst, bool) or not isinstance(slice_sst, int)
                                  or not 0 <= slice_sst <= 255):
        raise ValueError("slice_sst must be an integer in [0, 255]")
    if ratio_kind is not None and ratio_kind not in RATIO_KINDS:
        raise ValueError(f"ratio_kind must be one of {list(RATIO_KINDS)}")
    slice_fields = slice_sst is not None or ratio_kind is not None
    if scope == "cell" and slice_fields:
        raise ValueError("slice_sst and ratio_kind require scope 'slice'")
    if (scope == "slice" or slice_fields) and parameter not in SLICE_SCOPED_PARAMETERS:
        raise ValueError(f"slice scope applies only to {list(SLICE_SCOPED_PARAMETERS)}")

@dataclass
class XAppAction:
    xapp_id: str
    node_id: str
    parameter: str
    value: float
    priority: int
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    t_arrival: float = 0.0
    t_selection: float = 0.0
    t_encode_start: float = 0.0
    t_dispatch_start: float = 0.0
    t_dispatch_end: float = 0.0
    t_ack: float = 0.0
    arrival_monotonic: float = 0.0
    context_features: Optional[dict] = None
    confidence_score: Optional[float] = None
    # Janela de decisão: classe de urgência atribuída na chegada e pedido de adiamento da xApp
    urgency: str = "NORMAL"
    defer_ok: bool = False
    ttl_ms: Optional[float] = None
    # Governança: prioridade pedida antes do teto do registro/A1 e origem interceptada (nível 2)
    requested_priority: Optional[int] = None
    intercepted: bool = False
    # Escopo do efeito (doc 18 §4.1): ``cell`` ou ``slice``; com ``slice``, a fatia (SST) e o campo do
    # RRM Policy Ratio que o valor ocupa. Opcionais; o padrão vem do perfil do backend (``scope_defaults``).
    scope: Optional[str] = None
    slice_sst: Optional[int] = None
    ratio_kind: Optional[str] = None

    def __post_init__(self):
        validate_scope_fields(self.parameter, self.scope, self.slice_sst, self.ratio_kind)
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
class ConflictSet:
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflicting_actions: List[XAppAction] = field(default_factory=list)
    affected_kpis: List[str] = field(default_factory=list)
    graph_embedding: Optional[dict] = None
    topology_state: Optional[dict] = None


@dataclass
class ResolutionAction:
    conflict_id: str
    strategy_used: ResolutionStrategy
    winning_actions: List[XAppAction]
    modified_value: Optional[float]
    confidence: float
    validation_level: int
    resolved_at: float = field(default_factory=time.time)
    # Guarda de SLA (doc 18 §4.4): action_id -> detalhe das candidatas declaradas inelegíveis
    # (recusa ``SLA_PROTECTION``, não ``LOST_ARBITRATION``).
    sla_excluded: Dict[str, str] = field(default_factory=dict)
    # Modelo de efeito usado (doc 18 §4.5): "heuristic" ou "curve:<sha256>".
    effect_model: str = "heuristic"

@dataclass
class KPMReport:
    node_id: str
    ue_id: str
    drb_thp_dl: Optional[float]
    drb_thp_ul: Optional[float]
    drb_delay_dl: Optional[float]
    prb_used_dl: Optional[int]
    timestamp: float = field(default_factory=time.time)

@dataclass
class RDLDecision:
    """
    Contrato formal de saída da Camada de Decisão (H-RDL / CA-RDL).
    Separa estritamente a inteligência determinística/analítica/MARL da camada de transporte E2.
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
    marl_agent_id: Optional[str] = None
    reward_estimate: Optional[float] = None
    affected_node: str = "gnb_01"
    affected_cell: str = "cell_01"
    previous_safe_value: Optional[float] = None
    conflict_id: Optional[str] = None
    conflict_ids: List[str] = field(default_factory=list)
