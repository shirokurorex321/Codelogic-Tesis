import hashlib
import logging
import json
import re
import time
from datetime import datetime, timezone
import requests
from google import genai
from google.genai import types
from config import Config
from models import db, AICache

# ── Gemini (fallback) ───────────────────────────────────────────
_gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None
# Lista de modelos, en orden de preferencia. GEMINI_MODEL es el primero y se
# mantiene como variable suelta porque el resto del modulo la usa.
#
# Por que gemini-3.5-flash-lite el primero: con facturacion activa cada
# llamada cuesta, y un Flash normal sale ~5 veces mas caro que un Lite. Medido
# sobre el consumo real de esta plataforma: el pilotaje entero son ~39.000 COP
# con Flash frente a ~7.400 con Lite. Y se comprobo que la calidad aguanta —
# calificando el mismo ejercicio correcto, con error y con basura, el Lite da
# 100/85/5 frente al 100/95/5 del caro: misma discriminacion, y penaliza algo
# mas el error, que para ensenar viene bien.
#
# Por que una lista y no uno solo: los modelos se caen (el 20/08 uno devolvio
# 503) y se retiran con el tiempo. Si el primero falla se prueba el siguiente
# en vez de dejar al estudiante sin respuesta.
# Registro propio con salida a stderr, que gunicorn recoge al diario del
# servicio. No basta con getLogger: el logger raiz de esta aplicacion no tiene
# manejadores, asi que Python cae en el "de ultimo recurso" y los mensajes se
# pierden. Sin esto, quedarse sin cuota no dejaba ni rastro: el 20/08/2026 el
# diario marcaba cero incidencias mientras los estudiantes veian el error en
# pantalla.
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[ia] %(levelname)s %(message)s"))
    logger.addHandler(_h)


MODELOS_GEMINI = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3-flash-preview",
]
GEMINI_MODEL = MODELOS_GEMINI[0]
THINKING_LEVEL = "HIGH"

# Precio real de gemini-3.5-flash-lite (23/08/2026): 0,30 USD por millon de
# entrada y 2,50 por millon de salida. Google avisa en su tabla que el precio
# de salida "incluye los tokens de razonamiento", y esos tokens NO aparecen en
# completion_tokens: solo se ven restando prompt_tokens al total_tokens. Para
# contar el gasto hay que usar (total - prompt) como salida, nunca completion.
#
# Nivel de razonamiento por operacion. Calificar era el peor derrochador:
# 31.142 tokens de razonamiento para producir 2.752 de respuesta; convertir,
# 136.813 para 31.424. Medido con 12 casos de error sutil (off-by-one, maximo
# que falla con negativos, acumulador sin inicializar, Euclides sin variable
# temporal) y 6 conversiones ejecutadas de verdad contra su salida esperada,
# LOW acierta lo mismo que HIGH. Explicar y retroalimentar apenas razonan
# (63 tokens por llamada), asi que ahi no hay nada que ahorrar.
# Precio por millon de tokens, por modelo (USD, consultado el 23/08/2026 en
# ai.google.dev/gemini-api/docs/pricing). La rotacion puede caer en un modelo
# mas caro que el preferido, asi que el gasto se calcula con el que respondio
# de verdad, no con el primero de la lista. OpenCode Zen no cobra por token.
PRECIOS_POR_MILLON = {
    "gemini-3.5-flash-lite":   (0.30, 2.50),
    "gemini-flash-lite-latest": (0.30, 2.50),
    "gemini-3-flash-preview":  (0.50, 3.00),
}
PRECIO_POR_DEFECTO = (0.50, 3.00)   # ante la duda, el mas caro conocido


def coste_usd(usage: dict) -> float:
    """Cuanto costo una llamada, en dolares, a partir de su usage.

    La salida facturable es total - entrada, NO completion_tokens: los tokens
    de razonamiento se cobran como salida pero no aparecen en completion.
    """
    if not usage or usage.get("provider") != "gemini":
        return 0.0
    entrada = int(usage.get("prompt_tokens") or 0)
    total = int(usage.get("total_tokens") or 0)
    salida = max(total - entrada, 0)
    p_in, p_out = PRECIOS_POR_MILLON.get(usage.get("model"), PRECIO_POR_DEFECTO)
    return entrada / 1e6 * p_in + salida / 1e6 * p_out


def salida_facturable(usage: dict) -> int:
    if not usage:
        return 0
    return max(int(usage.get("total_tokens") or 0) - int(usage.get("prompt_tokens") or 0), 0)
# Medido caso por caso, no supuesto. Convertir, calificar y diagramar son
# transformaciones con respuesta verificable: LOW acierta igual que HIGH
# (12 casos de error sutil al calificar, 6 conversiones ejecutadas de verdad,
# 5 diagramas comprobados nodo a nodo) y cuesta entre 8 y 23 veces menos.
#
# Retroalimentar es lo contrario y se queda en HIGH a proposito: con 8 casos
# y un juez a ciegas, HIGH gana 6-2 tanto contra LOW como contra MEDIUM.
# Detecta el mismo error, pero lo explica mejor, y esa explicacion es justo
# lo que el estudiante viene a buscar. Cuesta 16 COP por llamada frente a 5;
# se paga a sabiendas. El 30/08/2026 se probo bajarla y se descarto.
THINKING_POR_OPERACION = {
    "convert": "LOW",
    "grade": "LOW",
    "diagram": "LOW",
    "explain": THINKING_LEVEL,
    "feedback": THINKING_LEVEL,
}

# ── OpenCode Zen (primario) ─────────────────────────────────────
OPENCODE_KEY = Config.OPENCODE_API_KEY
OPENCODE_URL = Config.OPENCODE_BASE_URL.rstrip("/")
OPENCODE_MODEL = Config.OPENCODE_MODEL                    # fallback general
OPENCODE_MODEL_CONVERT = Config.OPENCODE_MODEL_CONVERT    # convert → MiniMax
OPENCODE_MODEL_TUTOR = Config.OPENCODE_MODEL_TUTOR        # feedback + explain → DeepSeek
REQUEST_TIMEOUT = 60

CONVERSION_SYSTEM_PROMPT = """Eres un asistente educativo experto en programación. Tu tarea es convertir pseudocódigo escrito en español a código funcional.

REGLAS IMPORTANTES:
1. El pseudocódigo está escrito en español por estudiantes principiantes.
2. Debes generar código limpio, bien comentado en español y funcional.
3. Usa nombres de variables descriptivos en español cuando sea posible.
4. Agrega comentarios explicativos breves en español.
5. El pseudocódigo es informal POR DEFINICIÓN: existe para que el estudiante piense la lógica sin pelearse con la sintaxis. Interpreta SIEMPRE lo que quiso decir y tradúcelo a código que funcione. "sumar a y b" es una suma y debes escribirla; "Definir 2 numeros a, b" declara a y b; mayúsculas/minúsculas, tildes, comillas simples o dobles y sinónimos (escribir/mostrar/imprimir, Leer/Ingresar) son equivalentes. NADA de esto es un error: para el estudiante esas formas son correctas, así que NO las comentes ni las corrijas.
5b. NO "mejores" los números que escribió el estudiante. Si el pseudocódigo dice 3.1416, el código debe decir 3.1416, NUNCA math.pi, M_PI ni pi(). El estudiante compara el resultado con lo que calculó a mano y un valor distinto le hace creer que se equivocó.
5c. Comenta algo SOLO si la intención es genuinamente ambigua (dos lecturas razonables) o si falta algo sin lo cual el programa no puede funcionar. En ese caso implementa la lectura más probable —nunca dejes el programa a medias— y explica tu elección en UNA línea, en tono de tutor que acompaña, jamás de corrector que señala. No uses la palabra "error" para hablar del estilo de escritura.
6. Estructura típica del pseudocódigo (ORIENTACIÓN para que la reconozcas, NO un formato obligatorio: el estudiante puede expresar lo mismo de otras maneras igual de válidas):
   - "Algoritmo" o "Proceso" = inicio del programa
   - "Definir X Como Entero/Real/Cadena/Logico" = declaración de variables
   - "Escribir" = imprimir/mostrar en pantalla
   - "Leer" = leer entrada del usuario
   - "Si ... Entonces ... Sino ... FinSi" = condicional
   - "Mientras ... Hacer ... FinMientras" = ciclo while
   - "Para X <- inicio Hasta fin Con Paso p Hacer ... FinPara" = ciclo for
   - "Dimension arreglo[N]" = declarar arreglo
   - "FinAlgoritmo" o "FinProceso" = fin del programa

Responde ÚNICAMENTE con el código convertido, sin explicaciones fuera de los comentarios del propio código."""

DIAGRAM_SYSTEM_PROMPT = """Eres un experto en diagramas de flujo que trabaja con estudiantes principiantes.
Conviertes pseudocodigo en un diagrama de flujo escrito en sintaxis Mermaid.

SIMBOLOGIA ESTANDAR — respetala exactamente, es lo que el estudiante debe aprender:
- Inicio y Fin        -> ovalo:         A(["Inicio"])
- Entrada y salida    -> paralelogramo: B[/"Leer edad"/]
- Proceso o asignacion-> rectangulo:    C["suma = a + b"]
- Decision            -> rombo:         D{"edad >= 18"}

REGLAS OBLIGATORIAS:
1. Empieza SIEMPRE con: flowchart TD
2. TODA etiqueta va entre comillas dobles: C["texto"]. Sin excepciones.
3. Dentro de las etiquetas escribe la asignacion con = (nunca <-, rompe el diagrama).
4. No uses parentesis, llaves ni corchetes DENTRO del texto de una etiqueta.
5. Las decisiones salen con -->|"Si"| y -->|"No"|.
6. Los ciclos se dibujan como una decision cuya rama de repetir vuelve a un nodo anterior.
7. Identificadores de nodo simples: A, B, C... o N1, N2. Nunca con tildes ni espacios.
8. Todo camino termina en un nodo Fin.

EJEMPLO de la forma esperada:
flowchart TD
    A(["Inicio"]) --> B[/"Leer edad"/]
    B --> C{"edad >= 18"}
    C -->|"Si"| D["mensaje = Es mayor"]
    C -->|"No"| E["mensaje = Es menor"]
    D --> F[/"Escribir mensaje"/]
    E --> F
    F --> G(["Fin"])

Responde UNICAMENTE con el codigo Mermaid, sin markdown, sin explicaciones, sin bloques con comillas triples."""

FEEDBACK_SYSTEM_PROMPT = """Eres un tutor de programación amigable y paciente que ayuda a estudiantes principiantes de la Institución Universitaria del Putumayo. Los estudiantes están aprendiendo algoritmos y pseudocódigo por primera vez.

Tu rol es:
1. Analizar el pseudocódigo del estudiante.
2. Identificar errores de lógica, estructura o sintaxis de pseudocódigo.
3. Explicar QUÉ está mal, DÓNDE está el error y CÓMO corregirlo.
4. Ser amigable y motivador. Nunca hagas sentir mal al estudiante.
5. Dar retroalimentación progresiva: primero lo positivo, luego lo que se puede mejorar.
6. Si el pseudocódigo es correcto, felicita al estudiante y sugiere posibles optimizaciones.

FORMATO DE RESPUESTA:
- Usa un lenguaje claro y sencillo en español.
- Usa emojis moderadamente para ser amigable (✅, ⚠️, 💡, 🎯).
- Estructura tu respuesta en secciones claras.
- Si hay errores, muestra el fragmento problemático y la corrección sugerida.
- Termina siempre con una palabra de aliento.

CONTEXTO DEL EJERCICIO (si se proporciona): Considera la descripción del ejercicio para evaluar si la solución del estudiante cumple con lo solicitado."""

FREE_MODE_SYSTEM_PROMPT = """Eres un tutor de programación amigable. El estudiante está practicando pseudocódigo libremente sin un ejercicio específico.

Analiza su pseudocódigo y:
1. Verifica que la estructura sea correcta.
2. Identifica si la lógica tiene sentido.
3. Sugiere mejoras si las hay.
4. Explica brevemente qué hace el algoritmo.

Sé breve, claro y motivador. Responde en español."""

EXPLAIN_SYSTEM_PROMPT = """Eres un tutor de programación que explica código a estudiantes principiantes en español.

Tu tarea: explicar de forma CONCISA, CLARA y PROPORCIONAL a la complejidad del código.

REGLAS DURAS:
- NO inventes secciones vacías. Si el código no importa nada, NO escribas "No se importa nada". Si no declara variables, NO escribas "No se declaran variables". Solo menciona lo que SÍ existe.
- NO abras con frases motivacionales ("¡Excelente que estés empezando!", "¡Qué buen trabajo!"). Ve al punto con tono profesional y amable.
- NO repitas el código completo dentro de un bloque ```...```. Cita fragmentos cortos con backticks inline (`así`).
- Adapta la longitud:
  • Código trivial (1-3 líneas) → 3-6 frases en total. NADA de subsecciones numeradas.
  • Código mediano → estructura con 2-3 secciones cortas.
  • Código complejo → expande con subsecciones.
- Usa markdown ligero: **negritas** para resaltar términos, `inline code` para nombres/símbolos del código, ## o ### para títulos solo si el código es mediano o complejo.
- Termina con **💡 Pista para crecer:** seguida de UNA sugerencia accionable concreta. Una sola. Sin lista.

ESTRUCTURA SUGERIDA según tamaño:
- TRIVIAL: párrafo único explicando qué hace + 1-2 viñetas sobre el concepto clave + 💡 pista.
- MEDIANO/COMPLEJO: ### Qué hace (1 frase) → ### Cómo funciona (paso a paso lo IMPORTANTE) → ### Conceptos clave (lista corta) → 💡 Pista."""


def explain_code(code: str, language: str) -> dict:
    """Explica en español qué hace un fragmento de código."""
    language_names = {"python": "Python", "cpp": "C++", "php": "PHP"}
    lang_name = language_names.get(language, language)

    prompt = f"""Explica el siguiente código de {lang_name} a un estudiante principiante:

```{language}
{code}
```"""

    # v2 = nuevo prompt más conciso (2026-05-12). Bumpear si vuelves a tocar el prompt.
    key = _cache_key("explain", "v2", NAMESPACE_CACHE, language, code.strip())
    cached = cache_get("explain", key)
    if cached:
        return {**cached, "cached": True}

    try:
        explanation, usage = _generate(EXPLAIN_SYSTEM_PROMPT, prompt, model=OPENCODE_MODEL_TUTOR, operacion="explain")
        result = {"success": True, "explanation": explanation, "usage": usage}
        cache_put("explain", key, result)
        return {**result, "cached": False}
    except Exception as e:
        return {"success": False, "error": str(e), "cached": False}


def _generate_opencode(system_instruction: str, user_prompt: str, model: str = None) -> str:
    """Llama a OpenCode Zen (formato OpenAI-compatible).
    Si `model` es None usa OPENCODE_MODEL (default histórico)."""
    if not OPENCODE_KEY:
        raise RuntimeError("OPENCODE_API_KEY no configurada")
    payload = {
        "model": model or OPENCODE_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt},
        ],
    }
    # Los modelos de razonamiento a veces gastan todo su presupuesto en
    # reasoning_content y devuelven content vacío. Sin este reintento la app
    # respondía success=True con texto vacío y lo guardaba en caché: el
    # estudiante veía el panel en blanco de forma permanente.
    ultimo_error = None
    for intento in range(2):
        r = requests.post(
            f"{OPENCODE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OPENCODE_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        text = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        if text:
            break
        ultimo_error = "el modelo devolvió una respuesta vacía"
    else:
        raise RuntimeError(ultimo_error or "respuesta vacía del modelo")

    u = data.get("usage", {}) or {}
    usage = {
        "model": payload["model"],
        "provider": "opencode",
        "prompt_tokens": int(u.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(u.get("completion_tokens", 0) or 0),
        "total_tokens": int(u.get("total_tokens", 0) or 0),
    }
    return text, usage


def _generate_gemini(system_instruction: str, user_prompt: str,
                     operacion: str = None):
    """Llama a Gemini probando los modelos de la lista en orden.

    Si uno esta caido o sin cuota se pasa al siguiente. Antes se usaba un
    unico modelo fijo: el 20/08/2026 se agoto su cupo diario y la plataforma
    se quedo sin retroalimentacion ni calificacion durante horas, mientras
    otros modelos seguian disponibles sin que nadie pudiera alcanzarlos.
    """
    if not _gemini_client:
        raise RuntimeError("GEMINI_API_KEY no configurada")
    ultimo = None
    for modelo in MODELOS_GEMINI:
        try:
            return _generar_con_modelo(modelo, system_instruction, user_prompt,
                                       operacion)
        except Exception as e:
            ultimo = e
            texto = str(e).lower()
            # Solo se pasa al siguiente si el problema es del modelo. Un fallo
            # de clave o de formato se repetiria igual en todos.
            if not any(t in texto for t in ("429", "resource_exhausted", "quota",
                                            "503", "unavailable", "404", "not found",
                                            "overloaded")):
                raise
            logger.warning("Gemini: %s no disponible (%s), probando el siguiente",
                           modelo, str(e)[:90])
    logger.error("Gemini: ningun modelo disponible. Ultimo error: %s", str(ultimo)[:200])
    raise ultimo


def _generar_con_modelo(GEMINI_MODEL: str, system_instruction: str, user_prompt: str,
                        operacion: str = None):
    nivel = THINKING_POR_OPERACION.get(operacion, THINKING_LEVEL)
    response = _gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(thinking_level=nivel),
        ),
    )
    text = (response.text or "").strip()
    meta = getattr(response, "usage_metadata", None)
    usage = {
        "model": GEMINI_MODEL,
        "provider": "gemini",
        "prompt_tokens": int(getattr(meta, "prompt_token_count", 0) or 0) if meta else 0,
        "completion_tokens": int(getattr(meta, "candidates_token_count", 0) or 0) if meta else 0,
        "total_tokens": int(getattr(meta, "total_token_count", 0) or 0) if meta else 0,
    }
    return text, usage


# Palabras clave de pseudocódigo (estilo PSeInt). Solo estas se normalizan a
# minúsculas para la clave de caché; los nombres de variables NO se tocan, para
# que el código devuelto siga correspondiendo a lo que escribió el estudiante.
_PALABRAS_CLAVE = {
    "algoritmo", "finalgoritmo", "proceso", "finproceso", "subproceso",
    "definir", "como", "entero", "real", "caracter", "cadena", "logico", "texto",
    "dimension", "leer", "escribir", "imprimir", "mostrar",
    "si", "entonces", "sino", "finsi",
    "para", "hasta", "con", "paso", "hacer", "finpara",
    "mientras", "finmientras", "repetir", "hasta que",
    "segun", "de", "otro", "modo", "finsegun", "caso",
    "y", "o", "no", "mod", "verdadero", "falso",
}

_ESPACIOS = re.compile(r"[ \t]+")
_TOKEN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ_][A-Za-zÁÉÍÓÚÜÑáéíóúüñ_0-9]*")


def normalizar_pseudocodigo(texto: str) -> str:
    """Normaliza pseudocódigo para la clave de caché.

    Dos estudiantes que escriben el MISMO algoritmo pero con distinta
    indentación, espaciado o mayúsculas en las palabras clave deben compartir
    la entrada de caché. Así una sola llamada a la IA sirve a muchos.

    Lo que se normaliza:
      - saltos de línea (CRLF/CR -> LF)
      - indentación y espacios repetidos -> un espacio
      - líneas en blanco -> se eliminan
      - mayúsculas SOLO de palabras clave del pseudocódigo

    Lo que NO se toca: nombres de variables, literales de texto ni números,
    porque cambiarlos haría que el código devuelto no coincida con el del
    estudiante.
    """
    if not texto:
        return ""
    t = texto.replace("\r\n", "\n").replace("\r", "\n")
    lineas = []
    for linea in t.split("\n"):
        linea = _ESPACIOS.sub(" ", linea).strip()
        if not linea:
            continue

        # Bajar a minúsculas solo las palabras clave, respetando literales "..."
        partes = []
        resto = linea
        while True:
            ini = resto.find('"')
            if ini == -1:
                partes.append((resto, False))
                break
            fin = resto.find('"', ini + 1)
            if fin == -1:
                partes.append((resto, False))
                break
            partes.append((resto[:ini], False))
            partes.append((resto[ini:fin + 1], True))   # literal: intacto
            resto = resto[fin + 1:]

        salida = []
        for frag, es_literal in partes:
            if es_literal:
                salida.append(frag)
            else:
                salida.append(_TOKEN.sub(
                    lambda m: m.group(0).lower()
                    if m.group(0).lower() in _PALABRAS_CLAVE else m.group(0),
                    frag))
        lineas.append("".join(salida))
    return "\n".join(lineas)


# Espacio de nombres de la cache. Es un valor CONGELADO, no un ajuste.
#
# Antes las claves se construian con OPENCODE_MODEL_TUTOR/CONVERT, que siguen
# siendo editables desde el panel. Pero OpenCode esta apagado desde el
# 27/08/2026 y hoy responde Gemini: ese ajuste ya no dice quien contesta, y sin
# embargo cambiarlo invalidaba de golpe las 647 entradas de cache y disparaba
# una racha de llamadas de pago. Alguien tocando un ajuste que "ya no hace
# nada" se llevaba por delante el ahorro de meses.
#
# El valor es el que tenian esas claves historicamente, para no perder ni una
# entrada. Solo hay que cambiarlo si se quiere invalidar la cache A PROPOSITO.
NAMESPACE_CACHE = "hy3-free"


def _cache_key(*parts: str) -> str:
    """SHA256 de los inputs concatenados con separador nulo (evita colisiones)."""
    raw = "\x00".join(p or "" for p in parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def cache_get(endpoint: str, key: str):
    """Devuelve el response cacheado o None.

    El contador de aciertos es SECUNDARIO y se actualiza aparte: si su commit
    falla (algo habitual cuando 40 estudiantes piden lo mismo a la vez y la
    fila entra en contención), el acierto de caché se respeta igual.

    Antes ambas cosas iban en el mismo try: al fallar el commit se hacía
    rollback y se devolvía None, así que la app creía que NO había caché y
    llamaba a la IA. La caché se caía justo cuando más falta hacía.
    """
    try:
        row = AICache.query.filter_by(cache_key=key, endpoint=endpoint).first()
    except Exception:
        db.session.rollback()
        return None

    if not row:
        return None

    respuesta = row.response          # se guarda ANTES de tocar la BD

    try:                              # actualizar el contador, best-effort
        row.hit_count = (row.hit_count or 0) + 1
        row.last_used_at = datetime.now(timezone.utc)
        db.session.commit()
    except Exception:
        db.session.rollback()         # da igual: el dato ya lo tenemos

    return respuesta


def _respuesta_util(response: dict) -> bool:
    """Una respuesta vacía no se guarda: cachearla condenaría a todos los
    estudiantes que envíen ese pseudocódigo a ver un panel en blanco."""
    if not isinstance(response, dict) or not response.get("success"):
        return False
    for campo in ("code", "feedback", "explanation", "diagram"):
        if campo in response:
            return len((response.get(campo) or "").strip()) >= 10
    return True


def cache_put(endpoint: str, key: str, response: dict):
    """Guarda en caché. Idempotente (si ya existe no falla)."""
    if not _respuesta_util(response):
        return
    try:
        existing = AICache.query.filter_by(cache_key=key, endpoint=endpoint).first()
        if existing:
            existing.response = response
            existing.last_used_at = datetime.now(timezone.utc)
        else:
            db.session.add(AICache(
                cache_key=key,
                endpoint=endpoint,
                response=response,
                hit_count=0,
            ))
        db.session.commit()
    except Exception:
        db.session.rollback()


# ── Respaldo de OpenCode: APAGADO ──────────────────────────────
# Se apaga el 27/08/2026 a peticion del usuario: sus modelos gratuitos tardaban
# 11,6 s de media con picos de 24,8 s, frente a los 0,9 s de Gemini, y en clase
# eso parece que la plataforma se colgo. El codigo se conserva entero y en el
# .env queda `OPENCODE_MODEL=hy3-free` (el unico gratuito que respondia bien),
# asi que para volver a activarlo basta con poner esto en True.
USAR_RESPALDO_OPENCODE = False


# Errores que se arreglan solos esperando: saturacion momentanea del proveedor.
# Un 400 o un fallo de clave NO estan aqui: repetirlos da exactamente lo mismo.
_TRANSITORIOS = ("429", "503", "502", "504", "timeout", "timed out",
                 "unavailable", "overloaded", "temporarily", "resource_exhausted")


def _es_transitorio(err) -> bool:
    texto = str(err).lower()
    return any(t in texto for t in _TRANSITORIOS)


# Lo que ve el estudiante cuando no hay forma de generar. El detalle tecnico va
# al log: "429 Client Error..." no le dice nada a quien esta aprendiendo a
# programar, y encima parece que rompio el la plataforma.
MENSAJE_IA_NO_DISPONIBLE = (
    "El asistente no esta disponible en este momento. "
    "Espera unos segundos y vuelve a intentarlo."
)


def _generate(system_instruction: str, user_prompt: str, model: str = None,
              operacion: str = None) -> str:
    """Genera con Gemini y, si no puede, cae al modelo gratuito de OpenCode.

    El orden importa y se midio el 27/08/2026: Gemini responde en 0,9 s de media
    (1,1 / 1,0 / 0,6) y el gratuito `hy3-free` en 11,6 s, con picos de 24,8 s.
    En una clase, esperar 25 s por una conversion hace que el estudiante crea
    que la plataforma se colgo, asi que manda la respuesta rapida y lo gratuito
    queda de red de seguridad.

    Gemini se reintenta porque el 26/08/2026 sus tres modelos dieron 503 a la
    vez unos segundos y la plataforma se quedo sin generar, cuando bastaba con
    volver a preguntar. OpenCode no se reintenta: cuando falla suele ser el cupo
    gratuito agotado, y esperar no lo arregla.
    """
    err_gemini = None
    if _gemini_client:
        for intento in range(3):
            try:
                return _generate_gemini(system_instruction, user_prompt, operacion)
            except Exception as e:
                err_gemini = e
                if not _es_transitorio(e) or intento == 2:
                    break
                espera = 2 * (intento + 1)          # 2 s y luego 4 s
                logger.warning("Gemini saturado (%s); reintento en %ss",
                               str(e)[:80], espera)
                time.sleep(espera)
        logger.warning("Gemini no pudo generar (%s); se pasa al respaldo gratuito",
                       str(err_gemini)[:120])

    if USAR_RESPALDO_OPENCODE:
        try:
            return _generate_opencode(system_instruction, user_prompt, model=model)
        except Exception as err_opencode:
            logger.error("Sin IA disponible. Gemini: %s | OpenCode: %s",
                         str(err_gemini)[:150], str(err_opencode)[:150])
            raise RuntimeError(MENSAJE_IA_NO_DISPONIBLE)

    logger.error("Sin IA disponible (respaldo apagado). Gemini: %s", str(err_gemini)[:200])
    raise RuntimeError(MENSAJE_IA_NO_DISPONIBLE)


# Constantes que los modelos "mejoran" por su cuenta: el estudiante escribe
# 3.1416 y el codigo sale con math.pi. El area de un circulo de radio 5 pasa
# de 78.54 a 78.5398, el estudiante compara con lo que calculo a mano y cree
# que se equivoco. Pedirlo en el prompt ayuda pero no garantiza nada, asi que
# ademas se comprueba y se corrige aqui, que si es seguro.
_CONSTANTES_SUSTITUIDAS = {
    "python": ((r"\bmath\.pi\b", 3.141592653589793),
               (r"\bnp\.pi\b", 3.141592653589793),
               (r"\bnumpy\.pi\b", 3.141592653589793),
               (r"\bmath\.e\b", 2.718281828459045)),
    "cpp":    ((r"\bM_PI\b", 3.141592653589793),
               (r"\bM_E\b", 2.718281828459045)),
    "php":    ((r"\bM_PI\b", 3.141592653589793),
               (r"\bpi\(\)", 3.141592653589793),
               (r"\bM_E\b", 2.718281828459045)),
}

_RE_DECIMAL = re.compile(r"\d+\.\d+")


def _respetar_constantes(codigo: str, pseudocodigo: str, idioma: str) -> str:
    """Devuelve el codigo con las constantes del lenguaje cambiadas por el
    numero que escribio el estudiante, cuando lo escribio.

    Solo actua si en el pseudocodigo hay un decimal que se parece a la
    constante (menos de 0.01 de diferencia). Si el estudiante no escribio
    ninguna aproximacion, no se toca nada: puede que math.pi sea justo lo que
    toca.
    """
    if not codigo or not pseudocodigo:
        return codigo
    decimales = _RE_DECIMAL.findall(pseudocodigo)
    if not decimales:
        return codigo

    for patron, valor in _CONSTANTES_SUSTITUIDAS.get(idioma, ()):
        if not re.search(patron, codigo):
            continue
        parecidos = [t for t in decimales if abs(float(t) - valor) < 0.01]
        if parecidos:
            codigo = re.sub(patron, parecidos[0], codigo)
    return codigo


def convert_pseudocode(pseudocode: str, target_language: str) -> dict:
    """Convierte pseudocódigo a un lenguaje de programación."""
    language_names = {
        "python": "Python",
        "cpp": "C++",
        "php": "PHP"
    }

    lang_name = language_names.get(target_language, target_language)

    prompt = f"""Convierte el siguiente pseudocódigo a {lang_name}.

PSEUDOCÓDIGO:
```
{pseudocode}
```

Genera ÚNICAMENTE el código en {lang_name}, sin markdown, sin explicaciones, sin bloques de código con ```. Solo el código puro."""

    # v3 = prompt que interpreta el pseudocódigo informal en vez de auditarlo
    # (2026-08-19). Bumpear si vuelves a tocar CONVERSION_SYSTEM_PROMPT.
    key = _cache_key("convert", "v3", NAMESPACE_CACHE, target_language,
                     normalizar_pseudocodigo(pseudocode))
    cached = cache_get("convert", key)
    if cached:
        return {**cached, "cached": True}

    try:
        code, usage = _generate(CONVERSION_SYSTEM_PROMPT, prompt, model=OPENCODE_MODEL_CONVERT, operacion="convert")

        if code.startswith("```"):
            lines = code.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)

        code = _respetar_constantes(code, pseudocode, target_language)

        result = {"success": True, "code": code, "usage": usage}
        cache_put("convert", key, result)
        return {**result, "cached": False}

    except Exception as e:
        return {"success": False, "error": str(e), "cached": False}


def convert_to_diagram(pseudocode: str) -> dict:
    """Convierte pseudocodigo en un diagrama de flujo (sintaxis Mermaid).

    Comparte tuberia con convert_pseudocode a proposito: mismo modelo, misma
    cache y mismo respaldo de Gemini. Para la plataforma, un diagrama es un
    destino mas de la conversion, como Python o C++.
    """
    prompt = f"""Convierte el siguiente pseudocodigo en un diagrama de flujo Mermaid.

PSEUDOCODIGO:
```
{pseudocode}
```

Genera UNICAMENTE el codigo Mermaid empezando por 'flowchart TD'."""

    key = _cache_key("diagram", "v1", NAMESPACE_CACHE,
                     normalizar_pseudocodigo(pseudocode))
    cached = cache_get("diagram", key)
    if cached:
        return {**cached, "cached": True}

    try:
        diagram, usage = _generate(DIAGRAM_SYSTEM_PROMPT, prompt,
                                   model=OPENCODE_MODEL_CONVERT, operacion="diagram")
        diagram = _limpiar_mermaid(diagram)
        result = {"success": True, "diagram": diagram, "usage": usage}
        cache_put("diagram", key, result)
        return {**result, "cached": False}

    except Exception as e:
        return {"success": False, "error": str(e), "cached": False}


def _limpiar_mermaid(texto: str) -> str:
    """Deja el Mermaid listo para el navegador.

    Los modelos devuelven a veces el diagrama envuelto en ```mermaid, y a
    veces escriben la asignacion con <-, que Mermaid interpreta como parte de
    una flecha y le rompe el dibujo entero.
    """
    t = texto.strip()
    if t.startswith("```"):
        lineas = t.split("\n")[1:]
        if lineas and lineas[-1].strip() == "```":
            lineas = lineas[:-1]
        t = "\n".join(lineas).strip()

    # <- solo es peligroso dentro de las etiquetas; ahi significa asignacion
    t = re.sub(r'(?<=")([^"]*?)<-([^"]*?)(?=")', r'\1=\2', t)

    if not t.lower().startswith("flowchart") and not t.lower().startswith("graph"):
        t = "flowchart TD\n" + t
    return t


def get_ai_feedback(pseudocode: str, exercise_description: str = None,
                    permitir_llamada: bool = True) -> dict:
    """Genera retroalimentación sobre el pseudocódigo del estudiante.

    permitir_llamada=False sirve para el cupo por ejercicio: si la respuesta
    ya esta en cache se entrega igual, porque no cuesta nada; solo se corta
    cuando habria que pagar una llamada nueva. Asi el estudiante que reenvia
    el mismo pseudocodigo no gasta cupo, y quien lo cambia si.
    """
    if exercise_description:
        prompt = f"""EJERCICIO: {exercise_description}

PSEUDOCÓDIGO DEL ESTUDIANTE:
```
{pseudocode}
```

Analiza si el pseudocódigo resuelve correctamente el ejercicio y proporciona retroalimentación."""
        system = FEEDBACK_SYSTEM_PROMPT
    else:
        prompt = f"""PSEUDOCÓDIGO DEL ESTUDIANTE:
```
{pseudocode}
```

Analiza el pseudocódigo y proporciona retroalimentación."""
        system = FREE_MODE_SYSTEM_PROMPT

    key = _cache_key("feedback", "v2", NAMESPACE_CACHE,
                     normalizar_pseudocodigo(pseudocode),
                     (exercise_description or "").strip())
    cached = cache_get("feedback", key)
    if cached:
        return {**cached, "cached": True}

    if not permitir_llamada:
        return {"success": False, "sin_cupo": True, "cached": False,
                "error": "Se acabaron los intentos de retroalimentación para "
                         "este ejercicio."}

    try:
        feedback, usage = _generate(system, prompt, model=OPENCODE_MODEL_TUTOR, operacion="feedback")
        result = {"success": True, "feedback": feedback, "usage": usage}
        cache_put("feedback", key, result)
        return {**result, "cached": False}

    except Exception as e:
        return {"success": False, "error": str(e), "cached": False}


def convert_to_all_languages(pseudocode: str) -> dict:
    """Convierte pseudocódigo a los tres lenguajes simultáneamente."""
    results = {}
    for lang in ["python", "cpp", "php"]:
        results[lang] = convert_pseudocode(pseudocode, lang)
    return results


GRADING_SYSTEM_PROMPT = """Eres un calificador automático de ejercicios de pseudocódigo para estudiantes principiantes.

Recibirás la DESCRIPCIÓN de un ejercicio y el PSEUDOCÓDIGO que entregó el estudiante.
Evalúa si la solución resuelve lo pedido. Criterios:
- Corrección lógica (¿resuelve el problema?): peso principal.
- Estructura del pseudocódigo (Algoritmo/FinAlgoritmo, Definir, instrucciones bien usadas).
- Claridad (nombres de variables razonables).
No castigues detalles cosméticos ni diferencias menores de sintaxis si la lógica es correcta.

RESPONDE ÚNICAMENTE con un objeto JSON válido, sin markdown, sin texto extra:
{"score": <entero de 0 a 100>, "reason": "<explicación breve en español, máximo 2 frases>"}

Guía de puntaje: 90-100 correcto y completo · 70-89 correcto con detalles menores ·
40-69 lógica parcial o incompleta · 10-39 intento con errores graves · 0-9 no corresponde al ejercicio."""


def grade_submission(pseudocode: str, exercise_description: str) -> dict:
    """Califica de 0 a 100 la solución de un ejercicio. Cacheado."""
    prompt = f"""EJERCICIO: {exercise_description}

PSEUDOCÓDIGO DEL ESTUDIANTE:
```
{pseudocode}
```

Califica la solución."""

    key = _cache_key("grade", "v2", NAMESPACE_CACHE,
                     normalizar_pseudocodigo(pseudocode),
                     exercise_description.strip())
    cached = cache_get("grade", key)
    if cached:
        return {**cached, "cached": True}

    try:
        raw, usage = _generate(GRADING_SYSTEM_PROMPT, prompt, model=OPENCODE_MODEL_TUTOR, operacion="grade")
        score, reason = _parse_grade(raw)
        if score is None:
            # Se responde como fallo para que quien llama guarde la nota vacia
            # en vez de un numero inventado. Tampoco se cachea: seria fijar el
            # error para siempre en esa entrega.
            return {"success": False, "cached": False,
                    "error": "La IA respondió en un formato ilegible; "
                             "el ejercicio quedó sin calificar."}
        result = {"success": True, "score": score, "reason": reason, "usage": usage}
        cache_put("grade", key, result)
        return {**result, "cached": False}
    except Exception as e:
        return {"success": False, "error": str(e), "cached": False}


def _parse_grade(raw: str) -> tuple:
    """Extrae (score, reason) de la respuesta del modelo, tolerando ruido."""
    import re
    text = (raw or "").strip()
    # Quitar fences de markdown si el modelo desobedece
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
        score = max(0, min(100, int(data.get("score", 0))))
        reason = str(data.get("reason", "")).strip()[:400]
        return score, reason
    except Exception:
        # Último recurso: buscar "score": NN en el texto
        m = re.search(r'"score"\s*:\s*(\d{1,3})', text)
        # Sin nota legible se devuelve None, NUNCA 0. Un 0 guardado por un
        # fallo de formato es indistinguible de un ejercicio genuinamente mal
        # hecho, y `submissions.score` es la variable de resultado del estudio:
        # una sola nota inventada contamina el analisis y nadie se entera.
        score = max(0, min(100, int(m.group(1)))) if m else None
        m2 = re.search(r'"reason"\s*:\s*"([^"]*)"', text)
        reason = (m2.group(1) if m2 else "No se pudo interpretar la calificación de la IA.")[:400]
        return score, reason
