#!/bin/bash
# ═══════════════════════════════════════════════
# CodeLogic IUP — Instalación completa
# ═══════════════════════════════════════════════

echo ""
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║                                              ║"
echo "  ║      ⟨/⟩  CodeLogic IUP                     ║"
echo "  ║      Plataforma de Aprendizaje               ║"
echo "  ║      de Programación                         ║"
echo "  ║                                              ║"
echo "  ║      Institución Universitaria               ║"
echo "  ║      del Putumayo                            ║"
echo "  ║                                              ║"
echo "  ╚══════════════════════════════════════════════╝"
echo ""

# ─── 1. DEPENDENCIAS DEL SISTEMA ───────────────
echo "1️⃣  Verificando dependencias del sistema..."

sudo apt update -qq

# Python
if ! command -v python3 &> /dev/null; then
    echo "   Instalando Python3..."
    sudo apt install -y python3 python3-pip python3-venv
fi
echo "   ✅ Python3: $(python3 --version)"

# ─── 2. ENTORNO VIRTUAL ────────────────────────
echo ""
echo "2️⃣  Configurando entorno virtual de Python..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ Entorno virtual creado."
fi

source venv/bin/activate
echo "   ✅ Entorno virtual activado."

# ─── 3. DEPENDENCIAS DE PYTHON ─────────────────
echo ""
echo "3️⃣  Instalando dependencias de Python..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "   ✅ Dependencias instaladas."

# ─── 4. ARCHIVO .ENV ───────────────────────────
echo ""
echo "4️⃣  Configurando variables de entorno..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    
    # Generar clave secreta
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/cambia-esto-por-una-clave-segura/$SECRET/" .env
    
    echo "   ✅ Archivo .env creado."
    echo ""
    echo "   ⚠️  IMPORTANTE: Edita el archivo .env con tus datos:"
    echo "   - DB_PASSWORD: Contraseña de tu usuario MySQL"
    echo "   - GEMINI_API_KEY: Tu API key de Google Gemini"
    echo ""
    echo "   Para obtener la API key de Gemini (gratis):"
    echo "   → https://aistudio.google.com/apikey"
    echo ""
    read -p "   ¿Quieres editar .env ahora? (s/n): " EDIT_ENV
    if [ "$EDIT_ENV" = "s" ] || [ "$EDIT_ENV" = "S" ]; then
        nano .env
    fi
else
    echo "   ✅ Archivo .env ya existe."
fi

# ─── 5. BASE DE DATOS ──────────────────────────
echo ""
echo "5️⃣  Configurando base de datos..."
read -p "   ¿Configurar MySQL/MariaDB ahora? (s/n): " SETUP_DB
if [ "$SETUP_DB" = "s" ] || [ "$SETUP_DB" = "S" ]; then
    bash setup_db.sh
fi

# ─── 6. INICIAR APLICACIÓN ─────────────────────
echo ""
echo "6️⃣  Iniciando la aplicación..."
echo ""
echo "   La plataforma estará disponible en:"
echo "   → http://localhost:5000"
echo ""
echo "   Cuenta docente: la de ADMIN_EMAIL en el .env (por defecto docente@iup.edu.co)."
echo "   Su contraseña es ADMIN_PASSWORD; si está vacía, la app genera una y la muestra una sola vez."
echo ""
echo "   Para exponer con Cloudflare (en otra terminal):"
echo "   → bash setup_tunnel.sh"
echo ""
echo "   Presiona Ctrl+C para detener el servidor."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 app.py
