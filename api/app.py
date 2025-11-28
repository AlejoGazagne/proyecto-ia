import uuid
import os
import asyncio
import json
import logging
from typing import Dict, Any, Tuple, Optional
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
from google import genai

logging.basicConfig(
    level=os.getenv("API_LOG_LEVEL", "INFO"),
    format="[%(asctime)s] %(levelname)s api_service - %(message)s"
)
logger = logging.getLogger("api_service")

app = FastAPI(title="ETH Security Toolbox API - Microservices")

class ContractRequest(BaseModel):
    code: str
    filename: str = "contract.sol"
    is_production_ready: bool = True

# URLs de los microservicios
SERVICES = {
    "slither": os.getenv("SLITHER_URL", "http://slither:8001"),
    "solc": os.getenv("SOLC_URL", "http://solc:8002"),
    "medusa": os.getenv("MEDUSA_URL", "http://medusa:8003"),
    "echidna": os.getenv("ECHIDNA_URL", "http://echidna:8004")
}

WORKSPACE_DIR = "/workspace"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
GEMINI_PROMPT_TEMPLATE = """Eres un experto analista de seguridad de smart contracts en Solidity. Tu tarea es analizar los resultados de múltiples herramientas de auditoría y generar un reporte conciso en formato JSON.
Datos de entrada
A continuación recibirás un JSON con los resultados del análisis de seguridad de un contrato Solidity que incluye:

Análisis estático con Slither (vulnerabilidades)
Compilación con Solc (estructura del contrato)
Fuzzing con Medusa y Echidna (testing automatizado)
Historial de correcciones (_fix_history): Si existe, contiene los intentos previos de corrección automática.

Tu tarea
Analiza los datos y genera un JSON con la siguiente estructura EXACTA:
json{
  "contract_name": "string - nombre del contrato analizado",
  "analysis_id": "string - ID único del análisis",
  "status": "SAFE | WARNING | CRITICAL - estado general del contrato",
  "risk_score": "number - puntuación de 0-100 (0=seguro, 100=muy peligroso)",
  
  "vulnerabilities": [
    {
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "type": "string - tipo de vulnerabilidad",
      "description": "string - explicación clara en español de 1-2 líneas",
      "location": "string - función o líneas afectadas",
      "recommendation": "string - cómo solucionarlo en 1-2 líneas"
    }
  ],
  
  "tools_reports": {
    "slither": {
      "status": "PASS | FAIL",
      "message": "string - resumen en español de lo encontrado",
      "issues_found": "number - cantidad de problemas encontrados"
    },
    "solc": {
      "status": "PASS | FAIL", 
      "message": "string - resumen en español del proceso de compilación",
      "contracts_compiled": "number"
    },
    "medusa": {
      "status": "PASS | FAIL",
      "message": "string - resumen en español del fuzzing",
      "tests_executed": "number"
    },
    "echidna": {
      "status": "PASS | FAIL",
      "message": "string - resumen en español del fuzzing",
      "tests_executed": "number"
    }
  },
  
  "contract_info": {
    "functions": ["array - nombres de funciones públicas/externas"],
    "has_payable_functions": "boolean",
    "compiled_successfully": "boolean"
  },
  
  "testing_results": {
    "total_tests": "number",
    "passed": "number",
    "failed": "number",
    "coverage_score": "number - % aproximado de cobertura"
  },
  
  "summary": {
    "is_production_ready": "boolean - ¿está listo para producción?",
    "critical_issues": "number - cantidad de issues críticos",
    "main_concerns": ["array - máximo 3 preocupaciones principales en español"],
    "recommendation": "string - recomendación final en 2-3 líneas"
  }
}
Reglas importantes:

Para tools_reports:

Slither:
PASS si no hay vulnerabilidades críticas/altas
Mensaje ejemplo: "Se encontró 1 issue informativo sobre la versión de Solidity" o "No se encontraron vulnerabilidades"

Solc:
PASS si exit_code = 0
Mensaje ejemplo: "Compilación exitosa sin errores" o "Error en la compilación: [razón]"

Medusa:
PASS si todos los tests pasaron
Mensaje ejemplo: "3 tests ejecutados exitosamente sin fallos" o "Se encontraron X tests fallidos"

Echidna:

PASS si todos los tests están "passing"
Mensaje ejemplo: "50,218 llamadas ejecutadas, todos los tests pasaron" o "Se detectaron fallos en las assertions"

Calcula el risk_score y status de forma COHERENTE:
CRITICAL (risk_score: 80-100):

Tiene al menos 1 vulnerabilidad CRITICAL o 2+ HIGH
Tests fallidos críticos
Compilación fallida

HIGH (risk_score: 50-79):
Tiene 1 vulnerabilidad HIGH
Varios MEDIUM con impacto serio

MEDIUM (risk_score: 25-49):
Tiene vulnerabilidades MEDIUM
Problemas menores detectados

LOW (risk_score: 10-24):
Solo issues informativos importantes
Mejores prácticas no seguidas

SAFE (risk_score: 0-9):
Sin vulnerabilidades significativas
Solo issues informativos menores o ninguno

Regla de oro: El status DEBE reflejar la severidad MÁS ALTA encontrada:

Si hay HIGH → status debe ser HIGH (no WARNING)
Si hay CRITICAL → status debe ser CRITICAL
El risk_score debe estar en el rango correspondiente al status

Para vulnerabilities:

Solo incluye las que realmente importan (omite issues puramente informativos de versiones si no hay otros problemas)
Traduce las descripciones técnicas a español claro
Sé específico en las recomendaciones

Para is_production_ready:

false si hay vulnerabilidades CRITICAL o HIGH
false si hay tests fallidos
false si el risk_score > 30
true en caso contrario

Para main_concerns:

Lista las 3 preocupaciones MÁS importantes
Si no hay problemas serios, deja el array vacío
Si hay un historial de correcciones (_fix_history), DEBES mencionar qué problemas originales fueron corregidos.

Para strengths:

Si el contrato pasó todos los tests, mencionar "Testing exhaustivo exitoso"
Si tiene buena estructura, mencionar "Arquitectura bien organizada"
Si no tiene vulnerabilidades críticas, mencionar "Sin vulnerabilidades de alta severidad"

Formato de respuesta
Responde ÚNICAMENTE con el objeto JSON, sin texto adicional antes o después. No uses markdown, ni etiquetas, solo el JSON puro."""

GEMINI_FIX_PROMPT_TEMPLATE = """Eres un experto desarrollador de seguridad en Solidity.
Tu tarea es CORREGIR un contrato inteligente que ha fallado en un análisis de seguridad.

Código Original:
{code}

Reporte de Análisis (JSON):
{analysis_json}

Resultados de Herramientas (JSON):
{tool_outputs}

Tu tarea:
1. Analiza las vulnerabilidades reportadas en el análisis y por las herramientas.
2. Reescribe el contrato completo corrigiendo TODOS los errores de seguridad encontrados.
3. Mantén la funcionalidad original del contrato tanto como sea posible, solo arregla la seguridad.
4. Si hay problemas de reentrancia, overflow, control de acceso, etc., aplícales los patrones de diseño seguros correspondientes.

Formato de Salida (JSON):
Responde ÚNICAMENTE con un objeto JSON con la siguiente estructura:
json{{
  "fixed_code": "string - el código fuente completo del contrato corregido",
  "changes_made": [
    {{
      "issue": "string - nombre de la vulnerabilidad corregida",
      "fix_description": "string - descripción técnica de qué cambiaste",
      "severity": "string - severidad original (CRITICAL, HIGH, etc)"
    }}
  ],
  "explanation": "string - resumen general de las correcciones aplicadas"
}}
"""

try:
    GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except Exception as exc:  # pragma: no cover - defensive
    logger.error("Failed to initialize Gemini client: %s", exc)
    GEMINI_CLIENT = None

logger.info(
    "Gemini configuration loaded | key_present=%s model=%s client_ready=%s",
    bool(GEMINI_API_KEY),
    GEMINI_MODEL,
    GEMINI_CLIENT is not None
)


def _extract_json_from_text(text: str) -> Tuple[Optional[Any], Optional[str]]:
    """Try to parse a Gemini response into JSON, handling ``` fences."""
    if not text:
        return None, "empty_response"

    cleaned = text.strip()
    
    # Intentar encontrar el bloque JSON entre ```json y ``` o simplemente entre { y }
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
        
        # Estrategia 2: Buscar simplemente el primer { y el último }
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = cleaned[start_idx:end_idx+1]
            return json.loads(json_str), None
            
        # Estrategia 3: Intentar parsear todo el texto (si no tiene markdown)
        return json.loads(cleaned), None
        
    except json.JSONDecodeError as exc:
        return None, f"json_decode_error: {exc} | Text snippet: {cleaned[:100]}..."


async def query_gemini(tool_outputs: Dict[str, Any]) -> Dict[str, Any]:
    """Envía los resultados agregados a Gemini antes de responder al usuario."""
    prompt = GEMINI_PROMPT_TEMPLATE.strip()

    if not GEMINI_API_KEY:
        logger.warning("Gemini API key missing; skipping Gemini call")
        return {"enabled": False, "reason": "missing_api_key"}
    if not prompt or "<<<" in prompt:
        logger.warning("Gemini prompt not configured; skipping Gemini call")
        return {"enabled": False, "reason": "missing_prompt"}
    if GEMINI_CLIENT is None:
        logger.warning("Gemini client not initialized; skipping Gemini call")
        return {"enabled": False, "reason": "client_not_initialized"}

    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: GEMINI_CLIENT.models.generate_content(
                model=GEMINI_MODEL,
                contents=f"{prompt}\n\nResultados de herramientas:\n{json.dumps(tool_outputs, ensure_ascii=False)}"
            )
        )
        text_response = getattr(response, "text", None)
        if not text_response:
            # Some SDK versions return candidates via response.candidates
            candidates = getattr(response, "candidates", [])
            texts = []
            for cand in candidates or []:
                parts = getattr(getattr(cand, "content", None), "parts", []) or []
                for part in parts:
                    text = part.get("text") if isinstance(part, dict) else getattr(part, "text", "")
                    if text:
                        texts.append(text)
            text_response = "\n".join(texts).strip() if texts else None

        parsed_json, parse_error = _extract_json_from_text(text_response)
        response_payload = {
            "enabled": True,
            "response": parsed_json if parsed_json is not None else text_response,
            "response_format": "json" if parsed_json is not None else "text",
            # "raw_text": text_response,
            # "raw": response.to_dict() if hasattr(response, "to_dict") else None
        }
        if parse_error:
            response_payload["parse_warning"] = parse_error
        return response_payload
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected Gemini error")
        return {"enabled": True, "error": f"Gemini request failed: {exc}"}

async def call_service(service_name: str, service_url: str, analysis_id: str, filename: str) -> Dict[str, Any]:
    """
    Llama a un microservicio de análisis de forma asíncrona.
    """
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
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
        return {
            "success": False,
            "error": f"Service {service_name} timed out",
            "error_type": "timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error calling {service_name}: {str(e)}",
            "error_type": "connection_error"
        }

@app.post("/analyze")
async def analyze(request: ContractRequest = Body(...)):
    """
    Recibe un contrato Solidity, lo guarda en el volumen compartido
    y distribuye el análisis a todos los microservicios.
    Si is_production_ready es False, intenta corregir el contrato automáticamente.
    """
    # Generar ID único para este análisis
    analysis_id = str(uuid.uuid4())
    contract_folder = os.path.join(WORKSPACE_DIR, analysis_id)
    
    current_code = request.code
    current_filename = request.filename
    
    # Historial de correcciones
    fix_history = []
    
    # Si is_production_ready es False, habilitamos el loop de corrección (max 3 reintentos)
    max_retries = 3 if not request.is_production_ready else 0
    
    final_output = {}
    final_gemini_feedback = {}
    
    try:
        # Crear carpeta para este análisis
        os.makedirs(contract_folder, exist_ok=True)
        
        for attempt in range(max_retries + 1):
            logger.info(f"Starting analysis attempt {attempt+1}/{max_retries+1} for {analysis_id}")
            
            # Guardar contrato (actualizado si es un reintento)
            contract_path = os.path.join(contract_folder, current_filename)
            with open(contract_path, "w") as f:
                f.write(current_code)
            
            # Llamar a todos los servicios en paralelo
            tasks = [
                call_service(name, url, analysis_id, current_filename)
                for name, url in SERVICES.items()
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Construir respuesta consolidada
            output = {}
            has_critical_errors = False
            tools_with_errors = []
            
            for (service_name, _), result in zip(SERVICES.items(), results):
                output[service_name] = result
                service_success = result.get("success")
                error_type = result.get("error_type")

                if not service_success and error_type != "vulnerabilities_found":
                    has_critical_errors = True
                    tools_with_errors.append(service_name)
            
            # Si hay historial, lo agregamos al output para que Gemini lo vea en el análisis final
            if fix_history:
                output["_fix_history"] = fix_history

            gemini_feedback = await query_gemini(output)
            
            final_output = output
            final_gemini_feedback = gemini_feedback
            
            # Si is_production_ready es True, terminamos aquí (comportamiento original)
            if request.is_production_ready:
                break
                
            # Verificar si necesitamos corregir
            analysis_json = gemini_feedback.get("response", {})
            if not isinstance(analysis_json, dict):
                break # No se pudo parsear, abortar loop
                
            is_safe = analysis_json.get("status") == "SAFE"
            risk_score = analysis_json.get("risk_score", 100)
            
            # Criterio de parada: SAFE
            # Si el usuario pidió corrección (is_production_ready=False), somos más estrictos:
            # Solo paramos si es SAFE. Ignoramos el risk_score < 30 para forzar corrección si hay warnings.
            if is_safe:
                logger.info(f"Contract deemed SAFE (Score: {risk_score}). Stopping loop.")
                break
            
            if attempt < max_retries:
                logger.info(f"Attempting to fix contract. Attempt {attempt+1}")
                fix_result = await request_fix_from_gemini(current_code, output, analysis_json)
                
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
                        logger.warning("Gemini returned the same code or empty code. No fixes applied.")
                        fix_history.append({
                            "attempt": attempt + 1,
                            "error": "Gemini returned the same code. No fixes applied."
                        })
                else:
                    error_msg = fix_result.get('error', 'Unknown error')
                    logger.error(f"Fix failed: {error_msg}")
                    fix_history.append({
                        "attempt": attempt + 1,
                        "error": f"Fix generation failed: {error_msg}"
                    })
                
                # Si fallamos en arreglar (ya sea por error o porque no hubo cambios), 
                # salimos del loop para evitar bucles infinitos o reintentos inútiles.
                break
        
        # Preparar respuesta final
        response_content = {
            "results": final_gemini_feedback,
            # "tools_results": final_output # Opcional: incluir resultados crudos
        }
        
        if fix_history:
            response_content["fixed_contract_code"] = current_code
            response_content["fix_history"] = fix_history
            # Asegurar que el análisis final mencione el historial
            if isinstance(final_gemini_feedback.get("response"), dict):
                 final_gemini_feedback["response"]["fix_summary"] = "El contrato fue corregido automáticamente. Ver historial."

        return JSONResponse(content=response_content)
        
    except Exception as e:
        logger.exception("Error in analyze loop")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Internal server error: {str(e)}",
                "analysis_id": analysis_id
            }
        )

@app.get("/health")
async def health_check():
    """
    Verifica el estado de todos los microservicios.
    """
    health_status = {}
    
    async def check_service(name: str, url: str):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                return name, response.status_code == 200
        except:
            return name, False
    
    tasks = [check_service(name, url) for name, url in SERVICES.items()]
    results = await asyncio.gather(*tasks)
    
    for name, is_healthy in results:
        health_status[name] = "healthy" if is_healthy else "unhealthy"
    
    all_healthy = all(status == "healthy" for status in health_status.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": health_status
    }

@app.get("/")
async def root():
    """
    Información de la API.
    """
    return {
        "message": "ETH Security Toolbox API - Microservices Architecture",
        "version": "2.0",
        "endpoints": {
            "analyze": "POST /analyze - Analyze a Solidity contract",
            "health": "GET /health - Check all services health"
        },
        "available_tools": list(SERVICES.keys())
    }

async def request_fix_from_gemini(code: str, tool_outputs: Dict[str, Any], analysis_json: Dict[str, Any]) -> Dict[str, Any]:
    """Solicita a Gemini que corrija el contrato basado en los reportes."""
    prompt = GEMINI_FIX_PROMPT_TEMPLATE.format(
        code=code,
        analysis_json=json.dumps(analysis_json, ensure_ascii=False),
        tool_outputs=json.dumps(tool_outputs, ensure_ascii=False)
    )

    if not GEMINI_API_KEY or GEMINI_CLIENT is None:
        return {"enabled": False, "reason": "gemini_not_configured"}

    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: GEMINI_CLIENT.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
        )
        text_response = getattr(response, "text", None)
        if not text_response:
             # Fallback for candidates
            candidates = getattr(response, "candidates", [])
            texts = []
            for cand in candidates or []:
                parts = getattr(getattr(cand, "content", None), "parts", []) or []
                for part in parts:
                    text = part.get("text") if isinstance(part, dict) else getattr(part, "text", "")
                    if text:
                        texts.append(text)
            text_response = "\n".join(texts).strip() if texts else None

        parsed_json, parse_error = _extract_json_from_text(text_response)
        return {
            "success": parsed_json is not None,
            "fix_data": parsed_json,
            "error": parse_error
        }
    except Exception as exc:
        logger.exception("Error requesting fix from Gemini")
        return {"success": False, "error": str(exc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
