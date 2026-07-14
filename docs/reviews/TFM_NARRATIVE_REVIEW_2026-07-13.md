# Revisión narrativa integral del TFM

Fecha: 13 de julio de 2026

## Dictamen

El diagnóstico inicial era correcto: la memoria tenía material científico valioso, pero lo presentaba como una acumulación de campañas, tablas y miniinformes. La contribución principal quedaba enterrada, el lector debía reconstruir la relación entre SP1--SP8 y A0--FULL, y resultados repetía método, teoría y protocolo antes de llegar a la interpretación. No era un problema cosmético; era un problema de arquitectura argumental.

La revisión realizada es mayor. La memoria ahora tiene un centro reconocible: una asignación multi-AMR no basta si la coalición no puede realizar físicamente la carga. A0--FULL aporta la evidencia integrada principal; SP1--SP8 explican mecanismos y límites. Esta jerarquía evita que ocho estudios parciales compitan por ser la tesis.

## Diagnóstico de la versión de partida

La versión inicial tenía 110 páginas físicas. El cuerpo principal ocupaba 89 páginas frente al máximo de 80 y el control local devolvía un bloqueo y 18 advertencias. El recuento era de unas 20 515 palabras.

Los defectos narrativos más graves eran:

1. La introducción dedicaba demasiada extensión al mercado y al contexto antes de formular el problema técnico.
2. La escalera SP1--SP8 aparecía repetida en hipótesis, metodología y resultados.
3. Resultados contenía ocho miniinformes casi autónomos y volvía a derivar método y teoría.
4. No se declaraba con suficiente fuerza la jerarquía entre evidencia integrada, modular, descriptiva y exploratoria.
5. El término distribuido excedía en algunos puntos lo realmente implementado: cierre, guardia y selector de reemplazo todavía consultan información global.
6. Los saltos forzados y flotantes rígidos producían títulos huérfanos, páginas casi vacías y cortes artificiales.
7. Las conclusiones cerraban como inventario de objetivos e hipótesis, no como respuesta razonada a la pregunta de investigación.
8. Varias comparaciones podían leerse como superioridad general cuando los propios resultados muestran compromisos y resultados negativos.

## Columna vertebral resultante

La secuencia argumental que organiza la memoria es ahora:

1. Una asignación combinatoriamente válida puede fracasar al ejecutar una carga heterogénea.
2. La coalición física exige cardinalidad, capacidad efectiva, wrench, dinámica, seguridad e información.
3. La escalera A0--FULL prueba esos requisitos sobre los mismos mundos y constituye la evidencia principal.
4. SP1--SP3 aíslan cómo se pasa de preferencia continua a factibilidad mecánica.
5. SP4--SP6 estudian movimiento, transporte y recuperación una vez formada la coalición.
6. SP7--SP8 delimitan preguntas todavía descriptivas, no estimables o exploratorias.
7. La conclusión responde qué quedó demostrado, qué resultó negativo y qué sigue abierto.

## Cambios editoriales aplicados

- Resumen y abstract se reescribieron alrededor del problema, el protocolo, los efectos principales y los límites de atribución.
- La introducción pasó de mercado primero a problema primero; la pregunta de investigación y la definición de coalición física aparecen temprano.
- Objetivos e hipótesis se ajustaron para no prometer una implementación distribuida extremo a extremo que la evidencia no demuestra.
- Metodología declara una jerarquía explícita de evidencia y deja de repetir la misma tabla de campañas.
- Resultados conserva A0--FULL como experimento principal y sintetiza SP1--SP8 en tres bloques interpretativos. Los archivos detallados siguen en el repositorio para trazabilidad, pero ya no interrumpen la memoria.
- Las conclusiones distinguen apoyo específico, resultados negativos, compromisos y evidencia no confirmatoria. También hacen explícitos los límites globales del cierre y del reemplazo.
- Se eliminaron cortes de página innecesarios que producían vacíos y encabezados aislados.

## Mapa exigente de afirmaciones

| Afirmación | Evidencia admisible | Decisión |
|---|---|---|
| La validez de una coalición exige más que asignación | A0--FULL y síntesis SP1--SP6 | Sostenida en simulación planar |
| Añadir comprobaciones mejora siempre el resultado | Efecto negativo A2--A3 en escasez | Refutada |
| El cierre de torque aporta complementariedad | Efecto de A3 en la familia torque | Sostenida en el modelo |
| Existe un protocolo de revisión universalmente superior | Comparaciones SP1--SP2 | No sostenida |
| CLOSED es distribuido extremo a extremo | Uso de reparación y candidatos globales | No demostrado |
| FULL atribuye por separado comunicación y reemplazo | Paquete conjunto A4--FULL | No identificable |
| La propuesta demuestra seguridad funcional | Colisiones residuales y planta reducida | No demostrado |
| H7 resiste intermitencia extrema | Ausencia de bloques completos | No estimable |
| H8 demuestra coste computacional real | Timeouts declarados y memoria analítica | Exploratoria |
| La estabilidad práctica queda acotada | Certificado ISS con carga y ganancias fijas | Sostenida bajo esas hipótesis |

## Estado verificado después de la revisión

- PDF: 66 páginas físicas.
- Cuerpo principal: 49/80 páginas.
- Anexos: 7/8 páginas.
- Recuento local: 13 414 palabras.
- Control de entrega: PASS_WITH_WARNINGS, con cero bloqueos y una advertencia.
- Referencias o citas indefinidas: ninguna.
- Desborde tipográfico: uno de 1,25 pt en una tabla, visualmente menor.
- Inspección visual: resumen y abstract en una página cada uno; sin títulos huérfanos ni páginas grandes vacías en resultados, conclusiones o anexos.

## Pendientes que no deben maquillarse

1. Falta un informe externo de similitud. El control local no puede certificar originalidad frente a corpus externos.
2. Persisten sustituciones de fuente Arial en elementos del frontispicio y cajas subllenas en tablas estrechas. Son asuntos de pulido, no de estructura.
3. La generalización sigue limitada a simulación planar, contacto simplificado y una campaña integrada sintética.
4. El selector FULL y parte del cierre continúan usando información global; la palabra distribuido debe conservar siempre esa salvedad.
5. Seguridad funcional, contacto tridimensional, validación independiente y hardware permanecen como trabajo futuro.
6. H7--H8 no deben promocionarse a evidencia confirmatoria sin nuevas ejecuciones y mediciones externas.

## Veredicto editorial final

La memoria dejó de ser una colección caótica de experimentos y ya presenta una tesis defendible. Su fortaleza es la cadena diagnóstica entre asignación y ejecución física, incluido el resultado negativo de que una comprobación adicional puede empeorar el transporte. Su debilidad principal ya no es narrativa, sino de validez externa: la evidencia todavía no autoriza superioridad universal, distribución extremo a extremo ni seguridad funcional. Mantener esas fronteras es parte de la contribución, no una concesión.
