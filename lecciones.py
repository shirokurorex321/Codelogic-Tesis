# -*- coding: utf-8 -*-
"""Contenido pedagógico de CodeLogic.

Antes de esto, el estudiante veía una descripción de una línea por tema y
pasaba directo a programar. La tesis sostiene que ese salto sin andamiaje es
una de las causas del fracaso en cursos introductorios (Vygotsky, zona de
desarrollo próximo; Sweller, carga cognitiva), así que aquí se enseña el
concepto antes de pedir que se aplique.

Redactado para estudiantes de primer semestre SIN experiencia previa.

FUENTE UNICA del texto de las lecciones desde el 28/08/2026. Lo leen las dos
paginas que lo muestran: /aprender/<id> y /exercises/<id>. Antes esta segunda
lo sacaba de unas columnas topics.leccion_* con una copia del mismo texto; las
dos copias se separaron dos veces (una dejo cinco temas en blanco, otra dejo la
ortografia a medias), asi que esas columnas se retiraron.

Para cambiar una leccion se cambia aqui, y basta con reiniciar el servicio.
"""

LECCIONES = {

# ════════════════════════════════════════════════════════════════════
1: {  # Variables y Tipos de Datos
"que_es": """Una variable es un espacio en la memoria del computador donde guardas un dato para usarlo después. Piensa en una caja con una etiqueta: la etiqueta es el nombre y lo que hay adentro es el valor.

Si escribes edad <- 20, le estás diciendo al computador: "guarda el número 20 en una caja llamada edad". Más adelante puedes usar esa caja sin recordar el número: basta con escribir edad.

¿Para qué sirve? Para que un algoritmo funcione con cualquier dato, no con uno fijo. Un programa que calcula el área de UN círculo de radio 5 sirve de poco. Uno que usa una variable radio sirve para todos los círculos.

Cada variable tiene un tipo, que le dice al computador qué clase de dato va a guardar:

• Entero  → números sin decimales: 7, -3, 150
• Real    → números con decimales: 3.5, -0.28, 3.1416
• Cadena  → texto: "Daniel", "Hola mundo"
• Logico  → solo dos valores posibles: Verdadero o Falso""",

"sintaxis": """// Declarar: reservar la caja y decir qué tipo de dato guarda
Definir edad Como Entero
Definir promedio Como Real
Definir nombre Como Cadena
Definir aprobado Como Logico

// Varias del mismo tipo, separadas por comas
Definir suma, resta, total Como Entero

// Asignar: meter un valor en la caja. La flecha <- apunta al destino
edad <- 20
promedio <- 4.5
nombre <- "Daniel"
aprobado <- Verdadero

// Una variable puede cambiar de valor: el nuevo reemplaza al anterior
edad <- 21""",

"ejemplo": """Algoritmo DatosDeUnEstudiante
    Definir nombre Como Cadena
    Definir edad Como Entero
    Definir promedio Como Real

    nombre <- "Ana"
    edad <- 19
    promedio <- 4.2

    Escribir "Estudiante: ", nombre
    Escribir "Edad: ", edad
    Escribir "Promedio: ", promedio
FinAlgoritmo""",

"ejemplo_explicacion": """Definir nombre Como Cadena
    Reserva una caja llamada nombre que guardará texto.

Definir edad Como Entero
    Otra caja, esta para un número sin decimales.

Definir promedio Como Real
    Una tercera, para un número con decimales. El promedio necesita ser Real
    porque 4.2 no es un entero.

nombre <- "Ana"
    Mete el texto Ana en la caja nombre. Va entre comillas porque es texto.

edad <- 19
    Mete el número 19. Sin comillas: es un número, no texto.

Escribir "Estudiante: ", nombre
    Muestra en pantalla. Lo que va entre comillas sale tal cual; nombre sin
    comillas se reemplaza por su contenido. En pantalla se lee:
    Estudiante: Ana""",

"errores": """• Usar una variable sin declararla antes. Siempre va primero el Definir.

• Confundir el tipo. Si declaras Definir promedio Como Entero y luego intentas
  guardar 4.2, pierdes los decimales.

• Olvidar las comillas en el texto. nombre <- Ana da error; lo correcto es
  nombre <- "Ana".

• Ponerle comillas a los números. edad <- "19" guarda el TEXTO 19, y con texto
  no se puede sumar ni restar.

• Confundir el sentido de la flecha. Se escribe edad <- 20 (el valor entra a la
  variable), nunca 20 -> edad.""",
},

# ════════════════════════════════════════════════════════════════════
2: {  # Entrada y Salida
"que_es": """Hasta ahora los valores los escribías tú dentro del algoritmo. Pero un programa útil trabaja con datos que le da el usuario mientras se ejecuta.

Para eso existen dos instrucciones:

• Leer  → el programa se detiene, espera a que la persona escriba algo por el
          teclado, y guarda lo escrito en una variable. Es la ENTRADA.

• Escribir → el programa muestra un mensaje o el contenido de una variable en
             la pantalla. Es la SALIDA.

¿Para qué sirve? Es la diferencia entre un algoritmo que suma 5 + 3 siempre, y
uno que suma los dos números que la persona quiera.

Una regla de oro: antes de cada Leer, escribe siempre un mensaje que diga qué
se espera. Si el programa se queda esperando en silencio, el usuario no sabe
qué hacer.""",

"sintaxis": """Definir edad Como Entero
edad <- 20                       // para que los ejemplos de abajo tengan qué mostrar

// SALIDA: mostrar en pantalla
Escribir "Hola mundo"            // texto tal cual
Escribir edad                    // el contenido de la variable: 20
Escribir "Tu edad es: ", edad    // combinando ambos, separados por comas

// ENTRADA: pedir un dato al usuario
Leer edad                        // espera y guarda lo escrito en edad

// El patrón correcto: avisar ANTES de leer
Escribir "Ingrese su edad:"
Leer edad""",

"ejemplo": """Algoritmo SaludoPersonalizado
    Definir nombre Como Cadena
    Definir edad Como Entero

    Escribir "¿Cuál es tu nombre?"
    Leer nombre

    Escribir "¿Cuántos años tienes?"
    Leer edad

    Escribir "Hola ", nombre, ", tienes ", edad, " años."
FinAlgoritmo""",

"ejemplo_explicacion": """Escribir "¿Cuál es tu nombre?"
    Muestra la pregunta. Sin esto el programa se quedaría esperando sin que el
    usuario sepa por qué.

Leer nombre
    El programa se detiene aquí. Lo que la persona escriba y confirme con Enter
    queda guardado en la variable nombre.

Escribir "¿Cuántos años tienes?"
Leer edad
    El mismo patrón: primero avisar, después leer.

Escribir "Hola ", nombre, ", tienes ", edad, " años."
    Arma una frase mezclando texto fijo y el contenido de las variables. Si la
    persona escribió Daniel y 20, en pantalla aparece:
    Hola Daniel, tienes 20 años.

    Fíjate en los espacios dentro de las comillas: sin ellos saldría
    HolaDaniel, pegado.""",

"errores": """• Leer sin avisar antes. El programa parece congelado y el usuario no sabe
  que debe escribir algo.

• Leer en una variable que no declaraste.

• Leer un número en una variable de tipo Cadena. Después no podrás hacer
  cuentas con ese dato.

• Olvidar las comas al combinar. Escribir "Hola " nombre da error; lo correcto
  es Escribir "Hola ", nombre.

• Olvidar los espacios dentro de las comillas, y que el texto salga pegado.""",
},

# ════════════════════════════════════════════════════════════════════
3: {  # Estructuras Condicionales
"que_es": """Hasta ahora tus algoritmos ejecutaban todas las líneas, siempre, de arriba abajo. Un condicional le permite al programa TOMAR DECISIONES: hacer una cosa u otra según lo que esté pasando.

Es lo mismo que haces todos los días: SI está lloviendo ENTONCES llevo sombrilla, SI NO salgo sin ella.

La estructura es Si ... Entonces ... Sino ... FinSi. El programa evalúa una condición, que solo puede ser verdadera o falsa:

• Si es verdadera → ejecuta lo que está después de Entonces
• Si es falsa     → ejecuta lo que está después de Sino

El Sino es opcional. Si no lo pones y la condición es falsa, simplemente no se
hace nada y el programa sigue.

Para construir condiciones usas operadores de comparación:

    =    igual a              <>   distinto de
    >    mayor que            <    menor que
    >=   mayor o igual que    <=   menor o igual que

Y puedes combinar varias con Y (deben cumplirse ambas) y O (basta con una).""",

"sintaxis": """// Forma simple: solo actúa si se cumple
Si edad >= 18 Entonces
    Escribir "Es mayor de edad"
FinSi

// Con alternativa
Si nota >= 3 Entonces
    Escribir "Aprobó"
Sino
    Escribir "Reprobó"
FinSi

// Encadenados: cuando hay más de dos casos
Si numero > 0 Entonces
    Escribir "Positivo"
Sino
    Si numero < 0 Entonces
        Escribir "Negativo"
    Sino
        Escribir "Cero"
    FinSi
FinSi

// Condiciones combinadas
Si edad >= 18 Y tieneCedula = Verdadero Entonces
    Escribir "Puede votar"
FinSi""",

"ejemplo": """Algoritmo ClasificarNota
    Definir nota Como Real

    Escribir "Ingrese la nota (0 a 5):"
    Leer nota

    Si nota >= 4 Entonces
        Escribir "Excelente"
    Sino
        Si nota >= 3 Entonces
            Escribir "Aprobado"
        Sino
            Escribir "Reprobado"
        FinSi
    FinSi
FinAlgoritmo""",

"ejemplo_explicacion": """Si nota >= 4 Entonces
    Evalúa si la nota es 4 o más. Si la persona escribió 4.5, es verdadero y
    muestra Excelente. Ahí termina: no revisa las demás condiciones.

Sino
    Solo llega aquí si la nota fue MENOR que 4.

    Si nota >= 3 Entonces
        Como ya sabemos que es menor que 4, esta pregunta equivale a
        "¿está entre 3 y 4?". Por eso no hace falta escribir
        nota >= 3 Y nota < 4.

    Sino
        Si tampoco llegó a 3, solo queda una posibilidad: reprobado.

FinSi
FinSi
    Dos cierres porque hay dos Si abiertos. Cada Si necesita su FinSi, y el de
    adentro se cierra primero.

Fíjate en el orden: primero la condición más exigente (>= 4) y después la
menos. Al revés no funcionaría: una nota de 4.5 también cumple >= 3 y
mostraría Aprobado en vez de Excelente.""",

"errores": """• Usar <- en vez de = dentro de un Si. En pseudocódigo se asigna con <- y se
  compara con =: un <- dentro de una condición no compara nada.

• Olvidar el FinSi. Cada Si necesita el suyo, y los de adentro se cierran
  primero.

• Ordenar mal las condiciones encadenadas. Si preguntas nota >= 3 antes que
  nota >= 4, todas las notas altas caerán en el primer caso.

• Comparar textos sin comillas: Si respuesta = si está mal;
  lo correcto es Si respuesta = "si".

• Escribir condiciones imposibles, como Si edad > 18 Y edad < 10, que nunca se
  cumplen.""",
},
}

# ════════════════════════════════════════════════════════════════════
LECCIONES[4] = {  # Ciclos y Repeticiones
"que_es": """Imagina que quieres mostrar la tabla del 7. Podrías escribir diez líneas de Escribir, una por cada multiplicación. ¿Y si fuera hasta el 100? ¿Y si el usuario elige hasta dónde?

Un ciclo permite repetir un bloque de instrucciones varias veces sin escribirlo varias veces. Es una de las ideas más potentes de la programación: escribes el paso UNA vez y le dices al computador cuántas veces repetirlo.

Hay dos que usarás casi siempre:

• Para → cuando SABES cuántas veces repetir. "Del 1 al 10", "las 5 notas".
         Lleva un contador que avanza solo.

• Mientras → cuando NO sabes cuántas veces, y dependes de una condición.
             "Mientras el usuario no escriba 0", "mientras el saldo sea
             positivo".

El contador del Para es una variable normal que va cambiando en cada vuelta.
Si escribes Para i <- 1 Hasta 5, la variable i vale 1 en la primera vuelta,
2 en la segunda, y así hasta 5. Puedes usar ese valor dentro del ciclo.

Un patrón que verás mucho es el acumulador: una variable que empieza en 0 y va
sumando en cada vuelta. Al terminar el ciclo tiene el total.""",

"sintaxis": """// PARA: se repite un número conocido de veces
Para i <- 1 Hasta 10 Con Paso 1 Hacer
    Escribir i
FinPara

// El paso puede ser distinto de 1
Para i <- 2 Hasta 20 Con Paso 2 Hacer    // solo los pares
    Escribir i
FinPara

// O ir hacia atrás, con paso negativo
Para i <- 10 Hasta 1 Con Paso -1 Hacer   // cuenta regresiva
    Escribir i
FinPara

// MIENTRAS: se repite mientras la condición sea verdadera
saldo <- 1000                             // tiene que valer algo ANTES de preguntar
Mientras saldo > 0 Hacer
    saldo <- saldo - 100                  // 1000, 900, 800... hasta 0: 10 vueltas
FinMientras

// ACUMULADOR: el patrón para sumar dentro de un ciclo
suma <- 0                                 // SIEMPRE empieza en 0
Para i <- 1 Hasta 5 Con Paso 1 Hacer
    suma <- suma + i                      // se le agrega en cada vuelta
FinPara""",

"ejemplo": """Algoritmo SumarNumerosDelUsuario
    Definir cantidad, i Como Entero
    Definir numero, suma Como Real

    Escribir "¿Cuántos números va a sumar?"
    Leer cantidad

    suma <- 0

    Para i <- 1 Hasta cantidad Con Paso 1 Hacer
        Escribir "Ingrese el número ", i, ":"
        Leer numero
        suma <- suma + numero
    FinPara

    Escribir "La suma total es: ", suma
FinAlgoritmo""",

"ejemplo_explicacion": """suma <- 0
    El acumulador empieza en cero ANTES del ciclo. Si lo pusieras adentro, se
    reiniciaría en cada vuelta y al final valdría solo el último número.

Para i <- 1 Hasta cantidad Con Paso 1 Hacer
    Repite tantas veces como el usuario haya indicado. Si escribió 3, el
    bloque se ejecuta 3 veces con i valiendo 1, luego 2, luego 3.

    Escribir "Ingrese el número ", i, ":"
        Aquí se aprovecha el contador para que el mensaje diga
        "Ingrese el número 1:", después "2:", etc.

    Leer numero
        La variable numero se sobrescribe en cada vuelta. No importa: su valor
        ya se guardó en suma.

    suma <- suma + numero
        El corazón del acumulador. Se lee: "el nuevo valor de suma es lo que
        ya tenía MÁS el número recién leído".

FinPara
    Cierra el ciclo. Todo lo que está entre Para y FinPara se repite.

Escribir "La suma total es: ", suma
    Va DESPUÉS del FinPara. Si estuviera adentro mostraría un total parcial en
    cada vuelta.""",

"errores": """• No inicializar el acumulador en 0 antes del ciclo, o inicializarlo adentro.

• Poner el Escribir del resultado dentro del ciclo, y ver el mensaje repetido
  en cada vuelta.

• Ciclo infinito con Mientras: si la condición nunca se vuelve falsa, el
  programa no termina. Algo dentro del ciclo debe modificar la variable de la
  condición.

• Confundir cuándo usar cada uno: si sabes el número de repeticiones usa Para;
  si depende de una condición, Mientras.

• Modificar el contador i dentro del ciclo. El Para ya lo maneja solo.

• Olvidar el FinPara o el FinMientras.""",
}

# ════════════════════════════════════════════════════════════════════
LECCIONES[5] = {  # Arreglos
"que_es": """Con lo que sabes hasta ahora, guardar 5 notas exige 5 variables: nota1, nota2, nota3, nota4, nota5. ¿Y si fueran 100? ¿Y si el usuario decide cuántas?

Un arreglo (también llamado vector) es una variable que guarda MUCHOS valores del mismo tipo bajo un solo nombre. En lugar de 5 cajas sueltas, es una fila de 5 casillas numeradas.

Cada casilla tiene una posición, llamada índice, que escribes entre corchetes:

    notas[1]  → la primera casilla
    notas[2]  → la segunda
    notas[5]  → la quinta

Lo verdaderamente útil aparece al combinarlos con ciclos: en vez de escribir
una línea por casilla, usas el contador del ciclo como índice y recorres todo
el arreglo con dos o tres líneas.

Ese es el patrón central del tema: un ciclo Para cuyo contador va recorriendo
las posiciones del arreglo.

Nota importante: en PSeInt los arreglos empiezan en la posición 1. En otros
lenguajes como Python o C++ empiezan en 0, algo que te encontrarás cuando
conviertas tu pseudocódigo.""",

"sintaxis": """// Declarar: primero el tipo, después el tamaño
Definir notas Como Real
Dimension notas[5]                    // 5 casillas: de notas[1] a notas[5]

// Guardar un valor en una posición concreta
notas[1] <- 4.5
notas[2] <- 3.8

// Consultar el valor de una posición (ojo: consultar no es Leer)
Escribir notas[1]

// LLENAR el arreglo con un ciclo (el patrón que más usarás)
Para i <- 1 Hasta 5 Con Paso 1 Hacer
    Escribir "Ingrese la nota ", i, ":"
    Leer notas[i]                     // el contador hace de índice
FinPara

// RECORRER para sumar
suma <- 0
Para i <- 1 Hasta 5 Con Paso 1 Hacer
    suma <- suma + notas[i]
FinPara""",

"ejemplo": """Algoritmo PromedioDeCincoNotas
    Definir notas Como Real
    Dimension notas[5]
    Definir i Como Entero
    Definir suma, promedio Como Real

    suma <- 0

    Para i <- 1 Hasta 5 Con Paso 1 Hacer
        Escribir "Ingrese la nota ", i, ":"
        Leer notas[i]
        suma <- suma + notas[i]
    FinPara

    promedio <- suma / 5

    Escribir "El promedio es: ", promedio
FinAlgoritmo""",

"ejemplo_explicacion": """Definir notas Como Real
Dimension notas[5]
    Dos pasos: el primero dice qué tipo de dato guarda cada casilla, el segundo
    cuántas casillas hay. Ambos son necesarios.

suma <- 0
    El acumulador, igual que en los ciclos. Va antes del Para.

Para i <- 1 Hasta 5 Con Paso 1 Hacer
    Cinco vueltas, una por casilla. La variable i vale 1, 2, 3, 4 y 5.

    Leer notas[i]
        La clave de todo el tema. En la primera vuelta i vale 1, así que esta
        línea equivale a Leer notas[1]. En la segunda, a Leer notas[2]. Con una
        sola línea llenas las cinco casillas.

    suma <- suma + notas[i]
        Aprovecha la misma vuelta para ir sumando. Podrías hacerlo en un ciclo
        aparte, pero así recorres el arreglo una sola vez.

FinPara

promedio <- suma / 5
    Fuera del ciclo, cuando suma ya tiene el total de las cinco.""",

"errores": """• Olvidar el Dimension. Solo con Definir no se reserva el espacio.

• Salirse del rango. Si el arreglo es notas[5], la posición notas[6] no existe
  y da error. Tampoco notas[0] en PSeInt.

• Empezar el ciclo en 0. En PSeInt la primera casilla es la 1, así que el ciclo
  va de 1 hasta el tamaño: Para i <- 1 Hasta 5 Con Paso 1 Hacer.

• Escribir notas sin índice cuando quieres una casilla concreta. notas es el
  arreglo completo; notas[3] es la tercera casilla.

• Poner el cálculo del promedio dentro del ciclo, y que salga un promedio
  parcial en cada vuelta.

• Al recorrer buscando el mayor, inicializarlo en 0. Si todos los números
  fueran negativos, el resultado sería incorrecto. Es mejor empezar con el
  primer elemento del arreglo.""",
}


# ─────────────────────────────────────────────────────────────────────
# Lecciones de PRIMER SEMESTRE (temas 6 a 10).
#
# Se escriben aparte, y no se reutilizan las de tercero, porque el plan de
# primero pide cosas que aquellas no explican: Segun sea, el ciclo Mientras,
# Repetir-Hasta Que y los metodos de ordenamiento.
# ─────────────────────────────────────────────────────────────────────

LECCIONES.update({

6: {  # Datos, Variables y Operadores
    "que_es": """Un dato es cualquier cosa que el programa necesita recordar: una edad, un
nombre, un precio. Una variable es la caja donde guardas ese dato para poder
usarlo más adelante, y el tipo dice qué clase de cosa cabe en esa caja.

Hay cuatro tipos básicos: Entero para números sin decimales (12, -5), Real
para números con decimales (3.14, 4.5), Cadena para texto ("Ana") y Logico
para lo que solo puede ser verdadero o falso.

Con esas cajas construyes expresiones: combinaciones de variables y
operadores que el computador calcula hasta dejar un solo valor. Los
operadores son de tres familias, y conviene no mezclarlas: los aritméticos
dan números, los relacionales dan verdadero o falso, y los lógicos combinan
varias condiciones en una sola.""",

    "sintaxis": """// Partimos de dos números concretos, para poder comprobar cada resultado
Definir a, b Como Entero
a <- 7
b <- 2

// ARITMÉTICOS: dan un número
suma <- a + b              // 9
resta <- a - b             // 5
producto <- a * b          // 14
division <- a / b          // 3.5   la división exacta, con decimales
entera <- trunc(a / b)     // 3     se queda con la parte de delante de la coma
resto <- a MOD b           // 1     lo que sobra al dividir

// RELACIONALES: dan Verdadero o Falso
a = b      // Falso       ¿son iguales?
a <> b     // Verdadero   ¿son distintos?
a > b      // Verdadero
a < b      // Falso
a >= b     // Verdadero
a <= b     // Falso

// LÓGICOS: combinan valores Verdadero/Falso
Definir edad Como Entero
Definir tieneLicencia Como Logico
edad <- 20
tieneLicencia <- Verdadero

edad >= 18 Y tieneLicencia     // Verdadero   Y  exige las DOS
edad < 12 O edad > 65          // Falso       O  se conforma con UNA
NO(tieneLicencia)              // Falso       NO le da la vuelta""",

    "ejemplo": """Algoritmo RevisarLosPuntos
    Definir puntos, faltan Como Entero
    Definir aprobo Como Logico

    Escribir "¿Cuántos puntos sacó? (de 0 a 100)"
    Leer puntos

    aprobo <- puntos >= 60 Y puntos <= 100
    faltan <- 100 - puntos

    Escribir "Puntos obtenidos: ", puntos
    Escribir "Aprobó: ", aprobo
    Escribir "Le faltan para el máximo: ", faltan
    Escribir "Es un puntaje redondo: ", (puntos MOD 10) = 0
FinAlgoritmo""",

    "ejemplo_explicacion": """Definir puntos, faltan Como Entero
    Los dos son números sin decimales. Trabajar con Enteros cuando los
    datos son enteros evita resultados como 0.7999999999999998, que
    aparecen al restar números con decimales.

Definir aprobo Como Logico
    Una caja que solo puede guardar Verdadero o Falso. No un número, no un
    texto: una de esas dos cosas.

aprobo <- puntos >= 60 Y puntos <= 100
    Aquí está la idea importante. "puntos >= 60" NO es una pregunta: es un
    valor, Verdadero o Falso. La Y junta los dos y el resultado, que
    también es Verdadero o Falso, se guarda en la caja aprobo.

faltan <- 100 - puntos
    Una expresión aritmética: primero se calcula la resta y después el
    resultado se guarda en la caja de la izquierda.

Escribir "Es un puntaje redondo: ", (puntos MOD 10) = 0
    Dos familias de operadores en una sola línea. Primero MOD calcula lo
    que sobra al dividir entre 10, y después el = compara ese resto con
    cero. Lo que se muestra en pantalla no es un número: es Verdadero o
    Falso.""",

    "errores": """• Confundir / con MOD. La división te dice cuántas veces cabe; MOD te dice
  lo que sobra. Para saber si un número es par se usa MOD, no /.

• Usar el tipo equivocado. Si defines un promedio Como Entero, 4.5 se
  guardará como 4 y el cálculo saldrá mal sin avisar.

• Escribir 1 y 0 en vez de Verdadero y Falso. Un Logico no es un número.

• Encadenar comparaciones como en matemáticas. "1 <= nota <= 5" no
  funciona: hay que escribir "nota >= 1 Y nota <= 5".

• Olvidar que Y exige las dos condiciones y O se conforma con una. Cambiar
  una por otra es el error más común al escribir un requisito."""
},

7: {  # Estructura Secuencial
    "que_es": """Un algoritmo secuencial es el más simple que existe: las instrucciones se
ejecutan una detrás de otra, de arriba abajo, sin saltos ni repeticiones.
Como una receta de cocina, donde no puedes hornear antes de mezclar.

Casi todos los programas siguen el mismo patrón de tres tiempos: primero
ENTRAN los datos (Leer), después se PROCESAN (los cálculos y asignaciones),
y al final SALE el resultado (Escribir). Si respetas ese orden, la mayoría
de los errores desaparecen solos.

El detalle que más cuesta al principio es que el orden importa de verdad: no
puedes calcular un promedio antes de haber leído las notas, porque en ese
momento las cajas todavía están vacías.""",

    "sintaxis": """Definir edad, cantidad, contador Como Entero
Definir precio, total Como Real

// SALIDA: mostrar algo en pantalla
Escribir "Hola"
total <- 5000
Escribir "El total es: ", total    // la coma pega el texto y el valor

// ENTRADA: pedirle un dato al usuario
Leer edad

// Casi siempre van juntos: primero avisas, luego lees
Escribir "Ingrese su edad:"
Leer edad

// ASIGNACIÓN: guardar un valor en una variable
total <- 0                  // un valor fijo
Leer precio                 // primero ENTRAN los datos...
Leer cantidad
total <- precio * cantidad  // ...y sólo después se calcula con ellos

// Un contador tiene que existir ANTES de poder crecer
contador <- 0
contador <- contador + 1    // se lee: el nuevo contador es el viejo más 1""",

    "ejemplo": """Algoritmo CalcularElTotal
    Definir precio, total Como Real
    Definir cantidad Como Entero

    Escribir "Precio del producto:"
    Leer precio
    Escribir "¿Cuántas unidades?"
    Leer cantidad

    total <- precio * cantidad

    Escribir "Total a pagar: ", total
FinAlgoritmo""",

    "ejemplo_explicacion": """Escribir "Precio del producto:"
    Antes de leer se avisa. Si no, el usuario ve la pantalla parada sin
    saber qué se espera de él.

Leer precio
    El programa se detiene aquí hasta que el usuario teclee un valor. Ese
    valor queda guardado en la caja precio.

total <- precio * cantidad
    Primero se calcula lo de la derecha y después se guarda en la caja de
    la izquierda. La flecha siempre apunta hacia donde se guarda.

Escribir "Total a pagar: ", total
    El resultado va al final, cuando ya existe. Si esta línea estuviera
    antes del cálculo, mostraría una caja vacía.""",

    "errores": """• Calcular antes de leer. Si pones el total antes del Leer, la operación
  se hace con cajas vacías y el resultado no significa nada.

• Leer sin avisar. El programa parece colgado porque nadie dijo que había
  que escribir algo.

• Invertir la asignación. Se escribe total <- precio, nunca precio <- total
  si lo que quieres es llenar total. La flecha apunta al destino.

• Mostrar el nombre de la variable en vez de su valor:
  Escribir "total" muestra la palabra total; Escribir total muestra 5000.

• Olvidar Definir antes de usar una variable."""
},

8: {  # Estructuras de Seleccion
    "que_es": """Hasta ahora el programa hacía siempre lo mismo. Con las estructuras de
selección aprende a decidir: mira una condición y, según sea verdadera o
falsa, toma un camino u otro.

La forma más simple es Si-Entonces: si se cumple, haz esto; si no, sigue de
largo. Cuando hay dos caminos se usa Si-Entonces-Sino: uno de los dos se
ejecuta siempre, nunca los dos.

Cuando las opciones son muchas y todas comparan la MISMA variable contra
valores concretos, Segun ... Hacer (lo que también se llama Segun sea) queda
mucho más claro que una escalera de Si encadenados. Y si una decisión depende de otra, se meten unas dentro de
otras: eso son las condiciones anidadas.""",

    "sintaxis": """// Un solo camino
Si edad >= 18 Entonces
    Escribir "Es mayor de edad"
FinSi

// Dos caminos: uno de los dos se ejecuta siempre
Si nota >= 3 Entonces
    Escribir "Aprobó"
Sino
    Escribir "Reprobó"
FinSi

// Anidada: una decisión dentro de otra
Si numero > 0 Entonces
    Escribir "Positivo"
Sino
    Si numero < 0 Entonces
        Escribir "Negativo"
    Sino
        Escribir "Es cero"
    FinSi
FinSi

// Selección múltiple: misma variable, muchos valores
Segun opcion Hacer
    1:
        Escribir "Sumar"
    2:
        Escribir "Restar"
    De Otro Modo:
        Escribir "Esa opción no existe"
FinSegun""",

    "ejemplo": """Algoritmo ClasificarLaEdad
    Definir edad Como Entero

    Escribir "Ingrese su edad:"
    Leer edad

    Si edad < 0 Entonces
        Escribir "Esa edad no es válida"
    Sino
        Si edad < 18 Entonces
            Escribir "Menor de edad"
        Sino
            Escribir "Mayor de edad"
        FinSi
    FinSi
FinAlgoritmo""",

    "ejemplo_explicacion": """Si edad < 0 Entonces
    Lo primero es descartar lo imposible. Validar antes de clasificar evita
    tener que repetir la comprobación en cada rama.

Sino
    Si edad < 18 Entonces
    Este Si vive DENTRO del Sino anterior, y solo se evalúa cuando la edad
    ya se sabe válida. Fíjate en la sangría: cada nivel se mueve a la
    derecha, y eso es lo que permite leer el camino de un vistazo.

FinSi
FinSi
    Dos Si abiertos, dos FinSi. Se cierran de dentro hacia afuera: el
    último que abriste es el primero que cierras.""",

    "errores": """• Usar <- en vez de = dentro de un Si. Se asigna con <- y se compara
  con =. Un <- dentro de una condición no compara nada.

• Olvidar un FinSi. Cada Si necesita el suyo, y los de adentro se cierran
  primero.

• Ordenar mal las condiciones. Si preguntas nota >= 3 antes que nota >= 4,
  todas las notas altas caerán en el primer caso y nunca llegarán al
  segundo.

• Poner dos Si seguidos cuando querías Si-Sino. Con dos Si independientes
  ambos se evalúan; con Si-Sino solo uno de los dos.

• Olvidar De Otro Modo en un Segun. Si el usuario escribe algo que no
  está en ningún caso, el programa no responde nada."""
},

9: {  # Estructuras de Repeticion
    "que_es": """Un ciclo repite un bloque de instrucciones sin que tengas que escribirlo
muchas veces. La pregunta que decide cuál usar es una sola: cuándo sabes de
antemano cuántas vueltas hay que dar.

Si lo sabes, usa Para: le dices desde dónde, hasta dónde y de cuánto en
cuánto, y él se encarga de contar. Si NO lo sabes y solo conoces la
condición para seguir, usa Mientras: repite mientras se cumpla, y si no se
cumple desde el principio no entra ni una vez.

Repetir-Hasta Que es el hermano del Mientras con una diferencia clave:
ejecuta primero y pregunta después, así que siempre da al menos una vuelta.
Por eso es el que se usa para validar datos: hay que pedir el dato una vez
antes de poder comprobarlo.

Dentro de los ciclos viven dos patrones que vas a usar toda la vida: el
contador, que suma de uno en uno para llevar la cuenta, y el acumulador,
que va sumando valores para obtener un total.""",

    "sintaxis": """// PARA: sabes cuántas vueltas
Para i <- 1 Hasta 10 Con Paso 1 Hacer
    Escribir i
FinPara

// MIENTRAS: repite mientras se cumpla; puede no entrar nunca
suma <- 0
Leer numero                 // la PRIMERA lectura va fuera del ciclo
Mientras numero <> 0 Hacer
    suma <- suma + numero
    Leer numero             // sin esta línea el ciclo no termina nunca
FinMientras

// REPETIR: ejecuta y DESPUÉS pregunta; entra al menos una vez
Repetir
    Escribir "Ingrese una edad válida:"
    Leer edad
Hasta Que edad >= 0 Y edad <= 120

// Contador y acumulador: los dos se ponen a cero ANTES del ciclo
cuantos <- 0
suma <- 0
cuantos <- cuantos + 1        // contador: cuenta veces
suma <- suma + numero         // acumulador: suma valores

// Anidados: por CADA vuelta del de fuera, el de dentro da todas las suyas
Para i <- 1 Hasta 3 Con Paso 1 Hacer
    Para j <- 1 Hasta 5 Con Paso 1 Hacer
        Escribir i, " x ", j, " = ", i * j
    FinPara
FinPara""",

    "ejemplo": """Algoritmo PromedioConCentinela
    Definir nota, suma, promedio Como Real
    Definir cuantas Como Entero

    suma <- 0
    cuantas <- 0

    Escribir "Ingrese una nota (o -1 para terminar):"
    Leer nota

    Mientras nota <> -1 Hacer
        suma <- suma + nota
        cuantas <- cuantas + 1
        Escribir "Ingrese una nota (o -1 para terminar):"
        Leer nota
    FinMientras

    Si cuantas > 0 Entonces
        promedio <- suma / cuantas
        Escribir "Notas ingresadas: ", cuantas
        Escribir "El promedio es: ", promedio
    Sino
        Escribir "No se ingresó ninguna nota"
    FinSi
FinAlgoritmo""",

    "ejemplo_explicacion": """suma <- 0
cuantas <- 0
    Dos cajas en cero antes de empezar. suma es el ACUMULADOR (guarda el
    total) y cuantas es el CONTADOR (cuenta cuántas veces se repitió). Son
    dos cosas distintas y casi siempre van juntas.

Escribir "Ingrese una nota (o -1 para terminar):"
Leer nota
    Esta primera lectura va FUERA del ciclo. Sin ella, el Mientras no
    tendría ningún valor que evaluar en su primera vuelta.

Mientras nota <> -1 Hacer
    Aquí no se sabe cuántas vueltas habrá: dependen de cuándo el usuario
    decida parar. Por eso Mientras y no Para. El -1 es el centinela: un
    valor acordado que significa "ya terminé".

    cuantas <- cuantas + 1
        El contador sube de uno en uno. Al final tendrá el número de notas.

    Leer nota
        La última línea del ciclo vuelve a leer. Si se olvida, nota nunca
        cambia y el ciclo se repite para siempre.

Si cuantas > 0 Entonces
    La división solo se hace si de verdad hubo notas. Si el usuario escribe
    -1 de entrada, cuantas vale 0 y dividir entre cero rompería el programa.""",

    "errores": """• Inicializar el acumulador dentro del ciclo. Se pone en cero antes, o se
  reinicia en cada vuelta y el total sale mal.

• Olvidar modificar la variable de la condición en un Mientras. Si nada
  cambia dentro, la condición se cumple siempre y el ciclo no termina
  nunca.

• Usar Mientras cuando sabes el número de vueltas. Funciona, pero te
  obliga a llevar el contador a mano y es más fácil equivocarse.

• Poner el resultado dentro del ciclo. Casi siempre va después del
  FinPara, cuando el cálculo ya terminó.

• En los ciclos anidados, usar la misma variable para los dos. El de
  dentro pisaría la cuenta del de fuera: usa i y j, no i e i.

• Empezar un acumulador de multiplicaciones en 0. Todo lo que multipliques
  dará 0: en ese caso se empieza en 1."""
},

10: {  # Vectores
    "que_es": """Un vector es una caja con muchos compartimentos numerados, todos del mismo
tipo y bajo un solo nombre. En vez de definir nota1, nota2, nota3... defines
notas[5] y accedes a cada una por su posición.

Esa posición se llama índice, y es lo que hace poderoso al vector: como el
índice es un número, puedes recorrerlo con un ciclo. Un Para que vaya de 1
hasta 5 toca todos los compartimentos sin que escribas cinco líneas.

Con el recorrido se construye todo lo demás: buscar un valor, calcular el
mayor o el promedio, ordenarlos de menor a mayor. Y cuando necesitas guardar
dos cosas de la misma persona (su nombre y su nota) usas dos vectores
paralelos: la posición 3 de uno se corresponde con la posición 3 del otro.""",

    "sintaxis": """// Declarar: primero el tipo, después el tamaño
Definir notas Como Real
Dimension notas[5]

// Acceder a una posición concreta
notas[1] <- 4.5
Escribir notas[1]

// Llenar y recorrer: siempre con un ciclo
Para i <- 1 Hasta 5 Con Paso 1 Hacer
    Leer notas[i]
FinPara

// Buscar (búsqueda lineal)
Leer buscado               // el valor que queremos encontrar
posicion <- 0              // 0 significa "no está"
Para i <- 1 Hasta 5 Con Paso 1 Hacer
    Si notas[i] = buscado Entonces
        posicion <- i
    FinSi
FinPara

// Intercambiar dos posiciones: SIEMPRE con una auxiliar
aux <- notas[1]
notas[1] <- notas[2]
notas[2] <- aux""",

    "ejemplo": """Algoritmo MayorYPromedio
    Definir notas Como Real
    Dimension notas[4]
    Definir i Como Entero
    Definir mayor, suma Como Real

    Para i <- 1 Hasta 4 Con Paso 1 Hacer
        Escribir "Nota ", i, ":"
        Leer notas[i]
    FinPara

    mayor <- notas[1]
    suma <- notas[1]

    Para i <- 2 Hasta 4 Con Paso 1 Hacer
        Si notas[i] > mayor Entonces
            mayor <- notas[i]
        FinSi
        suma <- suma + notas[i]
    FinPara

    Escribir "La mayor es: ", mayor
    Escribir "El promedio es: ", suma / 4
FinAlgoritmo""",

    "ejemplo_explicacion": """Definir notas Como Real
Dimension notas[4]
    Dos líneas: la primera dice que guardará números con decimales, la
    segunda cuántos compartimentos tendrá.

mayor <- notas[1]
    Aquí está el detalle que más se falla. El mayor arranca con el PRIMER
    elemento, no con cero: si todas las notas fueran negativas, un cero
    inicial ganaría siempre y el resultado sería falso.

Para i <- 2 Hasta 4 Con Paso 1 Hacer
    Empieza en 2 porque la posición 1 ya se usó para arrancar. Compararla
    consigo misma no aportaría nada.

Si notas[i] > mayor Entonces
    mayor <- notas[i]
    Si el de esta posición es más grande que el campeón actual, pasa a ser
    el nuevo campeón. Al terminar el recorrido, mayor tiene el más grande
    de todos.""",

    "errores": """• Inicializar el mayor en 0 en vez de con el primer elemento. Con datos
  negativos el resultado sale mal.

• Salirse del vector. Si declaraste notas[5], la posición 6 no existe y el
  programa falla.

• Intercambiar sin variable auxiliar. Si haces a <- b y luego b <- a, los
  dos quedan con el mismo valor: el primero se perdió al ser pisado.

• Confundir la posición con el valor. notas[3] es lo que hay guardado en
  la tercera casilla; el 3 es la casilla, no la nota.

• Recorrer con un ciclo que no llega al final, o que empieza en 0 cuando
  el vector arranca en 1.

• En vectores paralelos, ordenar uno y no el otro. Se rompe la
  correspondencia y los nombres dejan de coincidir con sus notas."""
},

})
