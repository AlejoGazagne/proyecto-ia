# Stage 1: Build Medusa
FROM golang:1.23-alpine AS builder

RUN apk add --no-cache git
RUN go install github.com/crytic/medusa@latest

# Stage 2: Get Solc binary
FROM ethereum/solc:0.8.20 AS solc-binary

# Stage 3: Runtime
FROM python:3.9-slim

# Copiar binario de Medusa desde builder
COPY --from=builder /go/bin/medusa /usr/local/bin/medusa

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
    requests \
    crytic-compile

# Copiar solc desde la imagen oficial DESPUÉS de pip install
COPY --from=solc-binary /usr/bin/solc /usr/local/bin/solc

WORKDIR /app

# Copiar servidor
COPY medusa_server.py .

# Exponer puerto
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8003/health')"

# Arrancar servidor
CMD ["uvicorn", "medusa_server:app", "--host", "0.0.0.0", "--port", "8003"]
