"""Precalentar la cache de IA de CodeLogic.

Contexto: la clave de cache incluye el nombre del modelo. Al cambiar
OPENCODE_MODEL_CONVERT de ling-3.0-flash-free (muerto) a deepseek-v4-flash-free,
las entradas de `convert` anteriores quedaron inalcanzables.

No se pueden "revivir": la cache guarda un sha256 de las entradas, no las
entradas. Lo que si se puede es precalentar lo reconstruible — la solucion de
referencia de cada ejercicio convertida a cada idioma.

Quien genera el texto da igual. La clave se calcula ANTES de generar, a partir
de OPENCODE_MODEL_CONVERT, y cache_put la guarda con esa clave sea cual sea el
proveedor que respondio. Por eso una entrada calentada con Gemini la acierta
igual el estudiante, cuya peticion va por OpenCode.

Es reanudable: se llama a la funcion real de la aplicacion, que consulta la
cache primero. Lo ya hecho no gasta ni una llamada.
"""
import time

from app import app
from models import db, AICache, Exercise
import gemini_service as g

IDIOMAS = ["python", "cpp", "php"]

# Espera entre llamadas que si pasan. 6 s ~ 10 por minuto, que es lo que suelen
# permitir los planes gratuitos de Gemini. Bajarlo invita a que corten.
PAUSA = 6.0

# Modelos retirados cuyas entradas quedaron inalcanzables. Se listan de forma
# EXPLICITA, no como "todo lo que no sea el modelo actual": con esa regla, una
# entrada generada por el respaldo de Gemini se borraria en la ejecucion
# siguiente por no coincidir con el modelo de OpenCode, y el guion se pasaria
# la vida calentando y borrando lo mismo. Al anadir un modelo aqui se limpia
# una vez; despues sobra.
MODELOS_RETIRADOS = {"ling-3.0-flash-free"}


def log(msg):
    print(msg, flush=True)


def es_limite(err):
    e = str(err).lower()
    return any(t in e for t in ("freeusagelimit", "rate limit", "429", "quota",
                                "too many", "resource_exhausted"))


with app.app_context():
    muertas = [e for e in AICache.query.filter_by(endpoint="convert").all()
               if ((e.response or {}).get("usage") or {}).get("model") in MODELOS_RETIRADOS]
    if muertas:
        for e in muertas:
            db.session.delete(e)
        db.session.commit()
        log("Borradas %d entradas de modelos retirados." % len(muertas))

    if g._gemini_client:
        log("Respaldo de Gemini disponible (%s): si OpenCode corta, sigue por ahi."
            % g.GEMINI_MODEL)
    else:
        log("Sin GEMINI_API_KEY: solo OpenCode, que corta a las pocas llamadas.")

    ejercicios = (Exercise.query.filter_by(is_active=True)
                  .order_by(Exercise.difficulty, Exercise.id).all())
    tareas = [(e, i) for e in ejercicios for i in IDIOMAS
              if (e.expected_pseudocode or "").strip()]

    nuevas = ya = fallos = 0
    por_proveedor = {}
    cortado = False

    for n, (ej, idi) in enumerate(tareas, 1):
        etiqueta = "[%2d/%d] %-28s %-7s" % (n, len(tareas), ej.title[:28], idi)
        try:
            r = g.convert_pseudocode(ej.expected_pseudocode, idi)
        except Exception as exc:
            r = {"success": False, "error": "%s: %s" % (type(exc).__name__, exc)}

        if r.get("success"):
            if r.get("cached"):
                ya += 1
            else:
                nuevas += 1
                prov = (r.get("usage") or {}).get("provider", "?")
                por_proveedor[prov] = por_proveedor.get(prov, 0) + 1
                log("%s OK por %-8s (%d lineas)"
                    % (etiqueta, prov, len((r.get("code") or "").splitlines())))
                time.sleep(PAUSA)
            continue

        # Aqui solo se llega si fallaron los dos proveedores: _generate cae a
        # Gemini por su cuenta cuando OpenCode falla.
        if es_limite(r.get("error")):
            log("%s limite en todos los proveedores — se deja para la proxima" % etiqueta)
            cortado = True
            break

        fallos += 1
        log("%s FALLO: %s" % (etiqueta, str(r.get("error"))[:160]))

    faltan = len(tareas) - ya - nuevas
    detalle = ("  (" + ", ".join("%s: %d" % kv for kv in sorted(por_proveedor.items())) + ")"
               if por_proveedor else "")
    log("Resumen: %d nuevas, %d ya estaban, %d fallos, %d por hacer%s%s"
        % (nuevas, ya, fallos, faltan,
           " (cortado por el limite)" if cortado else "", detalle))
    if faltan == 0 and fallos == 0:
        log("COMPLETO: las %d conversiones estan en cache." % len(tareas))
