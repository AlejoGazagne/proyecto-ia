"""
Modelos Pydantic para la API.
"""
from pydantic import BaseModel, Field


class ContractRequest(BaseModel):
    """Modelo para la solicitud de análisis de contrato."""
    code: str = Field(..., description="Código fuente del contrato Solidity")
    filename: str = Field(default="contract.sol", description="Nombre del archivo")
    is_production_ready: bool = Field(
        default=True, 
        description="Si es False, intenta correcciones automáticas"
    )


class FixChange(BaseModel):
    """Modelo para un cambio de corrección."""
    issue: str
    fix_description: str
    severity: str


class FixResult(BaseModel):
    """Modelo para el resultado de una corrección."""
    fixed_code: str
    changes_made: list[FixChange]
    explanation: str
