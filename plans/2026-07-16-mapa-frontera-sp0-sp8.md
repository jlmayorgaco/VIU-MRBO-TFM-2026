# Dos mapas visuales de la literatura y la frontera metodológica

## Propósito y resultado observable

Añadir al capítulo 5 dos figuras TikZ de media página: una línea temporal de trabajos ancla sobre robótica móvil cooperativa, asignación, coaliciones, transporte, seguridad y red; y un plano cartesiano cualitativo que ubique los trabajos ancla entre coordinación distribuida/centralizada y formulaciones white-box/data-driven.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md`: contribución nuclear y alcance priorizado.
- `docs/02_RESEARCH_MATRIX.md`: incremento, método y nivel objetivo por SP.
- `docs/04_CLAIMS_EVIDENCE.md`: estado actual de la evidencia y afirmación C8.
- `docs/05_NOTATION.md`: símbolos canónicos usados en la figura.
- `references/LITERATURE_LEDGER.md`: autores y resultados verificados.
- `thesis/sections/mainmatter/05-theoretical-framework.tex`: destino de la figura.

## Alcance y no alcance

Se incorpora una síntesis conceptual de revisión, no una figura cuantitativa ni una afirmación de prioridad universal. No se modifica la formulación de los SP, sus niveles de evidencia ni el alcance administrativo del TFM.

## Supuestos y preguntas resueltas

- Las figuras se ubican en `Síntesis crítica y brecha`, después de la tabla comparativa.
- La línea temporal representa hitos de trabajos ancla, no prioridad universal ni una historia exhaustiva.
- El plano cartesiano usa coordenadas cualitativas: $x=-1$ distribuido/descentralizado, $x=1$ centralizado; $y=-1$ white-box, $y=1$ data-driven.
- El registro exhaustivo permanece en `references/LITERATURE_LEDGER.md`; las figuras usan etiquetas abreviadas para conservar legibilidad.

## Diseño matemático/técnico

La composición separa historia intelectual y clasificación metodológica. Las etiquetas se limitan a trabajos verificados del ledger y se codifican como nombres abreviados; no se asignan números de rendimiento ni se interpreta la posición como calidad.

## Plan experimental

No aplica: la figura sintetiza revisión y trazabilidad. Su verificación será compilación LaTeX y revisión visual de la página renderizada.

## Hitos

- [x] Insertar narrativa, dos figuras TikZ, pies y etiquetas.
- [x] Compilar sin errores ni referencias rotas.
- [x] Verificar en PNG que el texto sea legible y no existan solapes.
- [x] Revisar el diff y confirmar que no se alteran cambios ajenos.

## Validación

- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`
- Render de la página afectada con Poppler.
- Inspección de avisos LaTeX y revisión visual al 100 %.

## Riesgos y mitigaciones

- Densidad excesiva: usar frases nominales breves y separar la explicación detallada en el párrafo previo.
- Sobreafirmación bibliográfica: citar solo fuentes `VERIFICADA` y mantener la limitación al corpus auditado.
- Confusión entre literatura y avance propio: usar bandas, colores y leyenda independientes.
- Desactualización del estado: fechar el estado de evidencia en el texto de la figura.

## Registro de decisiones

- 2026-07-16: se elige un mapa cartesiano de frontera, no una cronología, porque SP0--SP8 representan una escalera de capacidades y no años.
- 2026-07-16: la figura complementa, no sustituye, la tabla comparativa del capítulo 5.

## Progreso

Se auditaron los documentos canónicos, la sección de destino, la notación y las fuentes verificadas. Se sustituyó el mapa único por una línea temporal y un plano cartesiano metodológico, ambos en la síntesis crítica del capítulo 5. La revisión visual de la página 41 confirma que los ejes, fases y etiquetas principales son legibles. La compilación LuaLaTeX--Biber terminó correctamente; se mantienen únicamente avisos tipográficos preexistentes. Las figuras son una selección de trabajos ancla: la lista completa sigue trazada en el ledger para evitar saturar media página con 80 etiquetas.
