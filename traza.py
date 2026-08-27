# -*- coding: utf-8 -*-
"""Prueba de escritorio: traza real de la ejecución, paso a paso.

La tabla NO se la inventa la IA. Se obtiene ejecutando de verdad el código
con `sys.settrace` y anotando el valor de cada variable después de cada
línea. Si la traza dice que `suma` vale 60, es que vale 60.

Se apoya en executor.run() tal cual: el código instrumentado entra en el
mismo sandbox de bubblewrap, con los mismos límites. Este módulo no relaja
ninguna protección, solo envuelve el código antes de mandarlo.
"""
import json

import executor

MAX_PASOS = 120        # un ciclo largo llenaría la tabla de ruido
MAX_REPR = 60          # recorte de cada valor mostrado
MARCA = "@@TRAZA@@"    # separa la traza de lo que imprime el programa


_PLANTILLA = '''
import sys, json, io

class _Corte(Exception):
    """Se alcanzo el limite de pasos. No es un error del estudiante."""

_traza = []
_pend = [None]
_cortada = [False]

def _val(v):
    try:
        t = repr(v)
    except Exception:
        return "?"
    return t if len(t) <= {max_repr} else t[:{max_repr}] + "..."

def _foto(frame):
    return dict((k, _val(v)) for k, v in frame.f_locals.items()
                if not k.startswith("_"))

def _trazar(frame, evento, arg):
    if frame.f_code.co_filename != "<alumno>":
        return None
    if len(_traza) >= {max_pasos}:
        # Cortar SOLO la traza dejaria el programa corriendo hasta agotar el
        # tiempo, y el estudiante con un ciclo infinito no veria nada. Se
        # aborta la ejecucion para poder enseñarle los pasos que si dio: ahi
        # se ve, fila a fila, que su condicion nunca cambia.
        _cortada[0] = True
        raise _Corte()
    if evento == "line":
        # Al llegar a una linea, la ANTERIOR ya termino: esa es la que se
        # anota. Asi cada fila muestra el estado DESPUES de ejecutarse,
        # que es como se hace una prueba de escritorio a mano.
        if _pend[0] is not None:
            _traza.append({{"linea": _pend[0], "vars": _foto(frame)}})
        _pend[0] = frame.f_lineno
    elif evento == "return":
        if _pend[0] is not None:
            _traza.append({{"linea": _pend[0], "vars": _foto(frame)}})
            _pend[0] = None
    return _trazar

_codigo = {codigo!r}
_salida = io.StringIO()
_stdout_real = sys.stdout
_error = None
sys.stdout = _salida
try:
    sys.settrace(_trazar)
    exec(compile(_codigo, "<alumno>", "exec"), {{"__name__": "__main__"}})
except _Corte:
    pass
except Exception as e:
    _error = type(e).__name__ + ": " + str(e)
finally:
    sys.settrace(None)
    sys.stdout = _stdout_real

# executor trunca stdout a 10 KB, y un JSON truncado no se puede leer:
# la traza se recorta AQUI hasta caber, quedandose siempre con los
# primeros pasos, que son los que el estudiante sigue.
_datos = {{
    "salida": _salida.getvalue()[:2000],
    "traza": _traza,
    "cortada": _cortada[0],
    "error": _error,
}}
_txt = json.dumps(_datos)
while len(_txt) > 7500 and len(_datos["traza"]) > 3:
    _datos["traza"] = _datos["traza"][:len(_datos["traza"]) * 2 // 3]
    _datos["cortada"] = True
    _txt = json.dumps(_datos)
print({marca!r} + _txt)
'''


def _instrumentar(codigo: str) -> str:
    return _PLANTILLA.format(codigo=codigo, marca=MARCA,
                             max_pasos=MAX_PASOS, max_repr=MAX_REPR)


def trazar(codigo_python: str, stdin: str = "") -> dict:
    """Ejecuta el código y devuelve la traza paso a paso.

    Devuelve siempre el mismo shape:
      success, pasos[], variables[], salida, cortada, error
    """
    r = executor.run("python", _instrumentar(codigo_python), stdin)

    if r.get("timed_out"):
        return {"success": False,
                "error": "El programa tardó demasiado. Si tiene un ciclo, "
                         "revisa que su condición llegue a cumplirse."}

    salida_cruda = r.get("stdout") or ""
    if MARCA not in salida_cruda:
        # No llego a imprimir la traza: el fallo esta en stderr
        motivo = (r.get("stderr") or "").strip() or "No se pudo trazar el programa."
        return {"success": False, "error": motivo[-400:]}

    try:
        datos = json.loads(salida_cruda.split(MARCA, 1)[1].strip())
    except Exception:
        return {"success": False,
                "error": "La traza salió demasiado larga para mostrarse. "
                         "Prueba con menos datos de entrada o un ciclo más corto."}

    lineas = codigo_python.split("\n")
    pasos = []
    for n, p in enumerate(datos["traza"], 1):
        idx = p["linea"] - 1
        pasos.append({
            "paso": n,
            "linea": p["linea"],
            "instruccion": lineas[idx].strip() if 0 <= idx < len(lineas) else "",
            "vars": p["vars"],
        })

    # Columnas de la tabla: toda variable que aparezca en algun paso, en el
    # orden en que fue apareciendo (no alfabetico: se lee mejor asi).
    columnas = []
    for p in pasos:
        for k in p["vars"]:
            if k not in columnas:
                columnas.append(k)

    return {
        "success": True,
        "pasos": pasos,
        "variables": columnas,
        "salida": datos.get("salida", ""),
        "cortada": datos.get("cortada", False),
        "error": datos.get("error"),
        "max_pasos": MAX_PASOS,
    }
