# Stage 1: Obtain solc binary
FROM ethereum/solc:0.8.20 AS solc-binary

# Stage 2: Runtime
FROM python:3.9-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Instalar Slither y dependencias de Python
RUN pip install --no-cache-dir \
    slither-analyzer \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    requests

# Copiar solc desde la imagen oficial DESPUÉS de pip install para evitar que solc-select lo sobrescriba
COPY --from=solc-binary /usr/bin/solc /usr/local/bin/solc

WORKDIR /app

# Copiar servidor
COPY slither_server.py .

# Exponer puerto
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')"

# Arrancar servidor
CMD ["uvicorn", "slither_server:app", "--host", "0.0.0.0", "--port", "8001"]
