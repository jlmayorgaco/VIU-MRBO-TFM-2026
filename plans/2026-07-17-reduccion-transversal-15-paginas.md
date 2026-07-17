# Reducción transversal de 15 páginas de la memoria

## Propósito y resultado observable

Reducir aproximadamente 15 páginas del PDF completo mediante compresión editorial del contenido, sin modificar márgenes, tipografía, interlineado, resultados, ecuaciones, hipótesis, citas verificadas ni limitaciones. El PDF de referencia tiene 139 páginas; el objetivo operativo es 124 ± 1 páginas, con la Introducción numerada desde 1.

## Contexto y archivos canónicos

- Alcance y contribución: `docs/00_TFM_CHARTER.md`.
- Requisitos y presupuesto VIU: `docs/01_VIU_REQUIREMENTS.md`.
- Evidencia SP0--SP8: `docs/02_RESEARCH_MATRIX.md` y `docs/04_CLAIMS_EVIDENCE.md`.
- Protocolo y microestructura: `docs/03_EXPERIMENT_PROTOCOL.md` y `docs/07_SP_SECTION_TEMPLATE.md`.
- Notación: `docs/05_NOTATION.md`.
- Fuente: `thesis/main.tex` y `thesis/sections/**/*.tex`.
- Línea base compilada: `thesis/build/main.pdf`, 139 páginas.

## Alcance y no alcance

Incluye preliminares, capítulos 1--7 y anexos. Se compactarán redundancias, transiciones, enumeraciones narradas y repeticiones entre Resultados y Conclusiones. No se retirarán ecuaciones, resultados cuantitativos, supuestos, intervalos, tamaños muestrales, baselines, ablaciones, citas primarias, tablas o figuras necesarias para sustentar afirmaciones.

## Supuestos y preguntas resueltas

- "Recortar contenido" excluye cambios artificiales de maquetación.
- La reducción cercana al 10 % se distribuye por todo el manuscrito, pero Conclusiones admite una poda mayor porque excede el presupuesto VIU y repite el capítulo 6.
- La bibliografía no se acorta eliminando fuentes citadas; su extensión solo variará si desaparecen citas redundantes junto con texto redundante.
- Las demostraciones se compactan solo estilísticamente; no se omiten pasos lógicos necesarios.

## Diseño matemático/técnico

Presupuesto editorial inicial:

| Bloque | Reducción objetivo | Protección principal |
|---|---:|---|
| Preliminares | 5--8 % | Resumen de 200--300 palabras y cifras canónicas |
| Introducción--Hipótesis | 8--12 % | Preguntas, objetivos, hipótesis y criterios de refutación |
| Metodología y marco teórico | 10--15 % | Diseño experimental, escalas y brecha bibliográfica |
| Resultados SP0--SP8 e integración | 8--10 % | Ecuaciones, evidencia, comparadores, cifras y limitaciones |
| Conclusiones | 25--35 % | Respuestas a objetivos/hipótesis y límites, sin reexplicar métodos |
| Anexos | 5--10 % | Integridad de pruebas y reproducibilidad |

La edición aplicará cinco controles: eliminar lastre verbal; sustituir nominalizaciones por verbos; acortar predicados enterrados; conservar terminología canónica; y verificar que números/citas no cambian.

## Plan experimental

No se reejecutan campañas porque no cambian métodos ni resultados. La validación consiste en compilaciones completas, recuento de páginas, comparación del texto numérico/citas y revisión visual de transiciones críticas.

## Hitos

- [x] Hito 1 — fijar línea base de 139 páginas y localizar el exceso por bloque.
- [x] Hito 2 — compactar todos los capítulos sin alterar evidencia.
- [x] Hito 3 — situar el cuerpo principal dentro del máximo VIU de 80 páginas.
- [x] Hito 4 — revisar diff, referencias, encabezados y render final.

## Validación

- `thesis/build.ps1` debe terminar con código 0.
- `pdfinfo thesis/build/main.pdf` o `pypdf` debe informar 116 páginas totales y 80 de cuerpo principal.
- La Introducción debe conservar el folio 1 arriba a la derecha.
- `git diff --check` debe pasar.
- No deben aparecer referencias indefinidas, citas ausentes ni nuevas advertencias de maquetación material.
- Una muestra visual debe cubrir Introducción, Metodología, SP0, SP3, SP8, Conclusiones y un anexo.

## Riesgos y mitigaciones

- **Pérdida de rigor:** proteger enunciados, supuestos, pruebas, cifras y limitaciones; recortar primero repeticiones.
- **Ahorro de palabras sin ahorro de páginas:** medir tras cada bloque y priorizar páginas con cierres cortos antes de saltos obligatorios.
- **Floats desplazados:** compilar y revisar las transiciones SP, sin eliminar el inicio de cada SP en página nueva.
- **Contradicciones:** contrastar Conclusiones con `docs/04_CLAIMS_EVIDENCE.md`.
- **Cambios ajenos en el árbol:** limitar el diff a los archivos del manuscrito y conservar modificaciones preexistentes.

## Registro de decisiones

- 2026-07-17: mantener formato VIU intacto y reducir solo contenido.
- 2026-07-17: aplicar poda transversal, con mayor intensidad en Conclusiones por su desviación del presupuesto VIU.
- 2026-07-17: no eliminar evidencia ni trasladarla fuera del PDF para simular una reducción.
- 2026-07-17: aceptar 116 páginas totales, en vez de restaurar relleno para llegar a 124, porque el recorte adicional sitúa el cuerpo principal exactamente en el máximo VIU de 80 páginas; referencias y demostraciones permanecen en el PDF.

## Progreso

Trabajo completado. La compilación estable pasó de 139 a 116 páginas: 12 preliminares, 80 de cuerpo principal, 6 de referencias y 18 de anexos. La Introducción conserva el folio arábigo 1 arriba a la derecha; no hay citas ni referencias indefinidas y `git diff --check` no detecta errores de espacios.
