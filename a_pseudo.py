# -*- coding: utf-8 -*-
"""Devuelve la traza al lenguaje en el que el estudiante la escribio.

La prueba de escritorio se obtiene ejecutando Python de verdad, asi que la
tabla mostraba lineas como `n = int(input())` o `for i in range(1, n + 1):`.
A un estudiante de primer semestre, que esta aprendiendo QUE es un
pseudocodigo, eso no le dice nada: nunca ha visto Python.

La estrategia tiene dos pasos, y el primero es el que importa:

1. Se traduce la linea de Python a pseudocodigo y se busca esa forma entre
   las lineas que el alumno escribio DE VERDAD. Si aparece, se muestra la
   suya, tal cual la tecleo. Es exacto, no una aproximacion.

2. Solo si no hay correspondencia -por ejemplo porque el conversor partio una
   linea en dos- se muestra la traduccion. Peor que lo anterior, pero
   infinitamente mejor que ensenarle Python.
"""
import re

# Operadores, del lado Python al del pseudocodigo
_OPS = [
    (r"\bnot\b\s*", "NO "),   # tambien not(x), que el conversor escribe pegado
    (r"\band\b", "Y"),
    (r"\bor\b", "O"),
    (r"\bTrue\b", "Verdadero"),
    (r"\bFalse\b", "Falso"),
    (r"!=", "<>"),
    (r"\s%\s", " MOD "),
]


def _ops(txt: str) -> str:
    for pat, rep in _OPS:
        txt = re.sub(pat, rep, txt)
    # == pasa a = , pero sin tocar <= ni >=
    txt = re.sub(r"(?<![<>!])==", "=", txt)
    return txt.strip()


def a_pseudo(linea: str) -> str:
    """Traduce UNA linea de Python a su forma en pseudocodigo."""
    s = (linea or "").strip()
    if not s:
        return s

    # El nombre puede llevar indice: en los ejercicios de vectores la lectura
    # es v[i], y sin esto la tabla de primer semestre enseñaba
    # «v[i] = int(input())» en vez de «Leer v[i]».
    m = re.fullmatch(r"(\w+(?:\[[^\]]+\])?)\s*=\s*(?:int|float|str)?\(?\s*input\([^)]*\)\s*\)?", s)
    if m:
        return "Leer %s" % m.group(1)   # el mensaje, si lo llevaba, ya salio aparte

    m = re.fullmatch(r"([\w,\s]+)=\s*map\(\s*\w+\s*,\s*input\([^)]*\)\.split\(\)\s*\)", s)
    if m:
        return "Leer %s" % " ".join(m.group(1).split())

    m = re.fullmatch(r"print\((.*)\)", s)
    if m:
        cuerpo = m.group(1)
        # El conversor a veces usa el ternario de Python, que en pseudocodigo
        # no existe: se deja legible en lugar de dejar "if ... else" en ingles.
        t = re.fullmatch(r"(.+?)\s+if\s+(.+?)\s+else\s+(.+)", cuerpo)
        if t:
            return "Escribir %s  (si %s; en otro caso %s)" % (
                _ops(t.group(1)), _ops(t.group(2)), _ops(t.group(3)))
        return "Escribir %s" % _ops(cuerpo)

    m = re.fullmatch(r"for\s+(\w+)\s+in\s+range\(\s*([^,]+?)\s*,\s*(.+?)\s*\)\s*:", s)
    if m:
        var, desde, hasta = m.group(1), m.group(2).strip(), m.group(3).strip()
        h = re.sub(r"\s*\+\s*1$", "", hasta)          # range(a, n+1) → Hasta n
        if h == hasta:                                 # range(a, n) → Hasta n-1
            # Si el tope es un numero, se resta y ya: "Hasta 4" se lee mucho
            # mejor que "Hasta 5 - 1" en una tabla que mira un principiante.
            h = str(int(hasta) - 1) if hasta.lstrip("-").isdigit() else "%s - 1" % hasta
        return "Para %s <- %s Hasta %s Hacer" % (var, desde, h)

    m = re.fullmatch(r"while\s+(.+?)\s*:", s)
    if m:
        return "Mientras %s Hacer" % _ops(m.group(1))

    m = re.fullmatch(r"if\s+(.+?)\s*:", s)
    if m:
        return "Si %s Entonces" % _ops(m.group(1))

    m = re.fullmatch(r"elif\s+(.+?)\s*:", s)
    if m:
        return "Sino Si %s Entonces" % _ops(m.group(1))

    if re.fullmatch(r"else\s*:", s):
        return "Sino"

    m = re.fullmatch(r"(\w+(?:\[[^\]]+\])?)\s*([+\-*/])=\s*(.+)", s)
    if m:
        v, op, val = m.groups()
        return "%s <- %s %s %s" % (v, v, op, _ops(val))

    m = re.fullmatch(r"(\w+(?:\[[^\]]+\])?)\s*=\s*(.+)", s)
    if m and not s.startswith(("def ", "class ", "import ")):
        return "%s <- %s" % (m.group(1), _ops(m.group(2)))

    return _ops(s)


def _clave(txt: str) -> str:
    """Forma comparable: sin espacios de sobra, sin mayusculas, sin comillas."""
    t = re.sub(r"\s+", " ", (txt or "").strip().lower())
    t = t.replace('"', "").replace("'", "")
    return re.sub(r"\s*([<>=+\-*/,()])\s*", r"\1", t)


# Lineas que el conversor añade por su cuenta y que NO estan en el algoritmo
# del estudiante: envolver todo en una funcion y llamarla es idiomatico en
# Python, pero en la tabla de primer semestre son ruido puro. El alumno no
# escribio ningun "def", asi que no tiene por que verlo.
_ANDAMIAJE = re.compile(
    r"^\s*(?:def\s+\w+\s*\(.*\)\s*:"          # def main():
    r"|if\s+__name__\s*==.*:"                     # if __name__ == "__main__":
    r"|return\b.*"                                 # return
    r"|\w+\s*\(\s*\)\s*$"                        # main()
    r"|import\b.*|from\s+\w+\s+import\b.*)\s*$"
)


def traducir_pasos(pasos, pseudocodigo: str):
    """Reescribe cada paso de la traza con la linea del propio estudiante.

    Devuelve (pasos, cuantos se pudieron casar con una linea suya).
    """
    lineas = [l.rstrip() for l in (pseudocodigo or "").split("\n") if l.strip()]
    indice = {}
    for l in lineas:
        indice.setdefault(_clave(l), l.strip())

    # El conversor a veces funde un Escribir con el Leer siguiente en una sola
    # linea: input("Ingrese un numero:"). Entonces la tabla mostraba 3 pasos
    # para un algoritmo de 4, saltandose una instruccion que el estudiante SI
    # escribio. Aqui se recupera: si la peticion que quedo dentro del input()
    # coincide con un Escribir suyo, se emite tambien como su propio paso.
    def _escribir_absorbido(bruta):
        m = re.search(r"input\(\s*[\"']((?:[^\"'\\]|\\.)*)[\"']\s*\)", bruta)
        if not m:
            return None
        texto = m.group(1).replace("\\n", "").strip()
        if not texto:
            return None
        for l in lineas:
            if re.match(r"^\s*(?:escribir|mostrar|imprimir)\b", l.strip().lower()) and \
               _clave(texto) and _clave(texto) in _clave(l):
                return l.strip()
        return None

    fuera, casados = [], 0
    for p in pasos or []:
        bruta = p.get("instruccion", "")
        if _ANDAMIAJE.match(bruta):
            continue
        suya_escribir = _escribir_absorbido(bruta)
        if suya_escribir:
            previo = dict(fuera[-1]["vars"]) if fuera else {}
            fuera.append({**p, "instruccion": suya_escribir, "textual": True,
                          "vars": previo, "paso": len(fuera) + 1})
            casados += 1
        traducida = a_pseudo(bruta)
        suya = indice.get(_clave(traducida))
        if suya:
            casados += 1
        nuevo = dict(p)
        nuevo["instruccion"] = suya or traducida
        nuevo["textual"] = bool(suya)      # True = es la linea que el escribio
        nuevo["paso"] = len(fuera) + 1     # sin huecos tras quitar el andamiaje
        fuera.append(nuevo)
    return fuera, casados


# ── Errores de ejecucion, dichos en su idioma ──────────────────────
#
# La traza mostraba la excepcion de Python tal cual: "EOFError: EOF when
# reading a line" delante de un estudiante de primer semestre que ni siquiera
# ha visto Python. Peor aun: ese error concreto casi nunca es un fallo suyo,
# sino que ejecuto un algoritmo con Leer sin escribir los datos de entrada, y
# el mensaje no le decia ni eso ni donde ponerlos.
#
# Cada entrada: (patron, mensaje). El mensaje explica QUE paso y QUE hacer.
_ERRORES = [
    (r"EOFError",
     "Tu algoritmo pide datos con Leer, pero no le diste ninguno. "
     "Abre «datos de entrada» aquí arriba y escribe un valor por línea, "
     "en el mismo orden en que tu algoritmo los lee."),
    (r"invalid literal for int\(\)|could not convert string to float",
     "Tu algoritmo esperaba un número y recibió otra cosa. Revisa los datos "
     "de entrada: si el algoritmo hace Leer sobre una variable Entero, ahí "
     "tiene que ir un número."),
    (r"ZeroDivisionError",
     "El algoritmo intentó dividir entre cero. Comprueba el valor que tiene "
     "el divisor justo antes de esa división: mira la tabla de arriba."),
    (r"IndexError|list index out of range",
     "El algoritmo intentó usar una posición que no existe en el vector. "
     "Si lo dimensionaste con N casillas, las posiciones válidas van de 1 a N."),
    (r"NameError.*'(\w+)'",
     "Estás usando la variable «%s» antes de darle un valor. Toda variable "
     "necesita recibir algo -con Leer o con una asignación- antes de poder "
     "usarla."),
    (r"TypeError.*str.*int|TypeError.*int.*str",
     "Estás mezclando un texto con un número en la misma operación. Revisa si "
     "alguna variable que declaraste Como Cadena la estás usando para calcular."),
    (r"RecursionError|maximum recursion",
     "El algoritmo se llamó a sí mismo sin parar. Comprueba que la condición "
     "que lo detiene llegue a cumplirse."),
]


def error_amable(bruto: str) -> str:
    """Traduce una excepcion de Python a algo que un principiante entienda.

    Si no se reconoce, se devuelve tal cual: es preferible un mensaje raro a
    inventarse una explicacion que puede ser falsa y mandarlo a buscar donde
    no es.
    """
    if not bruto:
        return bruto
    for patron, mensaje in _ERRORES:
        m = re.search(patron, bruto)
        if m:
            if "%s" in mensaje and m.groups():
                return mensaje % m.group(1)
            return mensaje
    return bruto


# ── Los logicos, en el idioma del pseudocodigo ─────────────────────
#
# Una comparacion en pseudocodigo vale VERDADERO o FALSO; PSeInt lo escribe
# asi. Pero aqui debajo corre Python, que imprime True y False, y eso se le
# colaba al alumno de primer semestre en la prueba de escritorio: el ejercicio
# de operadores relacionales prometia "Son iguales: Verdadero" y en pantalla
# salia "Son iguales: True". No es un detalle: el curso es de pseudocodigo, y
# ahi True no significa nada.
#
# Solo se toca lo que se le ENSEÑA en primer semestre. La pestaña de Python
# sigue mostrando True, que es lo que Python escribe de verdad.
_LOGICOS = ((re.compile(r"\bTrue\b"), "Verdadero"),
            (re.compile(r"\bFalse\b"), "Falso"))


def logicos_en_pseudocodigo(texto):
    """True -> Verdadero, False -> Falso. Deja el resto igual."""
    if not texto:
        return texto
    for patron, palabra in _LOGICOS:
        texto = patron.sub(palabra, texto)
    return texto


def consola(salida, stdin, pasos):
    """Reconstruye lo que se veria en pantalla, con lo que TECLEO el alumno.

    Ejecutando por tuberia, lo que se escribe no se ve: el programa imprime
    "Ingrese un numero:" y salta a "Es par", sin rastro del 10. En una terminal
    de verdad el numero aparece ahi, y su ausencia hace que la traza parezca
    incompleta.

    Se intercala cada valor tecleado detras de la linea que lo pidio. Solo
    cuando cuadra: si hay tantos valores como lecturas y hay sitio para
    colocarlos. Si no cuadra, se devuelven aparte antes que colocarlos mal.
    """
    lineas = [l for l in (salida or "").split("\n")]
    if lineas and lineas[-1] == "":
        lineas = lineas[:-1]
    tecleados = [v for v in (stdin or "").replace("\r", "").split("\n") if v != ""]
    lecturas = sum(1 for p in (pasos or [])
                   if re.match(r"^\s*(?:Leer|Ingresar)\b", p.get("instruccion", "")))

    if not tecleados:
        return [{"t": l, "tipo": "salida"} for l in lineas], True

    # Camino bueno: los pasos de la traza dicen el orden EXACTO en que el
    # algoritmo escribio y leyo, asi que cada valor tecleado va detras de la
    # linea que lo pidio. Antes se adivinaba mirando si la linea acababa en
    # ":" o "?", y un cartel como «Tiene licencia? (1 = si, 0 = no)» -que
    # acaba en parentesis- no colaba: el 0 del alumno aparecia al final de
    # todo, como si el programa lo hubiera pedido despues de terminar.
    fuera, li, ti = [], 0, 0
    for paso in (pasos or []):
        instr = paso.get("instruccion", "")
        escribe = bool(re.match(r"^\s*(?:Escribir|Imprimir|Mostrar)\b", instr))
        lee = bool(re.match(r"^\s*(?:Leer|Ingresar)\b", instr)) or "input(" in instr
        # Un input("Ingrese...") hace las dos cosas: primero enseña el cartel.
        if lee and re.search(r"input\(\s*[\"'][^\"']", instr):
            escribe = True
        if escribe and li < len(lineas):
            fuera.append({"t": lineas[li], "tipo": "salida"}); li += 1
        if lee and ti < len(tecleados):
            fuera.append({"t": tecleados[ti], "tipo": "tecleado"}); ti += 1
    if ti == len(tecleados):
        # Lo que quede sin colocar es salida posterior (o traza cortada).
        fuera += [{"t": l, "tipo": "salida"} for l in lineas[li:]]
        return fuera, True

    if lecturas != len(tecleados) or len(lineas) < len(tecleados):
        # No se puede saber donde va cada uno: mejor decirlo que colocarlo mal.
        return ([{"t": l, "tipo": "salida"} for l in lineas]
                + [{"t": v, "tipo": "tecleado"} for v in tecleados]), False

    fuera, i = [], 0
    for l in lineas:
        fuera.append({"t": l, "tipo": "salida"})
        if i < len(tecleados) and (l.rstrip().endswith((":", "?")) or i == 0):
            fuera.append({"t": tecleados[i], "tipo": "tecleado"})
            i += 1
    for v in tecleados[i:]:
        fuera.append({"t": v, "tipo": "tecleado"})
    return fuera, True
