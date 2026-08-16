#!/bin/bash
# ═══════════════════════════════════════════════
# CodeLogic IUP — Script de configuración de BD
# ═══════════════════════════════════════════════

echo "╔══════════════════════════════════════════╗"
echo "║   CodeLogic IUP — Configuración de BD    ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Verificar que MySQL/MariaDB está instalado
if ! command -v mysql &> /dev/null; then
    echo "⚠️  MySQL/MariaDB no está instalado."
    echo "   Instalando MariaDB..."
    sudo apt update
    sudo apt install -y mariadb-server mariadb-client
    sudo systemctl start mariadb
    sudo systemctl enable mariadb
    echo "✅ MariaDB instalado y en ejecución."
fi

echo ""
echo "📦 Creando base de datos y usuario..."
echo "   (Se te pedirá la contraseña de root de MySQL)"
echo ""

# Contraseña para el usuario de la app
read -sp "Ingresa la contraseña para el usuario 'pseudocode_user': " DB_PASS
echo ""

# Crear BD y usuario
sudo mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS pseudocode_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'pseudocode_user'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON pseudocode_platform.* TO 'pseudocode_user'@'localhost';
FLUSH PRIVILEGES;
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Base de datos 'pseudocode_platform' creada."
    echo "✅ Usuario 'pseudocode_user' configurado."
    echo ""
    echo "📝 Ahora actualiza tu archivo .env con estos datos:"
    echo "   DB_HOST=localhost"
    echo "   DB_PORT=3306"
    echo "   DB_USER=pseudocode_user"
    echo "   DB_PASSWORD=${DB_PASS}"
    echo "   DB_NAME=pseudocode_platform"
else
    echo "❌ Error al crear la base de datos. Verifica tu instalación de MySQL."
fi
