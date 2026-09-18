# `main-v2`: versión 2 de la memoria con las revisiones integradas

La v2 incorpora los dos consolidados depositados en `thesis-reviews/` —revisión
académica de literatura y estado industrial y patentario— dentro de la memoria
VIU, repartidos por lo que certifica cada pieza en lugar de añadirse como un
anexo. El criterio de redacción es **figura primero**: todos los diagramas y
matrices van en el cuerpo y la prosa se limita a cuatro o cinco párrafos por
bloque, los justos para leer cada figura y declarar sus límites.

## Compilación

```powershell
.\pre-thesis\build-v2.ps1              # LuaLaTeX -> Biber -> LuaLaTeX x2
.\pre-thesis\build-v2.ps1 -SkipBiber   # iteración rápida sin rehacer la bibliografía
python .\pre-thesis\scripts\report_pages_v2.py .\pre-thesis\build-v2\main-v2.aux
```

La salida es `pre-thesis/build-v2/main-v2.pdf`. `build-v2.ps1` no ejecuta las
verificaciones de `build.ps1`: el sello de `config/release-manifest.json` y el
presupuesto de `config/page-budget.yaml` describen la v1 congelada, y la v2 añade
material por definición. La v1 sigue compilándose y verificándose igual que antes
con `build.ps1 -Target thesis -Verify`.

No se modificó ningún archivo sellado. La v2 es estrictamente aditiva: entry
propio, secciones propias y un segundo `.bib`.

## Cuál es la fuente buena de cada consolidado

**Industrial:** `TFM_estado_industrial_patentes_EDITABLE_v47.tex` y su PDF son la
misma versión. El `.tex` es la fuente y las figuras se portan de ahí literalmente.

**Académico:** el `.tex` depositado (`academic_literature_review (1).tex`, 14-sep)
está **superado** por `MROB_literature_review_reworked (2).pdf` (15-sep 22:35), que
tiene 9 páginas frente a las 4 que genera el `.tex`. El PDF manda. Las figuras que
solo existen en el PDF se reconstruyeron en TikZ leyendo los valores del propio PDF
como objetos de texto, no midiendo píxeles.

## Inventario de diagramas de los dos consolidados

Todos en el cuerpo, ninguno en anexo. Los flotantes viven en
`sections/v2/floats/`, uno por archivo, para que sigan siendo editables.

| Consolidado | Pieza original | Destino | Archivo |
|---|---|---|---|
| Académico | Tabla 1 · capas del corpus | Metodología §4.7 | `lit-tab-corpus-layers.tex` |
| Académico | Fig. 1 · mapa metodológico (32 trabajos) | Marco teórico §5.6 | `lit-fig-methodological-map.tex` |
| Académico | Fig. 2a · matriz de capacidades (con columna C) | Marco teórico §5.6 | `lit-fig-capability-matrix.tex` |
| Académico | Fig. 2b · modalidades físicas | Marco teórico §5.6 | (mismo archivo) |
| Académico | Tabla 2 · antecedentes más próximos (H·V·L·S·W·D·R·X) | Marco teórico §5.6 | `lit-tab-prior-art.tex` |
| Académico | Fig. 3a · cobertura del núcleo CORE | Resultados §6.2 | `lit-fig-coverage-rubric.tex` |
| Académico | Fig. 3b · rúbrica de dependencia global | Resultados §6.2 | (mismo archivo) |
| Académico | Fig. 5 · cambio metodológico por periodos | Resultados §6.2 | `lit-fig-method-change.tex` |
| Académico | Fig. 6 · cobertura de etapas e intersecciones | Resultados §6.2 | `lit-fig-stage-coverage.tex` |
| Industrial | Fig. 1 · mapa de precedentes | Marco teórico §5.7 | `ind-fig-map.tex` |
| Industrial | Tabla 1 · matriz funcional | Marco teórico §5.7 | `ind-tab-matrix.tex` |
| Industrial | Tabla 2 · normas e interfaces | Marco teórico §5.7 | `ind-tab-standards.tex` |
| Industrial | Fig. 2a/b/c · corpus patentario | Resultados §6.2 | `ind-fig-patents.tex` |
| Industrial | Fig. 3 · secuencia funcional | Metodología §4.7 | `ind-fig-sequence.tex` |

### Las dos que faltan

**Fig. 4** (actividad del corpus, seis paneles) y **Fig. 8** (redes de coautoría y
comunidades temático-metodológicas) del consolidado académico **no están**. Del PDF
se recuperan con certeza el panel (a) año a año, el cambio de cuota y los venues,
pero el panel (b) solo etiqueta los segmentos grandes, el (d) es una curva sin
valores impresos y las redes no exponen nodos ni aristas. Reconstruirlas obligaría a
inventar cifras, que es justo lo que se evita en el resto del documento. Hacen falta
el script o el CSV que las generó.

### Paleta y macros

`config/v2-review-palette.tex` reproduce la paleta de los consolidados (`autumn`,
`spicy`, `onyx`, `mustard`, `canary` y sus `\colorlet`) para que el TikZ portado no
haya que reescribirlo. Dos avisos para quien edite:

- Los `\colorlet` remapean `blue`, `green`, `teal`, `orange` y `olive`. Es seguro
  porque la memoria solo usa nombres `VIU*`/`SP*`, pero conviene no introducir
  figuras nuevas que dependan de esos nombres genéricos.
- Los tipos de columna del original (`L{}`, `C{}`, `Y`) se renombran a `J{}`, `K{}`
  y `Z`. Tienen que ser de **una sola letra**: `array` no maneja bien los nombres de
  varias y acaba rompiendo la `Y` de las tablas que ya existían en la memoria.

## Dónde entró cada cosa

| Pieza del consolidado | Destino | Archivo |
|---|---|---|
| Protocolo de las tres revisiones, codificación, cortes y límites | Metodología, §4.7 | `sections/v2/method-review.tex` |
| Estado del arte discriminante, composición del corpus, modalidades físicas, auditoría adversarial y brecha defendible | Marco teórico, §5.6 | `sections/v2/theory-discriminant.tex` |
| Mapa de precedentes industriales, matriz funcional de producto y normas | Marco teórico, §5.7 | `sections/v2/theory-industrial.tex` |
| Cobertura de intersecciones, autoridad por etapa, tendencias académicas y corpus patentario | Resultados, §6.2 | `sections/v2/results-review.tex` |

El criterio del reparto es el de las Instrucciones VIU: a Metodología el diseño
de la revisión, sus instrumentos y su análisis de datos; a Marco teórico el
estado del arte y la brecha; a Resultados las cifras que produce la revisión y
su contraste con los objetivos.

## Estado de la compilación

`main-v2.pdf`: 114 páginas físicas, 0 referencias o citas indefinidas, 0 `Overfull`.

| Bloque | Páginas |
|---|---:|
| 1. Introducción | 4 |
| 2. Objetivos | 2 |
| 3. Hipótesis | 2 |
| 4. Metodología | 10 |
| 5. Marco teórico | 16 |
| 6. Resultados | 43 |
| 7. Conclusiones | 4 |
| **Cuerpo** | **81** |
| Preliminares | 14 |
| Referencias | 11 |
| Anexos | 8 |

Resultados ocupa el 53,1 % del cuerpo (mínimo VIU: 50 %) y los anexos siguen en 8
de las 20 páginas permitidas, sin material de revisión.

### Incumplimiento abierto

**El cuerpo tiene 81 páginas y las Instrucciones VIU fijan un máximo de 80.** Queda
así por decisión del autor, para resolverlo en la revisión con el tutor en lugar de
recortar ahora. `viu_check.py` fallará en ese punto hasta que se cierre.

El recorte a prosa en favor de las figuras ya absorbió la diferencia una vez: la
versión anterior ocupaba las mismas 81 páginas con seis piezas gráficas desterradas
al anexo. Para la página que falta, la salida menos costosa es comprimir una página
de SP2, que ocupa 16 de las 43 de Resultados; la fracción de Resultados bajaría a
52,5 %, todavía por encima del mínimo.

## Archivos añadidos

- `main-v2.tex`, `build-v2.ps1`, `README-v2.md`
- `sections/v2/` — cuatro bloques y las versiones de resumen y *abstract* que
  declaran las revisiones
- `config/v2-review-macros.tex` — símbolos de las matrices de capacidades,
  dibujados en TikZ para que se distingan impresos en blanco y negro
- `bibliography/references-v2.bib` — 37 entradas nuevas
- `figures/review/academic-trends-dashboard.pdf` — copiado desde
  `academic-review/literature-review-v3/compact-6p/figures/`
- `scripts/report_pages_v2.py` — reparto de páginas contra los límites VIU

## Criterio seguido con la bibliografía

Los metadatos se transcriben de la lista de referencias de los consolidados. Donde
la fuente abrevia la autoría como «et al.», el `.bib` escribe `and others` en vez
de completar nombres; donde la fuente no da volumen, número ni páginas, esos
campos se omiten y el DOI queda como identificador. Es deliberado: reconstruir
esos datos de memoria habría metido metadatos inventados en un documento que pasa
por Turnitin y por el tribunal.

Las fuentes industriales son documentación oficial de fabricante con fecha de
consulta 11-09-2026, la del cierre de la auditoría web del consolidado.

## Límites que conviene recordar al defender

- Las tres revisiones son descriptivas del corpus curado. No miden prevalencia
  poblacional, cuota de mercado ni número de invenciones, y cada pie de figura lo
  repite.
- El corpus patentario es *publication-level*: la auditoría jurídica de familias
  queda fuera y el año de prioridad solo consta en 6 de 167 registros.
- La brecha se enuncia acotada al protocolo documentado. La auditoría adversarial
  muestra que el reemplazo durante el transporte ya existe en la literatura, de
  modo que cualquier reclamación de primacía sobre esa pieza sería incorrecta.
- El tablero de tendencias (Figura 14) conserva la paleta del consolidado original,
  no la VIU, porque se incrusta como PDF vectorial generado por su propio
  *pipeline*. Es la única figura del documento que no usa la paleta del `.sty`.
