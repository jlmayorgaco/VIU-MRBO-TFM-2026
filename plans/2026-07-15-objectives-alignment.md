# Ajuste de objetivos al esquema canónico

## Propósito y resultado observable

Sustituir el andamiaje provisional del capítulo 2 por objetivos medibles que conserven el estilo del borrador anterior, reflejen la contribución científica deseada y distingan con honestidad la evidencia ya disponible de la que todavía debe consolidarse.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`. Se modifica `thesis/sections/mainmatter/02-objectives.tex`; la notación y la nomenclatura ya incluyen el descuento espacial y la tasa de revisión. El texto anterior aportado por el autor se conserva como referencia de formulación cuando no contradice las fuentes canónicas.

## Alcance y no alcance

Incluye objetivo general, seis objetivos específicos y su alineación con el estado del repositorio. No promueve automáticamente los artefactos numéricos existentes a evidencia canónica, no fija resultados antes de su auditoría y no modifica C1--C7 en la matriz de afirmaciones.

## Supuestos y decisiones resueltas

- Se conserva la capacidad acumulada mediante los vectores canónicos `c_i` y `r_k` y su reducción homogénea `|C_k| >= n_k`.
- La contribución se presenta como una cadena: preferencia poblacional, cierre entero, capacidad, factibilidad mecánica, movimiento seguro y recuperación.
- El modelo físico de trabajo se concreta como carga rígida planar con contactos establecidos, coherente con las campañas SP3--SP5 y el certificado físico disponible.
- `Psi(delta_ik)` y `mu_i(t)` se integran en un único objetivo de diseño estratégico; la modulación espacial deja de constituir por sí sola una contribución principal.
- La implementación se formula como consolidación reproducible porque los reportes y datos existen, pero el código fuente y las pruebas que los generaron aparecen eliminados en el árbol de trabajo actual.
- CoppeliaSim permanece como validación cualitativa posterior y complementaria.

## Evidencia existente auditada

- `results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN/` contiene una campaña cerrada de 2400 filas y una escalera desde preferencia hasta factibilidad mecánica y seguridad, dentro de un modelo reducido.
- `results/theory_validation/` contiene validaciones independientes de asignación de *wrench*, balance dinámico, HOCBF y estabilidad práctica bajo supuestos declarados.
- SP2--SP8 disponen de reportes y artefactos numéricos; SP4 y SP5 separan RAW, SAFE y EXEC y declaran su alcance reducido.
- `results/sp1/SP1_READINESS_REPORT.md` mantiene SP1 bloqueado y sin campaña confirmatoria abierta.
- La evidencia de CoppeliaSim observada es limitada y no respalda todavía una validación completa del transporte.

## Plan experimental

Los objetivos exigen semillas pareadas, oráculos centralizados, baselines distribuidos, ablaciones y métricas de factibilidad, transporte, seguridad, recuperación, red y cómputo. Primero se restablecerá la trazabilidad entre código, configuración, datos y reporte; después se consolidarán las campañas disponibles y se cerrarán SP1 y las comparaciones acoplado/desacoplado pendientes.

## Hitos

- [x] Contrastar el borrador anterior con el alcance y la notación canónicos.
- [x] Auditar los principales reportes existentes de SP0--SP8, certificado físico y teoría.
- [x] Reorientar los seis objetivos hacia la contribución y la evidencia disponibles.
- [x] Compilar, revisar el PDF y auditar advertencias tras el ajuste final.

## Riesgos y mitigaciones

El principal riesgo es confundir campañas históricas con evidencia reproducible actual. Se mitiga condicionando su uso canónico a la recuperación de código, pruebas, configuraciones y procedencia. Otro riesgo es sobredimensionar CoppeliaSim; se mantiene como transferencia cualitativa posterior. Los resultados formales se limitarán a sus supuestos y ninguna simulación se presentará como prueba general de convergencia o estabilidad.

## Registro de decisiones

- 2026-07-15: se conservan seis objetivos específicos para mantener proximidad con el MID y brevedad.
- 2026-07-15: el objetivo aislado sobre `mu_i(t)` se integra en el diseño de *payoffs* y dinámicas.
- 2026-07-15: se añade un objetivo específico dedicado al puente entre coalición lógica y ejecución física.
- 2026-07-15: se priorizan el certificado físico y las validaciones teóricas ya disponibles; SP1 se reconoce como brecha confirmatoria.
- 2026-07-15: los resultados existentes no cambian el estado PENDIENTE de C1--C7 hasta recuperar su trazabilidad reproducible.

## Progreso

Trabajo completado. El capítulo contiene 535 palabras y ocupa exactamente dos páginas. `thesis/build.ps1` genera un PDF A4 de 54 páginas sin referencias indefinidas ni cajas desbordadas o subocupadas. Las páginas de objetivos se renderizaron e inspeccionaron visualmente sin detectar texto recortado, solapamientos ni problemas de jerarquía. No se modificó la matriz de afirmaciones: C1--C7 permanecen en estado PENDIENTE hasta recuperar la trazabilidad reproducible de las campañas.
