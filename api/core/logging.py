"""
Configuración de logging para la aplicación.
"""
import logging
from core.config import settings


def setup_logging():
    """Configura el sistema de logging."""
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="[%(asctime)s] %(levelname)s %(name)s - %(message)s"
    )


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger configurado."""
    return logging.getLogger(name)
