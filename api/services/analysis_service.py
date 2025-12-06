"""
Servicio de análisis de contratos.
"""
import os
import uuid
import asyncio
from typing import Dict, Any, List

from core.config import settings
from core.logging import get_logger
from services.http_client import call_service
from services.gemini_service import gemini_service

logger = get_logger(__name__)


class AnalysisService:
    """Servicio para análisis de contratos inteligentes."""
    
    async def analyze_contract(
        self,
        code: str,
        filename: str,
        enable_auto_fix: bool = False
    ) -> Dict[str, Any]:
        """
        Analiza un contrato y opcionalmente intenta corregirlo.
        
        Args:
            code: Código fuente del contrato
            filename: Nombre del archivo
            enable_auto_fix: Si se deben intentar correcciones automáticas
            
        Returns:
            Resultados del análisis
        """
        analysis_id = str(uuid.uuid4())
        contract_folder = os.path.join(settings.WORKSPACE_DIR, analysis_id)
        
        current_code = code
        fix_history = []
        
        max_retries = settings.MAX_FIX_RETRIES if enable_auto_fix else 0
        
        try:
            os.makedirs(contract_folder, exist_ok=True)
            
            for attempt in range(max_retries + 1):
                logger.info(
                    f"Analysis attempt {attempt+1}/{max_retries+1} for {analysis_id}"
                )
                
                # Guardar contrato actual
                contract_path = os.path.join(contract_folder, filename)
                with open(contract_path, "w") as f:
                    f.write(current_code)
                
                # Llamar a todos los servicios en paralelo
                tool_results = await self._call_all_services(analysis_id, filename)
                
                # Agregar historial de correcciones si existe
                if fix_history:
                    tool_results["_fix_history"] = fix_history
                
                # Análisis con Gemini
                gemini_feedback = await gemini_service.analyze_contract(tool_results)
                
                # Si no se pidió corrección, terminar aquí
                if not enable_auto_fix:
                    return self._build_response(
                        gemini_feedback, 
                        tool_results, 
                        current_code, 
                        fix_history
                    )
                
                # Verificar si necesitamos corregir
                analysis_json = gemini_feedback.get("response", {})
                if not isinstance(analysis_json, dict):
                    break
                
                is_safe = analysis_json.get("status") == "SAFE"
                
                if is_safe:
                    logger.info(f"Contract deemed SAFE. Stopping correction loop.")
                    break
                
                # Intentar corrección si quedan intentos
                if attempt < max_retries:
                    logger.info(f"Attempting to fix contract. Attempt {attempt+1}")
                    fix_result = await gemini_service.fix_contract(
                        current_code, 
                        tool_results, 
                        analysis_json
                    )
                    
                    if fix_result.get("success") and fix_result.get("fix_data"):
                        fix_data = fix_result["fix_data"]
                        new_code = fix_data.get("fixed_code")
                        
                        if new_code and new_code.strip() != current_code.strip():
                            current_code = new_code
                            fix_history.append({
                                "attempt": attempt + 1,
                                "changes": fix_data.get("changes_made"),
                                "explanation": fix_data.get("explanation")
                            })
                            continue
                        else:
                            logger.warning("Gemini returned same code. No fixes applied.")
                            fix_history.append({
                                "attempt": attempt + 1,
                                "error": "Same code returned. No fixes applied."
                            })
                    else:
                        error_msg = fix_result.get('error', 'Unknown error')
                        logger.error(f"Fix failed: {error_msg}")
                        fix_history.append({
                            "attempt": attempt + 1,
                            "error": f"Fix generation failed: {error_msg}"
                        })
                    
                    break
            
            return self._build_response(
                gemini_feedback, 
                tool_results, 
                current_code, 
                fix_history
            )
            
        except Exception as e:
            logger.exception("Error in analysis loop")
            raise
    
    async def _call_all_services(
        self, 
        analysis_id: str, 
        filename: str
    ) -> Dict[str, Any]:
        """
        Llama a todos los microservicios en paralelo.
        
        Args:
            analysis_id: ID del análisis
            filename: Nombre del archivo
            
        Returns:
            Resultados de todos los servicios
        """
        tasks = [
            call_service(name, url, analysis_id, filename)
            for name, url in settings.services.items()
        ]
        
        results = await asyncio.gather(*tasks)
        
        output = {}
        for (service_name, _), result in zip(settings.services.items(), results):
            output[service_name] = result
        
        return output
    
    def _build_response(
        self,
        gemini_feedback: Dict[str, Any],
        tool_results: Dict[str, Any],
        current_code: str,
        fix_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Construye la respuesta final del análisis.
        
        Args:
            gemini_feedback: Feedback de Gemini
            tool_results: Resultados de las herramientas
            current_code: Código actual (potencialmente corregido)
            fix_history: Historial de correcciones
            
        Returns:
            Respuesta estructurada
        """
        response = {
            "results": gemini_feedback
        }
        
        if fix_history:
            response["fixed_contract_code"] = current_code
            response["fix_history"] = fix_history
            
            if isinstance(gemini_feedback.get("response"), dict):
                gemini_feedback["response"]["fix_summary"] = (
                    "El contrato fue corregido automáticamente. Ver historial."
                )
        
        return response


# Instancia global del servicio
analysis_service = AnalysisService()
