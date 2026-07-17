# Auditoría dirigida de MARL para MAPF y transporte cooperativo

## Propósito y resultado observable

Comprobar si el corpus de la Figura 3 y el ledger omiten trabajos MARL relevantes para MAPF, navegación multiagente o transporte cooperativo. El resultado será una lista breve de fuentes primarias verificadas, clasificadas por arquitectura y relevancia para SP3--SP8; no se incorporará ninguna cita al TFM sin verificación adicional.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md`: MARL no puede ser el método principal del TFM, pero sí una familia comparativa.
- `docs/02_RESEARCH_MATRIX.md`: MAPF pertenece sobre todo a SP5/SP7/SP8; transporte físico requiere distinguir SP3/SP4.
- `references/LITERATURE_LEDGER.md`: corpus actual y regla de verificación.
- `references/METHODOLOGICAL_MAP_RUBRIC.md`: escala `dec`, `loc`, `learn` y `exp`.

## Alcance y no alcance

Incluye búsqueda web y arXiv de fuentes primarias en inglés, priorizando 2022--2026 y trabajos con método reproducible, e integración en la Figura 3 de los candidatos verificados. Excluye convertir MARL en contribución nuclear o atribuir transporte físico a trabajos que solo resuelven MAPF.

## Hitos

- [x] Ejecutar búsquedas de arXiv y actas primarias por tres familias: MARL-MAPF, MARL descentralizado y transporte cooperativo aprendido.
- [x] Verificar arquitectura, año, estado de publicación y alcance SP de los candidatos.
- [x] Entregar cribado y recomendación de incorporación sin modificar el ledger.

## Validación

- Cada candidato recomendado debe tener enlace primario y una evidencia explícita de su mecanismo.
- La clasificación debe separar entrenamiento centralizado, ejecución descentralizada y planificación centralizada.

## Riesgos y mitigaciones

- Confundir MARL con control de bajo nivel aprendido: registrar la capa que aprende.
- Confundir MAPF con transporte físico cooperativo: etiquetar el SP y la limitación.
- Inflar el mapa: recomendar solo trabajos que cambien la cobertura conceptual.

## Registro de decisiones

- 2026-07-16: se inicia una búsqueda dirigida tras confirmar que MAPF-LNS2 es white-box; MARL se trata como línea comparativa, no como método principal.
- 2026-07-16: se incorporan PRIMAL, CACTUS, Shibata--LG y TIHDP tras verificar sus fuentes primarias o ediciones publicadas.
- 2026-07-16: la auditoría posterior retiró la señal de título `kappa_ttl`; las palabras del título no alteran la coordenada data-driven y la clasificación depende exclusivamente de la arquitectura acreditada.
- 2026-07-16: la cercanía entre trabajos se cuantifica con `d_met` en el espacio de indicadores, no con la distancia visual entre marcadores TikZ.

## Progreso

Cribado e integración completados: se añadieron cuatro fuentes verificadas a ledger, BibLaTeX, rúbrica y Figura 3. Se identificó una línea consolidada de MARL-MAPF (PRIMAL y CACTUS) y una línea más limitada de transporte cooperativo (Shibata--LG y TIHDP). Se mantienen fuera los preprints recientes y los trabajos híbridos centralizados no verificados con el mismo nivel de detalle.
