# Pulido profesional de diagramas cenitales SP0--SP8

## Propósito y resultado observable

Elevar las nueve figuras TikZ del capítulo 6 a calidad de memoria académica: eliminar solapes, reforzar jerarquía visual, unificar convenciones y añadir el detalle espacial necesario para comprender cada SP sin depender del párrafo circundante.

## Contexto y archivos canónicos

El contenido de cada escena sigue `docs/00_TFM_CHARTER.md`, `docs/02_RESEARCH_MATRIX.md`, `docs/03_EXPERIMENT_PROTOCOL.md`, `docs/04_CLAIMS_EVIDENCE.md` y `docs/05_NOTATION.md`. Se modificarán `thesis/viu-mrob-thesis.sty` y `thesis/sections/mainmatter/06-results-and-analysis/sp0.tex`--`sp8.tex`.

## Alcance y no alcance

Incluye una nueva gramática gráfica, composición y anotación de las escenas. No convierte los dibujos en resultados de simulación ni fija dimensiones físicas no verificadas. Las figuras seguirán siendo esquemáticas y de elaboración propia.

## Supuestos y preguntas resueltas

- Se usará una paleta consistente y redundancia entre color, trazo y etiqueta.
- Cada figura tendrá un marco de escenario, rejilla tenue y franja de leyenda separada.
- Las etiquetas no se colocarán directamente sobre trayectorias o elementos activos.
- SP6 usará dos instantáneas cenitales para distinguir fallo y recuperación.
- SP3 mantendrá un contacto planar genérico hasta declarar el modo físico principal.

## Diseño matemático/técnico

La hoja de estilo definirá colores propios, rejilla, marcos, robots activos/libres/fallidos, cargas, objetivos, coaliciones, trayectorias, comunicaciones, fuerzas, medidas y anotaciones. Cada SP reutilizará esos estilos y reservará una franja inferior para leyendas o parámetros, evitando texto flotante sobre la escena.

## Plan experimental

No se generan resultados científicos. La validación consistirá en compilar con LuaLaTeX/Biber, auditar el log, localizar las nueve páginas y renderizarlas con Poppler. Se revisarán legibilidad a página completa, alineación, solapes, consistencia de símbolos y correspondencia con el SP.

## Hitos

- [x] Respaldar la versión cenital compilable actual.
- [x] Implementar el sistema gráfico compartido y la franja de leyenda.
- [x] Rediseñar SP0--SP4.
- [x] Rediseñar SP5--SP8.
- [x] Compilar, auditar y corregir el render.
- [x] Revisar visualmente las nueve figuras y cerrar el plan.

## Validación

Ejecutar `thesis/build.ps1`. El log no debe contener errores, referencias indefinidas, caracteres ausentes ni cajas desbordadas. Cada figura debe caber en el ancho de texto, mantener etiquetas de al menos tamaño `\scriptsize` y conservar una lectura clara en A4.

## Riesgos y mitigaciones

Más detalle puede producir saturación. Se limitará cada figura a un mensaje principal y tres o cuatro convenciones visibles. El color no será el único codificador. Si el capítulo crece, se ajustará la escala de las figuras sin reducir la tipografía por debajo de lo legible.

## Registro de decisiones

- 2026-07-14: se adopta una plantilla común con rejilla tenue y banda inferior de leyenda.
- 2026-07-14: SP6 se representará mediante estados espaciales antes/después.
- 2026-07-14: se usará una paleta propia en lugar de depender de colores DVIPS genéricos.
- 2026-07-14: se reserva una banda superior blanca para que el título nunca compita con la escena.
- 2026-07-14: SP3 separa visualmente contactos, fuerzas, marco de cuerpo, torque y wrench; SP7 explicita la regla de prioridad dentro del cruce.

## Progreso

Trabajo cerrado. Se creó el respaldo `tmp/thesis-backup-20260714-pre-professional-diagrams/`; se rediseñaron y revisaron visualmente SP0--SP8; y `thesis/build/main.pdf` compila en A4 con 37 páginas. La auditoría final no encontró errores, referencias indefinidas, caracteres ausentes, cajas desbordadas, marcadores de borrador ni etiquetas duplicadas. Permanece únicamente el aviso esperado de bibliografía vacía mientras no se incorporen referencias verificadas.
