from typing import Tuple, Dict, Any, List, Optional
import time
from src.conflict_types import ConflictEvent, ResolutionAction, XAppAction
from src.observability.logging import setup_logger

logger = setup_logger("Refinement")

class Refinement:
    """
    Componente de Refinamento e Guardiões de Segurança (Safety Guards / Núcleo / Core).
    Aplica validação invariante, limites físicos de rádio (Boundary Clipping) e histerese temporal.
    """
    def __init__(self, memory, strict_capabilities: bool = False):
        self.memory = memory
        self.strict_capabilities = strict_capabilities
        self.config = {
            "enabled": True,
            "minimum_control_interval_ms": 1000,
        }
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
        return float(self.config.get("max_tx_power_dbm", 23.0))

    def _validate_parameter_bounds(self, action: XAppAction) -> Tuple[bool, str]:
        """
        Valida se o parâmetro é reconhecido e se seu valor está dentro dos limites físicos.
        Aplica princípio Default-Deny estrito (Fail-Closed).
        """
        max_tx = self._get_max_tx_power(action.node_id)

        if action.parameter == "PRB_QUOTA":
            if action.value < 0 or action.value > 100:
                return False, "PRB value out of bounds (0-100)"
        elif action.parameter == "TX_POWER":
            if max_tx is None:
                return False, f"TX_POWER capability not discovered for node {action.node_id}"
            if action.value < -10 or action.value > max_tx:
                return False, f"TX Power out of bounds (-10 to {max_tx} dBm)"
        elif action.parameter == "HANDOVER":
            if action.value < 0 or action.value > 1:
                return False, "Handover flag out of bounds (0-1)"
        elif action.parameter == "VERTICAL_DOWNTILT":
            if action.value < 0.0 or action.value > 15.0:
                return False, "Vertical Downtilt out of bounds (0-15 degrees)"
        elif action.parameter == "SENSING_RATIO":
            if action.value < 0.0 or action.value > 0.60:
                return False, "Sensing Ratio out of bounds (0.0-0.60)"
        elif action.parameter == "LOAD_THRESHOLD":
            if action.value < 0.0 or action.value > 1.0:
                return False, "Load threshold out of bounds (0.0-1.0)"
        elif action.parameter == "PING_INTERVAL":
            if action.value < 1.0 or action.value > 5000.0:
                return False, "Ping interval out of bounds (1-5000 ms)"
        elif action.parameter in ("SCHEDULER_WEIGHT", "BEAM_WEIGHTS"):
            if action.value < 0.0 or action.value > 100.0:
                return False, f"{action.parameter} out of bounds (0-100)"
        else:
            return False, f"Unsupported action parameter (Default-Deny): {action.parameter}"

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
