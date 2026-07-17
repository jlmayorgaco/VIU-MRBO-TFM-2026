# Servorregulación estratégica en SP0--SP3

## Propósito y resultado observable
Reformular el bloque «Problema de control y acoplamiento» para que cada SP declare la salida estratégica regulada, su referencia, el error, la información realimentada, el estimador, la ley de revisión y la garantía disponible. El control físico se conserva como una segunda capa cuando existe planta.

## Contexto y archivos canónicos
- `docs/00_TFM_CHARTER.md`
- `docs/04_CLAIMS_EVIDENCE.md`
- `docs/05_NOTATION.md`
- `docs/07_SP_SECTION_TEMPLATE.md`
- `thesis/sections/mainmatter/06-results-and-analysis/sp0.tex`--`sp3.tex`

## Alcance y no alcance
Incluye la formulación de lazo cerrado estratégico de SP0--SP3 y la interfaz con el control físico. No añade experimentos, no inventa sensores implementados y no demuestra convergencia de las dinámicas muestreadas donde esa prueba no existe.

## Supuestos y preguntas resueltas
- «Control» incluye regulación de errores de asignación, cuota, capacidad y wrench.
- El problema de optimización define la referencia o conjunto objetivo; la ley de revisión describe cómo se intenta alcanzarlo.
- Solo SP0 y el caso realizable de SP1 admiten un corolario inmediato de regulación finita a partir de las proposiciones ya demostradas.

## Diseño matemático/técnico
- SP0: regular `D(a)` y `E(a)` a cero mediante mejor respuesta asíncrona realimentada por ocupación.
- SP1: regular déficit/exceso a cero si la demanda es realizable; bajo escasez, regular el residual de cierre respecto de cargas seleccionadas.
- SP2: regular déficit normalizado de capacidad con feedback de `S_k`; la campaña actual usa agregados y scorers secuenciales, no una EDO distribuida.
- SP3: regular residual de wrench y congestión de slots mediante preferencias y precios; separar este lazo del docking físico.

## Plan experimental
No aplica: se conserva la evidencia existente y se explicita qué lazos no fueron ejecutados.

## Hitos
- [x] Plantilla y notación sincronizadas.
- [x] SP0--SP3 reformulados sin sobreafirmar estabilidad.
- [x] Compilación LaTeX y 23 pruebas específicas superadas.

## Validación
Buscar referencias y etiquetas rotas, compilar la memoria o al menos los artefactos LaTeX disponibles y revisar el diff de los archivos afectados.

## Riesgos y mitigaciones
- Confundir estabilidad estratégica con estabilidad física: nombrar y analizar las capas por separado.
- Presentar un estimador candidato como implementado: declarar explícitamente la información global usada por cada campaña.
- Forzar error cero bajo escasez: definir el conjunto alcanzable mediante selección `y_k` y cierre todo-o-nada.

## Registro de decisiones
- 2026-07-16: se adopta «servorregulación estratégica» como contenido obligatorio del bloque de control en todos los SP; el control físico es una capa adicional.

## Progreso
Plantilla, notación, matriz de claims, SP0--SP3 y anexos SP0/SP1 actualizados. La memoria compila con LuaLaTeX, las 23 pruebas específicas pasan y la inspección visual de las páginas afectadas no muestra cortes, solapamientos ni ecuaciones ilegibles. Se añadieron corolarios únicamente para SP0 y el juego finito realizable de SP1; SP2 y SP3 conservan explícita la falta de prueba de convergencia de sus lazos muestreados.
