# Revisión editorial de SP1.N1

## Objetivo

Revisar la prosa del documento activo de diez páginas `thesis/sp1_levels_23p/main.tex` para que la lectura sea fluida, académica y específica, sin patrones reconocibles de escritura automática. Se conservarán sin cambios las cifras, ecuaciones, figuras, hipótesis y límites de evidencia.

## Riesgos y controles

- **Deriva científica:** contrastar cada reformulación con `docs/00_TFM_CHARTER.md`, `docs/03_EXPERIMENT_PROTOCOL.md`, `docs/04_CLAIMS_EVIDENCE.md` y `docs/05_NOTATION.md`.
- **Cambio de paginación:** compilar tras la revisión y exigir diez páginas.
- **Pérdida de trazabilidad:** mantener las macros que enlazan los resultados con los datos generados.
- **Prosa mecánica:** eliminar aperturas repetidas, transiciones formularias, recapitulaciones redundantes y conclusiones genéricas.

## Secuencia de trabajo

1. Auditar la prosa visible y los textos de apoyo de las diez páginas.
2. Reescribir por función narrativa: planteamiento, evidencia, interpretación y límite.
3. Realizar un segundo pase de ritmo, terminología y precisión.
4. Compilar, ejecutar las pruebas pertinentes e inspeccionar visualmente las diez páginas.

## Criterio de cierre

- PDF de diez páginas sin desbordamientos ni cambios en resultados.
- Prosa específica, con variación sintáctica y transiciones causales explícitas.
- Todas las pruebas de SP1.N1 y figuras protegidas superadas.

## Verificación realizada

- Segunda auditoría sin muletillas ni aperturas formularias detectadas en el texto visible.
- Compilación reproducible: `output/pdf/sp1_n1_10p/SP1_N1_10P.pdf`, 10 páginas.
- Inspección visual de las páginas 1--10: sin solapamientos, desbordamientos ni figuras desplazadas.
- Pruebas: 20 superadas (`test_sp1_levels`, `test_sp1_a1_hungarian` y `test_protected_tikz_figures`).
- Registro de LaTeX: sin avisos `Overfull`, `Underfull` ni advertencias de compilación.
