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
    (r"\bnot\s+", "NO "),
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

    m = re.fullmatch(r"(\w+)\s*=\s*(?:int|float|str)?\(?\s*input\([^)]*\)\s*\)?", s)
    if m:
        return "Leer %s" % m.group(1)

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
    return re.sub(r"\s*([<>=+\-*/,])\s*", r"\1", t)


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

    fuera, casados = [], 0
    for p in pasos or []:
        bruta = p.get("instruccion", "")
        if _ANDAMIAJE.match(bruta):
            continue
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
