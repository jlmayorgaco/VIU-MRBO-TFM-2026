# Auditoría visual de los PDF

Fecha de inspección: 2026-09-09.

## Alcance

Se renderizaron todas las páginas de los dos entregables a JPEG de 100 dpi y se revisaron mediante once hojas de contacto, además de ampliaciones de las páginas densas con tablas, ecuaciones, figuras TikZ, resultados Cargo, atlas formal y bibliografía.

| Documento | Páginas revisadas | Resultado |
|---|---:|---|
| Memoria VIU (`pre-thesis/build/main.pdf`) | 97/97 | PASS |
| Monografía (`pre-thesis/monograph/build/monograph.pdf`) | 110/110 | PASS |

## Criterios comprobados

- No faltan páginas ni existen páginas completamente en blanco.
- No se observan figuras, tablas, ecuaciones o texto recortados fuera del área imprimible.
- Los encabezados, pies, numeración, márgenes y cambios de capítulo son coherentes.
- Las cinco figuras TikZ protegidas aparecen en la memoria y conservan legibilidad vectorial en el PDF fuente.
- Las páginas densas inspeccionadas individualmente mantienen separación suficiente entre texto, tablas y pies de figura.
- La última página de la monografía contiene el cierre normal de las referencias; no existe una página final espuria.

## Registros de compilación

La búsqueda final no encontró cajas `Overfull`, citas o referencias indefinidas, etiquetas duplicadas ni advertencias de referencias no resueltas. La monografía emitió avisos `Infinite glue shrinkage` en las tablas largas del atlas, inspeccionadas una por una entre las páginas físicas 74 y 81: no produjeron pérdida, solapamiento ni recorte de contenido.

La inspección detectó primero una cita partida de forma antinatural entre las páginas físicas 15 y 16 de la memoria. Se fijó la figura contractual en el punto de lectura, se recompiló y se reexaminaron ambas páginas: la cita quedó completa y la figura conserva su tamaño y carácter vectorial. Los binarios finales tienen hashes `07b32806a6f7a0ede9f93fb80ba7e68bb106dae0389e6d10b591ab0ea7c385c8` y `d22f011514079e7573dded2f8e19dd4710a1a01239d5450b76eb160738e2730f`. Respecto de los binarios inspeccionados, el único cambio es el `/ID` del trailer: al normalizar ese campo los archivos son byte a byte iguales y el texto extraído coincide en 207/207 páginas. Por ello la revisión visual conserva validez y no quedan defectos pendientes.

## Veredicto

`PASS WITH P3`. Ambos PDF son visualmente íntegros para el punto de control de la etapa 2.5. Los avisos tipográficos del atlas son P3 y pueden pulirse después de la revisión académica sin alterar el contenido científico.
