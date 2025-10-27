#!/bin/bash

# Aplicar migraciones
echo "Aplicando migraciones..."
python manage.py migrate --noinput

# Recolectar archivos estáticos
echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Iniciar gunicorn
echo "Iniciando servidor..."
exec gunicorn --bind 0.0.0.0:8000 \
    --timeout 120 \
    --workers 2 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    core.wsgi:application