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

    # ── Clave provisional ──
    # Las cuentas que crea el docente desde el servidor nacen con una
    # contrasena igual para toda la clase, y como su correo no se verifica,
    # "recuperar clave" no les sirve. Mientras esto sea cierto la cuenta no
    # hace nada mas que cambiarla: la clave de partida la sabe todo el mundo.
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)

    # ── Ultima vez que se le vio ──
    # El registro de actividad solo apunta acciones (convertir, entregar...):
    # quien pasa veinte minutos escribiendo en el editor no deja rastro y el
    # docente lo veia "desconectado". Esto se renueva con cualquier peticion,
    # como mucho una vez por minuto.
    ultima_vez = db.Column(db.DateTime, nullable=True)

    submissions = db.relationship("Submission", backref="student", lazy="dynamic")
    logs = db.relationship("ActivityLog", backref="user", lazy="dynamic")
    test_results = db.relationship("TestResult", backref="student", lazy="dynamic")

    # ── Nombre de pila ──
    # Las cuentas de la clase guardan el nombre como en la lista oficial,
    # apellidos primero ("Ramirez Vargas Ana Lucia"), que es como el
    # docente busca a sus estudiantes. Pero saludar con la primera palabra
    # decia "Hola, Ramirez". Esto guarda el nombre para tratar al estudiante.
    nombre_pila = db.Column(db.String(60), nullable=True)

    # ── Asignatura que cursa ──
    # La plataforma sirve a dos asignaturas (1er y 3er semestre) y a cada
    # estudiante se le ensenaban las dos: diez temas, la mitad de otra
    # materia. Con esto ve solo la suya. None = ve las dos (quien se registra
    # por su cuenta, hasta que el docente lo asigne).
    semestre_curso = db.Column(db.Integer, nullable=True)

    # ── Fuera del estudio ──
    # Cuentas de prueba (las del propio autor, la de pruebas automaticas).
    # Siguen funcionando, pero no cuentan como participantes: no entran en el
    # panel de investigacion ni en las exportaciones, y no se les exige el
    # pretest.
    excluido_estudio = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def nombre_corto(self):
        """Como se le saluda: su nombre de pila, o la primera palabra del
        nombre en las cuentas que se registraron solas ("Brayan Torres")."""
        if self.nombre_pila:
            return self.nombre_pila.title()
        partes = (self.name or "").split()
        if not partes:
            return ""
        # Con la inicial en mayuscula: quien se registro como "daniel rosero"
        # veia "Hola, daniel".
        return partes[0][:1].upper() + partes[0][1:]

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
    orden = db.Column(db.Integer, default=0, nullable=False)
    # Que se le pide al estudiante:
    #   "escribir" — el de siempre: le dan un enunciado y escribe el algoritmo.
    #   "leer"     — le dan el algoritmo YA ESCRITO y dice que imprime. Primer
    #                semestre tiene que aprender a LEER pseudocodigo, no solo a
    #                escribirlo, y hasta ahora no habia forma de practicarlo.
    # Se corrige comparando la salida, sin gastar una sola llamada de IA.
    tipo = db.Column(db.String(12), default="escribir", nullable=False)
    # Diagrama de flujo en sintaxis Mermaid, para los ejercicios de tipo
    # "diagrama": se le enseña el diagrama y el escribe el pseudocodigo que le
    # corresponde. El plan de asignatura habla de "tecnicas de representacion"
    # en plural, pero hasta ahora solo se iba en un sentido: del pseudocodigo
    # al diagrama, nunca al reves.
    diagrama = db.Column(db.Text)           # lo que imprime de verdad
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
    # Orden en que se le mostraron las opciones a ESTE estudiante. Sin esto no
    # se puede reconstruir despues que vio cada uno, y el analisis por item
    # (dificultad, discriminacion) quedaria sin base.
    ordenes_json = db.Column(db.JSON)
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


class Borrador(db.Model):
    """Lo que el estudiante lleva escrito en el editor, aunque no lo entregue.

    Antes el borrador vivia en el localStorage del navegador: se perdia al
    cambiar de equipo, y en una sala de computadores compartidos el siguiente
    alumno que abria el mismo ejercicio se encontraba el trabajo del anterior.
    Ahora es del estudiante, no del navegador: vuelve al recargar, al cerrar
    sesion o al apagar el equipo, y solo lo ve el.

    `clave` es "ej-<id>" para un ejercicio y "libre" para el editor libre.
    """
    __tablename__ = "borradores"
    __table_args__ = (db.UniqueConstraint("user_id", "clave", name="uq_borrador_usuario_clave"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    clave = db.Column(db.String(20), nullable=False)
    pseudocodigo = db.Column(db.Text, nullable=False)
    actualizado = db.Column(db.DateTime, nullable=False,
                            default=lambda: datetime.now(timezone.utc))

    @property
    def ms(self):
        """Hora de guardado en milisegundos. La base la devuelve sin zona y
        se guarda en UTC: sin decirlo, .timestamp() usaria la zona del proceso."""
        f = self.actualizado
        if f.tzinfo is None:
            f = f.replace(tzinfo=timezone.utc)
        return int(f.timestamp() * 1000)
