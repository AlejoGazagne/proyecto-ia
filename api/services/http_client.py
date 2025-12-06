"""
Cliente HTTP para comunicación con microservicios.
"""
from typing import Dict, Any
import httpx
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


async def call_service(
    service_name: str, 
    service_url: str, 
    analysis_id: str, 
    filename: str
) -> Dict[str, Any]:
    """
    Llama a un microservicio de análisis de forma asíncrona.
    
    Args:
        service_name: Nombre del servicio (slither, solc, etc.)
        service_url: URL del servicio
        analysis_id: ID único del análisis
        filename: Nombre del archivo a analizar
        
    Returns:
        Diccionario con el resultado del análisis
    """
    try:
        async with httpx.AsyncClient(timeout=settings.SERVICE_TIMEOUT) as client:
            response = await client.post(
                f"{service_url}/analyze",
                json={
                    "analysis_id": analysis_id,
                    "filename": filename
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "error_type": "http_error"
                }
                
    except httpx.TimeoutException:
        logger.error(f"Service {service_name} timed out")
        return {
            "success": False,
            "error": f"Service {service_name} timed out",
            "error_type": "timeout"
        }
    except Exception as e:
        logger.exception(f"Error calling {service_name}")
        return {
            "success": False,
            "error": f"Error calling {service_name}: {str(e)}",
            "error_type": "connection_error"
        }
