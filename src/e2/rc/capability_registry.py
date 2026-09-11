"""
Registro e Descoberta Dinâmica de Capacidades RAN Function (E2SM-RC v01.03)
Implementa o desacoplamento formal entre a ontologia interna da xApp e os Control Styles / Actions / RAN Parameter IDs
declarados pelos E2 Nodes / NORI em tempo de execução via RANFunctionDefinition (E2 Setup / RIC Service Update).
"""

import os
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from src.e2.rc.control_parameter import RANParameterDefinition, RAN_PARAMETERS
from src.observability.logging import setup_logger

logger = setup_logger("RanFunctionCapabilityRegistry")

class CapabilityNotDiscoveredError(Exception):
    """Exceção levantada em modo O_RAN_INTEROP / oran-strict quando uma capacidade de controle é solicitada para um nó ou parâmetro não registrado via RANFunctionDefinition."""
    pass

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
    Suporta formalmente dois modos de operação:
      1. RDL_MODE=simulation (OFFLINE_SIMULATION): catálogo desacoplado estático para testes e benchmarks sintéticos.
      2. RDL_MODE=oran-strict (O_RAN_INTEROP): conformidade estrita O-RAN onde fallbacks e defaults são proibidos.
    """
    def __init__(self):
        # Mapeamento padrão exclusivo para simulação offline / retrocompatibilidade
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

    def is_strict_mode(self, override: Optional[bool] = None) -> bool:
        if override is not None:
            return bool(override)
        mode = os.getenv("RDL_MODE", "OFFLINE_SIMULATION").upper()
        return mode in ("O_RAN_INTEROP", "ORAN-STRICT", "ORAN_STRICT", "STRICT")

    def register_node_capability(
        self,
        node_id: str,
        param_name: str,
        style_type: int,
        action_id: int,
        param_id: int,
        min_val: float,
        max_val: float,
        unit: str = "raw",
        strict_mode: Optional[bool] = None
    ) -> None:
        """
        Registra dinamicamente uma capacidade/parâmetro descoberto a partir da RANFunctionDefinition de um E2 Node.
        Em modo estrito, novos nós iniciam estritamente vazios sem herdar defaults não anunciados.
        """
        strict = self.is_strict_mode(strict_mode)
        if node_id not in self._node_capabilities:
            self._node_capabilities[node_id] = {} if strict else dict(self._default_capabilities)
            
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
            f"Capacidade E2SM-RC registrada para E2 Node '{node_id}' [Strict={strict}]: "
            f"Param={param_name} -> Style={style_type}, Action={action_id}, ParamID={param_id}"
        )

    def resolve_action(
        self,
        param_name: str,
        node_id: Optional[str] = None,
        strict_mode: Optional[bool] = None
    ) -> Tuple[int, int, int]:
        """
        Resolve a tupla normativa (style_type, action_id, param_id) para um determinado parâmetro e nó.
        Em modo estrito (RDL_MODE=oran-strict / O_RAN_INTEROP), defaults são estritamente proibidos e o nó/parâmetro
        deve ter sido explicitamente descoberto via RANFunctionDefinition.
        """
        is_strict = self.is_strict_mode(strict_mode)

        if is_strict:
            if not node_id or node_id not in self._node_capabilities:
                raise CapabilityNotDiscoveredError(
                    f"[ORAN-STRICT] Nó E2 '{node_id}' não possui RANFunctionDefinition descoberta em runtime."
                )
            if param_name not in self._node_capabilities[node_id]:
                raise CapabilityNotDiscoveredError(
                    f"[ORAN-STRICT] Parâmetro '{param_name}' não foi anunciado nas capacidades descobertas do nó '{node_id}'."
                )
            cap = self._node_capabilities[node_id][param_name]
            return cap.style_type, cap.action_id, cap.param_id

        # Modo OFFLINE_SIMULATION / Fallback desacoplado
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

