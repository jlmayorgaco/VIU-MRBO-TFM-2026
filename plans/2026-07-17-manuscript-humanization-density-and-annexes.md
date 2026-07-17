# Cierre editorial, densidad y anexos de la memoria

## Propósito y resultado observable

Dejar la memoria lista para lectura académica: prosa directa, sin patrones de generación automática, metadiscurso ni repeticiones; terminología estable; citas usadas solo donde respaldan una afirmación; diagramas legibles y funcionales; y material auxiliar fuera del cuerpo principal. El resultado observable será un PDF recompilado, más corto y denso, con las mismas afirmaciones científicas y trazabilidad.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, el código y los resultados actuales. La estructura VIU y los nueve bloques de cada SP se conservan. Las demostraciones completas, tablas panorámicas, detalles de reproducibilidad y desarrollos secundarios pueden pasar a anexos; el cuerpo debe retener problema, método, resultado, evidencia y límite.

## Alcance y no alcance

Incluye preliminares, capítulos 1--7, diagramas TikZ, tablas narrativas, cajas de contribución, pies de figura, anexos y estilo LaTeX. Incluye eliminación de jerga interna, frases formularias, aperturas repetidas, voz pasiva innecesaria, listas simétricas, citas duplicadas y explicaciones que repiten tablas o ecuaciones. No modifica resultados, datos, fórmulas demostradas, nivel de evidencia, título administrativo ni estructura superior VIU.

## Supuestos y preguntas resueltas

- El perfil editorial es una memoria técnica, no un texto promocional; se admite lenguaje cauteloso cuando expresa una limitación real.
- Los términos `robustez`, `dinámica`, `distribuido` y `potencial` se conservan cuando tienen significado matemático.
- Una referencia repetida se elimina solo si otra cita cercana respalda la misma afirmación; no se sacrifica atribución por densidad.
- Los diagramas deben explicar una relación que el texto no comunica con igual rapidez. Los elementos decorativos se eliminan.
- Las cajas naranjas se reservan para resultados propios centrales; los desarrollos secundarios se resumen y remiten a anexos.

## Diseño matemático/técnico

El pase se ejecuta en cuatro capas: auditoría léxica y estructural; reescritura por capítulo; compactación y traslado a anexos; y revisión visual. La notación matemática permanece canónica. Toda fórmula movida conserva etiqueta o recibe una nueva sin romper referencias. Los diagramas usan una jerarquía común: estado de entrada, decisión, restricción nueva y salida acreditada.

## Plan experimental

No se generan experimentos nuevos. Las cifras se contrastan con las macros y tablas procesadas actuales. La validación incluye suite completa de pruebas, compilación LaTeX, búsqueda de referencias indefinidas, comparación del número de páginas, extracción de texto y revisión visual de páginas con diagramas, tablas o saltos nuevos.

## Hitos

- [x] Auditar patrones de escritura, redundancias, citas y densidad por archivo.
- [x] Limpiar preliminares y capítulos 1--5.
- [x] Compactar SP0--SP8 y la discusión sin alterar evidencia.
- [x] Reducir cajas, referencias y metadiscurso repetidos; trasladar o retirar material auxiliar.
- [x] Mejorar los diagramas conceptuales y su coherencia visual.
- [x] Limpiar conclusiones y anexos, ejecutar una segunda auditoría de estilo.
- [x] Probar, compilar, inspeccionar el PDF y registrar limitaciones restantes.

## Validación

- `python -m pytest tests`
- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`
- Búsqueda de patrones formularios P0/P1, dobles guiones narrativos, metadiscurso, rutas internas y citas repetidas.
- Inspección del log: sin errores LaTeX, referencias o citas indefinidas.
- Renderizado y revisión visual de todas las páginas modificadas con diagramas y tablas.

## Riesgos y mitigaciones

- La compactación puede borrar un supuesto: cada párrafo reescrito se compara con su formulación y evidencia.
- Una cita aparentemente repetida puede ser la única atribución primaria: se conserva cuando cambia la afirmación respaldada.
- Mover material puede romper etiquetas: la compilación completa es obligatoria tras cada bloque grande.
- La reducción de cajas puede contradecir la plantilla: se conserva al menos el resultado propio central de cada SP y se remite a la demostración correspondiente.
- El árbol contiene cambios del autor: se editan solo fuentes de memoria, anexos, trazabilidad y este plan.

## Registro de decisiones

- 2026-07-17: usar un perfil de memoria científica y cinco pases sucesivos de revisión de escritura.
- 2026-07-17: priorizar densidad argumental sobre simetría entre SP.
- 2026-07-17: mantener en el cuerpo la tabla crítica obligatoria de cada SP y trasladar solo detalle suplementario.

## Progreso

Cierre completado. El PDF pasa de 155 a 114 páginas: 79 páginas de cuerpo (páginas 12--90), seis de referencias y 18 de anexos. La cronología bibliográfica, el mapa metodológico y sus textos de validación se retiraron por duplicar el ledger y no aportar evidencia directa. La discusión transversal y los contrastes repetidos se integraron en prosa; el anexo SP0 se redujo a las pruebas citadas. La búsqueda final no encuentra metadiscurso, jerga de proceso ni patrones P0/P1 seleccionados. Las 60 pruebas pasan y la compilación no contiene referencias o citas indefinidas. Permanecen avisos de sustitución de fuentes matemáticas, sin pérdida visible en las páginas inspeccionadas.
