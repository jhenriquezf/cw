#!/bin/bash

echo "======================================"
echo "Setup inicial del servidor"
echo "======================================"

# Actualizar sistema
sudo apt update
sudo apt upgrade -y

# Instalar Docker si no está
if ! command -v docker &> /dev/null; then
    echo "Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker instalado. Cierra y vuelve a entrar para aplicar cambios."
fi

# Crear directorios
mkdir -p ~/media
touch ~/db.sqlite3

# Instalar Caddy
echo "Instalando Caddy..."
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy

# Configurar Caddy
echo "Configurando Caddy..."
echo "cw.cloud8.cl {
    reverse_proxy localhost:8000
    encode gzip
    
    log {
        output file /var/log/caddy/access.log
    }
}" | sudo tee /etc/caddy/Caddyfile

# Habilitar e iniciar Caddy
sudo systemctl enable caddy
sudo systemctl start caddy

# Configurar firewall si es necesario
echo "Configurando firewall..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable || true

echo ""
echo "======================================"
echo "✅ Setup completado"
echo "======================================"
echo ""
echo "Ahora puedes hacer git push y el deploy será automático."
echo "Tu app estará en: https://cw.cloud8.cl"
```

---

## 🚀 PASOS PARA IMPLEMENTAR

### **Paso 1: Configurar Cloudflare (DNS Only)**

En **Cloudflare** → **DNS**:
```
Type: A
Name: cw
Content: 34.42.211.110
Proxy: GRIS (DNS only) ← IMPORTANTE