---
name: tfm-viu-submit-ready
description: Revisar, corregir y preparar para entrega el TFM del Máster Universitario en Robótica y Automatización de Procesos de VIU. Usar ante solicitudes de revisión integral, estructura VIU, plantilla LaTeX, límite de páginas, APA 7, español académico, trazabilidad de afirmaciones, declaración de IA, originalidad, informe de similitud o eliminación de patrones de redacción mecánica y calcos del inglés. Aplicar tanto en modo auditoría como en modo corrección, sin alterar resultados ni intentar evadir detectores.
---

# TFM VIU listo para entrega

## Mandato

Usar este archivo como contrato operativo para revisar y corregir el TFM. Trabajar sobre:

```text
docs/doc-05-final-report/main.tex
```

Considerar `TFM.md` material auxiliar. Tratar `docs/doc-05-final-report/` como fuente LaTeX canónica salvo instrucción expresa del usuario.

Priorizar, en este orden:

1. Instrucciones oficiales de VIU, convocatoria y tutor.
2. Integridad científica, datos canónicos y trazabilidad del repositorio.
3. Plantilla institucional del TFM.
4. APA 7 para citas, referencias, tablas y figuras.
5. Claridad del español académico y conservación de la voz del autor.

No prometer que un texto “pasará” Turnitin ni que un clasificador lo considerará humano. Ningún ajuste estilístico ofrece esa garantía. Buscar autoría real, fuentes verificadas, formulaciones propias y declaración honesta del apoyo recibido.

## Fuentes que deben leerse

Antes de modificar el manuscrito, leer:

```text
README.md
Makefile
docs/doc-05-final-report/main.tex
docs/doc-05-final-report/viu-mrob-midreport.sty
docs/doc-05-final-report/README.md
docs/VIU_GUIDELINES_ALIGNMENT.md
docs/THESIS_NARRATIVE_LOCK.md
docs/CLAIM_LEDGER.md
docs/CANONICAL_RESULTS.md
docs/generated/submit_ready/main_tex_submit_ready_report.md
scripts/submit_ready_gate.py
```

Para una sección concreta, leer también sus figuras, tablas, entradas BibTeX, resultados generados y artefactos de los que dependa.

Referencias externas de control:

- Ficha oficial del TFM MROB: `https://www.universidadviu.com/sites/universidadviu.com/files/media_files/MROB.Trabajo%20Final%20de%20M%C3%A1ster.pdf`
- Página oficial del máster: `https://www.universidadviu.com/es/master-robotica-automatizacion-procesos`
- Memoria verificada del título: `https://www.universidadviu.com/sites/universidadviu.com/files/media_files/MRobotica_MV_20233101.pdf`
- Citas APA: `https://apastyle.apa.org/style-grammar-guidelines/citations`
- Referencias APA: `https://apastyle.apa.org/style-grammar-guidelines/references`
- Tablas y figuras APA: `https://apastyle.apa.org/style-grammar-guidelines/tables-figures`
- Formato APA: `https://apastyle.apa.org/style-grammar-guidelines/paper-format`

## Contrato VIU y plantilla local

Tomar como fuente estructural directa la diapositiva `Estructura del TFM` de la Tutoría Colectiva Intermedia TFM MROB del 17/06/2026. Exigir este orden:

```text
Portada
Resumen y palabras clave
Índice
1. Introducción
2. Objetivos
   2.1. Objetivo general
   2.2. Objetivos específicos
3. Hipótesis de partida
4. Metodología
5. Marco teórico
6. Resultados y análisis
   Validación de los resultados
7. Conclusiones y recomendaciones
8. Referencias bibliográficas
9. Anexos
```

Comprobar además que el TFM es original, personal e inédito, está relacionado con robótica o automatización industrial y mantiene correspondencia entre objetivos, hipótesis, resultados y conclusiones. El Abstract, las keywords, la nomenclatura y la declaración de IA pueden añadirse por exigencia de la plantilla o de la convocatoria, pero no sustituyen ni alteran el orden anterior.

Conservar el contrato LaTeX actual:

- `\documentclass[12pt,a4paper]{article}`.
- `\usepackage{viu-mrob-midreport}`.
- LuaLaTeX o XeLaTeX por el uso de `fontspec` y Arial.
- Español mediante `babel`.
- A4, cuerpo Arial 12 pt, interlineado 1,5 y estilos VIU definidos en `viu-mrob-midreport.sty`.
- Citas y referencias APA 7 mediante `biblatex-apa` y Biber, con la interfaz
  `natbib=true` para conservar los comandos `\citep` y `\citet` del manuscrito.

No mover estilos de documento a archivos de sección. No cambiar el diseño institucional para ganar páginas sin autorización del tutor.

## Límite de páginas

Aplicar estos límites como bloqueos:

- Documento principal: máximo 80 páginas.
- Anexos: máximo 8 páginas físicas en total.
- Empezar el conteo en la primera página de la Introducción.
- Excluir portada y preliminares anteriores a la Introducción.
- Incluir las referencias en el cupo de 80 páginas.
- Contar cualquier página que contenga material de anexo dentro del cupo de 8 páginas.
- Si el documento principal y el Anexo A comparten página, contarla de forma conservadora en ambos cupos.

Contar sobre el PDF final, nunca sobre líneas LaTeX ni solo con el índice. Tras aplicar el orden VIU de la tutoría, incorporar el desarrollo SP0 y retirar del PDF el desarrollo matemático extendido, que se conserva en el repositorio como material suplementario, la instantánea comprobada el 10 de julio de 2026 es `68/80` para el documento principal y `5/8` para anexos. Ambos bloques cumplen sus límites respectivos.

## Flujo obligatorio

1. Revisar `git status --short` y preservar cambios ajenos.
2. Leer el archivo objetivo y sus dependencias.
3. Ejecutar el gate antes de editar.
4. Corregir primero integridad, estructura, páginas, citas y afirmaciones.
5. Corregir después claridad, calcos y patrones mecánicos.
6. Compilar el PDF.
7. Revisar visualmente el PDF completo.
8. Ejecutar otra vez el gate y registrar advertencias pendientes.

```powershell
make submit-ready FILE=docs/doc-05-final-report/main.tex
make report-pdf
```

Para el cierre final:

```powershell
make submit-ready FILE=docs/doc-05-final-report/main.tex SIMILARITY_REPORT=path/to/report.pdf REQUIRE_SIMILARITY=1 STRICT=1
```

## APA 7

La memoria usa `biblatex-apa` con Biber y `sorting=nyt`. Esta configuración implementa el
estilo autor-año de APA 7 con más fidelidad que `apalike`, pero no reemplaza la revisión de
metadatos ni la inspección visual de la salida PDF. Declarar `langid` o una regla de idioma
cuando sea necesario para aplicar mayúsculas tipo oración; proteger con llaves solo siglas,
nombres propios y términos cuya capitalización deba conservarse.

### Citas en el texto

- Citar cada idea, definición, método, dato, estándar, figura o resultado ajeno.
- Situar la cita junto a la afirmación que respalda.
- Usar apellido y año de forma consistente.
- Citar a los dos autores en todas las citas de una obra con dos autores.
- Usar `et al.` desde la primera cita para obras de tres o más autores.
- Añadir página, párrafo, sección, tabla o ecuación en citas textuales.
- Ordenar de forma consistente varias obras dentro de un mismo paréntesis.
- Diferenciar obras del mismo autor y año con `a`, `b`, etc.
- Evitar citas de segunda mano. Si son inevitables, identificar la fuente original y citar como fuente consultada la obra realmente leída.
- No presentar como leído un documento que solo se conoce por un resumen, una revisión o una cita secundaria.
- No acumular cinco o más referencias al final de una afirmación genérica. Explicar qué aporta cada familia de fuentes.

### Lista de referencias

- Mantener correspondencia exacta entre citas y bibliografía.
- Eliminar `\nocite{*}` para una aplicación estricta de APA 7, salvo que VIU o el tutor exijan bibliografía consultada adicional.
- Ordenar alfabéticamente y aplicar sangría francesa en la salida final.
- Verificar autor, fecha, título y fuente de cada entrada.
- Incluir hasta 20 autores; para 21 o más, aplicar la elipsis prevista por APA 7.
- Escribir el DOI como URL `https://doi.org/...` cuando exista.
- Añadir fecha de recuperación solo para contenido diseñado para cambiar con el tiempo.
- Usar mayúsculas tipo oración en títulos cuando corresponda.
- Mantener nombre de revista y volumen con la cursiva requerida; no poner en cursiva el número de fascículo.
- Omitir la ciudad de la editorial en libros.
- Verificar DOI, URL, año, volumen, número y páginas contra la fuente original.
- No inventar metadatos ni completar BibTeX por analogía.

### Tablas y figuras

- Numerar y mencionar cada tabla o figura antes o cerca de su aparición.
- Usar títulos informativos, no promocionales.
- Definir abreviaturas, unidades, tamaño muestral, escenarios, intervalos y notas necesarias.
- Añadir `Elaboración propia` bajo el pie de todo diagrama, esquema, gráfico o figura creada por el autor; usar `\viuownsource` en LaTeX.
- Para una adaptación, usar `\viusource{Elaboración propia a partir de Autor (año)}` y citar la obra completa.
- Para una reproducción, usar `\viusource{Tomado de Autor (año, p. X)}` y respetar atribución, licencia o permiso aplicable.
- No marcar como propia una captura, imagen descargada, reproducción ni adaptación no declarada.
- En figuras generadas con scripts y datos propios, indicar `Elaboración propia`; si hubo asistencia generativa, declararla además en el anexo de IA.
- Mantener legibilidad en el PDF a tamaño de lectura normal.
- No duplicar en prosa todos los valores ya visibles en una tabla.
- Dar prioridad a la plantilla VIU cuando su formato visual entre en conflicto con el formato general de APA; mantener siempre la atribución y el contenido exigidos por APA.

## Español académico del TFM

Redactar para un tribunal técnico, no para una campaña comercial ni para un tutorial. Mantener una voz formal, directa y responsable.

- Formular una afirmación principal por párrafo.
- Identificar quién decide, ejecuta, mide o interpreta cuando sea relevante.
- Preferir verbos concretos: `mide`, `compara`, `estima`, `ejecuta`, `falla`, `limita`, `simula`, `converge`.
- Repetir el término técnico correcto. No rotar sinónimos para evitar repetición.
- Definir cada sigla en su primera aparición en el resumen, en el cuerpo y, cuando proceda, en pies autónomos.
- Mantener una persona gramatical estable. No alternar sin razón entre `se`, `nosotros`, `el autor` y `este trabajo`.
- Usar la pasiva solo si el actor no importa o si el objeto debe ocupar el foco.
- Separar resultado, interpretación y limitación.
- Conservar resultados negativos, decisiones metodológicas y dudas justificadas.
- Leer en voz alta. Reescribir cualquier oración que exija una segunda lectura para identificar sujeto, verbo o referente.

No introducir faltas, coloquialismos, fragmentos artificiales ni puntuación errática para “parecer humano”. La variación debe surgir de la lógica del argumento.

## Frontera de integridad frente a detectores

El propósito de esta auditoría es retirar residuos de chatbot, prosa genérica y mala traducción. No usarla para ocultar plagio o asistencia no declarada.

Prohibir:

- Homoglifos, caracteres invisibles, espacios de ancho cero o texto blanco.
- Capturas de texto para impedir extracción.
- Traducir y retraducir para disimular una fuente.
- Sustituir palabras con un “spinner” de sinónimos.
- Introducir errores deliberados o alterar puntuación al azar.
- Fabricar citas, DOI, resultados, decisiones o experiencias personales.
- Parafrasear una fuente manteniendo su sintaxis y cambiando solo vocabulario.
- Ajustar el documento con el único objetivo de reducir un porcentaje o una etiqueta de IA.

Conservar borradores, notas, scripts, resultados, historial de cambios y decisiones. Esos artefactos sostienen la autoría mejor que cualquier truco estilístico.

## Auditoría de patrones asociados a IA

Los patrones son señales de revisión, no pruebas de autoría. No cambiar una frase clara solo porque coincide con una lista. Evaluar función, densidad y repetición.

### P0: bloqueos inmediatos

Eliminar siempre del manuscrito:

- `como modelo de lenguaje`, `as an AI`, `as a language model`.
- `hasta mi última actualización`, `no tengo acceso a datos en tiempo real`.
- `espero que esto ayude`, `gran pregunta`, `excelente observación`.
- Restatements del prompt: `la pregunta solicita`, `para responder a tu pregunta`.
- Razonamiento interno: `pensemos paso a paso`, `mi proceso de razonamiento`, `primero consideraré`.
- Saludos, despedidas, ofrecimientos de ayuda y comentarios dirigidos al usuario.
- Marcadores de edición: `TODO`, `TBD`, `FIXME`, `XXX`, texto de ejemplo o instrucciones al redactor.

### P1: corregir antes de entregar

Corregir cuando aparezcan sin una función técnica clara:

- Aperturas universales como `hoy en día`, `en la era actual`, `en un mundo cada vez más`.
- Metanarración: `a continuación veremos`, `este capítulo explorará`, `vamos a analizar`.
- Énfasis vacío: `cabe destacar`, `es importante señalar`, `conviene mencionar`.
- Atribución vaga: `los estudios demuestran`, `la literatura confirma`, `los expertos consideran` sin cita próxima.
- Inflación: `revolucionario`, `transformador`, `sin precedentes`, `vanguardista`, `paradigmático`.
- Neutralidad automática que enumera ventajas y desventajas sin tomar una decisión razonada.
- Conclusiones intercambiables sobre un futuro prometedor o un campo que seguirá evolucionando.
- Encadenamiento de gerundios que aparenta análisis: `mostrando`, `demostrando`, `reflejando`, `evidenciando`.
- Nominalizaciones repetidas: `realización de`, `ejecución de`, `llevado a cabo`, `se procedió a` cuando existe un verbo directo.
- Cadenas de tres adjetivos, tres sustantivos o tres consecuencias usadas de forma sistemática.
- Encabezados genéricos y excesivos dentro de secciones breves.
- Listas simétricas donde cada punto tiene la misma longitud y construcción.

### Construcciones de contraste formularias

Marcar y revisar:

- `no es A, es B`.
- `no se trata de A, sino de B`.
- `no solo A, sino también B` cuando se repite.
- `más que A, B` usado como eslogan.
- `si bien A, B` o `aunque A, B` cuando ambas partes son vagas.
- `mientras que` cuando no expresa simultaneidad ni contraste real.

No prohibir un contraste necesario. Sustituir el molde por la afirmación positiva y su evidencia.

```text
Evitar: No es un problema de asignación, sino un problema físico.
Mejorar: La asignación debe incorporar restricciones físicas de fuerza y torque.

Evitar: El método no solo reduce colisiones, sino que también mejora la energía.
Mejorar: El método reduce la tasa de colisión del 4,8 % al 1,2 %. El consumo energético cambia en X bajo el mismo escenario.
```

### Transiciones y relleno

Reducir por repetición, no necesariamente por una aparición aislada:

- `además`, `asimismo`, `adicionalmente`.
- `por otro lado`, `por otra parte`, `en este sentido`.
- `en conclusión`, `en resumen`, `en síntesis` dentro de cada subsección.
- `de este modo`, `por consiguiente`, `en consecuencia` cuando la relación causal no está demostrada.
- `resulta evidente`, `claramente`, `sin duda`, `indudablemente`.
- `es preciso señalar que`, `merece la pena destacar que`.
- `a nivel de`, `en términos de`, `en lo que respecta a` cuando puede nombrarse la variable.

Unir párrafos mediante el contenido. La primera frase debe responder, limitar o desarrollar la idea anterior sin depender siempre de un conector.

### Calcos del inglés y falso español técnico

| Evitar o revisar | Preferir según el contexto |
|---|---|
| `hacer sentido` | `tener sentido` |
| `en orden a` | `para` |
| `correr un experimento` | `ejecutar un experimento` |
| `soportar una hipótesis` | `respaldar` o `sustentar una hipótesis` |
| `direccionar un problema` | `abordar` o `resolver un problema` |
| `realizar una decisión` | `tomar una decisión` |
| `performar` o `performance` | `rendir`, `rendimiento` o la métrica concreta |
| `aplicar el método sobre el problema` | `aplicar el método al problema` |
| `los datos evidencia` | `los datos muestran` o `la evidencia indica` |
| `las evidencias` | `la evidencia`, `los indicios` o `los resultados` |
| `estar en línea con` | `coincidir con`, `ser compatible con` |
| `consistente con` | `coherente con` o `compatible con`, salvo sentido matemático preciso |
| `eventualmente` por *eventually* | `finalmente` |
| `actualmente` por *actually* | `en realidad` |
| `comprensivo` por *comprehensive* | `exhaustivo`, `integral` o `completo` |
| `sensible` por *sensible* | `razonable` o `prudente` |
| `accuracy` como `precisión` | `exactitud` si esa es la métrica; distinguirla de precisión |
| `baseline` sin definir | `referencia`, `línea base` o `comparador` |
| `framework` repetido | `marco`, `arquitectura` o término inglés definido una vez |
| `paper` | `artículo`, `trabajo` o `publicación` |
| `data` | `datos` |
| `significativo` sin contraste | `relevante`, `apreciable` o una diferencia numérica |

No traducir nombres oficiales, algoritmos ni términos asentados si la traducción crea ambigüedad. Definir una vez `wrench`, `baseline`, `framework`, `rollout` u otro término conservado y usarlo de forma estable.

### Léxico inflado

Revisar por densidad: `robusto`, `integral`, `innovador`, `escalable`, `efectivo`, `dinámico`, `sofisticado`, `crucial`, `clave`, `holístico`, `perfecto`, `óptimo`, `seamless`, `leverage`, `delve`, `pivotal`.

Mantener un término si tiene significado verificable. `Control robusto`, `optimización robusta`, `dinámica de Smith` y `escalabilidad de flota` son expresiones técnicas válidas cuando se definen y miden. Eliminar el adjetivo cuando solo significa “bueno”.

### Puntuación y ritmo

- Objetivo para `—` y ` -- ` en prosa: cero. Sustituir por coma, paréntesis, dos puntos o dos oraciones.
- No tocar `2025--26`, rangos de páginas BibTeX, opciones como `--strict`, operadores matemáticos ni código.
- Usar `;` solo entre oraciones estrechamente relacionadas o en enumeraciones complejas. Revisar párrafos con tres o más.
- Usar `:` después de una proposición completa para anunciar explicación, lista o consecuencia. No separarlo del verbo y su complemento.
- Evitar dos puntos repetidos como mecanismo de énfasis: `La conclusión es clara:`.
- Limitar paréntesis anidados y aclaraciones consecutivas.
- Dividir oraciones de más de 45 a 55 palabras cuando la estructura matemática no las justifique.
- Variar la longitud de las oraciones según la función, no al azar.
- Evitar que todos los párrafos tengan tres o cuatro oraciones y una extensión similar.
- No iniciar cinco párrafos consecutivos con `Este`, `Esta`, `El`, `La` o el mismo conector.

### Señales de autoría sustantiva

Conservar y reforzar cuando sean verdaderas:

- Motivo concreto de una decisión metodológica.
- Alternativa considerada y razón para descartarla.
- Resultado inesperado o negativo.
- Límite del simulador, los datos o la inferencia.
- Número, escenario, semilla, figura, tabla o artefacto verificable.
- Diferencia entre lo esperado y lo observado.
- Relación explícita entre resultado, objetivo e hipótesis.

No añadir anécdotas, emociones o primera persona solo para humanizar. La voz académica surge de decisiones específicas y responsabilidad sobre la interpretación.

## Protocolo de reescritura

Aplicar por párrafos, no mediante reemplazo global ciego:

1. Identificar la afirmación que el párrafo debe sostener.
2. Separar datos, interpretación, antecedentes y limitación.
3. Eliminar metanarración, relleno y énfasis no ganado.
4. Sustituir calcos y nominalizaciones por español directo.
5. Mantener términos técnicos, cifras, citas, etiquetas y alcance científico.
6. Añadir la fuente o evidencia exacta junto a la afirmación.
7. Expresar la limitación sin convertirla en una concesión vacía.
8. Leer el párrafo en su contexto y ajustar el puente con el anterior.
9. Ejecutar una segunda auditoría después de la reescritura.

Reescribir desde cero un párrafo cuando combine tres o más familias de patrones, presente sintaxis uniforme y carezca de una afirmación verificable. Partir de la evidencia y reconstruir el argumento. No parchear palabra por palabra.

## Salida obligatoria de una revisión

Entregar una tabla o informe con:

- Archivo y ubicación.
- Severidad: `P0 bloqueo`, `P1 corregir`, `P2 revisar`.
- Fragmento original.
- Tipo de patrón.
- Revisión propuesta.
- Justificación lingüística o científica.
- Riesgo de alterar significado.

En modo corrección, aplicar los cambios seguros y enumerar los que requieren decisión del autor. En modo detección, no modificar archivos.

No reportar como problema las apariciones dentro de:

- Ejemplos explícitamente marcados como incorrectos.
- Citas textuales.
- Código, comandos, rutas y opciones CLI.
- Fórmulas, rangos, claves BibTeX y nombres oficiales.
- Bibliografía cuando la puntuación pertenece al estilo de referencia.

## Originalidad, similitud y Turnitin

El porcentaje de similitud no equivale a plagio y un indicador de escritura con IA no demuestra autoría. Revisar el informe fuente por fuente.

- Distinguir coincidencias en bibliografía, frases técnicas estándar, citas, metodología reutilizada y prosa sustantiva.
- Corregir primero fragmentos largos idénticos o con estructura demasiado próxima a la fuente.
- Parafrasear después de comprender: cerrar la fuente, redactar la idea desde el argumento propio y verificar fidelidad al volver a abrirla.
- Citar aunque la redacción sea propia si la idea, el dato o el método procede de otra obra.
- Usar comillas y localizador para texto literal.
- Revisar autorreutilización entre entregas y cumplir la política del campus.
- No interpretar los umbrales locales de 15 % y 20 % como garantía oficial de VIU.
- No declarar el documento listo sin revisar manualmente el informe externo cuando exista.

## Declaración de uso de IA

La declaración debe ser específica, sobria y verdadera. Indicar, cuando corresponda:

- Herramienta utilizada.
- Tareas concretas: corrección lingüística, organización, código auxiliar, búsqueda u otras.
- Secciones o fases afectadas.
- Verificación realizada por el autor.
- Responsabilidad del autor sobre datos, citas, decisiones, interpretación y versión final.

No afirmar “sin uso de IA” si hubo asistencia. No presentar texto, imágenes, datos o referencias generados como evidencia experimental.

## Seguridad de afirmaciones de esta tesis

Consultar `docs/THESIS_NARRATIVE_LOCK.md`, `docs/CLAIM_LEDGER.md` y `docs/CANONICAL_RESULTS.md` antes de reforzar una conclusión.

Permitir:

- Suite reproducible SP1-SP8 dentro del simulador implementado.
- Inferencias acotadas a escenarios y supuestos documentados.
- Crítica de factibilidad wrench planar cuasiestática en SP3.
- Conclusiones mesoscópicas de escalabilidad en SP8.
- Ley AMR explícita descrita como capa simulada de orden reducido.

Bloquear:

- Superioridad universal.
- Validación industrial o despliegue físico no ejecutado.
- Uso de vídeos como única prueba.
- Equivalencia entre factibilidad wrench y manipulación física completa.
- SP9 como ejecutado sin manifiesto, CSV, figuras e informe trazable.
- Conversión de resultados negativos o mixtos en conclusiones positivas.

Cada afirmación fuerte debe apuntar a una cita, un artefacto canónico, una entrada del ledger o una hipótesis/limitación claramente marcada.

## Revisión por sección

- Resumen: problema, método, evidencia numérica, contribución y límite.
- Introducción: problema específico, brecha respaldada, contribución y estructura breve.
- Objetivos: verbos medibles y correspondencia con resultados.
- Hipótesis: formulación falsable y resultado o limitación posterior.
- Metodología: simulador, escenarios, métricas, baselines, semillas, criterios y procedencia de datos.
- Marco teórico: síntesis crítica de fuentes primarias, no catálogo de artículos.
- Modelo: variables definidas, ecuaciones interpretadas y supuestos visibles.
- Resultados y análisis: cifras antes de valoración, comparadores justos, resultados negativos y un bloque visible de validación de los resultados.
- Discusión: explicación, contraste con literatura, validez y límites.
- Conclusiones y recomendaciones: respuesta a objetivos e hipótesis, límites y recomendaciones concretas sin introducir resultados nuevos.
- Anexos: material indispensable, citado desde el cuerpo y limitado a ocho páginas.

## Gate local

El gate debe comprobar:

- Plantilla y secciones VIU.
- Compilación y texto extraíble.
- Cupos `80 + 8`.
- Claves de cita y entradas BibTeX.
- Declaración de IA.
- Placeholders y residuos de chatbot.
- Densidad de patrones formularios, contrastes y puntuación.
- Afirmaciones incompatibles con el narrative lock.
- Duplicados internos e informe de similitud externo.

Umbrales locales por defecto:

```text
min_words = 5000
min_citations = 20
min_bib_entries = 20
max_main_pages = 80
max_appendix_pages = 8
similarity_warn_pct = 15.0
similarity_block_pct = 20.0
human_warn_density = 4.0
human_block_density = 12.0
```

## Lista final

No declarar `submit-ready` hasta confirmar:

- PDF compilado, seleccionable y revisado visualmente.
- Máximo 80 páginas principales desde la Introducción y 8 de anexos.
- Portada, índice, encabezados y numeración correctos.
- Español natural, preciso y sin calcos repetidos.
- Cero residuos de chatbot o proceso interno.
- Contrastes `no es A, sino B`, tríadas, transiciones y puntuación revisados en contexto.
- Figuras y tablas legibles, citadas y atribuidas.
- Citas resueltas y referencias verificadas según APA 7.
- Sin `\nocite{*}` salvo autorización expresa.
- Resultados, cifras y conclusiones alineados con artefactos canónicos.
- Limitaciones y resultados negativos conservados.
- Declaración de IA exacta.
- Informe de similitud revisado fuente por fuente.
- Gate sin bloqueos y advertencias aceptadas de forma explícita.
- PDF final en `docs/doc-05-final-report/main.pdf`.
