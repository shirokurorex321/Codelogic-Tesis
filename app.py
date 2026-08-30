import os
import re
import logging
import secrets
from zoneinfo import ZoneInfo
import sys

# Consolas de Windows con cp1252 revientan con los emojis de los prints
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime, timezone, timedelta
import unicodedata
from sqlalchemy import func
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, current_app
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_limiter import Limiter
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from models import (
    db, User, Topic, Exercise, Submission,
    ActivityLog, TestResult, SelfEfficacyResult, CognitiveLoadResult, GastoIA
)
from gemini_service import (
    convert_pseudocode, get_ai_feedback, convert_to_all_languages,
    explain_code, grade_submission,
    convert_to_diagram,
)
from questions import (
    TEST_QUESTIONS, SELF_EFFICACY_ITEMS, LIKERT_LABELS,
    COGNITIVE_LOAD_ITEMS, COGNITIVE_LOAD_LABELS,
)
import executor
import traza

# Versión del texto de consentimiento informado. Súbela si cambias el texto:
# permite demostrar qué versión aceptó cada participante.
CONSENT_VERSION = "1.0-2026-07"

# ─── CREAR APP ──────────────────────────────────────────────────────

app = Flask(__name__)
app.config.from_object(Config)

# Detrás de Cloudflare Tunnel, cloudflared se conecta desde 127.0.0.1. Sin esto,
# request.remote_addr sería siempre "127.0.0.1" y url_for(_external=True)
# generaría http:// en vez de https://.
# Confiar en estas cabeceras solo es seguro porque la app escucha en loopback
# y únicamente cloudflared puede alcanzarla.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

db.init_app(app)

csrf = CSRFProtect(app)

# ─── CABECERAS DE SEGURIDAD ─────────────────────────────────────────
#
# Anade las cabeceras con las que el navegador se defiende solo: CSP, HSTS,
# X-Frame-Options, X-Content-Type-Options, Referrer-Policy y Permissions-Policy.
# Antes de esto el sitio no enviaba ninguna.
#
# La CSP arranca en modo SOLO INFORME a proposito. Las plantillas tienen 145
# atributos style= y 9 manejadores onclick= en linea; una politica estricta los
# bloquearia y romperia la interfaz. En modo informe el navegador no bloquea
# nada, solo avisa por consola, y permite ver que se rompería antes de
# aplicarla en firme.
#
# Lo que SI se aplica desde ya: HSTS, X-Frame-Options, X-Content-Type-Options,
# Referrer-Policy y Permissions-Policy, que no dependen del contenido.
#
# force_https queda en False porque la app escucha en loopback y quien termina
# el HTTPS es Cloudflare. Si Talisman redirigiera aqui, se formaria un bucle.

CSP = {
    "default-src": "'self'",
    # 'unsafe-inline' es necesario mientras existan los onclick= de las
    # plantillas. Quitarlos y pasar a addEventListener permitiria eliminarlo,
    # que es la mejora de seguridad real pendiente.
    "script-src": ["'self'", "'unsafe-inline'"],
    "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
    "font-src": ["'self'", "https://fonts.gstatic.com", "data:"],
    "img-src": ["'self'", "data:"],
    "connect-src": "'self'",
    "frame-ancestors": "'none'",
    "base-uri": "'self'",
    "form-action": "'self'",
    "object-src": "'none'",
}

Talisman(
    app,
    force_https=False,
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,
    strict_transport_security_include_subdomains=False,
    strict_transport_security_preload=False,
    session_cookie_secure=app.config.get("SESSION_COOKIE_SECURE", True),
    session_cookie_http_only=True,
    content_security_policy=CSP,
    # En modo informe desde el 7 de agosto: 152 paginas servidas y la unica
    # violacion registrada (77 veces) fue el beacon de analitica que
    # Cloudflare inyecta en el borde, que no es parte de la aplicacion.
    # Cero violaciones propias, asi que pasa a bloquear de verdad.
    content_security_policy_report_only=False,
    # Talisman exige un destino cuando la politica va en modo informe. El
    # navegador envia ahi cada violacion que la CSP habria bloqueado, lo que
    # permite ver exactamente que romperia antes de aplicarla en firme.
    content_security_policy_report_uri="/csp-report",
    frame_options="DENY",
    x_content_type_options=True,
    referrer_policy="strict-origin-when-cross-origin",
    permissions_policy={
        "geolocation": "()",
        "microphone": "()",
        "camera": "()",
        "payment": "()",
        "usb": "()",
    },
)


limiter = Limiter(
    key_func=lambda: (
        f"user:{current_user.id}" if current_user.is_authenticated else f"ip:{client_ip()}"
    ),
    app=app,
    storage_uri=app.config["RATELIMIT_STORAGE_URI"],
    strategy="fixed-window",
)
@app.route("/csp-report", methods=["POST"])
@csrf.exempt          # lo envia el navegador, no un formulario nuestro
@limiter.exempt       # un fallo de CSP no debe gastar cuota de peticiones
def csp_report():
    """Recibe los avisos de la politica de seguridad de contenido.

    Solo registra. Sirve para saber que recursos bloquearia la CSP antes de
    pasarla de modo informe a modo bloqueo.
    """
    try:
        datos = request.get_json(force=True, silent=True) or {}
        aviso = datos.get("csp-report", datos)
        app.logger.warning(
            "CSP: se bloquearia %s (directiva %s) en %s",
            aviso.get("blocked-uri", "?"),
            aviso.get("violated-directive", "?"),
            aviso.get("document-uri", "?"),
        )
    except Exception:
        pass
    return "", 204


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Inicia sesión para acceder a la plataforma."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ─── HELPERS ────────────────────────────────────────────────────────

def client_ip():
    """IP real del estudiante.

    Detrás de Cloudflare Tunnel la conexión llega desde cloudflared (127.0.0.1),
    así que remote_addr no sirve. Cloudflare pone la IP original en
    CF-Connecting-IP; ProxyFix ya resuelve X-Forwarded-For como respaldo.
    """
    return request.headers.get("CF-Connecting-IP") or request.remote_addr


# "diagram" faltaba: consume tokens igual que las demas y se quedaba fuera
# del libro de gasto desde que se añadio la funcion, el 26/08/2026.
# Unica lista de operaciones de IA. Antes estaba repetida en tres sitios y al
# anadir "diagram" solo se actualizo uno: el contador que ve el estudiante y
# las estadisticas del docente llevaban desde entonces sin contar ni un solo
# diagrama, que es de las operaciones que mas cuesta. Cualquier operacion
# nueva se anade AQUI y solo aqui.
OPERACIONES_IA = ("convert", "feedback", "explain", "grade", "diagram")

# Las que ademas se anotan en el libro de gasto (hoy, todas).
OPERACIONES_CON_COSTE = OPERACIONES_IA


def registrar_gasto(action, details, user_id):
    """Anota en el libro de gasto lo que costo una llamada a la IA.

    Va aparte de ActivityLog porque aquel se borra en cascada al borrar una
    cuenta y el gasto tiene que sobrevivir a la baja del alumno. Nunca puede
    tumbar la peticion: si falla, se pierde la linea y no la respuesta.
    """
    if action not in OPERACIONES_CON_COSTE or not isinstance(details, dict):
        return
    # Lo servido desde cache no se pago y no debe anotarse. Hay que mirar el
    # indicador "cached", NO si vienen tokens: la cache guarda la respuesta
    # entera, usage incluido, asi que una respuesta cacheada trae los tokens
    # de la llamada original y colarse por aqui inflaba el gasto y ademas
    # gastaba cupo al alumno que reenviaba el mismo pseudocodigo.
    if details.get("cached"):
        return
    usage = details.get("usage") or {}
    if not usage.get("total_tokens"):
        return          # sin consumo: no hay nada que cobrar
    try:
        from gemini_service import coste_usd, salida_facturable
        db.session.add(GastoIA(
            user_id=user_id,
            operacion=action,
            proveedor=usage.get("provider"),
            modelo=usage.get("model"),
            tokens_entrada=int(usage.get("prompt_tokens") or 0),
            tokens_salida=salida_facturable(usage),
            coste_usd=round(coste_usd(usage), 8),
            desde_cache=False,   # si llega aqui, no vino de cache
            exercise_id=details.get("exercise_id"),
        ))
    except Exception:
        current_app.logger.warning("no se pudo registrar el gasto de %s", action,
                                   exc_info=True)


def feedback_gastadas(user_id, exercise_id):
    """Retroalimentaciones DE PAGO que lleva este alumno en este ejercicio.

    Se cuenta sobre gasto_ia y no sobre activity_logs a proposito: ahi solo
    entra lo que realmente se facturo, asi que lo servido desde cache no
    descuenta cupo. Es la misma pregunta que responde el libro de gasto
    ("cuanto me ha costado este alumno en este ejercicio"), expresada en
    numero de llamadas.
    """
    if not exercise_id:
        return 0
    return GastoIA.query.filter_by(user_id=user_id, operacion="feedback",
                                   exercise_id=exercise_id).count()


def feedback_cupo(user, exercise_id):
    """(quedan, tope). quedan=None significa sin limite."""
    tope = app.config.get("FEEDBACK_MAX_POR_EJERCICIO", 0)
    if not tope or not exercise_id or user.role in ("docente", "admin"):
        return None, tope
    return max(tope - feedback_gastadas(user.id, exercise_id), 0), tope


def log_activity(action, details=None):
    """Registra actividad del usuario para la investigación."""
    if current_user.is_authenticated:
        log = ActivityLog(
            user_id=current_user.id,
            action=action,
            details=details,
            ip_address=client_ip()
        )
        db.session.add(log)
        registrar_gasto(action, details, current_user.id)
        db.session.commit()


def log_activity_para(user, action, details=None):
    """Igual que log_activity pero para un usuario que aún no inició sesión
    (por ejemplo mientras espera verificar su correo)."""
    try:
        db.session.add(ActivityLog(
            user_id=user.id, action=action, details=details, ip_address=client_ip()
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()


RESET_TTL_MINUTOS = 60


def _enviar_restablecimiento(user) -> bool:
    """Genera un token de un solo uso y envía el correo para cambiar la clave."""
    from mailer import correo_restablecer

    ahora = datetime.now(timezone.utc)
    user.reset_token = secrets.token_urlsafe(32)
    user.reset_sent_at = ahora
    user.reset_expires_at = ahora + timedelta(minutes=RESET_TTL_MINUTOS)
    db.session.commit()

    base = app.config.get("PUBLIC_BASE_URL") or request.url_root.rstrip("/")
    enlace = f"{base}/restablecer-clave/{user.reset_token}"
    return correo_restablecer(user.name, user.email, enlace, RESET_TTL_MINUTOS)


# El envio de correo registra los fallos como ERROR (se ven) pero los exitos
# como INFO, y nadie sube el nivel: por defecto es WARNING, asi que no quedaba
# ni rastro de los correos que SI salieron. Durante el pilotaje hace falta
# poder decir "a este estudiante se le mando el enlace tal dia a tal hora"
# cuando llame diciendo que no le llega nada.
# Subir el nivel no basta: el logger raiz no tiene ningun manejador, asi que
# Python cae en el "de ultimo recurso", que solo emite WARNING o mas. Hay que
# darle su propia salida a stderr, que es lo que gunicorn captura al registro
# del servicio (--capture-output).
_log_correo = logging.getLogger("mailer")
_log_correo.setLevel(logging.INFO)
if not _log_correo.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[correo] %(levelname)s %(message)s"))
    _log_correo.addHandler(_h)


def _enviar_verificacion(user) -> bool:
    """Genera un token nuevo y manda el correo de confirmación."""
    from mailer import correo_verificacion

    horas = int(app.config.get("VERIFICATION_TTL_HOURS", 48))
    ahora = datetime.now(timezone.utc)

    user.verification_token = secrets.token_urlsafe(32)
    user.verification_sent_at = ahora
    user.verification_expires_at = ahora + timedelta(hours=horas)
    db.session.commit()

    base = app.config.get("PUBLIC_BASE_URL") or request.url_root.rstrip("/")
    enlace = f"{base}/verificar/{user.verification_token}"
    # Se espera al envio en vez de lanzarlo a un hilo. Con el hilo, `enviar`
    # devolvia True siempre y nadie sabia si el correo habia salido: el
    # estudiante se quedaba mirando "revisa tu bandeja" para siempre y el
    # fallo solo aparecia en un registro que nadie mira. Registrarse es una
    # accion unica; esperar dos segundos no molesta a nadie.
    return correo_verificacion(user.name, user.email, enlace, horas,
                               en_segundo_plano=False)


@app.errorhandler(429)
def ratelimit_handler(e):
    """Las rutas /api/ responden JSON; el resto, un mensaje en pantalla."""
    if request.path.startswith("/api/"):
        return jsonify({
            "error": "Has superado el límite de solicitudes. Espera un momento "
                     "antes de volver a intentarlo.",
            "retry_after": getattr(e, "description", None),
        }), 429
    # Ojo con los bucles: si aquí se redirige a /dashboard, un usuario anónimo
    # limitado en /login entra en ciclo (dashboard exige login → login sigue
    # limitado → dashboard...). Se responde 429 con una página propia, que
    # además es lo correcto según HTTP.
    return render_template("limite.html"), 429


# Palabras que delatan pseudocódigo de verdad (estilo PSeInt).
_CLAVES_PSEUDO = {
    "algoritmo", "finalgoritmo", "proceso", "finproceso",
    "definir", "como", "dimension",
    "leer", "escribir", "imprimir", "mostrar",
    "si", "entonces", "sino", "finsi",
    "para", "hasta", "hacer", "finpara", "paso",
    "mientras", "finmientras", "repetir",
    "segun", "finsegun", "entero", "real", "cadena", "logico", "caracter",
}

# Mínimos para considerar que el estudiante escribió un algoritmo y no una frase
_MIN_LINEAS = 3
_MIN_CLAVES = 2


def validar_pseudocodigo(texto: str):
    """Comprueba que el texto sea pseudocódigo y no lenguaje natural.

    Sin esto, escribir "suma dos números" bastaba para que la IA devolviera un
    programa completo. Eso convierte la plataforma en un generador de código y
    rompe la premisa del estudio: el estudiante debe construir la lógica, no
    pedirla. Además contaminaría los resultados, porque el postest mediría el
    uso de una IA y no el aprendizaje de programación.

    Es deliberadamente tolerante: acepta pseudocódigo con errores (son
    principiantes) y solo rechaza lo que claramente es prosa.

    Devuelve (True, None) si pasa, o (False, mensaje) si no.
    """
    if not texto or not texto.strip():
        return False, "Escribe tu algoritmo en pseudocódigo antes de convertir."

    lineas = [l for l in texto.strip().split("\n") if l.strip()]
    bajo = texto.lower()
    claves = {k for k in _CLAVES_PSEUDO if re.search(rf"\b{k}\b", bajo)}

    if len(lineas) < _MIN_LINEAS or len(claves) < _MIN_CLAVES:
        # Se distinguen dos fallos que antes compartian mensaje. Quien escribe
        # `Escribir "Hola Mundo"` SI esta escribiendo pseudocodigo, solo que
        # corto: decirle que "parece una descripcion en espanol" es falso y
        # desconcierta justo en el primer ejercicio del curso. Los verbos de
        # abajo son los que la prosa no usa para empezar una linea ("si" y
        # "para" quedan fuera a proposito: son palabras corrientes).
        VERBOS = ("leer", "escribir", "imprimir", "mostrar", "definir",
                  "algoritmo", "finalgoritmo", "proceso", "finproceso",
                  "inicio", "fin", "dimension")
        estructura = any(
            l.strip().lower().split()[0].strip(":;") in VERBOS
            for l in lineas if l.strip()
        ) or ("<-" in texto)

        if estructura:
            return False, (
                "Vas bien, pero tu algoritmo está incompleto: aún es muy corto "
                "para poder traducirlo.\n\n"
                "Un algoritmo necesita al menos abrirse, hacer algo y cerrarse. "
                "Por ejemplo:\n\n"
                "Algoritmo MiPrograma\n"
                "    Escribir \"Hola Mundo\"\n"
                "FinAlgoritmo\n\n"
                "Añade las líneas que te falten y vuelve a intentarlo."
            )

        return False, (
            "Eso parece una descripción en español, no pseudocódigo. "
            "La plataforma traduce algoritmos que TÚ escribes: ahí está el "
            "aprendizaje.\n\n"
            "Un algoritmo se ve así:\n\n"
            "Algoritmo SumaDeDosNumeros\n"
            "    Definir a, b, suma Como Entero\n"
            "    Escribir \"Primer numero:\"\n"
            "    Leer a\n"
            "    Escribir \"Segundo numero:\"\n"
            "    Leer b\n"
            "    suma <- a + b\n"
            "    Escribir \"La suma es: \", suma\n"
            "FinAlgoritmo\n\n"
            "Si no sabes por dónde empezar, revisa la lección del tema o abre "
            "las ayudas del ejercicio."
        )

    return True, None


@app.context_processor
def inyectar_version_css():
    """Versión del CSS basada en su fecha de modificación.

    Sin esto el navegador sirve la hoja de estilos en caché y los cambios de
    diseño no se ven hasta forzar una recarga completa.
    """
    import os
    try:
        ruta = os.path.join(app.static_folder, "css", "style.css")
        return {"css_version": int(os.path.getmtime(ruta))}
    except Exception:
        return {"css_version": 0}


# Las fechas se guardan en UTC (el servidor corre en UTC) pero quien las lee
# esta en Colombia, cinco horas por detras. Sin convertir, un estudiante que
# entrega a las 11:44 ve "16:44" en su panel, y en el pilotaje eso confunde
# tambien a quien analiza los registros.
_ZONA = ZoneInfo("America/Bogota")


@app.template_filter("hora_local")
def _hora_local(dt, formato="%d/%m/%Y %H:%M"):
    """Pasa una fecha guardada en UTC a la hora de Colombia."""
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_ZONA).strftime(formato)


@app.template_filter("parrafos")
def filtro_parrafos(texto):
    """Convierte texto plano en HTML estructurado.

    Depender de `white-space: pre-wrap` es frágil: basta con que el CSS llegue
    en caché o lo pise otra regla para que todo se vea como un bloque corrido.
    Aquí se generan párrafos y listas de verdad.

    Reglas: línea en blanco = párrafo nuevo; línea que empieza por • o - = ítem
    de lista; una línea indentada bajo otra = explicación de esa línea.
    """
    from markupsafe import Markup, escape
    if not texto:
        return ""

    bloques = []
    lista = []

    def cerrar_lista():
        if lista:
            items = "".join(f"<li>{escape(x)}</li>" for x in lista)
            bloques.append(f"<ul class=\"lec-lista\">{items}</ul>")
            lista.clear()

    for crudo in str(texto).replace("\r\n", "\n").split("\n\n"):
        parrafo = crudo.strip("\n")
        if not parrafo.strip():
            continue

        lineas = parrafo.split("\n")
        # ¿es un bloque de viñetas?
        if all(l.strip().startswith(("•", "-", "*")) or l.startswith((" ", "\t"))
               for l in lineas if l.strip()):
            actual = ""
            for l in lineas:
                t = l.strip()
                if not t:
                    continue
                if t.startswith(("•", "-", "*")):
                    if actual:
                        lista.append(actual)
                    actual = t.lstrip("•-* ").strip()
                else:
                    actual += " " + t          # continuación de la viñeta
            if actual:
                lista.append(actual)
            cerrar_lista()
            continue

        cerrar_lista()
        # ¿cabecera con líneas indentadas debajo? (ej: código + su explicación)
        if len(lineas) > 1 and lineas[0].strip() and lineas[1].startswith((" ", "\t")):
            cab = escape(lineas[0].strip())
            cuerpo = " ".join(l.strip() for l in lineas[1:] if l.strip())
            bloques.append(
                f'<div class="lec-item"><code class="lec-clave">{cab}</code>'
                f'<span class="lec-desc">{escape(cuerpo)}</span></div>')
        else:
            texto_p = " ".join(l.strip() for l in lineas if l.strip())
            bloques.append(f"<p>{escape(texto_p)}</p>")

    cerrar_lista()
    return Markup("".join(bloques))


def role_required(*roles):
    """Decorador para restringir acceso por rol."""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("login"))
            if current_user.role not in roles:
                flash("No tienes permiso para acceder a esta sección.", "error")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ─── RUTAS PÚBLICAS ────────────────────────────────────────────────

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
# methods=["POST"]: antes el limite contaba tambien los GET, asi que ABRIR la
# pagina gastaba cupo. En un aula, donde los 40 estudiantes salen por la misma
# IP de la institucion, el undecimo ya no podia ni ver el formulario: recibia
# un 429 crudo. Mirar la pagina ahora es gratis; solo se cuentan los intentos.
@limiter.limit(lambda: app.config["RATELIMIT_AUTH"], methods=["POST"])
# Y este limita por CORREO, no por IP: es el que de verdad frena a quien
# intenta adivinar la contrasena de una cuenta concreta. Separarlos permite
# ser generoso con el aula sin aflojar la proteccion de cada cuenta.
@limiter.limit("8 per 15 minutes", methods=["POST"],
               key_func=lambda: "correo:" + (request.form.get("email") or "").strip().lower())
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # Cuenta creada pero sin confirmar el correo: no se deja entrar.
            # Es lo que impide que alguien invente direcciones @itp.edu.co.
            if not user.email_verified and app.config.get("EMAIL_VERIFICATION_ENABLED"):
                log_activity_para(user, "login_bloqueado_sin_verificar")
                flash("Tu cuenta aún no está confirmada. Revisa tu correo "
                      "institucional y abre el enlace que te enviamos.", "error")
                return redirect(url_for("verificacion_pendiente"))

            login_user(user, remember=True)
            log_activity("login")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))
        else:
            flash("Correo o contraseña incorrectos.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
# Solo los envios, por lo mismo que en el acceso. El registro ya esta cerrado
# con el codigo de acceso y el dominio institucional obligatorio, asi que el
# limite por IP aqui es la tercera barrera, no la primera.
@limiter.limit(lambda: app.config["RATELIMIT_AUTH"], methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Código de acceso: si está configurado, sin él no hay registro.
        # Impide que cualquiera en internet cree cuenta, consuma la cuota de IA
        # y contamine los datos de la investigación (asignación de grupos A/B).
        expected_code = app.config.get("REGISTRATION_CODE", "")
        if expected_code:
            given_code = request.form.get("registration_code", "").strip()
            if not secrets.compare_digest(given_code, expected_code):
                flash("El código de acceso no es válido. Pídelo a tu docente.", "error")
                return render_template("register.html")

        # Validaciones
        if not all([name, email, password]):
            flash("Todos los campos son obligatorios.", "error")
            return render_template("register.html")

        if password != confirm:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template("register.html")

        # Solo correos institucionales. Junto con la verificación por correo,
        # esto garantiza que quien se registra es estudiante real de la IUP y
        # no alguien inventando direcciones.
        dominio = app.config.get("ALLOWED_EMAIL_DOMAIN", "")
        if dominio and not email.endswith("@" + dominio):
            flash(f"Debes registrarte con tu correo institucional (@{dominio}).", "error")
            return render_template("register.html")

        existente = User.query.filter_by(email=email).first()
        if existente:
            # Si la cuenta existe pero nunca se verificó, se reenvía el correo
            # en vez de dejar el correo bloqueado para siempre.
            if not existente.email_verified and app.config.get("EMAIL_VERIFICATION_ENABLED"):
                _enviar_verificacion(existente)
                flash("Ya habías empezado el registro con ese correo. "
                      "Te reenviamos el enlace de confirmación.", "info")
                return redirect(url_for("verificacion_pendiente"))
            flash("Ya existe una cuenta con ese correo.", "error")
            return render_template("register.html")

        # Consentimiento informado: obligatorio antes de recoger ningún dato.
        # Ley 1581/2012 y Decreto 1377/2013 (datos personales) + Resolución
        # 8430/1993 (investigación con seres humanos).
        if not request.form.get("consent"):
            flash("Debes aceptar el consentimiento informado para crear la cuenta.", "error")
            return render_template("register.html")

        user = User(name=name, email=email, role="estudiante")
        user.set_password(password)
        user.consent_accepted = True
        user.consent_at = datetime.now(timezone.utc)
        user.consent_version = CONSENT_VERSION

        verificar = bool(app.config.get("EMAIL_VERIFICATION_ENABLED"))
        user.email_verified = not verificar     # sin SMTP no se bloquea a nadie
        if not verificar:
            user.verified_at = datetime.now(timezone.utc)

        db.session.add(user)
        db.session.commit()

        if verificar:
            if not _enviar_verificacion(user):
                flash("Tu cuenta se creó, pero no pudimos enviarte el correo "
                      "de confirmación. Usa «reenviar verificación» en un rato "
                      "o avisa a tu docente.", "error")
            log_activity_para(user, "register_pendiente_verificacion")
            return redirect(url_for("verificacion_pendiente"))

        login_user(user)
        log_activity("register")
        flash("¡Bienvenido/a a la plataforma!", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/recuperar-clave", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def recuperar_clave():
    """Pide el correo y envía el enlace para restablecer la contraseña."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.email_verified:
            _enviar_restablecimiento(user)
            log_activity_para(user, "solicito_restablecer_clave")
        elif user and not user.email_verified:
            # Cuenta sin confirmar: reenviar la verificación es lo que
            # realmente necesita, no un cambio de contraseña.
            _enviar_verificacion(user)

        # La respuesta es idéntica exista o no la cuenta: si variara, cualquiera
        # podría averiguar qué correos están registrados.
        flash("Si ese correo tiene una cuenta, te enviamos un enlace. "
              "Revisa tu bandeja institucional.", "info")
        return redirect(url_for("login"))

    return render_template("recuperar_clave.html")


@app.route("/restablecer-clave/<token>", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def restablecer_clave(token):
    """Permite elegir una contraseña nueva desde el enlace del correo."""
    user = User.query.filter_by(reset_token=token).first()

    vencido = (
        user is None
        or user.reset_expires_at is None
        or datetime.now(timezone.utc).replace(tzinfo=None)
        > user.reset_expires_at.replace(tzinfo=None)
    )
    if vencido:
        flash("Ese enlace no es válido o ya venció. Pide uno nuevo.", "error")
        return redirect(url_for("recuperar_clave"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if password != confirm:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("restablecer_clave.html", token=token)

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template("restablecer_clave.html", token=token)

        user.set_password(password)
        user.reset_token = None            # de un solo uso
        user.reset_expires_at = None
        db.session.commit()

        log_activity_para(user, "restablecio_clave")
        flash("Contraseña actualizada. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("restablecer_clave.html", token=token)


@app.route("/verificacion-pendiente")
def verificacion_pendiente():
    """Pantalla tras registrarse: avisa que hay que revisar el correo."""
    return render_template("verificacion_pendiente.html",
                           horas=app.config.get("VERIFICATION_TTL_HOURS", 48))


@app.route("/verificar/<token>")
@limiter.limit("30 per hour")
def verificar_correo(token):
    """Activa la cuenta desde el enlace del correo."""
    user = User.query.filter_by(verification_token=token).first()

    if not user:
        # Puede ser un enlace ya usado: si el token se limpió tras verificar,
        # no hay forma de distinguirlo de uno falso. Se explica sin alarmar.
        flash("Ese enlace no es válido o ya fue usado. "
              "Si ya confirmaste tu cuenta, simplemente inicia sesión.", "error")
        return redirect(url_for("login"))

    if user.email_verified:
        flash("Tu cuenta ya estaba confirmada. Puedes iniciar sesión.", "info")
        return redirect(url_for("login"))

    vence = user.verification_expires_at
    if vence and datetime.now(timezone.utc).replace(tzinfo=None) > vence.replace(tzinfo=None):
        flash("El enlace venció. Pide uno nuevo con tu correo y contraseña.", "error")
        return redirect(url_for("reenviar_verificacion"))

    user.email_verified = True
    user.verified_at = datetime.now(timezone.utc)
    user.verification_token = None          # de un solo uso
    user.verification_expires_at = None
    db.session.commit()

    log_activity_para(user, "email_verificado")
    flash("¡Cuenta confirmada! Ya puedes iniciar sesión.", "success")
    return redirect(url_for("login"))


@app.route("/reenviar-verificacion", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def reenviar_verificacion():
    """Reenvía el correo de confirmación a quien no lo recibió."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        # Se pide la contraseña para que nadie pueda bombardear de correos a
        # una dirección ajena. La respuesta es siempre la misma, así no se
        # revela qué correos existen.
        if user and user.check_password(password) and not user.email_verified:
            _enviar_verificacion(user)

        flash("Si los datos son correctos y la cuenta está pendiente, "
              "acabamos de enviarte un nuevo enlace.", "info")
        return redirect(url_for("verificacion_pendiente"))

    return render_template("reenviar_verificacion.html")


@app.route("/logout")
@login_required
def logout():
    log_activity("logout")
    logout_user()
    return redirect(url_for("index"))


# ─── DASHBOARD ──────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role in ("docente", "admin"):
        return redirect(url_for("admin_dashboard"))

    # Estadísticas del estudiante
    total_submissions = Submission.query.filter_by(user_id=current_user.id).count()
    recent_submissions = (
        Submission.query
        .filter_by(user_id=current_user.id)
        .order_by(Submission.created_at.desc())
        .limit(5)
        .all()
    )
    topics = Topic.query.order_by(Topic.order).all()

    # Progreso por tema
    topic_progress = []
    for topic in topics:
        exercise_ids = [e.id for e in topic.exercises.all()]
        if exercise_ids:
            # count(distinct exercise_id): .distinct(col) no funciona igual
            # en MySQL/SQLite y contaba submissions repetidas del mismo ejercicio
            completed = (
                db.session.query(func.count(func.distinct(Submission.exercise_id)))
                .filter(
                    Submission.user_id == current_user.id,
                    Submission.exercise_id.in_(exercise_ids),
                    Submission.score >= 60
                )
                .scalar() or 0
            )
            total = len(exercise_ids)
            topic_progress.append({
                "topic": topic,
                "completed": completed,
                "total": total,
                "percent": round(completed / total * 100) if total > 0 else 0
            })

    # Estado de los instrumentos de investigación del estudiante
    def _done(model, **kw):
        return model.query.filter_by(user_id=current_user.id, **kw).first() is not None

    research_status = {
        "pretest": _done(TestResult, test_type="pretest"),
        "postest": _done(TestResult, test_type="postest"),
        "escala_pre": _done(SelfEfficacyResult, test_type="pre"),
        "escala_post": _done(SelfEfficacyResult, test_type="post"),
    }

    return render_template(
        "dashboard.html",
        total_submissions=total_submissions,
        recent_submissions=recent_submissions,
        topic_progress=topic_progress,
        topics=topics,
        research_status=research_status
    )


# ─── EDITOR ─────────────────────────────────────────────────────────

@app.route("/editor")
@login_required
def editor():
    """Editor libre de pseudocódigo."""
    log_activity("open_editor", {"mode": "free"})
    return render_template("editor.html", exercise=None, cc_items=COGNITIVE_LOAD_ITEMS)


@app.route("/api/registrar-ayuda", methods=["POST"])
@limiter.limit("120 per hour")
@login_required
def registrar_ayuda():
    """Deja constancia de que el estudiante recurrió a las ayudas.

    Dato relevante para la investigación: permite saber en qué ejercicios se
    atascan y cuánto aguantan antes de pedir apoyo, no solo si acertaron.
    """
    data = request.get_json() or {}
    log_activity("pidio_ayuda", {
        "exercise_id": data.get("exercise_id"),
        "segundos_antes_de_pedirla": data.get("segundos"),
    })
    return jsonify({"success": True})


@app.route("/ejercicio/<int:exercise_id>")
@login_required
def ejercicio_teoria(exercise_id):
    """Pantalla de teoría previa al ejercicio.

    El estudiante llega aquí ANTES del editor: lee el concepto, estudia un
    ejemplo parecido resuelto y ve los pasos sugeridos. Solo entonces pasa a
    programar. Es el andamiaje que la tesis defiende: no lanzar al estudiante
    a la práctica sin preparación.
    """
    exercise = Exercise.query.get_or_404(exercise_id)
    log_activity("abrir_teoria", {"exercise_id": exercise_id})
    return render_template("ejercicio_teoria.html", exercise=exercise,
                           ya_predijo=_ya_predijo(exercise_id))


@app.route("/editor/<int:exercise_id>")
@login_required
def editor_exercise(exercise_id):
    """Editor con ejercicio específico."""
    exercise = Exercise.query.get_or_404(exercise_id)
    log_activity("open_editor", {"mode": "exercise", "exercise_id": exercise_id})

    # Cargar última submission si existe
    last_submission = (
        Submission.query
        .filter_by(user_id=current_user.id, exercise_id=exercise_id)
        .order_by(Submission.created_at.desc())
        .first()
    )

    return render_template("editor.html", exercise=exercise, last_submission=last_submission,
                           cc_items=COGNITIVE_LOAD_ITEMS)


# ─── EJERCICIOS ─────────────────────────────────────────────────────

# ─── APRENDER ──────────────────────────────────────────────────────
#
# El material de lecciones.py (10 temas) y guias.py (24 guias) estaba escrito
# y NO se mostraba en ningun sitio. Estas dos rutas son la puerta que le
# faltaba: primero se lee como se hacen las cosas, y desde ahi se pasa a los
# ejercicios del mismo tema.
#
# lecciones.py es la UNICA fuente del texto de las lecciones. Las columnas
# topics.leccion_* existieron hasta el 28/08/2026 con una copia del mismo
# texto; se retiraron porque las dos copias se separaron dos veces.

def _lista_errores(texto):
    """Los errores comunes vienen como parrafos que empiezan por vinneta."""
    trozos = [t.strip() for t in (texto or "").split("\n\n") if t.strip()]
    return [t.lstrip("• ").replace("\n  ", " ").strip() for t in trozos]


@app.route("/aprender")
@login_required
def aprender():
    """Indice de temas, con lo que ya llevas hecho.

    Sin esto, cinco tarjetas iguales y el estudiante sin saber por donde
    empezar ni que le falta. Los datos ya se estaban registrando: solo habia
    que pintarlos.
    """
    from lecciones import LECCIONES

    # Temas cuya leccion ya se abrio alguna vez. El dato lo deja
    # `leer_leccion` en el historial de actividad desde que existe la seccion.
    leidos = set()
    for reg in (ActivityLog.query
                .filter_by(user_id=current_user.id, action="leer_leccion")
                .all()):
        try:
            leidos.add(int((reg.details or {}).get("topic_id")))
        except (TypeError, ValueError):
            pass

    temas = []
    for t in Topic.query.order_by(Topic.order).all():
        ids = [e.id for e in Exercise.query.filter_by(topic_id=t.id, is_active=True).all()]
        # Mismo criterio que el panel de inicio (nota >= 60) para que las dos
        # pantallas no se contradigan.
        hechos = 0
        if ids:
            hechos = (db.session.query(func.count(func.distinct(Submission.exercise_id)))
                      .filter(Submission.user_id == current_user.id,
                              Submission.exercise_id.in_(ids),
                              Submission.score >= 60)
                      .scalar() or 0)
        temas.append({
            "tema": t,
            "tiene_leccion": t.id in LECCIONES,
            "leido": t.id in leidos,
            "n_ejercicios": len(ids),
            "hechos": hechos,
            "porcentaje": round(hechos / len(ids) * 100) if ids else 0,
            "completo": bool(ids) and hechos == len(ids),
        })

    # Por donde seguir: el primer tema sin terminar. Asi el indice guia en vez
    # de dejar cinco tarjetas identicas.
    #
    # Se calcula POR SEMESTRE: con las dos asignaturas en la misma pagina,
    # un unico "siguiente" global mandaba al alumno de primero a un tema de
    # tercero en cuanto terminaba los suyos.
    siguientes = {}
    for t in temas:
        sem = t["tema"].semestre
        if not t["completo"] and sem not in siguientes:
            siguientes[sem] = t["tema"].id
    # El boton de cabecera apunta al plan vigente (1er semestre) si lo hay.
    siguiente = siguientes.get(1) or siguientes.get(3) or next(iter(siguientes.values()), None)
    log_activity("abrir_aprender")
    return render_template("aprender.html", temas=temas, siguiente=siguiente,
                           siguientes=siguientes)


@app.route("/aprender/<int:topic_id>")
@login_required
def aprender_tema(topic_id):
    """La leccion de un tema, y al final el paso a sus ejercicios."""
    from lecciones import LECCIONES
    tema = db.session.get(Topic, topic_id)
    if not tema or topic_id not in LECCIONES:
        flash("Ese tema todavía no tiene lección.", "info")
        return redirect(url_for("aprender"))

    leccion = LECCIONES[topic_id]
    ejercicios = (Exercise.query
                  .filter_by(topic_id=topic_id, is_active=True)
                  .order_by(Exercise.difficulty, Exercise.orden, Exercise.id).all())
    # Temas anterior y siguiente, para poder recorrerlos en orden.
    # Solo dentro del MISMO semestre: encadenarlos todos hacia que la
    # ultima leccion de una asignatura llevara a la primera de la otra.
    todos = (Topic.query
             .filter(Topic.semestre == tema.semestre)
             .order_by(Topic.order).all())
    pos = [t.id for t in todos].index(topic_id) if tema in todos else -1
    log_activity("leer_leccion", {"topic_id": topic_id})
    return render_template(
        "aprender_tema.html", tema=tema, leccion=leccion,
        errores=_lista_errores(leccion.get("errores", "")),
        ejercicios=ejercicios,
        anterior=todos[pos - 1] if pos > 0 else None,
        siguiente=todos[pos + 1] if 0 <= pos < len(todos) - 1 else None)


@app.route("/exercises")
@login_required
def exercises():
    topics = Topic.query.order_by(Topic.order).all()
    return render_template("exercises.html", topics=topics)


@app.route("/exercises/<int:topic_id>")
@login_required
def topic_exercises(topic_id):
    # La leccion sale de lecciones.py, igual que en /aprender. Fue la unica
    # fuente desde el 28/08/2026: antes esta pagina leia las columnas
    # topics.leccion_* y la otra el archivo, asi que cada una podia mostrar
    # un texto distinto del mismo tema.
    from lecciones import LECCIONES
    topic = Topic.query.get_or_404(topic_id)
    # Sin ordenar, salian en el orden en que se insertaron y la dificultad
    # quedaba en zigzag: el estudiante se topaba con el avanzado antes de
    # terminar los intermedios. El ENUM esta declarado en el orden bueno
    # (basico, intermedio, avanzado), asi que MySQL ordena por su indice.
    exercises = (Exercise.query
                 .filter_by(topic_id=topic_id, is_active=True)
                 .order_by(Exercise.difficulty, Exercise.orden, Exercise.id)
                 .all())

    # Marcar cuáles ya completó el estudiante
    for ex in exercises:
        ex.completed = (
            Submission.query
            .filter_by(user_id=current_user.id, exercise_id=ex.id)
            .filter(Submission.score >= 60)
            .first() is not None
        )
        ex.attempts = (
            Submission.query
            .filter_by(user_id=current_user.id, exercise_id=ex.id)
            .count()
        )

    return render_template("topic_exercises.html", topic=topic,
                           exercises=exercises,
                           tiene_leccion=topic_id in LECCIONES)


# ─── API ENDPOINTS ──────────────────────────────────────────────────

@app.route("/api/convert", methods=["POST"])
@limiter.limit(lambda: app.config["RATELIMIT_AI"])
@login_required
def api_convert():
    """Convierte pseudocódigo a un lenguaje de programación."""
    data = request.get_json()
    pseudocode = data.get("pseudocode", "").strip()
    language = data.get("language", "python")

    if language not in ("python", "cpp", "php"):
        return jsonify({"success": False, "error": "Lenguaje no soportado."}), 400

    valido, motivo = validar_pseudocodigo(pseudocode)
    if not valido:
        log_activity("convert_rechazado", {"largo": len(pseudocode)})
        return jsonify({"success": False, "error": motivo, "no_es_pseudocodigo": True}), 400

    result = convert_pseudocode(pseudocode, language)

    log_activity("convert", {
        "language": language,
        "pseudocode_length": len(pseudocode),
        "success": result["success"],
        "cached": result.get("cached", False),
        "usage": result.get("usage", {}),
    })

    return jsonify(result)


@app.route("/api/trace", methods=["POST"])
@limiter.limit(lambda: app.config["RATELIMIT_EXEC"])
@login_required
def api_trace():
    """Prueba de escritorio: traza real de la ejecución, paso a paso.

    Acepta el código Python ya convertido (que el estudiante puede haber
    retocado a mano) o, si no lo hay, el pseudocódigo: en ese caso lo
    convierte primero, casi siempre desde caché.
    """
    data = request.get_json() or {}
    code = (data.get("code") or "").strip()
    pseudocode = (data.get("pseudocode") or "").strip()
    stdin = data.get("stdin", "") or ""

    if len(code) > 50_000 or len(stdin) > 10_000:
        return jsonify({"success": False, "error": "El código o los datos son demasiado largos."}), 400

    if not code:
        if not pseudocode:
            return jsonify({"success": False, "error": "No hay código que trazar."}), 400
        conv = convert_pseudocode(pseudocode, "python")
        if not conv.get("success"):
            return jsonify({"success": False, "error": conv.get("error", "No se pudo convertir.")}), 400
        code = conv["code"]

    result = traza.trazar(code, stdin)

    log_activity("trace", {
        "code_length": len(code),
        "success": result["success"],
        "pasos": len(result.get("pasos", [])),
        "cortada": result.get("cortada", False),
    })

    return jsonify(result)


@app.route("/api/diagram", methods=["POST"])
@limiter.limit(lambda: app.config["RATELIMIT_AI"])
@login_required
def api_diagram():
    """Convierte pseudocódigo en un diagrama de flujo (Mermaid)."""
    data = request.get_json() or {}
    pseudocode = data.get("pseudocode", "").strip()

    valido, motivo = validar_pseudocodigo(pseudocode)
    if not valido:
        log_activity("diagram_rechazado", {"largo": len(pseudocode)})
        return jsonify({"success": False, "error": motivo, "no_es_pseudocodigo": True}), 400

    result = convert_to_diagram(pseudocode)

    log_activity("diagram", {
        "pseudocode_length": len(pseudocode),
        "success": result["success"],
        "cached": result.get("cached", False),
        "usage": result.get("usage", {}),
    })

    return jsonify(result)


@app.route("/api/usage", methods=["GET"])
@login_required
def api_usage():
    """Cuenta llamadas REALES a la IA (no caché) en las últimas 5 horas.
    Devuelve el cupo libre estimado del plan free de OpenCode Zen (200 / 5h)."""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import func

    window_h = 5
    # naive UTC: las columnas DateTime se guardan sin tz (MySQL y SQLite)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=window_h)

    rows = db.session.query(ActivityLog).filter(
        ActivityLog.action.in_(OPERACIONES_IA),
        ActivityLog.created_at >= since,
    ).all()

    real_calls = sum(1 for r in rows if not (r.details or {}).get("cached"))
    cached_calls = sum(1 for r in rows if (r.details or {}).get("cached"))

    limit = 200
    return jsonify({
        "window_hours": window_h,
        "real_calls": real_calls,
        "cached_calls": cached_calls,
        "limit": limit,
        "remaining": max(0, limit - real_calls),
        "percent_used": round(real_calls / limit * 100, 1),
    })


@app.route("/api/execute", methods=["POST"])
@limiter.limit(lambda: app.config["RATELIMIT_EXEC"])
@login_required
def api_execute():
    """Ejecuta código en el sandbox de bubblewrap. Devuelve stdout/stderr/exit_code."""
    data = request.get_json() or {}
    language = data.get("language", "")
    code = data.get("code", "")
    stdin = data.get("stdin", "") or ""

    if language not in ("python", "cpp", "php"):
        return jsonify({"success": False, "error": "Lenguaje no soportado."}), 400

    # Limitar tamaño del código y stdin para evitar abuso
    if len(code) > 50_000:
        return jsonify({"success": False, "error": "El código excede 50.000 caracteres."}), 400
    if len(stdin) > 10_000:
        return jsonify({"success": False, "error": "El stdin excede 10.000 caracteres."}), 400

    result = executor.run(language, code, stdin)

    log_activity("execute", {
        "language": language,
        "code_length": len(code),
        "exit_code": result["exit_code"],
        "timed_out": result["timed_out"],
    })

    return jsonify({"success": True, **result})


@app.route("/api/explain", methods=["POST"])
@limiter.limit(lambda: app.config["RATELIMIT_AI"])
@login_required
def api_explain():
    """Pide a la IA que explique paso a paso un código convertido."""
    data = request.get_json() or {}
    code = (data.get("code") or "").strip()
    language = data.get("language", "")

    if language not in ("python", "cpp", "php"):
        return jsonify({"success": False, "error": "Lenguaje no soportado."}), 400
    if not code:
        return jsonify({"success": False, "error": "El código está vacío."}), 400

    result = explain_code(code, language)

    log_activity("explain", {
        "language": language,
        "code_length": len(code),
        "success": result["success"],
        "cached": result.get("cached", False),
        "usage": result.get("usage", {}),
    })

    return jsonify(result)


@app.route("/api/convert-all", methods=["POST"])
@limiter.limit(lambda: app.config["RATELIMIT_AI"])
@login_required
def api_convert_all():
    """Convierte pseudocódigo a los tres lenguajes."""
    data = request.get_json()
    pseudocode = data.get("pseudocode", "").strip()

    if not pseudocode:
        return jsonify({"success": False, "error": "El pseudocódigo está vacío."}), 400

    valido, motivo = validar_pseudocodigo(pseudocode)
    if not valido:
        log_activity("submit_rechazado", {"largo": len(pseudocode)})
        return jsonify({"success": False, "error": motivo, "no_es_pseudocodigo": True}), 400


    valido, motivo = validar_pseudocodigo(pseudocode)
    if not valido:
        log_activity("feedback_rechazado", {"largo": len(pseudocode)})
        return jsonify({"success": False, "error": motivo, "no_es_pseudocodigo": True}), 400


    valido, motivo = validar_pseudocodigo(pseudocode)
    if not valido:
        log_activity("convert_all_rechazado", {"largo": len(pseudocode)})
        return jsonify({"success": False, "error": motivo, "no_es_pseudocodigo": True}), 400


    results = convert_to_all_languages(pseudocode)

    # Loguear cada lenguaje por separado para el contador /api/usage
    for lang, sub in results.items():
        log_activity("convert", {
            "language": lang,
            "pseudocode_length": len(pseudocode),
            "success": sub.get("success", False),
            "cached": sub.get("cached", False),
            "via": "convert_all",
            "usage": sub.get("usage", {}),
        })

    return jsonify({"success": True, "results": results})


@app.route("/api/feedback", methods=["POST"])
@limiter.limit(lambda: app.config["RATELIMIT_AI"])
@login_required
def api_feedback():
    """Genera retroalimentación con IA sobre el pseudocódigo."""
    data = request.get_json()
    pseudocode = data.get("pseudocode", "").strip()
    exercise_id = data.get("exercise_id")
    exercise_description = None

    if not pseudocode:
        return jsonify({"success": False, "error": "El pseudocódigo está vacío."}), 400

    if exercise_id:
        exercise = Exercise.query.get(exercise_id)
        if exercise:
            exercise_description = exercise.description

    quedan, tope = feedback_cupo(current_user, exercise_id)
    result = get_ai_feedback(pseudocode, exercise_description,
                             permitir_llamada=(quedan is None or quedan > 0))

    # Usamos "feedback" para que cuente en /api/usage
    log_activity("feedback", {
        "exercise_id": exercise_id,
        "pseudocode_length": len(pseudocode),
        "success": result["success"],
        "cached": result.get("cached", False),
        "usage": result.get("usage", {}),
    })

    if result.get("sin_cupo"):
        return jsonify({**result, "cupo": {"quedan": 0, "tope": tope}}), 429

    if quedan is not None:
        # log_activity ya anoto el gasto de esta llamada, asi que se vuelve a
        # contar en vez de restar a mano: es la unica cifra que no se desvia.
        restantes = max(tope - feedback_gastadas(current_user.id, exercise_id), 0)
        result = {**result, "cupo": {"quedan": restantes, "tope": tope}}

    return jsonify(result)


@app.route("/api/submit", methods=["POST"])
@limiter.limit(lambda: app.config["RATELIMIT_AI"])
@login_required
def api_submit():
    """Guarda una submission del estudiante."""
    data = request.get_json()
    pseudocode = data.get("pseudocode", "").strip()
    exercise_id = data.get("exercise_id")
    converted = data.get("converted", {})
    feedback = data.get("feedback", "")
    time_spent = data.get("time_spent", 0)

    if not pseudocode:
        return jsonify({"success": False, "error": "El pseudocódigo está vacío."}), 400

    # Contar intento
    attempt = 1
    exercise = None
    if exercise_id:
        exercise = Exercise.query.get(exercise_id)
        attempt = (
            Submission.query
            .filter_by(user_id=current_user.id, exercise_id=exercise_id)
            .count() + 1
        )

    # Calificación automática con IA (0-100) cuando hay ejercicio asociado
    score = None
    grade_reason = None
    if exercise:
        grade = grade_submission(pseudocode, exercise.description)
        if grade.get("success"):
            score = grade["score"]
            grade_reason = grade.get("reason", "")
            log_activity("grade", {
                "exercise_id": exercise_id,
                "score": score,
                "cached": grade.get("cached", False),
                "usage": grade.get("usage", {}),
            })

    submission = Submission(
        user_id=current_user.id,
        exercise_id=exercise_id,
        pseudocode=pseudocode,
        converted_python=converted.get("python", ""),
        converted_cpp=converted.get("cpp", ""),
        converted_php=converted.get("php", ""),
        ai_feedback=feedback,
        score=score,
        attempt_number=attempt,
        time_spent_seconds=time_spent
    )
    db.session.add(submission)
    db.session.commit()

    log_activity("submit", {
        "exercise_id": exercise_id,
        "attempt": attempt,
        "submission_id": submission.id,
        "score": score,
    })

    return jsonify({
        "success": True,
        "submission_id": submission.id,
        "score": score,
        "grade_reason": grade_reason,
        "passed": (score is not None and score >= 60),
    })


# ─── INSTRUMENTOS DE INVESTIGACIÓN (pretest/postest + autoeficacia) ──

VALID_TESTS = ("pretest", "postest")
VALID_SCALES = ("pre", "post")


@app.route("/evaluacion/<test_type>")
@login_required
def take_test(test_type):
    """Pretest o postest de conocimientos (20 ítems de opción múltiple)."""
    if test_type not in VALID_TESTS:
        return redirect(url_for("dashboard"))
    existing = TestResult.query.filter_by(
        user_id=current_user.id, test_type=test_type
    ).first()
    log_activity("open_test", {"test_type": test_type, "already_done": existing is not None})
    return render_template(
        "test.html",
        test_type=test_type,
        questions=TEST_QUESTIONS,
        existing=existing,
    )


@app.route("/api/evaluacion/<test_type>", methods=["POST"])
@login_required
def submit_test(test_type):
    if test_type not in VALID_TESTS:
        return jsonify({"success": False, "error": "Evaluación no válida."}), 400
    if TestResult.query.filter_by(user_id=current_user.id, test_type=test_type).first():
        return jsonify({"success": False, "error": "Ya presentaste esta evaluación."}), 400

    data = request.get_json() or {}
    answers = data.get("answers") or {}
    time_spent = int(data.get("time_spent") or 0)

    total = len(TEST_QUESTIONS)
    unanswered = [q["id"] for q in TEST_QUESTIONS if answers.get(q["id"]) is None]
    if unanswered:
        return jsonify({
            "success": False,
            "error": f"Faltan {len(unanswered)} preguntas por responder.",
            "unanswered": unanswered,
        }), 400

    correct = sum(1 for q in TEST_QUESTIONS if answers.get(q["id"]) == q["answer"])
    score = round(correct / total * 100, 1)

    result = TestResult(
        user_id=current_user.id,
        test_type=test_type,
        score=score,
        total_questions=total,
        correct_answers=correct,
        answers_json=answers,
        time_spent_seconds=time_spent,
    )
    db.session.add(result)
    db.session.commit()

    log_activity("submit_test", {
        "test_type": test_type, "score": score,
        "correct": correct, "total": total, "time_spent": time_spent,
    })
    return jsonify({"success": True, "score": score, "correct": correct, "total": total})


@app.route("/escala/<scale_type>")
@login_required
def take_scale(scale_type):
    """Escala de autoeficacia en programación (10 ítems Likert 1-5)."""
    if scale_type not in VALID_SCALES:
        return redirect(url_for("dashboard"))
    existing = SelfEfficacyResult.query.filter_by(
        user_id=current_user.id, test_type=scale_type
    ).first()
    log_activity("open_scale", {"scale_type": scale_type, "already_done": existing is not None})
    return render_template(
        "scale.html",
        scale_type=scale_type,
        items=SELF_EFFICACY_ITEMS,
        likert_labels=LIKERT_LABELS,
        existing=existing,
    )


@app.route("/api/escala/<scale_type>", methods=["POST"])
@login_required
def submit_scale(scale_type):
    if scale_type not in VALID_SCALES:
        return jsonify({"success": False, "error": "Escala no válida."}), 400
    if SelfEfficacyResult.query.filter_by(user_id=current_user.id, test_type=scale_type).first():
        return jsonify({"success": False, "error": "Ya respondiste esta escala."}), 400

    data = request.get_json() or {}
    responses = data.get("responses") or {}

    missing = [it["id"] for it in SELF_EFFICACY_ITEMS if responses.get(it["id"]) is None]
    if missing:
        return jsonify({
            "success": False,
            "error": f"Faltan {len(missing)} ítems por responder.",
            "missing": missing,
        }), 400

    values = []
    for it in SELF_EFFICACY_ITEMS:
        try:
            v = int(responses[it["id"]])
        except (TypeError, ValueError):
            v = 0
        if not 1 <= v <= 5:
            return jsonify({"success": False, "error": "Respuestas fuera de rango (1-5)."}), 400
        values.append(v)

    total_score = sum(values)
    result = SelfEfficacyResult(
        user_id=current_user.id,
        test_type=scale_type,
        responses_json=responses,
        total_score=total_score,
    )
    db.session.add(result)
    db.session.commit()

    log_activity("submit_scale", {"scale_type": scale_type, "total_score": total_score})
    return jsonify({"success": True, "total_score": total_score, "max_score": len(values) * 5})


# ─── CARGA COGNITIVA (Paas, 1-9, tras cada actividad) ──────────────

@app.route("/api/carga-cognitiva", methods=["POST"])
@limiter.limit("60 per hour")
@login_required
def submit_cognitive_load():
    """Registra la carga cognitiva percibida tras una actividad práctica.

    Cuarta variable dependiente de la hipótesis. A diferencia de las escalas
    pre/post, se puede responder varias veces: una por actividad.
    """
    data = request.get_json() or {}
    responses = data.get("responses") or {}
    exercise_id = data.get("exercise_id")
    submission_id = data.get("submission_id")

    missing = [it["id"] for it in COGNITIVE_LOAD_ITEMS if responses.get(it["id"]) is None]
    if missing:
        return jsonify({
            "success": False,
            "error": f"Faltan {len(missing)} ítems por responder.",
            "missing": missing,
        }), 400

    values = []
    for it in COGNITIVE_LOAD_ITEMS:
        try:
            v = int(responses[it["id"]])
        except (TypeError, ValueError):
            v = 0
        if not 1 <= v <= 9:
            return jsonify({"success": False, "error": "Respuestas fuera de rango (1-9)."}), 400
        values.append(v)

    # Validar que el ejercicio y el envío existan y sean del propio estudiante
    if exercise_id is not None and not db.session.get(Exercise, exercise_id):
        exercise_id = None
    if submission_id is not None:
        sub = db.session.get(Submission, submission_id)
        if not sub or sub.user_id != current_user.id:
            submission_id = None

    mean_score = round(sum(values) / len(values), 2)
    result = CognitiveLoadResult(
        user_id=current_user.id,
        exercise_id=exercise_id,
        submission_id=submission_id,
        responses_json=responses,
        mean_score=mean_score,
    )
    db.session.add(result)
    db.session.commit()

    log_activity("submit_cognitive_load", {
        "exercise_id": exercise_id,
        "mean_score": mean_score,
    })
    return jsonify({"success": True, "mean_score": mean_score})


# ─── PRIVACIDAD / CONSENTIMIENTO ───────────────────────────────────

# Endpoints que un estudiante sin consentimiento SI puede visitar: los que
# necesita justamente para leerlo y aceptarlo, y los de salir.
SIN_CONSENTIMIENTO = {
    "consentimiento", "privacidad", "logout", "static",
    "login", "register", "verificar_correo", "verificacion_pendiente",
    "reenviar_verificacion", "recuperar_clave", "restablecer_clave", "index",
}


@app.before_request
def exigir_consentimiento():
    """Nadie participa en el estudio sin haberlo aceptado.

    consent_accepted se escribia al registrarse pero NO se comprobaba en
    ningun sitio. Una cuenta creada a mano por el docente entraba, presentaba
    el pretest y sus datos entraban al estudio sin que la persona hubiera
    aceptado nada. Comprobado el 18/08/2026: saco 60,0 en el pretest sin
    pasar por ninguna casilla. Ley 1581/2012 y Resolucion 8430/1993.

    Solo se exige a los estudiantes: docentes y administradores no son
    participantes del estudio, y bloquearlos los dejaria sin poder entrar a
    administrar.
    """
    if not current_user.is_authenticated:
        return
    if current_user.role != "estudiante" or current_user.consent_accepted:
        return
    if request.endpoint in SIN_CONSENTIMIENTO:
        return
    # Las llamadas de la API contestan JSON: una redireccion la recibiria el
    # fetch como HTML y el estudiante veria un error raro sin explicacion.
    if request.path.startswith("/api/"):
        return jsonify({"success": False,
                        "error": "Antes de continuar tienes que leer y aceptar "
                                 "el consentimiento informado."}), 403
    return redirect(url_for("consentimiento"))


@app.route("/consentimiento", methods=["GET", "POST"])
@login_required
def consentimiento():
    """Aceptacion del consentimiento para quien no paso por el registro."""
    if current_user.consent_accepted:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        if not request.form.get("consent"):
            flash("Para participar tienes que marcar la casilla.", "error")
            return render_template("consentimiento.html",
                                   consent_version=CONSENT_VERSION)
        current_user.consent_accepted = True
        current_user.consent_at = datetime.now(timezone.utc)
        current_user.consent_version = CONSENT_VERSION
        db.session.commit()
        log_activity("consentimiento_aceptado", {"version": CONSENT_VERSION})
        flash("Gracias. Ya puedes usar la plataforma.", "success")
        return redirect(url_for("dashboard"))

    return render_template("consentimiento.html", consent_version=CONSENT_VERSION)


@app.route("/privacidad")
def privacidad():
    """Política de tratamiento de datos. El Decreto 1377 de 2013 exige que sea
    consultable de forma permanente, no solo en el momento del registro."""
    return render_template("privacidad.html", consent_version=CONSENT_VERSION)


# ─── PERFIL (cambio de contraseña) ─────────────────────────────────

@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        if not current_user.check_password(current):
            flash("La contraseña actual no es correcta.", "error")
        elif len(new) < 6:
            flash("La contraseña nueva debe tener al menos 6 caracteres.", "error")
        elif new != confirm:
            flash("Las contraseñas nuevas no coinciden.", "error")
        else:
            current_user.set_password(new)
            db.session.commit()
            log_activity("password_change")
            flash("Contraseña actualizada correctamente.", "success")
            return redirect(url_for("perfil"))

    return render_template("perfil.html")


# ─── PANEL DE DOCENTE ───────────────────────────────────────────────

@app.route("/admin")
@login_required
@role_required("docente", "admin")
def admin_dashboard():
    total_students = User.query.filter_by(role="estudiante").count()
    total_submissions = Submission.query.count()
    total_exercises = Exercise.query.filter_by(is_active=True).count()

    # Estudiantes con más actividad
    from sqlalchemy import func
    active_students = (
        db.session.query(
            User.name,
            func.count(Submission.id).label("submissions")
        )
        .join(Submission, User.id == Submission.user_id)
        .filter(User.role == "estudiante")
        .group_by(User.id)
        .order_by(func.count(Submission.id).desc())
        .limit(10)
        .all()
    )

    # Submissions recientes
    recent = (
        Submission.query
        .order_by(Submission.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        total_submissions=total_submissions,
        total_exercises=total_exercises,
        active_students=active_students,
        recent_submissions=recent
    )


@app.route("/admin/exercises", methods=["GET", "POST"])
@login_required
@role_required("docente", "admin")
def admin_exercises():
    if request.method == "POST":
        topic_id = request.form.get("topic_id")
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        difficulty = request.form.get("difficulty", "basico")
        hints = request.form.get("hints", "").strip()

        exercise = Exercise(
            topic_id=topic_id,
            title=title,
            description=description,
            difficulty=difficulty,
            hints=hints
        )
        db.session.add(exercise)
        db.session.commit()
        flash("Ejercicio creado exitosamente.", "success")
        return redirect(url_for("admin_exercises"))

    topics = Topic.query.order_by(Topic.order).all()
    exercises = Exercise.query.order_by(Exercise.created_at.desc()).all()
    return render_template("admin/exercises.html", topics=topics, exercises=exercises)


@app.route("/admin/exercises/<int:exercise_id>/delete", methods=["POST"])
@login_required
@role_required("docente", "admin")
def delete_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    exercise.is_active = False
    db.session.commit()
    flash("Ejercicio desactivado.", "info")
    return redirect(url_for("admin_exercises"))


@app.route("/admin/students")
@login_required
@role_required("docente", "admin")
def admin_students():
    students = User.query.filter_by(role="estudiante").order_by(User.name).all()
    return render_template("admin/students.html", students=students)


@app.route("/admin/students/<int:user_id>/group", methods=["POST"])
@login_required
@role_required("docente", "admin")
def assign_group(user_id):
    user = User.query.get_or_404(user_id)
    group = request.form.get("group")
    if group in ("A", "B"):
        user.group = group
        db.session.commit()
        flash(f"{user.name} asignado al Grupo {group}.", "success")
    return redirect(url_for("admin_students"))


@app.route("/admin/logs")
@login_required
@role_required("docente", "admin")
def admin_logs():
    """Exportar logs de actividad para análisis."""
    from sqlalchemy import func

    # Resumen de actividad
    activity_summary = (
        db.session.query(
            ActivityLog.action,
            func.count(ActivityLog.id).label("count")
        )
        .group_by(ActivityLog.action)
        .all()
    )

    logs = (
        ActivityLog.query
        .order_by(ActivityLog.created_at.desc())
        .limit(100)
        .all()
    )

    return render_template("admin/logs.html", summary=activity_summary, logs=logs)


@app.route("/api/admin/export-logs")
@login_required
@role_required("docente", "admin")
def export_logs():
    """Exportar logs en formato JSON para análisis en R/SPSS."""
    logs = ActivityLog.query.order_by(ActivityLog.created_at).all()
    data = [{
        "id": l.id,
        "user_id": l.user_id,
        "action": l.action,
        "details": l.details,
        "timestamp": l.created_at.isoformat()
    } for l in logs]
    return jsonify(data)


# ─── ADMIN: PANEL DE INVESTIGACIÓN + EXPORTACIÓN CSV ───────────────

def _csv_response(filename, header, rows):
    """Arma una respuesta CSV (UTF-8 con BOM para que Excel lo abra bien)."""
    import csv
    import io
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    from flask import Response
    return Response(
        "﻿" + buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _research_rows():
    """Consolida por estudiante: grupo, pretest, postest, ganancia, escalas."""
    students = User.query.filter_by(role="estudiante").order_by(User.name).all()
    tests = {(t.user_id, t.test_type): t for t in TestResult.query.all()}
    scales = {(s.user_id, s.test_type): s for s in SelfEfficacyResult.query.all()}

    # Carga cognitiva: media por estudiante y número de mediciones.
    # Se agrega porque es medida repetida (una por actividad), no pre/post.
    carga = {
        uid: (round(media, 2) if media is not None else None, n)
        for uid, media, n in db.session.query(
            CognitiveLoadResult.user_id,
            func.avg(CognitiveLoadResult.mean_score),
            func.count(CognitiveLoadResult.id),
        ).group_by(CognitiveLoadResult.user_id).all()
    }

    rows = []
    for s in students:
        pre = tests.get((s.id, "pretest"))
        post = tests.get((s.id, "postest"))
        e_pre = scales.get((s.id, "pre"))
        e_post = scales.get((s.id, "post"))
        gain = (post.score - pre.score) if (pre and post) else None
        subs = Submission.query.filter_by(user_id=s.id)
        cc_media, cc_n = carga.get(s.id, (None, 0))
        rows.append({
            "student": s,
            "group": s.group or "",
            "pretest": pre,
            "postest": post,
            "gain": gain,
            "escala_pre": e_pre,
            "escala_post": e_post,
            "carga_cognitiva": cc_media,
            "carga_n": cc_n,
            "consentimiento": s.consent_at.strftime("%Y-%m-%d %H:%M") if s.consent_at else "",
            "submissions": subs.count(),
            "avg_score": db.session.query(func.avg(Submission.score))
                         .filter(Submission.user_id == s.id, Submission.score.isnot(None))
                         .scalar(),
        })
    return rows


@app.route("/admin/research")
@login_required
@role_required("docente", "admin")
def admin_research():
    """Resultados de los instrumentos del estudio, por estudiante."""
    rows = _research_rows()
    done = {
        "pretest": sum(1 for r in rows if r["pretest"]),
        "postest": sum(1 for r in rows if r["postest"]),
        "escala_pre": sum(1 for r in rows if r["escala_pre"]),
        "escala_post": sum(1 for r in rows if r["escala_post"]),
    }
    return render_template("admin/research.html", rows=rows, done=done,
                           total_students=len(rows))


@app.route("/api/admin/export/research.csv")
@login_required
@role_required("docente", "admin")
def export_research_csv():
    """CSV listo para R/SPSS: una fila por estudiante."""
    header = [
        "id_estudiante", "nombre", "email", "grupo", "experiencia_previa",
        "promedio_ingreso", "pretest_puntaje", "pretest_correctas",
        "pretest_segundos", "postest_puntaje", "postest_correctas",
        "postest_segundos", "ganancia", "autoeficacia_pre", "autoeficacia_post",
        "carga_cognitiva_media", "carga_cognitiva_mediciones",
        "envios_totales", "promedio_calificacion_ejercicios",
        "consentimiento_fecha",
    ]
    rows = []
    for r in _research_rows():
        s = r["student"]
        rows.append([
            s.id, s.name, s.email, r["group"],
            1 if s.prior_experience else 0,
            s.gpa_entry if s.gpa_entry is not None else "",
            r["pretest"].score if r["pretest"] else "",
            r["pretest"].correct_answers if r["pretest"] else "",
            r["pretest"].time_spent_seconds if r["pretest"] else "",
            r["postest"].score if r["postest"] else "",
            r["postest"].correct_answers if r["postest"] else "",
            r["postest"].time_spent_seconds if r["postest"] else "",
            r["gain"] if r["gain"] is not None else "",
            r["escala_pre"].total_score if r["escala_pre"] else "",
            r["escala_post"].total_score if r["escala_post"] else "",
            r["carga_cognitiva"] if r["carga_cognitiva"] is not None else "",
            r["carga_n"],
            r["submissions"],
            round(r["avg_score"], 1) if r["avg_score"] is not None else "",
            r["consentimiento"],
        ])
    return _csv_response("investigacion.csv", header, rows)


@app.route("/api/admin/export/logs.csv")
@login_required
@role_required("docente", "admin")
def export_logs_csv():
    """CSV de logs de actividad (una fila por evento)."""
    import json as _json
    header = ["id", "id_usuario", "accion", "detalles", "fecha_utc"]
    rows = [
        [l.id, l.user_id, l.action,
         _json.dumps(l.details, ensure_ascii=False) if l.details else "",
         l.created_at.isoformat() if l.created_at else ""]
        for l in ActivityLog.query.order_by(ActivityLog.created_at).all()
    ]
    return _csv_response("logs_actividad.csv", header, rows)


@app.route("/api/admin/export/submissions.csv")
@login_required
@role_required("docente", "admin")
def export_submissions_csv():
    """CSV de envíos de ejercicios (una fila por envío)."""
    header = ["id", "id_estudiante", "id_ejercicio", "ejercicio", "intento",
              "calificacion", "segundos_dedicados", "fecha_utc"]
    rows = []
    for s in Submission.query.order_by(Submission.created_at).all():
        rows.append([
            s.id, s.user_id, s.exercise_id or "",
            s.exercise.title if s.exercise else "practica_libre",
            s.attempt_number,
            s.score if s.score is not None else "",
            s.time_spent_seconds or "",
            s.created_at.isoformat() if s.created_at else "",
        ])
    return _csv_response("envios.csv", header, rows)


# ─── ADMIN: TOKENS / IA / USUARIOS ─────────────────────────────────

@app.route("/admin/tokens")
@login_required
@role_required("docente", "admin")
def admin_tokens():
    """Panel de uso de tokens IA por usuario + stats globales."""
    from sqlalchemy import func
    from datetime import datetime, timezone, timedelta
    from models import AICache

    # MariaDB devuelve datetimes naive (asumimos UTC). Normalizamos a naive
    # para poder comparar con created_at directamente.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    h5_ago = now - timedelta(hours=5)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    ai_logs = ActivityLog.query.filter(
        ActivityLog.action.in_(OPERACIONES_IA)
    ).all()

    # ── Agregado por usuario ──
    per_user = {}
    for l in ai_logs:
        d = l.details or {}
        u = d.get("usage") or {}
        bucket = per_user.setdefault(l.user_id, {
            "user_id": l.user_id,
            "real_calls": 0, "cached_calls": 0,
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
            "by_action": {"convert": 0, "feedback": 0, "explain": 0, "grade": 0},
            "last_used": None,
        })
        bucket["by_action"][l.action] = bucket["by_action"].get(l.action, 0) + 1
        if d.get("cached"):
            bucket["cached_calls"] += 1
        else:
            bucket["real_calls"] += 1
            bucket["prompt_tokens"] += int(u.get("prompt_tokens", 0) or 0)
            bucket["completion_tokens"] += int(u.get("completion_tokens", 0) or 0)
            bucket["total_tokens"] += int(u.get("total_tokens", 0) or 0)
        if bucket["last_used"] is None or (l.created_at and l.created_at > bucket["last_used"]):
            bucket["last_used"] = l.created_at

    user_ids = list(per_user.keys())
    users_map = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}
    rows = []
    for uid, b in per_user.items():
        u = users_map.get(uid)
        rows.append({
            **b,
            "name": (u.name if u else f"#{uid}"),
            "email": (u.email if u else ""),
            "role": (u.role if u else ""),
        })
    rows.sort(key=lambda r: r["total_tokens"], reverse=True)

    # ── Stats globales por ventana ──
    def window_stats(since):
        real = cached = total_tok = 0
        for l in ai_logs:
            if l.created_at and l.created_at >= since:
                d = l.details or {}
                if d.get("cached"):
                    cached += 1
                else:
                    real += 1
                    total_tok += int((d.get("usage") or {}).get("total_tokens", 0) or 0)
        return {"real": real, "cached": cached, "tokens": total_tok}

    stats_5h = window_stats(h5_ago)
    stats_24h = window_stats(day_ago)
    stats_7d = window_stats(week_ago)

    # ── Récords ──
    max_user = max(rows, key=lambda r: r["total_tokens"], default=None)
    max_calls_user = max(rows, key=lambda r: r["real_calls"], default=None)

    # Modelos usados
    by_model = {}
    for l in ai_logs:
        d = l.details or {}
        if d.get("cached"): continue
        u = d.get("usage") or {}
        m = u.get("model", "desconocido")
        bm = by_model.setdefault(m, {"calls": 0, "tokens": 0})
        bm["calls"] += 1
        bm["tokens"] += int(u.get("total_tokens", 0) or 0)
    by_model_list = sorted(
        [{"model": m, **v} for m, v in by_model.items()],
        key=lambda r: r["tokens"], reverse=True,
    )

    cache_entries = db.session.query(func.count(AICache.id)).scalar() or 0
    cache_hits_total = db.session.query(func.coalesce(func.sum(AICache.hit_count), 0)).scalar() or 0

    return render_template(
        "admin/tokens.html",
        rows=rows,
        stats_5h=stats_5h, stats_24h=stats_24h, stats_7d=stats_7d,
        max_user=max_user, max_calls_user=max_calls_user,
        by_model=by_model_list,
        models_config={
            "convert": os.getenv("OPENCODE_MODEL_CONVERT", "minimax-m2.5-free"),
            "tutor": os.getenv("OPENCODE_MODEL_TUTOR", "deepseek-v4-flash-free"),
            "fallback": os.getenv("OPENCODE_MODEL", "deepseek-v4-flash-free"),
        },
        cache_entries=cache_entries,
        cache_hits_total=cache_hits_total,
    )


@app.route("/admin/cache")
@login_required
@role_required("docente", "admin")
def admin_cache():
    """Vista de la caché IA."""
    from models import AICache
    top = AICache.query.order_by(AICache.hit_count.desc()).limit(50).all()
    return render_template("admin/cache.html", entries=top)


@app.route("/admin/cache/clear", methods=["POST"])
@login_required
@role_required("admin")
def admin_cache_clear():
    """Borra TODA la caché IA. Solo admin."""
    from models import AICache
    n = AICache.query.delete()
    db.session.commit()
    flash(f"Caché IA limpiada ({n} entradas eliminadas).", "success")
    return redirect(url_for("admin_cache"))


@app.route("/admin/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@role_required("admin")
def admin_toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("No puedes deshabilitarte a ti mismo.", "error")
        return redirect(url_for("admin_students"))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"{user.name} {'activado' if user.is_active else 'desactivado'}.", "success")
    return redirect(request.referrer or url_for("admin_students"))


@app.route("/admin/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
@role_required("admin")
def admin_reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_pwd = request.form.get("new_password", "").strip()
    if len(new_pwd) < 6:
        flash("La contraseña debe tener al menos 6 caracteres.", "error")
        return redirect(request.referrer or url_for("admin_students"))
    user.set_password(new_pwd)
    db.session.commit()
    log_activity("admin_password_reset", {"target_user_id": user.id})
    flash(f"Contraseña de {user.name} actualizada.", "success")
    return redirect(request.referrer or url_for("admin_students"))


# ─── INICIALIZACIÓN ─────────────────────────────────────────────────

def seed_topics():
    """Crear temas iniciales del curso."""
    if Topic.query.count() == 0:
        topics = [
            Topic(name="Variables y Tipos de Datos", description="Declaración, asignación y tipos de datos básicos (entero, real, cadena, lógico).", order=1, icon="📦"),
            Topic(name="Entrada y Salida", description="Lectura de datos del usuario y visualización de resultados.", order=2, icon="📥"),
            Topic(name="Estructuras Condicionales", description="Toma de decisiones con Si-Entonces-Sino.", order=3, icon="🔀"),
            Topic(name="Ciclos y Repeticiones", description="Estructuras repetitivas: Mientras, Para, Repetir-Hasta.", order=4, icon="🔄"),
            Topic(name="Arreglos", description="Manejo de colecciones de datos con vectores y matrices.", order=5, icon="📊"),
        ]
        db.session.add_all(topics)
        db.session.commit()


EXERCISES_SEED = [
    # ── Tema 1: Variables ──
    dict(topic_id=1, title="Hola Mundo", description="Escribe un algoritmo que muestre el mensaje 'Hola Mundo' en pantalla.", difficulty="basico", hints="Usa la instrucción 'Escribir' para mostrar texto en pantalla."),
    dict(topic_id=1, title="Suma de dos números", description="Escribe un algoritmo que lea dos números enteros, los sume y muestre el resultado.", difficulty="basico", hints="Necesitas: definir dos variables, leer sus valores con 'Leer' y mostrar la suma con 'Escribir'."),
    dict(topic_id=1, title="Área del círculo", description="Escribe un algoritmo que lea el radio de un círculo y calcule su área (π × r²). Usa 3.1416 como valor de π.", difficulty="basico", hints="Define una variable para el radio, calcula area <- 3.1416 * radio * radio."),
    dict(topic_id=1, title="Conversión de temperatura", description="Escribe un algoritmo que lea una temperatura en grados Celsius y la convierta a Fahrenheit. Fórmula: F = C × 9/5 + 32.", difficulty="basico", hints="Lee la variable celsius y calcula fahrenheit <- celsius * 9 / 5 + 32."),
    dict(topic_id=1, title="Intercambio de variables", description="Escribe un algoritmo que lea dos números A y B, intercambie sus valores y los muestre. Al final A debe tener el valor de B y viceversa.", difficulty="intermedio", hints="Necesitas una tercera variable auxiliar: aux <- A, luego A <- B, luego B <- aux."),
    # ── Tema 2: Entrada y salida ──
    dict(topic_id=2, title="Saludo personalizado", description="Escribe un algoritmo que pregunte el nombre del usuario y lo salude con el mensaje 'Hola, [nombre]! Bienvenido a CodeLogic'.", difficulty="basico", hints="Define una variable Como Cadena, léela con 'Leer' y únela al mensaje en el 'Escribir'."),
    dict(topic_id=2, title="Datos personales", description="Escribe un algoritmo que lea el nombre, la edad y la ciudad de una persona, y luego muestre los tres datos en una sola línea con un formato claro.", difficulty="basico", hints="Usa tres 'Leer' seguidos y un solo 'Escribir' combinando textos y variables con comas."),
    dict(topic_id=2, title="Promedio de dos números", description="Escribe un algoritmo que lea dos números reales y muestre su promedio.", difficulty="basico", hints="El promedio es (a + b) / 2. Define las variables Como Real."),
    # ── Tema 3: Condicionales ──
    dict(topic_id=3, title="Mayor de edad", description="Escribe un algoritmo que lea la edad de una persona y determine si es mayor o menor de edad (18 años).", difficulty="basico", hints="Usa Si edad >= 18 Entonces ... Sino ... FinSi"),
    dict(topic_id=3, title="Número mayor", description="Escribe un algoritmo que lea tres números y determine cuál es el mayor.", difficulty="intermedio", hints="Puedes comparar los números de dos en dos usando condicionales anidados."),
    dict(topic_id=3, title="Par o impar", description="Escribe un algoritmo que lea un número entero y determine si es par o impar.", difficulty="basico", hints="Un número es par si el residuo de dividirlo entre 2 es cero: n % 2 = 0 (en PSeInt: n MOD 2 = 0)."),
    dict(topic_id=3, title="Positivo, negativo o cero", description="Escribe un algoritmo que lea un número y clasifique si es positivo, negativo o cero.", difficulty="basico", hints="Necesitas un Si con tres caminos: Si n > 0 ... Sino Si n < 0 ... Sino ... FinSi."),
    dict(topic_id=3, title="Calculadora simple", description="Escribe un algoritmo que lea dos números y un símbolo de operación (+, -, *, /) y muestre el resultado de la operación elegida. Si se divide entre cero, muestra un mensaje de error.", difficulty="intermedio", hints="Lee la operación Como Cadena y usa condicionales para decidir qué cálculo hacer. Recuerda validar la división entre cero."),
    dict(topic_id=3, title="Descuento de tienda", description="Una tienda ofrece 20% de descuento si la compra supera $100.000 y 10% si supera $50.000. Escribe un algoritmo que lea el valor de la compra y muestre cuánto debe pagar el cliente.", difficulty="intermedio", hints="Evalúa primero la condición del monto más alto. total <- compra - compra * 0.20."),
    # ── Tema 4: Ciclos ──
    dict(topic_id=4, title="Tabla de multiplicar", description="Escribe un algoritmo que lea un número y muestre su tabla de multiplicar del 1 al 10.", difficulty="basico", hints="Usa un ciclo Para desde 1 hasta 10."),
    dict(topic_id=4, title="Suma de N números", description="Escribe un algoritmo que lea N números y calcule su suma total. Primero debe pedir cuántos números va a ingresar.", difficulty="intermedio", hints="Primero lee N, luego usa un ciclo Para que se repita N veces, acumulando cada número en una variable suma."),
    dict(topic_id=4, title="Contador regresivo", description="Escribe un algoritmo que lea un número entero positivo y muestre la cuenta regresiva desde ese número hasta 1, y al final escriba '¡Despegue!'.", difficulty="basico", hints="Puedes usar Para i <- n Hasta 1 Con Paso -1, o un Mientras restando 1 en cada vuelta."),
    dict(topic_id=4, title="Suma de pares", description="Escribe un algoritmo que calcule y muestre la suma de todos los números pares entre 2 y 100.", difficulty="intermedio", hints="Usa Para i <- 2 Hasta 100 Con Paso 2 y acumula en una variable suma."),
    dict(topic_id=4, title="Factorial", description="Escribe un algoritmo que lea un número entero positivo N y calcule su factorial (N! = 1 × 2 × ... × N).", difficulty="avanzado", hints="Inicia factorial <- 1 y multiplícalo por cada i de un ciclo Para desde 1 hasta N."),
    dict(topic_id=4, title="Promedio de notas con ciclo", description="Escribe un algoritmo que lea cuántas notas tiene el estudiante, luego lea cada nota, y muestre el promedio y si aprobó (promedio >= 3.0).", difficulty="intermedio", hints="Acumula las notas en una suma dentro del ciclo y divide por la cantidad al final. Después usa un Si para el mensaje."),
    # ── Tema 5: Arreglos ──
    dict(topic_id=5, title="Promedio de notas", description="Escribe un algoritmo que almacene 5 notas en un arreglo, calcule el promedio y lo muestre.", difficulty="intermedio", hints="Declara un arreglo con Dimension notas[5], llénalo con un ciclo, suma todas las notas y divide entre 5."),
    dict(topic_id=5, title="Mayor de un arreglo", description="Escribe un algoritmo que lea 6 números en un arreglo y encuentre cuál es el mayor.", difficulty="intermedio", hints="Guarda el primer elemento como 'mayor' y recorre el resto comparando: Si arreglo[i] > mayor Entonces mayor <- arreglo[i]."),
    dict(topic_id=5, title="Contar aprobados", description="Escribe un algoritmo que lea las notas de 8 estudiantes en un arreglo y cuente cuántos aprobaron (nota >= 3.0) y cuántos reprobaron.", difficulty="intermedio", hints="Usa dos contadores y un Si dentro del ciclo que recorre el arreglo."),
    dict(topic_id=5, title="Invertir un arreglo", description="Escribe un algoritmo que lea 5 números en un arreglo y los muestre en orden inverso al que fueron ingresados.", difficulty="avanzado", hints="Recorre el arreglo desde la última posición hasta la primera: Para i <- 5 Hasta 1 Con Paso -1."),
]


def seed_exercises():
    """Sembrar ejercicios. Idempotente: solo agrega los que falten (por título)."""
    existing = {e.title for e in Exercise.query.all()}
    new = [Exercise(**data) for data in EXERCISES_SEED if data["title"] not in existing]
    if new:
        db.session.add_all(new)
        db.session.commit()


def create_admin():
    """Crear usuario docente por defecto.

    La contraseña sale del .env (ADMIN_PASSWORD). Si no está definida se genera
    una aleatoria y se imprime UNA sola vez, al crear la cuenta.
    Nunca una contraseña fija en el código: esta cuenta ve los datos de todos
    los estudiantes y las exportaciones CSV de la investigación.
    """
    if User.query.filter_by(role="docente").first():
        return

    email = os.getenv("ADMIN_EMAIL", "docente@iup.edu.co").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "").strip()
    generated = False
    if not password:
        password = secrets.token_urlsafe(16)
        generated = True

    admin = User(name="Docente IUP", email=email, role="docente")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    if generated:
        print(
            "\n" + "=" * 62 +
            f"\n  CUENTA DOCENTE CREADA\n"
            f"  correo:     {email}\n"
            f"  contraseña: {password}\n"
            "  Guárdala ahora: no se vuelve a mostrar.\n"
            "  Cámbiala desde el perfil tras el primer ingreso.\n"
            + "=" * 62 + "\n"
        )
    else:
        print(f"✅ Usuario docente creado: {email} (contraseña tomada del .env)")


# ─── INIT EN IMPORT (también bajo gunicorn) ────────────────────────
# create_all() es idempotente pero puede racear si N workers arrancan a la vez
# y la tabla aún no existe → uno la crea, el otro pisa con "1050 already exists".
with app.app_context():
    try:
        db.create_all()
        # Seeds idempotentes: también aplican bajo gunicorn/flask run,
        # no solo con `python app.py`.
        seed_topics()
        seed_exercises()
        create_admin()
    except Exception as _init_e:
        app.logger.warning(f"db.create_all() race (ignorable si tablas ya existen): {_init_e}")
        db.session.rollback()

# ─── MAIN ───────────────────────────────────────────────────────────

# ─── Paso de predicción ──────────────────────────────────────────────
#
# Antes de resolver, el estudiante predice qué imprime el ejemplo ya
# resuelto. Leer un ejemplo no enseña; predecir su salida sí: si acierta
# confirma su modelo mental, y si falla ve exactamente dónde lo tenía roto.
#
# No puntúa. Es formativo, y lo que importa para la investigación es la
# tasa de acierto, que queda registrada en cada intento.

def _normalizar_salida(texto):
    """Deja la salida comparable sin ser permisivo de más.

    Se ignoran mayúsculas, tildes y espacios de sobra, porque escribir
    "3 x 1 = 3" o "3x1=3" demuestra el mismo entendimiento. NO se ignora el
    orden de las líneas: en un ciclo, el orden es justo lo que se evalúa.
    """
    lineas = []
    for linea in (texto or "").splitlines():
        l = unicodedata.normalize("NFKD", linea.lower())
        l = "".join(c for c in l if not unicodedata.combining(c))
        l = " ".join(l.split())
        l = l.replace(" = ", "=").replace(" x ", "x").replace(" , ", ",")
        l = l.rstrip(".")
        if l:
            lineas.append(l)
    return "\n".join(lineas)


def _numeros(texto):
    return re.findall(r"-?\d+(?:\.\d+)?", texto or "")


@app.route("/prediccion/<int:exercise_id>", methods=["POST"])
@login_required
def prediccion(exercise_id):
    ejercicio = Exercise.query.get_or_404(exercise_id)
    esperada = ejercicio.ejemplo_salida or ""
    if not esperada:
        return jsonify({"error": "Este ejercicio todavía no tiene predicción."}), 400

    datos = request.get_json(silent=True) or {}
    prediccion_texto = (datos.get("prediccion") or "").strip()
    if not prediccion_texto:
        return jsonify({"error": "Escribe qué crees que imprime antes de comprobar."}), 400
    if len(prediccion_texto) > 2000:
        return jsonify({"error": "Respuesta demasiado larga."}), 400

    if _normalizar_salida(prediccion_texto) == _normalizar_salida(esperada):
        resultado = "correcto"
    elif _numeros(prediccion_texto) == _numeros(esperada) and _numeros(esperada):
        # Los números salen bien pero el texto no: entendió el cálculo.
        resultado = "casi"
    else:
        resultado = "incorrecto"

    log_activity("prediccion", {
        "exercise_id": exercise_id,
        "resultado": resultado,
        "prediccion": prediccion_texto[:500],
    })

    return jsonify({
        "resultado": resultado,
        "salida_real": esperada,
        "mensaje": {
            "correcto": "Correcto. Tu idea de lo que hace el programa encaja con lo que hace.",
            "casi": "Casi: los números están bien, el texto no coincide del todo. "
                    "Compara con la salida real y fíjate en qué cambia.",
            "incorrecto": "No coincide. Mira la salida real y vuelve al ejemplo "
                          "línea por línea: ahí está lo que se te escapó.",
        }[resultado],
    })


def _ya_predijo(exercise_id):
    """¿Este estudiante ya predijo en este ejercicio alguna vez?

    Se pide obligatoriamente la primera vez, para que nadie se salte el
    paso. Si vuelve al ejercicio, ya no se le exige otra vez.
    """
    if not current_user.is_authenticated:
        return True
    # details es una columna JSON: se consulta por su ruta, no con LIKE
    # sobre el texto, que dependeria de como MySQL serialice el JSON.
    return (ActivityLog.query
            .filter_by(user_id=current_user.id, action="prediccion")
            .filter(func.json_extract(ActivityLog.details, "$.exercise_id") == exercise_id)
            .first() is not None)


if __name__ == "__main__":
    with app.app_context():
        print("✅ Base de datos inicializada correctamente.")
        print(f"🚀 Servidor iniciando en http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")

    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
