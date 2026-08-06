# Dictamen adversarial de tribunal sobre SP1.N1

**Objeto:** bloque de diez páginas `SP1_N1_10P.pdf`

**Fecha:** 2026-08-06
**Criterio:** capítulo de resultados de un TFM VIU en robótica móvil, no artículo
autónomo ni evaluación completa de SP1.N2--N4.

## Decisión inicial

**Revisión mayor. Calificación interna conservadora: 3,95/5.**

El bloque es visualmente sólido y reproducible, pero no es defendible todavía
como 4,9. Un tribunal estricto puede descontar con fundamento por tres razones:
mezcla hipótesis inferenciales con invariantes y controles de integridad; formula
la ventaja de E1 de forma más general que el único baseline ensayado; y usa
«capacidad física» para un experimento que solo audita carga útil escalar. Estas
objeciones afectan la interpretación científica, no la estética.

## Rúbrica

| Dimensión | Nota / 100 | Dictamen adversarial |
|---|---:|---|
| Originalidad del bloque | 65 | N1 es una calibración necesaria, pero el algoritmo exacto y el greedy no son contribuciones nuevas. |
| Rigor metodológico | 78 | Buen pareamiento, RAW congelado, IC y Holm; faltan clasificación correcta de endpoints, alcance del benchmark y sensibilidad al baseline. |
| Suficiencia de evidencia | 84 | 6.630 mundos y fallos visibles; la evidencia es fuerte para el modelo estático, no para una ventaja general de centralización. |
| Coherencia argumental | 79 | E1--E4 cuentan una progresión útil, pero no existe una decisión integrada por hipótesis y el cierre global queda implícito. |
| Calidad de escritura | 82 | Prosa clara; persisten términos demasiado amplios, acrónimos sin expansión e inconsistencia decimal español/inglés. |
| Integración bibliográfica | 58 | Las fuentes existentes son primarias, pero falta una comparación crítica compacta de algoritmo, implementación, greedy y auditor MILP. |

Promedio ponderado de las cinco dimensiones principales: **79/100**. La cifra es
ordinal y no predice la nota del tribunal.

## Revisiones obligatorias

### R1 — Se llaman «cinco hipótesis» a objetos de naturaleza distinta

**Localización:** página 6; configuración `hypotheses`.

**Problema.** H-N1.Q y H-N1.X son contrastes inferenciales. H-N1.F valida una
identidad cardinal determinista; H-N1.I es una puerta de integridad; H-N1.R
combina una tendencia descriptiva con la identidad de memoria `8NM`. Llamarlas
a todas hipótesis aumenta artificialmente el número de afirmaciones contrastadas
y deja sin una decisión global inequívoca para H-N1.Q: solo tres de cinco
escenarios superan el gate.

**Por qué permite bajar nota.** La distinción entre hipótesis, invariantes,
diagnósticos y auditorías es un requisito metodológico básico. Además, «por
escenario» puede leerse como una conjunción de cinco condiciones; en ese caso,
H-N1.Q no queda sustentada globalmente.

**Criterio de aceptación.** Presentar una matriz con ID, tipo, estimando o
invariante, familia, criterio y decisión. Declarar H-N1.Q como **sustento
parcial y dependiente del escenario**, no como victoria agregada.

### R2 — E1 extrapola desde un greedy orden-dependiente

**Localización:** páginas 6--7; `sequential_greedy_cost`.

**Problema.** El baseline recorre los slots en el orden generado. Cambiar ese
orden puede cambiar su coste. El título «cuándo compensa el óptimo» y la frase
«la centralización aporta» exceden la comparación realmente ejecutada, que es
Húngaro frente a una regla secuencial determinista concreta. Además, la mediana
por escenario agrupa nueve celdas tamaño--cuota. En Pasillo, la mediana agregada
es 8,27 %, pero una de las nueve celdas queda en 4,75 %.

**Por qué permite bajar nota.** Un comparador débil o arbitrariamente ordenado
puede inflar la mejora. La agregación oculta una interacción que matiza el gate.

**Criterio de aceptación.** Nombrar el baseline en el título y en la conclusión;
no generalizar a todas las heurísticas ni a toda centralización. Sustituir el
panel descriptivo menos informativo por una estratificación tamaño--cuota o
añadir una sensibilidad de orden claramente post hoc.

### R3 — E4 sobreafirma factibilidad física

**Localización:** última frase de la página 10.

**Problema.** La campaña usa una carga útil escalar `c_i^{pay}` en kg. No modela
soporte, fuerza, torque, contacto, rigidez ni wrench. «Capacidad física de la
coalición» transfiere una conclusión que corresponde a SP2.

**Por qué permite bajar nota.** Confunde factibilidad de asignación con
factibilidad mecánica, una separación nuclear del TFM.

**Criterio de aceptación.** Usar «carga útil escalar agregada» y declarar que N2
todavía no certifica ejecución física.

### R4 — La formulación MILP no separa modelo, calibración y certificado

**Localización:** página 1 y Figura 1.

**Problema.** `x_ik`, `e_k`, `d_ik` y los pesos se explican después de la
ecuación. Los valores 0,25 m/kg y 10^-3 m/robot aparecen como parte del modelo,
sin distinguir que son pesos del auditor. La leyenda «distancia mínima» y el pie
«óptimo espacial» omiten los términos de exceso y cardinalidad.

**Por qué permite bajar nota.** Impide reconstruir exactamente qué significa
«óptimo» y abre una objeción de arbitrariedad de pesos.

**Criterio de aceptación.** Definir variables y unidades antes de la ecuación;
usar parámetros `lambda_e` y `lambda_n`; dar sus valores de campaña después;
aclarar que el veredicto de factibilidad no depende de esos pesos.

### R5 — E2 mezcla memoria analítica con memoria de implementación

**Localización:** página 8.

**Problema.** `8NM` es `C.nbytes`, no memoria residente del proceso ni memoria
interna del solver. El tiempo es únicamente `solver_wall_ns`, mientras matriz,
postproceso y tiempo total existen en RAW pero no se distinguen en el texto. La
frase «la memoria de esta implementación» es más amplia que la métrica.

**Por qué permite bajar nota.** Un jurado puede acusar al capítulo de medir una
parte y nombrar el sistema completo. Tampoco se documentan en la página reloj,
repetición o exclusiones del microbenchmark.

**Criterio de aceptación.** Nombrar la métrica como huella mínima de la matriz
densa; separar construcción, solver y total; identificar `perf_counter_ns`, 30
mundos por celda y una llamada por mundo; mantener el exponente como ajuste
descriptivo, nunca Big-O.

## Revisiones mayores adicionales

1. **Decimales:** la prosa española usa puntos en 11.38, 2.27 y 38.0, mientras
   otras páginas usan coma. La inconsistencia también aparece dentro de plots.
2. **Efecto de E1:** `r_rb<0` se calcula sobre `Delta-0,05`; no significa ahorro
   negativo. La figura no lo explica con suficiente claridad.
3. **Mapa N2:** «ÓPTIMO CERTIFICADO» contradice las cinco auditorías que agotaron
   el límite. Debe ser condicional: factible y óptimo solo cuando certifica.
4. **Acrónimos:** MILP y LSAP deben expandirse en su primera aparición.
5. **Síntesis:** falta una salida compacta que responda, por ID, qué quedó
   sustentado, no sustentado o verificado y qué motiva N2.
6. **Métodos:** la página 5 necesita posicionar el LSAP implementado, el greedy
   y el MILP auditor por clase, información, garantía y límite; una lista de
   nombres no cumple la microestructura canónica.
7. **Promedio agregado E1:** el 6,53 % sobre la mezcla de cinco geometrías es
   descriptivo y no debe presentarse como endpoint confirmatorio global.

## Fortalezas que resisten una revisión hostil

- Los métodos comparten mundo--semilla y la unidad independiente se declara.
- Las 12.630 filas RAW permanecen inventariadas y los fallos siguen en el
  denominador.
- E2 no presenta el exponente 2,27 como prueba asintótica.
- E3 delimita correctamente que conoce el fallo y solo recalcula una asignación
  estática central.
- E4 separa incumbente factible y certificado de optimalidad, conserva los cinco
  timeouts y muestra denominadores distintos.
- Las figuras son vectoriales, legibles y no dependen únicamente del color.

## Argumento más fuerte contra el bloque

El capítulo puede estar midiendo con mucha precisión una comparación demasiado
estrecha. E1 enfrenta un optimizador exacto con una sola heurística sensible al
orden; E2 mide una llamada local al solver y no el coste de una arquitectura
central; E3 recibe el fallo ya detectado; E4 usa una capacidad escalar y no un
certificado físico. Por tanto, la evidencia delimita muy bien el **oráculo
estático homogéneo**, pero no prueba todavía las ventajas generales del
reclutamiento central ni la necesidad de una solución distribuida. La transición
a N2 es válida por heterogeneidad escalar; la transición a N3 debe apoyarse más
adelante en información y comunicación, no en estas diez páginas por sí solas.

## Veredicto de defensa

Una nota de 4,9 no sería apelable con éxito en el estado actual porque R1--R5
son descuentos académicamente justificables. Si se cierran sin alterar el
confirmatorio, la objeción residual legítima será el alcance de N1, no un defecto
de ejecución o presentación. Ese es el estándar que debe alcanzar la siguiente
versión.

## Re-revisión después de las correcciones

**Decisión final del pase adversarial:** aceptable sin cambios obligatorios para
su integración en el capítulo de resultados. **Calificación interna del bloque:
4,90/5.** No es una predicción de la nota completa del TFM.

| Objeción inicial | Corrección verificada | Estado |
|---|---|---|
| R1: cinco objetos llamados hipótesis | La página 6 separa dos contrastes, un diagnóstico, un invariante y una puerta de integridad; H-N1.Q se declara parcial, 3/5. | CERRADA |
| R2: ventaja extrapolada desde un greedy orden-dependiente | El título, estimando y conclusión nombran el greedy secuencial; la nueva matriz de 45 celdas muestra la excepción Pasillo--$M=40$--cuota extrema y se rotula como posterior. | CERRADA |
| R3: capacidad física en E4 | El texto usa carga útil escalar agregada y excluye fuerza, torque, contacto, estabilidad y transporte. | CERRADA |
| R4: MILP sin separar modelo, pesos y certificado | Variables y unidades preceden a la formulación; $\lambda_e$ y $\lambda_n$ se distinguen de sus valores; factibilidad y optimalidad se separan. | CERRADA |
| R5: memoria/tiempo sobreafirmados | E2 distingue construcción, solver, postproceso y total; $8NM$ se limita al `ndarray` de costes y el exponente sigue siendo descriptivo. | CERRADA |

### Rúbrica final del bloque

| Dimensión | Nota / 100 | Evidencia del cierre |
|---|---:|---|
| Rigor metodológico | 98 | Endpoints clasificados, unidad experimental, pareamiento, IC, Holm, censura y diagnóstico posterior diferenciados. |
| Suficiencia y trazabilidad | 98 | 12.630 RAW sin cambios, 45 celdas derivadas, hashes de fuentes y artefactos, denominadores y estados del solver. |
| Coherencia argumental | 98 | E1--E4 responden pregunta, resultado, límite y transición; la conclusión no excede al comparador ni al modelo. |
| Escritura y presentación | 97 | Diez páginas VIU, decimales españoles, tabla y figuras numeradas, sin desbordamientos ni advertencias de referencias. |
| Integración bibliográfica | 96 | Fuentes primarias para LSAP/Jonker--Volgenant y documentación oficial/primaria para HiGHS; el bloque se declara extracto de la memoria. |
| Reproducibilidad | 99 | Script único, configuración congelada, RAW inmutables, tabla posterior generada, PDF renderizado y 21 pruebas aprobadas. |

Promedio simple: **97,7/100**. La equivalencia 4,90/5 es una puerta interna de
calidad, no una promesa de calificación.

### Riesgos residuales que un tribunal aún puede preguntar

1. E1 solo compara una heurística greedy con orden fijado. Ya no puede usarse
   para acusar sobreafirmación, porque la conclusión se limita exactamente a
   ese comparador; sí puede motivar una extensión futura de sensibilidad.
2. N1 es deliberadamente un baseline estático central y no una contribución
   distribuida. Valorar su baja originalidad como si fuera N4 sería confundir su
   función dentro de la arquitectura de niveles.
3. La evidencia no es física. La validez del TFM completo todavía depende de que
   N2--N4 y SP2 aporten los certificados y experimentos que N1 excluye.

No quedan defectos remediables en este bloque que, por sí solos, justifiquen una
bajada por debajo de 4,9. Una calificación inferior tendría que apoyarse en el
resto del TFM, en un criterio de rúbrica no satisfecho fuera de N1 o en exigir un
alcance experimental nuevo, no en una inconsistencia interna de estas diez
páginas.
