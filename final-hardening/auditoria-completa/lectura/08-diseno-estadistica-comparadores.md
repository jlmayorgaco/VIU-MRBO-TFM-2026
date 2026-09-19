# Diseño experimental, estadística, comparadores y validez

**Criterio aplicado:** `pre-thesis/guidelines/01-auditoria-maestra.md`, bloques **28**
(Diseño experimental, líneas 472–496), **29** (Estadística, 497–517), **30**
(Baselines y comparadores, 518–535), **35** (Validez interna, 599–612) y **36**
(Validez externa, 613–628); más `pre-thesis/guidelines/05-checklist-por-fases.md`,
**FASE 12**, **FASE 13** y **FASE 14**. La política estadística propia del
proyecto está en `docs/03_EXPERIMENT_PROTOCOL.md` §7 y se usa aquí como norma
autoimpuesta, no como criterio añadido.

**Artefactos auditados**

| Artefacto | Contenido |
|---|---|
| `pre-thesis/build-v2/main-v2.pdf` | 147 páginas de PDF = 17 preliminares + 130 arábigas |
| `final-hardening/census.json` | 89 ficheros fuente del documento activo |
| `pre-thesis/shared/generated-macros/` | 31 ficheros de macros; toda cifra impresa sale de aquí |
| `results/processed/{sp3,sp4,sp6,sp7,sp8,integrated}/` | campañas confirmatorias con `manifest.json` y `audit.json` |
| `legacy/results/{sp2,sp3,sp4,sp6,sp7}/` | campañas heredadas con `tables/runs.csv` |
| `legacy/results/coppeliasim_validation/aws_industrial2_method_comparison_pilot/` | piloto AWS, 32 ejecuciones |
| `docs/03_EXPERIMENT_PROTOCOL.md` §7 | política estadística declarada |

**Convención de paginación.** *Página impresa = página del PDF − 17*. El capítulo 6
ocupa las páginas impresas **34–62** (PDF 51–79); el capítulo 7, **63–69**
(PDF 80–86). Salvo indicación expresa, los números de este informe son páginas
impresas.

**Fecha de la auditoría:** 2026-09-19. No se modificó ningún fichero del TFM.

---

## Veredicto

**FALLA el bloque 29 (Estadística) y la FASE 13 en lo esencial: el cuerpo impreso
no contiene ni un solo intervalo de confianza numérico, mientras la metodología
promete uno por contraste. FALLA el bloque 30 y la FASE 14 por brazos ejecutados
y no publicados y por tablas de «métodos comparados» que no corresponden con las
tablas de resultados. FALLA el bloque 35 por una puerta de admisión condicionada
al resultado en la campaña de CoppeliaSim. CUMPLE el bloque 36 (Validez externa)
con holgura: es la dimensión mejor resuelta del documento.**

| FASE 13 — Estadística | Estado |
|---|---|
| Mundo/seed = unidad independiente | **FALLA**: en las cinco campañas activas el $n$ impreso es de celdas, no de semillas (ver §1.6) |
| Pareamiento preservado | CUMPLE |
| McNemar para binario pareado | CUMPLE (declarado y usado) |
| Paired bootstrap CI | CUMPLE en el cálculo, **FALLA en la impresión** (§1.1) |
| Wilcoxon cuando corresponde | CUMPLE |
| Friedman si procede | declarado; no se imprime ningún estadístico Friedman ni Kendall $W$ |
| Holm por familia coherente | CUMPLE en el cálculo; las familias no se enumeran en el cuerpo |
| **IC del efecto** | **FALLA: cero intervalos numéricos en 130 páginas arábigas** |
| **$n$ explícito** | parcial: en 4 de 9 tablas de resultados; ausente en toda la prosa |
| Failures incluidos | CUMPLE (verificado sobre las tablas, §1.9) |
| Timeouts incluidos | CUMPLE |
| No pseudo-replication | **FALLA en E2, E3, E4, E6-C y E7-C**; cumple en Cargo, E1 y el banco factorial del megajuego (§1.5) |
| No «no significativo = equivalentes» | **FALLA** en §7.1 (§1.8) |
| No causalidad desde contraste no causal | **FALLA** en la ablación Cargo del cuerpo (§4.1) |

| FASE 12 — Diseño experimental | Estado |
|---|---|
| Pregunta / Hipótesis | CUMPLE: Tabla 1 (p. 9) asigna estimando y regla a H1a–H5b |
| **Seed set** | parcial: registrado para E2, E3, E6, E7, Cargo; **ausente** para E4 en el manifiesto (recuperable del `runs.csv`) |
| Unidad experimental | declarada (§4.5), **contradicha por los $n$ impresos** |
| Tratamientos / Factores / Niveles | CUMPLE en los manifiestos; **no impresos** |
| Baselines / Ablations / Oracles | CUMPLE en las tablas «Métodos comparados»; **FALLA** la correspondencia con resultados (§2.4) |
| Primary / Secondary endpoint | **FALLA**: ninguna campaña declara cuál es el primario |
| Horizon / Timeout | solo AWS (60 s) y CoppeliaSim (120 s) |
| Failure / Success / Collision definition | CUMPLE (p. 35, definición FP/FN) |
| **Pre-specification** | **FALLA en 7 de 10 campañas**. Existe congelación previa verificable solo en Cargo (`freeze_manifest.json`, `frozen_before_execution`, SHA de configuración, de registro de semillas y de *commit*), en SP5 (`frozen_before_confirmatory_seed_opening`, `confirmatory_seed_opening_event_sha256`) y en el banco factorial del megajuego (`final-hardening/megajuego_regeneration_manifest.json`, `frozen_at_utc: 2026-09-18`, con familias de Holm F1–F4 y *endpoint* primario declarados antes de ejecutar). E1, E2, E3, E4, E6-C, E7-C, AWS y CoppeliaSim no tienen ninguno; en E6-C y E7-C las hipótesis existen solo como literales de Python dentro de `experiment.py` |
| **Raw data conservado** | **FALLA para E3 y E4**: `historical_generator_present_in_worktree: false` |
| Ningún optional stopping | **FALLA en CoppeliaSim** (§4.3) |

| FASE 14 — Comparadores | Estado |
|---|---|
| Implementación corresponde al nombre | **FALLA** para CBBA, ORCA, DMPC, SCP, CBS/ECBS, planificación priorizada |
| Si no, llamar «adaptación inspirada en…» | **FALLA en el cuerpo, CUMPLE en el dato**: la etiqueta honrada «Puntuación inspirada en Smith» existe en `sp2_comparison.tex` y esa tabla nunca se imprime en el cuerpo |
| Información disponible declarada | CUMPLE (Tabla 3, p. 16) |
| Misma planta / escenario / horizonte / unidad | CUMPLE |
| No comparar oracle con implementación local como equivalentes | CUMPLE explícitamente (p. 35 y §4.8) |

| Bloque 36 — Validez externa | Estado |
|---|---|
| Escenarios sintéticos declarados | CUMPLE |
| Falta de hardware declarada | CUMPLE |
| Coppelia = replay cinemático, no física | CUMPLE, repetido cuatro veces |
| Industria | CUMPLE: «no estima una probabilidad industrial» |
| Generalización a otros AMR / topología / cargas | CUMPLE: se niega explícitamente |

---

## 1. Estadística

### 1.1 El hallazgo previo se confirma: cero intervalos numéricos en el cuerpo

Barrido regular sobre el texto extraído de `main-v2.pdf`, páginas PDF 18–87
(todo el cuerpo arábigo, introducción a referencias):

- **Pares numéricos entre corchetes del tipo `[a, b]` o `[a; b]`: 0 ocurrencias.**
- Token «IC»: 4 ocurrencias, **ninguna acompañada de números**.
  - p. 9, Tabla 1: «El IC del 95 % debe excluir cero en la dirección favorable» (regla de decisión de H3).
  - p. 36, Figura 11: «estimando e IC» como etiqueta de un diagrama de procedencia.
  - p. 62, Tabla 23: «el IC del 95 % del contraste temporal incluye cero».
  - p. 65, Tabla 24: la misma frase.
- Valores $p$ numéricos: **1**, repetido dos veces — $p_{\mathrm{Holm}}=0{,}068$, pp. 62 y 65.

Las macros existen y contienen los números. Inventario completo de las 23 macros
de intervalo en `pre-thesis/shared/generated-macros/`:

| Fichero | Macros de IC |
|---|---|
| `sp2_numbers.tex` | `\SPTwoGapCILow/-High` `[-0.2225,-0.2057]`, `\SPTwoSuccessCILow/-High` `[0.0759,0.0920]`, `\SPTwoPDCILow/-High` `[-0.128,-0.111]` |
| `sp3_numbers.tex` | `\SPThreeGuardCI…` `[-0.370,-0.295]`, `\SPThreeVectorCI…`, `\SPThreeGraphCI…` |
| `sp4_numbers.tex` | `\SPFourDockCILow/-High` `[0.037,0.157]`, `\SPFourTimeDiffLow/-High`, `\SPFourWorkDiffLow/-High` |
| `sp5_numbers.tex` | tres pares |
| `sp6_numbers.tex` | `\SPSixHOneCILow/-High` `[0.710,0.787]` |
| `cargo_e2e_numbers.tex` | `\CargoEtwoETimingCI` `[-0.178;0.013]`, `\CargoEtwoEGuardCI` `[0.989;1.000]`, `\CargoEtwoERepairCI` `[0.967;1.000]` |

### 1.2 Dónde viven los intervalos: en los anexos, sin excepción

Toda frase del `.tex` que expande una macro de IC pertenece a un fichero de anexo
o al *source-snapshot*:

| Fichero | Destino |
|---|---|
| `pre-thesis/sections/v2/support/sp1-e2-trimmed.tex:180,190` | Anexo G |
| `pre-thesis/sections/v2/support/sp2-e4-trimmed.tex:150` | Anexo H |
| `pre-thesis/sections/v2/support/sp2-e6-trimmed.tex:157` | Anexo H |
| `pre-thesis/sections/v2/support/cargo-e2e-v2.tex:147,149` | Anexo H |
| `pre-thesis/sections/source-snapshot/mainmatter/06-results-and-analysis/*.tex` | no se `\input` en el cuerpo |

El cuerpo del capítulo 6 se arma con
`sections/v2/{results-interface, results-review, sp1-compact, sp2-compact,
sp3-compact, megajuego-compact, coppelia-compact}.tex`
(vía `thesis-results-v2.tex`, líneas 7–25). **Ninguno de esos siete ficheros
contiene una sola macro `…CI…`.** La separación es sistemática, no accidental:
al comprimir para la v2 se conservaron los efectos puntuales y se eliminaron los
intervalos y los valores $p$.

Esto contradice frontalmente dos compromisos del propio documento:

- `docs/03_EXPERIMENT_PROTOCOL.md` §7: «**Incluir intervalos de confianza.**»
- Metodología §4.5, p. 15: «Cada contraste informa el efecto, su intervalo
  obtenido con el número de remuestreos de *bootstrap* pareado predeclarado por
  campaña y el valor $p$ corregido mediante Holm.»
- Tabla 6, p. 35, fila «Elevar un claim»: la evidencia mínima exigida es
  «estimando, intervalo, tamaño muestral, McNemar o prueba declarada».

El capítulo 6 eleva ocho claims sin ninguno de los cuatro elementos que su propia
Tabla 6 declara obligatorios.

### 1.3 Inventario claim por claim del capítulo 6

Marcas: **E** efecto impreso, **IC** intervalo impreso, **p** valor $p$ impreso,
**n** tamaño muestral impreso, **D** denominador identificable por el lector del
cuerpo.

| # | p. | Afirmación empírica | E | IC | p | n | D | Macro con IC que existe y no se imprime |
|---|---|---|---|---|---|---|---|---|
| C1 | 37 | Cobertura del corpus: 23 / 18 / … → 2 → 0 | sí | no | no | no¹ | sí | — (conteos) |
| C2 | 38 | 115 SP1 vs 20 SP3 vs 15 SP2; 99 simulación vs 12 físico | sí | no | no | no¹ | sí | — |
| C3 | 38 | Modularidad $Q=0{,}108$ «sin escuela dominante» | sí | no | no | no | no | — (sin modelo nulo) |
| C4 | 41 | Corpus patentario +20,9 p.p. (37,9 % → 58,8 %) | sí | no | no | no¹ | sí | — |
| C5 | 44 | Tabla 10: plana 0.051 / marginal 0.135; brecha 0.372 → 0.157 | sí | no | no | pie² | sí | `\SPTwoGapCI…`, `\SPTwoSuccessCI…` |
| C6 | 44 | «sigue por debajo de la red neuronal (0.263) y del oráculo MILP (0.487)» | sí | no | no | no | **no**³ | `\SPTwoPDCI…` |
| C7 | 45 | E3: 7200 ejecuciones, semillas 461000–461099, FP 0.333 → 0.000 | sí | no | no | sí | ambiguo⁴ | `\SPThreeGuardCI…` |
| C8 | 46 | Tabla 11: FP y residual KKT sobre 600 mundos | sí | no | no | pie | sí | `\SPThreeVectorCI…`, `\SPThreeGraphCI…` |
| C9 | 48 | Tabla 13: E4, cinco métodos, $n=108$ | sí | no | no | **sí** | sí | `\SPFourDockCI…` |
| C10 | 49 | Tabla 15: E6-C, 480 mundos, certificado restaurado 0.750 | sí | no | no | pie | sí | `\SPSixHOneCI…` |
| C11 | 49 | «La caída de éxito temporal bajo plazo estrecho es un efecto empírico distinto» | **no**⁵ | no | no | no | no | — |
| C12 | 50 | Tabla 16: Cargo, seis tratamientos, $n=360$ | sí | no | no | **sí** | sí | — |
| C13 | 50 | «tasa de misión 0.997 … frente a 1.000 de la referencia central» | sí | no | no | no | sí | — |
| C14 | 50 | «la guardia física cambió el éxito en 0.996» | sí | **no** | **no** | **no** | **no**⁶ | `\CargoEtwoEGuardCI` = `[0.989;1.000]`, $p_{\mathrm{Holm}}=5{,}79\times10^{-21}$, $n=270$ |
| C15 | 50 | «continuar con reemplazo lo elevó en 0.989» | sí | **no** | **no** | **no** | **no**⁶ | `\CargoEtwoERepairCI` = `[0.967;1.000]`, $p_{\mathrm{Holm}}=6{,}46\times10^{-27}$, $n=90$ |
| C16 | 52 | Tabla 18: E7-C, cinco métodos, 360 mundos | sí | no | no | pie | sí | — |
| C17 | 52 | «al retirarla, la tasa cayó 26.1 puntos porcentuales» | sí | no | no | no | sí | `sp7_hypotheses.tex`: `[0.217; 0.308]`, $p=5\times10^{-29}$, $n=360$ |
| C18 | 53 | Piloto AWS: 32 ejecuciones, solo el escenario abierto entrega, 2 violaciones de barrera | sí | n/a | n/a | **sí** | sí | — |
| C19 | 55 | Extragradiente: residual $<10^{-9}$ en 113 iteraciones; 30 instancias, máx. $9{,}998\times10^{-10}$ | sí | n/a | n/a | **sí** | sí | — (determinista) |
| C20 | 56 | *Caging*: solución racional exacta, brecha $10^{-11}$ | sí | n/a | n/a | n/a | sí | — (algebraico) |
| C21 | 57 | Tabla 20: E2E, coste 62.83, +1,49 % sobre FCFS, KKT $1{,}4\times10^{-11}$ | sí | n/a | n/a | **sí** ($n=1$) | sí | — |
| C22 | 57 | Figura 25: «reduce energía (−1,97 %), aceleración (−77,6 %) y torque pico (−59,1 %)» | sí | no | no | **no**⁷ | no | — |
| C23 | 59 | CoppeliaSim: error de reejecución $6{,}89\times10^{-9}$ m; Tabla 21 | sí | n/a | n/a | **sí** ($n=1$) | sí | — |
| C24 | 62 | Tabla 23: «H3 no se sustenta: el IC del 95 % incluye cero, y $p_{\mathrm{Holm}}=0{,}068$» | **no** | **no** | **sí** | **no** | no | `\CargoEtwoETimingCI` = `[-0.178;0.013]`, efecto $-0{,}086$, $n=90$ |

¹ El $n$ aparece solo en la fuente de la figura («$n = 244$», «$n = 75$»), no en la prosa.
² «(1560 mundos)» en el pie de la Tabla 10.
³ Los valores 0.263 y 0.487 proceden de `sp2_comparison.tex`, tabla que **no se `\input` en el cuerpo**: el lector no puede ver de dónde salen.
⁴ Coexisten «7200 ejecuciones» (p. 45) y «600 mundos pareados» (Tabla 11, p. 46). El capítulo 7, p. 63, usa un tercer fraseo: «En 600 instancias».
⁵ Ni una sola cifra para el régimen que se está discutiendo; se remite al Anexo H.
⁶ La Tabla 16 adyacente muestra $n=360$ en todas las filas; los contrastes C14 y C15 se calculan sobre 270 y 90 pares respectivamente. El lector atribuirá 360.
⁷ Corrida única del demostrador E2E ($n=1$, declarado dos párrafos antes, pero no en el pie de la Figura 25).

**Respuesta directa a la pregunta planteada:** el capítulo 6 imprime **un único
valor $p$** ($p_{\mathrm{Holm}}=0{,}068$, C24) y lo imprime **sin su intervalo**.
Es, además, el resultado negativo. El intervalo que la regla de decisión de H3
exige (p. 9: «El IC del 95 % debe excluir cero en la dirección favorable») se
describe verbalmente —«incluye cero»— y nunca se muestra. El lector no puede
comprobar la regla que el propio documento se impuso.

En sentido inverso, C14 y C15 imprimen el efecto y omiten a la vez intervalo,
$p$ y $n$, aunque los tres existen y son extraordinariamente favorables
($p_{\mathrm{Holm}}\approx10^{-21}$ y $10^{-27}$). La asimetría es llamativa: el
documento oculta la evidencia fuerte y publica el $p$ débil, de modo que el
sesgo no es de autopresentación sino de compresión mal ejecutada.

### 1.4 Las tablas de hipótesis existen y no se `\input` en ninguna parte

Seis ficheros de macros contienen exactamente la tabla que el bloque 29 pide
—ID, métrica, $n$, efecto, IC 95 %, $p_{\mathrm{Holm}}$—:

`cargo_e2e_hypotheses.tex`, `sp5_hypotheses.tex`, `sp6_hypotheses.tex`,
`sp7_hypotheses.tex`, `sp8_hypotheses.tex`, `sp0_hypothesis_summary.tex`.

Búsqueda de `_hypotheses` sobre todos los `.tex` del repositorio excluyendo el
propio directorio de macros: **cero resultados**. Son artefactos muertos. El
documento generó la tabla correcta y no la imprimió en ningún sitio, ni siquiera
en los anexos.

Contenido de `cargo_e2e_hypotheses.tex`, que por sí sola habría resuelto C14,
C15 y C24:

| ID | Métrica | $n$ | Efecto | IC 95 % | $p_{Holm}$ |
|---|---|---|---|---|---|
| E2E-H1 | tiempo de misión [s] | 90 | −0,086 | [−0,178; 0,013] | 0,068 |
| E2E-H2 | éxito de misión | 270 | 0,996 | [0,989; 1,000] | $5{,}79\times10^{-21}$ |
| E2E-H3 | éxito de misión | 90 | 0,989 | [0,967; 1,000] | $6{,}46\times10^{-27}$ |
| E2E-H4 | éxito de misión | 90 | **0,000** | **[0,000; 0,000]** | 1,000 |

La fila E2E-H4 merece atención aparte: efecto exactamente cero con intervalo
degenerado $[0;0]$ sobre 90 pares significa **diferencia nula en las noventa
comparaciones**, no «diferencia pequeña». Es el contraste información
perfecta *vs.* vecinal. Ver §4.5.

### 1.5 Pseudorreplicación: el $n$ impreso no es el número de semillas

`docs/03_EXPERIMENT_PROTOCOL.md` §7: «La unidad independiente es el mundo o
bloque escenario–semilla; robots, cargas y muestras temporales son observaciones
anidadas.» Metodología §4.4, p. 14: «Los robots y las muestras temporales están
anidados en el mundo; no cuentan como réplicas.»

La regla se respeta para robots e instantes y se incumple un nivel más arriba:
lo que las campañas llaman «mundo» es una **celda (escenario × factor × semilla)**,
y la misma semilla se reutiliza en todas las celdas.

| Campaña | «mundos» impresos | Semillas distintas | Celdas por semilla | Fuente |
|---|---|---|---|---|
| E2 (`SP2_MC_capacity_comparison`) | **1560** | **40** (3100–3139) | 39 | `legacy/results/sp2/SP2_MC_capacity_comparison/tables/runs.csv` |
| E2 ablación (`SP2_MC_marginal_payoff_ablation`) | 1560 | 40 (3100–3139) | 39 | ídem |
| E3 (`SP3_WRENCH_NASH_GAME_v1_1`) | **600** | **100** (461000–461099) | 6 | `legacy/results/sp3/.../tables/runs.csv` |
| E4 (`SP4_DOCKING_GAME_CONFIRMATORY_v3`) | **108** | **6** (474100–474105) | 18 | `legacy/results/sp4/.../tables/runs.csv` |
| E6-C (`SP6_RECOVERY_CONFIRMATORY_v1`) | **480** | **40** (8600–8639) | 12 | `results/processed/sp6/.../manifest.json` |
| E7-C (`SP7_TRAFFIC_CONFIRMATORY_v1`) | **360** | **40** (8700–8739) | 9 | `results/processed/sp7/.../manifest.json` |
| Cargo | 360 | 30 (9700–9729) | 12 | `results/processed/integrated/.../manifest.json` |
| E1 (`SP1_QUORUM_v1`, fuera del cuerpo) | 1440 | **1440** | 1 | `legacy/results/sp1/SP1_QUORUM_v1/tables/runs.csv` |
| Megajuego factorial | 30 / 20 | **30 / 20** | 1 | `final-hardening/megajuego_regeneration_manifest.json` |

**Tres campañas se salvan y conviene decirlo.** E1 asigna una semilla distinta a
cada mundo. El banco factorial del megajuego declara la regla en su manifiesto
—«los 8 AMR, las 2 cargas y los pasos temporales dentro de una corrida NO son
réplicas independientes»— y usa $n = 30$. Y **Cargo agrupa correctamente**:
`hypotheses.csv` registra a la vez `n_pairs` y `n_independent_instances`
(E2E-H2: 270 y **90**), y el intervalo se remuestrea sobre medias de conglomerado,
no sobre pares — `src/viu_mrob_tfm/integrated/experiment.py:963-965`:

```python
cluster_diffs = paired.groupby(["n_robots", "seed"], sort=True)["difference"].mean()
low, high = _bootstrap_ci(cluster_diffs, 77100 + index)
```

Cargo es, por tanto, la única de las seis campañas del capítulo 6 cuya inferencia
resiste el bloque 29. El problema es de las otras cinco.

El caso extremo es **E4: seis semillas presentadas como $n = 108$.** La columna
`$n$` de la Tabla 13 (p. 48) dice literalmente 108 en las cinco filas, y el
intervalo del anexo, `\SPFourDockCI` $=[0{,}037,\,0{,}157]$ con
$p_{\mathrm{Holm}}=3{,}17\times10^{-3}$, remuestrea 108 unidades correlacionadas
a partir de seis extracciones aleatorias. Es el único contraste de SP2 con valor
$p$ en todo el documento.

El caso más visible es **E2**: un efecto pareado de $-0{,}2145$ con semiamplitud
de intervalo $0{,}0084$ y $p_{\mathrm{Holm}}=2{,}23\times10^{-242}$. Un valor $p$
de ese orden sobre 1560 unidades es la firma aritmética de tratar como
independientes observaciones que comparten semilla. Comprobación directa sobre
`runs.csv`, semilla 3100, generador `balanced_capacity`, método
`greedy_capacity_nearest`: las variantes v00, v01 y v02 comparten
`n_robots = 8`, `n_loads = 3` y producen 0,466 / 0,481 / 0,412 de
`capacity_satisfaction_ratio`. No son mundos independientes.

Fuera de Cargo, ningún script de análisis agrupa por semilla: E2, E3, E4, E6-C y
E7-C consumen el $n$ inflado directamente (`n_pairs = 1560`, `600`, `108`, `480`,
`360` en sus respectivos `hypothesis_results.csv` / `hypotheses.csv`).
`SPTwoWorlds` está además **codificado a mano** como la cadena `"1560"` en
`src/viu_mrob_tfm/sp2/evidence.py:129`, no calculado del dato.

Esto no invierte ningún signo —los efectos son grandes— pero invalida los valores
$p$ y estrecha artificialmente los intervalos de las cinco campañas afectadas.
Bloque 29, «Independencia»: **falla**.

### 1.6 Remuestreos de bootstrap: cero cifras en el cuerpo y cuatro valores distintos en el código

Metodología §4.5 promete «el número de remuestreos de *bootstrap* pareado
predeclarado por campaña». **En el cuerpo impreso no aparece ninguna cifra.**
En los anexos aparecen dos. En el código hay cuatro valores distintos, sin
justificación de la variación:

| Campaña | Remuestreos | Dónde consta | ¿Impreso? |
|---|---|---|---|
| E1 / SP1.N4 | 2000 | `manifest.json` + `sp1.tex:278` | anexo |
| E3 | 2000 | `sp3.tex:282` | anexo |
| E6-C | 2000 | `src/viu_mrob_tfm/sp6/experiment.py:550` | **no** |
| E7-C | 2000 | `src/viu_mrob_tfm/sp7/experiment.py:692` | **no** |
| Cargo | **3000** | `src/viu_mrob_tfm/integrated/experiment.py:926` | **no** |
| SP2 canónico | **5000** | `sp2_canonical/benchmark.py:943,2761` | **no** |
| E4 (estrato transporte) | **10000** | `experiments/configs/sp4_transport_evidence.yaml` | **no** |
| Megajuego | **10000**, con semilla de análisis 20260918 distinta de las del simulador | `megajuego_regeneration_manifest.json` | **no** |
| **E2** | **no consta en ninguna parte** | — | no |
| AWS | 2000 declarado en el config, **sin artefacto que lo consuma** (no hay columnas de IC en `multiscenario_summary.csv`) | — | no |

Bloque 29, «Número de remuestreos»: **falla**. `docs/03_EXPERIMENT_PROTOCOL.md` §7
pide además «registrar una semilla de análisis distinta de las semillas del
simulador»: solo Cargo (77100 + índice) y el megajuego (20260918) lo hacen.

### 1.7 Pares IC / $p$ mutuamente contradictorios, impresos sin explicación

Tres contrastes imprimen —en los anexos— un intervalo que excluye cero junto a un
$p_{\mathrm{Holm}}$ igual o cercano a 1, o al revés:

| Contraste | Efecto | IC 95 % | $p_{\mathrm{Holm}}$ | Fichero |
|---|---|---|---|---|
| Primal–dual vs. voraz (E2) | −0,119 | [−0,128; −0,111] | **1** | `sp2_numbers.tex` |
| Previsión central mejora CBF local (E5) | −0,426 | [−0,519; −0,333] | **1,00** | `sp5_hypotheses.tex` |
| CBF local reduce violación vs. APF (E5) | 0,001 | **[−0,031; 0,039]** | $3{,}76\times10^{-3}$ | `sp5_hypotheses.tex` |

La explicación es que las pruebas son **unilaterales** en la dirección favorable
mientras los intervalos son bilaterales —`sp3.tex:282` dice «Wilcoxon pareado
unilateral»— de modo que un efecto grande en la dirección adversa produce $p=1$.
Es correcto en el cálculo y **ilegible en la página**: ninguna de las tres frases
advierte al lector de la lateralidad, y `07-conclusions-v2.tex:6` conserva un
comentario del autor sobre que Holm corrige valores $p$ y no intervalos, es decir,
el problema era conocido y no se resolvió en la prosa. La lectura natural de
«IC = [−0,128; −0,111], $p_{\mathrm{Holm}}=1$» es «no hay diferencia», que es
exactamente lo contrario de lo que el dato dice.

### 1.8 «No significativo» tratado como equivalencia

`07-conclusions-v2.tex:41` (p. 63): «Las variantes vecinal y perfecta completaron
el régimen degradado ensayado.» Es una afirmación de equivalencia entre el
contrato de información local y la información perfecta, presentada sin
contraste, sin $n$ y sin intervalo. El contraste existe —E2E-H4, efecto 0,000,
IC [0,000; 0,000], $n=90$— y su lectura correcta no es «equivalen» sino «la
ventaja informativa fue inerte en este banco», que es un resultado distinto y más
interesante. Bloque 29, «No interpretar *no significativo* como equivalencia»:
**falla**.

### 1.9 Denominadores: la única parte que se cumple bien

Comprobación aritmética sobre las tablas del cuerpo:

- Tabla 13 (E4): éxito + colisión + horizonte agotado $= 1{,}000$ en las cinco
  filas (0.167+0.833; 0.176+0+0.824; 0.028+0+0.972; 0.009+0+0.991;
  0.269+0+0.731). **Los timeouts están en el denominador.**
- Tabla 18 (E7): entrega + interbloqueo $= 1{,}000$ en las cinco filas.
- Tabla 16 (Cargo): la fila «sin guarda física» declara misión 0,247 con
  intersección 0,750; los fallos no se eliminan.

Comprobación sobre el dato crudo, que confirma la ausencia de filtros de éxito:
E1 conserva 5760 corridas no convergidas de 8640; E3, 1760 de 7200; **E4, 818
*timeouts* de 1188**; E6-C conserva los 120 mundos infactibles por construcción;
Cargo conserva 372 fallos de misión y 102 *timeouts*; AWS conserva las 24
ejecuciones con entrega cero. No existe en los pipelines confirmatorios ningún
filtro del tipo `[df.success]`, `!= 'timeout'` o `status == 'ok'`; las llamadas a
`dropna` que hay (`sp6:547`, `sp7:689`, `integrated:920`, `sp8:715`) son guardas
de alineación del `pivot` y no eliminan ninguna fila en estas ejecuciones.

Metodología §4.4 y §4.7 lo declaran dos veces y Tabla 1 (p. 9) una tercera:
«un *timeout* cuenta como fallo». Se cumple. Bloque 29, «Failures/timeouts
incluidos»: **cumple**.

**Una sola excepción, y está declarada.** `src/viu_mrob_tfm/sp7/experiment.py:685-688`
implementa un filtro condicionado al desenlace:

```python
if successful_only:
    success = selected.pivot(index="world_hash", columns="method", values="delivery_success")
    valid = success[method_a].astype(bool) & success[method_b].astype(bool)
    values = values.loc[valid]
```

Las hipótesis H7.2 y H7.3 —ambas sobre tiempo de terminación— se declaran con
`successful_only=True` (l. 578-579), es decir, comparan *makespan* solo en los
mundos donde **ambos** métodos entregaron. Es un condicionamiento sobre una
variable posterior al tratamiento. Dos atenuantes: el `hypotheses.csv` lo registra
honradamente en la columna `successful_pairs_only`, y en esta ejecución no
eliminó nada ($n_{\text{pairs}}=360$ en los tres contrastes, porque solo la
ablación «sin reserva de zona» falla entregas y no participa en H7.2/H7.3). El
mecanismo está ahí y sesgaría en cuanto un método empeorase.

La excepción es de *presentación*, no de cálculo: entre el capítulo 6 y el 7 el
denominador de la restauración de E6 cambia sin aviso. Tabla 15 (p. 49) imprime
0,750 (incondicional); §7.1 (p. 63) y RQ4 (p. 64) imprimen «una fracción 1.000
de los certificados recuperables» (condicionado a factibilidad física). Ambos
números son correctos y el segundo declara su condicionamiento, pero el 0,750
no reaparece en el capítulo 7 y el lector que solo lea las conclusiones se lleva
la cifra favorable.

---

## 2. Comparadores

### 2.1 Clasificación por método

Evidencia obtenida leyendo el código, no las tablas del documento.

| Método nombrado | Implementación | Clase | ¿Lo dice el documento? |
|---|---|---|---|
| **CBBA** (Choi et al., 2009) | `src/viu_mrob_tfm/sp1_geo/allocators/cbba.py::allocate_capacity_cbba` — *arg-max* lexicográfico centralizado; las rondas de consenso se **simulan** (`consensus_rounds += diameter`) y los mensajes se calculan (`messages = 2*edges*consensus_rounds`) en vez de enviarse. Segunda variante en `sp1_n3/capacity_cbba.py::step`: paso de mensajes real, pero sin construcción de *bundle* y con un contador de versión en lugar de los tres vectores canónicos (pujas, ganadores, marcas de tiempo) | **proxy adaptado** | **parcialmente**. Tabla 9, p. 44: «garantía CBBA original inaplicable». Tabla 14, p. 49: «no equivale a CBBA completo». El propio docstring dice «it is not canonical one-winner CBBA». En el cuerpo nunca se dice que el consenso esté simulado |
| **ORCA** (van den Berg et al., 2011) | **no existe**. Ni semiplanos, ni LP, ni conjunto $ORCA_{A\vert B}$ en todo el repositorio. Lo más próximo es `sp5/payload_transport.py:342 velocity_obstacle_proxy`, una fuerza repulsiva activada por tiempo al contacto | **nombrado, no implementado** | **parcialmente**. Tabla 17, p. 52, lista ORCA como «Método comparado» con coste «LP local» y no dice que no se ejecutó; §7.5, p. 66, sí lo dice para el piloto AWS: «adaptaciones piloto, no implementaciones completas de CBBA, ORCA o DMPC» |
| **DMPC** | **no existe** ningún MPC distribuido. `sp2_canonical/controllers.py:152 CentralMPCController` es un MPC lineal **centralizado** real (`lsq_linear` con cotas de entrada) | **nombrado, no implementado** | solo en §7.5 |
| **MILP** | `sp1_geo/allocators/milp.py::solve_physical_milp` con `scipy.optimize.milp` (HiGHS); registra `optimal_certified`, `welfare_upper_bound`, `mip_gap`; `information_scope = global_oracle` | **oráculo exacto y certificado** | **sí**, Tabla 9: «certificado de optimalidad con brecha cero» |
| **«neural» / imitación** | `legacy/tmp/src/viu_mrob_tfm/sp2/methods.py:777 fit_neural_imitation_model`: MLP real en PyTorch, 8→8→1, 97 parámetros, Adam, 180 épocas. Entrenado sobre la salida del **oráculo MILP** más un término de *reward shaping* diseñado a mano (`_imitation_dataset`, l. 848) | **red real, pero destilada del oráculo** | **no**. Tabla 9 dice «evaluación empírica; sin certificado combinatorio». En ningún punto se dice que el maestro de la red es el propio oráculo con el que después se la compara |
| **Húngaro** (Kuhn, 1955) | `sp1_geo/allocators/hungarian.py::allocate_hungarian_slots`, `scipy.optimize.linear_sum_assignment` con columnas mudas y *big-M*; devuelve `not_applicable_nonseparable` fuera de la familia separable | **fiel**, con restricción honrada | **sí**: «exacto para el LAP expandido; capacidad aproximada» |
| **Planificación priorizada** | `sp7/experiment.py:488`: `profile = np.zeros(...)` fija **todos** los agentes a la ruta 0 y solo impone un orden de servicio; no hay búsqueda espacio-temporal contra reservas de agentes prioritarios. Mensajes sintetizados: `n*(n-1)` | **proxy adaptado** | **no**. Tabla 17 la agrupa con «Priorizado / oráculo restringido — referencia y techo interno; no equivalen a CBS/ECBS». No se dice que no sea planificación priorizada |
| **Oráculo restringido** | `sp8/theory.py:318 exhaustive_global_oracle` y `sp7/experiment.py:51 restricted_schedule_oracle`: enumeración exhaustiva con guarda de presupuesto y desempate lexicográfico | **oráculo exacto** dentro de su dominio | **sí**, y el nombre es honrado |
| **CBS / ECBS / LA-MAPF** | **no existen** | nombrados, no implementados | **sí**: Tabla 17, «no incluidas en el comparativo numérico» |
| **SCP** (Alonso-Mora et al., 2017) | **no existe** | nombrado, no implementado | **sí**: Tabla 12, «referencia de formulación, fuera del comparativo numérico» |

Balance del bloque 30: de nueve comparadores nombrados, **cuatro no están
implementados** (ORCA, DMPC, CBS/ECBS, SCP), **tres son proxies adaptados**
(CBBA, priorizada, dinámicas poblacionales del linaje SP2/SP3), **dos son fieles
o exactos** (Húngaro, MILP/oráculos). El documento lo declara con claridad para
CBS/ECBS y SCP, con ambigüedad para CBBA y ORCA, y **no lo declara** para la
planificación priorizada ni para el origen oracular de la red neuronal.

### 2.2 Dinámicas poblacionales: el revisor tiene razón a medias, y la mitad que falta es la grave

**Existen dos implementaciones distintas bajo los mismos nombres.**

*Integraciones reales de la EDO*, correctas y comprobadas:
`src/viu_mrob_tfm/sp1_n4/continuous.py:214 population_direction` implementa los
cuatro campos canónicos (replicator, Smith, BNN, logit) con proyección al símplex
y retroceso monótono en el potencial;
`sp1_canonical/validation/dynamics_v3.py:236 _revision_step`,
`sp1/theory.py:299 smith_preferences` y
`sp1_geo/allocators/qpg.py:110 _smith_direction` hacen lo mismo. Ninguna de esas
campañas alimenta el capítulo 6 activo.

*Ordenaciones secuenciales con el nombre de la dinámica*:
`legacy/tmp/src/viu_mrob_tfm/sp2/methods.py`, líneas 143, 190, 214 y 229. Los
cuatro métodos —`replicator_capacity`, `bnn_capacity`, `logit_capacity`,
`smith_capacity`— **construyen la misma clase `UtilityCapacityAllocator` y se
diferencian solo en hiperparámetros escalares**; «BNN» es literalmente el mismo
voraz con `exponent=2.0`. `UtilityCapacityAllocator.allocate` (l. 593) es un
barrido único sobre `np.argsort` de distancias, sin estado, sin tiempo y sin
derivada. **Esta es la campaña que alimenta E2, es decir, el capítulo 6.**

Qué dice cada capa del documento:

| Capa | Texto | Veredicto |
|---|---|---|
| **Dato** (`sp2_comparison.tex:10-11`) | «Puntuación **inspirada en** replicator» / «Puntuación **inspirada en** Smith» | **correcto** |
| **Código** (`src/viu_mrob_tfm/sp2/evidence.py:342,358`) | `"smith_ode_integrated_in_campaign": False`; «The methods labelled Smith in the inherited campaign use sequential scoring and do not integrate the Smith ODE» | **correcto** |
| **Anexo** (`support/sp1-e2-trimmed.tex:117,180`) | «las variantes Smith se implementaron como ordenaciones secuenciales y no como integraciones de la EDO»; «La campaña no integró la EDO Smith» | **correcto y explícito** |
| **Cuerpo** (`sections/v2/sp1-compact.tex:136`, Tabla 9, p. 44) | «Replicator/BNN/Smith (Sandholm, 2010) — $O(NK)$ — ordenación finita; garantías de la EDO fuera de esta implementación» | **insuficiente** |
| **Cuerpo**, prosa (p. 45) | «CBBA, voraz y **dinámicas poblacionales** son comparadores aproximados (Choi et al., 2009; Kuhn, 1955; Sandholm, 2010)» | **insuficiente** |

**Respuesta a la pregunta planteada: el cuerpo lo dice, pero solo en una celda de
tabla y con la fórmula más débil disponible.** «Ordenación finita» en la columna
«Garantía o límite» no informa de que no hay EDO; informa de que la EDO no
transfiere sus garantías, que es otra cosa. La frase inequívoca —«no como
integraciones de la EDO»— está únicamente en el anexo. Y la etiqueta honrada
que el propio pipeline genera, «Puntuación inspirada en Smith», vive en una tabla
(`sp2_comparison.tex`) **que el cuerpo no imprime**: `sp1-compact.tex:149` solo
carga `sp2_ablation.tex`. El cuerpo conserva el nombre desnudo con cita a
Sandholm y descarta la etiqueta correcta.

Colisión adicional que ningún capítulo resuelve: el mismo término «Smith» designa
una EDO integrada en SP1-N4 y un `argsort` en E2. Un lector que cruce el
capítulo 6 con los anexos no puede saber cuál está leyendo.

### 2.3 Brazos ejecutados y no publicados

Recuento directo sobre los `runs.csv` frente a lo impreso:

| Campaña | Brazos ejecutados | Brazos impresos en el cuerpo | No publicados |
|---|---|---|---|
| **E2** comparación | **13** (`greedy`, `hungarian`, `milp`, `cbba`, `replicator`, `bnn`, `smith`, `primal_dual`, `local_primal_dual`, `imitation`, `neural`, 2 oráculos) | **0** en el cuerpo; 7 en el anexo | **6**, entre ellos `hungarian_capacity`, `cbba_capacity` y `bnn_capacity` |
| **E2** ablación | 6 (`replicator_plain/marginal`, `smith_plain/marginal`, 2 oráculos) | **2** (Tabla 10) | 4 |
| **E3** | **12** (incluidos `wrench_oracle`, `cbba_slots`, `wrench_greedy`, `smith_price_guarded`, `replicator_price_guarded`, `erv_bnn_price_guarded`) | **3** (Tabla 11) | **9** |
| **E4** | **11** (`direct_to_slot`, `apf_navigation`, `rvo_proxy`, `cbf_qp`, `central_potential_reference`, `nash_pd_exact_raw`, `nash_pd_exact`, `nash_pd_ring`, `smith_primitives`, `replicator_primitives`, `erv_bnn_primitives`) | **5** (Tabla 13) | **6** |
| **E6-C** | 5 | 5 | 0 |
| **E7-C** | 5 | 5 | 0 |
| **Cargo** | 6 | 6 | 0 |

Consecuencias concretas:

1. **CBBA, Húngaro y BNN están nombrados como métodos comparados en la Tabla 9
   (p. 44) y ninguna cifra suya se imprime en todo el documento.** El filtro es
   explícito: `src/viu_mrob_tfm/sp2/evidence.py:174-180` define una lista
   `selected` de siete métodos que excluye `hungarian_capacity`, `cbba_capacity`,
   `bnn_capacity`, `primal_dual_capacity` y `local_primal_dual_capacity`.
2. **E3 ejecutó el oráculo de wrench, CBBA y tres dinámicas poblacionales sobre
   los mismos 600 mundos y no publica ninguna.** La Tabla 11 contiene solo tres
   variantes de la propia guardia. La prosa de p. 45 afirma que «el oráculo
   enumera instancias pequeñas, Hungarian es solo referencia escalar y CBBA,
   voraz y dinámicas poblacionales son comparadores aproximados» — describe
   comparadores cuyos resultados existen y no se muestran.
3. **La Tabla 10 de E2 es solo el brazo Smith.**
   `src/viu_mrob_tfm/sp2/evidence.py:118-119` selecciona
   `ablation.loc["smith_capacity_plain"]` y `["smith_capacity_marginal"]`; los
   brazos `replicator_capacity_plain/marginal` se descartan. La tabla se titula
   «Puntuación plana / Puntuación marginal» sin decir sobre qué regla base.

### 2.4 Reporte selectivo de las comparaciones adversas

La frase de p. 44 dice: «La corrección marginal mejora la regla secuencial propia
(0.051 → 0.135), pero en términos absolutos sigue por debajo de la red neuronal
no certificada (0.263) y del oráculo MILP (0.487).»

La tabla completa (`sp2_comparison.tex`, anexo), columna Completitud:

| Método | Completitud |
|---|---|
| Oráculo de puntuación (MILP) | 0,487 |
| Puntuación neuronal | 0,263 |
| Referencia de cobertura | **0,227** |
| Voraz de servicio | **0,219** |
| Imitación lineal | **0,218** |
| Puntuación inspirada en replicator | **0,139** |
| **Propuesta (marginal)** | **0,135** |
| Puntuación inspirada en Smith | 0,103 |

La propuesta queda **séptima de ocho**. La frase del cuerpo nombra las dos
comparaciones adversas de mayor prestigio —el oráculo y la red— y omite que
también queda por debajo del voraz de servicio, de la imitación lineal, de la
referencia de cobertura y del propio replicator. No es una afirmación falsa; es
una omisión que cambia la lectura. Bloque 30, «No rankings injustos»:
técnicamente no hay ranking injusto, pero sí hay un ranking recortado.

Lo mismo ocurre en E6-C. En la Tabla 15 (p. 49) el certificado restaurado vale
**0,750 en los cuatro métodos con reparación** —juego potencial, subasta marginal,
voraz por distancia y oráculo exacto— porque 0,750 es el techo de factibilidad
física. El *endpoint* primario está saturado y no discrimina. El efecto que sí se
reporta (`\SPSixHOneEffect` $=0{,}750$, $p_{\mathrm{Holm}}=1{,}3\times10^{-108}$)
es contra la ablación «sin reparación», es decir, contra no hacer nada. Y en el
*endpoint* secundario, éxito temporal, el método propuesto (**0,544**) es el
**peor de los cuatro**: subasta 0,596, voraz 0,596, oráculo 0,583. El cuerpo
comenta ese régimen sin dar una sola cifra («La caída de éxito temporal bajo plazo
estrecho es un efecto empírico distinto…») y remite al anexo.

### 2.5 Las tablas «Métodos comparados» no corresponden con las tablas de resultados

Metodología §4.7 promete: «Las tablas distinguen el oráculo con información global
del método, los comparadores y las ablaciones.» Lo hacen las tablas 9, 12, 14 y
17; **no lo hacen las tablas de resultados 10, 11, 13, 15, 16 y 18**, que listan
nombres sin etiqueta de clase. El lector debe cruzar dos tablas cuyos nombres no
coinciden:

| Tabla 12 (métodos E4, p. 48) | Tabla 13 (resultados E4, p. 48) |
|---|---|
| SCP restringido | — |
| Directo/CBF (referencia) | Directo al contacto / Proyección CBF |
| Planificador central + HOCBF | — |
| Juego PD/replicator + HOCBF (TFM) | Nash–PD exacto / Nash–PD anillo / Replicator + CBF |
| Control de pose + proyección de wrench | — |

Las dos tablas describen campañas distintas: la Tabla 13 procede de
`SP4_DOCKING_GAME_CONFIRMATORY_v3` (métodos `direct_to_slot`, `cbf_qp`,
`nash_pd_exact`, `nash_pd_ring`, `replicator_primitives`), mientras la
nomenclatura HOCBF de la Tabla 12 corresponde a `SP4_DOCKING_GAME_V4_*`
(`direct_hocbf`, `priority_hocbf`, `central_hocbf`, …). Son inconmensurables y el
documento las presenta consecutivas como si una explicara la otra.

Caso análogo en E7: la Tabla 17 (p. 52) lista **ORCA** entre los «Métodos
comparados en E7-C» y la Tabla 18 (p. 52) no contiene ninguna fila ORCA —porque
no existe la implementación—. La tabla de métodos marca «no incluidas en el
comparativo numérico» solo para CBS/ECBS/LA-MAPF, no para ORCA.

### 2.6 Lo que el capítulo 6 no dice del comparador «Replicator + CBF»

La Tabla 13 (p. 48) es la única tabla del capítulo 6 con $n$ por fila, y muestra
que los dos métodos nominalmente propuestos, **Nash–PD exacto (0,028) y Nash–PD
anillo (0,009), quedan muy por debajo de la línea base trivial «Directo al
contacto» (0,167) y de la «Proyección CBF» (0,176)**. Solo «Replicator + CBF»
(0,269) las supera. El texto que sigue a la tabla es una sola línea: «El Anexo H
amplía las cifras, los intervalos y la comparación completa de métodos.»
No hay interpretación, no hay lectura del resultado adverso, no hay mención de
que dos de los cinco métodos mostrados sean del propio TFM y pierdan. Bloque 33
(resultados negativos, fuera del alcance nominal de este informe pero solidario
con el 30): la tabla conserva el resultado negativo y la prosa lo ignora.

---

## 3. Diseño experimental por campaña

| | **E2** | **E3** | **E4** | **E6-C** | **E7-C** | **Cargo** | **AWS Ind.2** | **Coppelia** | **E2E** |
|---|---|---|---|---|---|---|---|---|---|
| Identificador | `SP2_MC_capacity_comparison` + `…_marginal_payoff_ablation` | `SP3_WRENCH_NASH_GAME_v1_1` | `SP4_DOCKING_GAME_CONFIRMATORY_v3` | `SP6_RECOVERY_CONFIRMATORY_v1` | `SP7_TRAFFIC_CONFIRMATORY_v1` | `CARGO_E2E_CONFIRMATORY_v1` | `AWS_INDUSTRIAL2_METHOD_COMPARISON_PILOT_v1` | `SP4_V4_COPPELIA_PAIRED_NARROW` | `simulate_e2e_megagame.py` |
| Unidad declarada | mundo | mundo | mundo | mundo | mundo | mundo | escenario×semilla | mundo | — |
| Unidad **real** | (generador, variante, semilla) | (config, semilla) | (escenario, robots, semilla) | (escenario, reserva, semilla) | (escenario, coaliciones, semilla) | (escenario, robots, semilla) | (escenario, semilla) | uno | uno |
| Pareado entre métodos | sí | sí | sí | sí | sí | sí | sí | sí | n/a |
| **Semillas distintas** | **40** | **100** | **6** | **40** | **40** | **30** | **2** | **1** | **1** |
| Lista de semillas registrada | sí, `manifest.json` | sí, en `runs.csv`; **no** en el manifiesto | sí, en `runs.csv`; **no** en el manifiesto | sí, `manifest.json` | sí, `manifest.json` | sí, `manifest.json` + `seed_registry_sha256` | sí, `runs.csv` (23100, 23101) | sí, 886001 | n/a |
| Valores | 3100–3139 | 461000–461099 | 474100–474105 | 8600–8639 | 8700–8739 | 9700–9729 | 23100–23101 | 886001 | — |
| $n$ impreso | 1560 | 600 / 7200 | 108 | 480 | 360 | 360 | 32 | 1 | 1 |
| Brazos | 13 / 6 | 12 | 11 | 5 | 5 | 6 | 4 | 2 | — |
| Corridas | 20 280 / 9 360 | 7 200 | 1 188 | 2 400 | 1 800 | 2 160 | 32 | 2 | — |
| Horizonte / *timeout* real | **no consta en ninguna parte**; el generador no está en el árbol | tope de iteraciones (1200 / 500 pasos), anexo | **35 s**; transporte 45 s, $\Delta t=0{,}15$ | plazo aleatorio por mundo: $\mathcal U(7{,}5;12{,}5)$ estrecho, $\mathcal U(18;24)$ o $\mathcal U(18;28)$ | 48 pasos; interbloqueo = 8 pasos parados | acople 16 s, transporte 50 s, $\Delta t=0{,}10$ | **60 s** | **120 s** | 300 s |
| …¿impreso en el **cuerpo**? | no | no | **no** | **no** | **no** | **no** | **sí** | **sí** | no |
| Fallos y *timeouts* en el denominador | sí | sí (1760 no convergidas) | sí (818/1188 *timeouts*) | sí (120 mundos infactibles) | sí | sí (372 fallos, 102 *timeouts*) | sí | sí |  sí |
| Filtro condicionado al desenlace | no | no | no | no | **sí** en H7.2/H7.3 (`successful_only`), inerte en esta corrida | no | no | **sí**, en la puerta de admisión (§4.3) | no |
| **Preespecificación** | no | no | no | no | no | **sí**: `frozen_before_execution`, `2026-09-13T00:06:17Z`, `config_sha256`, `seed_registry_sha256`, `git_sha_at_freeze`, más `protocol/seed_registry.yaml` con `disjoint: true` frente a las semillas piloto | parcial: `evidence_scope: …_not_confirmatory` y 7 limitaciones en el manifiesto | **puerta condicionada al resultado** (§4.3) | **sí**: `frozen_at_utc: 2026-09-18`, familias de Holm F1–F4 y *endpoint* primario declarados antes de ejecutar |
| Generador conservado | sí (`legacy`) | **no** (`historical_generator_present_in_worktree: false`) | **no** (ídem) | sí | sí | sí | sí | sí | sí |
| Nivel de evidencia declarado | — | — | — | **B** | **C** | confirmatorio | `…_not_confirmatory` | — | — |

Observaciones del bloque 28:

- **«Métrica primaria» y «métricas secundarias» no se declaran en ninguna
  campaña.** Las fichas de protocolo enumeran entre 5 y 11 métricas en pie de
  igualdad («Se miden éxito, intersección, tiempo, recuperación, error, *wrench*,
  saturación, energía, trabajo, comunicación y CPU»). Con Holm aplicado sobre
  familias que el cuerpo nunca enumera, el lector no puede reconstruir el tamaño
  de la familia ni verificar la corrección.
- **Horizonte y *timeout* no se imprimen en el cuerpo** para ninguna de las seis
  campañas principales, pese a que la Tabla 13 informa «horizonte agotado» como
  uno de sus tres desenlaces y a que en E4 ese desenlace alcanza **0,991** en una
  fila. Un lector del cuerpo no puede saber que el horizonte de E4 es de 35 s, ni
  que el «plazo estrecho» de E6-C es un valor aleatorio por mundo entre 7,5 y
  12,5 s. El único horizonte de E2 no existe en el árbol de trabajo.
- **Cargo y el banco factorial del megajuego son los dos ejemplares correctos.**
  El `manifest.json` de Cargo incluye `git_sha`, versiones de Python, NumPy, SciPy
  y pandas, hashes SHA-256 de cada artefacto, un `freeze_manifest.json` anterior a
  la ejecución y un registro de semillas con aserción de disjunción frente al
  piloto. El megajuego separa explícitamente «Parte I (diseño), fijada antes de
  ejecutar» de «Parte II (resultados)», declara el *endpoint* primario y las
  cuatro familias de Holm con su $k$, prohíbe el reintento con otra semilla
  («registrar la corrida como fallida con su traza; no reintentar con otra
  semilla») e incluye una sección «Qué no puede concluirse de esta campaña, por
  diseño». Ese es el nivel frente al que hay que medir E2, E3, E4, E6-C y E7-C.
- **E3 y E4 no son reproducibles**, solo reanalizables. Metodología §4.7 lo dice
  («Las etapas E2–E4 son reanálisis de observaciones archivadas… Parte de sus
  generadores históricos falta») y los `audit.json` lo confirman con
  `"historical_generator_present_in_worktree": false`. Es coherente; pero E3 y E4
  sostienen H2 y el único contraste con $p$ de SP2.

---

## 4. Validez interna

### 4.1 La ablación Cargo «sin guarda física» retira tres cosas a la vez

Confirmado en el código. `src/viu_mrob_tfm/integrated/experiment.py:538-548`
deriva **dos** banderas del único nombre de método, y la segunda gobierna **dos**
mecanismos distintos:

```python
"mechanical_guard": method != "no_physical_guard",
"safety_guard":     method != "no_physical_guard",
```

1. **Criterio de fuerza** (`mechanical_guard`, l. 348):
   `predicate = _certificate if mechanical_guard else _capacity_only`. `_certificate`
   exige $|C_k|\ge3$, capacidad $\ge$ masa **y** $\sum f_i^{\max}\ge F_k^{\mathrm{req}}$;
   `_capacity_only` suprime solo el término de fuerza.
2. **Punto de rodeo** (`safety_guard`, l. 513-521): sin la bandera, `_waypoint`
   devuelve directamente la pose destino y la carga se comanda **a través** del
   obstáculo.
3. **Filtro de velocidad** (`safety_guard`, l. 721 y 730-733): `_filter_velocity`
   impone `normal_speed >= -1.8*(clearance-0.08)`; sin la bandera no se aplica.

**¿Alguna conclusión atribuye el efecto solo al certificado de wrench?**

*En los anexos y en la metodología, no; y además se autocorrige de forma
ejemplar.* Tres textos lo dicen:

- `04-methodology.tex:296`: «La ablación “sin guardia física” retira a la vez el
  criterio agregado, el punto intermedio y el filtro, de modo que estima su
  efecto conjunto.»
- `support/cargo-e2e-v2.tex:106`: «…identifica el bloque conjunto, no cada
  componente.»
- `support/cargo-e2e-v2.tex:147`: «La variante sin ese bloque conservó el criterio
  agregado completo en **356 de 360 mundos** […]; **el contraste discrimina
  principalmente rodeo y filtrado, no certificación mecánica**.»
- `07-conclusions-v2.tex:117`, límite de H2: «QP planar; **ablación Cargo
  combinada**.»

Esa tercera frase es fuerte y correcta: como la variante sin guarda **siguió
satisfaciendo** el criterio de wrench en 356 de 360 mundos, el efecto 0,996 no
puede atribuirse al certificado.

*En el cuerpo, sí.* `sections/v2/sp2-compact.tex:213-218` (p. 50):

> «En los tres regímenes de riesgo […] **la guardia física cambió el éxito en
> 0,996**; continuar con reemplazo tras un fallo lo elevó en 0,989 frente a
> detenerse. El Anexo H detalla el protocolo, los cuatro regímenes y las
> ablaciones.»

«La guardia física» es aquí una etiqueta indivisa. El lector del cuerpo —es decir,
el tribunal— recibe un efecto de 0,996 atribuido a un bloque cuyo componente
distintivo, el certificado de wrench, es precisamente el que **no** explica el
efecto. La frase que lo desmiente está a treinta páginas, en un anexo, y el
cuerpo no la anuncia: dice «detalla el protocolo […] y las ablaciones», no
«corrige esta atribución».

Bloque 34 («¿Una ablación elimina una sola variable?») y bloque 35
(«Diferencias de implementación»): **falla en el cuerpo, cumple en el anexo.**
Es un fallo de arquitectura del documento, no de honradez del autor.

### 4.2 Otros dos tratamientos de Cargo también son multifactoriales, y esos no se declaran en ninguna parte

Del mismo bloque `_method_flags`:

| Tratamiento | Banderas alteradas | Confusión |
|---|---|---|
| `perfect_information` | `local=False` | **única.** Limpio |
| `no_repair` | `repair=False` | **única.** Limpio |
| `decoupled_local` («sin acoplamiento espacial») | `spatial=False` | **doble**: `experiment.py:344-347` sustituye la puntuación completa $\bar\delta_i-0{,}08\bar c_i-0{,}025\bar f_i$ por $-c_i$, de modo que también desaparece la preferencia por límite de fuerza, no solo la distancia |
| `central_reference` | `central=True` **y** `local=False` | **doble**: la referencia central es a la vez enumeración exhaustiva **y** información perfecta. No es un contraste «central vs. distribuido», sino «central y omnisciente vs. local» |

La Tabla 16 (p. 50) presenta las seis filas en pie de igualdad y el cuerpo compara
la tasa de misión del híbrido (0,997) con la de la referencia central (1,000) sin
decir que la referencia recibe también la ventaja informativa. Bloque 30,
«Igualdad de información»: **falla** para `central_reference`.

Nota menor: `_central_select` (l. 355-374) invoca `_certificate` de forma
incondicional y no acepta el parámetro `mechanical_guard`, por lo que la
referencia central no es ablacionable en el mismo marco que el resto.

### 4.3 La campaña de CoppeliaSim se admite solo si reproduce el resultado esperado

`pre-thesis/sections/v2/method-coppelia-narrow-v2.tex:15-19` (metodología §4.10,
p. 18), literal:

> «…y **admite la campaña solo si supera seis comprobaciones**: escena guardada,
> cuadros reales capturados, al menos treinta objetos en escena, error de
> reejecución por debajo de 1 mm, y **reproducción tanto del contraejemplo del
> método directo como del éxito seguro del método propuesto**.»

Y en el código, `legacy/tmp/scripts/coppelia/run_sp4_v4_coppelia_paired_scene.py:152-177`:

```python
gates = {
    "scene_saved": ...,
    "real_frames_captured": ...,
    "object_count_at_least_30": ...,
    "replay_tracking_error_below_1mm": ...,
    "direct_counterexample_reproduced": measured[DIRECT]["any_collision"],
    "proposed_safe_success_reproduced": measured[PROPOSED]["safe_success"],
}
passed = all(bool(value) for value in gates.values())
...
return 0 if passed else 2
```

Dos de las seis puertas son **condiciones sobre el desenlace**. Una ejecución en
la que el método directo no colisione, o en la que el método propuesto no
acople con seguridad, se marca `coppelia_real_kinematic_replay_failed_gate` y no
produce campaña admitida. Con **una sola semilla**, esto significa que el
resultado de la Tabla 21 (p. 59) está garantizado por construcción: el protocolo
no podía devolver otra cosa.

El capítulo 6 (p. 59) escribe sin embargo: «La reproducción confirma, en un motor
distinto, la misma conclusión que el modelo cinemático de E4», y §7.7 (p. 66) la
usa como una de las dos evidencias que sostienen OE6 y H6: «la reproducción en
CoppeliaSim […] conserva el resultado cualitativo en un motor distinto del que lo
generó». El argumento es circular: no puede conservar otro resultado.

Bloque 35, «Post-hoc selection» y FASE 12, «Ningún *optional stopping*»:
**falla**. Es el hallazgo de validez interna más grave del documento, porque
afecta a la única pieza de evidencia «independiente» que el capítulo 7 invoca.

### 4.4 El piloto AWS publica el contador de violaciones más favorable de los tres

`scripts/export_aws_industrial2_latex.py:108-110` suma una sola columna:

```python
safe_violations = sum(int(row["safe_barrier_violations"]) for row in comparison_runs)
```

Totales sobre las 32 ejecuciones de `multiscenario_runs.csv`:

| Columna | Total | ¿Se publica? |
|---|---|---|
| `raw_barrier_violations` | **35 561** | no |
| `barrier_projection_interventions` | **45 998** | no |
| `exec_barrier_violations` | **194** | no (solo su residual máximo, `\AwsMaxExecBarrierResidual` $=7{,}602\times10^{-2}$) |
| `safe_barrier_violations` | **2** | **sí**, `\AwsSafeBarrierViolations` |

Las dos violaciones provienen además de **una sola corrida**
(`open_center / replicator_cbf_tfm / semilla 23101`), con residual
$1{,}473\times10^{-5}$. El residual de la trayectoria ejecutada es cuatro órdenes
de magnitud mayor y su recuento (194) no se imprime en ninguna parte.

La frase de p. 53 —«El verificador registró 2 violaciones de la barrera de
seguridad pese a no observar solapamientos muestreados»— y la de §7.9 (p. 68)
—«el verificador registró dos violaciones de barrera bajo el modelo declarado, lo
que basta para exigir una cota continua»— son ambas honradas en su dirección
(usan el 2 para *restringir* el alcance, no para elogiar el método). Pero el
lector no puede saber que existen 194 violaciones en la trayectoria ejecutada.
Bloque 35, «Missing runs / NaNs / Failures eliminados»: **falla por omisión de
columnas**, no por eliminación de corridas.

Divergencia adicional entre ramas: `thesis/sections/mainmatter/06-results-and-analysis/aws-industrial2.tex:16`
**elimina por completo** la frase de las violaciones de barrera y la sustituye por
una sobre bloqueo. Las dos violaciones sobreviven solo en `pre-thesis/`.

### 4.5 Filas idénticas que el documento no comenta

**Tabla 16, p. 50** — «Híbrido vecinal» e «Información perfecta» coinciden en
las cuatro columnas de desenlace:

| | Misión | Intersección | Tiempo [s] | Recuperación [s] | Mensajes |
|---|---|---|---|---|---|
| Híbrido vecinal | 0,997 | 0,000 | 37,40 | 1,42 | 328,1 |
| Información perfecta | 0,997 | 0,000 | 37,40 | 1,42 | 0,0 |

No es coincidencia estadística: `cargo_e2e_hypotheses.tex` registra el contraste
E2E-H4 con efecto **0,000** e intervalo **[0,000; 0,000]** sobre $n=90$ pares.
Diferencia nula en las noventa comparaciones. El significado —que el contrato de
información local fue **inerte** en este banco, y que por tanto el banco no puede
acreditar ventaja alguna de la localidad— no se enuncia en ningún capítulo.
`final-hardening/CLAIM_LEDGER.csv`, CL-28, lo registra como SUPPORTED
(«La informacion perfecta iguala al regimen vecinal con cero mensajes») y el
documento lo convierte en la frase neutra de §7.1 analizada en §1.8.

**Tabla 18, p. 52** — «Sin penalización de congestión» y «Planificación
priorizada» coinciden en entrega, interbloqueo, terminación y espera
(1,000 / 0,000 / 11,49 / 12,08) y difieren solo en mensajes (12,7 frente a 19,3).
La explicación está en el código: `sp7/experiment.py:488` ejecuta la planificación
priorizada como el mismo simulador con `profile = np.zeros(...)` y orden fijo.
Es decir, **el comparador «Planificación priorizada» es, hasta el contador de
mensajes, una ablación del método propio con otro nombre.** Bloque 30,
«¿Está realmente implementado el algoritmo que se nombra?»: **falla**.

### 4.6 Parámetros por método y oráculos privilegiados

- La red neuronal y la imitación lineal se entrenan sobre etiquetas del oráculo
  MILP más un término de moldeado diseñado a mano
  (`legacy/tmp/.../methods.py:848`). Después se comparan **contra ese mismo
  oráculo** en la Tabla del anexo. El documento no lo declara. Bloque 35,
  «Data leakage» y «Oráculos privilegiados»: **falla**.
- Los cuatro «métodos poblacionales» de E2 son una clase con cuatro juegos de
  hiperparámetros ajustados a mano (`distance_weight`, `deficit_weight`,
  `exponent`…). Bloque 28, «Parámetros tuneados por método»: se cumple —todos
  tienen parámetros— pero el documento no informa de cuántos ni de cómo se
  eligieron. La ficha del anexo menciona «Cuatro/cinco parámetros ajustados» solo
  en el *source-snapshot* (`sp2.tex:130`).
- El oráculo se declara correctamente como techo y no como par arquitectónico
  (p. 35 y §4.8, p. 17: «El oráculo no se presenta como competidor distribuido»).
  **Cumple.**

---

## 5. Validez externa

**Es la dimensión mejor resuelta del documento y no se encuentra ninguna
generalización indebida.** El barrido sobre `pre-thesis/sections/**` devuelve casi
exclusivamente cláusulas de **no** transferencia:

| Lugar | Texto |
|---|---|
| Resumen y *abstract* (pp. i–ii) | «No demuestra estabilidad híbrida global, optimalidad social, coordinación completamente distribuida **ni validez industrial**.» |
| `sp1-compact.tex:68` (p. 43) | «**No se transfiere** a Smith muestreado, al cierre QR bajo escasez, a comunicación imperfecta ni a la planta mecánica.» |
| `megajuego-compact.tex:137` (p. 56) | «no generalizan sin nueva demostración a otro número de coaliciones o de contactos» |
| `thesis-results-v2.tex:34` (p. 60) | «acredita coexistencia funcional en su banco numérico, **no convergencia global ni transferencia industrial**» |
| Tabla 22 (p. 60) | regla de composición explícita: cada capa consume el certificado anterior «sin ampliar su dominio» |
| §7.5 (p. 66) | planta planar, pose conocida, contactos fijos; «omite soporte vertical, fricción 3D, deslizamiento, percepción y tracción rueda–suelo»; «la tasa 0.997 **no estima una probabilidad industrial**» |
| §7.9 (p. 68) | «La arquitectura **no debe aplicarse con congestión alta**» |
| §7.7 (p. 66) | «Reproducir un resultado geométrico no es revalidar el certificado que lo respalda.» |

**Población a la que se generaliza, declarada:** cargas planares rígidas
soportadas, AMR de tipo uniciclo, contactos fijos post-acoplamiento, fuerzas
acotadas, grafo estático, pérdidas Bernoulli, una carga simultánea, un fallo
simple, sin percepción y sin hardware. Bloque 36 en sus trece puntos: **cumple**.

**El piloto AWS.** Diseño: 4 escenarios × 4 métodos × **2 semillas** (23100,
23101) = 32 ejecuciones, horizonte 60 s, `evidence_scope:
"multi_scenario_proxy_integration_pilot_not_confirmatory"`. Entregas
(`multiscenario_summary.csv`):

| Escenario | MILP central | CBBA proxy | Predictivo proxy | Replicator+CBF (TFM) |
|---|---|---|---|---|
| `open_center` | **0,00** | 1,00 | 1,00 | 1,00 |
| `industrial_bottleneck` | 0,00 | 0,00 | 0,00 | 0,00 |
| `controlled_cross_traffic` | 0,00 | 0,00 | 0,00 | 0,00 |
| `backlog_and_low_battery` | 0,00 | 0,00 | 0,00 | 0,00 |

El tratamiento en el documento es correcto y, en el conjunto de la memoria,
ejemplar:

- p. 53: «con solo dos semillas por escenario, **ninguna de estas cifras sostiene
  un ranking ni una fiabilidad industrial**».
- §7.1, p. 63: «todos los escenarios congestionados agotaron el horizonte sin
  entregas».
- Tabla 23, p. 62: «tres de los cuatro escenarios del piloto no entregaron carga
  con ninguno de los métodos».
- §7.5, p. 66: «solo tiene dos semillas por escenario y usa **adaptaciones piloto,
  no implementaciones completas de CBBA, ORCA o DMPC**».
- §7.9, p. 68: se convierte en condición de no uso.
- `CLAIM_LEDGER.csv`, CL-32: «Entornos industriales» → **NOT_SUPPORTED**.

Dos reservas menores, ninguna de ellas un fallo de validez externa:

1. La frase de p. 53 —«Replicator+CBF (TFM) igualó a las dos referencias tipo
   subasta (1,00, igual que 1,00 y 1,00) y **superó solo al MILP central
   (0,00)**»— describe dos semillas de un solo escenario. La comparación
   favorable existe únicamente en la celda donde la referencia centralizada
   entregó cero. El calificativo «superó solo al» es prudente, pero la frase
   ocupa tres líneas y el aviso de las dos semillas llega cuatro líneas después.
2. El macro `\AwsTfmDeadlockMin/Max` = 0,467–0,646 (la fracción de tiempo que el
   método propio pasó bloqueado, frente a 0,008–0,010 del predictivo) **no se
   imprime en el cuerpo de la v2**; sí aparece en
   `source-snapshot/.../aws-industrial2.tex:16` y en la rama `thesis/`. Es el dato
   más adverso del piloto y el cuerpo de `main-v2.pdf` no lo recoge.

La única afirmación prospectiva de alcance industrial está en
`01-introduction-impact-v2.tex:9-18` y se autolimita: «**Ninguno de los tres
impactos se cuantifica en esta memoria**; se declaran como el resultado que el
trabajo persigue y frente al cual debe leerse su alcance.» Su fricción no es de
validez externa sino de coherencia con §4.1: el valor industrial que se atribuye
al certificado de *wrench* es justamente el componente que la ablación Cargo
—según el anexo— no consigue aislar.

---

## 6. Fallos, ordenados por gravedad

1. **Cero intervalos de confianza numéricos en 130 páginas arábigas**, contra
   `docs/03_EXPERIMENT_PROTOCOL.md` §7 («Incluir intervalos de confianza»),
   contra Metodología §4.5 («Cada contraste informa el efecto, su intervalo… y el
   valor $p$») y contra la propia Tabla 6, p. 35, que exige «estimando, intervalo,
   tamaño muestral» para elevar un claim. Las 23 macros existen. (§1.1–§1.2)
2. **La puerta de admisión de la campaña CoppeliaSim incluye dos condiciones
   sobre el desenlace** (`direct_counterexample_reproduced`,
   `proposed_safe_success_reproduced`), declaradas en §4.10 e implementadas en
   `run_sp4_v4_coppelia_paired_scene.py:157-158`. Con una sola semilla, la
   Tabla 21 está garantizada por construcción, y §7.7 la invoca como evidencia
   independiente de OE6 y H6. (§4.3)
3. **Pseudorreplicación en cinco de las seis campañas del capítulo 6**: el $n$
   impreso cuenta celdas, no semillas. E4 presenta **6 semillas como $n=108$**;
   E2, **40 como 1560**; E3, 100 como 600; E6-C, 40 como 480; E7-C, 40 como 360.
   Los valores $p$ y los intervalos de esas cinco campañas están calculados sobre
   unidades correlacionadas. `SPTwoWorlds` está además codificado a mano como
   `"1560"`. Cargo sí agrupa correctamente
   (`n_independent_instances`, *bootstrap* sobre medias de conglomerado) y no
   entra en este fallo. (§1.5)
4. **El único valor $p$ del cuerpo se imprime sin su intervalo** — y es el
   resultado negativo, cuya regla de decisión preespecificada (p. 9) está
   formulada precisamente en términos del intervalo. Simétricamente, los dos
   efectos con $p\approx10^{-21}$ y $10^{-27}$ se imprimen sin $p$, sin intervalo
   y sin $n$, con una tabla adyacente que induce el denominador equivocado
   (360 en vez de 270 y 90). (§1.3)
5. **En el cuerpo, la ablación Cargo se atribuye a «la guardia física» como bloque
   indiviso**, cuando retira tres mecanismos y el componente distintivo —el
   criterio de *wrench*— se satisfizo igualmente en 356 de 360 mundos. La
   corrección existe, es explícita y vive solo en el anexo y en la metodología.
   (§4.1)
6. **Brazos ejecutados y no publicados**: 9 de 12 en E3, 6 de 11 en E4, 6 de 13 en
   E2. Entre ellos, **CBBA, Húngaro y BNN, nombrados como métodos comparados en la
   Tabla 9 y sin una sola cifra en todo el documento**; el filtro es explícito en
   `src/viu_mrob_tfm/sp2/evidence.py:174-180`. (§2.3)
7. **«Planificación priorizada» no es planificación priorizada**: es el mismo
   simulador con todas las rutas fijadas a 0 y un orden de servicio fijo
   (`sp7/experiment.py:488`), lo que explica que su fila de la Tabla 18 coincida
   con la de la ablación «sin penalización de congestión» en cuatro de cinco
   columnas. (§2.1, §4.5)
8. **ORCA figura en la Tabla 17 como «Método comparado en E7-C» sin advertir que
   no se ejecutó**, mientras la fila contigua sí marca «no incluidas en el
   comparativo numérico» para CBS/ECBS. No hay ninguna implementación de ORCA en
   el repositorio. (§2.1, §2.5)
9. **La red neuronal y la imitación lineal se entrenan sobre etiquetas del oráculo
   MILP** más un término de moldeado escrito a mano, y después se comparan contra
   ese mismo oráculo. No se declara en ninguna parte. (§4.6)
10. **Las tablas 12 y 13 describen campañas distintas** con nomenclaturas
    inconmensurables (`SP4_DOCKING_GAME_CONFIRMATORY_v3` frente a
    `SP4_DOCKING_GAME_V4_*`) y se presentan consecutivas como si una explicara la
    otra. (§2.5)
11. **Reporte recortado de las comparaciones adversas**: la propuesta de E2
    (0,135) queda séptima de ocho y el cuerpo nombra solo las dos comparaciones
    adversas de mayor prestigio. En E6-C el *endpoint* primario está saturado en
    0,750 para los cuatro métodos con reparación, el efecto publicado es contra
    «no hacer nada», y en el secundario el método propuesto es el peor de los
    cuatro (0,544 frente a 0,596 / 0,596 / 0,583) sin que el cuerpo lo diga.
    (§2.4)
12. **`central_reference` de Cargo confunde centralización con omnisciencia** y
    `decoupled_local` retira también la preferencia por límite de fuerza; ninguno
    de los dos se declara multifactorial en ningún capítulo. (§4.2)
13. **Las seis tablas de hipótesis generadas —ID, $n$, efecto, IC 95 %,
    $p_{\mathrm{Holm}}$— no se `\input` en ningún `.tex` del repositorio.** Son
    artefactos muertos; `cargo_e2e_hypotheses.tex` por sí sola habría resuelto
    tres de los fallos de esta lista. (§1.4)
14. **El piloto AWS exporta el contador de violaciones más favorable de cuatro**:
    2 `safe_barrier_violations` publicadas frente a 194 `exec_barrier_violations`
    y 35 561 `raw_barrier_violations` no publicadas. (§4.4)
15. **El número de remuestreos de *bootstrap* no aparece en ninguna página del
    cuerpo**, pese a que §4.5 lo promete «predeclarado por campaña»; en el código
    conviven cuatro valores distintos (2000, 3000, 5000, 10 000) sin
    justificación, el de E2 no consta en ninguna parte y el de AWS se declara en
    el config sin que ningún artefacto lo consuma. Solo Cargo y el megajuego usan
    una semilla de análisis distinta de las del simulador, como exige
    `docs/03_EXPERIMENT_PROTOCOL.md` §7. (§1.6)
16. **Tres pares IC/$p$ contradictorios impresos sin explicar la lateralidad de
    la prueba** (efecto −0,119, IC [−0,128; −0,111], $p_{\mathrm{Holm}}=1$).
    (§1.7)
17. **«Las variantes vecinal y perfecta completaron el régimen degradado
    ensayado» (§7.1) presenta como coexistencia lo que el dato registra como
    diferencia exactamente nula en los 90 pares** (E2E-H4, IC [0,000; 0,000]):
    la ventaja informativa fue inerte y el banco no puede acreditar la localidad.
    (§1.8, §4.5)
18. **Ninguna campaña del capítulo 6 declara métrica primaria frente a
    secundarias**, ni enumera en el cuerpo las familias sobre las que se aplica
    Holm, ni imprime horizonte o *timeout* salvo en AWS y CoppeliaSim —ni
    siquiera en E4, donde «horizonte agotado» llega a 0,991 en una fila. El único
    lugar del repositorio donde se declaran *endpoint* primario y familias de Holm
    con su $k$ antes de ejecutar es `final-hardening/JCC_STATISTICAL_AUDIT.md`,
    del banco factorial del megajuego. (§3)

21. **Siete de diez campañas carecen de preespecificación**. En E6-C y E7-C las
    hipótesis existen solo como literales de Python dentro de `experiment.py`, sin
    marca temporal que demuestre que preceden a la ejecución. (§3)

22. **H7.2 y H7.3 se calculan con `successful_only=True`**, es decir, comparan
    *makespan* únicamente en los mundos donde ambos métodos entregaron —un
    condicionamiento sobre variable posterior al tratamiento—. Está declarado en
    la columna `successful_pairs_only` y en esta corrida no eliminó ninguna fila,
    pero el mecanismo sesgaría en cuanto un método empeorase. (§1.9)
19. **El denominador de E3 se enuncia de tres maneras distintas** —«7200
    ejecuciones» (p. 45), «600 mundos pareados» (Tabla 11, p. 46), «En 600
    instancias» (p. 63)— sin que el cuerpo aclare la relación 12 brazos × 600.
    (§1.3, §3)
20. **La lista de semillas no está en el manifiesto de E3 ni de E4** (solo es
    recuperable del `runs.csv`), y los generadores de ambas campañas no están en
    el árbol de trabajo (`historical_generator_present_in_worktree: false`), de
    modo que sostienen H2 y el único contraste con $p$ de SP2 sin ser
    reproducibles. (§3)

### Lo que sí cumple y conviene no tocar

- Los fallos, colisiones, bloqueos y agotamientos de horizonte **permanecen en el
  denominador** en todas las tablas verificadas, y se declara tres veces.
- El oráculo se presenta siempre como techo y **nunca** como par arquitectónico.
- `CARGO_E2E_CONFIRMATORY_v1` es una campaña **congelada antes de ejecutarse**,
  con SHA de configuración, de registro de semillas y de *commit*, y **es la
  única del capítulo 6 que clusteriza la inferencia por semilla**. Es el ejemplar
  correcto. El banco factorial del megajuego
  (`megajuego_regeneration_manifest.json` + `JCC_STATISTICAL_AUDIT.md`) lo iguala
  en diseño y lo supera en declaración de familias de Holm y de resultados no
  concluibles.
- E1 y el megajuego usan una semilla por mundo: no hay pseudorreplicación en
  ellos.
- El bloque 36 (validez externa) se cumple en sus trece puntos. El piloto AWS,
  que era el candidato natural a sobregeneralización, se usa en cuatro lugares
  distintos para **restringir** el alcance y en ninguno para ampliarlo.
- Los artefactos de datos ya contienen las etiquetas honradas —«Puntuación
  inspirada en Smith», `smith_ode_integrated_in_campaign: false`— y los anexos las
  reproducen. El problema no es de diagnóstico, sino de qué sobrevivió a la
  compresión al cuerpo de la v2.
