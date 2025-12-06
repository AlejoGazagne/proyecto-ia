"""
Prompts para Gemini AI.
"""

ANALYSIS_PROMPT = """Eres un experto analista de seguridad de smart contracts en Solidity. Tu tarea es analizar los resultados de múltiples herramientas de auditoría y generar un reporte conciso en formato JSON.
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


FIX_PROMPT = """Eres un experto desarrollador de seguridad en Solidity.
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
