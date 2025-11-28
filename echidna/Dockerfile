# Stage 1: Download Echidna
FROM debian:bullseye-slim AS downloader

RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
RUN wget https://github.com/crytic/echidna/releases/download/v2.2.4/echidna-2.2.4-x86_64-linux.tar.gz && \
    tar -xzf echidna-2.2.4-x86_64-linux.tar.gz

# Stage 2: Get Solc binary
FROM ethereum/solc:0.8.20 AS solc-binary

# Stage 3: Runtime
FROM python:3.9-slim

# Copiar binario de Echidna desde downloader
COPY --from=downloader /tmp/echidna /usr/local/bin/echidna
RUN chmod +x /usr/local/bin/echidna

# Instalar dependencias mínimas
RUN apt-get update && apt-get install -y \
    curl \
    libgmp10 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Instalar dependencias de Python
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    requests \
    crytic-compile \
    slither-analyzer

# Copiar solc desde la imagen oficial DESPUÉS de pip install
COPY --from=solc-binary /usr/bin/solc /usr/local/bin/solc

WORKDIR /app

# Copiar servidor
COPY echidna_server.py .

# Exponer puerto
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8004/health')"

# Arrancar servidor
CMD ["uvicorn", "echidna_server:app", "--host", "0.0.0.0", "--port", "8004"]
