import os
import secrets
import sys
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def _bool(name, default="false"):
    """Lee una variable de entorno booleana de forma tolerante."""
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


class Config:
    # ── Modo depuración ──
    # Default FALSE a propósito: si el .env no carga, la app arranca cerrada y
    # no con el depurador de Werkzeug expuesto, que permite ejecutar código.
    FLASK_DEBUG = _bool("FLASK_DEBUG", "false")

    # ── Clave de sesión ──
    # Sin fallback público: firma las cookies, y una clave conocida permite
    # falsificar la sesión de cualquier usuario, incluido admin.
    SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
    if not SECRET_KEY:
        if FLASK_DEBUG:
            SECRET_KEY = secrets.token_hex(32)
            print(
                "⚠️  SECRET_KEY ausente: se generó una efímera para desarrollo.\n"
                "    Las sesiones se invalidan en cada reinicio.",
                file=sys.stderr,
            )
        else:
            raise RuntimeError(
                "SECRET_KEY no está definida en el .env y FLASK_DEBUG es false.\n"
                "Genera una con:  python3 -c 'import secrets; print(secrets.token_hex(32))'"
            )

    # ── Base de datos ──
    # DB_ENGINE: "mysql" (producción Linux) | "sqlite" (desarrollo Windows).
    # SQLite no necesita servidor: crea el archivo instance/codelogic.db.
    DB_ENGINE = os.getenv("DB_ENGINE", "mysql").lower()

    # MySQL/MariaDB
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "pseudocode_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "pseudocode_platform")

    if DB_ENGINE == "sqlite":
        _db_dir = BASE_DIR / "instance"
        _db_dir.mkdir(exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(_db_dir / 'codelogic.db').as_posix()}"
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            "?charset=utf8mb4"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Reciclar conexiones antes del wait_timeout de MariaDB
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_recycle": 280, "pool_pre_ping": True}

    # ── Cookies de sesión ──
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # En producción la app va detrás de Cloudflare Tunnel → siempre HTTPS.
    # En desarrollo local (http://localhost) se desactiva sola, si no, no habría login.
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", "false" if FLASK_DEBUG else "true")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)

    # ── CSRF ──
    # Sin caducidad propia: un estudiante puede tener el editor abierto una hora
    # antes de enviar. El token vive lo que viva la sesión.
    WTF_CSRF_TIME_LIMIT = None

    # ── Límite de tamaño de petición (2 MB) ──
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    # ── Registro de usuarios ──
    # Si tiene valor, hace falta el código para crear cuenta. Evita que
    # cualquiera en internet se registre, queme la cuota de IA y contamine
    # los datos de la investigación (asignación de grupos A/B).
    REGISTRATION_CODE = os.getenv("REGISTRATION_CODE", "").strip()

    # ── Correo (verificación de cuentas) ──
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "CodeLogic IUP")

    # Dominio institucional exigido al registrarse. Vacío = se acepta cualquiera.
    ALLOWED_EMAIL_DOMAIN = os.getenv("ALLOWED_EMAIL_DOMAIN", "").strip().lower().lstrip("@")

    # Base pública para construir los enlaces de verificación. Se usa esta en vez
    # de url_for(_external=True) porque detrás del túnel el host puede variar.
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

    VERIFICATION_TTL_HOURS = int(os.getenv("VERIFICATION_TTL_HOURS", 48))

    # Si no hay SMTP configurado, la verificación se desactiva sola: así la app
    # sigue usable en desarrollo sin dejar a nadie fuera por un correo que
    # nunca llega.
    EMAIL_VERIFICATION_ENABLED = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)

    # ── Rate limiting ──
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_AI = os.getenv("RATELIMIT_AI", "20 per hour;120 per day")
    RATELIMIT_EXEC = os.getenv("RATELIMIT_EXEC", "60 per hour")
    RATELIMIT_AUTH = os.getenv("RATELIMIT_AUTH", "10 per 15 minutes")

    # Gemini (fallback)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # OpenCode Zen (primario — proxy multimodel)
    OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY", "")
    OPENCODE_BASE_URL = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1")
    OPENCODE_MODEL = os.getenv("OPENCODE_MODEL", "deepseek-v4-flash-free")  # fallback default
    # Routing híbrido (basado en benchmark de 2026-05-12):
    #   - convert  → MiniMax: rápido (3-7s), tokens limpios, código sin ruido
    #   - tutor    → DeepSeek: tono pedagógico cálido, mejor para feedback/explain
    OPENCODE_MODEL_CONVERT = os.getenv("OPENCODE_MODEL_CONVERT", "minimax-m2.5-free")
    OPENCODE_MODEL_TUTOR = os.getenv("OPENCODE_MODEL_TUTOR", "deepseek-v4-flash-free")

    # Flask
    # Bind a loopback: el acceso público entra por Cloudflare Tunnel, sin
    # exponer el puerto directamente a la red.
    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
