# -*- coding: utf-8 -*-
"""Revisa el pseudocodigo y dice QUE esta mal, antes de convertir nada.

El conversor esta hecho para ser tolerante: interpreta lo que el estudiante
quiso decir y produce codigo que funciona. Eso esta bien en tercer semestre,
donde el objetivo es llegar a codigo. En primero es al reves: la asignatura
es aprender a ESCRIBIR pseudocodigo, y si un Si sin Entonces se convierte sin
rechistar -o peor, si el conversor se inventa una variable que falta- el
estudiante nunca se entera de que lo escribio mal.

Esto no usa IA: son comprobaciones deterministas. No cuesta nada, responde al
instante y, sobre todo, dice siempre lo mismo ante lo mismo.

Principio: NUNCA avisar de algo que pueda estar bien. Un aviso falso a un
principiante lo manda a arreglar lo que no esta roto, y aprende a ignorar los
avisos. Ante la duda, callar.
"""
import re
import unicodedata

# Bloques que abren y su cierre. En minusculas y sin tildes.
BLOQUES = [
    ("algoritmo", "finalgoritmo"),
    ("proceso", "finproceso"),
    ("si", "finsi"),
    ("para", "finpara"),
    ("mientras", "finmientras"),
    ("segun", "finsegun"),
]
CIERRES = {c: a for a, c in BLOQUES}

# Como se escriben de verdad, para poder nombrarlos en los avisos: .capitalize()
# convertiria FinAlgoritmo en "Finalgoritmo", que no es lo que el estudiante ve.
NOMBRE = {
    "algoritmo": "Algoritmo", "finalgoritmo": "FinAlgoritmo",
    "proceso": "Proceso", "finproceso": "FinProceso",
    "si": "Si", "finsi": "FinSi",
    "para": "Para", "finpara": "FinPara",
    "mientras": "Mientras", "finmientras": "FinMientras",
    "segun": "Segun", "finsegun": "FinSegun",
    "escribir": "Escribir", "leer": "Leer", "definir": "Definir",
    "entonces": "Entonces", "sino": "Sino", "hacer": "Hacer",
    "hasta": "Hasta", "imprimir": "Imprimir", "mostrar": "Mostrar",
    "dimension": "Dimension", "repetir": "Repetir", "como": "Como",
}

# Palabras clave conocidas, para detectar erratas por parecido.
CLAVES = {
    "algoritmo", "finalgoritmo", "proceso", "finproceso", "definir", "como",
    "entero", "real", "cadena", "logico", "caracter", "dimension",
    "leer", "escribir", "imprimir", "mostrar", "ingresar",
    "si", "entonces", "sino", "finsi",
    "para", "hasta", "hacer", "finpara", "paso", "con",
    "mientras", "finmientras", "repetir",
    "segun", "finsegun", "de", "otro", "modo",
    # Construcciones de varias palabras: "Hasta Que" en el Repetir, "Con Paso"
    # en el Para, "Escribir Sin Saltar", "Esperar Tecla", "Limpiar Pantalla".
    # Sin esto, el «Que» de "Hasta Que edad >= 0" se tomaba por una variable
    # sin declarar y salia un aviso falso en un ejercicio correcto.
    "que", "sin", "saltar", "esperar", "tecla", "segundos",
    "limpiar", "pantalla", "borrar", "finrepetir",
    # Muchos escriben el cierre separado: "fin algoritmo", "fin si". El fallo
    # de que el bloque no se cierre ya se avisa aparte; sin este "fin" suelto,
    # la linea parecia una asignacion a la que le faltaba la flecha.
    "fin",
}


def _norm(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _sin_texto(linea):
    """La linea sin comillas ni comentarios: ahi dentro no hay sintaxis.

    El comentario se quita DESPUES de vaciar las comillas, para no cortar por
    un // que forme parte de un texto. Sin esto, un comentario como
    "// x ya no vale 5" hacia creer que «vale» era una variable sin declarar.
    """
    l = re.sub(r'"[^"]*"', '""', linea)
    l = re.sub(r"'[^']*'", "''", l)
    return re.split(r"//", l, 1)[0]


def _distancia(a, b):
    """Levenshtein, para detectar 'Escrivir' como 'Escribir'."""
    if abs(len(a) - len(b)) > 2:
        return 99
    ant = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        act = [i]
        for j, cb in enumerate(b, 1):
            act.append(min(ant[j] + 1, act[j - 1] + 1, ant[j - 1] + (ca != cb)))
        ant = act
    return ant[-1]


def _corregir_palabra(linea, mala, buena):
    """Cambia la palabra mal escrita conservando el resto de la linea."""
    return re.sub(r"\b%s\b" % re.escape(mala), buena, linea, count=1, flags=re.I)


def _anadir_al_final(linea, palabra):
    """Anade la palabra que falta al final, respetando comentarios al vuelo."""
    return "%s %s" % (linea.rstrip(), palabra)


def _falta_en_para(bajo):
    """Lo que le falta a la cabecera de un Para: "hasta", "inicial", "final" o
    "paso"; None si esta completa o si no se puede saber.

    La conversion es tolerante y completaba sola lo que faltaba: el 19/11/2026,
    «Para i <- 1 Hasta Con Paso 1 Hacer» paso el revisor sin aviso, la
    conversion se invento el valor final y la prueba de escritorio corrio como
    si el algoritmo estuviera bien. Solo se avisa de lo que falta sin duda: un
    «Para Cada x De v Hacer» no lleva Hasta, y sin flecha no se sabe donde
    empieza el valor inicial, asi que ahi se calla.
    """
    resto = re.sub(r"^\s*para(?![a-z])", "", bajo).strip()
    if re.match(r"cada(?![a-z])", resto):
        return None
    flecha = re.search("<-|←|=", resto)
    hasta = re.search(r"(?<![a-z])hasta(?![a-z])", resto)
    if not hasta:
        return "hasta" if flecha else None
    if flecha and flecha.start() < hasta.start() and not re.search(r"\w", resto[flecha.end():hasta.start()]):
        return "inicial"
    tras = resto[hasta.end():]
    if not re.search(r"\w", re.split(r"(?<![a-z])(?:con\s+paso|hacer)(?![a-z])", tras, 1)[0]):
        return "final"
    paso = re.search(r"(?<![a-z])con\s+paso(?![a-z])", tras)
    if paso and not re.search(r"\w", re.split(r"(?<![a-z])hacer(?![a-z])", tras[paso.end():], 1)[0]):
        return "paso"
    return None


_FALTA_EN_PARA = {
    "hasta": ("A este Para le falta Hasta con el valor final.",
              "Un Para se escribe así: Para i <- 1 Hasta 10 Hacer."),
    "inicial": ("A este Para le falta el valor inicial después de la flecha.",
                "Escribe desde qué valor empieza la variable, por ejemplo: Para i <- 1 Hasta 10 Hacer."),
    "final": ("A este Para le falta el valor final después de Hasta.",
              "Escribe hasta qué valor llega la variable, por ejemplo: Para i <- 1 Hasta 10 Hacer."),
    "paso": ("A este Para le falta el valor del paso después de Con Paso.",
             "Escribe de cuánto en cuánto avanza, por ejemplo Con Paso 2. Si avanza de uno en uno, "
             "puedes quitar Con Paso."),
}


# Palabras que empiezan una instruccion y son largas y sin ambiguedad: si
# aparecen PEGADAS al final de otra palabra, lo que hay es un salto de linea
# que se perdio. Se dejan fuera "si", "sino" y "para" a proposito: aparecen
# dentro de palabras corrientes (analiSIs, sePARAr) y darian avisos falsos.
_PEGADAS = ("escribir", "imprimir", "mostrar", "leer", "ingresar", "definir",
            "dimension", "mientras", "repetir", "segun", "finsi", "finpara",
            "finmientras", "finsegun", "finalgoritmo", "finproceso")


def _dos_instrucciones(linea, limpia, bajo):
    """Dos instrucciones en la misma linea, por un salto de linea perdido.

    Salio de un envio real: «Leer aEscribir "Ingrese un numero b:"». Al pegarse
    las dos lineas, «aEscribir» parecia una variable y el aviso que recibia el
    estudiante era que no la habia declarado, que no le decia nada. Lo que le
    pasa es que le falta un salto de linea.
    """
    # Palabra por palabra, y NUNCA sobre una que sea clave entera: FinSegun
    # acaba en "segun" y FinMientras en "mientras", asi que buscar el trozo
    # suelto acusaba de fallo a la mitad de los ejercicios de seleccion y de
    # repeticion del temario.
    for m in re.finditer(r"[a-z0-9_]+", bajo):
        palabra = m.group(0)
        if palabra in CLAVES:
            continue
        for clave in _PEGADAS:
            if palabra.endswith(clave) and len(palabra) > len(clave):
                corte = m.end() - len(clave)
                if corte >= len(linea):
                    continue
                sangria = re.match(r"^(\s*)", linea).group(1)
                return {"palabra": linea[corte:corte + len(clave)],
                        "corregida": linea[:corte].rstrip() + "\n" + sangria + linea[corte:]}

    # Un Leer o un Escribir no asignan nada, asi que una flecha en esa linea
    # es de otra instruccion que se pego. Aqui NO se ofrece la linea partida:
    # en «Leer bsuma <- a + b» no hay forma de saber donde acaba el nombre de
    # la variable que lee y empieza el de la que asigna, y una correccion
    # inventada es peor que ninguna.
    if re.match(r"^(?:leer|ingresar|escribir|imprimir|mostrar)\b", bajo) and (
            "<-" in limpia or "\u2190" in limpia):
        return {"palabra": None, "corregida": None}

    return None


def _falta_flecha(linea):
    """Devuelve la linea con la flecha puesta, o None si no toca avisar.

    Solo cuando queda claro que se quiso asignar: un nombre de variable, algo
    detras, y ningun motivo para pensar que es otra cosa (una etiqueta de
    Segun termina en :, y una llamada lleva parentesis pegados al nombre).
    """
    m = re.match(r"^(\s*)([A-Za-z_][\w]*(?:\[[^\]]*\])?)(\s+)(\S.*)$", linea)
    if not m:
        return None
    sangria, nombre, _hueco, resto = m.groups()
    # Una llamada lleva el parentesis PEGADO al nombre -MiProceso(a, b)-, y
    # entonces la expresion de arriba, que exige un hueco, ni siquiera casa.
    # Descartar todo lo que empiece por parentesis dejaba escapar el fallo mas
    # comun de todos: «promedio  (a + b) / 2», una asignacion sin su flecha.
    if resto.rstrip().endswith(":"):
        return None
    return "%s%s <- %s" % (sangria, nombre, resto.strip())


# Piezas de una linea para decidir si una comilla puesta en un sitio deja algo
# que se pueda leer como pseudocodigo. Los nombres van sin tildes a proposito:
# una palabra con tilde FUERA de las comillas es texto que se quedo sin ellas.
_PIEZA = re.compile(r'''
    (?P<hueco>\s+)
  | (?P<comentario>//.*)
  | (?P<texto>"[^"]*"|'[^']*')
  | (?P<numero>\d+(?:\.\d+)?)
  | (?P<nombre>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<abre>[(\[])
  | (?P<cierra>[)\]])
  | (?P<op><-|←|<=|>=|<>|==|!=|[-+*/^%=<>,&|~])
  | (?P<fin>[:;]\s*$)
''', re.X)

# Palabras que operan o separan, no valores: y, o, no, mod...
_OPERADORES_PALABRA = {"y", "o", "no", "mod", "div"}

# Que palabras clave pueden aparecer DESPUES de la que abre la linea.
_CLAVES_DENTRO = {
    "escribir": {"sin", "saltar"}, "imprimir": {"sin", "saltar"},
    "mostrar": {"sin", "saltar"},
    "si": {"entonces"}, "mientras": {"hacer"},
    "para": {"hasta", "con", "paso", "hacer"},
    "hasta": {"que"}, "segun": {"hacer"}, "de": {"otro", "modo"},
    "definir": {"como", "entero", "real", "cadena", "logico", "caracter"},
}
# Instrucciones que no pueden llevar los dos puntos de una etiqueta.
_INSTRUCCIONES = {"escribir", "imprimir", "mostrar", "leer", "ingresar", "si",
                  "mientras", "para", "hasta", "definir", "dimension", "nombre"}
# La palabra con la que tiene que terminar la linea que abre cada bloque.
_CIERRA_CON = {"si": "entonces", "mientras": "hacer", "para": "hacer"}


def _piezas_validas(linea, declaradas):
    """Nombres de variable usados fuera de las comillas, o None si no se lee.

    No es un analizador de PSeInt: solo descarta lo que seguro no es codigo
    (dos valores seguidos sin nada entre medias, una tilde fuera de un texto,
    un signo suelto al final) para elegir entre los sitios posibles de la
    comilla que falta.
    """
    pos, previo, nombres = 0, "inicio", []
    primera, ultima_clave, fin = None, None, None
    while pos < len(linea):
        m = _PIEZA.match(linea, pos)
        if not m:
            return None
        pos = m.end()
        tipo = m.lastgroup
        if tipo == "hueco":
            continue
        if tipo == "fin":
            fin = m.group().strip()
            continue
        if tipo == "comentario":
            # «"Visita http:"//iup.edu.co» no es un texto y un comentario: nadie
            # pega el // a lo anterior. Es la URL que se quedo sin su comilla.
            if m.start() and not linea[m.start() - 1].isspace():
                return None
            break
        palabra = _norm(m.group()) if tipo == "nombre" else None
        if tipo == "nombre":
            if palabra in _OPERADORES_PALABRA:
                tipo = "op"
            elif palabra in CLAVES:
                tipo = "clave"
            elif palabra not in _NO_SON_VARIABLES:
                nombres.append(palabra)
        if primera is None:
            primera = palabra if tipo == "clave" else tipo
        elif tipo == "clave":
            # Tras la instruccion solo caben SUS palabras: el «de» de
            # «"Ingrese el valor "de A» es texto que se quedo fuera.
            if palabra not in _CLAVES_DENTRO.get(primera, ()):
                return None
            ultima_clave = palabra
        if tipo in ("texto", "numero", "nombre"):
            # dos valores seguidos sin nada entre medias: «"Hola" mundo»
            if previo in ("valor", "nombre", "cierra"):
                return None
            actual = "nombre" if tipo == "nombre" else "valor"
        elif tipo == "abre":
            # tras un nombre es una llamada o una posicion: raiz(x), v[i]
            if previo in ("valor", "cierra"):
                return None
            actual = "abre"
        elif tipo == "cierra":
            if previo in ("inicio", "clave", "op", "abre") and m.group() == "]":
                return None
            actual = "cierra"
        elif tipo == "op":
            actual = "op"
        else:  # clave
            actual = "clave"
        previo = actual
    if previo in ("op", "abre", "inicio"):
        # una coma o un + al final: ahi faltaba algo
        return None
    if primera == "texto" and fin != ":":
        # Una linea no empieza por un texto; solo una etiqueta de Segun
        return None
    if fin == ":" and primera in _INSTRUCCIONES:
        # los dos puntos son de las etiquetas de Segun, no de un Escribir
        return None
    if primera in _CIERRA_CON and ultima_clave != _CIERRA_CON[primera]:
        return None
    return nombres


def _cerrar_comillas(linea, declaradas):
    """La linea con la comilla que falta en su sitio, o None si no esta claro.

    Antes se ponia siempre al final, y acertaba solo cuando faltaba la de
    cierre del ultimo texto: con «Escribir Hola"» proponia «Escribir Hola""»,
    y con «Escribir "La suma es: , suma» metia la variable dentro del texto.
    Ahora se prueba cada hueco y se queda el que deja una linea legible. Si
    quedan dos lecturas distintas, se prefiere la que usa variables que el
    estudiante declaro; y si aun asi hay empate, no se propone nada: una
    correccion inventada es peor que ninguna.
    """
    todas = []
    for i in range(len(linea) + 1):
        candidata = linea[:i] + '"' + linea[i:]
        nombres = _piezas_validas(candidata, declaradas)
        if nombres is None:
            continue
        # Una comilla pegada por fuera a una palabra (Escribir"Hola", "si"Entonces)
        # no la escribe nadie: esa posicion no se ofrece.
        abre = candidata[:i].count('"') % 2 == 0
        vecino = linea[i - 1:i] if abre else linea[i:i + 1]
        if vecino.isalnum() or vecino == "_":
            continue
        # Ni partiendo una flecha o una comparacion: «linea <"- "»
        if linea[i - 1:i + 1] in ("<-", "<=", ">=", "<>", "==", "!="):
            continue
        # Misma lectura con la comilla un espacio antes o despues: cuenta como
        # una sola, y se elige abajo donde queda el espacio.
        firma = re.sub(r'\s*"\s*', '"', candidata)
        todas.append((nombres, firma, i, candidata))
    # Si el estudiante declaro variables, una lectura que saca de las comillas
    # una palabra que no declaro («"Hola", mundo») es casi seguro falsa. Pero
    # si ninguna lectura las cumple (se le olvido un Definir), no se descarta
    # nada: ese fallo ya se le avisa aparte.
    declaradas_ok = [t for t in todas if all(x in declaradas for x in t[0])]
    elegibles = declaradas_ok if (declaradas and declaradas_ok) else todas
    # Puntuacion: cuantas variables DISTINTAS quedan fuera de las comillas. Se
    # cuentan una vez: en «Escribir a = "", a» la a repetida no hace mejor esa
    # lectura que «Escribir "a = ", a».
    buenas = [(len(set(n)), f, i, c) for n, f, i, c in elegibles]
    if not buenas:
        return None
    mejor = max(b[0] for b in buenas)
    lecturas = {}
    for usadas, firma, i, candidata in buenas:
        if usadas == mejor:
            lecturas.setdefault(firma, []).append((i, candidata))
    if len(lecturas) != 1:
        return None
    opciones = next(iter(lecturas.values()))
    # El espacio va DENTRO del texto, que es como se escribe: al abrir, la
    # comilla lo mas a la izquierda que deje un espacio fuera -«, " x "»-; al
    # cerrar, lo mas a la derecha -«"La suma es: ", suma»-.
    i0, c0 = opciones[0]
    if c0[:i0].count('"') % 2 == 0:
        con_espacio = [o for o in opciones if linea[o[0] - 1:o[0]].isspace()]
        elegida = min(con_espacio or opciones)
    else:
        elegida = max(opciones)
    return elegida[1].rstrip()


def _comillas_impares(linea):
    """¿Queda un texto abierto? Sin contar las comillas de un comentario.

    Con «Escribir "a" // dice "hola» la linea tiene tres comillas y se avisaba
    de unas sin cerrar que no existen. El // solo corta si esta FUERA de un
    texto: en «Escribir "http://..."» es parte de lo que se escribe.
    """
    dentro = False
    for i, ch in enumerate(linea):
        if ch == '"':
            dentro = not dentro
        elif not dentro and linea.startswith("//", i):
            break
    return dentro


def _declaradas(lineas):
    """Nombres declarados con Definir o Dimension, sin tildes y en minusculas."""
    nombres = set()
    for cruda in lineas:
        bajo = _norm(re.split(r"//", cruda, 1)[0]).strip()
        m = re.match(r"^definir\s+(.*?)\s+como\b", bajo)
        if m:
            nombres.update(x.strip() for x in m.group(1).split(",") if x.strip())
        m = re.match(r"^dimension\s+(.*)$", bajo)
        if m:
            nombres.update(re.findall(r"([a-z_]\w*)\s*\[", m.group(1)))
    return nombres


def revisar(pseudocodigo):
    """Devuelve una lista de problemas: {linea, texto, problema, sugerencia}."""
    problemas = []
    lineas = (pseudocodigo or "").split("\n")
    pila = []          # bloques abiertos: (palabra, numero de linea)
    declaradas = _declaradas(lineas)

    for n, cruda in enumerate(lineas, 1):
        linea = cruda.strip()
        if not linea or linea.startswith("//"):
            continue
        limpia = _sin_texto(linea)
        bajo = _norm(limpia)
        palabras = re.findall(r"[a-z]+", bajo)
        primera = palabras[0] if palabras else ""

        # comillas sin cerrar
        if _comillas_impares(linea):
            problemas.append({
                "linea": n, "texto": linea,
                "problema": "Hay unas comillas sin cerrar.",
                "sugerencia": "Todo texto entre comillas tiene que abrirlas y cerrarlas.",
                "corregida": _cerrar_comillas(linea, declaradas)})

        # dos instrucciones pegadas por un salto de linea perdido
        if primera in CLAVES:
            junto = _dos_instrucciones(linea, limpia, bajo)
            if junto:
                problemas.append({
                    "linea": n, "texto": linea,
                    "problema": ("Aquí hay dos instrucciones en la misma línea: "
                                 "se te pegó «%s» a la anterior." % junto["palabra"])
                                if junto["palabra"] else
                                ("Aquí hay dos instrucciones en la misma línea: "
                                 "un %s y una asignación." % linea.split()[0]),
                    "sugerencia": "Cada instrucción va en su propia línea.",
                    "corregida": junto["corregida"]})

        # cierres
        if primera in CIERRES:
            esperado = CIERRES[primera]
            if not pila:
                problemas.append({
                    "linea": n, "texto": linea,
                    "problema": "Aparece %s pero no hay ningún %s abierto." % (linea.split()[0], NOMBRE[esperado]),
                    "sugerencia": "Un cierre solo tiene sentido si antes se abrió el bloque."})
            elif pila[-1][0] != esperado:
                # Lo que falta no es este cierre: son los bloques de dentro que
                # siguen abiertos. Se avisa de cada uno y despues SI se cierra
                # el que toca, para no decir luego que quedo sin cerrar cuando
                # el estudiante si lo habia cerrado.
                while pila and pila[-1][0] != esperado:
                    abierto, ln = pila.pop()
                    problemas.append({
                        "linea": ln, "texto": lineas[ln - 1].strip(),
                        "problema": "Este %s se abre en la línea %d y no se cierra."
                                    % (NOMBRE[abierto], ln),
                        "sugerencia": "Escribe %s antes del %s de la línea %d."
                                      % (NOMBRE[dict(BLOQUES)[abierto]], linea.split()[0], n)})
                if pila and pila[-1][0] == esperado:
                    pila.pop()
            else:
                pila.pop()
            continue

        # aperturas
        for abre, _cierra in BLOQUES:
            if primera != abre:
                continue
            # "Sino Si ..." no abre un bloque nuevo en PSeInt clasico, pero
            # aqui se trata como anidado, que es como lo escriben.
            pila.append((abre, n))
            if abre == "si" and "entonces" not in bajo:
                problemas.append({
                    "linea": n, "texto": linea,
                    "problema": "A este Si le falta Entonces.",
                    "sugerencia": "Todo Si termina con Entonces.",
                    "corregida": _anadir_al_final(linea, "Entonces")})
            if abre == "para" and "hacer" not in bajo:
                problemas.append({
                    "linea": n, "texto": linea,
                    "problema": "A este Para le falta Hacer.",
                    "sugerencia": "Todo Para termina con Hacer.",
                    "corregida": _anadir_al_final(linea, "Hacer")})
            if abre == "para":
                falta = _falta_en_para(bajo)
                if falta:
                    problema, sugerencia = _FALTA_EN_PARA[falta]
                    problemas.append({"linea": n, "texto": linea,
                                      "problema": problema, "sugerencia": sugerencia})
            if abre == "mientras" and "hacer" not in bajo:
                problemas.append({
                    "linea": n, "texto": linea,
                    "problema": "A este Mientras le falta Hacer.",
                    "sugerencia": "Todo Mientras termina con Hacer.",
                    "corregida": _anadir_al_final(linea, "Hacer")})
            if abre == "segun" and "hacer" not in bajo:
                problemas.append({
                    "linea": n, "texto": linea,
                    "problema": "A este Segun le falta Hacer.",
                    "sugerencia": "Todo Segun termina con Hacer.",
                    "corregida": _anadir_al_final(linea, "Hacer")})
            break
        else:
            # erratas: una primera palabra que se parece mucho a una clave.
            # Solo si NO es una asignacion ni una llamada: ahi la primera
            # palabra es un nombre de variable que el estudiante elige.
            flecha = "<-" in limpia or "\u2190" in limpia
            con_igual = re.match(r"^\s*[\w\[\]]+\s*=[^=]", limpia)
            es_asignacion = flecha or con_igual
            if primera and not es_asignacion and primera not in CLAVES:
                cercanas = [k for k in CLAVES
                            if len(k) > 3 and _distancia(primera, k) == 1]
                if cercanas:
                    buena = NOMBRE.get(cercanas[0], cercanas[0].capitalize())
                    problemas.append({
                        "linea": n, "texto": linea,
                        "problema": "«%s» no es una palabra del pseudocódigo." % linea.split()[0],
                        "sugerencia": "La palabra correcta es %s." % buena,
                        "corregida": _corregir_palabra(linea, linea.split()[0], buena)})
                else:
                    # Una linea que no empieza por palabra clave solo puede ser
                    # una asignacion, y sin flecha no asigna nada: «suma a + b»
                    # calcula y tira el resultado. El conversor lo tapaba de una
                    # forma distinta en cada lenguaje -en Python le ponia el =
                    # que faltaba, en C++ dejaba la variable con basura y salia
                    # "el resultado es:106494"-, asi que el estudiante veia un
                    # numero y no se enteraba de que le faltaba la flecha.
                    hueco = _falta_flecha(linea)
                    if hueco:
                        problemas.append({
                            "linea": n, "texto": linea,
                            "problema": "A esta línea le falta la flecha de asignación.",
                            "sugerencia": "Para guardar un valor en una variable se "
                                          "escribe nombre <- valor.",
                            "corregida": hueco})
            elif con_igual and not flecha:
                # El = en pseudocodigo compara, no asigna. Es la confusion que
                # la asignatura quiere evitar desde el primer dia.
                problemas.append({
                    "linea": n, "texto": linea,
                    "problema": "En pseudocódigo se asigna con <- , no con =.",
                    "sugerencia": "El = sirve para comparar (dentro de un Si o "
                                  "un Mientras). Para guardar un valor va la flecha.",
                    "corregida": re.sub(r"=", "<-", linea, count=1)})

    # bloques que quedaron abiertos
    for abre, ln in reversed(pila):
        problemas.append({
            "linea": ln, "texto": lineas[ln - 1].strip(),
            "problema": "Este %s se abre y nunca se cierra." % NOMBRE[abre],
            "sugerencia": "Falta escribir %s al terminar el bloque."
                          % NOMBRE[dict(BLOQUES)[abre]]})

    # Una linea que ya tiene un fallo no recibe ademas la queja de las
    # variables. En «Algoritmo1» (pegado) o «frinAlgoritmo» las palabras mal
    # escritas parecen variables, y al estudiante se le acusaba de no declarar
    # algo que ni siquiera queria ser una variable. Se le dice una cosa por
    # linea: cuando la arregle y vuelva, se le dira la siguiente.
    problemas.extend(_sin_declarar(lineas, {p["linea"] for p in problemas}))
    problemas.sort(key=lambda p: p["linea"])
    return problemas


# Palabras que aparecen donde iria una variable pero no lo son.
_NO_SON_VARIABLES = CLAVES | {
    "verdadero", "falso", "mod", "div", "y", "o", "no", "raiz", "abs", "trunc",
    "redon", "sen", "cos", "tan", "ln", "exp", "azar", "longitud", "mayusculas",
    "minusculas", "subcadena", "concatenar", "convertiratexto", "convertiranumero",
}


def _sin_declarar(lineas, saltar=()):
    """Variables que se usan sin haberlas declarado con Definir.

    `saltar` son numeros de linea que ya tienen otro fallo: de ahi no se saca
    ninguna variable, porque lo que hay escrito no es de fiar.

    Es el error que mas se repite al empezar, y el conversor lo tapaba: se
    inventaba un valor inicial para que el programa funcionara, asi que el
    estudiante nunca se enteraba.

    Se avisa UNA vez con todas juntas, no una por variable: nadie arregla ocho
    avisos, y el arreglo es el mismo -anadir la linea Definir-.
    """
    declaradas, usadas, primera_linea = set(), {}, {}

    for n, cruda in enumerate(lineas, 1):
        linea = cruda.strip()
        if not linea or linea.startswith("//"):
            continue
        # Con unas comillas sin cerrar no se puede distinguir el texto del
        # codigo: en 'Escribir "hola' la palabra hola parece una variable, y
        # se acusaba al estudiante de no declararla. Ese fallo ya se le avisa
        # aparte, asi que aqui la linea se salta.
        if _comillas_impares(linea) or n in saltar:
            continue
        limpia = _sin_texto(linea)
        bajo = _norm(limpia)

        # La cabecera no aporta variables: su identificador es el nombre del
        # algoritmo. Antes se quitaba despues, y eso enmascaraba una variable
        # que se llamara igual que el algoritmo.
        # Sin \b al final a proposito: «Algoritmo1» y «fin algoritmo1» son
        # cabeceras mal escritas, no variables. El fallo de la cabecera ya se
        # avisa por su cuenta; de aqui no debe salir «no declaraste algoritmo1».
        if re.match(r"^\s*(?:fin\s*)?(?:algoritmo|proceso)", bajo):
            continue

        m = re.match(r"^\s*definir\s+(.+?)\s+como\s+\w+", bajo)
        if m:
            for v in re.split(r"[,\s]+", m.group(1)):
                if v:
                    declaradas.add(v)
            continue
        m = re.match(r"^\s*dimension\s+(.+)$", bajo)
        if m:
            for v in re.findall(r"([a-z_]\w*)\s*\[", m.group(1)):
                declaradas.add(v)
            continue

        for v in re.findall(r"\b([a-z_]\w*)\b", bajo):
            if v in _NO_SON_VARIABLES or v.isdigit():
                continue
            usadas.setdefault(v, 0)
            usadas[v] += 1
            primera_linea.setdefault(v, n)

    faltan = sorted(v for v in usadas if v not in declaradas)
    if not faltan:
        return []

    n = min(primera_linea[v] for v in faltan)
    nombres = ", ".join("«%s»" % v for v in faltan)
    return [{
        "linea": n,
        "texto": lineas[n - 1].strip(),
        "problema": ("Usas %s sin haberla declarado." % nombres) if len(faltan) == 1
                    else ("Usas estas variables sin declararlas: %s." % nombres),
        "sugerencia": "Toda variable se declara antes de usarla: "
                      "Definir %s Como Entero (o Real, Cadena, Logico)."
                      % ", ".join(sorted(faltan)),
    }]
