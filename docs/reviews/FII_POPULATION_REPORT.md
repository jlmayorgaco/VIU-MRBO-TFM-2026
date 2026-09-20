# Informe F-II — Dinámicas poblacionales y cierre atómico

## Pregunta

¿La dinámica que deja el mejor estado continuo también produce la mejor
coalición cuando los robots vuelven a ser indivisibles?

## Diseño

Replicator, Smith, BNN y Logit se ejecutaron en los mismos 1.200 mundos de E7.
Compartieron potencial, fitness, inicialización, DAC, tolerancias, presupuesto
de iteraciones y operador `R`. Los 40 mundos que el MILP declaró infactibles se
mantuvieron en RAW, pero el gap y la factibilidad comparativa se resumen sobre
los 1.160 mundos con óptimo entero certificado.

## Resultado continuo

Al agotar el presupuesto, Smith obtuvo el mayor potencial terminal en 1.184
mundos y BNN en 16. Esa clasificación no equivale a una clasificación de
equilibrios: Logit cruzó el criterio numérico en 84,5 % de los mundos;
Replicator lo hizo en uno, y Smith/BNN no lo hicieron. Por eso el resultado se
describe como endpoint a presupuesto fijo, no como convergencia general.

El error de DAC tampoco fue inocuo. La trayectoria del potencial exacto fue
monótona en 99,4 % de los mundos para BNN, 99,3 % para Replicator y 95,0 % para
Smith. La correlación positiva demostrable para el agregado exacto no se
transfiere sin resto a la ejecución con estimaciones locales. Logit queda fuera
de esa propiedad porque converge hacia una respuesta perturbada por `τ`.

## Resultado después de `R`

Entre mundos con oráculo factible, la factibilidad posterior al cierre fue
96,1 % para BNN, 96,2 % para Replicator, 96,6 % para Smith y 96,8 % para Logit.
Condicionadas además a cierres factibles, las brechas medianas fueron 18,17 %,
21,38 %, 18,57 % y 20,88 %, respectivamente.

El ganador por potencial terminal y el ganador atómico no coincidieron en
74,8 % de los mundos. La correlación de Spearman mediana entre ambos órdenes fue
0,32. BNN produjo el mejor endpoint atómico en 622 mundos, Smith en 300, Logit
en 234 y Replicator en 44. La discrepancia apareció en las cinco geometrías
(72,1–78,8 %), por lo que no depende de un único escenario.

## Respuesta

No: en esta campaña, optimizar mejor la relajación no predijo qué dinámica
dejaría la mejor coalición física. La atomicidad no puede tratarse como un
detalle de implementación al final de F-II. El cierre modifica factibilidad y
calidad lo suficiente para cambiar la interpretación del experimento.

## Límite

`R` es una recuperación determinista acotada, no un redondeo óptimo. Las tasas
anteriores caracterizan el par dinámica–DAC–cierre implementado. No prueban que
otra discretización, otro `τ`, más iteraciones o un recuperador exacto conserven
el mismo orden.
