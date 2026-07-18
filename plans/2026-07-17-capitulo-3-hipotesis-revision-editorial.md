# Revisión editorial del capítulo 3 de hipótesis

## Propósito y resultado observable
Reescribir el capítulo 3 para eliminar la referencia inexistente, corregir frases truncadas y patrones de redacción artificial, y conservar una formulación científica fluida y contrastable. El capítulo compilado ocupará como máximo dos páginas.

## Contexto y archivos canónicos
Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, la evidencia de `docs/04_CLAIMS_EVIDENCE.md`, los objetivos de `thesis/sections/mainmatter/02-objectives.tex` y el estado final de las hipótesis en `thesis/sections/mainmatter/07-conclusions.tex`. El archivo que se modifica es `thesis/sections/mainmatter/03-hypotheses.tex`.

## Alcance y no alcance
Incluye estructura argumental, claridad, cohesión, terminología y criterios de refutación. No modifica resultados, estados finales de las hipótesis, numeración científica, alcance administrativo ni notación canónica.

## Supuestos y preguntas resueltas
Cargo planar soportado sigue siendo el modo físico primario. H1 se conserva dividida en H1a--H1c porque las tres afirmaciones tienen tratamientos y evidencias distintos. H5 se conserva dividida en H5a--H5b para separar coste y calidad bajo escala. Los resultados conocidos no se anticipan en este capítulo.

## Diseño matemático/técnico
La secuencia será: introducción del marco de contraste, hipótesis principal, hipótesis específicas agrupadas por capacidad y cierre metodológico común. Cada hipótesis tendrá un enunciado direccional y una condición de refutación o falta de sustento, sin duplicar el protocolo estadístico del capítulo 4.

## Plan experimental
No se ejecutan experimentos nuevos. La comprobación se limita a consistencia con artefactos existentes, referencias LaTeX, compilación y revisión visual del PDF.

## Hitos
- [x] Hito 1: diagnóstico editorial y científico del texto actual.
- [x] Hito 2: capítulo reescrito sin referencias huérfanas ni frases truncadas.
- [x] Hito 3: compilación limpia y verificación visual de un máximo de dos páginas.
- [x] Hito 4: auditoría final de patrones de IA, terminología y diff.

## Validación
Compilar con `thesis/build.ps1`; buscar referencias indefinidas y cajas desbordadas en el log; extraer el intervalo del capítulo; renderizar sus páginas a PNG; comprobar legibilidad, continuidad y extensión; revisar `git diff --check` y el diff limitado al archivo.

## Riesgos y mitigaciones
La densidad puede superar dos páginas: se eliminará duplicación metodológica antes de reducir tipografía o espaciado. El árbol contiene cambios ajenos en otros capítulos y en el estilo: se preservarán y no se editarán.

## Registro de decisiones
- 2026-07-17: sustituir la referencia a `tab:operationalization` por una explicación autosuficiente, ya que la tabla no existe.
- 2026-07-17: mantener H1a--H1c y H5a--H5b para conservar la trazabilidad con resultados y conclusiones.
- 2026-07-17: aplicar un perfil de escritura académica técnica; se permite vocabulario técnico preciso, pero se eliminan aperturas formularias, simetrías mecánicas y cadenas de negaciones.

## Progreso
Trabajo completado. Se eliminó la referencia inexistente a `tab:operationalization`, se reescribió el capítulo con 581 palabras aproximadas y se conservaron HP, H1a--H5b y sus criterios de contraste. La compilación limpia generó el PDF; el capítulo ocupa exactamente dos páginas lógicas, 4--5, y el capítulo 4 comienza en la página 6. La inspección visual no detectó cortes, solapamientos ni encabezados aislados. El estilo general conserva un artefacto previo en los encabezados de determinadas páginas pares y la compilación informa dos referencias indefinidas en Metodología; ambos quedan fuera del archivo revisado y proceden de cambios concurrentes en otros archivos.
