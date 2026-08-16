#!/bin/bash
# ═══════════════════════════════════════════════
# CodeLogic IUP — Túnel Cloudflare
# ═══════════════════════════════════════════════

echo "╔══════════════════════════════════════════╗"
echo "║   CodeLogic IUP — Túnel Cloudflare       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Verificar si cloudflared está instalado
if ! command -v cloudflared &> /dev/null; then
    echo "📥 Instalando cloudflared..."
    
    # Detectar arquitectura
    ARCH=$(dpkg --print-architecture)
    
    if [ "$ARCH" = "amd64" ]; then
        curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    elif [ "$ARCH" = "arm64" ]; then
        curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
    else
        echo "❌ Arquitectura no soportada: $ARCH"
        exit 1
    fi
    
    sudo dpkg -i cloudflared.deb
    rm cloudflared.deb
    echo "✅ cloudflared instalado."
fi

echo ""
echo "🌐 Iniciando túnel rápido (sin cuenta de Cloudflare)..."
echo "   Esto generará una URL pública temporal para tu plataforma."
echo "   La plataforma debe estar corriendo en http://localhost:5000"
echo ""
echo "   Presiona Ctrl+C para detener el túnel."
echo ""

cloudflared tunnel --url http://localhost:5000

# ═══════════════════════════════════════════════
# NOTA: Para un túnel permanente con dominio propio:
# 
# 1. Crea una cuenta en Cloudflare
# 2. cloudflared tunnel login
# 3. cloudflared tunnel create codelogic-iup
# 4. Configura el DNS en tu panel de Cloudflare
# 5. cloudflared tunnel route dns codelogic-iup tu-dominio.com
# 6. cloudflared tunnel run codelogic-iup
#
# Para ejecutar como servicio (inicio automático):
# sudo cloudflared service install
# ═══════════════════════════════════════════════
