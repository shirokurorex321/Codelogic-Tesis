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


def revisar(pseudocodigo):
    """Devuelve una lista de problemas: {linea, texto, problema, sugerencia}."""
    problemas = []
    lineas = (pseudocodigo or "").split("\n")
    pila = []          # bloques abiertos: (palabra, numero de linea)

    for n, cruda in enumerate(lineas, 1):
        linea = cruda.strip()
        if not linea or linea.startswith("//"):
            continue
        limpia = _sin_texto(linea)
        bajo = _norm(limpia)
        palabras = re.findall(r"[a-z]+", bajo)
        primera = palabras[0] if palabras else ""

        # comillas sin cerrar
        if linea.count('"') % 2:
            problemas.append({
                "linea": n, "texto": linea,
                "problema": "Hay unas comillas sin cerrar.",
                "sugerencia": "Todo texto entre comillas tiene que abrirlas y cerrarlas.",
                "corregida": linea.rstrip() + '"'})

        # cierres
        if primera in CIERRES:
            esperado = CIERRES[primera]
            if not pila:
                problemas.append({
                    "linea": n, "texto": linea,
                    "problema": "Aparece %s pero no hay ningun %s abierto." % (linea.split()[0], NOMBRE[esperado]),
                    "sugerencia": "Un cierre solo tiene sentido si antes se abrio el bloque."})
            elif pila[-1][0] != esperado:
                # Lo que falta no es este cierre: son los bloques de dentro que
                # siguen abiertos. Se avisa de cada uno y despues SI se cierra
                # el que toca, para no decir luego que quedo sin cerrar cuando
                # el estudiante si lo habia cerrado.
                while pila and pila[-1][0] != esperado:
                    abierto, ln = pila.pop()
                    problemas.append({
                        "linea": ln, "texto": lineas[ln - 1].strip(),
                        "problema": "Este %s se abre en la linea %d y no se cierra."
                                    % (NOMBRE[abierto], ln),
                        "sugerencia": "Escribe %s antes del %s de la linea %d."
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
            es_asignacion = "<-" in limpia or re.match(r"^\s*[\w\[\]]+\s*=", limpia)
            if primera and not es_asignacion and primera not in CLAVES:
                cercanas = [k for k in CLAVES
                            if len(k) > 3 and _distancia(primera, k) == 1]
                if cercanas:
                    buena = NOMBRE.get(cercanas[0], cercanas[0].capitalize())
                    problemas.append({
                        "linea": n, "texto": linea,
                        "problema": "«%s» no es una palabra del pseudocodigo." % linea.split()[0],
                        "sugerencia": "La palabra correcta es %s." % buena,
                        "corregida": _corregir_palabra(linea, linea.split()[0], buena)})

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
        if linea.count('"') % 2 or n in saltar:
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
