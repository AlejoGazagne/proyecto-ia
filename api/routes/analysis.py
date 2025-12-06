"""
Rutas de la API para análisis de contratos.
"""
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse

from models.schemas import ContractRequest
from services.analysis_service import analysis_service
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/analyze")
async def analyze_contract(request: ContractRequest = Body(...)):
    """
    Analiza un contrato Solidity.
    
    - **code**: Código fuente del contrato
    - **filename**: Nombre del archivo (opcional)
    - **is_production_ready**: Si es False, intenta correcciones automáticas
    
    Retorna un análisis completo del contrato incluyendo:
    - Vulnerabilidades detectadas
    - Resultados de compilación
    - Resultados de fuzzing
    - Recomendaciones de seguridad
    - Código corregido (si se solicitó)
    """
    try:
        result = await analysis_service.analyze_contract(
            code=request.code,
            filename=request.filename,
            enable_auto_fix=not request.is_production_ready
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception("Error during contract analysis")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
