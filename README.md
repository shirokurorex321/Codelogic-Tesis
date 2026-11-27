# CodeLogic IUP

Plataforma web para el aprendizaje introductorio de programación. Los estudiantes escriben algoritmos en
pseudocódigo y la plataforma los revisa, muestra su prueba de escritorio y su diagrama de flujo, los convierte a
Python, C++ y PHP y da retroalimentación con inteligencia artificial. El docente sigue el avance de la clase y
administra los ejercicios.

Trabajo de grado de Daniel Alejandro Rosero Gómez y Brayan Aldahir Torres Yandul, programa de Ingeniería de Sistemas,
Institución Universitaria del Putumayo, 2026. Asesor: Jhoni Ricardo Cerón Chaves.

## Documentación

- [Manual de usuario](docs/Manual-de-usuario-CodeLogic.pdf): uso de la plataforma por estudiantes, docentes y
  administradores.
- [Manual del programador](docs/Manual-del-programador-CodeLogic.pdf): arquitectura, instalación, configuración,
  base de datos, rutas, despliegue, respaldos, seguridad y mantenimiento.
- [Manual de instalación](docs/Manual-de-instalacion-CodeLogic.pdf): instalación paso a paso en un servidor Linux,
  publicación con HTTPS, respaldos, actualización e instalación para desarrollo.
- [Carta de autorización de publicación](<docs/entrega/Carta de autorización de publicación.pdf>) y
  [formato F-INV-050 de entrega de la tesis](<docs/entrega/F-INV-050 Entrega tesis de grado.pdf>): formatos
  institucionales de la entrega del trabajo de grado, en Word y PDF, en la carpeta `docs/entrega`.

## Tecnologías

| Componente | Tecnología |
|---|---|
| Aplicación | Python 3 y Flask, servida con Gunicorn |
| Base de datos | MariaDB en producción; SQLite para desarrollo |
| Inteligencia artificial | API de Google Gemini, con caché de respuestas |
| Ejecución de código | Entorno aislado con bubblewrap (Python, C++ y PHP) |
| Interfaz | Plantillas Jinja2, CSS y JavaScript; diagramas con Mermaid |
| Publicación | Servidor propio con Ubuntu Server y túnel de Cloudflare |

## Instalación para desarrollo

```bash
sudo apt install -y python3 python3-venv git bubblewrap g++ php-cli
git clone https://github.com/shirokurorex321/Codelogic-Tesis.git codelogic
cd codelogic
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env          # completar: SECRET_KEY, DB_ENGINE=sqlite, SESSION_COOKIE_SECURE=false,
                              # ADMIN_EMAIL y ADMIN_PASSWORD
venv/bin/python -c "import app"        # crea las tablas, la semilla y la cuenta docente
venv/bin/python importar_contenido.py   # carga los 12 temas y 62 ejercicios del curso de 2026
venv/bin/python app.py                  # http://127.0.0.1:5000
```

Sin `GEMINI_API_KEY` la plataforma funciona y las funciones de inteligencia artificial avisan que no están
disponibles. La instalación en producción (MariaDB, systemd, túnel y respaldos) está en el manual de instalación y
en la carpeta `despliegue/`.

## Estructura

| Archivo o carpeta | Contenido |
|---|---|
| `app.py` | Aplicación Flask: rutas, seguridad, reglas de acceso y semillas iniciales |
| `config.py` | Configuración leída del `.env` |
| `models.py` | Modelo de datos (11 tablas) |
| `gemini_service.py` | Conversión, diagramas, retroalimentación y calificación con IA; caché y costos |
| `revisar.py`, `alcance.py` | Revisor de sintaxis y alcance del ejercicio, sin IA |
| `traza.py`, `a_pseudo.py` | Prueba de escritorio y su traducción a las líneas del pseudocódigo |
| `executor.py` | Ejecución en el entorno aislado |
| `seguimiento.py` | Panel del docente |
| `lecciones.py`, `questions.py` | Lecciones e instrumentos del estudio |
| `importar_contenido.py`, `datos/` | Contenido del curso para una instalación nueva |
| `templates/`, `static/` | Páginas, estilos y JavaScript |
| `despliegue/` | Unidades de systemd y guiones de respaldo del servidor |

## Datos y secretos

El archivo `.env`, con las claves de la base, de la API y del correo, nunca entra al repositorio (`.gitignore`).
El repositorio no contiene datos de estudiantes: `datos/contenido_curso.json` solo tiene los temas y los ejercicios.
