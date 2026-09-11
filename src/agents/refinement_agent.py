from typing import Tuple, Dict, Any, List
import time
from src.conflict_types import ConflictEvent, ResolutionAction, XAppAction
from src.observability.logging import setup_logger

logger = setup_logger("RefinementAgent")

class RefinementAgent:
    def __init__(self, memory):
        self.memory = memory
        self.config = {
            "enabled": True,
            "minimum_control_interval_ms": 1000,
        }
        self.last_control_time: Dict[str, float] = {}

    def validate_single_action(self, action: XAppAction) -> Tuple[bool, int, str]:
        """
        Valida individualmente uma ação que não esteve em conflito (Pass-Through).
        Retorna (is_valid, validation_level, reason).
        """
        if not self.config.get("enabled", True):
            return True, 1, "Safety guard disabled"

        if not action or action.node_id == "":
            return False, 1, "Unknown target node or empty action"

        now = time.time() * 1000
        target_key = f"{action.node_id}_{action.parameter}"

        # 1. Validade temporal (histerese / frequência máxima de controle para o mesmo alvo)
        last_time = self.last_control_time.get(target_key, 0)
        if (now - last_time) < self.config.get("minimum_control_interval_ms", 1000):
            return False, 1, f"Control frequency exceeded for {target_key}"

        # 2. Barreiras físicas de limites de rádio
        if action.parameter == "PRB_QUOTA":
            if action.value < 0 or action.value > 100:
                return False, 1, "PRB value out of bounds (0-100)"
        elif action.parameter == "TX_POWER":
            if action.value < -10 or action.value > 23:
                return False, 1, "TX Power out of bounds (-10 to 23 dBm)"
        elif action.parameter == "HANDOVER":
            if action.value < 0 or action.value > 1:
                return False, 1, "Handover flag out of bounds (0-1)"
        elif action.parameter == "VERTICAL_DOWNTILT":
            if action.value < 0.0 or action.value > 15.0:
                return False, 1, "Vertical Downtilt out of bounds (0-15 degrees)"
        elif action.parameter == "SENSING_RATIO":
            if action.value < 0.0 or action.value > 0.60:
                return False, 1, "Sensing Ratio out of bounds (0.0-0.60)"
        elif action.parameter == "LOAD_THRESHOLD":
            if action.value < 0.0 or action.value > 1.0:
                return False, 1, "Load threshold out of bounds (0.0-1.0)"
        elif action.parameter == "PING_INTERVAL":
            if action.value < 1.0 or action.value > 5000.0:
                return False, 1, "Ping interval out of bounds (1-5000 ms)"
        elif action.parameter in ("SCHEDULER_WEIGHT", "BEAM_WEIGHTS"):
            if action.value < 0.0 or action.value > 100.0:
                return False, 1, f"{action.parameter} out of bounds (0-100)"

        # Atualiza o timestamp da última ação executada para este alvo
        self.last_control_time[target_key] = now
        return True, 2, "Passed safety checks"

    def validate(self, resolution: ResolutionAction, conflict: ConflictEvent) -> Tuple[bool, int, str]:
        """
        Safety Guard que valida se o lote de controle proposto pela resolução de conflito é seguro.
        Retorna (is_valid, validation_level, reason)
        """
        if not self.config.get("enabled", True):
            return True, 1, "Safety guard disabled"
            
        actions = resolution.winning_actions
        if not actions:
            return False, 1, "No actions selected"

        now = time.time() * 1000
        
        for action in actions:
            target_key = f"{action.node_id}_{action.parameter}"
            
            # 1. Validade temporal (frequência máxima de controle no mesmo parâmetro/nó)
            last_time = self.last_control_time.get(target_key, 0)
            if (now - last_time) < self.config.get("minimum_control_interval_ms", 1000):
                return False, 1, f"Control frequency exceeded for {target_key}"
                
            # 2. Valores negativos ou fora de escopo para parâmetros conhecidos
            if action.parameter == "PRB_QUOTA":
                if action.value < 0 or action.value > 100:
                    return False, 1, "PRB value out of bounds (0-100)"
            elif action.parameter == "TX_POWER":
                if action.value < -10 or action.value > 23:
                    return False, 1, "TX Power out of bounds (-10 to 23 dBm)"
            elif action.parameter == "HANDOVER":
                if action.value < 0 or action.value > 1:
                    return False, 1, "Handover flag out of bounds (0-1)"
            elif action.parameter == "VERTICAL_DOWNTILT":
                if action.value < 0.0 or action.value > 15.0:
                    return False, 1, "Vertical Downtilt out of bounds (0-15 degrees)"
            elif action.parameter == "SENSING_RATIO":
                if action.value < 0.0 or action.value > 0.60:
                    return False, 1, "Sensing Ratio out of bounds (0.0-0.60)"
            elif action.parameter == "LOAD_THRESHOLD":
                if action.value < 0.0 or action.value > 1.0:
                    return False, 1, "Load threshold out of bounds (0.0-1.0)"
            elif action.parameter == "PING_INTERVAL":
                if action.value < 1.0 or action.value > 5000.0:
                    return False, 1, "Ping interval out of bounds (1-5000 ms)"
            elif action.parameter in ("SCHEDULER_WEIGHT", "BEAM_WEIGHTS"):
                if action.value < 0.0 or action.value > 100.0:
                    return False, 1, f"{action.parameter} out of bounds (0-100)"
            
            if action.node_id == "":
                return False, 1, "Unknown target node"

            # Atualiza tempo
            self.last_control_time[target_key] = now

        return True, 2, "Passed safety checks"
