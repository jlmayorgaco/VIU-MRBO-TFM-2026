# Depuración de metadiscurso técnico en la memoria

## Propósito y resultado observable

Eliminar de la memoria toda sección o frase sobre reproducibilidad, sistema
operativo, dependencias, comandos, rutas, repositorio, código, manifiestos,
hashes y archivos. La única mención de herramientas será una frase breve en
Metodología que indique la implementación en Python y CoppeliaSim.

## Contexto y archivos canónicos

- `thesis/main.tex` compone el documento.
- `thesis/sections/mainmatter/02-objectives.tex`, `04-methodology.tex` y
  `07-conclusions.tex` concentran el metadiscurso.
- `thesis/sections/appendices/01-reproducibility.tex` es un apéndice técnico que
  debe retirarse por completo.
- `requirements-reproducible.txt` queda fuera del alcance académico solicitado.

## Alcance y no alcance

Incluye la memoria LaTeX y la eliminación del archivo de dependencias indicado.
No elimina semillas, tamaños muestrales, métricas, pruebas matemáticas ni
limitaciones físicas, porque son contenido científico.

## Supuestos y preguntas resueltas

“Meta” se interpreta como información sobre cómo reconstruir, ejecutar,
versionar o archivar el trabajo. Las palabras relacionadas con ejecución física
o dependencia matemática se conservan cuando describen el sistema estudiado.

## Diseño matemático/técnico

No se alteran modelos, ecuaciones, resultados ni cifras. OE5 se retira porque
formula trazabilidad técnica; las referencias posteriores se ajustan para
mantener numeración y coherencia.

## Plan experimental

No aplica un experimento nuevo. Se validará mediante búsquedas textuales,
compilación completa e inspección visual de las páginas afectadas.

## Hitos

- [x] Retirar apéndice, archivo de dependencias y entrada de `main.tex`.
- [x] Depurar Objetivos, Metodología, Resultados, Conclusiones y anexos formales.
- [x] Confirmar que Python y CoppeliaSim solo aparecen en Metodología.
- [x] Compilar e inspeccionar el PDF.

## Validación

- Cero coincidencias de términos meta definidos en la memoria.
- Una única mención de Python y CoppeliaSim, dentro de Metodología.
- PDF sin referencias rotas, páginas vacías ni encabezados huérfanos.

## Riesgos y mitigaciones

- Confundir “reproducir” en sentido científico con reproducibilidad técnica:
  reformular también esos usos para evitar ambigüedad sin cambiar la afirmación.
- Romper OE5 o referencias al apéndice: auditar referencias cruzadas y numeración.

## Registro de decisiones

- 2026-07-17: conservar el diseño experimental y retirar solo el metadiscurso
  técnico y administrativo solicitado.

## Progreso

Depuración completada. La memoria no contiene menciones visibles de
reproducibilidad, Windows, dependencias, comandos, repositorio, código, hashes,
manifiestos, rutas ni OE5. Python y CoppeliaSim aparecen una sola vez en la
página 11 impresa, dentro de Metodología. El PDF compila en 128 páginas y se
inspeccionaron Objetivos, Metodología, Conclusiones y el inicio de anexos sin
defectos de composición.
