# Metodología mínima: modelo, SP y validación

## Propósito y resultado observable

Reducir `thesis/sections/mainmatter/04-methodology.tex` a los elementos que el autor considera necesarios: alcance, modelo, control, modalidades Cargo y caging, división SP0--SP8, escenarios, variables, métricas, validación estadística y evaluación final en CoppeliaSim. El capítulo debe ocupar como máximo seis páginas y evitar explicación editorial o repetición del capítulo de Resultados.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`, `docs/03_EXPERIMENT_PROTOCOL.md`, la evidencia de `docs/04_CLAIMS_EVIDENCE.md`, las hipótesis de `thesis/sections/mainmatter/03-hypotheses.tex` y el texto propuesto por el usuario. Se modifica principalmente `thesis/sections/mainmatter/04-methodology.tex`; no se tocarán los cambios ajenos presentes en `thesis/sections/mainmatter/05-theoretical-framework.tex`.

## Alcance y no alcance

Incluye diseño hipotético-deductivo, mundo pareado, escalera SP0--SP8, separación Cargo/caging, variables, instrumentos, comparadores, fases, estadística, reproducibilidad y límites de inferencia. No duplica las formulaciones completas de cada SP, no presenta resultados, no afirma que el piloto caging pendiente ya fue ejecutado y no convierte CoppeliaSim en validación industrial.

## Supuestos y preguntas resueltas

- La instrucción vigente fija un máximo de seis páginas. La versión final ocupa tres páginas, de la 6 a la 8, y el Marco teórico empieza en la 9.
- Cargo sigue siendo el modo primario con evidencia cuantitativa; caging permanece como rama secundaria de evidencia objetivo C y protocolo exploratorio.
- Los identificadores vigentes de hipótesis no se alteran en este cambio: H2 cubre Cargo y caging se trata como proposición exploratoria pendiente, evitando una desincronización transversal de resultados y conclusiones.
- El detalle matemático ya desarrollado en SP0--SP8 pertenece al capítulo 6 y a los anexos; Metodología solo fija interfaces, criterios y protocolo común.

## Diseño matemático/técnico

La síntesis conservará tres objetos mínimos: el mundo pareado, la asignación
binaria con certificado físico dependiente de modalidad y el estimando pareado.
Una tabla compacta agrupará SP0--SP8 por bloques. Una figura TikZ comparativa en
dos columnas mostrará, en vista cenital, la interfaz Cargo de contactos fijos y
\emph{wrench} realizable frente a la interfaz caging de contacto unilateral y
cierre de rutas de escape. La distinción entre preferencia continua, cierre
entero, interacción física, seguridad y comunicación permanecerá explícita.

## Plan experimental

Se describirán pruebas unitarias y enumeración, desarrollo, campañas confirmatorias pareadas, estrés y evaluación funcional en CoppeliaSim. Los oráculos globales se presentarán como techo informativo; las ablaciones, fallos y timeouts se conservarán. Caging se limitará a certificado discretizado y observación estructurada si se ejecuta el piloto, sin contraste inferencial mientras no exista tamaño suficiente.

## Hitos

- [x] Hito 1 — reducir la estructura a modelo, modalidades, SP, variables/métricas y validación.
- [x] Hito 2 — conservar el TikZ Cargo--caging y una tabla SP0--SP8 con aporte y validación.
- [x] Hito 3 — compilar, medir una extensión no superior a seis páginas y revisar visualmente el PDF.
- [x] Hito 4 — revisar referencias, cajas, patrones de escritura y trazabilidad final.

## Validación

Ejecutar `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`, inspeccionar citas, referencias y cajas desbordadas en `thesis/build/main.log`, medir el intervalo del capítulo en el PDF y renderizar sus páginas con Poppler para revisar tablas, saltos y legibilidad. Ejecutar las pruebas pertinentes del manuscrito si existen.

## Riesgos y mitigaciones

El principal riesgo editorial es que tablas o ecuaciones fuercen una séptima página; se mitigará eliminando detalle repetido antes que comprimiendo tipografía. El principal riesgo científico es presentar caging como evidencia obtenida cuando permanece pendiente; se declarará como rama secundaria y protocolo exploratorio. El árbol de trabajo está sucio, por lo que solo se editarán archivos autorizados y no se restaurarán cambios preexistentes.

## Registro de decisiones

- 2026-07-17: se adopta un objetivo exacto de seis páginas por instrucción del autor.
- 2026-07-17: se conserva Cargo como rama confirmatoria y caging como extensión exploratoria pendiente.
- 2026-07-17: se evita dividir H2 en este cambio porque resultados, conclusiones y matriz de evidencia aún usan H2; la bifurcación se expresa mediante modalidades físicas y niveles de evidencia.
- 2026-07-17: la ecuación del certificado se acompaña con dos vistas cenitales;
  la figura explica las interfaces sin convertir el protocolo caging pendiente en
  evidencia obtenida.
- 2026-07-17: el autor sustituyó la versión compacta por un desarrollo de más de mil líneas. La compilación preliminar alcanzó al menos 21 páginas de Metodología antes de fallar por una expresión porcentual; se compactará el contenido y no se conservará la paginación de esa versión.
- 2026-07-17: a petición del autor, la figura física cambia Cargo a vista lateral con los AMR bajo la carga y caging a vista cenital con carga rectangular girada y cuatro AMR empujando desde las esquinas.

## Progreso

Compactación terminada. El capítulo contiene únicamente cinco apartados: alcance,
modelo y control; Cargo y caging; aporte y validación de SP0--SP8; escenarios,
variables y métricas; y validación estadística con CoppeliaSim. La metodología
ocupa las páginas 6--8 y el Marco teórico comienza en la 9. El TikZ de dos paneles
y las tablas se revisaron visualmente a 120--140 dpi. El PDF compila sin errores,
referencias indefinidas, flotantes sobredimensionados ni cajas desbordadas. La
auditoría final de `avoid-ai-writing` no encontró transiciones prefabricadas,
énfasis vacío, rayas parentéticas ni conclusiones genéricas.
La figura Cargo--caging se rediseñó después de esta auditoría y se volvió a
compilar y renderizar. Las flechas de empuje terminan en las esquinas sin cruzar
las etiquetas de los robots; la extensión del capítulo permanece en tres páginas.
