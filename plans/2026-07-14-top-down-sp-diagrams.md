# Diagramas cenitales SP0--SP8

## Propósito y resultado observable

Sustituir los nueve flujos conceptuales de cajas del capítulo 6 por diagramas TikZ en vista cenital que representen el escenario espacial de robots, cargas y entorno propio de cada SP. El cambio se aceptará cuando las nueve figuras compilen, sean distinguibles entre sí y resulten legibles en A4.

## Contexto y archivos canónicos

El contenido de cada escenario sigue `docs/00_TFM_CHARTER.md`, `docs/02_RESEARCH_MATRIX.md` y `docs/03_EXPERIMENT_PROTOCOL.md`; la notación procede de `docs/05_NOTATION.md`. Los archivos afectados son `thesis/viu-mrob-thesis.sty` y `thesis/sections/mainmatter/06-results-and-analysis/sp0.tex`--`sp8.tex`.

## Alcance y no alcance

Incluye representaciones esquemáticas cenitales, no resultados de simulación ni mapas experimentales definitivos. Los dibujos no fijan distancias, fuerzas ni trayectorias numéricas; comunican la geometría y el cambio incremental de cada subproblema.

## Supuestos y preguntas resueltas

- Un círculo representa un AMR y un rectángulo naranja representa una carga.
- Las líneas discontinuas distinguen asignación, comunicación, huella o región de seguridad según la leyenda local.
- SP3 usa un contacto planar genérico para no decidir prematuramente entre transporte rígido y caging/empuje.
- SP7 permanece exploratorio y SP8 representa escala/red, no una topología experimental definitiva.

## Diseño matemático/técnico

Se centralizan estilos TikZ para arena, robot, carga, objetivo, obstáculo, trayectoria, comunicación y fuerza. Cada archivo SP conserva una sola figura y su etiqueta, pero cambia el contenido a una escena espacial: asignación uno-a-uno, cardinalidad, capacidades, contactos, transporte, obstáculos, fallo, tráfico y red imperfecta.

## Plan experimental

No se ejecutan experimentos. La verificación es documental: compilación LuaLaTeX/Biber, auditoría del log y renderizado de las nueve páginas iniciales de los SP para inspección visual.

## Hitos

- [x] Respaldar las figuras y estilos compilables actuales.
- [x] Definir estilos cenitales compartidos.
- [x] Sustituir las figuras de SP0--SP8 y actualizar texto, pies y etiquetas.
- [x] Compilar sin errores, referencias indefinidas ni desbordamientos.
- [x] Inspeccionar visualmente las nueve figuras y registrar el resultado.

## Validación

Desde `thesis/`, ejecutar `./build.ps1`. Auditar `build/main.log` y renderizar con Poppler las páginas que contengan `SP0:`--`SP8:`. Cada figura debe permanecer dentro del ancho de texto y distinguir robots, cargas y el elemento incremental del SP.

## Riesgos y mitigaciones

El mayor riesgo es saturar las páginas con etiquetas o hacer ambiguas las convenciones. Se mitiga con estilos y colores coherentes, texto breve y pies descriptivos. Si una escena no cabe, se reduce su escala antes de comprimir tipografía o eliminar información esencial.

## Registro de decisiones

- 2026-07-14: se descartan flujos de cajas; todas las figuras serán escenarios cenitales.
- 2026-07-14: SP3 conserva un modelo de contacto planar neutral respecto al modo físico definitivo.
- 2026-07-14: se eliminó una envolvente ambigua en SP2 y se desplazó la etiqueta nominal de SP5 tras la inspección del PDF.

## Progreso

Trabajo completado. El respaldo quedó en `tmp/thesis-backup-20260714-pre-topdown-diagrams/`. Las nueve figuras son escenas cenitales distintas, el PDF A4 conserva 37 páginas y el log final no contiene errores, referencias indefinidas, caracteres ausentes ni cajas desbordadas. Las nueve páginas se renderizaron con Poppler y se revisaron visualmente.
