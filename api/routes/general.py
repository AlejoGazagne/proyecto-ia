"""
Rutas generales de la API.
"""
from fastapi import APIRouter
from core.config import settings

router = APIRouter()


@router.get("/")
async def root():
    """
    Información general de la API.
    """
    return {
        "message": f"{settings.APP_NAME} - Microservices Architecture",
        "version": settings.VERSION,
        "endpoints": {
            "analyze": "POST /analyze - Analyze a Solidity contract",
            "docs": "GET /docs - Interactive API documentation"
        },
        "available_tools": list(settings.services.keys())
    }
