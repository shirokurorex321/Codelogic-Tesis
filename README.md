# ⟨/⟩ CodeLogic IUP

**Plataforma web con conversión de pseudocódigo y retroalimentación con IA**  
Institución Universitaria del Putumayo — Trabajo de Grado 2026

---

## Descripción

CodeLogic IUP es una plataforma web educativa que permite a los estudiantes de primer semestre:

1. **Escribir pseudocódigo** en un editor web interactivo
2. **Convertir automáticamente** a Python, C++ y PHP usando IA (Google Gemini)
3. **Recibir retroalimentación inmediata** sobre errores lógicos y de estructura
4. **Practicar con ejercicios guiados** organizados por tema

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3 + Flask |
| Base de datos | MySQL/MariaDB (producción) o SQLite (desarrollo) |
| IA | OpenCode Zen (primario) + Google Gemini (fallback) |
| Frontend | HTML + CSS + JavaScript |
| Hosting | Linux + Cloudflare Tunnel |

## Instalación en Windows (desarrollo)

```powershell
# 1. Instalar Python (si no está)
winget install -e --id Python.Python.3.13 --scope user

# 2. (Opcional) PHP y C++ para el módulo de ejecución
winget install -e --id PHP.PHP.8.4
winget install -e --id BrechtSanders.WinLibs.POSIX.UCRT

# 3. Arrancar (crea el venv e instala dependencias la primera vez)
run.bat
```

En Windows la app usa **SQLite** automáticamente (`DB_ENGINE=sqlite` en `.env`):
no necesitas instalar MySQL. La base de datos queda en `instance/codelogic.db`.

La ejecución de código corre **sin sandbox** en Windows (solo desarrollo local):
se habilita con `EXECUTOR_ALLOW_UNSAFE=true` en `.env`. **No expongas esta
instancia a internet con túnel**; para eso usa el despliegue Linux con bubblewrap.

## Instalación Rápida (Linux, producción)

```bash
# 1. Clonar o copiar el proyecto
cd pseudocode-platform

# 2. Ejecutar el instalador
chmod +x install.sh setup_db.sh setup_tunnel.sh
bash install.sh
```

El instalador te guiará paso a paso.

## Instalación Manual

```bash
# 1. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus datos (DB y API key de Gemini)

# 4. Configurar MySQL
bash setup_db.sh

# 5. Iniciar la aplicación
python3 app.py
```

## Obtener API Key de Gemini (Gratis)

1. Ve a [Google AI Studio](https://aistudio.google.com/apikey)
2. Inicia sesión con tu cuenta de Google
3. Crea una API key
4. Cópiala en tu archivo `.env` como `GEMINI_API_KEY`

## Exponer con Cloudflare Tunnel

```bash
# En una terminal separada (mientras la app está corriendo):
bash setup_tunnel.sh
```

Esto genera una URL pública temporal como `https://abc123.trycloudflare.com`

## Usuarios por Defecto

| Rol | Correo | Contraseña |
|---|---|---|
| Docente | docente@iup.edu.co | admin123 |

Los estudiantes se registran desde la página principal.

## Estructura del Proyecto

```
pseudocode-platform/
├── app.py                 # Aplicación Flask principal
├── config.py              # Configuración
├── models.py              # Modelos de base de datos
├── gemini_service.py      # Integración con Gemini AI
├── requirements.txt       # Dependencias Python
├── .env.example           # Template de variables de entorno
├── install.sh             # Script de instalación
├── setup_db.sh            # Script de configuración de BD
├── setup_tunnel.sh        # Script de túnel Cloudflare
├── static/
│   ├── css/style.css      # Estilos
│   └── js/app.js          # JavaScript general
└── templates/
    ├── base.html           # Template base
    ├── index.html          # Página de inicio
    ├── login.html          # Inicio de sesión
    ├── register.html       # Registro
    ├── dashboard.html      # Panel del estudiante
    ├── editor.html         # Editor de pseudocódigo
    ├── exercises.html      # Lista de temas
    ├── topic_exercises.html # Ejercicios por tema
    └── admin/
        ├── dashboard.html  # Panel del docente
        ├── exercises.html  # Gestión de ejercicios
        ├── students.html   # Gestión de estudiantes
        └── logs.html       # Logs de actividad
```

## Funcionalidades

### Para Estudiantes
- Editor de pseudocódigo con placeholder de ejemplo
- Conversión a Python, C++ y PHP (individual o simultánea)
- Retroalimentación de IA contextualizada
- Ejercicios organizados por tema y dificultad
- Sistema de pistas
- Seguimiento de progreso

### Para Docentes
- Dashboard con estadísticas
- Crear y gestionar ejercicios
- Asignar estudiantes a grupos experimentales (A/B)
- Exportar logs de actividad en JSON para R/SPSS
- Ver actividad de estudiantes

### Para la Investigación
- Registro automático de toda la actividad (logs)
- Almacenamiento de pretest/postest
- Escalas de autoeficacia
- Métricas: intentos, tiempo, errores, retroalimentaciones consultadas
- Exportación de datos para análisis estadístico

---

**Autores:** Daniel Alejandro Rosero Gómez & Brayan Aldahir Torres Yandul  
**Asesor:** Jhoni Ricardo Cerón Chaves  
**Institución Universitaria del Putumayo — 2026**
