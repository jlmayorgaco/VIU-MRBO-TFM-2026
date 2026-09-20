# Revisión sistematizada V3 — síntesis visual de cuatro páginas

## Objetivo

Convertir el manuscrito V3 y sus derivados reproducibles en un informe autónomo
de máximo cuatro páginas, conservando la identidad visual de la plantilla
facilitada por el autor y sustituyendo sus conteos, figuras y narrativa por los
resultados auditados del corpus V3.

## Decisiones editoriales

- El documento se presenta como **revisión sistematizada de mapeo y síntesis
  crítica**, no como revisión sistemática exhaustiva ni meta-análisis.
- Los conteos temáticos, metodológicos y de validación proceden exclusivamente
  de los CSV V3 y se etiquetan como señales multietiqueta de título/resumen.
- La lectura cercana respalda solo afirmaciones localizadas en las 20 fichas de
  evidencia. Los restantes documentos se usan para mapeo descriptivo.
- La contribución narrativa se concentra en tres resultados: evolución del rol
  de los métodos, discontinuidad SP1--SP2--SP3 y cadena de certificados para el
  diseño del TFM.
- La cobertura incompleta de WoS y arXiv se mantiene visible como limitación.

## Entregables y comprobaciones

- [x] Script reproducible de figuras y macros numéricas.
- [x] Fuente LaTeX de cuatro páginas con referencias verificadas.
- [x] PDF compilado en `output/pdf/`.
- [x] Comprobación de página, referencias y desbordamientos LaTeX.
- [x] Render de todas las páginas e inspección visual.
- [x] Pruebas de consistencia del paquete V3.

## Cierre

**Estado:** completado el 2026-09-14.

El PDF final contiene cuatro páginas letter, tres figuras derivadas de datos,
un diagrama conceptual TikZ, una tabla de fronteras cuantitativas localizadas,
agenda experimental, amenazas a la validez, declaraciones y 20 referencias.
XeLaTeX no reportó cajas desbordadas, referencias indefinidas ni caracteres
ausentes. La suite `academic-review/tests` finalizó con 63 pruebas aprobadas.

