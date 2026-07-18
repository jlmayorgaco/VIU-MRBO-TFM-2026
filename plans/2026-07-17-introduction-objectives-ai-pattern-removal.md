# Eliminación de patrones de escritura artificial en Introducción y Objetivos

## Propósito y resultado observable

Reescribir la Introducción y los Objetivos para eliminar guiones parentéticos,
aperturas formularias, enumeraciones simétricas, nominalizaciones y ritmo
uniforme. El contenido científico, las citas, la estructura superior VIU y el
nivel de evidencia permanecerán intactos.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`,
`docs/07_SP_SECTION_TEMPLATE.md` y la evidencia registrada. Se modifican
únicamente `thesis/sections/mainmatter/01-introduction.tex` y
`thesis/sections/mainmatter/02-objectives.tex`.

## Alcance y no alcance

Incluye una reescritura editorial completa de ambos capítulos, la inserción del
párrafo de entrada que falta en Objetivos y una segunda auditoría de patrones.
No incluye cambios en hipótesis, métodos, cifras, referencias, resultados,
notación ni título administrativo.

## Supuestos y preguntas resueltas

- La modalidad primaria sigue siendo Cargo planar soportado.
- La arquitectura se describe como híbrida porque algunas etapas consultan
  información global declarada.
- Los objetivos deben ser medibles, pero no necesitan compartir una plantilla
  sintáctica idéntica.
- Los rangos escritos con guiones tipográficos pueden expresarse en prosa para
  que los dos archivos queden libres de `--` y `---`.

## Diseño matemático/técnico

No se modifica ninguna formulación. La edición conserva las fronteras entre
decisión estratégica, cierre entero, certificado físico, control, seguridad y
comunicación. Cada limitación permanece junto a la afirmación que acota.

## Plan experimental

No se generan experimentos. La validación consiste en auditoría léxica y
estructural, comparación del diff, compilación completa y revisión del log y de
las páginas resultantes.

## Hitos

- [x] Auditar patrones P0, P1 y P2 y comprobar la coherencia documental.
- [x] Reescribir Introducción y Objetivos sin alterar su contenido científico.
- [x] Ejecutar una segunda auditoría, compilar y revisar el diff.

## Validación

- búsqueda de `---`, `--` y fórmulas discursivas recurrentes en ambos archivos;
- `git diff --check` y revisión del diff limitado al alcance;
- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`;
- búsqueda de errores, citas y referencias indefinidas en el log de compilación.

## Riesgos y mitigaciones

La poda estilística puede borrar supuestos o límites. Cada párrafo reescrito se
comparará con la matriz de evidencia y con su versión anterior. El árbol contiene
cambios ajenos en Metodología, Marco teórico y el estilo LaTeX; no se modificarán.

## Registro de decisiones

- 2026-07-17: aplicar una reescritura estructural, no una sustitución aislada de
  guiones, porque el ritmo y la sintaxis también muestran patrones repetitivos.
- 2026-07-17: añadir un párrafo antes de la primera subsección de Objetivos para
  cumplir la regla VIU que prohíbe dos encabezados consecutivos sin texto.

## Progreso

Trabajo completado. La auditoría inicial encontró un inciso con guiones largos en
OE4, cinco usos adicionales de dobles guiones en la Introducción, objetivos
sintácticamente uniformes y varios párrafos construidos como secuencias de listas.
La segunda pasada no encontró los patrones P0/P1 buscados ni usos de `--`, `---` o
guion largo. Se conservaron las dieciséis claves bibliográficas de la Introducción.
El PDF recompilado contiene 121 páginas; la Introducción ocupa dos páginas y
Objetivos una, sin cortes anómalos. El log mantiene dos referencias indefinidas,
`eq:method-unicycle` y `eq:method-wheel-torque`, procedentes de SP3 y SP4 y ajenas
a los archivos editados.
