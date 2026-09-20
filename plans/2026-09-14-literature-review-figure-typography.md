# Auditoría tipográfica de las figuras del estado del arte

**Estado:** completado.

## Objetivo

Unificar la tipografía interna de las Figuras 1--8 del PDF compacto. Los
gráficos, diagramas, ejes, rótulos y valores usarán Noto Sans. Noto Serif se
mantiene únicamente en la prosa, los pies de figura y las líneas de fuente para
conservar la jerarquía editorial del documento.

## Cambios

- [x] Regenerar las tres páginas heredadas desde una fuente LaTeX editable.
- [x] Evitar que los nodos TikZ en negrita pierdan la familia sans serif.
- [x] Aplicar Noto Sans a la matriz de la Figura 2 y a ambos paneles de la
  Figura 3.
- [x] Sustituir DejaVu Sans por Noto Sans en las figuras Matplotlib heredadas.
- [x] Recompilar el PDF de siete páginas y auditar visualmente todas las
  figuras.
- [x] Verificar pruebas, metadatos, lenguaje visible y hash del entregable.

## Riesgos y límites

- Se conservan datos, escalas, geometría, colores, pies y numeración.
- La fuente PDF aprobada permanece como referencia visual y de geometría; la
  nueva fuente editable sustituye solo su dependencia tipográfica.
- No se modifica ninguna figura TikZ protegida de la memoria canónica.

## Resultado

- Entregable final: `output/pdf/MROB_literature_review_7p_full_corpus_bibliometrics.pdf`.
- SHA-256: `31225989E47DE22161E228C534E65A618FBE10E84ED1B9C3B87BB67A6EE1E903`.
- Las Figuras 1--8 emplean Noto Sans para texto interno; Noto Serif queda
  reservado para prosa, pies y líneas de fuente.
