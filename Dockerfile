FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del proyecto
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/static /app/staticfiles /app/media

# Dar permisos de ejecución al entrypoint
RUN chmod +x entrypoint.sh

# Exponer puerto
EXPOSE 8000

# Usar el script de inicio
ENTRYPOINT ["./entrypoint.sh"]