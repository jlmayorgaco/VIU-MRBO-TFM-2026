# Changelog de la revisión editorial SP1 v2

## Línea base

- Fecha: 2026-08-15.
- PDF: `output/pdf/sp1_levels/SP1_levels_N1_N2_N3_N4.pdf`.
- Páginas: 48.
- Alcance: edición; sin cambios en resultados, hipótesis, conclusiones
  científicas, atlas, familias ni IDs históricos.

## Registro de cambios no triviales

| Fecha | Archivo/bloque | Cambio | Motivo | Efecto científico |
|---|---|---|---|---|
| 2026-08-15 | Plan de revisión | Se fijó la línea base, los límites y la validación | Evitar una edición estructural no autorizada | Ninguno |
| 2026-08-15 | `main.tex`, N1--N3 | Se normalizaron decimales, millares, notación científica, `puestos`, `brecha`, siglas y nombres de métodos | Aplicar la convención española y eliminar ambigüedad terminológica | Ninguno; cifras y signos se conservan |
| 2026-08-15 | Protocolo | Se explicitó la unidad mundo--semilla, el pareamiento dentro de celda y la ausencia de números aleatorios comunes entre celdas | Hacer auditable el diseño Monte Carlo | Ninguno; describe el protocolo existente |
| 2026-08-15 | N1--N3 | Se compactaron introducciones, resultados, respuestas y límites; se añadieron anclajes AMR y transiciones entre niveles | Convertir una sucesión de reportes en una argumentación continua | Ninguno; no cambian hipótesis ni conclusiones |
| 2026-08-15 | N4, F-I--F-IV | Se movió únicamente el bloque de concurrencia de F-I, se ordenó la tabla-guía y se uniformaron los recuadros de respuesta | Presentar primero el mecanismo y después su ejecución concurrente | Ninguno; familias, atlas y E1--E9 permanecen intactos |
| 2026-08-15 | N4, resultados formales | Se reservó R1--R6 para la tabla de trazabilidad y se enlazó cada ID con identidad, lema, proposición o recuadro | Evitar una doble numeración engañosa | Ninguno; enunciados y condiciones se conservan |
| 2026-08-15 | `docs/05_NOTATION.md` | `\mathcal N_h(a)` pasó a `\mathcal V_h(a)` como vecindad estratégica | Evitar colisión con el nivel N1 | Ninguno; conjunto y dominio son idénticos |
| 2026-08-15 | Generadores y figuras | Se regeneraron en modo de análisis con coma decimal, espacios finos, etiquetas españolas y ajustes locales de legibilidad | Hacer coherentes texto y gráficos sin editar datos a mano | Ninguno; datos de origen sin cambios |
| 2026-08-15 | Figura 1 | Se redujo localmente la escala vertical y se retiró el solapamiento con los parámetros de E4 | Conservar la primera página y la paginación contractual | Ninguno |
| 2026-08-15 | `tests/test_sp1_levels.py` | El congelado literal de prosa N1 se sustituyó por comprobaciones de datos, orden E1--E4 y título autorizado | Permitir edición sin relajar el contrato científico | Refuerza la comprobación de evidencia; no altera resultados |
| 2026-08-15 | Conclusiones de la memoria | Se reflejó como trabajo futuro la comparación FULL/AGG y el canal degradado | Mantener simetría entre la tabla-guía N4 y el cierre general | Ninguno; se declara una limitación existente |
| 2026-08-16 | Protocolo común | Se reescribieron escenarios, unidad mundo--semilla, remuestreo y elección del contraste; se añadió una tabla compacta de endpoints | Hacer visible el paso de la campaña Monte Carlo a la inferencia sin recurrir a prosa formularia | Ninguno; el diseño y los contrastes permanecen intactos |
| 2026-08-16 | N1--N3 | Se sustituyeron recuadros repetitivos y párrafos abstractos por respuestas directas ligadas a cifras y límites | Dar continuidad causal a cardinalidad, atomicidad y localidad informativa | Ninguno; cifras, hipótesis y transiciones se conservan |
| 2026-08-16 | N4 | Se explicitó la jerarquía F-I/F-II/F-III/F-IV, el alcance parcial de Q4 y la lectura exacta de E9; se reorganizaron el programa, la trazabilidad formal y la síntesis N1--N4 | Separar contribución, comparadores, piloto y alcance declarado | Ninguno; E9 sigue siendo una frecuencia observada hasta $h=3$, no un porcentaje de beneficio |
| 2026-08-16 | Citas de N4 | Se añadieron DPOP y aprendizaje log-lineal en sus primeras apariciones, con límites de transferencia a las variantes implementadas | Anclar las familias en fuentes verificadas sin heredar garantías no demostradas | Ninguno |
| 2026-08-16 | Maquetación | Se ampliaron tablas críticas, se corrigieron títulos, densidad y espacios, y se revisaron las 48 páginas renderizadas | Mantener legibilidad de cuerpo y algoritmos sin alterar la paginación | Ninguno |
| 2026-08-16 | `main.tex` y `n4_v2.tex` | Se retiraron recuadros de respuesta y rótulos formularios, se acortaron títulos y se reescribieron transiciones, interpretaciones y límites como prosa continua | Reducir repetición, metadiscurso y cadencias mecánicas sin sustituirlas por sinónimos superficiales | Ninguno; se mantienen cifras, signos, pruebas y alcance |
| 2026-08-16 | Limpieza para entrega | Se retiraron del PDF identificadores técnicos, estados internos y términos de control; se sustituyeron por descripciones directas del diseño y del resultado. También se eliminó el borrador N4 obsoleto situado después de `\end{document}` y se regeneraron las figuras afectadas desde los datos existentes | Evitar que el capítulo se lea como un informe de desarrollo y dejar una única versión vigente del manuscrito | Ninguno; no se ejecutaron campañas ni se modificaron datos, cifras o conclusiones |
| 2026-08-16 | Auditoría correctiva N1--N4 | Se corrigieron exceso y cobertura en N2; estadísticos Friedman/Kendall; semántica de `DIVERGED`; vecindades de 2BR/C3; orden conectado de E9; terminación sin truncamiento; máquina bifásica de Geo-LLL; juego vGNE; registros versionados y cierre común | Hacer coincidir cada afirmación con la implementación y el dominio realmente evaluado | Refuerza el alcance de los enunciados; no altera RAW ni resultados |
| 2026-08-16 | Denominadores y frontera contable | Se distinguieron los bancos de N3.E2 (1.159/41) y N4.E4/E7 (1.160/40), se fijaron 90 ejecuciones por presupuesto en N2.E4 y se declaró que los bytes de F-II/F-III excluyen el postproceso central $\mathcal R$ | Evitar comparaciones con denominadores o fronteras arquitectónicas ambiguas | Ninguno; se documentan campañas y contadores existentes |
| 2026-08-16 | Figuras y paginación | Se separaron inferencia y relevancia práctica en el protocolo, se corrigieron atlas y diagramas N4 y se recompusieron las páginas densas sin invadir el margen inferior | Eliminar solapamientos y contenido recortado manteniendo el extracto en 48 páginas | Ninguno |

## Evidencia preservada

- No se ejecutaron campañas nuevas ni se modificaron semillas, configuraciones,
  hipótesis, endpoints, signos o valores.
- `git diff -- experiments/configs` no presenta cambios de contenido.
- Las comprobaciones automáticas de los datos críticos de E4, E7 y E9 siguen
  aprobadas respecto de la línea base.

## Comprobaciones finales

- [x] Convención numérica española en texto y figuras; cero decimales con punto
  en la extracción final.
- [x] Siglas desarrolladas en primera aparición.
- [x] Notación y algoritmos sin colisiones.
- [x] Orden F-I corregido y referencias actualizadas.
- [x] Tabla-guía N4 y recuadros de respuesta uniformes.
- [x] Prosa revisada y anclajes AMR incluidos.
- [x] PDF de 48 páginas revisado completo; páginas 1, 12, 39, 41 y 48 revisadas
  de nuevo a 150 dpi. Sin recortes, solapamientos ni páginas de arrastre.
- [x] Datos experimentales intactos y configuraciones sin diferencias.
- [x] 96 pruebas SP1/N3/N4 aprobadas.
- [x] Log del extracto sin `Overfull`, referencias indefinidas ni errores fatales.
- [x] Barrido del texto extraído: sin guiones largos ni recuadros `qresponse`;
  los conectores frecuentes aparecen solo de forma puntual.
- [x] Barrido de entrega: sin metadatos de ejecución, estados internos ni marcas
  editoriales en el PDF.
- [x] Cinco figuras TikZ protegidas verificadas en fuente y en el auxiliar de la
  memoria completa; `thesis/build.ps1` generó `main.pdf` de 120 páginas, sin
  cajas desbordadas ni referencias indefinidas.

## Artefacto final y limitaciones

- PDF final: `output/pdf/sp1_levels/SP1_levels_N1_N2_N3_N4.pdf`.
- El extracto conserva un aviso intencional de `hyperref` por modo borrador y
  avisos `Underfull` en algunas tablas compactas; no producen un defecto
  visible. La memoria completa compila, pero mantiene avisos heredados de
  glifos, sustitución de fuentes y tablas estrechas fuera del alcance de esta
  revisión.
- Esta revisión es editorial. No aporta evidencia nueva ni amplía el dominio de
  validez de N1--N4.
- La revisión reduce indicios estilísticos observables, pero no permite prometer
  un resultado en Turnitin ni atribuir validez científica a sus clasificadores.
