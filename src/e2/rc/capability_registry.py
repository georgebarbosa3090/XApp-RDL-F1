"""
Registro e Descoberta Dinâmica de Capacidades RAN Function (E2SM-RC v01.03)
Implementa o desacoplamento formal entre a ontologia interna da xApp e os Control Styles / Actions / RAN Parameter IDs
declarados pelos E2 Nodes / NORI em tempo de execução.
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from src.e2.rc.control_parameter import RANParameterDefinition, RAN_PARAMETERS
from src.observability.logging import setup_logger

logger = setup_logger("RanFunctionCapabilityRegistry")

@dataclass
class ControlActionCapability:
    style_type: int
    action_id: int
    action_name: str
    param_id: int
    param_name: str
    min_value: float
    max_value: float
    unit: str

class RanFunctionCapabilityRegistry:
    """
    Catálogo dinâmico de capacidades expostas por E2 Nodes para o Service Model E2SM-RC.
    """
    def __init__(self):
        # Mapeamento padrão alinhado com o perfil NORI / O-RAN SC Release I/J
        self._default_capabilities: Dict[str, ControlActionCapability] = {
            "PRB_QUOTA": ControlActionCapability(
                style_type=1, # Radio Resource Allocation
                action_id=1,  # Slicing / PRB Quota Control
                action_name="SetPrbQuota",
                param_id=1,
                param_name="PRB_QUOTA",
                min_value=0.0,
                max_value=100.0,
                unit="percent"
            ),
            "SCHEDULER_WEIGHT": ControlActionCapability(
                style_type=1,
                action_id=2,  # Scheduler Weighting
                action_name="SetSchedulerWeight",
                param_id=2,
                param_name="SCHEDULER_WEIGHT",
                min_value=1.0,
                max_value=100.0,
                unit="weight"
            ),
            "TX_POWER": ControlActionCapability(
                style_type=2, # Power Control
                action_id=1,  # Sector TX Power
                action_name="SetTxPower",
                param_id=3,
                param_name="TX_POWER",
                min_value=-10.0,
                max_value=23.0,
                unit="dBm"
            ),
            "HANDOVER": ControlActionCapability(
                style_type=3, # Mobility Control
                action_id=1,  # Directed Handover
                action_name="TriggerHandover",
                param_id=4,
                param_name="HANDOVER",
                min_value=0.0,
                max_value=65535.0,
                unit="cell_id"
            )
        }
        # Tabela de capacidades por E2 Node ID específico: Dict[node_id, Dict[param_name, ControlActionCapability]]
        self._node_capabilities: Dict[str, Dict[str, ControlActionCapability]] = {}

    def register_node_capability(
        self,
        node_id: str,
        param_name: str,
        style_type: int,
        action_id: int,
        param_id: int,
        min_val: float,
        max_val: float,
        unit: str = "raw"
    ) -> None:
        """
        Registra dinamicamente uma capacidade/parâmetro descoberto a partir da RANFunctionDefinition de um E2 Node.
        """
        if node_id not in self._node_capabilities:
            self._node_capabilities[node_id] = dict(self._default_capabilities)
            
        self._node_capabilities[node_id][param_name] = ControlActionCapability(
            style_type=style_type,
            action_id=action_id,
            action_name=f"CustomAction_{param_name}",
            param_id=param_id,
            param_name=param_name,
            min_value=min_val,
            max_value=max_val,
            unit=unit
        )
        logger.info(
            f"Capacidade E2SM-RC registrada para E2 Node '{node_id}': "
            f"Param={param_name} -> Style={style_type}, Action={action_id}, ParamID={param_id}"
        )

    def resolve_action(
        self,
        param_name: str,
        node_id: Optional[str] = None
    ) -> Tuple[int, int, int]:
        """
        Resolve a tupla normativa (style_type, action_id, param_id) para um determinado parâmetro e nó.
        """
        cap_map = self._default_capabilities
        if node_id and node_id in self._node_capabilities:
            cap_map = self._node_capabilities[node_id]

        if param_name in cap_map:
            cap = cap_map[param_name]
            return cap.style_type, cap.action_id, cap.param_id
            
        # Fallback para dicionário canônico se registrado
        if param_name in RAN_PARAMETERS:
            p = RAN_PARAMETERS[param_name]
            return 1, 1, p.param_id

        raise ValueError(f"Parâmetro '{param_name}' não suportado nas capacidades E2SM-RC do nó '{node_id}'")

# Instância Singleton do Registry
rc_capability_registry = RanFunctionCapabilityRegistry()
