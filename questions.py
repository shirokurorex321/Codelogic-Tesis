"""Instrumentos de investigación del estudio cuasiexperimental.

- TEST_QUESTIONS: banco de 20 ítems de opción múltiple sobre fundamentos de
  algoritmos y pseudocódigo. El mismo instrumento se aplica como pretest y
  postest (diseño pretest-postest). Antes de aplicarlo debe pasar por la
  validación de contenido con los expertos del programa (ver metodología);
  este archivo se puede editar libremente para incorporar sus observaciones.

- SELF_EFFICACY_ITEMS: escala de autoeficacia en programación (10 ítems,
  Likert 1-5), adaptada de Ramalingam y Wiedenbeck (1998) al contexto local.

Cada pregunta: id único, tema, enunciado, opciones (4) y el índice (0-3)
de la respuesta correcta. El puntaje se calcula sobre 100.
"""

TEST_QUESTIONS = [
    # ── Variables y tipos de datos ──
    {
        "id": "q01", "topic": "Variables",
        "text": "¿Qué instrucción declara correctamente una variable entera en pseudocódigo?",
        "options": [
            "Definir edad Como Entero",
            "entero edad;",
            "edad = Entero",
            "Variable edad Tipo Numero",
        ],
        "answer": 0,
    },
    {
        "id": "q02", "topic": "Variables",
        "text": "¿Qué tipo de dato es el más adecuado para guardar el nombre de una persona?",
        "options": ["Entero", "Real", "Cadena", "Logico"],
        "answer": 2,
    },
    {
        "id": "q03", "topic": "Variables",
        "text": "Después de ejecutar:  x <- 5  y luego  x <- x + 3,  ¿cuál es el valor de x?",
        "options": ["5", "3", "8", "53"],
        "answer": 2,
    },
    {
        "id": "q04", "topic": "Variables",
        "text": "En pseudocódigo, el símbolo  <-  significa:",
        "options": [
            "Comparar dos valores",
            "Asignar un valor a una variable",
            "Restar y luego comparar",
            "Declarar una variable",
        ],
        "answer": 1,
    },
    # ── Entrada y salida ──
    {
        "id": "q05", "topic": "Entrada/Salida",
        "text": "¿Qué instrucción muestra un mensaje en pantalla?",
        "options": ["Leer", "Escribir", "Definir", "Asignar"],
        "answer": 1,
    },
    {
        "id": "q06", "topic": "Entrada/Salida",
        "text": "Para que el usuario ingrese su edad y el programa la guarde en la variable edad, se usa:",
        "options": [
            "Escribir edad",
            "Definir edad",
            "Leer edad",
            "Mostrar edad",
        ],
        "answer": 2,
    },
    {
        "id": "q07", "topic": "Entrada/Salida",
        "text": "¿Qué muestra este algoritmo?\n\nAlgoritmo X\n    Definir a Como Entero\n    a <- 4\n    Escribir \"El doble es: \", a * 2\nFinAlgoritmo",
        "options": [
            "El doble es: 4",
            "El doble es: 8",
            "El doble es: a * 2",
            "Error: falta Leer",
        ],
        "answer": 1,
    },
    # ── Condicionales ──
    {
        "id": "q08", "topic": "Condicionales",
        "text": "¿Cuándo se ejecuta el bloque Sino de una estructura Si-Entonces-Sino?",
        "options": [
            "Siempre, después del bloque Entonces",
            "Cuando la condición es verdadera",
            "Cuando la condición es falsa",
            "Nunca; es solo decorativo",
        ],
        "answer": 2,
    },
    {
        "id": "q09", "topic": "Condicionales",
        "text": "Si  nota <- 3.8,  ¿qué escribe este fragmento?\n\nSi nota >= 3.0 Entonces\n    Escribir \"Aprobado\"\nSino\n    Escribir \"Reprobado\"\nFinSi",
        "options": ["Aprobado", "Reprobado", "3.8", "No escribe nada"],
        "answer": 0,
    },
    {
        "id": "q10", "topic": "Condicionales",
        "text": "¿Cuál condición es verdadera cuando un número n es par?",
        "options": [
            "n / 2 = 0",
            "n % 2 = 0",
            "n * 2 = 0",
            "n - 2 = 0",
        ],
        "answer": 1,
    },
    {
        "id": "q11", "topic": "Condicionales",
        "text": "Para escribir \"Mayor\" solo cuando  edad >= 18  y  edad <= 65,  la condición correcta es:",
        "options": [
            "edad >= 18 O edad <= 65",
            "edad >= 18 Y edad <= 65",
            "edad = 18 Y edad = 65",
            "edad > 18 O edad < 65",
        ],
        "answer": 1,
    },
    # ── Ciclos ──
    {
        "id": "q12", "topic": "Ciclos",
        "text": "¿Cuántas veces se ejecuta el cuerpo de este ciclo?\n\nPara i <- 1 Hasta 5 Hacer\n    Escribir i\nFinPara",
        "options": ["4", "5", "6", "Infinitas"],
        "answer": 1,
    },
    {
        "id": "q13", "topic": "Ciclos",
        "text": "¿Qué escribe este algoritmo?\n\ns <- 0\nPara i <- 1 Hasta 3 Hacer\n    s <- s + i\nFinPara\nEscribir s",
        "options": ["3", "6", "123", "0"],
        "answer": 1,
    },
    {
        "id": "q14", "topic": "Ciclos",
        "text": "Un ciclo Mientras se repite:",
        "options": [
            "Un número fijo de veces, siempre",
            "Mientras su condición sea verdadera",
            "Hasta que su condición sea verdadera",
            "Solo una vez",
        ],
        "answer": 1,
    },
    {
        "id": "q15", "topic": "Ciclos",
        "text": "¿Qué le pasa a este ciclo?\n\nx <- 1\nMientras x > 0 Hacer\n    x <- x + 1\nFinMientras",
        "options": [
            "Se ejecuta exactamente una vez",
            "No se ejecuta nunca",
            "Nunca termina (ciclo infinito)",
            "Da error de sintaxis",
        ],
        "answer": 2,
    },
    {
        "id": "q16", "topic": "Ciclos",
        "text": "Para mostrar la tabla de multiplicar del 7 (del 1 al 10), lo más adecuado es:",
        "options": [
            "Escribir 10 veces la instrucción Escribir 7 * n",
            "Un ciclo Para i desde 1 hasta 10 que escriba 7 * i",
            "Un Si-Entonces con 10 condiciones",
            "Leer 10 números y sumarlos",
        ],
        "answer": 1,
    },
    # ── Arreglos ──
    {
        "id": "q17", "topic": "Arreglos",
        "text": "Un arreglo (vector) sirve para:",
        "options": [
            "Guardar un solo valor que cambia de tipo",
            "Guardar varios valores del mismo tipo bajo un mismo nombre",
            "Repetir instrucciones",
            "Tomar decisiones",
        ],
        "answer": 1,
    },
    {
        "id": "q18", "topic": "Arreglos",
        "text": "Si  notas[3]  guarda las notas {2.5, 4.0, 3.7}  (posiciones 1, 2 y 3), ¿qué vale notas[2]?",
        "options": ["2.5", "4.0", "3.7", "No se puede saber"],
        "answer": 1,
    },
    # ── Lógica / seguimiento ──
    {
        "id": "q19", "topic": "Lógica",
        "text": "¿Qué escribe este algoritmo?\n\na <- 2\nb <- 7\nSi a > b Entonces\n    Escribir a\nSino\n    Escribir b\nFinSi",
        "options": ["2", "7", "a", "b"],
        "answer": 1,
    },
    {
        "id": "q20", "topic": "Lógica",
        "text": "Un algoritmo se define como:",
        "options": [
            "Un lenguaje de programación",
            "Un programa que solo corre en computadores",
            "Una secuencia ordenada y finita de pasos para resolver un problema",
            "Un diagrama que no se puede ejecutar",
        ],
        "answer": 2,
    },
]

# ── Escala de autoeficacia (Likert 1-5) ──
# 1 = Nada seguro/a · 5 = Totalmente seguro/a
SELF_EFFICACY_ITEMS = [
    {"id": "e01", "text": "Escribir un algoritmo sencillo que lea datos y muestre un resultado."},
    {"id": "e02", "text": "Entender qué hace un pseudocódigo escrito por otra persona."},
    {"id": "e03", "text": "Encontrar el error en un algoritmo que no produce el resultado esperado."},
    {"id": "e04", "text": "Corregir ese error una vez lo encuentro."},
    {"id": "e05", "text": "Escribir un algoritmo que use condicionales (Si-Entonces-Sino)."},
    {"id": "e06", "text": "Escribir un algoritmo que use ciclos (Para, Mientras)."},
    {"id": "e07", "text": "Usar un arreglo para guardar y recorrer varios valores."},
    {"id": "e08", "text": "Dividir un problema grande en pasos pequeños antes de programarlo."},
    {"id": "e09", "text": "Terminar un ejercicio de programación aunque al inicio parezca difícil."},
    {"id": "e10", "text": "Aprender por mi cuenta un concepto nuevo de programación usando ejemplos."},
]

LIKERT_LABELS = [
    "Nada seguro/a",
    "Poco seguro/a",
    "Medianamente seguro/a",
    "Bastante seguro/a",
    "Totalmente seguro/a",
]

# ── Carga cognitiva percibida (escala 1-9) ──
# Adaptación de 3 ítems de la escala de inversión de esfuerzo mental de Paas (1992).
# Se aplica después de cada actividad práctica, no en pretest/postest.
# 1 = muy bajo esfuerzo · 9 = muy alto esfuerzo
COGNITIVE_LOAD_ITEMS = [
    {"id": "cc1", "text": "¿Cuánto esfuerzo mental invertiste para resolver esta actividad?"},
    {"id": "cc2", "text": "¿Qué tan difícil te resultó la actividad en sí misma?"},
    {"id": "cc3", "text": "¿Cuánto esfuerzo te costó entender el enunciado y las instrucciones?"},
]

COGNITIVE_LOAD_LABELS = {
    1: "Muy bajo",
    3: "Bajo",
    5: "Medio",
    7: "Alto",
    9: "Muy alto",
}
