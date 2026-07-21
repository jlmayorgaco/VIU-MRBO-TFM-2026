# Revisión mayor de la memoria tras el panel académico

## Propósito y resultado observable

Corregir la desalineación entre objetivos, contribución, arquitectura y evidencia integrada; reducir patrones editoriales mecánicos; consolidar el estado reproducible; y generar un PDF revisado de no más de 120 páginas totales como objetivo operativo indicado por el autor.

## Contexto y archivos canónicos

Se aplican `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, el dictamen `docs/14_FULL_THESIS_RIGOROUS_REVIEW_2026-07-18.md`, los informes de `docs/reviews/2026-07-18/`, el código y los resultados existentes. La versión inicial de esta ronda es `thesis/build/main.pdf`, con 135 páginas.

## Alcance y no alcance

Incluye Resumen/Abstract, Introducción, Objetivos, Hipótesis, Metodología, síntesis de Resultados, Cargo, Conclusiones, anexos de reproducibilidad y documentos de trazabilidad afectados. Incluye compresión editorial selectiva. No añade referencias, métodos, campañas ni resultados no contenidos en el repositorio. No cambia el título oficial.

## Supuestos y preguntas resueltas

El autor fija 120 páginas totales como objetivo operativo. Este criterio no modifica la regla canónica VIU de 50--80 páginas de cuerpo; la discrepancia queda documentada y requiere aprobación administrativa del director. Para no ampliar el alcance experimental, Cargo se reformulará como demostrador híbrido de compatibilidad funcional, no como validación directa de SP2--SP6.

## Diseño matemático/técnico

Se preservan ecuaciones, cifras y clasificación de evidencia. Cada afirmación integrada distinguirá mecanismo formal, proxy ejecutado, información local/por carga/global y resultado respaldado. Las ablaciones se interpretarán como bloque combinado y continuar frente a detenerse. SP2--SP4 se etiquetarán de manera uniforme como reanálisis cuando no exista regeneración completa.

## Plan experimental

No se ejecutan campañas nuevas. Se recompila la memoria, se ejecuta la suite completa, se verifican claves citadas, referencias cruzadas, advertencias LaTeX, conteo de páginas y renderizado visual de páginas modificadas.

## Hitos

- [ ] Corregir OE5, HP/RQ y definición de la contribución.
- [ ] Corregir Cargo, arquitectura distribuida/híbrida y causalidad de ablaciones.
- [ ] Unificar reproducibilidad y fuerza confirmatoria de SP1/SP4.
- [ ] Comprimir estructura y prosa hasta un máximo operativo de 120 páginas totales.
- [ ] Auditar y corregir patrones P0/P1/P2 de escritura artificial sin alterar contenido.
- [ ] Compilar, ejecutar pruebas, revisar PDF y actualizar trazabilidad/revisión.

## Validación

`thesis/build.ps1`; `python -m pytest -q` con `PYTHONPATH=src`; comprobación de referencias/citas indefinidas, caracteres ausentes, cajas desbordadas y metadatos; extracción del índice de páginas; renderizado de páginas críticas con Poppler.

## Riesgos y mitigaciones

La compresión puede eliminar evidencia: se priorizan duplicaciones tabla--figura--prosa y material secundario. La reformulación puede quedar desincronizada: se actualizan objetivos, hipótesis, metodología, resultados, conclusiones y matriz de evidencia en una misma ronda. El objetivo de 120 páginas puede seguir contradiciendo VIU: se registra como desviación administrativa, no como cumplimiento.

## Registro de decisiones

- 2026-07-18: revisión en modo `revision` con aislamiento de conocimiento y APA 7 existente.
- 2026-07-18: Cargo se conserva como demostrador híbrido; no se simula una integración SP2/SP3/SP6 inexistente.
- 2026-07-18: el título oficial permanece sin cambios.
- 2026-07-18: objetivo operativo de salida fijado por el autor en 120 páginas totales; la regla VIU canónica no se modifica.

## Progreso

Fuentes canónicas, contrato SP y reglas de revisión editorial cargados. `AUDIT.md` se adopta como inventario completo de reparación: no contiene hallazgos P0 y concentra los cambios en P1/P2, simetría estructural, metadiscurso, inventarios y cautelas repetidas. La primera tarea activa es cruzar cada marca con la versión actual de las fuentes, porque las líneas cambiaron después del corte de auditoría. Después se editarán preliminares/capítulos/anexos, se repetirá el barrido anti-IA y se cerrará con pruebas, compilación y revisión visual.
