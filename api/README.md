# API Principal - Estructura del Proyecto

Esta API sigue las mejores prácticas de FastAPI con una arquitectura modular y escalable.

## Estructura

```
api/
├── core/
│   ├── __init__.py
│   ├── config.py          # Configuración centralizada
│   └── logging.py         # Configuración de logs
├── models/
│   ├── __init__.py
│   └── schemas.py         # Modelos Pydantic
├── services/
│   ├── __init__.py
│   ├── analysis_service.py    # Lógica de análisis
│   ├── gemini_service.py      # Integración con Gemini AI
│   ├── http_client.py         # Cliente HTTP para microservicios
│   └── prompts.py             # Prompts para IA
├── routes/
│   ├── __init__.py
│   ├── analysis.py        # Rutas de análisis
│   └── general.py         # Rutas generales
├── main.py                # Punto de entrada
├── app.py                 # DEPRECATED - Mantener temporalmente
├── Dockerfile
└── requirements.txt
```

## Componentes

### Core
- **config.py**: Configuración centralizada usando variables de entorno
- **logging.py**: Sistema de logging consistente

### Models
- **schemas.py**: Modelos Pydantic para validación de datos

### Services
- **analysis_service.py**: Orquesta el análisis completo de contratos
- **gemini_service.py**: Maneja la comunicación con Gemini AI
- **http_client.py**: Cliente HTTP para llamar a microservicios
- **prompts.py**: Plantillas de prompts para IA

### Routes
- **analysis.py**: Endpoints de análisis de contratos
- **general.py**: Endpoints generales (info, status)

## Características

✅ **Separación de responsabilidades**: Cada módulo tiene una responsabilidad clara
✅ **Configuración centralizada**: Todas las variables en un solo lugar
✅ **Inyección de dependencias**: Servicios reutilizables
✅ **Logging estructurado**: Logs consistentes en toda la aplicación
✅ **Async/await**: Operaciones asíncronas para mejor rendimiento
✅ **Validación de datos**: Pydantic para validación automática
✅ **Documentación automática**: FastAPI genera docs en `/docs`

## Uso

### Desarrollo Local

```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t eth-security-api .
docker run -p 8000:8000 eth-security-api
```

## Variables de Entorno

```bash
# Logging
API_LOG_LEVEL=INFO

# Microservicios
SLITHER_URL=http://slither:8001
SOLC_URL=http://solc:8002
MEDUSA_URL=http://medusa:8003
ECHIDNA_URL=http://echidna:8004

# Gemini AI
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-pro
```

## Endpoints

- `GET /` - Información de la API
- `POST /analyze` - Analizar un contrato
- `GET /docs` - Documentación interactiva
- `GET /redoc` - Documentación alternativa

## Migración

El archivo `app.py` antiguo se mantiene temporalmente para compatibilidad. Una vez verificado el funcionamiento, puede eliminarse.
