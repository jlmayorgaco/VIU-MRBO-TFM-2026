# Esqueleto canónico de la memoria VIU

## Propósito y resultado observable

Crear en `thesis/` una memoria LaTeX modular, limpia y compilable que use el título administrativo vigente, contenga los preliminares exigidos por la VIU y refleje la estructura científica SP0--SP8 sin incorporar resultados no auditados del borrador histórico.

## Contexto y archivos canónicos

El alcance procede de `docs/00_TFM_CHARTER.md`; el formato y la estructura, de `docs/01_VIU_REQUIREMENTS.md`; la agrupación de resultados, de `docs/02_RESEARCH_MATRIX.md`; y la prudencia de las afirmaciones, de `docs/04_CLAIMS_EVIDENCE.md`. El borrador previo de `thesis/` se conserva en `tmp/thesis-backup-20260714-pre-scaffold/` y no se considera fuente canónica.

## Alcance y no alcance

Incluye portada, resumen y abstract provisionales, índices, nomenclatura inicial, siete capítulos con apartados mínimos, bibliografía APA 7 preparada para Biber, anexo de reproducibilidad y documentación de compilación. No incluye redacción sustantiva de capítulos, incorporación de resultados, verificación bibliográfica ni conclusiones científicas.

## Supuestos y preguntas resueltas

- Se usa el título administrativo sin sustituirlo por el título técnico de trabajo.
- Se mantiene el estilo visual disponible de la VIU, corrigiendo los márgenes a los valores canónicos.
- Los capítulos se implementan como secciones de nivel superior para conservar compatibilidad con la plantilla LaTeX existente basada en `article`.
- El resumen describe propósito, método y validación prevista; no presenta resultados como hechos.

## Diseño matemático/técnico

`main.tex` actúa como raíz. Los metadatos y comandos matemáticos se separan en `config/`; los preliminares, capítulos y anexos se organizan en directorios propios. LuaLaTeX proporciona Arial mediante `fontspec`; `biblatex` y Biber gestionan APA 7. Los artefactos de compilación se aíslan en `thesis/build/`.

## Plan experimental

No aplica a este cambio de infraestructura documental. La única validación funcional es compilar, comprobar referencias internas y revisar visualmente portada, índices, encabezados, márgenes y transiciones.

## Hitos

- [x] Respaldar el borrador previo.
- [x] Crear la estructura modular y el contenido preliminar.
- [x] Compilar sin errores fatales.
- [x] Inspeccionar visualmente el PDF.
- [x] Revisar el diff y documentar el comando reproducible.

## Validación

Desde `thesis/`: `.\build.ps1`. Se aceptará el esqueleto si existe `build/main.pdf`, no hay referencias o citas indefinidas y la inspección visual no muestra texto cortado o solapado. `latexmk` queda como alternativa cuando el entorno disponga de Perl.

## Riesgos y mitigaciones

El resumen quedará incompleto hasta contar con evidencia consolidada; se formula sin cifras ni afirmaciones fuertes. La plantilla LaTeX es una reproducción técnica y no sustituye la plantilla Word oficial, por lo que deberá compararse de nuevo antes de la entrega definitiva.

## Registro de decisiones

- 2026-07-14: se archiva el borrador previo porque contradice el título y el alcance canónicos actuales.
- 2026-07-14: se conserva LuaLaTeX para cumplir el requisito tipográfico de Arial.
- 2026-07-14: la bibliografía nace vacía; solo se añadirán fuentes verificadas y citadas.

## Progreso

Fuentes canónicas leídas, copia histórica creada y árbol LaTeX generado. El script de compilación produjo un PDF A4 de 19 páginas. Se revisaron visualmente todas las páginas y se corrigieron la posición del título de portada y un salto de página defectuoso en el bloque SP8. El resumen tiene 239 palabras y el abstract 221. El log no contiene cajas desbordadas, referencias indefinidas ni caracteres ausentes; permanece únicamente la advertencia esperada de bibliografía vacía hasta incorporar citas verificadas.
