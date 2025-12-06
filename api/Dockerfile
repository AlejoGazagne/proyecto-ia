FROM python:3.9-slim

# Instalar curl para health checks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copiar e instalar dependencias primero (mejor cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY core/ ./core/
COPY models/ ./models/
COPY services/ ./services/
COPY routes/ ./routes/
COPY main.py .

# Exponer puerto
EXPOSE 8000

# Arrancar servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
