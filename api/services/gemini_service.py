"""
Servicio de integración con Gemini AI.
"""
import asyncio
import json
from typing import Dict, Any, Tuple, Optional
from google import genai

from core.config import settings
from core.logging import get_logger
from services.prompts import ANALYSIS_PROMPT, FIX_PROMPT

logger = get_logger(__name__)


class GeminiService:
    """Servicio para interactuar con Gemini AI."""
    
    def __init__(self):
        """Inicializa el cliente de Gemini."""
        self.client = None
        self.enabled = False
        
        if settings.GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
                self.enabled = True
                logger.info(
                    f"Gemini initialized | model={settings.GEMINI_MODEL} enabled=True"
                )
            except Exception as exc:
                logger.error(f"Failed to initialize Gemini client: {exc}")
        else:
            logger.warning("Gemini API key not configured")
    
    def _extract_json_from_text(self, text: str) -> Tuple[Optional[Any], Optional[str]]:
        """
        Intenta parsear una respuesta de Gemini a JSON, manejando bloques de código.
        
        Args:
            text: Texto de respuesta de Gemini
            
        Returns:
            Tupla (json_parseado, error)
        """
        if not text:
            return None, "empty_response"

        cleaned = text.strip()
        
        try:
            # Estrategia 1: Buscar bloques de código markdown
            start_marker = "```json"
            end_marker = "```"
            start_idx = cleaned.find(start_marker)
            
            if start_idx != -1:
                start_idx += len(start_marker)
                end_idx = cleaned.find(end_marker, start_idx)
                if end_idx != -1:
                    json_str = cleaned[start_idx:end_idx].strip()
                    return json.loads(json_str), None
            
            # Estrategia 2: Buscar primer { y último }
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}")
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = cleaned[start_idx:end_idx+1]
                return json.loads(json_str), None
                
            # Estrategia 3: Parsear todo el texto
            return json.loads(cleaned), None
            
        except json.JSONDecodeError as exc:
            return None, f"json_decode_error: {exc} | Text snippet: {cleaned[:100]}..."
    
    async def analyze_contract(self, tool_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza los resultados de las herramientas con Gemini.
        
        Args:
            tool_outputs: Resultados de los microservicios
            
        Returns:
            Análisis de Gemini o error
        """
        if not self.enabled or not self.client:
            logger.warning("Gemini not available; skipping analysis")
            return {"enabled": False, "reason": "gemini_not_configured"}
        
        try:
            prompt = f"{ANALYSIS_PROMPT}\n\nResultados de herramientas:\n{json.dumps(tool_outputs, ensure_ascii=False)}"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )
            )
            
            text_response = self._extract_response_text(response)
            parsed_json, parse_error = self._extract_json_from_text(text_response)
            
            response_payload = {
                "enabled": True,
                "response": parsed_json if parsed_json is not None else text_response,
                "response_format": "json" if parsed_json is not None else "text"
            }
            
            if parse_error:
                response_payload["parse_warning"] = parse_error
                
            return response_payload
            
        except Exception as exc:
            logger.exception("Unexpected Gemini error during analysis")
            return {"enabled": True, "error": f"Gemini request failed: {exc}"}
    
    async def fix_contract(
        self, 
        code: str, 
        tool_outputs: Dict[str, Any], 
        analysis_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Solicita a Gemini que corrija el contrato.
        
        Args:
            code: Código fuente del contrato
            tool_outputs: Resultados de las herramientas
            analysis_json: Análisis previo
            
        Returns:
            Contrato corregido o error
        """
        if not self.enabled or not self.client:
            return {"success": False, "reason": "gemini_not_configured"}
        
        try:
            prompt = FIX_PROMPT.format(
                code=code,
                analysis_json=json.dumps(analysis_json, ensure_ascii=False),
                tool_outputs=json.dumps(tool_outputs, ensure_ascii=False)
            )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )
            )
            
            text_response = self._extract_response_text(response)
            parsed_json, parse_error = self._extract_json_from_text(text_response)
            
            return {
                "success": parsed_json is not None,
                "fix_data": parsed_json,
                "error": parse_error
            }
            
        except Exception as exc:
            logger.exception("Error requesting fix from Gemini")
            return {"success": False, "error": str(exc)}
    
    def _extract_response_text(self, response) -> Optional[str]:
        """Extrae el texto de respuesta del objeto de Gemini."""
        text_response = getattr(response, "text", None)
        
        if not text_response:
            # Fallback para candidates
            candidates = getattr(response, "candidates", [])
            texts = []
            for cand in candidates or []:
                parts = getattr(getattr(cand, "content", None), "parts", []) or []
                for part in parts:
                    text = part.get("text") if isinstance(part, dict) else getattr(part, "text", "")
                    if text:
                        texts.append(text)
            text_response = "\n".join(texts).strip() if texts else None
        
        return text_response


# Instancia global del servicio
gemini_service = GeminiService()
