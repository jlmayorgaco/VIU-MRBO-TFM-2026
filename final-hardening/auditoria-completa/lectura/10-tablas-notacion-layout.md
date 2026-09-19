# Auditoría de tablas, notación, layout y front matter

**Criterio:** `pre-thesis/guidelines/01-auditoria-maestra.md`, bloques **45** (Tablas, líneas 763–777),
**24** (Notación matemática, líneas 396–412), **48** (Layout / composición visual, líneas 808–827)
y **49** (Front matter, líneas 828–838).
**Artefacto:** `pre-thesis/build-v2/main-v2.pdf`, 146 páginas, **41 tablas numeradas**.
**Fuentes:** los 89 ficheros `.tex` listados en `final-hardening/census.json`.
**Fecha:** 2026-09-19.

## Base de medición

Todo lo que sigue está medido, no estimado a ojo.

- **Caja de texto**, del bloque `geometry` de `build-v2/main-v2.log`:
  **x ∈ [85,04 · 510,24] pt, y ∈ [70,87 · 771,02] pt** sobre 595,28 × 841,89 pt.
- **Página impresa = página PDF − 17**, verificado en los dos extremos: Tabla 1 en la
  impresa 9 → PDF 26; Tabla 41 en la impresa 121 → PDF 138.
- **Localización de cada tabla**: se toma el ancla del pie (`Tabla N.` a 10,91 pt, el
  cuerpo de la prosa es 11,96 pt, lo que descarta las menciones en texto corrido) y se le
  asignan los filetes horizontales (`\toprule`/`\midrule`/`\bottomrule`) que caen entre ese
  ancla y el ancla siguiente. El **cuerpo** de la tabla es la banda entre el primer y el
  último filete; la **nota** es la banda de 18 pt por debajo del `\bottomrule`. Las dos se
  miden por separado, porque mezclarlas es lo que produce cifras infladas.
- **Tamaños de fuente**: `size` por glifo, no la orden LaTeX declarada. Las equivalencias
  reales medidas en este documento son `\normalsize`=11,96 · `\small`=10,91 ·
  `\footnotesize`=9,96 · `\scriptsize`=7,97 · `\tiny`=5,98 pt, y la macro de la casa
  `\viutablefont` (`viu-mrob-thesis.sty:353`, `\fontsize{9}{10.5}`) = **8,97 pt**.
- **Recompilación concurrente.** A mitad de la auditoría el PDF fue reconstruido por otro
  proceso. Todas las mediciones se repitieron sobre el artefacto resultante
  (`sha256:200d40d9d2e0141e…`, 2 904 276 bytes, 146 páginas, 41 tablas) y **ninguna cifra
  cambió**. Las tablas de abajo valen para ambas compilaciones.

---

## 1. Tablas (bloque 45)

### 1.1 Corrección de la auditoría anterior

`03-fases-y-deposito.md` (líneas 886–888, 1649) afirma «**9 222 caracteres bajo 7 pt**,
hasta **2,6 pt**; **12 tablas** con `\resizebox`». Medido de nuevo, por separado:

| Afirmación previa | Medición propia | Veredicto |
|---|---|---|
| 9 222 caracteres bajo 7 pt | **9 669** en todo el documento (242 782 glifos totales) | cifra previa **baja**, y además **no es de las tablas** |
| — | **1 361** dentro del *cuerpo* de las 41 tablas; **1 583** si se suman las notas bajo el `\bottomrule` | el 86 % del texto microscópico está en **figuras**, no en tablas |
| glifo mínimo 2,6 pt | **0,98 pt** en el documento (PDF 54 = impresa 37, dentro de una figura); **3,79 pt** dentro de una tabla (T14, un subíndice de subíndice); el mínimo de *texto de tabla* legible como tal es **4,88 pt** (cabeceras de la Tabla 5) | los 2,6 pt proceden del **suplemento** (`05-suplementario.md:533`, Fig. 8), no de `main-v2.pdf` |
| 12 tablas con `\resizebox` | **12**, confirmado: T10, T13, T15, T16, T18, T31, T32, T34, T35, T37, T39, T41 | **correcto en el número, invertido en la conclusión** |

**La conclusión sobre `\resizebox` está al revés.** Los tamaños medidos dentro de esas doce
tablas son 8,28 · 9,46 · 9,53 · 9,86 · 9,99 · 10,30 · 10,46 pt: **ninguna baja de 8 pt**, y
ocho de las doce están *ampliadas* respecto de su tamaño nominal (`\resizebox{\textwidth}{!}`
sobre una tabla más estrecha que la caja **agranda** la letra: T15 pasa de `\scriptsize`
7,97 a 9,86 pt, factor 1,24). El texto diminuto del documento no lo produce `\resizebox`:
lo producen las órdenes `\fontsize` y `\scriptsize` escritas a mano dentro de `tabularx`.
Reducir los `\resizebox` **empeoraría** la legibilidad de las tablas de resultados.

### 1.2 Origen real de la letra pequeña

| Orden en el fuente | Fichero | pt medidos | Tablas |
|---|---|---|---|
| `\fontsize{4.9}{5.2}` (cabeceras) | `sections/v2/floats/ind-tab-matrix.tex:20-25` | **4,88** | T5 |
| `\fontsize{6.95}{7.65}` | `sections/v2/floats/ind-tab-standards.tex:9` | **6,92** | T29 |
| `\fontsize{7.35}{8.10}` | `sections/v2/floats/ind-tab-matrix.tex:14` | **7,32** | T5 (cuerpo) |
| `\fontsize{7.0}{7.8}` (leyenda) | `sections/v2/floats/lit-tab-prior-art.tex:24` | **6,97** | T28 (nota) |
| `\fontsize{7.6}{8.6}` | `sp1-compact.tex:123`, `sp2-compact.tex`, `sp3-compact.tex`, `lit-tab-corpus-layers.tex:8`, `lit-tab-prior-art.tex:9` | **7,57** | T9, T12, T14, T17, T26, T28 |
| `\scriptsize` | `03-hypotheses.tex:67`, `04-methodology.tex:407`, `method-comparison.tex:8`, `thesis-results-v2.tex:92`, `07-conclusions-v2.tex:100`, `conclusions-megajuego-addendum.tex:28` | **7,97** | T1, T3, T4, T23, T24, T25 |
| `\fontsize{8.5}{10}` | `results-review.tex:48`, `appendix-review-full-detail.tex:26` | **8,47** | T8, T27 |
| `\viutablefont` (norma de la casa, 9 pt) | `viu-mrob-thesis.sty:353` | **8,97** | T6, T7, T11, T19, T20, T21, T22, T30, T33, T36, T40 |

El umbral del propio repositorio es **≥ 8 pt al tamaño final, ideal 9–10**
(`guidelines/05-checklist-por-fases.md:603`; `guidelines/03-figuras-y-calidad-grafica.md:91-92`).
**14 de 41 tablas** quedan en 8 pt o por debajo; **8 de 41** quedan estrictamente por debajo
de 7,6 pt. Sólo 11 tablas usan la macro de la casa.

### 1.3 Tabla de medición, las 41 tablas

`mín`/`med` = glifo menor y mediano **del cuerpo** (entre `\toprule` y `\bottomrule`) ·
`<7pt` = glifos del cuerpo por debajo de 7 pt ·
`RB` = dentro de `\resizebox` · `Margen` = invasión de la caja de texto en pt (positivo = invade) ·
`Fte.` = declara fuente · `Cit.` = referenciada con `\ref` en alguno de los 89 ficheros ·
`n` = declara el tamaño muestral allí donde publica una tasa (`col` = columna, `pie` = en el pie, `—` = no aplica).

| # | Impr. | PDF | mín | med | máx | <7pt | RB | Margen | Fte. | Cit. | n | Incumple |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 9 | 26 | **7,97** | 7,97 | 7,97 | 0 | — | — | sí | sí | — | letra <8 pt; celda-prosa (1 058 car., 1,1 % dígitos) |
| 2 | 14 | 31 | 9,96 | 9,96 | 9,96 | 0 | — | der **+1,66** | sí | sí | — | desborda caja |
| 3 | 16 | 33 | **7,97** | 7,97 | 7,97 | 0 | — | der +1,33 | sí | sí | — | letra <8 pt; desborda; celda-prosa (1 171 car.) |
| 4 | 17 | 34 | **7,97** | 7,97 | 7,97 | 0 | — | der +1,33 | sí | sí | — | letra <8 pt; desborda; celda-prosa (1 019 car.) |
| 5 | 33 | 50 | **4,88** | 7,32 | 7,32 | **323** | — | izq +0,23 / der +1,29 | sí | sí | — | **cabeceras a 4,88 pt**; letra <8 pt; desborda; 2 159 car. |
| 6 | 35 | 52 | 8,97 | 8,97 | 8,97 | 0 | — | — | sí | sí | — | celda-prosa (949 car., 0,2 % dígitos) |
| 7 | 36 | 53 | 8,97 | 8,97 | 8,97 | 0 | — | — | sí | sí | — | **PASA** |
| 8 | 41 | 58 | 8,47 | 8,47 | 8,47 | 0 | — | — | sí | sí | — | celda-prosa (958 car.) |
| 9 | 44 | 61 | **5,30** | 7,57 | 7,57 | 1 | — | — | sí | sí | — | letra <8 pt |
| 10 | 44 | 61 | 9,99 | 9,99 | 9,99 | 0 | **RB** | — | sí | **no** | pie | **sin `\ref`**; sin IC ni p |
| 11 | 46 | 63 | 8,97 | 8,97 | 8,97 | 0 | — | — | sí | **no** | pie | **sin `\ref`**; sin IC ni p; página casi vacía (4,3 % de tinta) |
| 12 | 48 | 65 | **5,30** | 7,57 | 7,57 | 12 | — | — | sí | sí | — | letra <8 pt |
| 13 | 48 | 65 | 10,30 | 10,30 | 10,30 | 0 | **RB** | — | sí | sí | **col** | sin IC ni p; **duplicada en T34** |
| 14 | 49 | 66 | **3,79** | 7,57 | 7,57 | 12 | — | — | sí | sí | — | letra <8 pt; mínimo global de tabla |
| 15 | 49 | 66 | 9,86 | 9,86 | 9,86 | 0 | **RB** | — | sí | **no** | pie | **sin `\ref`**; sin IC ni p; **duplicada en T37** |
| 16 | 50 | 67 | 8,28 | 8,28 | 8,28 | 0 | **RB** | — | sí | **no** | **col** | **sin `\ref`**; **coma decimal** (única con T39); **duplicada en T39** |
| 17 | 52 | 69 | **5,30** | 7,57 | 7,57 | 9 | — | — | sí | sí | — | letra <8 pt |
| 18 | 52 | 69 | 9,46 | 9,46 | 9,46 | 0 | **RB** | — | sí | **no** | pie | **sin `\ref`**; sin IC ni p; sin unidad en «Terminación»/«Espera»; **duplicada en T41** |
| 19 | 53 | 70 | 8,97 | 8,97 | 8,97 | 0 | — | — | sí | sí | — | **PASA** |
| 20 | 57 | 74 | **5,98** | 8,97 | 8,97 | 3 | — | — | sí | sí | **no** | publica «+1,49 %» **sin n**; «62,83» sin unidad |
| 21 | 59 | 76 | 8,97 | 8,97 | 8,97 | 0 | — | — | sí | sí | **no** | dos ejecuciones, **sin n declarado** |
| 22 | 60 | 77 | 8,97 | 8,97 | 8,97 | 0 | — | — | sí | sí | — | **PASA** |
| 23 | 62 | 79 | **5,98** | 7,97 | 7,97 | 4 | — | der +1,32 | sí | sí | — | letra <8 pt; desborda; celda-prosa (1 092 car.) |
| 24 | 65 | 82 | **5,98** | 7,97 | 7,97 | 9 | — | der +1,33 | sí | sí | — | letra <8 pt; desborda; celda-prosa (1 165 car.) |
| 25 | 67 | 84 | **5,98** | 7,97 | 7,97 | 3 | — | der +1,32 | sí | **no** | — | **sin `\ref`**; letra <8 pt; desborda |
| 26 | 89 | 106 | **7,57** | 7,57 | 7,57 | 0 | — | der +0,04 | sí | sí | — | letra <8 pt |
| 27 | 89 | 106 | 8,47 | 8,47 | 8,47 | 0 | — | — | sí | **no** | — | **sin `\ref`**; celda-prosa (985 car.) |
| 28 | 92 | 109 | **7,57** | 7,57 | 7,57 | 0 (nota **222** a 6,97) | — | izq +0,25 | sí | sí | — | letra <8 pt; **leyenda a 6,97 pt** |
| 29 | 93 | 110 | **6,92** | 6,92 | 6,92 | **982** | — | der +0,87 | sí | sí | — | **tabla entera a 6,92 pt**; 100 % del cuerpo bajo 7 pt; desborda |
| 30 | 100 | 117 | 8,97 | 8,97 | 8,97 | 0 | — | — | sí | sí | — | **PASA** |
| 31 | 101 | 118 | 9,53 | 9,53 | 9,53 | 0 | **RB** | — | sí | sí | pie | sin IC ni p |
| 32 | 101 | 118 | 9,99 | 9,99 | 9,99 | 0 | **RB** | — | sí | sí | **no** | publica cuatro tasas **sin n en ningún sitio**; **duplicada de T10** |
| 33 | 106 | 123 | 8,97 | 8,97 | 8,97 | 0 | — | — | sí | sí | — | **PASA** |
| 34 | 106 | 123 | 10,30 | 10,30 | 10,30 | 0 | **RB** | — | sí | sí | **col** | sin IC ni p; **duplicada de T13** |
| 35 | 107 | 124 | **6,97** | 10,46 | 10,46 | 1 | **RB** | — | sí | sí | **col** | sin IC ni p |
| 36 | 111 | 128 | **5,98** | 8,97 | 8,97 | 1 | — | — | sí | sí | — | **PASA** (salvo un subíndice) |
| 37 | 111 | 128 | 9,86 | 9,86 | 9,86 | 0 | **RB** | — | sí | sí | pie | sin IC ni p; **duplicada de T15** |
| 38 | 115 | 132 | 10,91 | 10,91 | 10,91 | 0 | — | — | sí | sí | — | **PASA** |
| 39 | 116 | 133 | 8,28 | 8,28 | 8,28 | 0 | **RB** | — | sí | sí | **col** | **coma decimal** frente al punto del resto; **duplicada de T16** |
| 40 | 121 | 138 | **5,98** | 8,97 | 8,97 | 1 | — | — | sí | sí | — | **PASA** (salvo un subíndice) |
| 41 | 121 | 138 | 9,46 | 9,46 | 9,46 | 0 | **RB** | — | sí | sí | pie | sin IC ni p; sin unidad en «Terminación»/«Espera»; **duplicada de T18** |

Totales: **1 361** glifos bajo 7 pt en los cuerpos, **222** más en la nota de T28.
**10 tablas desbordan la caja de texto**, con un máximo de **1,66 pt (0,59 mm)** en T2 —
invasiones reales pero de orden submilimétrico, muy por debajo de las que registran las figuras.

### 1.4 Lo que la medición aprueba

Conviene decirlo, porque tres de los ítems del bloque 45 se cumplen sin excepción:

- **Columnas alineadas.** En T13, T15, T16, T31, T35 y T41 se midió el borde derecho de
  cada celda numérica: **dispersión 0,0 pt** en las 31 columnas comprobadas, con el mismo
  número de decimales en toda la columna. Alineación decimal impecable.
- **Fuente declarada: 41/41.** Todas las tablas cierran con `\viusource`
  (`viu-mrob-thesis.sty:222`), que imprime «Fuente: …» en cursiva a 9,96 pt. Trece
  declaran el guion o el script concreto (`simulate_e2e_megagame.py`,
  `run_sp4_v4_coppelia_paired_scene.py`, «datos procesados de E2»…).
- **Ninguna tabla se parte entre páginas.** Las 41 caben íntegras en una página; cada una
  tiene exactamente tres filetes (T5 cuatro, por un `\cmidrule`). El ítem «no dividir
  incómodamente entre páginas» se cumple al 100 %.

### 1.5 Los cuatro fallos duros de las tablas

**(a) Ninguna tabla publica intervalo de confianza, dispersión ni valor p.** Las 41, sin
excepción. Trece tablas de resultados publican tasas con tres decimales
(`0,167`, `0,750`, `0,997`) como si fueran valores exactos. El criterio 45 exige
explícitamente «IC» y «p cuando corresponde», y la metodología declara mundos pareados
—es decir, el contraste pareado está disponible y no se reporta. Es el incumplimiento
más grave de este bloque, y no se arregla con tipografía.

**(b) Cinco tablas están duplicadas palabra por palabra.** Verificado comparando el texto
normalizado del cuerpo:

| Copia en el cuerpo | Copia en el anexo | Contenido |
|---|---|---|
| T10 (impresa 44) | T32 (impresa 101) | Ablación plana/marginal E2 |
| T13 (impresa 48) | T34 (impresa 106) | Acoplamiento dinámico E4 |
| T15 (impresa 49) | T37 (impresa 111) | Recuperación E6-C |
| T16 (impresa 50) | T39 (impresa 116) | Demostrador Cargo |
| T18 (impresa 52) | T41 (impresa 121) | Rutas y reserva E7-C |

Son los mismos números, las mismas columnas y las mismas filas. El bloque 50 prohíbe
«repetir resultados extensos» en los anexos. Y al duplicar, T32 **perdió el n**: el pie de
T10 dice «(1560 mundos)» y el de T32 no dice nada, de modo que la copia del anexo publica
cuatro tasas sin denominador en ningún sitio del documento.

**(c) Siete tablas no están citadas en el texto.** Ningún `\ref`, `\autoref` ni `\cref`
apunta a ellas en los 89 ficheros compilados:

| Tabla | Etiqueta | Definida en |
|---|---|---|
| T10 | `tab:sp1-compact-e2-ablation` | `sections/v2/sp1-compact.tex:145` |
| T11 | `tab:sp3-results` | `sections/sp1-wrench-condensed.tex:57` |
| T15 | `tab:sp2-compact-e6-results` | `sections/v2/sp2-compact.tex:154` |
| T16 | `tab:sp2-compact-cargo-results` | `sections/v2/sp2-compact.tex:202` |
| T18 | `tab:sp3-compact-e7-results` | `sections/v2/sp3-compact.tex:89` |
| T25 | `tab:conclusion-hypothesis-h6` | `sections/v2/conclusions-megajuego-addendum.tex:28` |
| T27 | `tab:method-review-protocol` | `sections/v2/appendix-review-full-detail.tex:22` |

Las cinco primeras son **tablas de resultados**: el lector llega a ellas sin que el texto se
las anuncie. T11 además ocupa ella sola una página al 4,3 % de tinta (impresa 46).

**(d) La página xvi promete algo que las tablas no hacen.** La «Guía de lectura» afirma
que «las tablas distinguen explícitamente los oráculos globales de los mecanismos
distribuidos». No lo hacen: en T15/T37 el «Oráculo exacto» es una fila más; en T18/T41 el
«Oráculo restringido» es una fila más; en T31 el «Oráculo de puntuación» y la «Referencia
de cobertura» son filas más. No hay columna de clase, ni `\cmidrule` separador, ni marca
tipográfica: las 41 tablas tienen tres filetes y ninguno separa oráculos de métodos. La
distinción existe sólo en la redacción de la etiqueta de fila.

### 1.6 Defectos menores, con su localización

- **Separador decimal mixto.** T16 y T39 usan coma decimal (30 ocurrencias cada una,
  correcto en español); las otras 16 tablas con cifras usan punto (`0.750`, `1.000`,
  `40.84`). El documento es en español y la convención se aplica en el 11 % de las tablas.
- **Unidades ausentes.** T18/T41 publican «Terminación 7,49» y «Espera 2,82» sin unidad
  (son pasos discretos, declarado sólo en la prosa de la impresa 120). T20 publica un
  coste «62,83» sin unidad. T13/T31/T34/T35/T39 sí declaran `[ms]`, `[s]`, `[m]`, `[°]`, `[J]`.
- **Prosa dentro de celdas.** Doce tablas tienen menos del 2 % de dígitos y más de 900
  caracteres: T1 (1 058), T3 (1 171), T4 (1 019), T5 (2 159), T6 (949), T8 (958),
  T23 (1 092), T24 (1 165), T27 (985), T29 (999), más T12 y T17. Son bloques de texto con
  filetes, y son exactamente las que están compuestas a 7,57–7,97 pt: la letra pequeña es
  la consecuencia de meter párrafos en celdas, no la causa.
- **Una tabla sin número.** La «Clave de estados empleada en la memoria» de la página xvi
  (`sections/frontmatter-evidence-key.tex:10`) es un entorno `table` con `tabularx` y
  filetes, pero sin `\caption` ni `\label`: no lleva número, no entra en el Índice de
  tablas y no se puede referenciar.
- **Dos entornos `table` muertos en ficheros activos.**
  `sections/source-snapshot/mainmatter/04-methodology.tex:261` (`tab:method_sp_contribution_validation`,
  61 líneas) y `sections/v2/support/cargo-e2e-v2.tex:81` (`tab:cargo-sp-mapping`, 24 líneas)
  están encerrados en `\iffalse`. Ocupan 85 líneas de fuente compilado, definen etiquetas
  que nadie puede resolver y no imprimen nada.

---

## 2. Notación matemática (bloque 24)

Alcance: los **89 ficheros compilados**, no los ~460 del repositorio. La lista canónica del
proyecto es `docs/05_NOTATION.md` (441 filas y siete reglas explícitas en las líneas 452–458).
Hay **72 bloques de matemática desplegada**, repartidos en sólo 19 de los 89 ficheros.

### 2.1 «Un símbolo, un significado»: el caso `z`

El hallazgo previo decía que `z` arrastra al menos ocho significados en el repositorio, dos
de ellos literalmente `z_k`. Restringido a lo que **sobrevive al documento compilado**:
**siete clases semánticas, y tres de ellas subindizadas por `k`** —una más de las dos
anunciadas.

| Significado | Fichero:línea | Fragmento |
|---|---|---|
| escalar mudo de la parte positiva | `05-theoretical-framework.tex:66` | `$[z]_+=\max\{z,0\}$` |
| variable continua de decisión del bloque | `sections/v2/megajuego-compact.tex:55` | `$\Phi(d,z)=\sum_i\phi_i(z_i)+\sum_a\psi_a(z_{\mathcal I_a})$` |
| vector de fuerzas de contacto del QP de *caging*, `z∈ℝ⁸` | `sections/v2/megajuego-compact.tex:98` | `$\min_z\tfrac12z^{\mathsf T}z$ s.a. `$Az=(20,0,5)^{\mathsf T}$` |
| sustitución auxiliar de Bézier, `z=(2s−1)²` | `sections/v2/appendix-megajuego-detail.tex:40` | `Sea $z=(2s-1)^2\in[0,1]$` |
| **`z_k` binaria** de compleción todo-o-nada (MILP de E2) | `sections/v2/support/sp1-e2-trimmed.tex:73` | `$x_{ik},z_k\in\{0,1\}$` |
| **`z_{2,k}(\rho)`** salida estratégica regulada (déficit de servicio normalizado); familia con `z_4^S`, `z_4^L`, `z_7^S` | `sections/v2/support/sp1-e2-trimmed.tex:123` | `$z_{2,k}(\rho)=[1-S_k(\rho)/d_k^{\mathrm{srv}}]_+$` |
| **`z_k` coordenadas de pose de la carga**, adimensionalizadas | `sections/source-snapshot/appendices/06-sp4-proofs.tex:67` | `$q_k^L=S_qz_k$, con $S_q=\operatorname{diag}(\ell_0,\ell_0,1)$` |

Las dos peores son la quinta y la séptima: **ambas son `z_k`, ambas van indexadas por el
índice de carga, ambas están en los anexos y las separan diecisiete páginas impresas**, sin
una sola nota cruzada. Una es un entero `{0,1}`; la otra es un vector de ℝ³ en metros.

La memoria **reconoce el problema a medias**: `sections/v2/04-nomenclature-megajuego-v2.tex:9`
dice «*el mismo símbolo designa las fuerzas de contacto en el QP de caging y una sustitución
auxiliar en la prueba de Bézier, y cada uso se define en su punto de aparición*». Declara
tres de los siete usos y calla los tres `z_k`, que son justamente los que colisionan.

Los ocho significados restantes de `z` que registra `docs/05_NOTATION.md` (registro versionado
de cuotas `:122`, salida regulada SP0 `:208`, error de cierre SP1 `:209`, error de *wrench*
SP3 `:211`, barrido LiDAR `:281`, estado integral LQI `:320`, residuo de barrera muestreado
`:381`, coordenada del mapa bibliométrico `:429`) **no aparecen en el documento compilado**.

### 2.2 Los demás símbolos que el criterio 24 señala por nombre, y el resto

El criterio pide evitar reutilizar `z, ρ, λ, S, R, K`. Los seis están reutilizados:

| Símbolo | Significados activos | Caso más agudo |
|---|---|---|
| **`R`** | **7** + 5 caligráficos | radio de comunicación escrito `R` en la figura y `R_c` en `04-methodology.tex:33`; matriz de peso del LQR en `sp2-e4-trimmed.tex:16`; matriz de rotación `R(\theta_L)` en `sp2-canonical-bridge.tex:9`; radio de la carga `R=0{,}45` m en `appendix-megajuego-detail.tex:116` |
| **`λ`** | **5** | esfuerzo de contacto `\boldsymbol\lambda_k` (N, `04-methodology.tex:134`) y peso de penalización adimensional `\lambda` (`sp1-compact.tex:52`) **conviven dentro de SP1** |
| **`S`** | **5** | `S_k(x)` servicio agregado (`sp1-compact.tex:79`) y `S` = número de puestos (`sp1-e2-trimmed.tex:81`) **en el mismo fichero** |
| **`K`** | **4** | `K` = número de cargas (`04-nomenclature.tex:7`) y `K` = conjunto factible convexo (`04-nomenclature-megajuego-v2.tex:12`): **los dos declarados en el front matter, en ficheros que se `\input` consecutivamente** (`main-v2.tex:78-79`) |
| **`ρ`** | **4** | preferencia continua `\rho_{ik}` (`sp1-e2-trimmed.tex:89`) y residuo mecánico `\rho_k^{W\star}` (`sp1-wrench-condensed.tex:18`) a **29 líneas de distancia, en el mismo apartado** |

Y el barrido encuentra bastantes más. Los que importan, por gravedad:

| Símbolo | Significado A | Significado B | Por qué es grave |
|---|---|---|---|
| `u_i` | **entrada de control**, `04-nomenclature.tex:11` | **utilidad**, `05-theoretical-framework.tex:25,49` | el significado declarado **no se usa nunca**; el usado **no se declara nunca** |
| `\mathcal L` | **conjunto de cargas** (macro `\Loads`, `config/math-commands.tex:4`, usada en `04-methodology.tex:23`) | **lagrangiano**, `sp2-e4-trimmed.tex:88` | una macro del proyecto contra un operador estándar |
| `\tau_d` | **retardo de comunicación** (s), `04-nomenclature.tex:29` | **par demandado** (N·m), `sp2-canonical-bridge.tex:56,60` | mismo glifo, dos sistemas de unidades |
| `\Delta_i` | **símplex del robot** `i`, `sp1-wrench-condensed.tex:47` | **operador de desviación unilateral**, `04-nomenclature-megajuego-v2.tex:11` | glifo idéntico, uno declarado y otro no |
| `\mathcal U` | fuerzas de contacto admisibles `\mathcal U_{\mathcal C_k}` | límites de actuación `\mathcal U_i` | **aparecen en la misma ecuación desplegada**, `sp2-e4-trimmed.tex:28-29` |
| `F_i` | protocolo de revisión (Smith/BNN/replicator), `sp1-e2-trimmed.tex:140` | campo vectorial del uniciclo, `sp2-e4-trimmed.tex:25` | ambos `F_i`, ambos en anexos |
| `k` | **índice de carga** (índice primario del documento) | índice de estrategia poblacional (`tf:59-62`), índice de coalición (`thesis-results-v2.tex:69`), índice de tubo (`appendix-megajuego-detail.tex:184`) | no es reutilización benigna de índice: es el índice rector, reasignado tres veces sin aviso |
| `\ell`, `r`, `d`, `s`, `P` | **7 significados cada uno** | | `r_k` = ratio de cobertura escalar (`sp1-e2-trimmed.tex:89`) contra la regla `docs/05_NOTATION.md:453`, que reserva `r_k` para requisitos multidimensionales |
| `m` / `M` | índice de iteración, masa `m_k^{\mathrm{req}}`, margen `m_j`, matriz de inercia `M_k`, coste soporte `M` | | contradice directamente `docs/05_NOTATION.md:452` («no usar el mismo símbolo para masa, número de robots y mensaje») |

Reutilización **benigna** (registrada para no inflar la cuenta): `i`, `j` como índices
genéricos; `\omega` para velocidad angular de robot y de carga (misma magnitud física);
`\Phi`, `\Phi_1`, `\Phi_6`, `\Phi_7` siempre «potencial exacto»; `\alpha_4`, `\beta_4`
siempre pesos de E4; y `x_{ik}` binaria frente a `x_k` masa poblacional, que sí están
correctamente separadas conforme a `docs/05_NOTATION.md:456`.

### 2.3 El defecto inverso: un objeto, varios símbolos

Tan dañino como lo anterior, y menos visible:

| Objeto | Grafías en el documento compilado |
|---|---|
| matriz de agarre | `G_C(q)` (`tf:202`), `G_{\mathcal C_k}(q)` (`04-methodology.tex:129`), `G_{C_k}` (`sp2-compact.tex:60`), `G_k` (`sp1-wrench-condensed.tex:16`) — **cuatro** |
| *wrench* demandado | `W_k^d`, `\boldsymbol W_k^{\mathrm{dem}}`, `\boldsymbol W_k^{\mathrm{req}}`, `W_C` — **cuatro** |
| coalición | `\mathcal C_k`, `C_k`, `\mathcal C`, `C` — **cuatro** |
| fuerzas de contacto admisibles | `\mathcal U_C`, `\mathcal U_{\mathcal C_k}`, `\Lambda_k` — **tres** |
| residuo de *wrench* | `\rho_k^{W,\min}`, `\rho_k^{W\star}`, `\rho_k^W` — **tres** |
| conjunto de cargas | `\mathcal L` y `\mathcal K` — **dos** |
| proyección al símplex | `P_{\Delta_i}` y `\Pi_{\Delta_3}` — **dos** |
| radio de comunicación | `R` y `R_c` — **dos** |
| mejora mínima | `\delta_{min}` (recto) en `sp2-e6-trimmed.tex:66` y `\delta_{\min}` en `:74` — **dos, en el mismo fichero** |

En `sp2-e6-trimmed.tex:66` hay además `min_{\boldsymbol x:\ldots}` compuesto en cursiva en
lugar de `\min`: un error tipográfico dentro de una ecuación numerada.

### 2.4 Símbolos usados antes de definirse

Orden de documento tomado de la cadena de `\input` de `main-v2.tex`. **62 símbolos distintos
llegan a una ecuación desplegada antes de tener definición; 29 de ellos no se definen nunca
en los 89 ficheros.**

Los tres peores, con nombre y apellidos:

1. **`sections/sp1-wrench-condensed.tex:46-50`**, ecuación numerada `eq:sp3-digital-update`:
   ```
   \rho_i^{m+1}=P_{\Delta_i}(\rho_i^m+\Delta t\,F_i),\qquad
   \pi_a^{m+1}=[\pi_a^m+\Delta t_\pi h_a(\rho^m)]_+,
   ```
   **Siete símbolos sin definir en ese punto** (`\rho_i`, `P_{\Delta_i}`, `\Delta_i`, `F_i`,
   `m`, `\pi_a`, `\Delta t_\pi`, `h_a`), y **seis de ellos no se definen en ninguna parte**.
   La prosa que la sigue (`:51-52`) sólo dice que «proyecta `\rho_i` sobre el símplex».

2. **`sections/results-interface.tex:44-51`**, ecuación numerada `eq:pre-results-go-contract`:
   `\mathsf{GO}_k = \mathsf{CLOSE}_k \land \mathsf{SUPPORT}_k \land \mathsf{WRENCH}_k \land
   \mathsf{WHEELS}_k \land \mathsf{CONTACT}_k \land \mathsf{ROUTE}_k`.
   **Cada uno de los seis predicados aparece exactamente una vez en los 89 ficheros: dentro
   de esta ecuación.** Es una ecuación numerada cuyos seis átomos son indefinidos, y de ella
   cuelga el contrato de autorización ejecutable del capítulo de resultados.

3. **`04-methodology.tex:132-143`**, `eq:method_cargo_certificate_control`: seis infractores
   (`\boldsymbol\lambda_k`, `\mathcal U_{\mathcal C_k}`, `\epsilon_W`, `K_P`, `K_D`, `e_k^L`);
   cuatro esperan al Capítulo 5 o al anexo y tres (`\epsilon_W`, `K_P`, `K_D`) no llegan nunca.

También `sections/v2/sp2-compact.tex:59-64`: `M_k`, `D_k` y `\bar\lambda` sostienen el teorema
de estabilidad local de Lyapunov y ninguno se define (sólo se les impone `\succ0`).

**La causa es estructural, no descuido disperso.** Los ficheros compactados de la v2
(`sp1-compact.tex`, `sp2-compact.tex`, `sp3-compact.tex`, `megajuego-compact.tex`) empujaron
sus definiciones a `sections/v2/support/*-trimmed.tex` y `sections/v2/appendix-*-detail.tex`,
que se `\input` **entre 30 y 40 ficheros después**. La compactación de la v2 convirtió
definiciones locales en referencias hacia adelante. Casos medidos: `\mathcal L` se usa en
`04-methodology.tex:23` y se define en `:403`, **380 líneas más tarde**;
`\bar\tau_d,\bar\tau_a,\tau_s,\ell_i,v_i^{\min}` se usan en `thesis-appendices.tex:35-37` y
se definen en `sp2-e6-trimmed.tex:105`, **diecisiete ficheros después en la cadena**.

### 2.5 Nomenclatura: lo que sobra y lo que falta

La nomenclatura son 79 entradas repartidas en dos ficheros
(`04-nomenclature.tex`, 66; `04-nomenclature-megajuego-v2.tex`, 13) y cuatro páginas impresas.

**(a) Entradas muertas — declaradas y nunca usadas en el cuerpo activo: 25 de 79 (32 %).**
Comprobado contando ocurrencias en los 89 ficheros:

| Entrada | Declarada en | Ocurrencias fuera de la nomenclatura |
|---|---|---|
| **`\mu_i(t)`** — tasa local de revisión estratégica | `04-nomenclature.tex:26` | **0** (la única otra `\mu` del corpus es un prefijo de unidad en `ind-tab-matrix.tex:74`) |
| `\Psi(\delta_{ik})` — descuento espacial | `:25` | **0** |
| `\sigma_i` — modo local de misión | `:14` | **0** |
| `G(t)` — grafo de comunicación | `:27` | **0** (el cuerpo escribe `\mathcal G_c(t)`) |
| `p_{\mathrm{loss}}` — probabilidad de pérdida | `:29` | **0** |
| `X`, `\mathcal B_N` — asignación relajada y politopo de Birkhoff | `:33` | **0** con ese significado |
| `\gamma`, `\tau`, `\rho` (ganancias primal–dual) | `:34` | **0** |
| `\widetilde\kappa_{ik}`, `w_k`, `t_m`, `\pi_k`, `\mathcal G_A`, `\mathcal G_C`, `e_\pi^t`, `q`, `R^\star`, `T_{\mathrm{coal}}` | `:23-36` | **0** |
| `h_j`, `v_k^{\mathrm{fil}}`, `W_k^{\mathrm{nom/fil/apl}}`, `\varepsilon_{\mathrm{act}}` (bloque E5) | `:44-46` | **0** |
| `\mathcal E_{ir}^8`, `G_C^8` (bloque E8) | `:49` | **0** (no existe ningún superíndice `^8` en el corpus activo) |

El patrón es nítido: **los bloques E0/SP0 (líneas 33–36), E5 (44–46) y E8 (49) son residuo
histórico completo**. El propio `04-methodology.tex:405` dice que «E0, E1, E5 y E8 permanecen
como procedencia… no como evidencia»; la nomenclatura no se actualizó en consecuencia.

Merece subrayarse `\mu_i(t)`: la tasa de revisión modulada es la pieza que da nombre al
método propuesto en el encuadre del proyecto, y en el documento compilado **existe sólo como
una línea de la nomenclatura**.

**(b) Símbolos del cuerpo ausentes de la nomenclatura: ≥ 96.** Entre ellos, todos los que
sostienen resultados formales: `K_P`, `K_D`, `M_k`, `D_k`, `e_k^L`, `\epsilon_W`, `G_k`,
`\Lambda_k`, `\boldsymbol\lambda_k`, `\boldsymbol r_k^W`, `S_q`, `\lambda_D`, `\ell_0`,
`\succeq`, los seis predicados `\mathsf{GO}`, las familias completas de E4 (`c_{ia}^{(4)}`,
`b_{ia\ell}`, `y_\ell`, `\pi_\ell`, `h_\rho`, `h_\pi`, `z_4^S`, `z_4^L`), de E6 (`n_R`, `A_6`,
`\kappa_i^6`, `\kappa_{\max}^6`, `w_a`, `K_6`, `\operatorname{PoS}_6`, `\operatorname{PoA}_6`)
y de E7 (`\mathcal E_7`, `\lambda_7`, `n_e`, `B_7`, `\Phi_7`, `H_7`, `\theta_7`, `z_7^S`).

**Cobertura neta: ~54 de ~150 símbolos matemáticos vivos ≈ 36 %.** La nomenclatura describe
un documento que ya no es este.

**(c) Higiene de macros.** `config/math-commands.tex` define ocho macros; `\Neighbors`,
`\positivepart`, `\norm`, `\R`, `\argmax`, `\diag` y `\sat` se usan **cero o una vez** fuera
del propio fichero de configuración, porque el cuerpo escribe a mano `\mathcal N_i`,
`[\cdot]_+`, `\|\cdot\|`, `\mathbb R` y `\operatorname{diag}`. La cabecera del fichero pide
«mantenerlos alineados con `docs/05_NOTATION.md`»; no lo están.

### 2.6 Divergencias frente a `docs/05_NOTATION.md`

| # | La lista canónica dice | Los 89 ficheros hacen | Evidencia |
|---|---|---|---|
| D1 | `:229` `\tau_d` = retardo de comunicación (s) | par demandado (N·m) | `sp2-canonical-bridge.tex:56,60` |
| D2 | `:228` `R` = radio de comunicación | el cuerpo escribe `R_c` (cuarta grafía, ausente de la lista) y reutiliza `R` para el peso LQR y el radio de la carga | `04-methodology.tex:33`; `sp2-e4-trimmed.tex:16`; `appendix-megajuego-detail.tex:116` |
| D3 | `:63` `b_i` = estado de batería ∈[0,1] | `b_i=D/2`, desplazamiento de restricción | `appendix-megajuego-detail.tex:71` |
| D4 | `:275` `\delta` = resolución de rejilla SE(2) | coste de sustitución del teorema de presupuesto | `megajuego-compact.tex:118,126` |
| D5 | `:10` `K` = número de cargas | conjunto factible cerrado y convexo | `megajuego-compact.tex:68` |
| D6 | `:234` `W_k` = *wrench* | presupuesto de ejecución | `megajuego-compact.tex:118` |
| D7 | `:150` `\mathcal L` = lagrangiano | `config/math-commands.tex:4` define `\Loads=\mathcal L` = conjunto de cargas, y `sp2-e4-trimmed.tex:88` lo usa como lagrangiano | **la lista canónica y el fichero de macros del propio proyecto asignan el mismo glifo a dos objetos** |
| D9 | `:400` `\mathcal R_i^7` = catálogo de rutas de la coalición `i` | `\mathcal R_k^7` con `k` = coalición | `thesis-results-v2.tex:69-70`: error de semántica de índice, no sólo de glifo |
| D11 | `:84` `\rho_i^{\mathrm{nav}}`, decoración elegida **expresamente** para separarla de las demás `\rho` | el cuerpo escribe `\rho_i` a secas | `sp2-compact.tex:49` — la desambiguación canónica se perdió |
| D13 | `:452` «no usar el mismo símbolo para masa, número de robots y mensaje» | `m` índice, `m_k^{\mathrm{req}}` masa, `m_j` margen, `M_k` inercia, `M` coste | **violación directa de la regla** |
| D14 | `:453` «usar `r_k` para requisitos multidimensionales» | `r_k=S_k(\rho)/d_k^{\mathrm{srv}}`, un escalar | `sp1-e2-trimmed.tex:89` — **violación directa** |
| D15 | `:54` `u_i` = entrada de control | `u_i` sólo aparece como utilidad | `tf:25,49` |
| D16 | `:76` y `:122` registran dos `z_k` | existe un **tercero** que la lista no recoge (coordenadas de pose) | `06-sp4-proofs.tex:67` |

Cumplimiento de las siete reglas de `docs/05_NOTATION.md:452-458`: **cumplen tres**
(`:454` declaración del tipo de `x_{ik}`, `:456` `x_k` frente a `x_{ik}`, `:458` SI, con
excepciones), **incumplen tres** (`:452` masa/índice, `:453` `r_k`, `:457` convenio único de
marco de referencia y *wrench* —cuatro grafías—), y **una cumple a medias** (`:455`, correcta
en SP1 y derivada en SP2).

Y una advertencia sobre el propio documento canónico: **alrededor de dos tercios de
`docs/05_NOTATION.md` describe campañas que no están en `main-v2.pdf`** (los bloques N4 del
megajuego `:116-161`, SP0 `:160-195`, SLAM/N3 `:280-297`, gobernador `:298-327` y epistémico
`:443-448` tienen **cero ocurrencias** en los 89 ficheros). No lo declara en ninguna parte, lo
que lo hace inseguro como referencia de auditoría de la memoria compilada.

### 2.7 Convenios menores del bloque 24

- **`\Phi` maximizada o minimizada.** El convenio es consistente: `\Phi_1(a)=-\{C(a)+\lambda D(a)+\lambda O(a)\}`
  (`sp1-compact.tex:52`) se **maximiza**, y las cuatro variantes `\Phi`, `\Phi_1`, `\Phi_6`,
  `\Phi_7` son siempre «potencial exacto». **Pasa.**
- **Vectores frente a escalares, negrita.** Inconsistente: `\boldsymbol\lambda_k`,
  `\boldsymbol r_k^W`, `\boldsymbol W_k^{\mathrm{dem}}` llevan negrita, pero `W_k^d`
  (`04-methodology.tex:141`), `e_k^L`, `z_k` (pose, ℝ³) y `q_k^L` no la llevan siendo también
  vectores. El mismo *wrench* aparece con negrita y sin ella en el mismo documento.
- **Transpuesta.** Consistente: `^{\mathsf T}` en todo el corpus.
- **Índices `i,j,k`.** `i` robot y `j` vecino son estables; **`k` no lo es** (§2.2).
- **Unidades SI.** Se cumplen salvo donde un glifo arrastra dos sistemas: `\tau_d` (s / N·m),
  `\delta` (m / unidades de presupuesto), `D` (recuento / N·s·m⁻¹ / m), `\lambda` (N / adimensional).
- **Consistencia principal/suplemento.** Rota por construcción: las definiciones viven en los
  anexos y los enunciados en el cuerpo (§2.4).

---

## 3. Layout y composición visual (bloque 48)

### 3.1 Páginas casi vacías

Tinta = suma de las cajas de los glifos del cuerpo dividida por el área de la caja de texto.
La media del documento es **32,5 %**.

| PDF | Impr. | Tinta | Líneas | Qué hay | Diagnóstico |
|---|---|---|---|---|---|
| **4** | iii | **0,99 %** | **1** | `formation, potential games, cooperative transport` | cola de las *keywords* inglesas, sola en una página |
| **75** | 58 | **1,05 %** | **2** | `thesis/resources/MROB_MegaGame_E2E_bundle/` y, en la línea anterior, un punto suelto | **ruta de fichero que crea una página vacía** |
| **86** | 69 | **2,36 %** | **2** | «…el modelo declarado, lo que basta para exigir una cota continua, no muestreada, / antes de cualquier prueba con hardware.» | cola de párrafo (viuda de dos líneas) |
| **63** | 46 | **4,34 %** | 10 | sólo la Tabla 11, flotada al centro (top 356 pt) | 285 pt de blanco arriba y 294 pt abajo |
| **8** | vii | 6,94 % | 6 | seis líneas del índice (J.1–J.6) | cuarta página del TOC por seis renglones |
| **1** | — | 7,91 % | 9 | portada | normal |
| **10** | ix | 10,22 % | 9 | cola del Índice de figuras (figuras 24–28) | segunda página por cinco entradas |

La **PDF 75** es el caso literal del ítem «rutas de archivo creando páginas vacías» del
criterio 48: la ruta no admite guionado, se empuja a una página nueva y deja el punto final
de la frase huérfano en la línea de arriba, en x = 343,6 pt.

### 3.2 Páginas cuyo contenido es una sola línea

Tres: **PDF 4** (una línea), **PDF 75** (dos, una de ellas un punto aislado) y **PDF 86**
(dos). Ninguna otra página del documento baja de cinco líneas de cuerpo.

### 3.3 Viudas y huérfanas

Detectadas comparando el final de cada página con el principio de la siguiente
(interlineado base 20,8 pt; se considera salto de párrafo un hueco > 24 pt).

**Viudas** (última línea de un párrafo, sola en el alto de la página siguiente) — **8**:

| PDF | Impr. | Línea huérfana en la cabeza de la página | Ancho |
|---|---|---|---|
| 4 | iii | `formation, potential games, cooperative transport` | 260 pt |
| 24 | 7 | `histórica en la monografía; no adjudica H5b en esta memoria.` | 367 pt |
| 31 | 14 | `no compara el juego de reparación de SP2 con otro reasignador.` | 343 pt |
| **37** | **20** | `asignación factible.` | **102 pt** |
| 108 | 91 | `dentro de sus supuestos, en el capítulo de resultados.` | 286 pt |
| 113 | 96 | `aumentar C. Luego ningún perfil inexacto es Nash.` | 270 pt |
| 119 | 102 | `corresponden solo a los mundos evaluados.` | 234 pt |
| **123** | **106** | `en el Anexo C.4.` | **101 pt** |

Las de las impresas 20 y 106 son las peores: una sola línea de ~100 pt de ancho abriendo
la página.

**Huérfanas** (primera línea de un párrafo, sola al pie de la página) — **11**, en las
impresas 8, 22, 23, 64, 82, 92, 109, 110, 120, más dos en el front matter (ii y x, donde
corresponden a la línea `Keywords:` y a una entrada del índice, y no cuentan como defecto
de párrafo). Los casos de cuerpo más visibles:

- PDF 25 / impresa 8: `H4. Reparación. Tras un fallo simple, el juego restaurará el certificado aditivo`
- PDF 99 / impresa 82: `Demostración. Derivar p = p + R(θ)r da la primera igualdad; la restricción no`
- PDF 127 / impresa 110: `Corolario H.1 (cota temporal de reparación). Bajo los supuestos de los Teore-`
- PDF 137 / impresa 120: `Resultados El juego con reserva entregó todas las cargas con tiempo medio`

Abrir una demostración o un corolario en la última línea de una página es el caso que el
criterio 48 señala por nombre.

### 3.4 Encabezados aislados (título seguido de título, sin texto en medio)

Nueve casos, todos en los anexos:

| PDF | Impr. | Título | Título inmediatamente siguiente |
|---|---|---|---|
| 98 | 81 | `B. Demostraciones seleccionadas de SP1` | `B.1. Demostraciones complementarias de la etapa E2 (SP1)` |
| 99 | 82 | `C. Demostraciones seleccionadas de SP2` | `C.1. Puente cinemático–mecánico canónico` |
| 104 | 87 | `E. Demostraciones seleccionadas de SP3` | `E.1. Demostraciones complementarias de la etapa E7 (SP3)` |
| 113 | 96 | `G.2. Servicio operacional heterogéneo (E2)` | `G.2.1. Etapa 1.3: servicio operacional heterogéneo` |
| 119 | 102 | `H.1. Acoplamiento y transporte entre poses (E4)` | `H.1.1. Etapa 2.1: acoplamiento y transporte cooperativo` |
| 124 | 107 | `H.2. Recuperación ante fallo (E6)` | `H.2.1. Etapa 2.3: re-reclutamiento y sustitución tras un fallo` |
| 129 | 112 | `H.3. Demostrador híbrido Cargo` | `H.3.1. Etapa 2.4: demostrador híbrido de la cadena Cargo` |
| 134 | 117 | `I.1. Juego de rutas y reserva local (E7)` | `I.1.1. Etapa 3.1: juego de rutas y reserva local entre coaliciones` |
| 139 | 122 | `I.2. Piloto AWS Industrial` | `I.2.1. Etapa 3.3: piloto AWS Industrial` |

Seis de los nueve son además **redundantes**: el subapartado repite casi literalmente el
título del apartado que lo contiene (`H.2. Recuperación ante fallo (E6)` → `H.2.1. …
re-reclutamiento y sustitución tras un fallo`). No es sólo un problema de composición:
es un nivel de jerarquía que no aporta nada.

### 3.5 Tablas y figuras cortadas

**Ninguna.** Las 41 tablas caben en una página; las 28 figuras tienen su gráfico y su pie
en la misma página. Los únicos filetes que empiezan en el borde superior de una página
(PDF 131 y 137, a 71,3 pt) pertenecen a los **Algoritmos 2 y 3**, que sí se empujan a una
página nueva completa, no a tablas partidas.

### 3.6 Cajas desbordadas

`build-v2/main-v2.log` registra **8 `Overfull \hbox`**, la mayor de **4,80 pt**:

| Línea del log | Exceso |
|---|---|
| 2068, 2075 | 1,09 y 4,33 pt |
| 2430, 2435 | 0,67 y 1,66 pt |
| 2549 | **4,80 pt** |
| 2579 | 4,28 pt |
| 2611 | 1,77 pt |
| 3093 | 2,16 pt |

Ninguna llega al milímetro y medio. Los `Underfull \hbox` son muchos más (más de 60), casi
todos dentro de celdas `tabularx` estrechas y de las líneas cortas de las tablas-prosa: es
el mismo defecto del §1.6 visto desde el log.

### 3.7 Color, jerarquía y tipografía

- **Naranja VIU `#E65113`**: 4 421 glifos en 104 páginas (títulos, `Tabla N.`, `Figura N.`).
  Uso consistente en todo el cuerpo.
- **Tres naranjas más, todos dentro de figuras**: `#9F4A20` (PDF 47) y `#C8572A`
  (PDF 49 y 57). Son 334 glifos en total; corresponde al informe de figuras, se registra
  aquí sólo por completitud.
- **Dos azules**: `#0563C1` en 14 páginas (hipervínculos, coherente) y `#2369BD` en una
  sola (PDF 44, dentro de una figura).
- **Jerarquía de títulos**: exactamente tres niveles — 17,93 pt (capítulo/anexo),
  15,94 pt (sección), 13,95 pt (subsección). Sin niveles fantasma ni saltos.
- **Tipografía**: ArialMT / Arial-Italic / Arial-Bold para 232 633 glifos (cumple
  «Arial 12» de la plantilla VIU), Computer Modern (CMR, CMMI, CMSY, CMEX) para 8 643
  glifos de matemáticas y LM Mono para verbatim. **El tipo matemático no concuerda con el
  del texto**: toda fórmula del documento se compone en Computer Modern dentro de una
  página en Arial. Es la única incoherencia tipográfica sistemática, y afecta a todas las
  ecuaciones y a todos los símbolos en línea.
- **Capa de texto**: 35 glifos de *i sin punto* (U+0131) en el PDF. 31 son la traducción
  automática de `babel-spanish` de `\min` → `mín` (compuesto `m` + `´` + `ı`), que **se ve
  bien** pero se copia y se indexa como `m´ın`; 4 son el emulado de versalitas de Arial
  (`\textsc{Parcial}`, `\textsc{Pendiente}` en la página xvi, `\Call{SiguienteCelda}` en el
  Algoritmo 3), que también se ven bien pero se extraen como `Parcıal`, `Pendıente`,
  `SıguıenteCelda`. No es un defecto visual; sí lo es para búsqueda en el PDF, lectores de
  pantalla y cotejo antiplagio.

---

## 4. Front matter (bloque 49)

### 4.1 Qué ocupa exactamente las 17 páginas

La Introducción empieza en el PDF 18 = impresa 1. Antes hay 17 páginas: la portada sin
numerar más los folios romanos i–xvi.

| PDF | Folio | Contenido | Líneas | Tinta | Qué gana el lector |
|---|---|---|---|---|---|
| 1 | — | Portada VIU (máster, título, autor, tutor, convocatoria) | 9 | 7,9 % | **Obligatoria.** Identifica el trabajo |
| 2 | i | **Resumen**, 281 palabras + «Palabras clave» (5 términos) en la misma página | 30 | 43,2 % | **Cumple**: intervalo 200–300, keywords en la misma página |
| 3 | ii | **Abstract**, 287 palabras + «Keywords» iniciado al pie | 32 | 46,5 % | **Cumple** en extensión; la línea de keywords arranca en la última línea útil |
| **4** | **iii** | **Una línea**: `formation, potential games, cooperative transport` | **1** | **1,0 %** | **Nada.** Una página entera para cuatro términos. Incumple «Keywords en la misma página» |
| 5 | iv | **Contenido**, inicio (Resumen … §5.2) | 28 | 22,6 % | Necesario |
| 6 | v | Contenido (§5.3 … §6) | 30 | 30,5 % | Necesario |
| 7 | vi | Contenido (§6 … anexos A–I) | 30 | 30,5 % | Necesario |
| **8** | **vii** | Contenido, **seis renglones** (J.1–J.6) | **6** | **6,9 %** | Cuarta página por seis líneas. Ajustando interlineado o profundidad entra en tres |
| 9 | viii | **Índice de figuras**, figuras 1–23 | 33 | 38,3 % | Exigido por la plantilla |
| **10** | **ix** | Índice de figuras, **figuras 24–28** | **9** | **10,2 %** | Segunda página por cinco entradas |
| 11 | x | **Índice de tablas**, tablas 1–24 | 33 | 35,6 % | Exigido por la plantilla |
| 12 | xi | Índice de tablas, tablas 25–41 | 23 | 26,4 % | Necesario dado que hay 41 tablas |
| 13 | xii | **Nomenclatura**, inicio | 58 | 26,3 % | Útil: el documento tiene notación densa |
| 14 | xiii | Nomenclatura (cont.) | 66 | 29,6 % | Útil |
| 15 | xiv | Nomenclatura + «Símbolos adicionales del juego de integración (§6.5)» | 40 | 28,3 % | **Un segundo glosario paralelo** para un solo apartado |
| 16 | xv | Símbolos adicionales (cont.) | 35 | 21,0 % | Idem |
| 17 | xvi | **Guía de lectura y niveles de evidencia**: cuatro párrafos, una tabla sin numerar de cuatro estados y un diagrama de cadena | 26 | 27,6 % | Útil en principio; **pero afirma que «las tablas distinguen explícitamente los oráculos globales de los mecanismos distribuidos», y no lo hacen** (§1.5d) |

### 4.2 Veredicto por ítem del criterio 49

| Ítem | Estado |
|---|---|
| Resumen 200–300 palabras | **PASA** — 281 |
| Abstract equivalente | **PASA** — 287 |
| Keywords en la misma página | **FALLA en inglés.** Las «Palabras clave» españolas caben en la página i; las inglesas se parten y dejan cuatro términos solos en la página iii |
| Nomenclatura compacta | **FALLA.** Cuatro páginas (xii–xv) y **dos listas paralelas**: la nomenclatura general y «Símbolos adicionales del juego de integración» |
| Eliminar símbolos históricos inactivos | **FALLA. 25 de las 79 entradas (32 %) están muertas**: los bloques E0/SP0, E5 y E8 completos (§2.5a) |
| Guía de lectura: decidir si es necesaria | **Necesaria, pero desactualizada**: su promesa sobre las tablas es falsa |
| Índices compactos | **FALLA.** El TOC desborda a una cuarta página por seis renglones y el Índice de figuras a una segunda por cinco |
| Evitar 17 páginas antes de la Introducción | **FALLA: son exactamente 17** |

### 4.3 Cuánto se recupera, y sin perder nada

| Acción | Páginas |
|---|---|
| Absorber la cola de *keywords* en la página ii (`\emergencystretch`, o cinco términos más cortos) | **−1** |
| Encajar los seis renglones J.1–J.6 en la tercera página del TOC | **−1** |
| Encajar las cinco entradas de figuras en la primera página del Índice de figuras | **−1** |
| Fundir «Símbolos adicionales del juego de integración» en la nomenclatura general, sin duplicar cabeceras | **−1** |
| Retirar las 25 entradas muertas de la nomenclatura (§2.5a) | **−1** |

**Front matter de 17 → 12 páginas.** Los cuatro primeros ahorros son de composición y no
suprimen ni una pieza de contenido; el quinto suprime sólo símbolos que el documento no usa.

---

## 5. Resumen de hallazgos

### P0 — bloquean

| # | Hallazgo | Evidencia |
|---|---|---|
| P0-1 | **Ninguna de las 41 tablas publica IC, dispersión ni p**, pese a que trece publican tasas a tres decimales sobre mundos pareados | §1.5a |
| P0-2 | **Cinco tablas de resultados duplicadas literalmente** entre cuerpo y anexo; una de las copias (T32) pierde el n | §1.5b |
| P0-3 | **Tabla 29 entera a 6,92 pt** (982 glifos, el 100 % de su cuerpo bajo 7 pt) y **cabeceras de la Tabla 5 a 4,88 pt**, frente al umbral propio de ≥8 pt | §1.2, §1.3 |
| P0-4 | **Siete tablas sin `\ref` en el texto**, cinco de ellas de resultados | §1.5c |
| P0-5 | **Dos ecuaciones numeradas cuyos símbolos no existen en el resto del documento**: `eq:sp3-digital-update` (siete símbolos sin definir, seis de ellos nunca definidos) y `eq:pre-results-go-contract` (sus seis predicados aparecen una sola vez, dentro de la propia ecuación) | §2.4 |
| P0-6 | **29 símbolos llegan a ecuación desplegada y no se definen nunca**; 62 se usan antes de su definición. La causa es la compactación de la v2, que dejó las definiciones 30–40 ficheros por detrás del enunciado | §2.4 |
| P0-7 | **`z` conserva siete significados en el documento compilado, tres de ellos `z_k`**; dos `z_k` (binaria de compleción y vector de pose en metros) comparten el índice de carga y están a 17 páginas sin cruce | §2.1 |

### P1 — visibles en una lectura atenta

| # | Hallazgo | Evidencia |
|---|---|---|
| P1-1 | Tres páginas con una o dos líneas de contenido: la cola de *keywords* (iii), una ruta de fichero (58) y una cola de párrafo (69) | §3.1, §3.2 |
| P1-2 | 8 viudas y 11 huérfanas; dos viudas de ~100 pt de ancho abren página | §3.3 |
| P1-3 | 9 encabezados seguidos de encabezado, seis de ellos con títulos casi idénticos | §3.4 |
| P1-4 | 17 páginas antes de la Introducción, reducibles a 13 sólo con composición | §4.3 |
| P1-5 | La «Guía de lectura» (p. xvi) promete una distinción oráculo/método que las tablas no implementan | §1.5d |
| P1-6 | 14 tablas a 8 pt o menos; sólo 11 de 41 usan la macro de la casa `\viutablefont` | §1.2 |
| P1-7 | **32 % de la nomenclatura está muerta** (25 de 79 entradas: bloques E0/SP0, E5 y E8 completos), y ≥96 símbolos vivos no figuran en ella. Cobertura real ≈ 36 % | §2.5 |
| P1-8 | Los seis símbolos que el criterio señala por nombre (`z, ρ, λ, S, R, K`) están todos reutilizados; `R` acumula 7 significados, `ℓ`, `r`, `d`, `s` y `P` siete cada uno | §2.2 |
| P1-9 | Cuatro objetos mecánicos centrales se escriben con **cuatro grafías distintas** cada uno (matriz de agarre, *wrench* demandado, coalición, conjunto de fuerzas admisibles) | §2.3 |
| P1-10 | **`\mu_i(t)`, la tasa de revisión modulada que da nombre al método propuesto, existe sólo como una línea de la nomenclatura**: cero usos en los 89 ficheros | §2.5a |
| P1-11 | El front matter se contradice: `04-nomenclature.tex` y `04-nomenclature-megajuego-v2.tex` se `\input` seguidos (`main-v2.tex:78-79`) y asignan significados incompatibles a `X`, `K`, `W` y `d` sin una sola referencia cruzada | §2.2, §2.6 |

### P2 — pulido

| # | Hallazgo | Evidencia |
|---|---|---|
| P2-1 | 10 tablas desbordan la caja de texto, máximo 1,66 pt (0,59 mm) | §1.3 |
| P2-2 | Separador decimal mixto: coma en T16/T39, punto en las otras 16 | §1.6 |
| P2-3 | Unidades ausentes en T18/T41 y T20 | §1.6 |
| P2-4 | Una tabla sin numerar (p. xvi) y dos entornos `table` muertos dentro de `\iffalse` | §1.6 |
| P2-5 | Matemáticas en Computer Modern dentro de un documento en Arial | §3.7 |
| P2-6 | 35 *i sin punto* en la capa de texto (copia/indexación, no visual) | §3.7 |
| P2-7 | 8 `Overfull \hbox`, máximo 4,80 pt | §3.6 |
| P2-8 | `min` en cursiva en lugar de `\min` dentro de una ecuación numerada (`sp2-e6-trimmed.tex:66`); `\delta_{min}` recto y `\delta_{\min}` en el mismo fichero | §2.3 |
| P2-9 | Negrita de vectores inconsistente: el mismo *wrench* aparece como `\boldsymbol W_k^{\mathrm{dem}}` y como `W_k^d` | §2.7 |
| P2-10 | Siete de las ocho macros de `config/math-commands.tex` se usan cero o una vez; el cuerpo escribe a mano lo que ellas abrevian | §2.5c |
| P2-11 | ~2/3 de `docs/05_NOTATION.md` describe campañas ausentes de `main-v2.pdf`, sin declararlo: no es seguro usarlo como referencia de la memoria compilada | §2.6 |

### Lo que pasa limpio

- Alineación decimal de columnas numéricas: **0,0 pt de dispersión** en las 31 columnas medidas.
- Fuente declarada: **41/41** tablas.
- Tablas partidas entre páginas: **0**. Figuras partidas: **0**.
- Resumen (281) y Abstract (287) dentro del intervalo 200–300.
- Jerarquía de títulos: tres niveles limpios, naranja VIU consistente en 104 páginas.
- Tipografía del cuerpo: Arial 12, conforme a la plantilla VIU.
- Convenio de `\Phi`: siempre potencial exacto, siempre maximizado. Transpuesta siempre `^{\mathsf T}`.
- `x_{ik}` binaria frente a `x_k` masa poblacional: correctamente separadas, conforme a `docs/05_NOTATION.md:456`.

---

## 6. Nota de método

Ningún fichero de la memoria fue modificado. Las mediciones sobre el PDF se hicieron con
`pdfplumber` (geometría de glifos, filetes, color y tipografía) y `pypdf`; las del fuente,
sobre la expansión recursiva de `\input` desde `main-v2.tex`, restringida a los 89 ficheros
de `final-hardening/census.json`. Las cifras del §1 y del §3 se repitieron sobre la
recompilación que ocurrió durante la auditoría y salieron idénticas.
