# Puerta VIU no especialista para SP1.N1

## Propósito y resultado observable

Evaluar las diez páginas de SP1.N1 desde el punto de vista de un miembro del
tribunal que conoce las normas de la VIU, pero no domina asignación multi-robot,
optimización ni estadística no paramétrica. El resultado observable será un
dictamen independiente, una versión revisada que pueda seguirse sin reconstruir
la lógica técnica y un PDF de diez páginas verificado visualmente.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md` y
  `docs/07_SP_SECTION_TEMPLATE.md` fijan alcance, formato y lenguaje.
- `docs/04_CLAIMS_EVIDENCE.md` limita las afirmaciones de N1.
- `thesis/sp1_levels_23p/main.tex` produce el extracto evaluado.
- `output/pdf/sp1_n1_10p/SP1_N1_10P.pdf` es el entregable vigente.
- La revisión técnica adversarial anterior permanece en
  `reports/2026-08-06-sp1-n1-adversarial-jury-review.md`.

## Alcance y no alcance

Incluye comprensión, continuidad narrativa, definición de siglas y tecnicismos,
lectura de figuras, referencias cruzadas, cumplimiento formal VIU y consistencia
entre pregunta, dato y respuesta. No reabre semillas, hipótesis, métricas ni
resultados; tampoco califica N2--N4 ni la memoria completa.

## Supuestos y preguntas resueltas

- El lector debe entender qué pregunta responde cada página sin conocimientos
  previos de optimización.
- El rigor no se reduce: cada término técnico necesario conserva su nombre, pero
  recibe una traducción breve en lenguaje común.
- La nota objetivo de 4,9/5 es una puerta interna, no una promesa de calificación.

## Diseño matemático/técnico

No cambia la formulación. La intervención se limita a una capa editorial:
definir abreviaturas al primer uso, explicar medidas estadísticas en la frase
que las interpreta, citar cada figura antes de insertarla y distinguir con
lenguaje directo entre observación, certificado y límite.

## Plan experimental

No se ejecutan nuevos experimentos. Se contrastarán el PDF, el LaTeX, la
configuración congelada y la matriz de evidencia. Las cifras deben permanecer
idénticas antes y después de la revisión.

## Hitos

- [x] Hito 1 -- dictamen inicial de solo lectura con hallazgos por página.
- [x] Hito 2 -- corrección de problemas mayores de comprensión y formato.
- [x] Hito 3 -- PDF recompilado y diez páginas inspeccionadas visualmente.
- [x] Hito 4 -- re-revisión cerrada, pruebas y validadores aprobados.

## Validación

- Extraer y revisar el texto completo del PDF.
- Comprobar que todas las figuras y tablas se citan en la prosa.
- Compilar el extracto y exigir exactamente diez páginas.
- Renderizar las diez páginas y revisar cortes, solapes, densidad y jerarquía.
- Ejecutar pruebas dirigidas, comprobador TikZ protegido y búsqueda de avisos
  LaTeX de referencias o cajas desbordadas.

## Riesgos y mitigaciones

- **Simplificación excesiva:** conservar el término técnico junto a su glosa.
- **Desbordamiento:** sustituir prosa en vez de añadir bloques redundantes.
- **Cambio de significado:** contrastar cada edición con la matriz de evidencia.
- **Falsa apariencia de capítulo autónomo:** mantener explícito que es un extracto
  de Resultados y análisis para integración en la memoria VIU.

## Registro de decisiones

- 2026-08-06: se abre una segunda puerta independiente de la revisión técnica,
  centrada en comprensión y cumplimiento VIU.
- 2026-08-06: el dictamen se registra antes de editar el manuscrito; la revisión
  académica permanece de solo lectura y la remediación se ejecuta después como
  una fase editorial separada.

## Progreso

Puerta cerrada. El PDF final conserva diez páginas, supera 32 pruebas dirigidas,
el comprobador de las cinco figuras TikZ protegidas y la revisión del registro
LaTeX sin avisos de desbordamiento ni referencias indefinidas. El dictamen de
re-revisión queda registrado en
`reports/2026-08-06-sp1-n1-viu-nonspecialist-review.md`.
