# -*- coding: utf-8 -*-
"""Que esta haciendo cada estudiante: lo que el docente necesita ver en clase.

La plataforma apunta en activity_logs todo lo que hace un estudiante -abrir
una leccion, convertir, ejecutar, pedir ayuda, responder un ejercicio de
lectura- y el panel del docente solo le ensenaba las entregas. Si alguien no
habia entrado nunca, o llevaba media hora dando vueltas al mismo ejercicio,
no habia forma de saberlo. Aqui se junta todo eso por estudiante.

Solo lee: no escribe nada ni llama a la IA.
"""
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func

from models import db, User, ActivityLog, Submission, Exercise, Topic

ZONA = ZoneInfo("America/Bogota")
EN_LINEA_MIN = 10        # visto hace menos de esto: "en linea"
INACTIVO_DIAS = 7        # sin entrar en estos dias: se avisa
ATASCADO_INTENTOS = 3    # entregas a un mismo ejercicio sin llegar a aprobar
APROBADO = 60


def ahora():
    return datetime.now(timezone.utc)


def _utc(dt):
    """Las fechas de la base vienen sin zona y son UTC."""
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def inicio_de_hoy():
    """Medianoche de hoy en Colombia, en UTC: "hoy" es el dia del aula."""
    local = ahora().astimezone(ZONA).replace(hour=0, minute=0, second=0, microsecond=0)
    return local.astimezone(timezone.utc)


def hace(dt):
    """'hace 5 min', 'hace 3 h', 'ayer'... lo que se entiende de un vistazo."""
    if not dt:
        return "nunca"
    s = (ahora() - _utc(dt)).total_seconds()
    if s < 60:
        return "ahora mismo"
    if s < 3600:
        return "hace %d min" % (s // 60)
    if s < 86400:
        return "hace %d h" % (s // 3600)
    dias = int(s // 86400)
    if dias == 1:
        return "ayer"
    if dias < 30:
        return "hace %d días" % dias
    return _utc(dt).astimezone(ZONA).strftime("%d/%m/%Y")


def _detalles(log):
    d = log.details
    if isinstance(d, str):
        try:
            d = json.loads(d)
        except ValueError:
            d = {}
    return d if isinstance(d, dict) else {}


def estado_cuenta(u, entro):
    """(clave, texto, clase css). El orden es el de lo que le falta hacer."""
    if not u.is_active:
        return ("desactivada", "Desactivada", "diff-avanzado")
    if u.must_change_password:
        if not entro:
            return ("sin_estrenar", "Sin estrenar", "diff-avanzado")
        return ("clave", "Falta cambiar la clave", "diff-intermedio")
    if not u.consent_accepted:
        return ("consentimiento", "Falta el consentimiento", "diff-intermedio")
    return ("activa", "Activa", "diff-basico")


# ── Frases para el registro ─────────────────────────────────────────
# El registro guarda nombres de accion ("convert_con_fallos") y numeros de
# ejercicio. Al docente hay que contarselo con palabras y con titulos.

_RESULTADO = {"correcto": "bien", "casi": "casi", "incorrecto": "mal"}


def _frase(accion, d, titulos, temas):
    """(icono, texto) de una accion, o None si no le dice nada al docente."""
    ej = "«%s»" % titulos.get(d.get("exercise_id"), "un ejercicio")
    if accion == "login":
        return ("🔓", "Entró a la plataforma")
    if accion == "logout":
        return ("🚪", "Salió")
    if accion == "password_change_inicial":
        return ("🔑", "Cambió su clave provisional")
    if accion == "password_change":
        return ("🔑", "Cambió su contraseña")
    if accion == "consentimiento_aceptado":
        return ("📝", "Aceptó el consentimiento informado")
    if accion == "abrir_aprender":
        return ("📚", "Abrió Aprender")
    if accion == "leer_leccion":
        try:
            tema = temas.get(int(d.get("topic_id")), "un tema")
        except (TypeError, ValueError):
            tema = "un tema"
        return ("📖", "Leyó la lección «%s»" % tema)
    if accion in ("abrir_teoria", "abrir_lectura", "abrir_diagrama"):
        return ("👀", "Abrió el ejercicio %s" % ej)
    if accion == "open_editor":
        if d.get("exercise_id"):
            return ("✏️", "Empezó a escribir en %s" % ej)
        return ("✏️", "Abrió el editor libre")
    if accion == "convert":
        return ("🔄", "Convirtió su pseudocódigo a %s" % {"python": "Python", "cpp": "C++",
                                                         "php": "PHP"}.get(d.get("language"), "código"))
    if accion in ("convert_con_fallos", "diagram_con_fallos"):
        n = d.get("total") or 1
        return ("⚠️", "El revisor le encontró %d fallo%s de escritura" % (n, "" if n == 1 else "s"))
    if accion in ("convert_rechazado", "diagram_rechazado"):
        return ("⚠️", "Intentó convertir sin haber escrito casi nada")
    if accion == "execute":
        if d.get("timed_out"):
            return ("▶️", "Ejecutó su código: se quedó en un bucle sin fin")
        ok = d.get("exit_code") == 0
        return ("▶️", "Ejecutó su código" + ("" if ok else ": terminó con error"))
    if accion == "trace":
        return ("🧮", "Hizo la prueba de escritorio")
    if accion == "diagram":
        return ("🔷", "Generó el diagrama de flujo")
    if accion == "explain":
        return ("💡", "Pidió que le explicaran el código")
    if accion == "feedback":
        return ("🤖", "Pidió retroalimentación a la IA")
    if accion == "pidio_ayuda":
        return ("🙋", "Pidió ayuda en %s" % ej)
    if accion == "submit":
        nota = d.get("score")
        nota = "" if nota is None else " — nota %d" % round(nota)
        return ("📤", "Entregó %s%s (intento %s)" % (ej, nota, d.get("attempt", "?")))
    if accion == "submit_rechazado":
        return ("⚠️", "Intentó entregar sin haber escrito casi nada")
    if accion == "leer_respuesta":
        return ("📤", "Respondió la lectura %s: %s (intento %s)"
                % (ej, _RESULTADO.get(d.get("resultado"), "?"), d.get("intento", "?")))
    if accion == "diagrama_respuesta":
        return ("📤", "Respondió el diagrama %s: %s" % (ej, _RESULTADO.get(d.get("resultado"), "?")))
    if accion == "prediccion":
        return ("🔮", "Predijo la salida de %s: %s" % (ej, _RESULTADO.get(d.get("resultado"), "?")))
    if accion == "open_test":
        return ("🧪", "Abrió el %s" % d.get("test_type", "test"))
    if accion == "open_scale":
        return ("🧪", "Abrió un cuestionario")
    if accion in ("submit_pretest", "submit_postest", "submit_scale", "submit_cognitive_load"):
        return ("🧪", "Respondió un cuestionario del estudio")
    # grade repite lo mismo que submit; el resto es de fontaneria
    return None


def _nombres():
    titulos = {e.id: e.title for e in Exercise.query.all()}
    temas = {t.id: t.name for t in Topic.query.all()}
    return titulos, temas


def _por_ejercicio(entregas):
    """{exercise_id: {"intentos": n, "mejor": nota o None}}"""
    res = {}
    for s in entregas:
        if not s.exercise_id:
            continue
        r = res.setdefault(s.exercise_id, {"intentos": 0, "mejor": None})
        r["intentos"] += 1
        if s.score is not None and (r["mejor"] is None or s.score > r["mejor"]):
            r["mejor"] = s.score
    return res


def _atascos(por_ej, titulos):
    """Ejercicios con varios intentos y ninguno aprobado: ahi hace falta el docente."""
    return [{"id": eid, "titulo": titulos.get(eid, "Ejercicio %d" % eid),
             "intentos": r["intentos"], "mejor": r["mejor"]}
            for eid, r in por_ej.items()
            if r["intentos"] >= ATASCADO_INTENTOS
            and (r["mejor"] is None or r["mejor"] < APROBADO)]


def resumen_clase():
    """Una fila por estudiante con lo que el docente mira primero."""
    alumnos = User.query.filter_by(role="estudiante").all()
    if not alumnos:
        return []
    ids = [a.id for a in alumnos]
    titulos, temas = _nombres()

    ultimo_log = dict(db.session.query(ActivityLog.user_id, func.max(ActivityLog.created_at))
                      .filter(ActivityLog.user_id.in_(ids))
                      .group_by(ActivityLog.user_id).all())
    # La ultima accion de cada uno: "que esta haciendo"
    ult_ids = [i for (i,) in db.session.query(func.max(ActivityLog.id))
               .filter(ActivityLog.user_id.in_(ids))
               .group_by(ActivityLog.user_id).all()]
    ultima_accion = {}
    for log in ActivityLog.query.filter(ActivityLog.id.in_(ult_ids)).all() if ult_ids else []:
        f = _frase(log.action, _detalles(log), titulos, temas)
        ultima_accion[log.user_id] = f[1] if f else None

    entraron = {uid for (uid,) in db.session.query(ActivityLog.user_id)
                .filter(ActivityLog.action == "login", ActivityLog.user_id.in_(ids)).distinct()}
    lecciones = defaultdict(set)
    ayudas = Counter()
    for log in (ActivityLog.query
                .filter(ActivityLog.user_id.in_(ids),
                        ActivityLog.action.in_(("leer_leccion", "pidio_ayuda"))).all()):
        if log.action == "pidio_ayuda":
            ayudas[log.user_id] += 1
        else:
            tid = _detalles(log).get("topic_id")
            if tid is not None:
                lecciones[log.user_id].add(str(tid))

    entregas = defaultdict(list)
    for s in Submission.query.filter(Submission.user_id.in_(ids)).all():
        entregas[s.user_id].append(s)

    corte_linea = ahora() - timedelta(minutes=EN_LINEA_MIN)
    corte_hoy = inicio_de_hoy()
    corte_inactivo = ahora() - timedelta(days=INACTIVO_DIAS)

    filas = []
    for a in alumnos:
        vista = [x for x in (_utc(a.ultima_vez), _utc(ultimo_log.get(a.id))) if x]
        ultima = max(vista) if vista else None
        entro = a.id in entraron or ultima is not None
        estado = estado_cuenta(a, entro)
        por_ej = _por_ejercicio(entregas[a.id])
        mejores = [r["mejor"] for r in por_ej.values() if r["mejor"] is not None]
        atascos = _atascos(por_ej, titulos)

        avisos = []
        if estado[0] == "sin_estrenar":
            avisos.append("No ha entrado nunca")
        elif ultima and ultima < corte_inactivo and a.is_active:
            avisos.append("Sin entrar %s" % hace(ultima))
        for t in atascos[:2]:
            avisos.append("Atascado en «%s»" % t["titulo"])

        filas.append({
            "id": a.id, "nombre": a.name, "correo": a.email, "grupo": a.group,
            "activo": a.is_active, "estado": estado,
            "excluido": bool(a.excluido_estudio), "semestre": a.semestre_curso,
            "ultima": ultima, "hace": hace(ultima),
            "en_linea": bool(ultima and ultima >= corte_linea and a.is_active),
            "hoy": bool(ultima and ultima >= corte_hoy),
            "ultima_accion": ultima_accion.get(a.id),
            "lecciones": len(lecciones[a.id]),
            "intentados": len(por_ej),
            "resueltos": sum(1 for r in por_ej.values()
                             if r["mejor"] is not None and r["mejor"] >= APROBADO),
            "nota": round(sum(mejores) / len(mejores)) if mejores else None,
            "ayudas": ayudas[a.id],
            "atascos": atascos,
            "avisos": avisos,
        })
    return filas


def ficha(alumno, limite=80):
    """Todo lo de un estudiante: uso, lecciones, atascos y lo que ha hecho."""
    titulos, temas = _nombres()
    logs = (ActivityLog.query.filter_by(user_id=alumno.id)
            .order_by(ActivityLog.id.desc()).all())
    entregas = Submission.query.filter_by(user_id=alumno.id).all()

    cuenta = Counter(l.action for l in logs)
    uso = [
        ("📖", "Lecciones abiertas", cuenta["leer_leccion"]),
        ("👀", "Ejercicios abiertos", cuenta["abrir_teoria"] + cuenta["abrir_lectura"]
         + cuenta["abrir_diagrama"]),
        ("🔄", "Conversiones", cuenta["convert"]),
        ("▶️", "Ejecuciones", cuenta["execute"]),
        ("🧮", "Pruebas de escritorio", cuenta["trace"]),
        ("⚠️", "Fallos que le marcó el revisor", cuenta["convert_con_fallos"]
         + cuenta["diagram_con_fallos"]),
        ("🙋", "Veces que pidió ayuda", cuenta["pidio_ayuda"]),
        ("🤖", "Retroalimentaciones de la IA", cuenta["feedback"]),
    ]

    leidas = set()
    for l in logs:
        if l.action == "leer_leccion":
            tid = _detalles(l).get("topic_id")
            if tid is not None:
                leidas.add(str(tid))
    lecciones = [{"nombre": t.name, "semestre": t.semestre, "leida": str(t.id) in leidas}
                 for t in Topic.query.order_by(Topic.semestre, Topic.order).all()]

    por_ej = _por_ejercicio(entregas)

    # Actividad: las acciones seguidas iguales se juntan ("Ejecutó su codigo ×6"),
    # que si no diez ejecuciones tapan todo lo demas.
    eventos = []
    for l in logs:
        f = _frase(l.action, _detalles(l), titulos, temas)
        if not f:
            continue
        cuando = _utc(l.created_at)
        if eventos and eventos[-1]["texto"] == f[1]:
            eventos[-1]["veces"] += 1
            eventos[-1]["desde"] = cuando
            continue
        if len(eventos) >= limite:
            break
        eventos.append({"icono": f[0], "texto": f[1], "cuando": cuando, "desde": cuando, "veces": 1})

    hoy = ahora().astimezone(ZONA).date()
    dias = []
    for e in eventos:
        fecha = e["cuando"].astimezone(ZONA).date()
        if fecha == hoy:
            etiqueta = "Hoy"
        elif fecha == hoy - timedelta(days=1):
            etiqueta = "Ayer"
        else:
            etiqueta = e["cuando"].astimezone(ZONA).strftime("%d/%m/%Y")
        if not dias or dias[-1]["dia"] != etiqueta:
            dias.append({"dia": etiqueta, "eventos": []})
        e["hora"] = e["cuando"].astimezone(ZONA).strftime("%H:%M")
        dias[-1]["eventos"].append(e)

    ultima_log = _utc(logs[0].created_at) if logs else None
    vista = [x for x in (_utc(alumno.ultima_vez), ultima_log) if x]
    ultima = max(vista) if vista else None
    entro = cuenta["login"] > 0 or ultima is not None
    return {
        "estado": estado_cuenta(alumno, entro),
        "ultima": ultima, "hace": hace(ultima),
        "en_linea": bool(ultima and ultima >= ahora() - timedelta(minutes=EN_LINEA_MIN)),
        "uso": uso,
        "lecciones": lecciones,
        "leidas": sum(1 for x in lecciones if x["leida"]),
        "resueltos": sum(1 for r in por_ej.values()
                         if r["mejor"] is not None and r["mejor"] >= APROBADO),
        "atascos": _atascos(por_ej, titulos),
        "por_ej": por_ej,
        "dias": dias,
    }
