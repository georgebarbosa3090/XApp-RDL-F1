"""
Mapeamento e Validação Normativa de Parâmetros de RAN Control (E2SM-RC v1.03 / v10.00)
Conforme O-RAN.WG3.E2SM-RC.
"""

from typing import Dict, Any, Tuple
from dataclasses import dataclass

@dataclass(frozen=True)
class RANParameterDefinition:
    param_id: int
    param_name: str
    param_type: str # "INTEGER", "ENUM", "OCTET_STRING"
    min_value: float
    max_value: float
    unit: str
    description: str

# Tabela Canônica de Parâmetros da RAN para H-RDL
RAN_PARAMETERS: Dict[str, RANParameterDefinition] = {
    "PRB_QUOTA": RANParameterDefinition(
        param_id=1,
        param_name="PRB_QUOTA",
        param_type="INTEGER",
        min_value=0.0,
        max_value=100.0,
        unit="percent",
        description="Fração de PRBs físicos alocados para a fatia de rede"
    ),
    "SCHEDULER_WEIGHT": RANParameterDefinition(
        param_id=2,
        param_name="SCHEDULER_WEIGHT",
        param_type="INTEGER",
        min_value=1.0,
        max_value=100.0,
        unit="weight",
        description="Peso relativo do agendador MAC Proportional Fair / RR"
    ),
    "TX_POWER": RANParameterDefinition(
        param_id=3,
        param_name="TX_POWER",
        param_type="INTEGER",
        min_value=-10.0,
        max_value=23.0,
        unit="dBm",
        description="Potência máxima de transmissão do setor gNodeB"
    ),
    "HANDOVER": RANParameterDefinition(
        param_id=4,
        param_name="HANDOVER",
        param_type="INTEGER",
        min_value=0.0,
        max_value=65535.0,
        unit="cell_id",
        description="Identificador da célula alvo para migração de UE"
    )
}

# Alias para retrocompatibilidade
PARAM_PROFILES = RAN_PARAMETERS

def validate_ran_parameter(param_name: str, value: float) -> Tuple[bool, int, str]:

    """
    Valida se o parâmetro pertence ao modelo E2SM-RC e respeita os limites operacionais.
    """
    if param_name not in RAN_PARAMETERS:
        return False, 99, f"Parâmetro desconhecido no modelo E2SM-RC: {param_name}"
    
    defn = RAN_PARAMETERS[param_name]
    if value < defn.min_value or value > defn.max_value:
        return False, defn.param_id, f"Valor {value} fora dos limites [{defn.min_value}, {defn.max_value}] {defn.unit}"
        
    return True, defn.param_id, "OK"
