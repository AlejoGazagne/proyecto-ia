# Stage 1: Get Solc binary
FROM ethereum/solc:0.8.20 AS solc-binary

# Stage 2: Runtime
FROM python:3.9-slim

# Copiar binario de solc desde imagen oficial
COPY --from=solc-binary /usr/bin/solc /usr/local/bin/solc

# Instalar dependencias mínimas
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Instalar dependencias de Python
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    requests

WORKDIR /app

# Copiar servidor
COPY solc_server.py .

# Exponer puerto
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8002/health')"

# Arrancar servidor
CMD ["uvicorn", "solc_server:app", "--host", "0.0.0.0", "--port", "8002"]
