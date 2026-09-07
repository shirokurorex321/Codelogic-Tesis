# -*- coding: utf-8 -*-
"""¿Lo que escribió el estudiante va de lo que pide EL EJERCICIO?

El editor corregía siempre igual, mirara el ejercicio que mirara: comprobaba
que el pseudocódigo estuviera bien escrito y poco más. Así, en un ejercicio de
sumar, un alumno podía entregar un algoritmo con un Si y comparaciones -que no
tocan hasta la unidad siguiente- y nadie le decía nada; y podía entregar media
suma sin que nadie le dijera que le faltaba la otra mitad.

Aquí se responden dos preguntas, las dos sin IA y sin coste:

  1. ¿Está usando algo que no entra en este ejercicio?
  2. ¿Le falta algo que el ejercicio sí pide?

Ninguna de las dos BLOQUEA. Puede ejecutar y puede entregar: se le dice que
está incompleto o que se salió del tema, y decide él. Bloquear a un
principiante por escribir de más es peor que dejarle entregar sabiendo qué le
falta.

Principio heredado de revisar.py: ante la duda, callar. Un aviso falso enseña
a ignorar los avisos.
"""
import re
import unicodedata


# ── Escalones del temario ────────────────────────────────────────────
# El nivel de un tema NO está escrito a mano: sale de lo que de verdad
# necesitan las soluciones de referencia de sus ejercicios. Si mañana se
# añade un ejercicio con Mientras a un tema, el tema sube de nivel solo.
NIVEL = {
    "si": 2, "sino": 2, "segun": 2,
    "para": 3, "mientras": 3, "repetir": 3,
    "dimension": 4,
}
NOMBRE_NIVEL = {
    1: "escribir el algoritmo paso a paso, sin decisiones ni repeticiones",
    2: "decisiones (Si / Segun)",
    3: "repeticiones (Para / Mientras / Repetir)",
    4: "vectores",
}
COMO_SE_ESCRIBE = {
    "si": "Si", "sino": "Sino", "segun": "Segun", "para": "Para",
    "mientras": "Mientras", "repetir": "Repetir", "dimension": "Dimension",
}

# Operaciones aritméticas, para poder decir "aquí hay que restar".
OPERACIONES = [
    ("+", "sumar"),
    ("-", "restar"),
    ("*", "multiplicar"),
    ("/", "dividir"),
    ("^", "elevar a una potencia"),
    ("mod", "sacar el resto (mod)"),
]


def _norm(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _sin_texto(linea):
    """La línea sin lo que va entre comillas ni el comentario: dentro de un
    texto puede haber cualquier cosa y no es código."""
    l = re.sub(r'"[^"]*"', '""', linea)
    l = re.sub(r"'[^']*'", "''", l)
    return re.split(r"//", l, maxsplit=1)[0]


def inventario(pseudocodigo):
    """Qué construcciones y qué operaciones usa un pseudocódigo."""
    estructuras, operaciones = set(), set()
    lee = escribe = escribe_valor = 0
    for cruda in (pseudocodigo or "").split("\n"):
        linea = _sin_texto(cruda).strip()
        if not linea:
            continue
        bajo = _norm(linea)
        for palabra in NIVEL:
            if re.match(r"^%s\b" % palabra, bajo):
                estructuras.add(palabra)
        # Un índice entre corchetes es un vector aunque no haya Dimension.
        if re.search(r"\w\s*\[", bajo):
            estructuras.add("dimension")
        if re.match(r"^(?:leer|ingresar)\b", bajo):
            lee += len([v for v in re.split(r",", bajo.split(None, 1)[-1]) if v.strip()])
        if re.match(r"^(?:escribir|imprimir|mostrar)\b", bajo):
            escribe += 1
            # Solo cuentan los que MUESTRAN algo calculado. Los otros son
            # carteles ("Ingrese un número:") y son cuestion de estilo: si se
            # contaran, a quien juntara el texto y el valor en una sola linea
            # -que es igual de correcto- se le diria que le faltan tres
            # Escribir. Un aviso asi enseña a ignorar los avisos.
            resto = re.sub(r"^\s*\w+", "", _sin_texto(linea), count=1)
            if re.search(r"[A-Za-z_]\w*", _norm(resto)):
                escribe_valor += 1
        # Las operaciones solo cuentan a la derecha de una asignación: en
        # "Escribir a - b" también hay una resta, pero el signo de un Si o de
        # un texto no debe contar como cálculo.
        derecha = re.split(r"<-|←", linea, maxsplit=1)
        cuerpo = _norm(derecha[1]) if len(derecha) > 1 else _norm(linea)
        for signo, _nombre in OPERACIONES:
            if signo == "mod":
                if re.search(r"\bmod\b", cuerpo):
                    operaciones.add(signo)
            elif signo == "-":
                # Un menos que resta lleva algo delante; "-3" es un negativo.
                if re.search(r"[\w\)\]]\s*-\s*[\w\(]", cuerpo):
                    operaciones.add(signo)
            elif signo in cuerpo:
                operaciones.add(signo)
    return {"estructuras": estructuras, "operaciones": operaciones,
            "lee": lee, "escribe": escribe, "escribe_valor": escribe_valor}


def nivel_de(pseudocodigos):
    """El escalón más alto que necesita un conjunto de soluciones."""
    alto = 1
    for ps in pseudocodigos:
        for e in inventario(ps)["estructuras"]:
            alto = max(alto, NIVEL[e])
    return alto


def revisar_alcance(pseudocodigo, referencia, nivel_tema, permitidas=()):
    """Avisos sobre el ejercicio. Nunca bloquean: son para que sepa.

    `referencia`  la solución del profesor, para saber qué pide el ejercicio.
    `nivel_tema`  hasta qué escalón llega el tema al que pertenece.
    `permitidas`  construcciones que este ejercicio concreto sí usa aunque
                  estén por encima del nivel del tema.
    """
    suyo = inventario(pseudocodigo)
    avisos = []

    # ── 1. Se salió del tema ─────────────────────────────────────────
    fuera = sorted(e for e in suyo["estructuras"]
                   if NIVEL[e] > nivel_tema and e not in permitidas)
    if fuera:
        nombres = ", ".join(COMO_SE_ESCRIBE[e] for e in fuera)
        avisos.append({
            "tipo": "fuera",
            "mensaje": "Estás usando %s, y eso todavía no entra en este ejercicio."
                       % nombres,
            "detalle": "Aquí se practica %s. Puedes entregarlo así, pero lo que "
                       "se te evalúa es lo del ejercicio."
                       % NOMBRE_NIVEL.get(nivel_tema, "lo del tema"),
        })

    if not (referencia or "").strip():
        return avisos

    # ── 2. Le falta algo que el ejercicio sí pide ────────────────────
    del_profe = inventario(referencia)

    if del_profe["lee"] and suyo["lee"] < del_profe["lee"]:
        avisos.append({
            "tipo": "falta",
            "mensaje": "Este ejercicio necesita leer %d dato%s y tu algoritmo lee %d."
                       % (del_profe["lee"], "s" if del_profe["lee"] != 1 else "",
                          suyo["lee"]),
            "detalle": "Cada dato que el ejercicio pide al usuario va con su Leer.",
        })

    if (del_profe["escribe_valor"]
            and suyo["escribe_valor"] < del_profe["escribe_valor"]):
        n = del_profe["escribe_valor"]
        avisos.append({
            "tipo": "falta",
            "mensaje": "El ejercicio muestra %d resultado%s y tu algoritmo muestra %d."
                       % (n, "s" if n != 1 else "", suyo["escribe_valor"]),
            "detalle": "Los carteles del tipo «Ingrese un número» no cuentan: "
                       "esto va de los Escribir que enseñan un valor calculado.",
        })
    elif not del_profe["escribe_valor"] and suyo["escribe"] < del_profe["escribe"]:
        # Hay ejercicios que solo escriben texto: «Hola Mundo» no calcula nada,
        # asi que arriba no hay nada que contar y una entrega sin un solo
        # Escribir se daba por completa. Cuando la referencia no muestra ningun
        # valor, lo que cuenta son los Escribir a secas.
        n = del_profe["escribe"]
        avisos.append({
            "tipo": "falta",
            "mensaje": "El ejercicio escribe %d línea%s por pantalla y tu algoritmo "
                       "escribe %d." % (n, "s" if n != 1 else "", suyo["escribe"]),
            "detalle": "Un algoritmo que no muestra nada no resuelve el ejercicio.",
        })

    faltan_ops = [nombre for signo, nombre in OPERACIONES
                  if signo in del_profe["operaciones"]
                  and signo not in suyo["operaciones"]]
    if faltan_ops:
        avisos.append({
            "tipo": "falta",
            "mensaje": "Aquí hay que %s, y no lo veo en tu algoritmo."
                       % " y ".join(faltan_ops),
            "detalle": "Si lo resolviste de otra forma, ignora este aviso.",
        })

    faltan_est = sorted(e for e in del_profe["estructuras"]
                        if e not in suyo["estructuras"]
                        and NIVEL[e] == max([NIVEL[x] for x in del_profe["estructuras"]],
                                            default=0))
    if faltan_est:
        avisos.append({
            "tipo": "falta",
            "mensaje": "Este ejercicio se resuelve con %s, y tu algoritmo no lo usa."
                       % " o ".join(COMO_SE_ESCRIBE[e] for e in faltan_est),
            "detalle": "Si lo resolviste de otra forma y funciona, ignora este aviso.",
        })

    return avisos
