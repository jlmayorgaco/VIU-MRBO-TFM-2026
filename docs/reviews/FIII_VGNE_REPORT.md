# Informe F-III — Primal–dual distribuido, residuos y cierre

## Pregunta

¿Tratar las cuotas como restricciones compartidas mediante precios duales deja
intenciones más realizables que el potencial poblacional, especialmente bajo
presión alta?

## Auditoría continua

La referencia central resolvió el problema regularizado y verificó KKT. La
versión distribuida mantuvo copias duales, DAC del residual y proyección primal.
Una ejecución solo se marcó convergente cuando el residual conjunto —primal,
dual, complementariedad, estacionariedad y consenso— fue menor que `5×10⁻⁴`.

La versión distribuida cruzó ese umbral en 91,9 % de los 1.200 mundos; la
mediana final de KKT fue `4,97×10⁻⁴`. La tasa descendió al aumentar la
heterogeneidad: con presión 0,70 pasó de 97,3 % (`CV=0`) a 86,0 % (`CV=1`); con
presión 0,85, de 93,3 % a 88,7 %. Los 97 casos que no cruzaron el umbral siguen
en el denominador y en RAW.

## Endpoint atómico

Sobre los 1.160 mundos con oráculo entero factible, PD-vGNE+R alcanzó 99,57 %
de factibilidad y un gap mediano de 9,04 %. La referencia central+R alcanzó
99,74 % y 9,10 %, respectivamente. La proximidad de ambas salidas sugiere que,
cuando los residuos son pequeños, la capa distribuida reproduce bien la
referencia continua; no demuestra equivalencia para toda inicialización o
grafo.

En la celda preespecificada de presión 0,85, PD-vGNE+R superó a Smith+R en 5,50
puntos porcentuales de factibilidad (IC bootstrap del 95 %: 3,67–7,50;
McNemar con Holm `p=1,02×10⁻⁸`). En las 521 parejas con gaps definidos, la
diferencia mediana fue −7,39 puntos (IC del 95 %: −9,65 a −5,07; Wilcoxon con
Holm `p=2,79×10⁻³⁴`).

## Coste de esa mejora

La mediana fue 654 ms y 2,73 MB modelados por agente para PD-vGNE+R. Smith+R
usó 1.366 ms pero 0,90 MB. Por tanto, los precios no son una mejora gratuita:
en esta implementación redujeron gap y fallos del cierre, pero triplicaron
aproximadamente el tráfico modelado frente a Smith.

## Respuesta

Sí para los endpoints preespecificados de presión alta: los precios duales
dejaron estados más fáciles de cerrar y con menor gap que Smith. No se concluye
que F-III domine a F-I: Geo-QPG-C3 obtuvo 100 % de factibilidad y 3,23 % de gap
mediano con muchos menos bytes que F-III. El resultado sitúa F-III entre la
calidad de la formulación restringida y el coste de sostener consenso dual.

## Límite

La convergencia es un hecho numérico condicionado al umbral y al presupuesto.
No se invoca un teorema global para el predictor–corrector digital implementado.
La regularización `ε=0,02` hace más tratable el problema continuo, pero también
lo modifica; el cierre sigue siendo heurístico.
