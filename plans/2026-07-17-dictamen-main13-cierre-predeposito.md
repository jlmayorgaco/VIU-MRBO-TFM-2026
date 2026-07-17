# Cierre de predepósito a partir del dictamen de `main(13)`

## Propósito y resultado observable
Corregir las contradicciones científicas y narrativas identificadas en el dictamen, convertir Cargo en un algoritmo reconstruible desde la memoria, restaurar Arial 12 en los anexos y reducir el cuerpo principal hasta un máximo de 80 páginas sin inventar evidencia ni ocultar resultados negativos. El resultado observable será un PDF recompilado, trazable y auditado visualmente.

## Contexto y archivos canónicos
Rigen `docs/00_TFM_CHARTER.md`, `docs/01_VIU_REQUIREMENTS.md`, `docs/02_RESEARCH_MATRIX.md`, `docs/03_EXPERIMENT_PROTOCOL.md`, `docs/04_CLAIMS_EVIDENCE.md`, `docs/05_NOTATION.md` y `docs/07_SP_SECTION_TEMPLATE.md`. La fidelidad visual se contrasta con `docs/06_VIU_TEMPLATE_FIDELITY.md` y `resources/VIU_MROB_TFM_TEMPLATE.docx`. La memoria está en `thesis/`; los resultados y configuraciones existentes son la única fuente de cifras.

## Alcance y no alcance
Incluye H1, la garantía delimitada de SP8, la especificación de Cargo, el nombre de la métrica de intersección, la síntesis de Industrial 2, nomenclatura, terminología SP2, referencias puntuales, tipografía de anexos, poda estructural y trazabilidad. No incluye nuevos experimentos, nuevas citas, nuevos teoremas ni la creación de una etiqueta/release/DOI. Tampoco cambia el título administrativo ni la numeración oficial mientras las fuentes de mayor precedencia registren AMR y numeración arábiga continua.

## Supuestos y preguntas resueltas
- El título se conserva con AMR porque `docs/00_TFM_CHARTER.md` lo declara administrativo vigente; la alegación AGV del dictamen queda registrada como contradicción pendiente de evidencia administrativa o aprobación del director.
- Se conserva la numeración arábiga continua porque la auditoría OOXML de la plantilla oficial la documenta; no se adopta la recomendación romana sin una plantilla posterior verificable.
- El encabezado conserva el diseño extraído del DOCX oficial; añadir el nombre del estudiante exigiría una fuente administrativa superior a la plantilla auditada.
- La release permanece pendiente del autor; el texto no fingirá una instantánea inexistente.

## Diseño matemático/técnico
H1 se descompone en H1a (cuotas realizables), H1b (efecto del cierre QR bajo escasez) y H1c (efecto incremental del cuórum con QR fijo). SP8 separa el juego de perfil coherente de la ejecución con copias obsoletas. Cargo declara entradas, conjunto visible, líder, puntuación, desempates, cierre, abstención, certificado agregado, reapertura, registro y costes por fase. Los anexos conservan las pruebas sustantivas y condensan argumentos finitos rutinarios.

## Plan experimental
No se ejecutan campañas nuevas. Las cifras se verifican contra tablas procesadas, manifiestos y configuraciones existentes. La validación consiste en pruebas de regresión, compilación LaTeX, inspección de logs, recuento de páginas por bloque, auditoría de fuentes y render PNG de páginas críticas.

## Hitos
- [x] Hito 1 — Inventario exacto de pasajes, artefactos y contradicciones del dictamen.
- [x] Hito 2 — H1, SP8, Cargo, métrica de intersección, SP2 y nomenclatura corregidos y trazados.
- [x] Hito 3 — Industrial 2 reducido a una síntesis proporcional a su evidencia piloto.
- [x] Hito 4 — Anexos en Arial 12 y pruebas rutinarias condensadas sin perder supuestos.
- [x] Hito 5 — Cuerpo principal reducido a 80 páginas o menos, manteniendo al menos 50 % en resultados/análisis.
- [x] Hito 6 — Pruebas, bibliografía, compilación, revisión visual y diff final completados.

## Validación
Ejecutar búsquedas de términos contradictorios; comprobar cifras contra datos; ejecutar las pruebas pertinentes y, si el coste lo permite, `python -m pytest -q`; compilar con `thesis/build.ps1`; comprobar citas/referencias indefinidas, cajas `Overfull`, fuentes incrustadas y páginas; renderizar las páginas críticas con Poppler e inspeccionarlas.

## Riesgos y mitigaciones
El principal riesgo es sacrificar trazabilidad para ganar páginas. Se mitiga conservando formulación, supuestos, resultado, incertidumbre y limitación, y trasladando únicamente detalle suplementario ya disponible en el repositorio. Otro riesgo es pisar cambios ajenos: los tres archivos inicialmente modificados se preservan y cualquier solapamiento se revisa antes de editar. La release y el título son acciones administrativas externas y quedan marcadas como bloqueos, no simuladas.

## Registro de decisiones
- 2026-07-17 — Aplicar modo de revisión académica y verificación PDF.
- 2026-07-17 — Rechazar provisionalmente los cambios AGV y numeración romana por contradicción con fuentes canónicas verificadas.
- 2026-07-17 — No crear una release ni modificar afirmaciones de archivo inmutable sin autorización y sin que el artefacto exista.

## Progreso
Se completaron las correcciones científicas y narrativas P0/P1, la especificación de Cargo, la síntesis de Industrial 2 y la restauración de Arial 12. El PDF final tiene 116 páginas: cuerpo 1--80, referencias 81--86 y anexos 87--104. Pasan 74 pruebas, la compilación no presenta referencias/citas indefinidas ni cajas `Overfull`, y la muestra visual cubre todos los bloques críticos. Permanecen fuera de este plan la creación de la release inmutable y la resolución administrativa AGV/AMR.
