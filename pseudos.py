# -*- coding: utf-8 -*-
"""Pseudocódigo canónico de los 24 ejercicios de CodeLogic.

Escrito en el estilo PSeInt que documenta CONVERSION_SYSTEM_PROMPT, tal como lo
escribiría un estudiante que resuelve bien el ejercicio. Sirve para dos cosas:
  1. Rellenar exercises.expected_pseudocode (la columna estaba vacía).
  2. Precargar la caché de IA, para que la primera vez que un estudiante envíe
     algo equivalente no gaste tokens.
"""

PSEUDOS = {
1: """Algoritmo HolaMundo
    Escribir "Hola Mundo"
FinAlgoritmo""",

2: """Algoritmo SumaDeDosNumeros
    Definir numero1, numero2, suma Como Entero
    Escribir "Ingrese el primer numero:"
    Leer numero1
    Escribir "Ingrese el segundo numero:"
    Leer numero2
    suma <- numero1 + numero2
    Escribir "La suma es: ", suma
FinAlgoritmo""",

3: """Algoritmo AreaDelCirculo
    Definir radio, area Como Real
    Escribir "Ingrese el radio del circulo:"
    Leer radio
    area <- 3.1416 * radio * radio
    Escribir "El area del circulo es: ", area
FinAlgoritmo""",

4: """Algoritmo ConversionTemperatura
    Definir celsius, fahrenheit Como Real
    Escribir "Ingrese la temperatura en grados Celsius:"
    Leer celsius
    fahrenheit <- celsius * 9 / 5 + 32
    Escribir "La temperatura en Fahrenheit es: ", fahrenheit
FinAlgoritmo""",

5: """Algoritmo IntercambioDeVariables
    Definir A, B, auxiliar Como Entero
    Escribir "Ingrese el valor de A:"
    Leer A
    Escribir "Ingrese el valor de B:"
    Leer B
    auxiliar <- A
    A <- B
    B <- auxiliar
    Escribir "Ahora A vale: ", A
    Escribir "Ahora B vale: ", B
FinAlgoritmo""",

6: """Algoritmo SaludoPersonalizado
    Definir nombre Como Cadena
    Escribir "Cual es tu nombre?"
    Leer nombre
    Escribir "Hola, ", nombre, "! Bienvenido a CodeLogic"
FinAlgoritmo""",

7: """Algoritmo DatosPersonales
    Definir nombre, ciudad Como Cadena
    Definir edad Como Entero
    Escribir "Ingrese su nombre:"
    Leer nombre
    Escribir "Ingrese su edad:"
    Leer edad
    Escribir "Ingrese su ciudad:"
    Leer ciudad
    Escribir "Nombre: ", nombre, " - Edad: ", edad, " - Ciudad: ", ciudad
FinAlgoritmo""",

8: """Algoritmo PromedioDeDosNumeros
    Definir numero1, numero2, promedio Como Real
    Escribir "Ingrese el primer numero:"
    Leer numero1
    Escribir "Ingrese el segundo numero:"
    Leer numero2
    promedio <- (numero1 + numero2) / 2
    Escribir "El promedio es: ", promedio
FinAlgoritmo""",

9: """Algoritmo MayorDeEdad
    Definir edad Como Entero
    Escribir "Ingrese su edad:"
    Leer edad
    Si edad >= 18 Entonces
        Escribir "Es mayor de edad"
    Sino
        Escribir "Es menor de edad"
    FinSi
FinAlgoritmo""",

10: """Algoritmo NumeroMayor
    Definir a, b, c, mayor Como Real
    Escribir "Ingrese el primer numero:"
    Leer a
    Escribir "Ingrese el segundo numero:"
    Leer b
    Escribir "Ingrese el tercer numero:"
    Leer c
    mayor <- a
    Si b > mayor Entonces
        mayor <- b
    FinSi
    Si c > mayor Entonces
        mayor <- c
    FinSi
    Escribir "El numero mayor es: ", mayor
FinAlgoritmo""",

11: """Algoritmo ParOImpar
    Definir numero Como Entero
    Escribir "Ingrese un numero entero:"
    Leer numero
    Si numero MOD 2 = 0 Entonces
        Escribir "El numero es par"
    Sino
        Escribir "El numero es impar"
    FinSi
FinAlgoritmo""",

12: """Algoritmo PositivoNegativoOCero
    Definir numero Como Real
    Escribir "Ingrese un numero:"
    Leer numero
    Si numero > 0 Entonces
        Escribir "El numero es positivo"
    Sino
        Si numero < 0 Entonces
            Escribir "El numero es negativo"
        Sino
            Escribir "El numero es cero"
        FinSi
    FinSi
FinAlgoritmo""",

13: """Algoritmo CalculadoraSimple
    Definir numero1, numero2, resultado Como Real
    Definir operacion Como Caracter
    Escribir "Ingrese el primer numero:"
    Leer numero1
    Escribir "Ingrese el segundo numero:"
    Leer numero2
    Escribir "Ingrese la operacion (+, -, *, /):"
    Leer operacion
    Si operacion = "+" Entonces
        resultado <- numero1 + numero2
        Escribir "El resultado es: ", resultado
    Sino
        Si operacion = "-" Entonces
            resultado <- numero1 - numero2
            Escribir "El resultado es: ", resultado
        Sino
            Si operacion = "*" Entonces
                resultado <- numero1 * numero2
                Escribir "El resultado es: ", resultado
            Sino
                Si operacion = "/" Entonces
                    Si numero2 = 0 Entonces
                        Escribir "Error: no se puede dividir entre cero"
                    Sino
                        resultado <- numero1 / numero2
                        Escribir "El resultado es: ", resultado
                    FinSi
                Sino
                    Escribir "Operacion no valida"
                FinSi
            FinSi
        FinSi
    FinSi
FinAlgoritmo""",

14: """Algoritmo DescuentoDeTienda
    Definir compra, descuento, total Como Real
    Escribir "Ingrese el valor de la compra:"
    Leer compra
    Si compra > 100000 Entonces
        descuento <- compra * 0.20
    Sino
        Si compra > 50000 Entonces
            descuento <- compra * 0.10
        Sino
            descuento <- 0
        FinSi
    FinSi
    total <- compra - descuento
    Escribir "Descuento aplicado: ", descuento
    Escribir "Total a pagar: ", total
FinAlgoritmo""",

15: """Algoritmo TablaDeMultiplicar
    Definir numero, i, resultado Como Entero
    Escribir "Ingrese un numero:"
    Leer numero
    Para i <- 1 Hasta 10 Con Paso 1 Hacer
        resultado <- numero * i
        Escribir numero, " x ", i, " = ", resultado
    FinPara
FinAlgoritmo""",

16: """Algoritmo SumaDeNNumeros
    Definir n, i Como Entero
    Definir numero, suma Como Real
    Escribir "Cuantos numeros va a ingresar?"
    Leer n
    suma <- 0
    Para i <- 1 Hasta n Con Paso 1 Hacer
        Escribir "Ingrese el numero ", i, ":"
        Leer numero
        suma <- suma + numero
    FinPara
    Escribir "La suma total es: ", suma
FinAlgoritmo""",

17: """Algoritmo ContadorRegresivo
    Definir numero, i Como Entero
    Escribir "Ingrese un numero entero positivo:"
    Leer numero
    Para i <- numero Hasta 1 Con Paso -1 Hacer
        Escribir i
    FinPara
    Escribir "Despegue!"
FinAlgoritmo""",

18: """Algoritmo SumaDePares
    Definir i, suma Como Entero
    suma <- 0
    Para i <- 2 Hasta 100 Con Paso 2 Hacer
        suma <- suma + i
    FinPara
    Escribir "La suma de los pares entre 2 y 100 es: ", suma
FinAlgoritmo""",

19: """Algoritmo Factorial
    Definir n, i, factorial Como Entero
    Escribir "Ingrese un numero entero positivo:"
    Leer n
    factorial <- 1
    Para i <- 1 Hasta n Con Paso 1 Hacer
        factorial <- factorial * i
    FinPara
    Escribir "El factorial de ", n, " es: ", factorial
FinAlgoritmo""",

20: """Algoritmo PromedioDeNotasConCiclo
    Definir cantidad, i Como Entero
    Definir nota, suma, promedio Como Real
    Escribir "Cuantas notas tiene?"
    Leer cantidad
    suma <- 0
    Para i <- 1 Hasta cantidad Con Paso 1 Hacer
        Escribir "Ingrese la nota ", i, ":"
        Leer nota
        suma <- suma + nota
    FinPara
    promedio <- suma / cantidad
    Escribir "El promedio es: ", promedio
    Si promedio >= 3 Entonces
        Escribir "Aprobo"
    Sino
        Escribir "Reprobo"
    FinSi
FinAlgoritmo""",

21: """Algoritmo PromedioDeNotas
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
    Escribir "El promedio de las notas es: ", promedio
FinAlgoritmo""",

22: """Algoritmo MayorDeUnArreglo
    Definir numeros Como Real
    Dimension numeros[6]
    Definir i Como Entero
    Definir mayor Como Real
    Para i <- 1 Hasta 6 Con Paso 1 Hacer
        Escribir "Ingrese el numero ", i, ":"
        Leer numeros[i]
    FinPara
    mayor <- numeros[1]
    Para i <- 2 Hasta 6 Con Paso 1 Hacer
        Si numeros[i] > mayor Entonces
            mayor <- numeros[i]
        FinSi
    FinPara
    Escribir "El numero mayor es: ", mayor
FinAlgoritmo""",

23: """Algoritmo ContarAprobados
    Definir notas Como Real
    Dimension notas[8]
    Definir i, aprobados, reprobados Como Entero
    aprobados <- 0
    reprobados <- 0
    Para i <- 1 Hasta 8 Con Paso 1 Hacer
        Escribir "Ingrese la nota del estudiante ", i, ":"
        Leer notas[i]
        Si notas[i] >= 3 Entonces
            aprobados <- aprobados + 1
        Sino
            reprobados <- reprobados + 1
        FinSi
    FinPara
    Escribir "Aprobados: ", aprobados
    Escribir "Reprobados: ", reprobados
FinAlgoritmo""",

24: """Algoritmo InvertirUnArreglo
    Definir numeros Como Entero
    Dimension numeros[5]
    Definir i Como Entero
    Para i <- 1 Hasta 5 Con Paso 1 Hacer
        Escribir "Ingrese el numero ", i, ":"
        Leer numeros[i]
    FinPara
    Escribir "Los numeros en orden inverso son:"
    Para i <- 5 Hasta 1 Con Paso -1 Hacer
        Escribir numeros[i]
    FinPara
FinAlgoritmo""",
}
