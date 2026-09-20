# Revisión visual exacta del literature review

## Objetivo

Entregar una versión de seis páginas que preserve literalmente las cuatro
páginas del PDF de referencia facilitado por el autor y añada dos páginas de
actualización V3. De este modo, mapa, ejes, matriz, modalidades físicas,
intersecciones, colores, tipografía y dashboard permanecen idénticos al
documento aprobado visualmente.

## Decisión de edición

- Páginas 1--4: facsímil vectorial del PDF de referencia, sin redibujar ni
  reinterpretar sus figuras.
- Páginas 5--6: actualización V3 con la misma tipografía, paleta, márgenes,
  cabeceras y jerarquía editorial del original.
- La página 5 declara explícitamente que las páginas 1--4 corresponden al corte
  legado `n=59` y que la actualización V3 usa `n=244`.
- Se conservan como análisis adicionales la evolución metodológica, la
  cobertura de interfaces, la madurez de evidencia y la cadena de certificados.
- Las cifras del facsímil no se presentan como recomputadas con V3.

## Definición de terminado

- [x] PDF final de exactamente seis páginas.
- [x] Páginas 1--4 visualmente idénticas al PDF original mediante comparación
  de render píxel a píxel.
- [x] Páginas 5--6 compiladas con el estilo exacto del original.
- [x] Sin desbordamientos, referencias indefinidas ni caracteres ausentes.
- [x] Pruebas académicas aprobadas e inspección visual de las seis páginas.
- [x] PDF final en `output/pdf/` y manifiesto/hash de trazabilidad.

## Cierre

La edición se construyó con `academic-review/scripts/build_exact_visual_review.py`.
Las cuatro comparaciones renderizadas a 160 dpi devolvieron
`difference_bbox=None`; las 63 pruebas de `academic-review/tests` pasaron. El
detalle de control queda registrado en
`academic-review/literature-review-v3/compact-6p-exact/QA_EXACT_VISUAL_6P.md`.

## Revisión editorial e integración del capítulo

Solicitud del autor: eliminar el tono de suplemento o edición, integrar el
corpus ampliado en la argumentación del capítulo y rediseñar la Figura 7.

- [x] Presentar el núcleo curado y el corpus ampliado como niveles
  complementarios de análisis, sin instrucciones meta al lector.
- [x] Sustituir los rótulos de actualización por títulos propios del capítulo
  de marco teórico y estado del arte.
- [x] Rediseñar la Figura 7 como contrato verificable SP1--SP3, conservando
  TikZ vectorial y la paleta del documento.
- [x] Auditar las páginas reescritas para retirar patrones de redacción
  formularia, énfasis vacío y transiciones mecánicas.
- [x] Recompilar, comprobar seis páginas y revisar visualmente el PDF completo.
