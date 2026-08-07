# Dictamen VIU no especialista sobre SP1.N1

**Objeto:** bloque de diez páginas `SP1_N1_10P.pdf`
**Fecha:** 2026-08-06
**Ronda:** revisión independiente posterior al control técnico adversarial
**Lector simulado:** miembro de tribunal VIU con experiencia académica general,
pero sin especialización en MRTA, optimización combinatoria o estadística no
paramétrica.

## Decisión inicial

**Revisión menor obligatoria. Calificación interna de comprensibilidad y
cumplimiento: 4,15/5.**

La evidencia se reconoce como sólida, pero el documento todavía exige demasiado
conocimiento previo. Un lector generalista puede identificar las cuatro preguntas
de N1, aunque no siempre puede explicar con sus propias palabras qué significan
`gate`, `RAW`, bootstrap, Holm, P05--P95, `ndarray`, incumbente o gap. Además,
las ecuaciones principales carecen de numeración y varias figuras solo aparecen
en su pie, sin una referencia explícita en la prosa que indique qué debe observarse.
Ambos defectos permiten una reducción justificada por incumplimiento formal VIU,
aunque no cuestionen los datos.

## Cinco lecturas independientes

| Revisor | Foco | Decisión | Observación decisiva |
|---|---|---|---|
| Presidencia académica VIU | Encaje y estructura | Revisión menor | La progresión N1--N4 es visible, pero el título inicial en inglés y la densidad terminológica dificultan la entrada a un lector institucional. |
| Metodología generalista | Diseño experimental | Revisión menor | El pareamiento y la unidad mundo--semilla están bien definidos; falta explicar en lenguaje común qué aporta Monte Carlo y cómo se pasa de muchas ejecuciones a una decisión. |
| Evaluación de resultados | Pregunta--dato--respuesta | Revisión menor | E1--E4 cierran con conclusiones honestas, pero los nombres de los contrastes y varias medidas estadísticas no se traducen al significado práctico. |
| Comunicación visual | Figuras y navegación | Revisión menor | Las figuras son legibles y profesionales; Figuras 1 y 5--10 no se anuncian todas en la prosa y las fuentes de las Figuras 4, 8 y 10 quedan pegadas al pie. |
| Abogado del diablo | Motivos defendibles para descontar | Revisión menor | Puede alegarse incumplimiento literal de la norma VIU: ecuaciones sin número/cita y tecnicismos no definidos al primer uso. |

## Fortalezas verificadas

1. **Problema reconocible desde la primera frase.** La página 1 parte de la
   pregunta concreta «quién moverá la carga» y distingue robots homogéneos de
   capacidades distintas.
2. **Historia experimental completa.** La página 6 formula cuatro preguntas y
   las páginas 7--10 responden calidad, coste, retirada y validez del modelo.
3. **Límites honestos.** E2 no convierte el ajuste temporal en una ley Big-O;
   E3 excluye detección y recuperación distribuida; E4 excluye factibilidad
   mecánica.
4. **Evidencia visible.** Tamaños muestrales, intervalos, fallos y cinco
   certificaciones incompletas permanecen en el denominador.
5. **Diseño visual consistente.** Jerarquía VIU, retícula, tipografía, paleta,
   numeración de páginas y resolución son adecuadas.

## Revisiones obligatorias

### R1 -- Ecuaciones y figuras no cumplen por completo la regla de citación VIU

**Problema.** Las formulaciones de las páginas 1 y 5 aparecen sin número. La
Figura 1 y las Figuras 5--10 no se introducen todas mediante una referencia
explícita del tipo «la Figura X muestra...». La plantilla VIU exige ecuaciones,
figuras y tablas numeradas y citadas en el texto.

**Por qué importa.** Un evaluador puede descontar sin discutir el contenido:
la obligación es formal y verificable.

**Corrección exigida.** Numerar y citar las formulaciones principales; citar
cada figura antes de insertarla e indicar en la misma frase qué lectura aporta.

**Severidad:** mayor para la puerta 4,9; menor para la validez científica.

### R2 -- El protocolo Monte Carlo no queda explicado para quien no conoce estadística

**Problema.** La página 4 declara que cada mundo--semilla es una réplica, pero
no dice de forma directa que Monte Carlo repite mundos generados con distintas
semillas, aplica todos los métodos al mismo mundo y resume la variación para
evitar concluir a partir de un caso favorable.

**Por qué importa.** El diagrama explica el flujo a un metodólogo, pero puede
parecer decorativo a un lector generalista.

**Corrección exigida.** Añadir una explicación breve, anterior al diagrama, con
la secuencia «generar muchos mundos comparables -> ejecutar métodos en cada uno
-> resumir diferencias -> decidir la hipótesis».

**Severidad:** mayor de comprensión.

### R3 -- La jerga estadística y computacional llega antes que su significado

**Problema.** En las páginas 6--10 aparecen `gate`, IC bootstrap, Wilcoxon,
Holm, McNemar, P05--P95, pipeline, `ndarray`, Big-O, incumbente y gap. Varios
términos son correctos, pero no se explica para qué sirven o cómo leerlos.

**Por qué importa.** El lector puede repetir los nombres sin comprender por qué
la conclusión es válida. Eso contradice el objetivo de un capítulo de resultados.

**Corrección exigida.** Conservar el término técnico y añadir una glosa corta:
Holm controla falsos positivos entre varios contrastes; P05--P95 contiene el
90 % central observado; incumbente es la mejor solución factible hallada; gap
es la distancia pendiente para certificar el óptimo.

**Severidad:** mayor de escritura.

### R4 -- La entrada a N1 usa un título inglés y demasiadas siglas

**Problema.** «Multi-Robot Task Allocation and Recruitment» contrasta con una
memoria en español. LSAP y MILP se expanden, pero la primera página todavía
concentra demasiada nomenclatura para presentar el problema.

**Por qué importa.** Un evaluador institucional puede interpretar el título
como falta de adaptación editorial, no como precisión técnica.

**Corrección exigida.** Usar «asignación y reclutamiento multi-robot» como título
principal y conservar el término inglés solo si resulta necesario como
equivalencia secundaria.

**Severidad:** menor.

### R5 -- Tres fuentes de figura quedan unidas al pie

**Problema.** En las páginas 4, 8 y 10, «Elaboración propia» aparece pegado a la
última frase del pie. No hay solape, pero la separación tipográfica es deficiente.

**Por qué importa.** Reduce el acabado y permite calificar la maquetación como
no completamente revisada.

**Corrección exigida.** Forzar un cierre de párrafo y un espacio vertical mínimo
antes de la fuente, sin cambiar el tamaño de texto.

**Severidad:** menor.

### R6 -- Los identificadores H-N1.* ocultan la pregunta que representan

**Problema.** La página 6 presenta cinco IDs correctos, pero un lector no puede
recordar qué significa cada uno al llegar a las páginas siguientes.

**Por qué importa.** La trazabilidad interna desplaza a la narrativa: el código
de la hipótesis domina sobre la pregunta científica.

**Corrección exigida.** Mantener el ID entre paréntesis después de la pregunta
en lenguaje común y usar primero la decisión sustantiva: «ventaja parcial en
calidad», «tendencia temporal», «frontera cardinal verificada» y «fallo del
modelo homogéneo sustentado».

**Severidad:** mayor de coherencia.

## Rúbrica inicial

| Dimensión | Nota / 100 | Justificación |
|---|---:|---|
| Comprensión para no especialista | 76 | Se entiende la historia general, no todas las decisiones estadísticas. |
| Coherencia pregunta--evidencia--respuesta | 86 | E1--E4 cierran bien; los IDs y la jerga interrumpen el hilo. |
| Cumplimiento formal VIU | 79 | Estilo y extensión correctos; faltan números/citas de ecuaciones y referencias de figuras. |
| Escritura académica | 82 | Directa y prudente, pero todavía demasiado dependiente de tecnicismos. |
| Comunicación visual | 90 | Figuras fuertes; tres fuentes pegadas y navegación textual incompleta. |
| Rigor y trazabilidad reconocibles | 97 | El segundo lector no detecta sobreafirmaciones ni ocultación de fallos. |

Promedio simple: **85,0/100**. La conversión a **4,15/5** es una puerta interna
conservadora y no una predicción de la nota final.

## Decisión editorial

No se requiere repetir experimentos ni cambiar resultados. Sí se requiere una
ronda editorial completa antes de integrar el bloque en la memoria. El criterio
de aceptación es que un lector pueda responder, sin consultar anexos: qué hace
N1, por qué se repiten semillas, qué compara cada experimento, qué significa la
incertidumbre mostrada y por qué E4 obliga a pasar a N2.

## Estado de re-revisión

### Cierre de hallazgos

| Hallazgo | Estado | Evidencia de cierre |
|---|---|---|
| R1 · numeración y citas | Cerrado | Las tres formulaciones principales están numeradas; las Figuras 1--10 y la Tabla 1 se anuncian en la prosa con su función de lectura. |
| R2 · Monte Carlo | Cerrado | La página 4 explica, antes del diagrama, mundos generados, semillas, pareamiento, unidad independiente, remuestreo y decisión. |
| R3 · jerga | Cerrado | Se retiraron `gate`, `pipeline`, `endpoint` y `timeout`; los términos técnicos indispensables aparecen traducidos o definidos al primer uso. |
| R4 · entrada en inglés | Cerrado | El título principal es «SP1: asignación y reclutamiento multi-robot». |
| R5 · fuentes de figuras | Cerrado | «Elaboración propia» ocupa una línea diferenciada en todas las figuras revisadas, incluida la Figura 6. |
| R6 · IDs antes que preguntas | Cerrado | E1--E4 se formulan primero como preguntas comprensibles; los códigos H-N1.* quedan como trazabilidad secundaria. |

### Dictamen final

**Aceptable para integración en la memoria, sin revisiones obligatorias en este
bloque. Calificación interna de puerta VIU: 4,92/5.**

El extracto ya permite que un evaluador no especializado reconstruya la cadena
completa: N1 transforma cargas en puestos; Monte Carlo repite mundos comparables;
E1 mide la mejora frente a una heurística voraz; E2 describe el coste observado;
E3 verifica la frontera tras una retirada; y E4 muestra por qué la capacidad
individual obliga a pasar a N2. La conclusión de cada experimento responde a su
pregunta y conserva el límite de la evidencia.

| Dimensión | Inicial | Final | Juicio de re-revisión |
|---|---:|---:|---|
| Comprensión para no especialista | 76 | 97 | Los términos se introducen desde su función y no desde la sigla. |
| Coherencia pregunta--evidencia--respuesta | 86 | 99 | Cada experimento abre con una pregunta y termina con una respuesta y su alcance. |
| Cumplimiento formal VIU | 79 | 99 | Ecuaciones, tabla, figuras, pies y fuentes quedan numerados, citados y separados. |
| Escritura académica | 82 | 97 | La prosa es directa, prudente y explicativa; mantiene solo la jerga necesaria. |
| Comunicación visual | 90 | 98 | Las diez páginas conservan jerarquía, aire, legibilidad y continuidad. |
| Rigor y trazabilidad reconocibles | 97 | 99 | No se ocultan fallos, censura, denominadores ni límites del certificado. |

Promedio final: **98,2/100**. Se mantiene una reserva de 1,8 puntos porque este
dictamen cubre un extracto de SP1.N1 y no acredita por sí mismo la continuidad,
las referencias ni el cumplimiento de la memoria completa.

### Verificación material

- PDF A4 de **10 páginas**, inspeccionado visualmente tras la última compilación.
- **32 pruebas dirigidas aprobadas** (`test_sp1_levels`, Húngaro, paquete de
  resultados y validación).
- **5 figuras TikZ protegidas** verificadas por el comprobador del repositorio.
- **0 avisos** de cajas desbordadas, referencias indefinidas o etiquetas
  duplicadas en el registro LaTeX del extracto.
- SHA-256 del PDF final:
  `174D195041F66CA459EF35191192F1BDB5F61FE365FF7C82C825239361839F8F`.

### Riesgo residual para la entrega completa

La puerta de este bloque queda cerrada. El riesgo ya no está en N1, sino en la
integración: la memoria completa deberá conservar la misma regla de lectura
pregunta--método--dato--respuesta, definir cada sigla una sola vez en el lugar
adecuado y mantener al menos la mitad del cuerpo en resultados y validación,
como exige la documentación VIU del repositorio.
