from typing import Tuple, Dict, Any, List, Optional
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
    def __init__(self, memory, strict_capabilities: bool = False, config: Optional[Dict[str, Any]] = None):
        self.memory = memory
        self.strict_capabilities = strict_capabilities
        self.config = {
            "enabled": True,
            "minimum_control_interval_ms": 1000,
        }
        if config:
            self.config.update(config)
        self.last_control_time: Dict[str, float] = {}
        self.node_capabilities: Dict[str, Dict[str, Any]] = {}

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
        if action.parameter in ("PRB_QUOTA", "SCHEDULER_WEIGHT", "HANDOVER") and not value.is_integer():
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
        return True, ""

    def validate_single_action(self, action: XAppAction) -> Tuple[bool, int, str]:
        """
        Valida individualmente uma ação que não esteve em conflito (Pass-Through).
        Retorna (is_valid, validation_level, reason).
        """
        if not self.config.get("enabled", True):
            return True, 1, "Safety guard disabled"

        if not action or not action.node_id:
            return False, 1, "Unknown target node or empty action"

        now = time.time() * 1000
        target_key = f"{action.node_id}_{action.parameter}"

        # 1. Validade temporal (histerese / frequência máxima de controle para o mesmo alvo)
        last_time = self.last_control_time.get(target_key, 0)
        if (now - last_time) < self.config.get("minimum_control_interval_ms", 1000):
            return False, 1, f"Control frequency exceeded for {target_key}"

        # 2. Barreiras físicas de limites de rádio (Default-Deny)
        is_valid_param, err_msg = self._validate_parameter_bounds(action)
        if not is_valid_param:
            return False, 1, err_msg

        # Atualiza o timestamp da última ação executada para este alvo
        self.last_control_time[target_key] = now
        return True, 2, "Passed safety checks"

    def validate(self, resolution: ResolutionAction, conflict: ConflictEvent) -> Tuple[bool, int, str]:
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

        now = time.time() * 1000
        pending_time_updates: Dict[str, float] = {}
        
        for action in actions:
            if not action or not action.node_id:
                return False, 1, "Unknown target node or empty action"

            target_key = f"{action.node_id}_{action.parameter}"
            
            # 1. Validade temporal (frequência máxima de controle no mesmo parâmetro/nó)
            last_time = self.last_control_time.get(target_key, 0)
            if (now - last_time) < self.config.get("minimum_control_interval_ms", 1000):
                return False, 1, f"Control frequency exceeded for {target_key}"
                
            # 2. Valores negativos ou fora de escopo para parâmetros conhecidos (Default-Deny)
            is_valid_param, err_msg = self._validate_parameter_bounds(action)
            if not is_valid_param:
                return False, 1, err_msg

            pending_time_updates[target_key] = now

        # Commit transacional: atualiza os timestamps somente após todo o lote passar
        self.last_control_time.update(pending_time_updates)
        return True, 2, "Passed safety checks"

# Alias de compatibilidade retroativa
RefinementAgent = Refinement
