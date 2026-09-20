# Plan experimental de SP1.N4 por preguntas

## Contrato común

La unidad independiente es el mundo--semilla. Dentro de una fila se anidan
métodos, tratamientos, robots, cargas, propuestas y realizaciones de canal. Los
fallos, timeouts y no convergencias permanecen en el denominador. El MILP puede
usar información global como techo experimental; esa ventaja se declara y no se
presenta como comparación arquitectónica justa.

Los endpoints binarios usan diferencias de riesgo pareadas, McNemar exacto e
intervalo de Newcombe. Las respuestas continuas usan la diferencia dentro del
mundo, mediana, intervalo bootstrap de mundos completos y Wilcoxon cuando
proceda. Si varias preguntas forman una familia confirmatoria, se aplica Holm.
Los ajustes log--log son descriptivos del rango ejecutado.

## Q1. Orden mínimo de escape

- **Hipótesis:** una fracción no despreciable de los mínimos de BR requiere
  `h*=2` o `h*=3`, y esa fracción cambia con heterogeneidad y presión.
- **Estimando:** `P(h*=1)`, `P(h*=2)`, `P(h*=3)`, `P(h*>3)` condicionadas a
  `CV(c_i)`, presión, geometría y `N/K`.
- **Worlds:** instancias pequeñas que permitan enumerar la vecindad completa del
  perfil terminal de BR; semillas pareadas entre factores.
- **Baselines:** perfil BR; MILP solo como referencia del coste global.
- **Métricas:** `h*`, gap del perfil antes/después, número de candidatos y CPU.
- **Decisión:** distribución e intervalos multinomiales; un efecto de factor se
  declara solo con contraste preespecificado e intervalo, no por inspección.
- **Artefactos:** configuración, mundos, perfil BR, tabla de enumeración, testigos
  reales `h*=1,2,3`, resumen y figura.
- **Estado:** pendiente. Los testigos unitarios actuales no estiman frecuencias.

## Q2. Regla de revisión frente a orden estratégico

- **Hipótesis:** cambiar la exploración dentro de `N1` no sustituye coordinar
  pares o triples.
- **Estimando:** diferencias pareadas de factibilidad, gap, bytes y CPU para
  BR--Geo-ASR--Geo-LLL, seguidas de BR--2BR--C3.
- **Worlds:** los 1.200 mundos congelados de E4.
- **Baselines:** BR (`h=1`); el MILP certifica el denominador del gap.
- **Métricas:** factibilidad, gap, bytes/agente, CPU y tamaño de lote.
- **Decisión:** inferencia pareada existente con Holm; no mezclar ASR/LLL con
  dinámicas poblacionales.
- **Artefactos:** RAW E4, procesados, manifiesto, Figura 28 y Tabla 6.
- **Estado:** ejecutado. No volver a correr para esta refactorización.

## Q3. Suficiencia de agregados afectados

- **Hipótesis:** FULL y AGG calculan exactamente el mismo delta y, con iguales
  candidatos y desempates, el mismo perfil final.
- **Estimando:** tasa de discrepancias en `Delta D`, `Delta J`, propuesta elegida
  y perfil final; diferencia de bytes y memoria.
- **Worlds:** al menos los mundos E4, con propuestas pre-generadas y pareadas.
- **Baselines:** FULL con perfil completo frente a AGG con registros afectados.
- **Métricas:** errores absolutos, discrepancias, bytes, memoria y CPU.
- **Decisión:** cero discrepancias discretas y tolerancia numérica congelada para
  distancias; cualquier diferencia invalida equivalencia. Bytes se reportan con
  IC pareado, no como prueba de información mínima.
- **Artefactos:** dos evaluadores independientes, corpus de propuestas, log de
  divergencias, tests y tabla pareada.
- **Estado:** pendiente.

## Q4. Coste de retirar el orden global

- **Hipótesis:** DMIS+TX conserva la salida de CF en red nominal y aumenta el
  tráfico; bajo canal degradado pueden aparecer abortos o divergencias.
- **Estimando:** diferencias pareadas de factibilidad, gap, perfil final, rondas,
  commits, abortos, mensajes, bytes y CPU.
- **Worlds:** E4 para nominal; realizaciones de canal de Q9 para degradado.
- **Baselines:** CF global como control arquitectónico; mismos candidatos y
  desempates.
- **Métricas:** las anteriores, separando arbitraje de transacción.
- **Decisión:** nominal: igualdad de calidad/factibilidad y diferencia de coste;
  degradado: intervalos y tasa de violación, sin borrar abortos.
- **Artefactos:** RAW E4, identidad final por mundo, rondas, contadores por campo,
  trazas TX y realización de canal.
- **Estado:** parcial. E4 cubre calidad, factibilidad, bytes y CPU nominales;
  faltan identidad final, rondas y canal degradado.

## Q5. Control distribuido exacto pequeño

- **Hipótesis:** DPOP puede reproducir el MILP en instancias pequeñas, pero el
  tamaño UTIL crece con el ancho inducido.
- **Estimando:** tasa de coincidencia de factibilidad, error objetivo máximo,
  entradas y bytes de la tabla UTIL.
- **Worlds:** los 400 mundos E5 con `N=6,8`.
- **Baselines:** MILP; C3 y DMIS+TX son referencias de calidad, no certificados.
- **Métricas:** factibilidad, objetivo, error, entradas, bytes y CPU.
- **Decisión:** coincidencia discreta total y error dentro de la tolerancia
  numérica fijada; la escala se describe, no se extrapola.
- **Artefactos:** RAW E5, pseudored, tablas UTIL, manifiesto y Figura 30.
- **Estado:** ejecutado.

## Q6. Crecimiento de cómputo y comunicación

- **Hipótesis:** el coste de DMIS+TX sigue creciendo en el rango evaluado y no
  ofrece evidencia de saturación.
- **Estimando:** mediana por tamaño y pendiente log--log descriptiva de tiempo y
  bytes para BR y DMIS+TX.
- **Worlds:** E6: `N=16,32,48,64`, `K=N/4`, 60 mundos.
- **Baselines:** BR; 2BR/C3 solo se añadirán donde el presupuesto permita el
  mismo número de mundos o se declare el desequilibrio.
- **Métricas:** tiempo, bytes/agente, calidad, factibilidad y timeouts.
- **Decisión:** intervalos de pendiente y curvas por tamaño. No usar lenguaje de
  complejidad asintótica ni de flota ilimitada.
- **Artefactos:** RAW E6, entorno de hardware, resumen, ajuste y Figura 31.
- **Estado:** ejecutado en el rango declarado.

## Q7. Paso de población a coalición atómica

- **Hipótesis:** el ranking por residual/objetivo continuo puede cambiar después
  de aplicar un cierre común.
- **Estimando:** diferencias por método antes y después de `R(x)=a`.
- **Worlds:** mismos mundos, payoff, inicialización, timeout y semillas para
  Replicator, Smith, BNN y Logit.
- **Baselines:** mismo cierre `R`, MILP atómico y relajación central.
- **Métricas:** residual, objetivo continuo y convergencia; después factibilidad,
  gap MILP, exceso de capacidad, CPU y bytes.
- **Decisión:** ranking separado continuo/post-cierre; Holm para la familia
  confirmatoria. No hay ranking si `R` difiere entre métodos.
- **Artefactos:** especificación y tests de `R`, RAW continuo, asignaciones
  cerradas, fallos de cierre y tabla pareada.
- **Estado:** pendiente; E71 no satisface este contrato.

## Q8. vGNE primal--dual a enteros

- **Hipótesis:** una implementación F-III solo es candidata a comparación
  atómica si primero reduce residuos primal, dual, consenso y KKT.
- **Estimando:** distribución de residuos al timeout y calidad tras el mismo
  cierre de Q7.
- **Worlds:** pequeños para verificación contra solver central; después tamaños
  moderados con grafos conectados preespecificados.
- **Baselines:** primal--dual central, LP, MILP y familia poblacional con `R` común.
- **Métricas:** residuos primal/dual/consenso/KKT, iteraciones, mensajes, bytes,
  factibilidad y gap post-cierre.
- **Decisión:** tolerancias y timeout se congelan antes de ejecutar; solo las
  filas que cumplen el gate de residuos pasan al análisis post-cierre.
- **Artefactos:** formulación dimensional, integrador, configuración, tests de
  proyección, RAW por iteración y auditoría KKT.
- **Estado:** formulación propuesta; no implementado.

## Q9. Canal degradado

- **Hipótesis:** pérdida, retardo, reordenamiento y caída del proponente afectan
  de forma distinta a GRAPE, DMIS+TX y una futura variante DAC-QPG.
- **Estimando:** diferencias pareadas por realización de canal en divergencia,
  abortos, reintentos, factibilidad, gap y bytes.
- **Worlds:** mismos mundos y mismos streams de canal para todos los métodos;
  factores de severidad congelados.
- **Baselines:** canal nominal y métodos N3 compatibles con el mismo contrato.
- **Métricas:** registros divergentes, commits parciales, abortos, reintentos,
  tiempo, factibilidad, gap, mensajes y bytes.
- **Decisión:** cero commits parciales como invariante de seguridad; el resto se
  analiza con efectos pareados e intervalos por severidad. No se declara
  tolerancia a fallos por ausencia de violación en pocas semillas.
- **Artefactos:** simulador de canal, seeds de red, trazas por mensaje/TX,
  registro de fallos, tests de invariantes y tabla de severidad.
- **Estado:** pendiente y compartido con N3.

## Adquisición necesaria para la figura temporal

La figura de una ejecución debe salir de una traza nueva, no de una ilustración
manual. Por evento debe persistir: fase Q/G, `D(e)`, `J(e)`, orden aceptado,
número de commits paralelos, bytes acumulados, propuesta, versiones leídas y
estado final. La semilla representativa se seleccionará mediante una regla
declarada antes de abrir los resultados, por ejemplo la mediana de gap de C3
entre mundos factibles. Hasta que exista ese RAW, la figura no debe entrar en la
memoria.
