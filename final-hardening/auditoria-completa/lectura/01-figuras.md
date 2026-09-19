# Auditoría de figuras

**Criterio:** `pre-thesis/guidelines/03-figuras-y-calidad-grafica.md`, reglas 1–110.
**Artefacto:** `pre-thesis/build-v2/main-v2.pdf`, 146 páginas, 28 figuras.
**Fecha:** 2026-09-19.

## Base de medición

Esto es lo que hace comprobables las cifras de abajo.

- **Caja de texto**, tomada del bloque `geometry` real en `build-v2/main-v2.log`:
  `h-part (85.36 / 426.79 / 85.36)`, `v-part (71.13 / 702.78 / 71.13)` en puntos TeX,
  es decir **x ∈ [85,04 · 510,24], y ∈ [70,87 · 771,02]** sobre 595,28 × 841,89 pt.
  Confirma márgenes de 3 cm a los lados y 2,5 cm arriba y abajo.
- **Página impresa = página PDF − 17**, verificado en los dos extremos: Figura 1
  en la impresa 2 → PDF 19; Figura 28 en la impresa 122 → PDF 139.
- **Tamaños de fuente**: `span["size"]` por glifo, restringido al contenido de la
  figura. Se excluye el cuerpo (11,84–12,07 pt) y el pie (10,8–10,9 pt), y cada
  glifo se asigna a su figura por el ancla del pie.
- **Resolución** de los rásteres: dimensiones en píxeles frente al tamaño colocado.
- **Luminancia**: muestreo RGB del recuadro de leyenda y cálculo de luminancia
  relativa, para decidir la regla 8 con un número y no a ojo.
- **Regla 1 cumplida**: no se aprobó ninguna figura leyendo su código. Se
  inspeccionaron las páginas renderizadas a tamaño final, más recortes a 400 dpi
  de las zonas sospechosas.

---

## Tabla de medición, las 28 figuras

`mín` = glifo más pequeño dentro de la figura · `p10` = percentil 10 ·
`<7pt` = fracción de glifos de la figura por debajo de 7 pt ·
Margen = invasión con signo, en cm (positivo = invade).

| # | Nombre corto | Impr. | PDF | mín pt | p10 | med | %<7pt | Margen | Reglas incumplidas |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Escenario asignación + coaliciones | 2 | 19 | **4,98** | 5,98 | 5,98 | 99,4 | — | 3, 96, 101 |
| 2 | Contratos (4 capas) | 4 | 21 | 8,22 | 8,22 | 9,20 | 0 | — | **PASA** |
| 3 | Uniciclo | 12 | 29 | 7,97 | 7,97 | 7,97 | 0 | — | 3 (límite) |
| 4 | Retratos 4 dinámicas (símplex) | 22 | 39 | **3,98** | 3,98 | 6,23 | 74,8 | — | 3, 96, 51, 101 |
| 5 | Evolución/cobertura del corpus | 27 | 44 | **6,35** | 6,57 | 6,62 | 84,3 | **izq +0,74 / der +0,74** | 2, 3, 95, 96, 99 |
| 6 | Mapa metodológico agrupado | 28 | 45 | **3,68** | 3,68 | 4,46 | 71,3 | — | 2, 3, 7, 8, 24, 96, 99 |
| 7 | Mapa del núcleo canónico | 30 | 47 | **2,91** | 2,91 | 4,16 | 89,0 | — | 2, 3, 7, 8, 24, 96, 99, 102 |
| 8 | Matriz de capacidades | 31 | 48 | **4,95** | 4,95 | 7,45 | 34,9 | — | 3, 80, 96, 99 |
| 9 | Precedentes industriales | 32 | 49 | **3,89** | 4,88 | 4,92 | 81,1 | izq +0,09 | 2, 3, 24, 95, 96, 99 |
| 10 | Contrato composición SP1–SP3 | 34 | 51 | 5,98 | 7,97 | 9,96 | 0,8 | — | 3 (dos subíndices) |
| 11 | Cadena de procedencia | 36 | 53 | 8,89 | 8,97 | 8,97 | 0 | — | **PASA** |
| 12 | Síntesis del núcleo curado | 37 | 54 | **4,08** | 4,08 | 4,53 | 87,3 | — | 2, 3, 71, 96 |
| 13 | Cobertura de etapas | 37 | 54 | **3,12** | 3,40 | 4,21 | 62,7 | — | 3, 17, 96, 101 |
| 14 | Cambio metodológico por periodos | 38 | 55 | **3,35** | 3,35 | 4,02 | 94,6 | — | 3, 89, 96, 101 |
| 15 | Cuota temática por periodo | 38 | 55 | **4,05** | 4,05 | 4,70 | 62,2 | der +0,13 | **2, 3, 11, 17, 18, 89, 95, 96, 103** |
| 16 | Estructura bibliométrica | 39 | 56 | **2,60** | 3,75 | 5,58 | 51,6 | — | 3, 17, 80, 96, 99 |
| 17 | Corpus patentario curado | 40 | 57 | **3,98** | 4,11 | 5,33 | 82,5 | — | **2, 3, 84, 90, 96, 99** |
| 18 | Composición etapas SP1 | 42 | 59 | 5,98 | 5,98 | 5,98 | 83,2 | — | 3, 70, 96 |
| 19 | Caso didáctico E2 | 43 | 60 | 5,98 | 5,98 | 7,97 | 20,1 | — | 3, 96 |
| 20 | Composición bloques SP2 | 47 | 64 | 5,98 | 5,98 | 5,98 | 81,9 | **der +0,14** | 3, 70, 95, 96 |
| 21 | Composición bloques SP3 | 51 | 68 | 5,98 | 5,98 | 5,98 | 82,1 | der +0,05 | 3, 70, 96 |
| 22 | Cadena ejecutable ruta→física | 52 | 69 | 5,30 | 7,57 | 7,57 | 0,8 | — | 3 (bajo el suelo de 8 pt) |
| 23 | Arquitectura juego integración | 54 | 71 | 5,98 | 5,98 | 5,98 | 74,6 | — | 3, 70, 96 |
| 24 | Deformación cooperativa de rutas | 57 | 74 | 5,98 | 8,89 | 8,97 | 0,9 | — | **7, 8, 9, 49, 91** |
| 25 | Ejecución vs. parada segura | 57 | 74 | 9,96 | 9,96 | 9,96 | 0 | — | 16, 20, 90 (menor) |
| 26 | Trayectorias CoppeliaSim | 59 | 76 | 7,97 | 8,97 | 8,97 | 0 | — (420 dpi) | **7, 8, 47** |
| 27 | Secuencia funcional | 90 | 107 | **5,06** | 5,06 | 5,80 | 98,6 | — | 2, 3, 70, 95, 96 |
| 28 | Vista depurada AWS Industrial 2 | 122 | 139 | — (ráster) | — | — | — | — (433 dpi) | **PASA** |

---

## Los defectos concretos detrás de las cifras

### Reglas 3 y 96 — legibilidad a tamaño final

El estándar fija 9–10 pt ideal, 8 pt mínimo aceptable, 7 pt solo
excepcionalmente, y por debajo de 7 pt **rediseño**.

**23 de 28 figuras llevan texto por debajo de 7 pt. 14 de 28 por debajo de 5 pt.**

Los peores casos, con lo que exactamente está a ese tamaño:

- **Figura 7 a 2,91 pt** — los superíndices de referencia `[10]`…`[32]`.
- **Figura 16 a 2,60 pt** — las etiquetas de grado de los nodos de coautoría.
- **Figura 13 a 3,12 pt** — las etiquetas de fila `SP1/SP2/SP3` del panel (b).
- **Figura 14 a 3,35 pt** — **todas** las marcas del eje x, en los cinco paneles.

A tamaño real nada de esto se lee. La regla 101 («¿leo todo sin lupa?») falla.

### Reglas 2 y 95 — colisión y recorte, confirmadas renderizando

**Figura 15 (PDF 55) es la peor del documento.** El panel (a) imprime *dos*
rotulaciones conflictivas de la misma variable: una fila de cabeceras de columna
(`≤2010 / 2011-16 / 2017-21 / 2022-26`) y además una pila en negrita de 9,7 pt
con esas mismas cuatro etiquetas en el margen izquierdo, que cae directamente
sobre los nombres de categoría (`Coalición / MRTA`, `Recuperación / resil.`…).
El valor `17.3` de la barra «Contexto / otros» sale **recortado a `17.`** por el
segmento. Las filas 1–3 dibujan una barra que abarca los cuatro periodos
mientras las 4–5 dibujan cuatro segmentos separados: la misma magnitud
codificada de dos formas en un panel. El panel (a) **no tiene eje x ni unidades**
(regla 11), y sus glifos van a ~4 pt contra los 9,96 pt del panel (b)
(reglas 17 y 18).

**Figura 17 (PDF 57).** Panel (a): la caja de anotación
`Δ decisión de misión: +20,9 p.p. / sin balanceo por solicitante: +22,0 p.p.`
se superpone al texto de leyenda `MM3 volumen` y a la etiqueta de valor `26`;
el recuadro «Cambio de cuota temática» se dibuja encima del área de trazado.
Panel (b): el recuadro de leyenda `ampliación dirigida` cae **sobre** la marca
`60` del eje x, y el título del panel se parte como `identifi- / cados`, una
palabra partida dentro de la figura que la regla 2 prohíbe de forma explícita.

**Figura 9 (PDF 49).** El nodo negro `7` tapa el subtítulo
`coordinación distribuida; sin carga compartida`; el recuadro `TFM objetivo`
toca el título de cuadrante `convergencia objetivo`; `HUBTEX Aviation 2020`
toca el nodo `3`; el título del eje x se superpone a la línea de nota. Además,
un fragmento huérfano **`Anexo F.` a 11,96 pt queda solo en y = 73,6 pt**, a
4,7 cm por encima de la figura, sobrante del párrafo anterior.

**Figura 27 (PDF 107).** `carga compartida` queda recortado por el borde
derecho de la caja 4 y `Recomposición` toca el borde de la caja 5; la nota de
5,06 pt corre por debajo y dentro de las etiquetas de banda.

**Figura 12 (PDF 54).** Fragmentos con guion dentro de las cajas (`Cer-`,
`Recover;`, `Recruit,`) a 4,08 pt. La regla 71 no admite más de una línea de
salvedad dentro de una caja de contrato.

### Reglas 7 y 8 — redundancia de color y escala de grises, medidas

Luminancia relativa muestreada de los recuadros de leyenda:

- **Figura 6 (PDF 45):** azul 0,374 · púrpura 0,395 · naranja 0,423 · verde 0,448.
  Cuatro categorías dentro de un margen de luminancia de **0,074**, todas con
  marcador circular idéntico. En gris son un único gris.
- **Figura 7 (PDF 47):** púrpura 0,368 · azul 0,394 · verde **0,496** · naranja **0,499**.
  Verde y naranja difieren en **0,003**. Indistinguibles.
- **Figura 26 (PDF 76):** cuatro trayectorias separadas solo por tono, mismo
  grosor, mismo estilo, sin marcadores — y los obstáculos se dibujan en la misma
  familia de naranja que una de las trayectorias.
- **Figura 24 (PDF 74):** la identidad de coalición **no se conserva** entre
  mapas de color: A es azul discontinua pero naranja continua, B púrpura
  discontinua pero marrón continua, C amarilla discontinua pero cian continua
  (reglas 7 y 91). La `C: propuesta recta` amarilla sobre blanco incumple además
  la regla 9 de contraste.

### Regla 80 — tablas dibujadas como figuras

El panel (a) de la Figura 8 es una matriz de marcas de 12 × 10, y el panel (b)
de la Figura 16 son dos cajas de prosa. Ambos son tablas dibujadas como figura;
el estándar pide tabla LaTeX.

### Regla 92 — procedencia impresa

Las Figuras 15, 16 y 26 imprimen rutas internas del repositorio
(`pre-thesis/scripts/build_review_figure_data.py`,
`run_sp4_v4_coppelia_paired_scene.py`) en la línea de fuente. La procedencia se
conserva internamente, no se imprime.

### Lo que sí pasa

**Regla 4, tipografía: pasa.** Todas las figuras resuelven a
`ArialMT / Arial-Bold / Arial-Italic` más Computer Modern para matemáticas,
igual que el cuerpo. Las figuras de matplotlib (24–26) están correctamente en
Arial, no en DejaVu. Sin mezcla de fuentes.

**Regla 6, resolución: pasa.** Solo dos rásteres: Figura 26 a **420 dpi** y
Figura 28 a **433 dpi**, ambos sobre el suelo de 300.

---

## Presupuesto de páginas

Esto conecta con los dos incumplimientos VIU abiertos: anexos 49 páginas frente
a un máximo de 20, y Resultados 29 de 69 = 42 % frente a un mínimo de 50 %.

Páginas de solo flotante que desaprovechan la caja:

| PDF | Figura | Ocupación | Observación |
|---|---|---:|---|
| 48 | 8 | **51 %** | |
| 49 | 9 | **52 %** | **11,7 cm en blanco bajo el pie** |
| 56 | 16 | 55 % | |
| 47 | 7 | 58 % | |
| 44 | 5 | 64 % | |
| 57 | 17 | 68 % | |

Además, tres figuras aparecen **después** de su primera mención: Figura 6 con
2 páginas de retraso, Figura 8 con 2 y Figura 9 con 3 (primera mención en
PDF 43, 46 y 46). Eso fuerza saltos de composición que gastan página.

Una pasada de colocación y consolidación de flotantes sobre esas seis páginas
recupera de forma realista **2 a 3 páginas** sin tocar contenido, y más si
alguna figura se retira.

## Cruce con los flotantes no citados

Una auditoría paralela encontró que **19 elementos numerados no se citan en
ninguna parte del texto**: 10 figuras y 9 tablas. Entre las figuras:
`fig:cargo-e2e-success`, `fig:coppelia-narrow-trajectories`, `fig:megajuego-routes`,
`fig:megajuego-stopgo`, `fig:method-cargo-caging`, `fig:method-coppeliasim-warehouse`,
`fig:method-unicycle-fleet`, `fig:pre-results-provenance`,
`fig:pre-sp3-execution-envelope` y `fig:sp1-compact-pipeline`.

La consecuencia práctica: **una figura que no se lee y que además nadie cita no
es candidata a rediseño, es candidata a retirada.** Retirarla resuelve tres
problemas a la vez — legibilidad, cita obligatoria y presupuesto de páginas.

Caen en esa intersección, entre otras, la Figura 24 (`fig:megajuego-routes`),
la Figura 26 (`fig:coppelia-narrow-trajectories`) y la Figura 18
(`fig:sp1-compact-pipeline`). La 26 es la figura estrella de CoppeliaSim: esa
hay que **citarla**, no retirarla.

---

## Prioridad

### Antes del depósito — incumplen la regla 109 (un cero en colisión, recorte o legibilidad)

| # | Figura | Impr./PDF | Motivo | Fuente |
|---|---|---|---|---|
| 1 | **15** | 38 / 55 | panel (a) roto: etiquetas duplicadas sobre los nombres de fila, `17.3` recortado, codificación inconsistente, sin eje, 4,05 pt | `sections/v2/floats/lit-fig-period-shift.tex` |
| 2 | **17** | 40 / 57 | anotación sobre leyenda y leyenda sobre marca; palabra partida `identifi-/cados`; 3,98 pt | `sections/v2/floats/ind-fig-patents.tex` |
| 3 | **9** | 32 / 49 | cinco colisiones + fragmento huérfano `Anexo F.` + 3,89 pt | `sections/v2/floats/ind-fig-map.tex` |
| 4 | **7** | 30 / 47 | 2,91 pt, el texto más pequeño de la tesis; etiquetas tocando marcadores; Δluminancia 0,003 | `sections/v2/floats/lit-fig-methodological-map.tex` |
| 5 | **16** | 39 / 56 | 2,60 pt; panel (a) micro frente a panel (b) macro; el (b) es una tabla | `sections/v2/floats/lit-fig-bibliometric.tex` |
| 6 | **14** | 38 / 55 | todas las marcas a 3,35 pt en cinco paneles | `sections/v2/floats/lit-fig-method-change.tex` |
| 7 | **13** | 37 / 54 | 3,12 pt | `sections/v2/floats/lit-fig-stage-coverage.tex` |
| 8 | **12** | 37 / 54 | 4,08 pt con palabras partidas dentro de cajas de contrato | `sections/v2/floats/lit-fig-coverage-rubric.tex` |
| 9 | **6** | 28 / 45 | 3,68 pt, solapes etiqueta/marcador, falla en gris | v1 sellada, `sections/source-snapshot/mainmatter/05-theoretical-framework.tex` |
| 10 | **5** | 27 / 44 | **0,74 cm dentro de ambos márgenes** (x ∈ [64,1 · 531,3] frente a [85,04 · 510,24]) y 84 % bajo 7 pt | misma v1 sellada |
| 11 | **4** | 22 / 39 | subíndices del símplex a 3,98 pt, títulos de panel a 6,23 pt | misma v1 sellada |
| 12 | **27** | 90 / 107 | `carga compartida` recortado por su caja, 5,06 pt | `sections/v2/floats/ind-fig-sequence.tex` |

### Conviene corregir — suelo de 7 pt, sin colisión

- **Figuras 18, 20, 21, 23** (42/59, 47/64, 51/68, 54/71): toda la familia
  «composición de bloques SP*» rotula títulos de caja y líneas `certifica:` a
  **5,98 pt** en diagramas de 15 cm con sitio de sobra. La regla 70 exige además
  que la fuente de diagrama sea ≥ la de gráfico. La Figura 20 saca una caja
  **4,06 pt (0,14 cm) del margen derecho**.
- **Figura 8** (31/48): panel (b) a 4,95 pt; el (a) debería ser tabla LaTeX.
- **Figura 1** (2/19): subíndices a 4,98 pt y etiquetas a 5,98 pt en una figura
  casi de portada (regla 107).
- **Figura 19** (43/60): 5,98 pt en el 20 % de los glifos.
- **Figuras 24 y 26**: el color es el único canal (regla 8); el mapa de la 24 no
  es consistente por coalición (reglas 7 y 91); la amarilla sobre blanco de la
  24 incumple la regla 9.

### Cosmético

- Figura 20 con 0,14 cm de desborde y Figura 15 con 0,13 cm (la etiqueta `+17.7`):
  menos de 1,5 mm, se arregla con 2 mm de caja envolvente.
- Figura 22 (52/69) a 7,57 pt y Figura 3 (12/29) a 7,97 pt: bajo el mínimo
  normal de 8 pt pero sobre la línea de rediseño de 7.
- Figura 10: solo dos subíndices a 5,98 pt; el resto a 9,96.
- Figura 25: el pie da porcentajes sin declarar *n* (regla 16); marcas en
  diagonal (regla 90); sin trama para gris (regla 20); la barra de altura cero
  `Tiempo parado` queda sin etiquetar.
- Regla 92: retirar las rutas de script impresas bajo las Figuras 15, 16 y 26.
- Regla 99: Figuras 6, 8 y 9 aparecen 2–3 páginas después de su primera mención.

### Limpias — cumplen el estándar tal como se imprimen

**Figura 2** (8,22–9,20 pt), **Figura 11** (8,89–9,96 pt) y **Figura 28**
(ráster a 433 dpi, sin texto interno). Son las tres únicas que hoy superarían
los doce gates de la regla 110.
