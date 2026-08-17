"""Repoblar la cache de IA de CodeLogic, a goteo.

Contexto: la clave de cache incluye el nombre del modelo. Al cambiar
OPENCODE_MODEL_CONVERT de ling-3.0-flash-free (muerto) a deepseek-v4-flash-free,
las entradas de `convert` anteriores quedaron inalcanzables.

No se pueden "revivir": la cache guarda un sha256 de las entradas, no las
entradas. Lo que si se puede es precalentar lo que de verdad se pide — la
solucion de referencia de cada ejercicio convertida a cada idioma.

Por que a goteo: el plan gratuito de OpenCode deja pasar unas cuatro llamadas
y despues devuelve 429 FreeUsageLimitError durante un rato largo, sin cabecera
que diga cuanto. Esperar dentro del proceso no sirve: probado con esperas de
60, 120 y 240 segundos, seguia cerrado. Asi que cada ejecucion aprovecha lo que
haya y se retira en cuanto topa; el temporizador vuelve a intentarlo mas tarde.

Es reanudable por construccion: se llama a la funcion real de la aplicacion,
que consulta la cache primero. Lo ya precalentado no gasta ni una llamada, asi
que cuando este todo hecho estas ejecuciones son gratis.
"""
import time

from app import app
from models import db, AICache, Exercise
import gemini_service as g

IDIOMAS = ["python", "cpp", "php"]
PAUSA = 3.0   # segundos entre llamadas que si pasan


def log(msg):
    print(msg, flush=True)


def es_limite(err):
    e = str(err).lower()
    return any(t in e for t in ("freeusagelimit", "rate limit", "429", "quota", "too many"))


with app.app_context():
    # Entradas inalcanzables: se reconocen por el modelo grabado dentro de la
    # propia respuesta. Van en el volcado diario de la base, no se pierden.
    muertas = [e for e in AICache.query.filter_by(endpoint="convert").all()
               if ((e.response or {}).get("usage") or {}).get("model") != g.OPENCODE_MODEL_CONVERT]
    if muertas:
        for e in muertas:
            db.session.delete(e)
        db.session.commit()
        log("Borradas %d entradas inalcanzables del modelo viejo." % len(muertas))

    ejercicios = (Exercise.query.filter_by(is_active=True)
                  .order_by(Exercise.difficulty, Exercise.id).all())
    tareas = [(e, i) for e in ejercicios for i in IDIOMAS
              if (e.expected_pseudocode or "").strip()]

    nuevas = ya = fallos = 0
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
                log("%s OK (%d lineas)" % (etiqueta, len((r.get("code") or "").splitlines())))
                time.sleep(PAUSA)
            continue

        if es_limite(r.get("error")):
            log("%s limite del plan gratuito — se deja para la proxima" % etiqueta)
            cortado = True
            break

        fallos += 1
        log("%s FALLO: %s" % (etiqueta, str(r.get("error"))[:120]))

    faltan = len(tareas) - ya - nuevas
    log("Resumen: %d nuevas, %d ya estaban, %d fallos, %d por hacer%s"
        % (nuevas, ya, fallos, faltan, " (cortado por el limite)" if cortado else ""))
    if faltan == 0 and fallos == 0:
        log("COMPLETO: las %d conversiones estan en cache." % len(tareas))
