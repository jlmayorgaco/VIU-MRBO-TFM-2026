# Normalización computacional de las tablas de métodos SP0--SP8

## Propósito y resultado observable

Revisar las tablas metodológicas de SP0--SP8 para que cada fila identifique una fuente representativa verificada, la clase del problema, el coste asintótico pertinente, la arquitectura de información, los parámetros principales y la garantía o limitación. El PDF debe compilar sin desbordamientos críticos y las afirmaciones de complejidad deben distinguir problema, algoritmo e implementación.

## Contexto y archivos canónicos

Se aplican `docs/00_TFM_CHARTER.md`, `docs/01_VIU_REQUIREMENTS.md`, `docs/02_RESEARCH_MATRIX.md`, `docs/03_EXPERIMENT_PROTOCOL.md`, `docs/04_CLAIMS_EVIDENCE.md`, `docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, `references/LITERATURE_LEDGER.md`, las implementaciones reproducibles de SP0--SP3 y las secciones `sp0.tex`--`sp8.tex`.

## Alcance y no alcance

Incluye las tablas de comparación metodológica y su convención común. No cambia algoritmos, resultados experimentales, alcance administrativo ni eleva SP4--SP8 por encima de su evidencia prevista.

## Supuestos y preguntas resueltas

- P, NP y NP-difícil califican al problema de decisión/optimización, no a una heurística.
- Para una iteración o actualización local se reporta coste por evento y el multiplicador de iteraciones cuando exista.
- Si la implementación aún no existe o la fuente no ofrece una cota transferible, se declara “no determinada” y se da únicamente el coste del subproblema identificable.
- Los parámetros son los que modifican el comportamiento o el coste; no se listan constantes cosméticas.

## Diseño matemático/técnico

Cada tabla prioriza seis campos: método/fuente, clase, coste, arquitectura/información, parámetros y garantía/límite. Se definen localmente los símbolos auxiliares de complejidad. Los costes de solver se expresan como exponenciales en peor caso para MILP o como coste de QP por iteración cuando no existe un exponente universal independiente del solver.

## Plan experimental

No se generan nuevos resultados. La validación consiste en contrastar tablas con código/configuración, verificar claves bibliográficas y compilar/renderizar la memoria.

## Hitos

- [x] Inventario de las nueve tablas y de sus referencias.
- [x] Convención común y tablas SP0--SP3 actualizadas con costes ejecutados.
- [x] Tablas SP4--SP8 actualizadas sin presentar propuestas pendientes como implementadas.
- [x] Compilación, inspección de avisos y revisión visual.

## Validación

- Buscar claves citadas en `thesis/references.bib` y estado VERIFICADA en el ledger.
- Ejecutar las pruebas de evidencia y compilación LaTeX pertinentes.
- Revisar el log por `Overfull`, referencias indefinidas y errores.
- Renderizar las páginas de tablas para comprobar legibilidad.

## Riesgos y mitigaciones

- **Sobreafirmar NP-dureza:** usar solo reducciones ya documentadas o fuentes primarias; en otro caso declarar clase no establecida.
- **Confundir coste por paso y total:** mostrar el número de pasos/eventos como factor explícito.
- **Tablas ilegibles:** usar texto compacto, símbolos definidos y conservar el análisis crítico fuera de las celdas.
- **Cotas no reproducibles en SP2--SP3 heredados:** etiquetar el coste como estructural y registrar la ausencia del generador cuando corresponda.

## Registro de decisiones

- 2026-07-16: se revisan SP0--SP8 porque “tablas SPx” se interpreta como la escalera completa.
- 2026-07-16: las filas de SP4--SP8 conservarán su carácter de método previsto o referencia conceptual.
- 2026-07-16: el reporte histórico de SP3 afirma NP-dureza de la selección entera, pero no se localizó una reducción en la memoria ni una fuente que clasifique exactamente esa formulación; la tabla la deja como no demostrada y solo informa su enumeración exponencial.

## Progreso

Se normalizaron las nueve tablas y la plantilla SP. Las 47 claves citadas en SP0--SP8 existen en `thesis/references.bib` y figuran como VERIFICADA en el ledger. Las cuatro suites pertinentes suman 23 pruebas superadas. LuaLaTeX/Biber generó un PDF de 117 páginas sin errores, citas o referencias indefinidas; la revisión visual confirmó que las tablas no se recortan ni se solapan. Los dos `Overfull` restantes pertenecen a una tabla previa de Metodología y quedan fuera del alcance de este plan.
