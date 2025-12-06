# ETH Security - Arquitectura de Microservicios

Sistema de análisis de seguridad para contratos inteligentes Ethereum basado en microservicios Docker.

## Arquitectura

```
eth-security-microservices/
├── api/                      # API principal (FastAPI)
│   ├── core/                 # Configuración y utilidades
│   ├── models/               # Modelos Pydantic
│   ├── routes/               # Endpoints REST
│   ├── services/             # Lógica de negocio
│   ├── main.py               # Punto de entrada
│   ├── Dockerfile
│   └── requirements.txt
├── slither/                  # Servicio de análisis Slither
│   ├── slither_server.py
│   ├── Dockerfile
│   └── requirements.txt
├── solc/                     # Servicio de compilación Solc
│   ├── solc_server.py
│   ├── Dockerfile
│   └── requirements.txt
├── medusa/                   # Servicio de fuzzing Medusa
│   ├── medusa_server.py
│   ├── Dockerfile
│   └── requirements.txt
├── echidna/                  # Servicio de testing Echidna
│   ├── echidna_server.py
│   ├── Dockerfile
│   └── requirements.txt
├── shared_workspace/         # Volumen compartido entre servicios
├── docker-compose.yml        # Orquestación de servicios
└── README.md
```

## Servicios

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **API Principal** | 8000 | Coordinador que distribuye análisis |
| **Slither** | 8001 | Análisis de vulnerabilidades |
| **Solc** | 8002 | Compilador de Solidity |
| **Medusa** | 8003 | Fuzzing de contratos |
| **Echidna** | 8004 | Property-based testing |

## Instalación

### Iniciar Sistema Completo

```bash
# Iniciar en segundo plano
docker compose up -d --build

# Ver logs
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f api
docker compose logs -f slither
```

## Uso

### Endpoint Principal

**POST** `http://localhost:8000/analyze`

```json
{
  "code": "pragma solidity ^0.8.0;\ncontract Example { uint256 public value; }",
  "filename": "contract.sol"
}
```

## Respuesta de la API

```json
{
  "success": true,
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "contract.sol",
  "has_critical_errors": false,
  "tools_with_errors": [],
  "results": {
    "slither": {
      "success": true,
      "command": "slither /workspace/...",
      "stdout": "...",
      "stderr": "...",
      "exit_code": 1,
      "error_type": "vulnerabilities_found",
      "generated_json": {...}
    },
    "solc": {
      "success": true,
      "compiled_json": {...}
    },
    "medusa": {
      "success": true,
      "stdout": "..."
    },
    "echidna": {
      "success": true,
      "stdout": "..."
    }
  }
}
```

## Límites de Recursos

| Servicio | CPU | Memoria |
|----------|-----|---------|
| API | 1 core | 512MB |
| Slither | 1 core | 1GB |
| Solc | 0.5 core | 512MB |
| Medusa | 2 cores | 2GB |
| Echidna | 2 cores | 2GB |

## Flujo de Trabajo

1. Usuario envía contrato a `POST /analyze`
2. API guarda contrato en `/workspace/[analysis_id]/`
3. API llama concurrentemente a todos los microservicios
4. Cada servicio ejecuta su análisis sobre el archivo compartido
5. API consolida resultados y devuelve respuesta unificada
6. Archivos temporales persisten en volumen compartido

## Arquitectura de la API

La API principal sigue una arquitectura modular con separación de responsabilidades:

- **core/**: Configuración y utilidades compartidas
- **models/**: Modelos de datos y validación (Pydantic)
- **routes/**: Definición de endpoints REST
- **services/**: Lógica de negocio y servicios externos

### Beneficios

✅ **Mantenibilidad**: Código organizado y fácil de mantener
✅ **Escalabilidad**: Fácil agregar nuevas funcionalidades
✅ **Testabilidad**: Componentes independientes y testeables
✅ **Documentación**: FastAPI genera docs automáticas en `/docs`

## Personalización

### Agregar nueva herramienta

1. Crear carpeta `newtool/`
2. Crear `newtool_server.py` con FastAPI
3. Crear `Dockerfile` para la herramienta
4. Agregar servicio en `docker-compose.yml`
5. Actualizar `api/core/config.py` para incluir nuevo servicio

### Modificar timeouts

Editar en `api/core/config.py`:
```python
SERVICE_TIMEOUT: float = 600.0  # 10 minutos
```

### Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:
```bash
GEMINI_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-pro
API_LOG_LEVEL=INFO
```