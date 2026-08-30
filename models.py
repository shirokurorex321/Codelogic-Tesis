from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum("estudiante", "docente", "admin"), default="estudiante")
    group = db.Column(db.Enum("A", "B"), nullable=True)  # Grupo experimental
    semester = db.Column(db.String(10), default="2026-II")
    prior_experience = db.Column(db.Boolean, default=False)
    gpa_entry = db.Column(db.Float, nullable=True)  # Promedio de ingreso
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # ── Verificación de correo ──
    # Sin confirmar el correo la cuenta no sirve: así se garantiza que quien se
    # registra es dueño real de esa dirección institucional, y no alguien
    # inventando cuentas @itp.edu.co.
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(64), unique=True, nullable=True)
    verification_sent_at = db.Column(db.DateTime, nullable=True)
    verification_expires_at = db.Column(db.DateTime, nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    # ── Recuperación de contraseña ──
    # Vida corta a propósito (1 hora): un enlace de restablecimiento vale tanto
    # como la contraseña misma, así que cuanto menos tiempo exista, mejor.
    reset_token = db.Column(db.String(64), unique=True, nullable=True)
    reset_sent_at = db.Column(db.DateTime, nullable=True)
    reset_expires_at = db.Column(db.DateTime, nullable=True)

    # ── Consentimiento informado ──
    # Exigido por la Ley 1581 de 2012 y el Decreto 1377 de 2013 (datos personales)
    # y por la Resolución 8430 de 1993 (investigación con seres humanos).
    # Se guarda el momento y la versión del texto aceptado, para poder demostrar
    # ante el comité de ética QUÉ aceptó cada participante y CUÁNDO.
    consent_accepted = db.Column(db.Boolean, default=False, nullable=False)
    consent_at = db.Column(db.DateTime, nullable=True)
    consent_version = db.Column(db.String(20), nullable=True)

    submissions = db.relationship("Submission", backref="student", lazy="dynamic")
    logs = db.relationship("ActivityLog", backref="user", lazy="dynamic")
    test_results = db.relationship("TestResult", backref="student", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Topic(db.Model):
    """Temas del curso: variables, condicionales, ciclos, arreglos"""
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    icon = db.Column(db.String(50), default="📘")

    # ── Semestre al que pertenece el tema ──
    # La plataforma sirve a DOS asignaturas distintas que comparten temario
    # (variables, condicionales, ciclos, vectores) pero no alumnos. Cada
    # tema es de un semestre y no se mezclan en ninguna vista: un tema de
    # 3er semestre no aparece nunca en el listado de 1ro, ni al reves.
    semestre = db.Column(db.Integer)             # 1 o 3

    # ── Unidad del plan de asignatura (estatuto de 2026, 1er semestre) ──
    # Los temas existian antes que las unidades y no se tocaron: la unidad se
    # les puso encima, para que la plataforma hable el mismo idioma que el
    # temario sin renombrar ni mover nada de lo ya creado.
    unidad = db.Column(db.Integer)               # 1, 2 o 3
    unidad_nombre = db.Column(db.String(150))    # titulo de la unidad
    nivel = db.Column(db.String(150))            # nivel de profundizacion

    # ── Lección del tema ──
    # Antes de esta adición, el estudiante pasaba de una descripción de una línea
    # directamente a programar. La tesis sostiene que ese salto sin andamiaje es
    # una de las causas del fracaso en cursos introductorios, así que la
    # plataforma debe enseñar el concepto antes de pedir que se aplique.
    # El texto de la leccion vive en lecciones.py, que es su unica fuente.
    # Aqui hubo cinco columnas leccion_* con una copia; se retiraron el
    # 28/08/2026 porque las dos copias se separaron dos veces y cada pagina
    # mostraba una version distinta del mismo tema.

    exercises = db.relationship("Exercise", backref="topic", lazy="dynamic")


class Exercise(db.Model):
    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.Enum("basico", "intermedio", "avanzado"), default="basico")
    hints = db.Column(db.Text)  # Pistas para el estudiante
    expected_pseudocode = db.Column(db.Text)  # Solución de referencia

    # ── Guía del ejercicio ──
    concepto = db.Column(db.Text)          # qué se practica aquí
    pasos = db.Column(db.Text)             # pasos sugeridos, uno por línea
    ejemplo_resuelto = db.Column(db.Text)  # un caso parecido ya resuelto

    # ── Paso de prediccion ──
    # Antes de ver que hace el ejemplo, el estudiante predice su salida.
    # La salida guardada no esta escrita a mano: se obtuvo ejecutando cada
    # ejemplo traducido a Python.
    ejemplo_entrada = db.Column(db.String(200))   # datos que se suponen tecleados
    ejemplo_salida = db.Column(db.Text)
    # Orden pedagogico dentro de su dificultad. Sin esto se ordenaba por id,
    # asi que un ejercicio anadido despues salia al final aunque enseñara lo
    # primero: en Selección el Segun-Hacer aparecia antes que el Si, que es lo
    # que la leccion explica primero. 0 = sin preferencia (se ordena por id).
    orden = db.Column(db.Integer, default=0, nullable=False)           # lo que imprime de verdad
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    submissions = db.relationship("Submission", backref="exercise", lazy="dynamic")


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercises.id"), nullable=True)
    pseudocode = db.Column(db.Text, nullable=False)
    converted_python = db.Column(db.Text)
    converted_cpp = db.Column(db.Text)
    converted_php = db.Column(db.Text)
    ai_feedback = db.Column(db.Text)
    score = db.Column(db.Float, nullable=True)  # 0-100
    attempt_number = db.Column(db.Integer, default=1)
    time_spent_seconds = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class ActivityLog(db.Model):
    """Registros de actividad para la investigación"""
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # login, submit, convert, feedback, etc.
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class GastoIA(db.Model):
    """Libro de gasto de la IA, a proposito SIN clave foranea a users.

    ActivityLog si la tiene, y codelogic-admin borra los registros hijos antes
    de borrar una cuenta. El 23/08/2026 borre 40 cuentas de prueba y con ellas
    se fue todo el historial de consumo, justo cuando hacia falta para cuadrar
    la factura. El gasto ya ocurrio y hay que rendir cuentas de el aunque el
    alumno se de de baja, asi que aqui user_id es un entero suelto: si la
    cuenta desaparece la linea de gasto se queda.

    tokens_salida guarda la salida FACTURABLE (total - entrada). Los tokens de
    razonamiento se cobran como salida pero no aparecen en completion_tokens,
    asi que usar ese campo subestima el gasto unas tres veces.
    """
    __tablename__ = "gasto_ia"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)        # sin ForeignKey, a proposito
    operacion = db.Column(db.String(20), nullable=False, index=True)
    proveedor = db.Column(db.String(20))
    modelo = db.Column(db.String(60))
    tokens_entrada = db.Column(db.Integer, default=0, nullable=False)
    tokens_salida = db.Column(db.Integer, default=0, nullable=False)   # facturable
    coste_usd = db.Column(db.Numeric(12, 8), default=0, nullable=False)
    desde_cache = db.Column(db.Boolean, default=False, nullable=False)
    exercise_id = db.Column(db.Integer, index=True)
    created_at = db.Column(db.DateTime, index=True,
                           default=lambda: datetime.now(timezone.utc))


class AICache(db.Model):
    """Caché persistente de respuestas de IA (convert / feedback / explain).
    Evita llamadas duplicadas cuando el input es idéntico → ahorra tokens y rate-limit."""
    __tablename__ = "ai_cache"

    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(64), nullable=False, index=True)  # sha256 hex
    endpoint = db.Column(db.String(20), nullable=False)  # convert | feedback | explain
    response = db.Column(db.JSON, nullable=False)
    hit_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("cache_key", "endpoint", name="uq_ai_cache_key_endpoint"),
    )


class TestResult(db.Model):
    """Resultados de pretest y postest"""
    __tablename__ = "test_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    test_type = db.Column(db.Enum("pretest", "postest"), nullable=False)
    score = db.Column(db.Float, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    answers_json = db.Column(db.JSON)  # Respuestas detalladas
    time_spent_seconds = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class SelfEfficacyResult(db.Model):
    """Resultados de la escala de autoeficacia"""
    __tablename__ = "self_efficacy_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    test_type = db.Column(db.Enum("pre", "post"), nullable=False)
    responses_json = db.Column(db.JSON)  # Respuestas individuales por ítem
    total_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class CognitiveLoadResult(db.Model):
    """Carga cognitiva percibida — escala de 3 ítems (1 a 9) basada en Paas (1992).

    Es una de las cuatro variables dependientes de la hipótesis. A diferencia del
    pretest/postest, se aplica DESPUÉS DE CADA ACTIVIDAD PRÁCTICA, por lo que se
    vincula al ejercicio concreto que la originó.
    """
    __tablename__ = "cognitive_load_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercises.id"), nullable=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=True)
    responses_json = db.Column(db.JSON)   # {item_id: 1..9}
    mean_score = db.Column(db.Float)      # media de los 3 ítems
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
