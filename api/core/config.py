"""
Configuración centralizada de la aplicación.
"""
import os
from typing import Dict


class Settings:
    """Configuración de la aplicación."""
    
    # Configuración básica
    APP_NAME: str = "ETH Security Toolbox API"
    VERSION: str = "2.0"
    LOG_LEVEL: str = os.getenv("API_LOG_LEVEL", "INFO")
    
    # URLs de microservicios
    SLITHER_URL: str = os.getenv("SLITHER_URL", "http://slither:8001")
    SOLC_URL: str = os.getenv("SOLC_URL", "http://solc:8002")
    MEDUSA_URL: str = os.getenv("MEDUSA_URL", "http://medusa:8003")
    ECHIDNA_URL: str = os.getenv("ECHIDNA_URL", "http://echidna:8004")
    
    # Workspace
    WORKSPACE_DIR: str = "/workspace"
    
    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-pro")
    
    # Timeouts
    SERVICE_TIMEOUT: float = 300.0
    
    # Límites de reintentos para corrección automática
    MAX_FIX_RETRIES: int = 3
    
    @property
    def services(self) -> Dict[str, str]:
        """Retorna diccionario de servicios disponibles."""
        return {
            "slither": self.SLITHER_URL,
            "solc": self.SOLC_URL,
            "medusa": self.MEDUSA_URL,
            "echidna": self.ECHIDNA_URL
        }


settings = Settings()
