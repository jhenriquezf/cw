# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/static /app/staticfiles /app/media

# Dar permisos al entrypoint
RUN chmod +x entrypoint.sh

EXPOSE 8000

# Usar el entrypoint
ENTRYPOINT ["./entrypoint.sh"]