# ETH Security Toolbox - Arquitectura de Microservicios

Sistema de análisis de seguridad para contratos inteligentes Ethereum basado en microservicios Docker.

## 🏗️ Arquitectura

```
eth-security-microservices/
├── api/                      # API principal (FastAPI)
│   ├── app.py
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

## 🚀 Servicios

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **API Principal** | 8000 | Coordinador que distribuye análisis |
| **Slither** | 8001 | Análisis de vulnerabilidades |
| **Solc** | 8002 | Compilador de Solidity |
| **Medusa** | 8003 | Fuzzing de contratos |
| **Echidna** | 8004 | Property-based testing |
| **n8n** | 5678 | Automatización de workflows (opcional) |

## 📦 Instalación

### Prerrequisitos
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM mínimo (16GB recomendado)

### Iniciar Sistema Completo

```bash
# Construir e iniciar todos los servicios
docker-compose up --build

# Iniciar en segundo plano
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f api
docker-compose logs -f slither
```

## 🔍 Uso

### Endpoint Principal

**POST** `http://localhost:8000/analyze`

```json
{
  "code": "pragma solidity ^0.8.0;\ncontract Example { uint256 public value; }",
  "filename": "contract.sol"
}
```

### Ejemplo con cURL

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "pragma solidity ^0.8.0; contract Test { uint256 x; }",
    "filename": "test.sol"
  }'
```

### Ejemplo con Python

```python
import requests

response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "code": """
pragma solidity ^0.8.0;

contract VulnerableContract {
    address public owner;
    
    function withdraw() public {
        payable(msg.sender).transfer(address(this).balance);
    }
}
        """,
        "filename": "vulnerable.sol"
    }
)

result = response.json()
print(result)
```

## 📊 Respuesta de la API

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

## 🏥 Health Check

Verificar estado de todos los servicios:

**GET** `http://localhost:8000/health`

```json
{
  "status": "healthy",
  "services": {
    "slither": "healthy",
    "solc": "healthy",
    "medusa": "healthy",
    "echidna": "healthy"
  }
}
```

## 🔧 Comandos Útiles

```bash
# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

# Reconstruir un servicio específico
docker-compose build slither
docker-compose up -d slither

# Ver recursos utilizados
docker stats

# Acceder a logs de un contenedor
docker logs -f eth-security-api

# Ejecutar comando dentro de un contenedor
docker exec -it eth-security-slither bash

# Ver volumen compartido
docker volume inspect eth_shared_workspace

# Limpiar recursos no utilizados
docker system prune -a
```

## 🔒 Consideraciones de Seguridad

- Los contenedores no requieren permisos root
- Red interna aislada (`eth-security-network`)
- Volumen compartido solo entre servicios autorizados
- Timeouts de 300 segundos por análisis
- Límites de recursos por contenedor

## 📈 Límites de Recursos

| Servicio | CPU | Memoria |
|----------|-----|---------|
| API | 1 core | 512MB |
| Slither | 1 core | 1GB |
| Solc | 0.5 core | 512MB |
| Medusa | 2 cores | 2GB |
| Echidna | 2 cores | 2GB |
| n8n | 1 core | 1GB |

## 🐛 Troubleshooting

### Error: Port already in use
```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8080:8000"  # Puerto host:container
```

### Error: Cannot connect to Docker daemon
```bash
sudo systemctl start docker
sudo usermod -aG docker $USER
```

### Servicio no responde
```bash
# Reiniciar servicio específico
docker-compose restart slither

# Ver logs detallados
docker-compose logs --tail=100 slither
```

### Volumen sin espacio
```bash
# Limpiar archivos temporales
docker exec -it eth-security-api rm -rf /workspace/*

# Recrear volumen
docker-compose down -v
docker-compose up -d
```

## 📚 Documentación Interactiva

- **API Principal**: http://localhost:8000/docs
- **Slither Service**: http://localhost:8001/docs
- **Solc Service**: http://localhost:8002/docs
- **Medusa Service**: http://localhost:8003/docs
- **Echidna Service**: http://localhost:8004/docs

## 🔄 Flujo de Trabajo

1. Usuario envía contrato a `POST /analyze`
2. API guarda contrato en `/workspace/[analysis_id]/`
3. API llama concurrentemente a todos los microservicios
4. Cada servicio ejecuta su análisis sobre el archivo compartido
5. API consolida resultados y devuelve respuesta unificada
6. Archivos temporales persisten en volumen compartido

## 🛠️ Personalización

### Agregar nueva herramienta

1. Crear carpeta `newtool/`
2. Crear `newtool_server.py` con FastAPI
3. Crear `Dockerfile` para la herramienta
4. Agregar servicio en `docker-compose.yml`
5. Actualizar `api/app.py` para incluir nuevo servicio

### Modificar timeouts

Editar en `api/app.py`:
```python
async with httpx.AsyncClient(timeout=600.0) as client:  # 10 minutos
```

## 📄 Licencia

MIT License

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📞 Soporte

Para problemas o preguntas:
- Abrir un issue en GitHub
- Consultar documentación en `/docs`
- Revisar logs con `docker-compose logs`
