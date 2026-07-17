# SP3: certificado mecánico y juego de wrench

## Propósito y resultado observable

Completar `sp3.tex` con la microestructura canónica del capítulo 6: pregunta local, diagrama, certificado de optimización, tabla crítica de literatura, juego continuo, cierre mecánico, problema de control, protocolo, resultados y transición. Los valores cuantitativos deberán regenerarse desde la campaña `SP3_WRENCH_NASH_GAME_v1_1` mediante un postproceso versionado.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` fija Cargo como modo primario y empuje/caging como extensión.
- `docs/02_RESEARCH_MATRIX.md` exige evidencia B para SP3-C y C para SP3-E.
- `docs/03_EXPERIMENT_PROTOCOL.md` exige escenarios pareados, falsos positivos mecánicos, residual de wrench, incertidumbre y fallos.
- `docs/04_CLAIMS_EVIDENCE.md` mantiene C3-C y C3-E pendientes al inicio de este plan.
- `docs/05_NOTATION.md` fija pose, matriz de agarre, fuerzas admisibles, conjunto de wrench, formación y caging.
- `docs/07_SP_SECTION_TEMPLATE.md` fija la secuencia y la obligación de separar juego y control.
- `results/sp3/SP3_WRENCH_NASH_GAME_v1_1/` contiene 600 mundos, 7200 ejecuciones y una auditoría formal aprobada de la relajación planar.

## Alcance y no alcance

Se redacta y audita el certificado planar cuasiestático de slots y wrench, el juego continuo con precios de congestión, el cierre entero guardado y la interfaz de control de formación de Cargo. Se informa la rama de empuje/caging como extensión pendiente. No se atribuye a la campaña estabilidad de transporte, contacto tridimensional, caging, optimalidad del cierre entero ni distribución completa de la guardia mecánica.

## Supuestos y preguntas resueltas

- La campaña histórica usa columnas de wrench normalizadas, contactos unidireccionales acotados y demanda planar conocida.
- La matriz de geometría y los límites permanecen fijos durante cada decisión del juego.
- La agregación exacta y la variante de anillo son condiciones experimentales distintas; cuatro rondas de consenso no heredan el resultado de información exacta.
- El problema de control se formula para una carga estacionaria en SP3; el seguimiento origen--destino se reserva para SP4.

## Diseño matemático/técnico

El certificado de una coalición minimiza el residual normalizado de wrench con esfuerzos acotados. La relajación usa preferencias por robot sobre inactividad y pares carga--slot, restricciones simplex y ocupación de slot. Su potencial es el negativo del error cuadrático de wrench, el coste y una regularización cuadrática. El payoff es su gradiente menos el precio dual del slot. La salida continua se cierra en una asignación única y una guardia elimina cargas cuyo residual excede la tolerancia.

El control separa aproximación a slots, activación de contacto y reparto de esfuerzos. En Cargo se define error de formación respecto al marco de la carga, saturación cinemática y un QP de wrench; el transporte de pose no se activa todavía. La rama E requiere unilateralidad y un certificado geométrico adicional antes de usar el término caging.

## Plan experimental

Auditar 600 mundos pareados de seis generadores y doce métodos. Comparar oráculo de wrench, referencia escalar, CBBA por slots, greedy, cuatro protocolos poblacionales/precios, cierre guardado y no guardado. Reportar precisión, falsos positivos, gap frente al oráculo de wrench, residual KKT, CPU, mensajes y los cuatro contrastes preespecificados con corrección de Holm.

## Hitos

- [x] Hito 1 — postproceso reproduce tabla y macros de la campaña sin valores manuales.
- [x] Hito 2 — `sp3.tex` contiene los nueve bloques canónicos y distingue Cargo de empuje/caging.
- [x] Hito 3 — demostración de potencial/KKT y trazabilidad de claims/notación sincronizadas.
- [x] Hito 4 — pruebas del postproceso y compilación LaTeX aprobadas.

## Validación

- `python -m viu_mrob_tfm.cli.run_sp3_evidence --config experiments/configs/sp3_wrench_evidence.yaml`
- `python -m pytest tests/test_sp3_evidence.py -q`
- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`
- Revisión de referencias, etiquetas, rutas de figuras y diff limitado al alcance.

## Riesgos y mitigaciones

- El generador histórico de la campaña no está en el árbol de trabajo actual: se declarará que el postproceso es reproducible, pero la simulación completa requiere restaurar el generador.
- La guardia usa el oráculo planar y no es plenamente distribuida: se presentará como cierre certificado, no como prueba de arquitectura local completa.
- La campaña no mide rigidez ni formación Cargo tridimensional: C3-C solo puede avanzar a evidencia parcial.
- La rama E no contiene certificado de caging ni seguimiento de pose: C3-E permanecerá pendiente.

## Registro de decisiones

- 2026-07-16 — Se adopta `SP3_WRENCH_NASH_GAME_v1_1` como evidencia principal porque corrige el fallo KKT de v1, conserva semillas nuevas y documenta explícitamente sus no-afirmaciones.
- 2026-07-16 — Se separa el resultado formal de la relajación convexa del cierre entero y de la planta física.
- 2026-07-16 — Los métodos nuevos se nombran por mecanismo: juego potencial de wrench con precios, mercado de soporte residual, cierre pareado y guardia mecánica.

## Progreso

Trabajo completado. El postproceso auditó 600 mundos y 7200 ejecuciones, generó tabla y macros LaTeX, y pasó su prueba automatizada. `sp3.tex` contiene optimización, literatura, juego, cuatro métodos propios, control, protocolo, resultados y transición; el Anexo E contiene la prueba de potencial/KKT. La matriz de claims clasifica C3-C como parcial, sustenta C3A--C3D y mantiene C3-E pendiente. La batería SP0--SP3 terminó con 23 pruebas aprobadas y la tesis compiló en 113 páginas. La revisión visual de las páginas 64--71 y 113 no encontró recortes ni solapamientos.

Permanece una limitación reproducible: el postproceso puede repetirse desde los CSV, pero el generador histórico de la campaña SP3 no está en el árbol de trabajo actual. Tampoco se han ejecutado rigidez Cargo, soporte vertical, caging ni seguimiento de pose; esos elementos pasan a SP4 o a una campaña física posterior.
