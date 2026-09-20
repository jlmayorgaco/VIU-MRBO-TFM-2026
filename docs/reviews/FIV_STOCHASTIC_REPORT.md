# Informe F-IV — Piloto temporal con eventos exógenos

## Pregunta

¿Conocer la secuencia futura de llegadas, finalizaciones y fallos permite
reducir el coste frente a resolver de nuevo el juego estático en cada evento?

## Diseño

E8 contiene 30 mundo–semilla: cinco geometrías por seis semillas, `N=5`, `K=3`
y la misma secuencia de eventos para cada política. Se compararon Geo-QPG desde
cero, Geo-QPG activado por evento con warm start y un programa dinámico central
de horizonte finito con conocimiento perfecto de los eventos.

El coste descontado suma déficit normalizado, recorrido normalizado y cambios
de coalición. También se registraron tasa de servicio, pasos con demanda
incumplida, conmutaciones y mensajes. El oráculo no envía mensajes porque es
central; ese cero no representa una arquitectura desplegable.

## Resultados

Las medianas de coste fueron 2,823 para re-solving, 2,590 para warm start y
2,180 para el oráculo. Frente a re-solving, la diferencia pareada
oráculo–myopic fue −0,486 (IC bootstrap del 95 %: −0,649 a −0,415; Holm
`p=5,59×10⁻⁹`). Frente a warm start fue −0,415 (IC del 95 %: −0,486 a −0,329;
Holm `p=5,59×10⁻⁹`).

Warm start empató con re-solving en 15 mundos, ganó en 12 y perdió en tres. Su
diferencia pareada mediana fue cero, aunque redujo las medianas de cambios de
12,5 a 11,5 y de mensajes de 544,5 a 446,5. Se interpreta como ahorro de
recourse, no como anticipación del futuro.

El oráculo hizo cinco cambios medianos, pero su tasa media de servicio fue
95,6 %, frente a 97,8 % en ambas políticas Geo-QPG. El objetivo escalar prefirió
en algunos episodios aceptar demanda incumplida para evitar otros costes.

## Respuesta

La información futura redujo el coste escalar definido, pero no produjo una
dominancia Pareto: sacrificó tasa de servicio en algunos mundos. El piloto
demuestra que una política anticipatoria puede aportar valor y, al mismo tiempo,
que el reward debe revisarse antes de convertirlo en criterio operativo.

## Límite

F-IV se formula aquí como juego potencial repetido con eventos exógenos. No se
estima un kernel, no se prueba la propiedad de potencial de Markov y no se
modelan batería continua ni dinámica física. El oráculo solo es viable en el
espacio pequeño enumerado.
