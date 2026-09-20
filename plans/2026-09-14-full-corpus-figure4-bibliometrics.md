# Figura 4 y mapa bibliométrico del corpus completo

## Objetivo

Recalcular la Figura 4 con los 244 documentos del corpus analítico consolidado,
conservando su gramática visual de seis paneles, y añadir una figura
bibliométrica reproducible que muestre la estructura de coautoría, la
coocurrencia temática y el perfil temático de las comunidades de autores.

## Decisiones metodológicas

- El universo analítico es `analytic_corpus_v3.csv`: 244 documentos, 243 con
  año entre 1979 y 2026. No se mezclan las 3.014 identidades de descubrimiento
  con los documentos adquiridos y codificados.
- Las siete familias de la Figura 4 se obtienen de señales ya trazables de
  título/resumen. La pertenencia es multietiqueta y cada documento reparte un
  peso total de uno entre sus familias; así los totales anuales y las cuotas de
  periodo no se inflan por doble conteo.
- La diversidad móvil es entropía de Shannon normalizada por `log(7)` en una
  ventana retrospectiva de tres años. Un año sin documentos no se interpreta
  como diversidad cero.
- La proporción distribuida usa como denominador todos los documentos del año;
  mide presencia de la señal en título/resumen, no prueba de implementación.
- La red de coautoría conserva cadenas exactas, sin desambiguación. La vista
  principal muestra el núcleo recurrente: autores con al menos dos documentos
  y componentes conectados de al menos tres autores.
- La red temática combina señales controladas de tema, método y aplicación.
  Las aristas representan coocurrencia en al menos dos documentos y se ponderan
  por asociación normalizada. Las comunidades se calculan con Louvain y semilla
  fija; se describen como comunidades del corpus, no como escuelas del campo.
- La entrega conserva la gramática visual aprobada en siete páginas. Las
  páginas 1 y 3 permanecen exactas; la página 2 solo cambia el lenguaje de
  proceso por una delimitación académica de la novedad. La página 4 se
  recalcula, las páginas 5--6 integran el argumento y la página 7 concentra el
  análisis bibliométrico.
- La Figura 8 elimina la franja de cifras agregadas. El espacio se reasigna a
  las redes y a una matriz con códigos A1--A8, acompañada por una clave lateral
  de autores legible a tamaño de impresión.

## Entregables reproducibles

- [x] Script único de análisis y generación de las Figuras 4 y 8.
- [x] CSV de actividad/familias, cuotas, cambio, diversidad y emergencia.
- [x] CSV de nodos/aristas/comunidades de coautoría y temas.
- [x] Figura 4 vectorial con la composición visual aprobada.
- [x] Figura bibliométrica vectorial con criterios de filtrado visibles.
- [x] Página 4 de reemplazo y página 7 bibliométrica en LaTeX.
- [x] PDF final de siete páginas en `output/pdf/` y manifiesto con hashes.

## Verificación

- [x] La suma de pesos por documento y año es uno.
- [x] Las cuotas de cada periodo suman 100 % dentro de tolerancia numérica.
- [x] La diversidad está en `[0,1]` o es ausente si no hay documentos.
- [x] Los nodos y aristas de las redes provienen del corpus y los umbrales son
  reproducibles.
- [x] Páginas 1 y 3 son idénticas al PDF aprobado; la página 2 conserva la
  composición y sustituye únicamente el bloque de lenguaje de proceso.
- [x] Siete páginas letter, figuras vectoriales, sin desbordamientos LaTeX.
- [x] Inspección visual de todas las páginas, búsqueda de lenguaje de proceso y
  pruebas académicas aprobadas.

## Cierre

El PDF final conserva la composición aprobada y reúne en siete páginas la
Figura 4 recalculada, la síntesis SP1--SP3 y la Figura 8 bibliométrica. La
franja de cifras se retiró, la matriz usa códigos A1--A8 con clave lateral y el
texto visible quedó libre de etiquetas de proceso. Las 68 pruebas pasaron; el
QA visual y cuantitativo queda en el registro reproducible de la entrega.
