# -*- coding: utf-8 -*-
"""Contenido pedagógico de CodeLogic.

Antes de esto, el estudiante veía una descripción de una línea por tema y
pasaba directo a programar. La tesis sostiene que ese salto sin andamiaje es
una de las causas del fracaso en cursos introductorios (Vygotsky, zona de
desarrollo próximo; Sweller, carga cognitiva), así que aquí se enseña el
concepto antes de pedir que se aplique.

Redactado para estudiantes de primer semestre SIN experiencia previa.
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

"sintaxis": """// SALIDA: mostrar en pantalla
Escribir "Hola mundo"           // texto tal cual
Escribir edad                    // el contenido de la variable
Escribir "Tu edad es: ", edad    // combinando ambos, separados por comas

// ENTRADA: pedir un dato al usuario
Leer edad                        // espera y guarda lo escrito en edad

// El patrón correcto: avisar ANTES de leer
Escribir "Ingrese su edad:"
Leer edad""",

"ejemplo": """Algoritmo SaludoPersonalizado
    Definir nombre Como Cadena
    Definir edad Como Entero

    Escribir "¿Cual es tu nombre?"
    Leer nombre

    Escribir "¿Cuantos anios tienes?"
    Leer edad

    Escribir "Hola ", nombre, ", tienes ", edad, " anios."
FinAlgoritmo""",

"ejemplo_explicacion": """Escribir "¿Cual es tu nombre?"
    Muestra la pregunta. Sin esto el programa se quedaría esperando sin que el
    usuario sepa por qué.

Leer nombre
    El programa se detiene aquí. Lo que la persona escriba y confirme con Enter
    queda guardado en la variable nombre.

Escribir "¿Cuantos anios tienes?"
Leer edad
    El mismo patrón: primero avisar, después leer.

Escribir "Hola ", nombre, ", tienes ", edad, " anios."
    Arma una frase mezclando texto fijo y el contenido de las variables. Si la
    persona escribió Daniel y 20, en pantalla aparece:
    Hola Daniel, tienes 20 anios.

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
    Escribir "Aprobo"
Sino
    Escribir "Reprobo"
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

"errores": """• Usar = para comparar cuando ya lo usaste para asignar. En pseudocódigo se
  asigna con <- y se compara con =. Nunca uses <- dentro de un Si.

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
Mientras saldo > 0 Hacer
    saldo <- saldo - 100
FinMientras

// ACUMULADOR: el patrón para sumar dentro de un ciclo
suma <- 0                                 // SIEMPRE empieza en 0
Para i <- 1 Hasta 5 Con Paso 1 Hacer
    suma <- suma + i                      // se le agrega en cada vuelta
FinPara""",

"ejemplo": """Algoritmo SumarNumerosDelUsuario
    Definir cantidad, i Como Entero
    Definir numero, suma Como Real

    Escribir "¿Cuantos numeros va a sumar?"
    Leer cantidad

    suma <- 0

    Para i <- 1 Hasta cantidad Con Paso 1 Hacer
        Escribir "Ingrese el numero ", i, ":"
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

    Escribir "Ingrese el numero ", i, ":"
        Aquí se aprovecha el contador para que el mensaje diga
        "Ingrese el numero 1:", después "2:", etc.

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

// Leer el valor de una posición
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
  va Desde 1 Hasta el tamaño.

• Escribir notas sin índice cuando quieres una casilla concreta. notas es el
  arreglo completo; notas[3] es la tercera casilla.

• Poner el cálculo del promedio dentro del ciclo, y que salga un promedio
  parcial en cada vuelta.

• Al recorrer buscando el mayor, inicializarlo en 0. Si todos los números
  fueran negativos, el resultado sería incorrecto. Es mejor empezar con el
  primer elemento del arreglo.""",
}
