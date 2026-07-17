# Demostraciones en anexos y señalización de contribuciones originales

## Propósito y resultado observable

Reorganizar la memoria para que el cuerpo principal conserve los enunciados, supuestos, alcance e interpretación de los resultados formales, mientras las demostraciones completas quedan en anexos. Introducir una convención visual naranja que permita localizar con rapidez formulaciones, caracterizaciones, cotas y resultados formales propios sin confundirlos con literatura, baselines ni resultados pendientes.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` fija la contribución nuclear y prohíbe sobreafirmar.
- `docs/01_VIU_REQUIREMENTS.md` limita los anexos a 20 páginas y exige la plantilla oficial.
- `docs/04_CLAIMS_EVIDENCE.md` clasifica qué resultados propios están soportados.
- `docs/07_SP_SECTION_TEMPLATE.md` exige que el cuerpo mantenga el resultado formal y su garantía honesta.
- `thesis/viu-mrob-thesis.sty` centraliza los estilos LaTeX.
- `thesis/sections/mainmatter/06-results-and-analysis/sp0.tex`--`sp2.tex` contienen los resultados formales actuales.
- `thesis/sections/appendices/02-sp0-proofs.tex` y `03-sp1-proofs.tex` contienen las pruebas ya separadas.

## Alcance y no alcance

Incluye la creación de un entorno reutilizable para aportaciones originales, su aplicación a los resultados propios respaldados de SP0--SP2, el traslado de la prueba completa de SP2 a un nuevo anexo y la actualización de las reglas editoriales y de trazabilidad afectadas. No altera enunciados matemáticos, evidencia experimental, citas, notación ni resultados numéricos. No marca como novedosos resultados tomados de la literatura, oráculos, baselines, observaciones empíricas genéricas o afirmaciones pendientes.

## Supuestos y preguntas resueltas

- “Mandar todas las demostraciones a anexos” se interpreta como retirar del cuerpo las derivaciones completas, no los enunciados ni una síntesis argumental necesaria para su lectura.
- “Contribución nueva” se restringe a resultados formulados por este TFM y compatibles con la matriz de evidencia; la caja visual no equivale a una reivindicación de prioridad universal frente a toda la literatura.
- El naranja VIU existente se reutiliza con un fondo muy claro y una barra lateral para mantener legibilidad en impresión.

## Diseño matemático/técnico

Se añadirá un entorno `contribucion` basado en una caja divisible entre páginas. El título indicará la clase del aporte, por ejemplo “Formulación y caracterización propias” o “Cota propia”. Cada caja contendrá el objeto formal y, cuando corresponda, el enunciado con sus supuestos. La demostración se enlazará mediante una referencia explícita al anexo. El anexo de SP2 repetirá únicamente el enunciado mínimo necesario para que la prueba sea autocontenida.

## Plan experimental

No se ejecutan experimentos: el cambio es editorial y estructural. La validación consiste en compilación LuaLaTeX/Biber, resolución de referencias, búsqueda de entornos `proof` en el cuerpo y revisión visual de las páginas afectadas.

## Hitos

- [x] Hito 1 — entorno naranja y convención editorial definidos.
- [x] Hito 2 — contribuciones propias de SP0--SP2 marcadas sin alterar su estatus epistemológico.
- [x] Hito 3 — demostración de SP2 trasladada y enlazada desde el cuerpo.
- [x] Hito 4 — documentación y matriz de evidencia sincronizadas.
- [x] Hito 5 — PDF compilado y revisado; ninguna demostración completa permanece en el cuerpo.

## Validación

- `rg -n '\\begin\{proof\}' thesis/sections/mainmatter`
- `rg -n '\\begin\{contribucion\}' thesis/sections/mainmatter thesis/sections/appendices`
- `thesis/build.ps1`
- Revisión del log para referencias indefinidas y cajas desbordadas.
- Revisión visual de SP0, SP1, SP2 y del nuevo anexo.

## Riesgos y mitigaciones

- **Exceso de páginas en anexos:** medir el PDF final; mantener las pruebas compactas y no duplicar derivaciones en el cuerpo.
- **Sobreafirmación de novedad:** titular las cajas como aportaciones de este TFM, no como prioridad universal, y conservar limitaciones dentro del enunciado.
- **Ruido visual:** usar fondo tenue, una sola barra naranja y títulos descriptivos; no envolver resultados de literatura.
- **Rotura de referencias:** conservar las etiquetas existentes y añadir etiquetas nuevas solo para el anexo.

## Registro de decisiones

- 2026-07-16 — Se conserva en el cuerpo una síntesis razonada de cada prueba para que el resultado sea interpretable sin obligar a leer el anexo.
- 2026-07-16 — La señal visual significa “aporte formulado en este TFM”, no “novedad mundial demostrada por revisión exhaustiva”.
- 2026-07-16 — Se reutiliza `VIUOrange` para coherencia con la plantilla oficial.

## Progreso

Se revisaron las fuentes de verdad, la plantilla, los tres SP con resultados formales y los anexos existentes. La única demostración completa que permanecía en el cuerpo, la prueba de alineación marginal de SP2, se trasladó al nuevo Anexo D. El entorno naranja se aplicó a las formulaciones y resultados propios de SP0--SP2 y, en anexos, a las fronteras de complejidad, eficiencia e implementabilidad, las cotas grafo--gap y entrópica y la imposibilidad bajo desconexión. La compilación final produjo un PDF estable de 108 páginas sin referencias indefinidas; los anexos ocupan las páginas 93--108, es decir, 16 páginas frente al máximo VIU de 20. La revisión visual de SP0, SP1, SP2 y los anexos confirmó contraste, márgenes, legibilidad, partición de cajas y comienzos de anexo en página nueva. La búsqueda final no encontró entornos `proof` en el cuerpo principal.
