from typing import Tuple, Dict, Any, List, Optional, Callable
import time
import math
from src.conflict_types import ConflictEvent, ResolutionAction, XAppAction
from src.observability.logging import setup_logger

logger = setup_logger("Refinement")


class Refinement:
    """
    Componente de Refinamento e Guardiões de Segurança (Safety Guards / Núcleo / Core).
    Aplica validação invariante, limites físicos de rádio (Boundary Clipping) e histerese temporal.
    """
    def __init__(
        self,
        memory,
        strict_capabilities: bool = False,
        config: Optional[Dict[str, Any]] = None,
        committed_action_lookup: Optional[Callable[[str, str], Optional[XAppAction]]] = None,
        clock: Optional[Callable[[], float]] = None,
    ):
        self.memory = memory
        # Relógio em segundos (padrão: time.time); histerese e intervalo mínimo usam self.clock() * 1000
        self.clock: Callable[[], float] = clock or (lambda: time.time())
        self.strict_capabilities = strict_capabilities
        # Fonte do último valor confirmado (ACK) pela RAN para node/parâmetro; usada
        # pelo slew-rate. Sem ela, o slew-rate não pode ser verificado (ver abaixo).
        self.committed_action_lookup = committed_action_lookup
        self.config = {
            "enabled": True,
            "minimum_control_interval_ms": 1000,
            # Classe CRITICAL (janela de decisão): intervalo próprio, menor, no mesmo alvo
            "critical_control_interval_ms": 100,
            "enforce_slew_rate": False,
            "max_tx_power_slew_db": 3.0,
            "max_prb_slew_pct": 30.0,
        }
        if config:
            self.config.update(config)
        self.last_control_time: Dict[str, float] = {}
        self.node_capabilities: Dict[str, Dict[str, Any]] = {}
        # Restrições de política A1 (ver apply_policy); None = sem restrição adicional
        self.policy_max_prb_quota: Optional[float] = None
        self.policy_allow_cell_sleep: bool = True
        # Verificação opcional do destino de HANDOVER contra a topologia conhecida (grafo de conhecimento)
        self.handover_target_check: Optional[Callable[[XAppAction], bool]] = None

    def apply_policy(
        self,
        max_prb_quota: Optional[float] = None,
        allow_cell_sleep: bool = True,
        minimum_control_interval_ms: Optional[float] = None,
        critical_control_interval_ms: Optional[float] = None,
    ) -> None:
        """Aplica a política A1 efetiva: teto de cota de PRB, permissão de sleep e intervalos mínimos.

        Uma política só restringe dentro dos limites físicos; nunca os amplia.
        """
        self.policy_max_prb_quota = float(max_prb_quota) if max_prb_quota is not None else None
        self.policy_allow_cell_sleep = bool(allow_cell_sleep)
        if minimum_control_interval_ms is not None:
            self.config["minimum_control_interval_ms"] = float(minimum_control_interval_ms)
        if critical_control_interval_ms is not None:
            self.config["critical_control_interval_ms"] = float(critical_control_interval_ms)

    def min_interval_ms(self, action: XAppAction) -> float:
        """Intervalo mínimo entre controles no alvo da ação; menor para a classe CRITICAL."""
        normal = float(self.config.get("minimum_control_interval_ms", 1000))
        if getattr(action, "urgency", "NORMAL") == "CRITICAL":
            return min(normal, float(self.config.get("critical_control_interval_ms", normal)))
        return normal

    def remaining_lockout_ms(self, action: XAppAction, now_ms: Optional[float] = None) -> float:
        """Quanto falta para o alvo aceitar novo controle desta ação (0 = já aceita)."""
        now_ms = self.clock() * 1000 if now_ms is None else now_ms
        last_time = self.last_control_time.get(f"{action.node_id}_{action.parameter}")
        if last_time is None:                       # alvo nunca controlado: não há bloqueio
            return 0.0
        return max(0.0, self.min_interval_ms(action) - (now_ms - last_time))

    def _get_max_tx_power(self, node_id: str) -> Optional[float]:
        """Obtém o teto de potência de transmissão (dBm) para o nó específico ou padrão."""
        cap = self.node_capabilities.get(node_id, {})
        if "max_tx_power_dbm" in cap:
            return float(cap["max_tx_power_dbm"])

        from src.e2.rc.capability_registry import (
            CapabilityNotDiscoveredError,
            rc_capability_registry,
        )
        try:
            capability = rc_capability_registry.get_action_capability(
                "TX_POWER", node_id, strict_mode=self.strict_capabilities
            )
        except CapabilityNotDiscoveredError:
            return None
        except KeyError:
            if self.strict_capabilities:
                return None
        else:
            return float(capability.max_value)

        if self.strict_capabilities:
            return None
        from src.e2.rc.control_parameter import RAN_PARAMETERS
        return float(self.config.get("max_tx_power_dbm", RAN_PARAMETERS["TX_POWER"].max_value))

    def _validate_parameter_bounds(self, action: XAppAction) -> Tuple[bool, str]:
        """
        Valida se o parâmetro é reconhecido e se seu valor está dentro dos limites físicos.
        Aplica princípio Default-Deny estrito (Fail-Closed).
        """
        from src.e2.rc.capability_registry import (
            CapabilityNotDiscoveredError,
            rc_capability_registry,
        )
        from src.e2.rc.control_parameter import RAN_PARAMETERS

        if action.parameter not in RAN_PARAMETERS:
            return False, f"Unsupported action parameter (Default-Deny): {action.parameter}"
        try:
            value = float(action.value)
        except (OverflowError, TypeError, ValueError):
            return False, f"{action.parameter} value must be numeric"
        if not math.isfinite(value):
            return False, f"{action.parameter} value must be finite"
        if isinstance(action.priority, bool) or not isinstance(action.priority, int) or not 0 <= action.priority <= 100:
            return False, "Action priority must be an integer in [0, 100]"
        if action.parameter in ("PRB_QUOTA", "SCHEDULER_WEIGHT", "HANDOVER", "CELL_STATE") and not value.is_integer():
            return False, f"{action.parameter} value must be an integer"
        if action.parameter == "TX_POWER" and not (value * 10).is_integer():
            return False, "TX_POWER supports at most one decimal place"

        try:
            capability = rc_capability_registry.get_action_capability(
                action.parameter,
                action.node_id,
                strict_mode=self.strict_capabilities,
            )
        except CapabilityNotDiscoveredError:
            return False, f"{action.parameter} capability not discovered for node {action.node_id}"
        except KeyError:
            if self.strict_capabilities:
                return False, f"{action.parameter} capability not discovered for node {action.node_id}"
            definition = RAN_PARAMETERS[action.parameter]
            min_value, max_value = definition.min_value, definition.max_value
        else:
            min_value, max_value = capability.min_value, capability.max_value

        if action.parameter == "TX_POWER":
            configured_max = self._get_max_tx_power(action.node_id)
            if configured_max is None:
                return False, f"TX_POWER capability not discovered for node {action.node_id}"
            max_value = min(max_value, configured_max)
        if value < min_value or value > max_value:
            if action.parameter == "TX_POWER":
                return False, f"TX Power out of bounds ({min_value}-{max_value} dBm)"
            return False, f"{action.parameter} out of bounds ({min_value}-{max_value})"

        if action.parameter == "PRB_QUOTA" and self.policy_max_prb_quota is not None and value > self.policy_max_prb_quota:
            return False, f"PRB_QUOTA above A1 policy limit ({self.policy_max_prb_quota:g})"
        if action.parameter == "CELL_STATE" and value == 0 and not self.policy_allow_cell_sleep:
            return False, "Cell sleep not allowed by A1 policy"
        if action.parameter == "HANDOVER" and self.handover_target_check is not None \
                and not self.handover_target_check(action):
            return False, "HANDOVER target cell is outside the known topology"

        if self.config.get("enforce_slew_rate", False):
            get_committed = self.committed_action_lookup or getattr(self.memory, "get_committed_action", None)
            if not callable(get_committed):
                # Fail-closed: slew-rate habilitado sem fonte de estado confirmado.
                return False, "Slew-rate enforcement enabled but no committed-state source is configured"
            committed = get_committed(action.node_id, action.parameter)
            if committed is not None:
                delta_val = abs(value - float(committed.value))
                if action.parameter == "TX_POWER" and delta_val > float(self.config.get("max_tx_power_slew_db", 3.0)):
                    return False, f"TX_POWER slew-rate exceeded ({delta_val:.1f} dBm)"
                if action.parameter == "PRB_QUOTA" and delta_val > float(self.config.get("max_prb_slew_pct", 30.0)):
                    return False, f"PRB_QUOTA slew-rate exceeded ({delta_val:.1f}%)"

        return True, ""

    def check_bounds(self, action: XAppAction) -> Tuple[bool, str]:
        """Valida só limites físicos e formato do parâmetro (sem histerese temporal)."""
        if not self.config.get("enabled", True):
            return True, "Safety guard disabled"
        if not action or not action.node_id:
            return False, "Unknown target node or empty action"
        return self._validate_parameter_bounds(action)

    def commit_control_timestamps(self, actions: List[XAppAction], timestamp_ms: Optional[float] = None) -> None:
        """Registra os timestamps de histerese ao final do lote de decisão."""
        now = timestamp_ms if timestamp_ms is not None else (self.clock() * 1000)
        for action in actions:
            if action and action.node_id and action.parameter:
                self.last_control_time[f"{action.node_id}_{action.parameter}"] = now

    def validate_single_action(self, action: XAppAction, record_timestamp: bool = True) -> Tuple[bool, int, str]:
        """
        Valida individualmente uma ação que não esteve em conflito (Pass-Through).
        Retorna (is_valid, validation_level, reason).
        """
        if not self.config.get("enabled", True):
            return True, 1, "Safety guard disabled"

        if not action or not action.node_id:
            return False, 1, "Unknown target node or empty action"

        now = self.clock() * 1000
        target_key = f"{action.node_id}_{action.parameter}"

        # 1. Validade temporal (histerese / frequência máxima de controle para o mesmo alvo)
        # Alvo nunca controlado não tem bloqueio (antes, o padrão 0 recusava controles no primeiro intervalo
        # quando o relógio começa em zero, como o relógio simulado da malha fechada).
        last_time = self.last_control_time.get(target_key)
        if last_time is not None and (now - last_time) < self.min_interval_ms(action):
            return False, 1, f"Control frequency exceeded for {target_key}"

        # 2. Barreiras físicas de limites de rádio (Default-Deny)
        is_valid_param, err_msg = self._validate_parameter_bounds(action)
        if not is_valid_param:
            return False, 1, err_msg

        # Atualiza o timestamp da última ação executada para este alvo
        if record_timestamp:
            self.last_control_time[target_key] = now
        return True, 2, "Passed safety checks"

    def validate(self, resolution: ResolutionAction, conflict: ConflictEvent, record_timestamp: bool = True) -> Tuple[bool, int, str]:
        """
        Safety Guard que valida se o lote de controle proposto pela resolução de conflito é seguro.
        Aplica validação atômica/transacional (sem vazamento de timestamp se houver rejeição).
        Retorna (is_valid, validation_level, reason)
        """
        if not self.config.get("enabled", True):
            return True, 1, "Safety guard disabled"

        actions = resolution.winning_actions
        if not actions:
            return False, 1, "No actions selected"

        now = self.clock() * 1000
        pending_time_updates: Dict[str, float] = {}

        for action in actions:
            if not action or not action.node_id:
                return False, 1, "Unknown target node or empty action"

            target_key = f"{action.node_id}_{action.parameter}"

            # 1. Validade temporal (frequência máxima de controle no mesmo parâmetro/nó)
            last_time = self.last_control_time.get(target_key)
            if last_time is not None and (now - last_time) < self.min_interval_ms(action):
                return False, 1, f"Control frequency exceeded for {target_key}"

            # 2. Valores negativos ou fora de escopo para parâmetros conhecidos (Default-Deny)
            is_valid_param, err_msg = self._validate_parameter_bounds(action)
            if not is_valid_param:
                return False, 1, err_msg

            pending_time_updates[target_key] = now

        # Commit transacional: atualiza os timestamps somente após todo o lote passar
        if record_timestamp:
            self.last_control_time.update(pending_time_updates)
        return True, 2, "Passed safety checks"


# Alias de compatibilidade retroativa
RefinementAgent = Refinement
