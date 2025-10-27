#!/bin/bash

# Salir si hay errores
set -e

echo "======================================"
echo "Iniciando aplicación Django..."
echo "======================================"

# Aplicar migraciones
echo "→ Aplicando migraciones de base de datos..."
python manage.py migrate --noinput

# Recolectar archivos estáticos
echo "→ Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# Crear superusuario si no existe (opcional)
# echo "→ Creando superusuario..."
# python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"

echo "→ Iniciando servidor Gunicorn..."
echo "======================================"

# Iniciar Gunicorn
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    core.wsgi:application
```

---

## 4️⃣ `.dockerignore`
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv/

# Django
*.log
db.sqlite3
db.sqlite3-journal
/media
/staticfiles
*.pot

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Git
.git
.gitignore
.gitattributes

# Docker
Dockerfile
docker-compose.yml
.dockerignore

# CI/CD
.github/
.gitlab-ci.yml

# Environment
.env
.env.local
*.env

# Documentation
README.md
docs/

# Tests
.pytest_cache/
.coverage
htmlcov/