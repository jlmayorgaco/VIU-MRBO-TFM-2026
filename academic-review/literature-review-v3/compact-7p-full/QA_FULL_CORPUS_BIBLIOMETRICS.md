# QA — Figura 4 completa y estructura bibliométrica

## Artefacto

- PDF: `output/pdf/MROB_literature_review_7p_full_corpus_bibliometrics.pdf`
- Páginas: 7, tamaño letter `612 × 792 pt`.
- SHA-256 final: `DFE3C6647EC37C2D9CD799400ACE50F4E0A4FD706182C761527D3A09B8EEB9E2`.
- Corpus: `analytic_corpus_v3.csv`, SHA-256
  `0398EF95EF421C021A0FBF2D8F2C4DFBF117D1BA664E75B8BB982CF68A36D297`.

## Controles cuantitativos

- 244 documentos analíticos; 243 con año entre 1979 y 2026; uno sin año.
- Cada documento aporta peso temático total 1. Las cuotas de los cuatro
  periodos suman 100 % dentro de precisión numérica.
- La diversidad móvil se mantuvo en `[0,1]`; para 2026, la ventana 2024--2026
  produjo `H*=0,886021`.
- 807 cadenas exactas de autor, 72 recurrentes (`>=2` documentos), 11
  componentes mostrados (`>=3` autores), 41 nodos y 49 aristas.
- Red temática: 20 nodos, 90 coocurrencias con frecuencia `>=2`, backbone de
  50 aristas y tres comunidades Louvain; modularidad `Q=0,202332`.
- 117 venues normalizados. Primeros: IEEE Access 23, JINT 20, Autonomous
  Robots 12, arXiv 10, Sensors 8, LNCS 7 y Frontiers RAI 6.

## Lecturas que cambian respecto al corte legado

- Aprendizaje/RL aumenta `+6,25 p.p.` entre `<=2010` y 2022--2026, pero no
  domina el corpus ampliado.
- Coalición/MRTA reduce su cuota fraccional `-5,97 p.p.` y sigue siendo la
  familia más visible.
- Factibilidad/contacto aumenta `+2,52 p.p.` y planificación/routing
  `+1,54 p.p.`; recuperación/reemplazo cae `-2,68 p.p.`.
- La señal distribuida fluctúa por año y no sustenta una tendencia monótona.
- La modularidad temática baja favorece interpretar el área como combinación
  de capas y aplicaciones, no como escuelas separadas.

## Verificación editorial y visual

- El capítulo sigue una secuencia continua: protocolo y reglas de lectura;
  cobertura funcional; integración y centralización residual; evolución
  temática; persistencia y madurez de la evidencia; contraste experimental; y
  discusión bibliométrica.
- Solo la primera página presenta el título del capítulo. Las páginas 2--7
  continúan el argumento mediante párrafos de enlace, sin títulos que reinicien
  el texto como artículos o informes independientes.
- Se retiraron las bibliografías intermedias de las antiguas páginas 4 y 6. Las
  citas conservan una sola numeración y quedan destinadas a la bibliografía
  general del TFM, como corresponde a un capítulo de la memoria.
- Las Figuras 1--8 se conservaron. Cada bloque visual queda precedido por la
  pregunta o regla que lo organiza y seguido por una interpretación conectada
  con la arquitectura SP1--SP3.
- Las páginas 1--3 se recompilaron desde una fuente LaTeX editable conservando
  la geometría, composición, paleta, escalas y datos de la referencia visual.
  La página 2 conserva además la delimitación de novedad en lenguaje académico.
- La página 4 conserva el dashboard de seis paneles, paleta y jerarquía, con
  los 244 registros y límites de interpretación visibles. El espacio antes
  ocupado por una bibliografía local desarrolla la lectura temporal y enlaza
  con las Figuras 5--6.
- Las páginas 5--6 conservan la síntesis integrada. La Figura 7 expresa los
  estados operativos en español y cierra con una síntesis del contraste. Su
  realimentación sigue un trazado ortogonal de tres segmentos, con dos codos
  de 90 grados y sin solapamientos con el rótulo, la fuente o la tabla.
- La página 7 incorpora coautoría, red temática y matriz autor--tema. Se retiró
  la franja de cinco cifras, se ampliaron las redes y el panel (c) usa códigos
  A1--A8 con una clave lateral. Los tres paneles se interpretan dentro de una
  sola discusión sobre especialización, puentes y límites de inferencia.
- La búsqueda de texto visible no encontró rótulos de versión, nombres internos
  de archivos, rutas del repositorio, vocabulario de proceso, títulos
  ``Resultados:''/``Discusión:'' ni encabezados bibliográficos intermedios.
- El texto interno de las Figuras 1--8 usa Noto Sans. En particular, los
  paneles 3(a) y 3(b), la matriz de la Figura 2 y las Figuras 5--6 regeneradas
  comparten la misma familia; Noto Serif queda reservado para prosa, pies y
  líneas de fuente.
- Las familias Noto Sans y Noto Serif están incrustadas y no aparecen recursos
  Arial o DejaVu; las únicas fuentes adicionales corresponden a símbolos
  matemáticos de TeX.
- La última compilación no registró referencias indefinidas, caracteres
  ausentes ni errores LaTeX, y la inspección visual no mostró recortes ni
  solapamientos.
- Se inspeccionaron visualmente las siete páginas de la compilación final
  `DFE3C664`, renderizadas a 144 dpi.
- `python -m pytest academic-review/tests -q`: 68 pruebas aprobadas; una
  advertencia externa de compatibilidad de `requests`, sin fallo funcional.

## Límites

Los resultados describen el corpus adquirido. Las etiquetas proceden de
título/resumen y no prueban implementación ni rendimiento. La desambiguación de
autores permanece pendiente; las comunidades pueden dividir personas con
variantes nominales. WoS F01/F02 y la cartera arXiv siguen parciales, por lo que
no se afirma cobertura exhaustiva ni prevalencia del campo completo.
