# Revisión editorial y eliminación de patrones de escritura artificial

## Propósito

Revisar la memoria completa para que la prosa española sea compacta, idiomática y académica. La revisión elimina metadiscurso, calcos sintácticos del inglés, fórmulas repetitivas, nominalizaciones innecesarias, simetrías mecánicas y referencias al proceso interno de producción. No modifica ecuaciones, cifras, alcance ni clasificación de la evidencia.

## Criterios

- Cada párrafo debe desarrollar una idea reconocible y conectarse con el anterior.
- Los términos técnicos definidos se repiten sin rotación de sinónimos.
- Las afirmaciones empiezan por el hecho, no por una fórmula de encuadre.
- Se eliminan referencias al documento, al lector, a rondas de revisión, estados internos, nombres de archivos y etiquetas de proceso que no sean necesarias para reproducir el experimento.
- Los términos ingleses se conservan solo cuando son convencionales y se definen en español.
- Se varía el ritmo sin introducir coloquialismos impropios de un TFM.
- Las limitaciones se formulan como límites del modelo o del experimento, no como descargos editoriales.

## Hitos

- [x] Inventario cuantitativo de patrones y metadiscurso.
- [x] Revisión de preliminares y capítulos 1--5.
- [x] Revisión de resultados SP0--SP8 y Cargo.
- [x] Revisión de conclusiones y anexos.
- [x] Segunda auditoría de patrones, compilación, pruebas y control visual.

## Validación

- búsqueda comparativa de fórmulas discursivas antes y después;
- ausencia de referencias editoriales o internas en el texto extraído del PDF;
- consistencia de terminología, cifras, referencias cruzadas y citas;
- `python -m pytest -q`;
- `thesis/build.ps1` e inspección visual de páginas representativas.

## Riesgos

- Una poda excesiva puede borrar supuestos o límites; cada reescritura conservará el contenido proposicional.
- Términos como potencial, robustez, validación y estado tienen sentidos técnicos; no se eliminarán por coincidencia léxica.
- Los anexos de reproducibilidad pueden mencionar configuraciones, pero no convertirán la memoria en un registro de desarrollo.

## Progreso

La segunda auditoría no encontró metadiscurso de proceso ni las etiquetas editoriales prohibidas en el texto español compilado. Las tablas y figuras de SP2--SP5 y SP7 se regeneraron desde Python con terminología española. Pasaron 74 pruebas generales y 14 pruebas específicas de los generadores modificados. La compilación limpia produjo un PDF de 128 páginas sin referencias o citas sin resolver ni desbordamientos; se inspeccionaron visualmente páginas de preliminares, metodología, SP2--SP8, Cargo, conclusiones y anexos.
