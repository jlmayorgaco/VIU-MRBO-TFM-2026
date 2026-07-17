# Auditoría submit-ready de SP0--SP3

## Propósito y resultado observable

Cerrar SP0--SP3 como microcapítulos enviables: estructura canónica completa, contribuciones propias delimitadas, resultados formales con pruebas en anexos, claims alineados con la evidencia, comparaciones reproducibles y PDF sin defectos de composición.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md` a `docs/07_SP_SECTION_TEMPLATE.md`, la trazabilidad de `docs/04_CLAIMS_EVIDENCE.md`, los cuatro archivos `sp0.tex`--`sp3.tex`, sus anexos de pruebas y los artefactos versionados en `results/`.

## Alcance y no alcance

Incluye auditoría y corrección editorial, matemática y de trazabilidad de SP0--SP3; compilación, pruebas y revisión visual. No incluye ejecutar campañas científicas nuevas ni elevar a demostradas capacidades que permanecen pendientes, refutadas o fuera del modelo de cada SP.

## Supuestos y preguntas resueltas

“Submit-ready” significa que el texto es correcto respecto de la evidencia disponible. Una limitación explícita no bloquea el envío si el claim correspondiente se reduce al nivel realmente acreditado. Los resultados negativos se conservan.

## Diseño matemático/técnico

La auditoría verifica por SP: oráculo y complejidad; juego, potencial y equilibrio; cotas y límites; problema de control o delimitación; protocolo, baselines y métricas; correspondencia cuerpo--anexo--código--datos. Se aplicará la cadena `OBSERVADO -> ESTIMADO -> CRUDO -> CERRADO -> PROTEGIDO -> EJECUTADO` cuando exista interacción física.

## Plan experimental

No se añaden campañas. Se revalidan las pruebas unitarias existentes, la integridad de los artefactos citados, las referencias cruzadas y la compilación completa. Los métodos centrales se tratan como oráculos cuando disponen de información global.

## Hitos

- [x] Auditoría estructural y científica de SP0--SP3 terminada.
- [x] Claims, tablas, control y limitaciones corregidos.
- [x] Pruebas, compilación y revisión visual aprobadas.
- [x] Dictamen final y límites residuales registrados.

## Validación

`python -m pytest tests/test_sp0_theory.py tests/test_sp1_theory.py tests/test_sp2_effective_capacity.py tests/test_sp3_evidence.py -q`; `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`; búsqueda de referencias/citas indefinidas y renderizado de las páginas modificadas.

## Riesgos y mitigaciones

El riesgo principal es sobreafirmar distribución, optimalidad o control físico. Se mitiga distinguiendo teorema, evidencia empírica y trabajo pendiente. No se sustituye evidencia faltante con redacción.

## Registro de decisiones

- 2026-07-16: se adopta una revisión de dos rondas; la segunda sólo verifica issues mayores y regresiones.
- 2026-07-16: los resultados refutados de SP1 y SP2 permanecen visibles como resultados negativos.

## Progreso

Cierre completado. Se corrigió la separación entre el QP regularizado y el residual certificado de SP3, se explicitó el estado informacional de cada SP, se aclararon roles/paradigmas y signos de los contrastes, y se añadió la caja de mecanismos propios de SP3. Los postprocesos SP2/SP3 regeneraron sus artefactos, 23 pruebas pasaron y el PDF final de 126 páginas fue validado e inspeccionado. El dictamen detallado está en `docs/09_SP0_SP3_SUBMIT_READY_AUDIT.md`. Permanecen como limitaciones declaradas la ausencia de los generadores históricos completos de SP2/SP3 en el árbol actual y la falta de acreditación de la arquitectura distribuida/planta completa.
