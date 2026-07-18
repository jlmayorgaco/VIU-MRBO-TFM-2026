# Revisión de la Introducción en tres páginas

## Propósito y resultado observable

Reorganizar `thesis/sections/mainmatter/01-introduction.tex` como una única sección continua, sin subsecciones ni subtítulos internos, con una extensión máxima de tres páginas en el PDF canónico. La versión final debe presentar contexto, problema, brecha, propuesta, contribución delimitada y mapa del documento, con citas LaTeX existentes, verificadas y clicables.

## Contexto y archivos canónicos

- Alcance y contribución: `docs/00_TFM_CHARTER.md`.
- Requisitos formales: `docs/01_VIU_REQUIREMENTS.md`.
- Niveles de evidencia: `docs/02_RESEARCH_MATRIX.md` y `docs/04_CLAIMS_EVIDENCE.md`.
- Protocolo y notación: `docs/03_EXPERIMENT_PROTOCOL.md` y `docs/05_NOTATION.md`.
- Literatura verificada: `references/LITERATURE_LEDGER.md` y `thesis/references.bib`.
- Fuente que se modifica: `thesis/sections/mainmatter/01-introduction.tex`.
- Salida verificable: `thesis/build/main.pdf`.

## Alcance y no alcance

Incluye reordenación, condensación, corrección de prosa, sustitución de claves bibliográficas inexistentes y verificación del PDF. No cambia objetivos, hipótesis, resultados, cifras experimentales, título administrativo ni alcance científico. Las fuentes institucionales nuevas se verifican y registran antes de usarlas.

## Supuestos y preguntas resueltas

- La pregunta principal se integra en prosa; RQ1--RQ5 permanecen desarrolladas fuera de la Introducción para evitar duplicación.
- La cadena SP0--SP8 se resume por capacidades, sin enumerar cada SP.
- La modalidad primaria sigue siendo Cargo planar soportado; empuje/caging queda fuera del alcance validado.
- La afirmación de brecha se formula como resultado del corpus revisado, no como inexistencia universal.
- Las afirmaciones académicas se apoyan en entradas `VERIFICADA`; dos páginas corporativas `PARCIAL` se usan solo para constatar plataformas y aplicaciones declaradas. Todas las claves están presentes en `thesis/references.bib`.

## Diseño matemático/técnico

La sección seguirá un esquema de ocho párrafos: contexto industrial; escenario motivador; problema técnico; cobertura y límites de la literatura; arquitectura y pregunta principal; contribución y evidencia; alcance; organización del documento. Cada párrafo tendrá un mensaje dominante y una primera frase que lo anuncie.

## Plan experimental

No se generan experimentos nuevos. La validación consiste en compilación completa con Biber, inspección del intervalo de páginas ocupado por la Introducción, búsqueda de citas/referencias indefinidas y revisión visual de sus páginas.

## Hitos

- [x] Hito 1 — Auditar estructura, duplicaciones y claves bibliográficas actuales.
- [x] Hito 2 — Sustituir la Introducción por una narración continua y trazable.
- [x] Hito 3 — Compilar y demostrar una extensión máxima de tres páginas sin citas indefinidas.
- [x] Hito 4 — Completar el esquema inverso y revisar el diff final.

## Validación

- `thesis/build.ps1` para LuaLaTeX, Biber y estabilización de referencias.
- Búsqueda en `thesis/build/main.log` de `Citation ... undefined`, `undefined references` y errores.
- Extracción de marcadores o texto para localizar el inicio de Introducción y Objetivos.
- Renderizado de las páginas de la Introducción para revisar continuidad, blancos, cortes y enlaces visibles.
- `git diff --check` y revisión limitada a los archivos previstos.

## Riesgos y mitigaciones

- Riesgo de exceder tres páginas: eliminar duplicación con Objetivos/Hipótesis antes de reducir tipografía o espaciado.
- Riesgo de sobreafirmación: usar la matriz de evidencia y declarar los límites junto a la contribución.
- Riesgo de citas rotas: comprobar clave en `.bib`, estado `VERIFICADA` y log de Biber.
- Riesgo de mezclar cambios: preservar el ajuste pendiente del encabezado y revisar el diff por archivo.

## Registro de decisiones

- 2026-07-17: se adopta una estructura sin subtítulos ni listas de preguntas para respetar la petición y reducir redundancia.
- 2026-07-17: se conserva la cifra de ventas de 2024 después de verificar la fuente oficial de la IFR; se explicita que corresponde a una muestra de 294 proveedores y no a una proyección de toda la industria.
- 2026-07-17: las páginas oficiales sin fecha de Geek+ y MiR quedan `PARCIAL` y se usan exclusivamente para documentar plataformas y casos de uso declarados, no para sostener eficacia o superioridad.
- 2026-07-17: se usarán solo claves existentes y verificadas; las citas de bibliografía serán enlaces administrados por `biblatex`/`hyperref`.
- 2026-07-17: la versión final ocupa dos páginas; se condensó el mapa de capítulos para eliminar una tercera página que contenía una sola línea.

## Esquema inverso y control de afirmaciones

1. Contexto industrial de la intralogística; respaldo: IFR, Wurman y páginas oficiales de Geek+ y MiR, con sus límites explícitos.
2. Necesidad de coaliciones temporales para cargas menos regulares; respaldo: revisión de transporte cooperativo.
3. Dificultad técnica más allá de la cardinalidad; respaldo: taxonomías MRTA, coaliciones ejecutables y control cooperativo.
4. Fragmentación de la literatura y brecha limitada al corpus; respaldo: fuentes verificadas y afirmación C8.
5. Arquitectura híbrida, frontera de información y pregunta principal; respaldo: charter y arquitectura implementada.
6. Cadena metodológica y estrategia de evaluación; respaldo: matriz SP0--SP8, protocolo y resultados versionados.
7. Alcance Cargo planar y límites de generalización; respaldo: matriz de evidencia.
8. Mapa compacto de la memoria.

No se incorporaron cifras experimentales ni afirmaciones de optimalidad, estabilidad global, seguridad continua o descentralización integral.

## Progreso

Revisión textual y bibliográfica completada. La Introducción quedó en ocho párrafos continuos; las dieciséis claves citadas existen en `thesis/references.bib`. Catorce figuran como `VERIFICADA` y las dos páginas corporativas sin año como `PARCIAL`, con uso limitado. Pendiente de actualizar aquí el conteo definitivo de páginas y enlaces después de recompilar la versión concurrente más reciente.
