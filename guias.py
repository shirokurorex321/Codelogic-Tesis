# -*- coding: utf-8 -*-
"""Guía de cada ejercicio de CodeLogic.

Tres piezas por ejercicio, pensadas para que el estudiante no llegue en blanco:
  concepto → qué se practica y por qué importa
  pasos    → el plan, en lenguaje natural, sin darle el código
  ejemplo  → un caso PARECIDO ya resuelto, nunca el mismo

La distinción es deliberada: el ejemplo enseña el patrón, pero resolverlo sigue
siendo trabajo del estudiante.
"""

# ─────────────────────────────────────────────────────────────────────
# NO ES LA FUENTE. Este archivo es la semilla original, ya volcada a la
# tabla `exercises`, que es de donde la aplicacion sirve los ejercicios
# (las entregas apuntan a exercises.id, por eso tienen que ser filas).
#
# Nadie lo importa en caliente. Si vuelves a volcarlo pisaras lo que haya
# en la base, que es lo bueno: el 28/08/2026 las dos copias ya se habian
# separado en ortografia y hubo que sincronizarlas a mano.
#
# Para cambiar un ejercicio, cambia la fila. Este archivo se conserva solo
# como referencia de como se creo el material.
# ─────────────────────────────────────────────────────────────────────


GUIAS = {

1: {"concepto": "Tu primer algoritmo. Prácticas la estructura mínima que todo programa necesita: dónde empieza, dónde termina, y cómo mostrar algo en pantalla con Escribir.",
    "pasos": "Abre el algoritmo con Algoritmo y un nombre sin espacios\nUsa Escribir para mostrar el mensaje entre comillas\nCierra con FinAlgoritmo",
    "ejemplo": "// Muestra un mensaje distinto\nAlgoritmo MiPrimerPrograma\n    Escribir \"Estoy aprendiendo a programar\"\nFinAlgoritmo"},

2: {"concepto": "Combinas todo lo básico: declarar variables, leer datos del usuario, hacer una operación matemática y mostrar el resultado. Es el esqueleto de casi cualquier programa.",
    "pasos": "Declara tres variables enteras: los dos números y la suma\nAvisa al usuario y lee el primer número\nHaz lo mismo con el segundo\nGuarda en la tercera variable el resultado de sumar las dos\nMuestra el resultado",
    "ejemplo": "// Lo mismo pero restando\nAlgoritmo RestarDosNumeros\n    Definir a, b, resta Como Entero\n    Escribir \"Primer número:\"\n    Leer a\n    Escribir \"Segundo número:\"\n    Leer b\n    resta <- a - b\n    Escribir \"La resta es: \", resta\nFinAlgoritmo"},

3: {"concepto": "Trabajas con números decimales (tipo Real) y traduces una fórmula matemática a pseudocódigo. Ojo con el tipo: un área casi nunca es un número entero.",
    "pasos": "Declara radio y area como Real, porque llevan decimales\nPide el radio al usuario y léelo\nAplica la fórmula: area <- 3.1416 * radio * radio\nMuestra el área",
    "ejemplo": "// Misma idea con el perímetro\nAlgoritmo PerimetroDelCirculo\n    Definir radio, perimetro Como Real\n    Escribir \"Ingrese el radio:\"\n    Leer radio\n    perimetro <- 2 * 3.1416 * radio\n    Escribir \"El perímetro es: \", perimetro\nFinAlgoritmo"},

4: {"concepto": "Otra fórmula, pero con una trampa: el orden de las operaciones. La multiplicación y la división se hacen antes que la suma, igual que en matemáticas.",
    "pasos": "Declara celsius y fahrenheit como Real\nPide la temperatura en Celsius\nAplica F = C * 9 / 5 + 32\nMuestra el resultado",
    "ejemplo": "// La conversión inversa\nAlgoritmo FahrenheitACelsius\n    Definir fahrenheit, celsius Como Real\n    Escribir \"Temperatura en Fahrenheit:\"\n    Leer fahrenheit\n    celsius <- (fahrenheit - 32) * 5 / 9\n    Escribir \"En Celsius es: \", celsius\nFinAlgoritmo"},

5: {"concepto": "Un clásico que parece fácil hasta que lo intentas. Si haces A <- B y luego B <- A, el valor original de A ya se perdió. Necesitas una variable auxiliar que lo guarde temporalmente.",
    "pasos": "Declara A, B y una tercera variable auxiliar\nLee A y B\nGuarda el valor de A en la auxiliar\nPasa el valor de B a A\nPasa el valor de la auxiliar (el A original) a B\nMuestra los dos",
    "ejemplo": "// El mismo truco con dos textos\nAlgoritmo IntercambiarNombres\n    Definir nombre1, nombre2, temporal Como Cadena\n    nombre1 <- \"Ana\"\n    nombre2 <- \"Luis\"\n    temporal <- nombre1\n    nombre1 <- nombre2\n    nombre2 <- temporal\n    Escribir nombre1, \" y \", nombre2\nFinAlgoritmo"},

6: {"concepto": "Prácticas leer texto (tipo Cadena) y combinarlo con mensajes fijos en una sola línea de salida. Fíjate en los espacios dentro de las comillas.",
    "pasos": "Declara una variable de tipo Cadena para el nombre\nPregunta el nombre y léelo\nEscribe el saludo combinando texto y la variable, separados por comas",
    "ejemplo": "// Un saludo con dos datos\nAlgoritmo SaludoConCiudad\n    Definir nombre, ciudad Como Cadena\n    Escribir \"Tu nombre:\"\n    Leer nombre\n    Escribir \"Tu ciudad:\"\n    Leer ciudad\n    Escribir \"Hola \", nombre, \", saludos desde \", ciudad, \"!\"\nFinAlgoritmo"},

7: {"concepto": "Manejas tres variables de tipos distintos a la vez: dos de texto y una numérica. Elegir bien el tipo de cada una es parte del ejercicio.",
    "pasos": "Declara nombre y ciudad como Cadena, y edad como Entero\nPide y lee los tres datos, uno por uno\nMuestra los tres en una sola línea con un formato claro",
    "ejemplo": "// Tres datos de un libro\nAlgoritmo DatosDelLibro\n    Definir titulo, autor Como Cadena\n    Definir anio Como Entero\n    Escribir \"Titulo:\"\n    Leer titulo\n    Escribir \"Autor:\"\n    Leer autor\n    Escribir \"Anio:\"\n    Leer anio\n    Escribir titulo, \" - \", autor, \" (\", anio, \")\"\nFinAlgoritmo"},

8: {"concepto": "Un promedio simple, pero cuidado con los paréntesis: hay que sumar PRIMERO y dividir después. Sin ellos, solo se divide el segundo número.",
    "pasos": "Declara los dos números y el promedio como Real\nLee ambos números\nCalcula promedio <- (n1 + n2) / 2, con los paréntesis\nMuestra el promedio",
    "ejemplo": "// Promedio de tres números\nAlgoritmo PromedioDeTres\n    Definir a, b, c, promedio Como Real\n    Escribir \"Tres números:\"\n    Leer a\n    Leer b\n    Leer c\n    promedio <- (a + b + c) / 3\n    Escribir \"Promedio: \", promedio\nFinAlgoritmo"},

9: {"concepto": "Tu primer condicional. El programa deja de hacer siempre lo mismo y empieza a decidir según el dato que recibe.",
    "pasos": "Declara edad como Entero\nPide y lee la edad\nUsa Si edad >= 18 Entonces para el caso de mayor de edad\nUsa Sino para el otro caso\nCierra con FinSi",
    "ejemplo": "// Decidir si puede conducir\nAlgoritmo PuedeConducir\n    Definir edad Como Entero\n    Escribir \"Ingrese su edad:\"\n    Leer edad\n    Si edad >= 16 Entonces\n        Escribir \"Puede tramitar licencia\"\n    Sino\n        Escribir \"Aún no puede\"\n    FinSi\nFinAlgoritmo"},

10: {"concepto": "Comparar tres valores exige una estrategia. La más clara: supón que el primero es el mayor, y luego compara con los otros dos, actualizando si encuentras uno más grande.",
    "pasos": "Declara los tres números y una variable mayor\nLee los tres\nAsigna mayor <- el primer número\nSi el segundo es mayor que mayor, actualiza mayor\nHaz lo mismo con el tercero\nMuestra mayor",
    "ejemplo": "// La misma estrategia buscando el MENOR de dos\nAlgoritmo MenorDeDos\n    Definir a, b, menor Como Real\n    Leer a\n    Leer b\n    menor <- a\n    Si b < menor Entonces\n        menor <- b\n    FinSi\n    Escribir \"El menor es: \", menor\nFinAlgoritmo"},

11: {"concepto": "Conoces el operador MOD, que da el residuo de una división. Es la herramienta estándar para saber si un número es divisible por otro.",
    "pasos": "Declara numero como Entero\nLee el número\nPregunta Si numero MOD 2 = 0 Entonces es par\nEn el Sino, es impar",
    "ejemplo": "// Con MOD 3 en vez de MOD 2\nAlgoritmo MultiploDeTres\n    Definir numero Como Entero\n    Escribir \"Ingrese un número:\"\n    Leer numero\n    Si numero MOD 3 = 0 Entonces\n        Escribir \"Es múltiplo de 3\"\n    Sino\n        Escribir \"No es múltiplo de 3\"\n    FinSi\nFinAlgoritmo"},

12: {"concepto": "Tres casos posibles, no dos. Aquí necesitas condicionales anidados: un Si dentro del Sino de otro Si. El orden en que preguntas importa.",
    "pasos": "Declara numero como Real\nLee el número\nPregunta primero si es mayor que 0\nEn el Sino, pregunta si es menor que 0\nSi tampoco, solo puede ser cero\nRecuerda cerrar los dos FinSi",
    "ejemplo": "// Tres casos con la misma estructura\nAlgoritmo ClasificarEdad\n    Definir edad Como Entero\n    Leer edad\n    Si edad < 12 Entonces\n        Escribir \"Ninio\"\n    Sino\n        Si edad < 18 Entonces\n            Escribir \"Adolescente\"\n        Sino\n            Escribir \"Adulto\"\n        FinSi\n    FinSi\nFinAlgoritmo"},

13: {"concepto": "El ejercicio más largo del tema. Combinas comparación de texto (el símbolo de la operación) con varios condicionales anidados, y además debes prever un caso especial: la división entre cero.",
    "pasos": "Declara los dos números y el resultado como Real, y la operación como Caracter\nLee los tres datos\nCompara la operación con \"+\", \"-\", \"*\" y \"/\" usando Si anidados\nAntes de dividir, verifica que el segundo número no sea 0\nSi el símbolo no es ninguno de los cuatro, avisa que no es válido",
    "ejemplo": "// Version reducida con solo dos operaciones\nAlgoritmo SumaOResta\n    Definir a, b, resultado Como Real\n    Definir op Como Caracter\n    Leer a\n    Leer b\n    Escribir \"Operación (+ o -):\"\n    Leer op\n    Si op = \"+\" Entonces\n        resultado <- a + b\n        Escribir resultado\n    Sino\n        Si op = \"-\" Entonces\n            resultado <- a - b\n            Escribir resultado\n        Sino\n            Escribir \"Operación no válida\"\n        FinSi\n    FinSi\nFinAlgoritmo"},

14: {"concepto": "Un problema del mundo real con reglas escalonadas. La clave está en el ORDEN: debes preguntar primero por el descuento mayor. Si preguntas al revés, una compra de $200.000 recibiría el 10% en vez del 20%.",
    "pasos": "Declara compra, descuento y total como Real\nLee el valor de la compra\nPregunta PRIMERO si supera 100000, para el 20%\nEn el Sino, pregunta si supera 50000, para el 10%\nSi no cumple ninguna, el descuento es 0\nCalcula total <- compra - descuento y muestra ambos",
    "ejemplo": "// Dos niveles de recargo, misma lógica de orden\nAlgoritmo RecargoPorEnvio\n    Definir peso, recargo Como Real\n    Leer peso\n    Si peso > 20 Entonces\n        recargo <- 15000\n    Sino\n        Si peso > 5 Entonces\n            recargo <- 8000\n        Sino\n            recargo <- 0\n        FinSi\n    FinSi\n    Escribir \"Recargo: \", recargo\nFinAlgoritmo"},

15: {"concepto": "Tu primer ciclo. En vez de escribir diez líneas casi iguales, escribes una sola y le dices al computador que la repita. El contador del ciclo se usa dentro del cálculo.",
    "pasos": "Declara numero, i y resultado como Entero\nPide el número al usuario\nAbre un ciclo Para i desde 1 hasta 10 con paso 1\nDentro, calcula resultado <- numero * i\nMuestra la línea de la tabla usando numero, i y resultado\nCierra con FinPara",
    "ejemplo": "// Tabla, pero solo hasta el 5\nAlgoritmo TablaHastaCinco\n    Definir n, i, r Como Entero\n    Escribir \"Ingrese un número:\"\n    Leer n\n    Para i <- 1 Hasta 5 Con Paso 1 Hacer\n        r <- n * i\n        Escribir n, \" x \", i, \" = \", r\n    FinPara\nFinAlgoritmo"},

16: {"concepto": "Aquí aparece el acumulador, el patrón más importante de los ciclos: una variable que empieza en 0 y va creciendo en cada vuelta. Al terminar, contiene el total.",
    "pasos": "Declara n e i como Entero, y numero y suma como Real\nPregunta cuántos números va a ingresar y lee n\nInicializa suma <- 0 ANTES del ciclo\nAbre un Para desde 1 hasta n\nDentro: pide un numero, léelo, y hazlo suma <- suma + numero\nDespués del FinPara, muestra la suma",
    "ejemplo": "// Acumulador multiplicando en vez de sumando\nAlgoritmo ProductoDeNNumeros\n    Definir n, i Como Entero\n    Definir numero, producto Como Real\n    Escribir \"¿Cuántos números?\"\n    Leer n\n    producto <- 1\n    Para i <- 1 Hasta n Con Paso 1 Hacer\n        Leer numero\n        producto <- producto * numero\n    FinPara\n    Escribir \"El producto es: \", producto\nFinAlgoritmo"},

17: {"concepto": "Un ciclo que va hacia atrás. El paso negativo hace que el contador baje en lugar de subir. Es el mismo Para de siempre, con Con Paso -1.",
    "pasos": "Declara numero e i como Entero\nLee el número desde el que empieza la cuenta\nAbre el ciclo Para i desde numero hasta 1 con paso -1\nDentro, muestra i\nDespués del FinPara, escribe el mensaje final",
    "ejemplo": "// Cuenta regresiva fija, de 5 a 1\nAlgoritmo CuentaAtrasDeCinco\n    Definir i Como Entero\n    Para i <- 5 Hasta 1 Con Paso -1 Hacer\n        Escribir i\n    FinPara\n    Escribir \"Fin!\"\nFinAlgoritmo"},

18: {"concepto": "Un ciclo sin intervención del usuario: los límites ya están definidos en el enunciado. Puedes resolverlo de dos formas: recorriendo todos los números y filtrando los pares con un Si, o avanzando de dos en dos con Con Paso 2. La segunda es más elegante.",
    "pasos": "Declara i y suma como Entero\nInicializa suma <- 0\nAbre el ciclo desde 2 hasta 100 con paso 2, para pisar solo los pares\nDentro, acumula: suma <- suma + i\nDespués del ciclo, muestra el total",
    "ejemplo": "// Suma de los impares del 1 al 50\nAlgoritmo SumaDeImpares\n    Definir i, suma Como Entero\n    suma <- 0\n    Para i <- 1 Hasta 50 Con Paso 2 Hacer\n        suma <- suma + i\n    FinPara\n    Escribir \"Suma de impares: \", suma\nFinAlgoritmo"},

19: {"concepto": "Un acumulador que multiplica en vez de sumar. La diferencia crucial: debe empezar en 1, no en 0. Si empieza en 0, todo lo que multipliques dará 0.",
    "pasos": "Declara n, i y factorial como Entero\nLee n\nInicializa factorial <- 1 (nunca 0)\nAbre el ciclo Para i desde 1 hasta n\nDentro: factorial <- factorial * i\nMuestra el resultado después del ciclo",
    "ejemplo": "// Potencia: multiplicar la base por si misma n veces\nAlgoritmo Potencia\n    Definir base, exponente, i, resultado Como Entero\n    Leer base\n    Leer exponente\n    resultado <- 1\n    Para i <- 1 Hasta exponente Con Paso 1 Hacer\n        resultado <- resultado * base\n    FinPara\n    Escribir resultado\nFinAlgoritmo"},

20: {"concepto": "Juntas dos temas: un ciclo con acumulador para calcular el promedio, y un condicional al final para decidir si aprobó. Es el tipo de problema que combina lo aprendido.",
    "pasos": "Declara cantidad e i como Entero, y nota, suma y promedio como Real\nPregunta cuántas notas y léelo\nInicializa suma <- 0\nCon un ciclo Para, lee cada nota y acumúlala\nDespués del ciclo, calcula promedio <- suma / cantidad\nUsa un Si para mostrar si aprobó (promedio >= 3) o no",
    "ejemplo": "// Promedio de 3 notas fijas y decisión\nAlgoritmo PromedioDeTresNotas\n    Definir i Como Entero\n    Definir nota, suma, promedio Como Real\n    suma <- 0\n    Para i <- 1 Hasta 3 Con Paso 1 Hacer\n        Leer nota\n        suma <- suma + nota\n    FinPara\n    promedio <- suma / 3\n    Si promedio >= 3 Entonces\n        Escribir \"Aprobó con \", promedio\n    Sino\n        Escribir \"Reprobó con \", promedio\n    FinSi\nFinAlgoritmo"},

21: {"concepto": "Tu primer arreglo. La idea clave: en vez de cinco variables sueltas, una sola con cinco casillas. El contador del ciclo sirve de índice para recorrerlas.",
    "pasos": "Declara notas como Real y reserva el espacio con Dimension notas[5]\nDeclara i como Entero, y suma y promedio como Real\nInicializa suma <- 0\nCon un ciclo de 1 a 5, lee cada notas[i] y acumúlala en suma\nDespués del ciclo, divide entre 5\nMuestra el promedio",
    "ejemplo": "// Lo mismo con 3 casillas\nAlgoritmo PromedioDeTresEnArreglo\n    Definir datos Como Real\n    Dimension datos[3]\n    Definir i Como Entero\n    Definir suma, promedio Como Real\n    suma <- 0\n    Para i <- 1 Hasta 3 Con Paso 1 Hacer\n        Escribir \"Dato \", i, \":\"\n        Leer datos[i]\n        suma <- suma + datos[i]\n    FinPara\n    promedio <- suma / 3\n    Escribir \"Promedio: \", promedio\nFinAlgoritmo"},

22: {"concepto": "Buscar el mayor dentro de un arreglo. Usa la misma estrategia del ejercicio 10, pero ahora recorriendo casillas. Importante: inicializa el mayor con el PRIMER elemento, no con 0.",
    "pasos": "Declara el arreglo con Dimension numeros[6]\nLlena las 6 casillas con un ciclo\nAsigna mayor <- numeros[1]\nRecorre desde la posición 2 hasta la 6\nSi numeros[i] > mayor, actualiza mayor\nMuestra el mayor al final",
    "ejemplo": "// Buscar el MENOR en un arreglo de 4\nAlgoritmo MenorDelArreglo\n    Definir v Como Real\n    Dimension v[4]\n    Definir i Como Entero\n    Definir menor Como Real\n    Para i <- 1 Hasta 4 Con Paso 1 Hacer\n        Leer v[i]\n    FinPara\n    menor <- v[1]\n    Para i <- 2 Hasta 4 Con Paso 1 Hacer\n        Si v[i] < menor Entonces\n            menor <- v[i]\n        FinSi\n    FinPara\n    Escribir \"El menor es: \", menor\nFinAlgoritmo"},

23: {"concepto": "Contadores dentro de un ciclo con arreglo. Aquí no acumulas una suma, sino que cuentas cuántas veces se cumple una condición. Son dos contadores independientes.",
    "pasos": "Declara el arreglo con Dimension notas[8]\nDeclara i, aprobados y reprobados como Entero\nInicializa los dos contadores en 0\nEn un solo ciclo: lee cada nota y decide con un Si a que contador sumarle 1\nMuestra ambos totales al final",
    "ejemplo": "// Contar positivos y negativos en 5 números\nAlgoritmo ContarPositivos\n    Definir v Como Real\n    Dimension v[5]\n    Definir i, positivos, negativos Como Entero\n    positivos <- 0\n    negativos <- 0\n    Para i <- 1 Hasta 5 Con Paso 1 Hacer\n        Leer v[i]\n        Si v[i] >= 0 Entonces\n            positivos <- positivos + 1\n        Sino\n            negativos <- negativos + 1\n        FinSi\n    FinPara\n    Escribir \"Positivos: \", positivos\n    Escribir \"Negativos: \", negativos\nFinAlgoritmo"},

24: {"concepto": "Recorrer un arreglo al revés. No hace falta mover ni reordenar nada: basta con leerlo desde la última posición hacia la primera, usando un ciclo con paso negativo.",
    "pasos": "Declara el arreglo con Dimension numeros[5]\nLlena las 5 casillas con un ciclo normal, de 1 a 5\nAbre un SEGUNDO ciclo, esta vez desde 5 hasta 1 con paso -1\nDentro de ese segundo ciclo, muestra numeros[i]",
    "ejemplo": "// Mostrar 4 datos al revés\nAlgoritmo MostrarAlReves\n    Definir v Como Entero\n    Dimension v[4]\n    Definir i Como Entero\n    Para i <- 1 Hasta 4 Con Paso 1 Hacer\n        Escribir \"Dato \", i, \":\"\n        Leer v[i]\n    FinPara\n    Escribir \"En orden inverso:\"\n    Para i <- 4 Hasta 1 Con Paso -1 Hacer\n        Escribir v[i]\n    FinPara\nFinAlgoritmo"},
}
