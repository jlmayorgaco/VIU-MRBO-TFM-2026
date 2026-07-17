# Cierre científico y editorial de la memoria tras la revisión externa

## Propósito y resultado observable

Actualizar la memoria para que presente resultados ya existentes en lugar de estados de planificación, jerarquice SP0--SP8 según su peso científico y cierre la discusión y las conclusiones con afirmaciones trazables. La revisión eliminará lenguaje de pipeline del cuerpo cuando no sea necesario para definir una interfaz científica, sin ocultar resultados negativos ni rebajar los supuestos de los teoremas.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md` y `docs/07_SP_SECTION_TEMPLATE.md`. La petición adjunta recomienda compactar la escalera SP0--SP8 y centrar la narrativa en SP3, SP4, SP6 y SP8. Desde la auditoría de `docs/11_FULL_MANUSCRIPT_REVIEW.md` se ejecutaron SP7 y SP8; por tanto, sus diagnósticos prospectivos deben contrastarse con los artefactos actuales antes de reescribir.

## Alcance y no alcance

Incluye el capítulo 6, las conclusiones, el resumen/abstract cuando sus tiempos verbales o afirmaciones queden desactualizados, la matriz de evidencia y la notación afectada. Incluye compactación semántica y sustitución de metadiscurso. No inventa resultados, no añade referencias sin verificar y no cambia el título administrativo. La microestructura obligatoria de cada SP se conserva, aunque el marco común se concentra en `index.tex`.

## Supuestos y preguntas resueltas

- Los resultados SP7 y SP8 presentes en `results/processed/` sustituyen los estados prospectivos de la auditoría del 16 de julio.
- La cadena de etapas se explica una vez en la arquitectura; dentro de cada SP se usan términos académicos en español y solo se conservan etiquetas de etapa cuando distinguen magnitudes formalmente diferentes.
- SP8 acredita una red abstracta de intercambio de rutas, no consenso dinámico de los agregados de SP0--SP6 ni transporte físico extremo a extremo.
- La hipótesis principal se evalúa por componentes; no se declara verificada como sistema integrado mientras falte la composición completa.

## Diseño matemático/técnico

La discusión transversal se organiza por seis fronteras: equilibrio/eficiencia, relajación/cierre entero, capacidad/factibilidad mecánica, equilibrio/estabilidad, seguridad/vivacidad e información local/calidad global. SP8 incorporará el juego de potencial visible sobre el grafo, el resultado de indistinguibilidad por partición y la evidencia cuantitativa de red. Las conclusiones distinguirán resultados demostrados, observaciones empíricas, resultados refutados y límites abiertos.

## Plan experimental

No se genera evidencia nueva salvo que una comprobación de humo revele un artefacto ausente. Se reutilizan las configuraciones y resultados versionados de SP0--SP8. La validación comprende pruebas unitarias, auditoría de cifras citadas contra CSV/JSON, compilación de la memoria y revisión del texto extraído y de las páginas modificadas.

## Hitos

- [x] Auditar el estado actual y extraer cifras verificables de SP7/SP8 y del resto de afirmaciones centrales.
- [x] Sustituir SP8 prospectivo por teoría, experimento, resultados y límites actuales; sincronizar evidencia y notación.
- [x] Reescribir la discusión transversal y el capítulo 7 con respuestas reales a RQ1--RQ5 e H1--H5.
- [x] Eliminar metadiscurso y lenguaje interno prioritario del cuerpo sin borrar distinciones científicas.
- [x] Actualizar resumen/abstract y coherencia de tiempos verbales.
- [x] Ejecutar pruebas, compilar, revisar el PDF y auditar el diff.

## Validación

- `python -m pytest tests/test_sp0_theory.py tests/test_sp1_theory.py tests/test_sp2_effective_capacity.py tests/test_sp3_evidence.py tests/test_sp4_theory_and_evidence.py tests/test_sp5_evidence.py tests/test_sp5_payload_transport.py tests/test_sp6_recovery.py tests/test_sp7_traffic.py tests/test_sp8_network.py tests/test_literature_coverage.py`
- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`
- Contrastar toda cifra añadida con `results/processed/*/tables/` o `docs/04_CLAIMS_EVIDENCE.md`.
- Buscar futuro prospectivo, rutas internas y vocabulario de pipeline en el cuerpo.

## Riesgos y mitigaciones

- El árbol de trabajo contiene muchos cambios del autor: se tocarán solo archivos de memoria, trazabilidad y este plan.
- La revisión externa propone eliminar bloques que la plantilla canónica exige: se conservará el contrato y se compactará dentro de él.
- SP8 puede parecer cerrar toda la distribución: el texto limitará el resultado al juego de rutas y separará esa evidencia de la planta física.
- La compactación puede romper referencias LaTeX: la compilación y la inspección del log son obligatorias.

## Registro de decisiones

- 2026-07-17: conservar SP0--SP8 y asignarles profundidad desigual.
- 2026-07-17: aplicar la recomendación editorial sin contradecir `docs/07_SP_SECTION_TEMPLATE.md`.
- 2026-07-17: tratar la auditoría del 16 de julio como diagnóstico histórico, no como estado vigente de SP7/SP8.

## Progreso

Pase cerrado el 2026-07-17. SP8, la discusión transversal, las conclusiones y los resúmenes reflejan los resultados vigentes; la notación y la matriz de evidencia están sincronizadas. La suite completa termina con 60 pruebas superadas y la memoria compila en `thesis/build/main.pdf` (155 páginas). Se revisaron visualmente las páginas 110--120. Permanecen como riesgos externos a este pase la falta de integración extremo a extremo y el exceso de extensión respecto del intervalo VIU, que el encargo actual pidió no resolver por recorte de páginas.
