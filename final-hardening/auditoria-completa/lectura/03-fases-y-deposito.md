# Fases y depósito — FASE 0 a FASE 40, más la guía estratégica

**Criterio aplicado:** `pre-thesis/guidelines/05-checklist-por-fases.md` (FASE 0–40)
y `pre-thesis/guidelines/06-guia-estrategica-viu.md` (secciones 0–24), más
`.claude/skills/viu-compliance/SKILL.md` para la normativa oficial. Esos ficheros
son la norma; aquí no se añade criterio propio.

**Artefactos auditados**

| Artefacto | Páginas | Estado |
|---|---:|---|
| `pre-thesis/build-v2/main-v2.pdf` | 146 | compila limpio, 0 errores |
| `pre-thesis/supplementary/build/supplementary.pdf` | 113 | compila limpio, **desactualizado** frente a `references-v2.bib` |
| Cierre activo de `pre-thesis/main-v2.tex` | 89 `.tex` | — |

**Fecha:** 2026-09-19. **Ningún fichero del TFM fue modificado.**

**Informes hermanos cuyas cifras se citan sin repetir:** `mecanica/01-gates.md`,
`mecanica/02-prosa.md`, `mecanica/03-lenguaje-pipeline.md`,
`mecanica/05-referencias-cruzadas.md`, `lectura/06-bibliografia.md`.

> **Aviso sobre la instrumentación.** `final-hardening/census.json` está
> **desactualizado en un fichero**: lista
> `sections/source-snapshot/mainmatter/07-conclusions.tex`, pero `main-v2.tex`
> incluye `sections/v2/07-conclusions-v2.tex`. Toda herramienta gobernada por
> ese censo —incluido `scan_pipeline_language.py` y, por tanto, las cifras de
> `03-lenguaje-pipeline.md`— escanea el fichero de conclusiones **antiguo** y no
> ve el activo. Conviene regenerarlo antes de volver a medir.

> **Segundo aviso de conteo.** Seis regiones `\iffalse…\fi` ocultan **4 figuras
> y 2 tablas** que existen en el fuente y no se imprimen
> (`04-methodology.tex` L43-60, L162-193, L260-281, L377-388;
> `cargo-e2e-v2.tex` L80-98, L151-159). Los recuentos de este informe son
> **sobre lo que se imprime**, salvo donde se indique.

---

## Veredicto en una línea

**No depositable hoy.** Dos fallos duros de norma VIU —anexos 49 pp sobre un
máximo de 20; Resultados 42 % sobre un mínimo del 50 %— más diez P0 abiertos de
la guía estratégica, ninguna preparación de defensa y ninguna congelación.

La ciencia está en mucho mejor estado que la administración. El documento es
honesto hasta el punto de ser su propio auditor más severo: las nueve
confusiones que FASE 8 manda vigilar no sólo se evitan, varias son resultados
del trabajo. Lo que falla es presupuesto de páginas, tipografía, higiene de
entrega y las palabras del título.

**Recuento:** PASA 7 · PARCIAL 22 · FALLA 10 · no evaluable 1 · no alcanzado 1.

**FALLA:** 0 (extensión) · 1 (título) · 6 (referencias/APA) · 17 (tablas) ·
22 (originalidad) · 23 (reproducibilidad) · 26 (anexos) · 34 (defensa) ·
35 (congelación) · 36 (gates).

---

# FASE 0 — REQUISITOS OFICIALES VIU — **FALLA**

## 0.1 Formato obligatorio — PARCIAL

| Regla | Estado | Evidencia |
|---|---|---|
| Plantilla oficial | PASA | `resources/Plantilla memoria TFM_ MROB.docx`, SHA-256 `6b213806a83f7baa…` |
| A4 | PASA | 595 × 842 pt medidos |
| Arial 12 | PASA | `ArialMT`, `Arial-BoldMT`, `Arial-ItalicMT`, `Arial-BoldItalicMT` incrustadas; **ninguna fuente sustituta** |
| Justificado | PASA | bibliografía en bandera (`main-v2.tex:60`), que es práctica APA aceptada |
| Interlineado 1,5 | PASA | `\setstretch{1.4329}`, calibrado contra el `\baselineskip` real de Arial vía fontspec y no contra `\onehalfspacing` (`viu-mrob-thesis.sty:47-59`) |
| **Márgenes** | **FALLA** | 8 páginas invaden la caja — detalle en FASE 28 |
| Portada sin numerar | PASA | `/PageLabels`: p.1 `/D`, pp.2–17 `/r`, p.18+ `/D` |
| Preliminares en romanos | PASA | 16 páginas |
| Cuerpo en arábigos | PASA | desde `budget:body-start`, `\page{1}\abspage{18}` |
| PDF final | PASA | 146 pp, 2 903 786 bytes |
| Encabezado con el estudiante | PASA | «Jorge Luis Mayorga Taborda» |

## 0.2 Extensión — **FALLA: los dos fallos duros**

Medido por `pre-thesis/scripts/report_pages_v2.py` —el guion del propio
proyecto— y confirmado contra los `zlabel` de `build-v2/main-v2.aux`:

```
1. Introducción      5      Preliminares   17
2. Objetivos         2      Cuerpo         69   [OK ] 50-80
3. Hipótesis         3      Referencias    11
4. Metodología       8      Anexos         49   [NO ] <= 20
5. Marco teórico    15      Total         146
6. Resultados       29   [NO ] 42,0 % (mínimo 50 %)
7. Conclusiones      7
```

**Desglose de los 49 pp de anexos:**

| Anexo | Contenido | pp. |
|---|---|---:|
| A–E | Reproducibilidad + demostraciones SP1/SP2/SP3 | 81–88 (8) |
| **F** | **Detalle completo de la revisión** | 88–95 (8) |
| G | Detalle completo de SP1 | 95–102 (8) |
| **H** | **Detalle completo de SP2** | 102–117 (**16**) |
| I | Detalle completo de SP3 | 117–123 (7) |
| J | Detalle completo del juego de integración | 123–129 (7) |

Sobran **29 páginas**.

**Aritmética del 50 %.** Con $R$ = páginas de Resultados y $NR$ = resto del
cuerpo, la norma exige $R\ge NR$. Hoy $NR=40$, $R=29$. Sólo hay dos caminos:

- **Recortar $NR$ en 11 pp** → cuerpo 58 pp (sigue ≥50), $29/58=50{,}0\,\%$.
- **Añadir 11 pp de Resultados** → cuerpo 80 pp, $40/80=50{,}0\,\%$: exactamente
  en el techo, sin margen, y la guía §3 marca **[P0] «No resolver el porcentaje
  con relleno»**.

Recomendación: la primera. Es la única que además descarga los anexos.

**Riesgo adicional sobre el 42 %.** El propio `report_pages_v2.py` informa
«Bloque de revisión dentro de Resultados: 6 páginas». §6.1 (pp. 36–41) es
bibliometría, no validación experimental. Descontándola, la evidencia
experimental propiamente dicha son **23 pp = 33 % del cuerpo**. Se defiende
—§6.1 mapea cada hallazgo a un OE en `tab:results-review-synthesis`— pero
conviene tener preparada la respuesta.

## 0.3 Resumen — PASA

280 palabras (200–300). 5 palabras clave (3–5). Abstract semánticamente
equivalente. Contiene los ocho elementos exigidos, incluidos los dos que casi
siempre faltan:

- resultado negativo principal: «El contraste temporal de H3 no obtuvo apoyo»;
- limitación crítica: «No demuestra estabilidad híbrida global, optimalidad
  social, coordinación completamente distribuida ni validez industrial».

Diferencia menor: el Abstract cuantifica la revisión («3 014 discovered records,
59 canonical works», «fourteen commercial precedents», «167 analytic records») y
el Resumen no. No cambia ningún claim.

## 0.4 Referencias — PARCIAL

APA 7 activa y bien configurada: `style=apa`, `sorting=nyt` (confirmado activo
en la corrida de biber), mapeo `spanish-apa`, delimitador « y », DOI guardados
como `10.xxxx` desnudos y renderizados con prefijo `https://doi.org/`. Orden
alfabético, sangría francesa de 1,27 cm medida sobre el PDF: **PASAN**.

Dos defectos contra esta fase:

1. **Bibliografía metodológica ausente.** VIU exige temática *y* metodológica.
   Las seis entradas metodológicas —`holm1979Sequential`, `demsar2006Statistical`,
   `lakens2013EffectSizes`, `kerby2014SimpleDifference`, `huangfuHall2018Highs`,
   `highs2026Official`— están **huérfanas en la v2**. El documento aplica
   corrección de Holm sin citar a Holm.
2. **32 de 101 entradas citadas** guardan el título en Title Case donde APA 7
   pide sentence case.

«Toda cita tiene referencia»: **PASA**, 0 citas sin entrada.

---

# FASE 1 — IDENTIDAD CIENTÍFICA — **FALLA**

## 1.1 Título — FALLA

Título vigente en portada, `config/metadata.tex:2` y `/Title` del PDF:

> Coordinación distribuida local de múltiples AMR para el transporte cooperativo
> de cargas heterogéneas en entornos industriales

`final-hardening/TITLE_DECISION.md` (2026-09-18) ya fijó ocho decisiones.
**Tres de las seis marcadas «aplicar ahora — dueño: autor» siguen sin aplicar:**

| # | Decisión | Estado real |
|---|---|---|
| 1 | «distribuido/local» sólo para revisión y mensajería | **aplicada** en Metodología; **incumplida en seis sitios de alta visibilidad** (FASE 11) |
| 2 | Arquitectura descrita como híbrida | **aplicada** — 15 ficheros activos |
| 3 | «cargas con **requisitos** heterogéneos» | **SIN APLICAR** — Resumen (`01-summary-v2.tex:7`) y Objetivo general (`02-objectives.tex:12`) siguen diciendo «cargas heterogéneas» |
| 4 | «industrial» sólo como procedencia | parcial — el cuerpo lo califica, el título y el `/Title` no |
| 5 | Tabla de taxonomía de localidad en Metodología | **aplicada** — `tab:results-model-map`, `04-methodology.tex:408` |
| 6 | Definición explícita de «local» en la Introducción | **SIN APLICAR** |
| 7 | Cambio del título de portada | pendiente del tutor |
| 8 | «cargas heterogéneas» sin matiz | condicionado a una campaña no ejecutada |

Palabra por palabra contra la evidencia:

| Término | ¿Demostrado? |
|---|---|
| «Coordinación» | sí |
| «Distribuida» | **no** — E0–E5 y Cargo consultan agregados globales; sólo E6 y E7 son locales. El Algoritmo 1 declara «registro global» y «líder designado globalmente» |
| «Local» | sí, **si** se define como mecanismo de revisión y mensajería vecinal — y esa definición no está escrita |
| «Múltiples AMR» | sí |
| «Transporte cooperativo» | sí, planar y en simulación |
| «Cargas heterogéneas» | **parcial** — SP1 varía la flota, no la carga; la heterogeneidad física está implementada en CoppeliaSim pero su campaña está `COPPELIA_GATE_BLOCKED` |
| «Entornos industriales» | **no** — único respaldo: un piloto derivado de AWS RoboMaker con 2 semillas por escenario, donde 3 de 4 escenarios entregaron cero |

**La tensión está escrita en el propio documento.** El título afirma
«distribuida local» sin matiz; el Resumen dice «No demuestra … coordinación
completamente distribuida» y el Abstract «does not establish … fully distributed
coordination». **Ni el Resumen ni el Abstract contienen una afirmación de
localidad sin cubrir; el título sí.**

La decisión de portada es del tutor. **La decisión 6 —escribir la definición
puente de TITLE_DECISION §5.3— es del autor, cuesta un párrafo, y sin ella el
título es una afirmación no sostenida.**

## 1.2 Pregunta central — PARCIAL

Problema, pregunta, contribución y limitación son inequívocos. La contribución,
verbatim (`01-summary-v2.tex:34`): «una arquitectura verificable de contratos y
juegos locales, más una composición funcional planar».

**Lo que falla es el último punto:** «la tesis completa puede explicarse sin
recurrir primero a códigos E0–E8». No puede. Los encabezados del capítulo 6 son
«E1 — regulación exacta de cuotas», «E2 — servicio operacional heterogéneo»,
«E4 — acoplamiento y transporte», «E6 — recuperación ante fallo», «E7 — juego de
rutas». Hay **300 apariciones de códigos `E0`–`E8`** en el árbol de secciones.
La nomenclatura histórica es la osamenta del capítulo de resultados.

Para la defensa esto es caro: el tribunal tiene que aprender un diccionario
antes de oír un resultado.

## 1.3 Historia científica — PASA

Cadena seleccionar → certificar → transportar → proteger → recuperar → coordinar
tráfico explícita, con qué entrega cada eslabón al siguiente
(`tab:pre-cross-certificates`). Cargo se presenta inequívocamente como
demostrador funcional: «acredita compatibilidad funcional, no validación
integrada de SP1–SP2».

---

# FASE 2 — RQ, OBJETIVOS E HIPÓTESIS — **PARCIAL**

## 2.1 RQ — PASA

Seis RQ en `01-introduction-impact-v2.tex:26-43`, cada una con su OE, cerradas
literalmente una a una en `07-conclusions-v2.tex:64-94` y
`conclusions-megajuego-addendum.tex:7`. Ninguna promete validación fuera de
alcance: RQ6 pregunta si el certificado «sobrevive a un motor de simulación
distinto», no si es válido en hardware. Orden RQ/OE cruzado (RQ2→OE3, RQ3→OE2),
lo que obliga a saltar al leer.

## 2.2 Objetivo general — PARCIAL

Compatible con la evidencia y explícitamente honesto: «arquitectura **híbrida**
e interpretable», no *full-distributed*. No promete hardware ni integración
formal extremo a extremo. El roce: dice «cargas heterogéneas» donde
TITLE_DECISION §3.4 fijó «cargas con requisitos heterogéneos».

## 2.3 OE — PASA

Seis OE, cadena OE → RQ → H → teoría/experimento → resultado completa y
tabulada dos veces (`tab:results-compliance`, `tab:conclusion-hypotheses`).
Ningún OE huérfano. El grado de cumplimiento se declara con honestidad
incómoda: «Parcial», «Teórico», «Delimitado»; OE4 dice «escala y red degradada
no se adjudican en la memoria».

## 2.4 Hipótesis — PASA

Nueve hipótesis (HP, H1a/b/c, H2, H3, H4, H5a/b) más H6. Cada una con variable
independiente, dependiente, dirección, estimando, unidad experimental y regla de
aceptación (`tab:hypothesis-decision-rules`), y familia de multiplicidad
preespecificada.

Los cinco casos que la fase señala por nombre:

| | Estado |
|---|---|
| H1b con la campaña QR | **No adjudicada**, contraste fuera del cuerpo activo — declarado, no escondido |
| H1c cuórum vs lineal | **No adjudicada**, ídem |
| H3 correctamente no sustentada | **Sí**, tres veces, con IC y $p_{\mathrm{Holm}}=0{,}068$ |
| H5b con $A=64$ | **No adjudicada** — es el hueco real (FASE 15) |
| H6 separa prueba de reproducción Coppelia | **Sí**: «Reproducir un resultado geométrico no es revalidar el certificado que lo respalda» |

Salvaguarda que merece nota: «Un intervalo que incluye cero deja una ventaja
direccional sin sustento; **no constituye una prueba de equivalencia**».

---

# FASE 3 — TRAZABILIDAD COMPLETA — **PASA**, con un error que corregir

La matriz maestra existe repartida en tres tablas activas:
`tab:results-compliance`, `tab:conclusion-hypotheses` y
`tab:conclusion-hypothesis-h6`. Ninguna columna vacía. Cada hipótesis tiene
cierre. Cada conclusión procede de Resultados.

Refuerzo mecánico (`mecanica/01-gates.md`): **17 familias de macros activas, 15
trazables a su generador, 0 sin registrar, 0 divergentes.** Ninguna cifra del
capítulo 6 está escrita a mano en el `.tex`.

**Un defecto concreto, y es un error estadístico.** `thesis-results-v2.tex:104`
sigue diciendo que H3 falla «porque el intervalo de confianza contiene cero
**tras el ajuste de Holm**». La cabecera de `07-conclusions-v2.tex:1-6`
documenta que esa misma frase se corrigió allí porque «Holm corrige p-valores,
no intervalos bootstrap», y la tabla de conclusiones ya separa ambas cosas.
**La tabla de Resultados quedó sin el arreglo: dos tablas del mismo documento
dicen cosas distintas sobre el mismo contraste.**

---

# FASE 4 — ORGANIZACIÓN Y FLUIDEZ — **PARCIAL**

## 4.1 Macroestructura — PASA

Orden VIU exacto. La Introducción anuncia la estructura por capítulos. Las
Conclusiones responden literalmente a la Introducción.

## 4.2 Cada capítulo — PASA

Los siete capítulos abren con párrafo introductorio. **Cero encabezados
consecutivos sin texto intermedio** en los 89 ficheros activos, verificado
programáticamente — que es una de las reglas que VIU mira explícitamente.

## 4.3 «No-retazos test» — PARCIAL

| Síntoma | Presencia |
|---|---|
| Nomenclatura histórica innecesaria | **SÍ** — 300 códigos E0–E8 |
| Versiones antiguas de teoría | residuo controlado: `theory-discriminant.tex` y `theory-industrial.tex` en disco **sin `\input`**, declarado en `main-v2.tex:22-25` |
| Conceptos añadidos tardíamente | visible pero honesto: OE6/H6/RQ6 llegan por adenda, y las adendas lo dicen |
| Diferencias fuertes de voz | no detectadas — `lmscan` 1,8 %, «Human-written», confianza alta |
| Repeticiones de introducción | no |
| Bloques que parecen mini papers | **SÍ** — §6.1 (revisión) y §6.5 (juego de integración) |
| Material conservado porque «costó hacerlo» | **SÍ** — Anexo J.5, «Extensión no ensayada» (FASE 26) |

---

# FASE 5 — MARCO TEÓRICO Y ESTADO DEL ARTE — **PASA**

Las seis subsecciones cumplen definir → comparar → criticar → identificar límite
→ justificar decisión. Cinco de seis lo cierran entero.

**La excepción es §5.2** («Información local, juegos y optimización
distribuida»). Compara las cinco dinámicas —BR, replicator, Smith, BNN, logit—
en ecuación y figura, pero **ninguna frase justifica por qué el TFM elige
Smith**. Cierra en «ambas forman parte del contrato implementado», que es un
requisito, no una selección. Es una pregunta de tribunal servida en bandeja.

Calidad de literatura: fundacionales presentes (Kuhn 1955, Khatib 1986,
Tsitsiklis 1986, Shehory–Kraus 1998, Parker 1998 y cuatro más ≤1999).
**24 trabajos distintos de 2024–2026** citados en el cierre del capítulo 5.
Seis *closest prior works* tabulados con su restricción decisiva.

**Debilidad:** una sola revisión reciente llega a la prosa
(`an2023cooperativeReview`), pese a que el corpus contiene 19 *surveys*.

**Citation dumping:** dos pasajes con forma «A hizo X, B hizo Y»
(`05-theoretical-framework.tex:29-36`, cinco trabajos de una cláusula cada uno;
`appendix-review-full-detail.tex:88-93`, dos bloques de 7 y 6 claves). Ambos se
rescatan con una frase de síntesis que asigna función al conjunto.

La taxonomía de nueve categorías de fuentes **no existe**; lo que existe cumple
la función (`tab:method-review-protocol` con «qué certifica / qué no certifica»,
`lit-tab-corpus-layers` con límite de evidencia por capa, y la clave de niveles
del preliminar). Los tres usos prohibidos —fabricante como teorema, patente como
validación, revisión como garantía primaria— **no se cometen**; el más cercano
es una fila que dice «Confirma pertinencia industrial de la capa estratégica»
sobre el corpus patentario, acotada aguas arriba.

---

# FASE 6 — AUDITORÍA DE REFERENCIAS Y APA — **FALLA**

Detalle en `lectura/06-bibliografia.md`. **Falla el gate DZ: 4 de 10 contadores
no están a cero.**

| Contador | Exigido | Real |
|---|---:|---|
| referencias inexistentes | 0 | 0 |
| DOI incorrectos | 0 | 0 erróneos; **4 entradas citadas sin el DOI que existe** |
| citas sin referencia | 0 | **0 — PASA** |
| referencias huérfanas | 0 | **54 — FALLA** (41 + 13) |
| `et al.` indebidos | 0 | **3 impresos, 8 en fuente — FALLA** |
| preprints con versión final | 0 | **2 — FALLA** |
| figuras adaptadas sin atribución | 0 | **7 puntos de `fig:lit-methodological-map` sin cita — FALLA** |

Más: 5 `@article` sin volumen ni páginas, 1 título truncado, 1 norma con título,
URL y estado equivocados, **2 iniciales de primer autor erróneas** (contaminan la
cita en texto) y 34 títulos en Title Case.

**Y el hallazgo de alcance, que es el grave.** `pre-thesis/CITATION_AUDIT.md`
dictamina PASS con 0 UNSUPPORTED, pero audita **`main.tex` y
`monograph/main.tex`, no `main-v2.tex`**. De los 89 ficheros del cierre activo,
**48 no están auditados** —todo `sections/v2/**`— y **28 de las 101 claves
citadas por la v2 no aparecen en su tabla**. La verificación contra Crossref
(`evidence/integrity/bibliography/reference-audit.csv`: 116/116, 112 respuestas
HTTP 200, `verdict PASS`, 2026-09-08) cubre `references.bib` y **nunca ha tocado
`references-v2.bib`**, creado diez días después. **26 de las 101 claves citadas
no tienen verificación de metadatos de ningún tipo.**

El claim-source audit de FASE 6.3 **no está hecho para el documento que se
pretende depositar**.

---

# FASE 7 — NOVEDAD — **PASA**

Claim específico de cuatro cláusulas, `review-compact.tex:31`:

> «En el corpus revisado **no se identificó** una arquitectura que integre, en
> una misma cadena operativa, la selección local de una coalición física
> heterogénea de tamaño variable desde una flota mayor, la verificación mecánica
> de factibilidad de la carga compartida y la recomposición en línea de un
> miembro durante el transporte, manteniendo la decisión de coalición y la
> ejecución sin una autoridad global permanente. […] El enunciado se restringe
> al protocolo de búsqueda documentado y **no afirma inexistencia absoluta**.»

Es exactamente la formulación que la fase pide, y la disciplina se repite en
cinco sitios más («"No documentado" no equivale a inexistencia»; «los ceros
significan "no identificado bajo esta codificación", no inexistencia
bibliográfica»). **Cero usos de «no existe» en contexto de novedad.**

*Closest prior work*: seis trabajos con restricción decisiva por fila; el más
próximo, Shibata et al. 2023; en lo industrial, Beacon Dual-AMR 2026, «el
precedente con mayor solapamiento funcional».

Diferencias declaradas: **6 de 7**.

| Familia | Estado |
|---|---|
| CBBA | presente — «no certifica contacto»; «requeriría una extensión multi-ganador verificada» |
| MILP | presente — «coste global y combinatorio»; «$x_{ik}$ carece de variables de contacto y fuerza» |
| **DMPC** | **ABSENTE** — ni fila en `tab:tf-comparison` ni frase diferenciadora. Aparece sólo como descargo y como antecedente admitido en el Anexo J |
| MAPF | presente — «conflicto discreto no es colisión física» |
| MARL | presente — «entrega una acción, no un predicado verificable con dominio declarado» |
| Manipulación cooperativa | presente — «no selecciona el equipo» |
| Mecanismo de reemplazo | presente, y el más fuerte — «**el reemplazo durante el transporte ya existe**», con tres precedentes y lo que cada uno no resuelve |

No se presenta integración de componentes conocidos como teorema nuevo: el
Anexo J dice «**No se reclama originalidad de esos bloques**» y enumera siete
antecedentes directos.

**Exposición residual.** `thm:megajuego-central-optimum` es la equivalencia
estándar entre desigualdad variacional y minimización convexa para un campo
gradiente, y `prop:megajuego-exact-potential` es álgebra estándar de juegos
potenciales exactos. Ambos viven dentro de una caja «contribución» con
`\estadoaporte{demostrado}` y **sin atribución en línea**, mientras el hermano
`prop:pre-cross-partition-limit` sí la lleva («es una aplicación de un argumento
de indistinguibilidad clásico … no un resultado de imposibilidad nuevo»). Los
cuatro teoremas de potencial exacto (E1, E6, E7, megajuego) son aplicaciones de
Monderer–Shapley y sólo el de E7 lo cita.

---

# FASE 8 — MATEMÁTICA — **PARCIAL**

## Censo real: 29 entornos, **20 resultados distintos**

El «29» de `mecanica/01-gates.md` cuenta **instancias de entorno**. Nueve
resultados se enuncian **dos veces** —una en el cuerpo compacto, otra literal en
el fichero de apoyo del anexo— **con etiqueta distinta**:

| Cuerpo | Gemelo en anexo |
|---|---|
| `prop:sp2-marginal-alignment` | `prop:sp2-marginal-alignment-detail` |
| `prop:sp2-compact-e4-potential` | `prop:sp4-potential` |
| `thm:sp2-compact-e4-pose` | `prop:sp4-pose-stability` |
| `thm:sp2-compact-e6-exact-potential` | `thm:sp6-exact-potential` |
| `thm:sp2-compact-e6-feasible-nash` | `thm:sp6-feasible-nash` |
| `prop:sp2-compact-e6-unbounded-poa` | `prop:sp6-unbounded-poa` |
| `thm:sp3-compact-e7-potential` | `thm:sp7-exact-potential` |
| `prop:sp3-compact-e7-conflict-free` | `prop:sp7-conflict-free` |
| `prop:sp3-compact-e7-no-starvation` | `prop:sp7-no-starvation` |

**29 − 9 = 20.** Un revisor que cuente teoremas encontrará el mismo enunciado
dos veces bajo números distintos. Y el puntero falla: `sp2-compact.tex:67` dice
«demostraciones en el Anexo~\ref{app:sp4-game-proof}», y ese anexo termina
hablando de «La Proposición~\ref{prop:sp4-potential}» — **otro número**. Mismo
patrón en E6 y E7.

Además, **nueve enunciados del cuerpo tienen `refs = 0`**: se enuncian y no se
invocan nunca más.

## Las nueve confusiones — **todas tratadas, y varias son el aporte**

| Confusión | Cómo la trata el documento |
|---|---|
| existencia ≠ convergencia | los teoremas afirman **terminación de caminos de mejora finitos** ($\le(K+1)^N-1$, $\le2^{n_R}-1$), nunca convergencia de la EDO: «La cota cuenta cambios estratégicos aceptados, **no segundos ni rondas globales**»; «garantías de la EDO fuera de esta implementación» |
| convergencia ≠ optimalidad | «cada bloque certifica sólo una mejora local»; «el término $\|\tilde r_k^W\|^2/(2\lambda_D)$ **impide deducir convergencia exacta**» |
| Nash ≠ óptimo social | `PoS`$_6=1$ y `PoA`$_6=+\infty$ «**incluso con un recurso y tres robots**», con contraejemplo explícito. **Hueco: no hay discusión de PoA/PoS para E1, E7 ni el juego de integración** |
| estabilidad ≠ seguridad | «un reparto realizable **no implica estabilidad** fuera del supuesto de contacto fijo y una ruta discreta sin conflicto **no implica ausencia de colisión continua**» |
| seguridad ≠ progreso | «**Una detención puede conservar distancia durante todo el horizonte y terminar sin entrega**» — y es un resultado reportado |
| terminación ≠ entrega | «**Lo demostrado es terminación, no vivacidad** … nada en este argumento obliga a que el objetivo se haya alcanzado al agotarse el presupuesto» |
| no-Zeno ≠ *dwell time* | **el pasaje más fino del documento**: «la ausencia de Zeno **no implica un tiempo de permanencia uniformemente positivo**: una sucesión con $t_{k+1}-t_k=1/k$ no acumula infinitos eventos en tiempo finito y aun así tiene margen ínfimo nulo» |
| rama convexa ≠ híbrido global | «ninguno certifica que el sistema híbrido completo … alcance un óptimo global; **no generalizan sin nueva demostración**». Y: «Un GNE ordinario no basta … **Fijar coalición y homotopía no garantiza por sí solo la convexidad requerida**» |
| factorización ≠ localidad reducida | «**La factorización antes de eliminar estados no prueba localidad de la sensibilidad reducida**» — pero **sólo en el anexo**; el cuerpo presenta la proposición sin ese matiz |

**Ninguna demostración se omite.** Búsqueda de `se omite`, `análoga a`,
`esbozo`, `se deja al lector` sobre los 89 ficheros: **cero aciertos**.

## Lo que baja la nota

1. **Nueve enunciados duplicados** con puntero cruzado a la etiqueta equivocada.
2. **Una demostración sin enunciado.** `appendix-megajuego-detail.tex:102`:
   `\begin{proof}[Demostración del Corolario, óptimo físico nominal dentro de la
   familia]` — **no existe ningún `\begin{corolario}` para ella.**
3. **Cero entornos `\begin{definicion}` en todo el cierre.** El entorno está
   declarado en `viu-mrob-thesis.sty:311` y nunca se usa; toda definición es
   prosa. Es la raíz de FASE 9.
4. **Dos demostraciones de una línea**, ambas en el juego de integración: «Los
   factores no incidentes no cambian y se cancelan»; «Es la condición de primer
   orden de minimización convexa».
5. **Un marcador de estado que contradice a su propio teorema.**
   `megajuego-compact.tex:113` dice
   `\estadoaporte{demostrado, condicionado a … ausencia de Zeno; …}`, mientras
   el cuerpo del teorema en `:125-127` afirma lo contrario: «La finitud de
   $N_{\mathrm{rev}}$ **no requiere suponer ausencia de Zeno**». Arreglo de una
   línea.
6. **Colisión de símbolos declarada y no resuelta:** `z` designa la variable
   continua del bloque, las fuerzas de contacto del QP de *caging* y una
   sustitución auxiliar en la prueba de Bézier
   (`04-nomenclature-megajuego-v2.tex:9`).
7. **5 ecuaciones numeradas nunca citadas** en `appendix-megajuego-detail.tex`
   (el cuerpo está limpio).
8. **La corrección de Holm mal descrita** en `tab:results-compliance` (FASE 3).

---

# FASE 9 — ¿JUEGO O ARQUITECTURA DE CONTINUACIONES? — **PARCIAL**

La fase obliga a decidir: o se define
$\mathcal G=(\mathcal P,Y,\Gamma,J,\mathcal R,F,G)$, o se renombra a
*Arquitectura de Continuaciones Certificadas*.

**De los doce elementos exigidos, 4 están formalizados y 8 narrados.**

| Formalizado | Narrado o ausente |
|---|---|
| **Estado** — `eq:megajuego-state`, $Y=(X,d,\widehat X,\mathcal E_X,\mathcal I,\Pi^{\mathrm{inc}},\mathcal S,t)$ … pero **ningún componente está tipado**: sin dominio para $X$, $d$, $\mathcal S$, sin σ-álgebra para $\mathcal E_X$ | **Jugadores/bloques** — el índice $i$ se usa; el conjunto de jugadores no se declara nunca. «jugador» aparece dos veces, ambas en el ejemplo de dos coaliciones |
| **Potencial** — $\Phi(d,z)=\sum_i\phi_i(z_i)+\sum_a\psi_a(z_{\mathcal I_a})$ | **Información** — $\mathcal I$ es «información con procedencia»; sin mapa de observación, sin partición, sin radio |
| **Payoff** — $J_i=\phi_i+\sum_{a:i\in\mathcal I_a}\psi_a$ | **Acciones/continuaciones** — definidas dentro del texto de una proposición como lista en prosa de siete ítems, no como conjunto de restricciones |
| **Conjunto certificado**, sólo para la rama convexa ($K$ no vacío, cerrado, convexo) | **Regla de revisión** — «se admite sólo si mejora»; formalizada sólo como decremento $\delta$ |
| | **Incumbent** — $\Pi^{\mathrm{inc}}$ está en el estado y en la nomenclatura; sin dinámica, sin regla de selección, sin tipo |
| | **Flow** — **no definido**. Búsqueda de «flujo»: cero aciertos relevantes |
| | **Reset** — **no definido**. «reinicio/reset»: cero aciertos. La única estructura de salto es «tubo», definida **dentro de una demostración** |
| | **Stopping/admission** — parcial: el corte del juego es $W\ge0$; el único test de parada plenamente especificado pertenece al **solver** extragradiente, no al juego |

**No hay ningún teorema sobre el objeto global.** Los cuatro resultados son
(i) una identidad de factorización, (ii) una condición de primer orden de libro
de texto, (iii) una familia Bézier de dos coaliciones, (iv) una desigualdad de
presupuesto. El propio documento lo dice.

**Veredicto:** por la letra de la fase, esto es una *arquitectura de
continuaciones certificadas*, no un juego, y el nombre es lo único que sobra.
El documento se protege con honestidad en el alcance, pero un revisor puede
abrir exactamente por ahí: *«llaman juego a una colección de certificados»*.

Además, **`megajuego-compact.tex:12` imprime «Una formulación previa de esta
misma arquitectura asumía convergencia al óptimo global»**. «Formulación previa»
está en la lista de supresión de FASE 21. La honestidad se agradece; el sitio
para contarlo es el repositorio.

---

# FASE 10 — ROBÓTICA Y FÍSICA — **PARCIAL**

## Declarado, con valores

| Ítem | Valor | Dónde |
|---|---|---|
| Uniciclo | $\dot q_i=[v\cos\theta, v\sin\theta, \omega]^\top$ | `04-methodology.tex:24-27` |
| **Radio de rueda** | **0,1 m** | `appendix-megajuego-detail.tex:141` |
| **Semivía / brazo de bumper** | **0,2 m** (vía 0,4 m) | ídem |
| **Mapa twist→ruedas** | $\dot\varphi_{i,L/R}=(v_{i,\parallel}\mp\ell_i^w\dot\theta_i)/r_i^w$ | `sp2-canonical-bridge.tex:8-13` |
| No-holonomía | nombrada **una vez**, dentro de una demostración | `sp2-canonical-bridge.tex:25` |
| **Par máximo alcanzado** | **0,325989 N·m/rueda**; 4,80260 rad/s; fuerza de pad 0,880001 N; rueda-suelo 3,29597 N; batería 181,543 J/20 s | `appendix-megajuego-detail.tex:96-98` |
| Constantes de motor | $nk_t=0{,}5$ N·m/A, $R=0{,}6\ \Omega$, $\tau_{\max}=1{,}206897$ N·m, $I_{\max}=2{,}413794$ A | `appendix-megajuego-detail.tex:142-148` |
| Masa de carga | **40 kg**, 4 pads en $(\pm0{,}45,\pm0{,}45)$ m; disco de robot r=0,32 m | `appendix-megajuego-detail.tex:88-92` |
| *Wrench* con unidades | $(20,0,5)$ en **N, N, N·m** | `megajuego-compact.tex:96` |
| Matriz de agarre | $W_C=G_C(q)\boldsymbol\lambda_C$ | `05-theoretical-framework.tex:202-208` |
| Fricción / cotas de contacto | $0\le n_i\le30$ N, $|t_i|\le0{,}4\,n_i$, «adherencia tangencial de Coulomb» | `appendix-megajuego-detail.tex:118-121` |
| Bilateral vs unilateral | separados explícitamente | `04-methodology.tex:5-8, 155-160` |
| Radios de sensado/comunicación | 1,8 m / 3,2 m | `04-methodology.tex:365-367` |

## No declarado en ninguna parte del cierre

| Falta | Nota |
|---|---|
| **Masa del robot** | sólo la de la carga |
| **Inercia** | búsqueda de `inerci` en los 89 ficheros: **cero aciertos**. $M_k\succ0$ sin entradas numéricas ni unidades |
| **Mapa directo $(\omega_L,\omega_R)\to(v,\omega)$** | sólo está el inverso |
| **$v_{\max}$, $\omega_{\max}$, aceleración numéricos** | sólo $U_i$ simbólico; `04-methodology.tex:336` promete «los límites de actuación» y nunca los imprime |
| **Cualquier sensor nombrado** | `LiDAR`/`encoder`/`IMU`/`odometría`: **cero aciertos**. Y `cargo-e2e-v2.tex:161` lo desmiente: «Tampoco se modelan soporte, fricción, percepción, **radio real**, tracción ni hardware» |
| **Fricción nombrada como $\mu$** | el 0,4 está embebido en una restricción, nunca se llama coeficiente |
| **Modelo de deslizamiento** | dos menciones, ambas como exclusión |
| **Motor de física de CoppeliaSim** | `Bullet`/`ODE`/`Vortex`/`MuJoCo`: **cero aciertos**. «motor de simulación 3D independiente» nunca se concreta |
| **Paso temporal de CoppeliaSim** | no declarado, aunque `04-methodology.tex:120` promete «Toda simulación digital declara su paso $\Delta t$» |

Pioneer P3-DX se nombra dos veces —12 unidades como recurso de escena
CoppeliaSim, y una campaña MuJoCo futura— y **ningún resultado se deriva de sus
parámetros**.

## 10.4 Realismo — PASA con nota alta

La cadena modelo lógico ≠ simulación cinemática ≠ *physics simulator* ≠ hardware
se respeta, y el artefacto que la sostiene es la columna **«Planta»** de
`tab:results-model-map`: E0/E1/E2 → **«sin planta»**; E3 → «carga estática
planar»; E7/E8 → «grafo discreto»; Cargo → «uniciclo y carga planar en una
misión». Reforzado en cinco sitios, entre ellos: «conflicto discreto **no es**
colisión física»; «evidencia integración lógica y visual, **no contacto físico
ni un gemelo digital**».

## Donde se difumina — es **léxico, no estructural**

El adjetivo *física* va pegado a cuatro objetos que no llevan física detrás:
«continuaciones **físicamente** admisibles» (respaldo: «con **rodadura ideal**,
pads rígidos centrados»); la ablación «sin **guardia física**» (cuyo criterio
«**no usa geometría, torque ni el QP de E3**»); «**factibilidad física**», que es
un chequeo aditivo estático; y «**éxito físico completo**», definido como
incluir comprobación de deslizamiento y pérdida de contacto cuando **ninguna
campaña del cierre mide deslizamiento**. Se arregla renombrando, no
reestructurando.

Una inconsistencia interna: el Resumen dice «El contacto instrumentado, el
hardware y **caging** quedan fuera de la evidencia confirmatoria», mientras
`megajuego-compact.tex:94-109` reporta un certificado QP de *caging* como
resultado.

---

# FASE 11 — AUDITORÍA «DISTRIBUTED» — **PARCIAL**

**La tabla que la fase pide existe y es honesta:** `tab:results-model-map`.

| Etapa | Cierre | Dependencia global declarada |
|---|---|---|
| E0 | discreto global | ocupación o precios globales |
| E1 | QR global | cuotas globales |
| E2 | global | déficit global |
| E3 | global | **QP de *wrench* central** |
| E4 | bilateral/global | pose exacta de carga |
| E5 | no aplica | reparto **central** por carga |
| **E6** | **local por carga** | déficit publicado |
| **E7** | **testigo local** | intención local |
| **Cargo** | líder por carga | **registro global**, líder designado globalmente |

**Sólo E6 y E7 son locales de extremo a extremo.** Y el documento lo remata:
«**Estas dependencias hacen híbrida la arquitectura**».

Las admisiones son ejemplares:

- «El conteo de mensajes y bytes comprende el *gossip*, pero **excluye la
  elección de líder, los atributos y las consultas al registro**. La cifra
  resultante es una **cota inferior**.»
- «**El uso generalizado del déficit global impide atribuir los resultados a una
  implementación vecinal.**»
- «**No se implementa una elección distribuida.**»
- «La **autoridad residual se desplaza a lo global** en certificación y
  recuperación … en vez de presentarse como distribuida.»

## Por qué no es PASA: seis afirmaciones sin matizar, todas en superficies de alta visibilidad

| # | Dónde | Qué dice |
|---|---|---|
| 1 | título, encabezado y `pdftitle` (`metadata.tex:2`) | «**Coordinación distribuida local** de múltiples AMR…» |
| 2 | **encabezado de §6.2** (`sp1-compact.tex:6`) | «SP1: **formación distribuida** de coaliciones» — contradicho por la propia tabla (E1 «QR global», E2 «déficit global», E3 «QP central») |
| 3 | `04-methodology.tex:271` | «SP1 & **Formación distribuida**…» — contradicho 150 líneas después **en el mismo fichero** |
| 4 | `ind-tab-matrix.tex:76`, fila del propio TFM | «…reclutamiento local, **coordinación/control distribuido**…» |
| 5 | `coppelia-compact.tex:28, 40`; también `method-coppelia-narrow-v2.tex:13` y el cierre de RQ6 | «Juego PD **distribuido** + HOCBF (TFM)», «el **juego distribuido** no [colisiona]» — sobre una etapa cuya fila dice «pose exacta de carga», cierre «bilateral/global», y cuyo fichero de apoyo declara «**calcula centralmente el agregado de transporte; no ejecuta el estimador vecinal**» |
| 6 | lienzo de `fig:problema` | «…**sin coordinador central**» dentro del dibujo; el matiz está 100 líneas más allá, en el pie |

**El documento tiene la rúbrica correcta y no se la aplica.**
`appendix-review-full-detail.tex:44-47`, sobre *otros* trabajos:

> «**"Distribuido" no se asigna por la presencia de control local**, sino por la
> combinación de autoridad de decisión, información disponible, existencia de
> líder o servidor y responsable del cierre, de modo que **un método con control
> local y adjudicación centralizada se codifica como mixto**.»

Por su propia rúbrica, SP1 y Cargo son **mixtos**. No hay ninguna frase en el
documento que asigne al TFM un nivel LOCAL/MIXTA/GLOBAL o C0–C4.

Dos huecos más: `tab:results-model-map` **no tiene fila para el juego de
integración ni para CoppeliaSim** —los dos bloques nuevos de la v2 no tienen
contrato de localidad declarado— y **no se declara ningún número de saltos** en
ninguna parte (`n-hop`/`k-hop`: cero aciertos).

---

# FASE 12 — DISEÑO EXPERIMENTAL — **PARCIAL**

Nueve campañas activas. El protocolo transversal que suple lo que falta por
campaña está en `results-interface.tex` (`tab:pre-results-protocol`): «Congelar
mundo … Ejecutar sin selección: se corren coaliciones aceptadas y rechazadas,
**los fallos no se eliminan** … Corregir multiplicidad: la familia de hipótesis
y Holm se fijan antes del confirmatorio».

Declarado en todas o casi todas: pregunta, hipótesis, unidad experimental,
tratamientos, factores y niveles, baselines, ablaciones, oráculos, *endpoint*
primario y secundarios, definición de éxito/fallo, retención de datos brutos.

**Huecos sistemáticos:**

| Ítem | Dónde falta |
|---|---|
| Horizonte | declarado sólo en E4 (35/45 s), E7 (48 pasos), AWS y Coppelia (120 s); **ausente en E2, E3, E6 y el juego de integración** |
| Timeout | ídem |
| Rango de semillas explícito | **E4** («seis semillas», sin rango), **Cargo** («30 semillas», sin rango), **AWS** («2 semillas», sin identificar). Sí explícito en E2 (3100–3139), E3 (461000–461099), E6 (8600–8639), E7 (8700–8739), Coppelia (886001) |
| Preespecificación por hipótesis | genérica en E4, E6, E7 y Cargo; explícita sólo en E2 y E3 |

Nada de *optional stopping*: prohibido por escrito y con el diseño congelado
antes de ejecutar en `megajuego_regeneration_manifest.json`, commit `73b0b720d`.

---

# FASE 13 — ESTADÍSTICA — **PARCIAL**

El plan estadístico es correcto y, en algunos puntos, ejemplar:

| Ítem | Estado |
|---|---|
| Mundo/semilla = unidad independiente | **sí, y declarado**: «los 8 AMR, 2 cargas, *timesteps* y rondas de mercado **no** son réplicas» |
| Pareamiento preservado | sí |
| McNemar exacto para binario pareado | sí — E6, E7, Cargo y el protocolo |
| *Paired bootstrap* | sí — 10 000 remuestreos, 0,95, **semilla de análisis 20260918 distinta de las del simulador** |
| Wilcoxon | sí, unilateral sobre la media por instancia |
| Friedman | sí, E2 |
| Holm por familia coherente | sí, cuatro familias predeclaradas F1–F4 |
| $n$ explícito | mayoritariamente vía macro (E2 1560, E3 600, E6 480, E7 360, Cargo 360/2160). **Débil en E4**; `n=1` declarado en Coppelia y en el e2e del juego |
| Fallos y timeouts en el denominador | **sí, por escrito**: «Colisiones, bloqueos, errores numéricos y agotamientos del horizonte **permanecen en el denominador**» |
| Sin «no significativo = equivalentes» | **cumplido y defendido activamente**: «Esta coincidencia describe un *benchmark* poco discriminante … **y no prueba equivalencia**» |
| Sin causalidad desde contraste no causal | **cumplido, con dos autocorrecciones**: «el diseño **no identifica ese mecanismo causal**»; «No se aislaron causalmente la batería ni sus procesos» |

**Por qué PARCIAL: los intervalos de confianza no llegan al PDF.**

La fase exige «IC del efecto». En las 146 páginas del documento activo, la
cadena «intervalo de confianza» aparece **dos veces**: como *regla* en la tabla
de protocolo de la p.52, y en la fila de H3 de la tabla de conclusiones. **No
hay un solo IC numérico en ninguna tabla de resultados del cuerpo.** Sobreviven
12 valores de $p_{\mathrm{Holm}}$ y nada más. Las tablas generadas son
estimaciones puntuales sin $n$, sin SD y sin IC —
`sp7_results.tex` → `Juego + reserva local & 1.000 & 0.000 & 7.49 & 2.82 & 15.8`.

Los IC numéricos **sí existían** en la v1: `source-snapshot/.../sp1.tex` imprime
`IC~95\%: [-12,07, -9,83]`. **No sobrevivieron a los ficheros `-trimmed` que la
v2 incluye.** La compactación del capítulo 6 se llevó por delante la
incertidumbre reportada, que es justo lo que la fase pide mostrar.

Salvedad adicional: la Parte II de `JCC_STATISTICAL_AUDIT.md` sigue marcada
«*(pendiente de la ejecución)*» aunque `results/megajuego_regen_v1/STATISTICS.csv`
existe en disco. El documento de auditoría nunca se cerró.

---

# FASE 14 — COMPARADORES — **PASA**

Doce comparadores, **cada uno etiquetado con lo que realmente es**:

| Comparador | Etiqueta honesta, verbatim |
|---|---|
| MILP | «certificado de optimalidad con brecha cero» — usado como **techo** |
| Hungarian | «exacto para el LAP expandido; **capacidad aproximada**»; «**sólo referencia escalar**» |
| CBBA | «**garantía CBBA original inaplicable**»; «Subasta marginal … **no equivale a CBBA completo**» |
| Replicator/BNN/Smith | «garantías de la EDO **fuera de esta implementación**» |
| CBS/ECBS/LA-MAPF, ORCA, SCP | «**no incluidas en el comparativo numérico**» |
| AWS Industrial 2 | «Subasta, reciprocidad y predictor son ***proxies* que no reproducen CBBA, ORCA o DMPC**» |

La regla arquitectónica está escrita, `results-interface.tex:57`:

> «cuando un oráculo usa información global, se presenta como **techo** y no
> como **par arquitectónicamente equivalente**.»

Misma planta, escenario, horizonte y unidad: afirmado y cumplido en E2, E3, E6,
E7, Cargo y Coppelia. **La excepción se autodeclara**: «Esta campaña carece de
una ejecución extremo a extremo: el estrato de acoplamiento no mueve la carga y
el de transporte comienza ya acoplado» (E4).

Ausencia menor: no hay comparador aleatorio en ninguna campaña.

---

# FASE 15 — RESULTADOS NEGATIVOS — **PASA**, con un hueco

Ocho de los nueve ítems están presentes, citados y promovidos a «fronteras del
mecanismo»:

| Ítem | Presencia |
|---|---|
| H3 | ×3, con IC y $p_{\mathrm{Holm}}=0{,}068$ |
| Industrial 2 | ×4 — «tres de los cuatro escenarios **no entregaron carga con ninguno de los métodos**» |
| *trade-off* seguridad–progreso | «evitó colisiones, pero **agotó el horizonte**»; «el residual del problema congelado **no funciona como proxy de vivacidad**» |
| peor Nash | `PoA`$_6=+\infty$ «incluso con un recurso y tres robots» |
| no-convergencia / sin óptimo global | `prop:pre-cross-partition-limit` + tres frases de alcance |
| timeouts e interbloqueos | Coppelia «120,0 s (agotado)»; «un reemplazo agotó el horizonte» |
| residual de barrera tras actuación | «el verificador contabilizó violaciones de la desigualdad de barrera», escalado a «**dos violaciones de barrera** … basta para exigir una cota continua» en las condiciones de no uso |
| teoremas fallidos/limitados | en el **suplemento**: «CONJECTURE 2; DUPLICATE 16; FAIL 43; LIMITED 87; PASS 18» |

Otros negativos que podrían haberse escondido y no se esconden: primal–dual peor
que *greedy*; la regla marginal por debajo de la red neuronal no certificada y
del oráculo MILP; E6 con éxito por debajo de *greedy* bajo plazo ajustado; el
oráculo conservando ventaja de tiempo de ruta; la referencia central puntuando
por encima del demostrador Cargo.

**El hueco: H5b a escala $A=64$.** El resultado existe —`sp8.tex:177`: «La
coordinación se degradó con la escala hasta alcanzar **tasa cero en $A=64$**»—
pero `sp8.tex` **no está en el cierre activo**: vive en el suplemento. La cadena
`A=64` no aparece en ningún `.tex` activo de `pre-thesis/`.

Es defendible como decisión de alcance, pero es el único de los nueve ítems que
se resuelve **retirando** el negativo en lugar de integrarlo, y H5b es una
hipótesis declarada en el cuerpo que se queda sin cierre empírico.

---

# FASE 16 — FIGURAS — **PARCIAL**

**28 figuras impresas** (32 en fuente, 4 ocultas por `\iffalse`).
**24 vectoriales / 4 raster.**

**Resolución efectiva de las cuatro raster — todas correctas:**

| Fichero | px | colocado | dpi efectivo |
|---|---:|---|---:|
| `sp4-v4-paired-trajectories.png` | 2280×1040 | p.76, 391×178 pt | **420** |
| `rutas-deformadas.png` | 1800×1080 | p.74, 349×209 pt | **372** |
| `stopgo-vs-cooperativo.png` | 1800×900 | p.74, 349×174 pt | **372** |
| `aws-industrial-oblique-camera.png` | 1280×960 | p.139, 213×159 pt | **433** |

Más portada JPEG (2481×3509, 300 dpi) y el logo de encabezado (~273–292 dpi en
las 146 páginas). **Ninguna figura de baja resolución.** Las tres PNG de gráfico
serían mejores en vectorial, pero no pixelan al tamaño impreso.

**Fuente en el pie: 32/32 figuras (100 %).** No la lleva en el `\caption` sino
en un macro dedicado dentro del flotante (`\viusource` ×12 con procedencia
explícita, `\viuownsource` ×20). Comprobado en el PDF: p.44 cierra
«*Elaboración propia.*», p.74 «*Fuente: simulación propia,
simulate_e2e_megagame.py.*».

**Clipping: ninguno.** 8 *overfull hbox*, máximo 4,80 pt; dos están dentro de un
`figure` y ambos en el **pie**, no en el gráfico. Ningún *overfull* dentro de un
`tikzpicture`.

## Los tres defectos reales

1. **Sin barras de error, sin $n$, sin IC en los pies.** «barras de error»:
   **0 apariciones** en fuente y en PDF. Sólo 3 de 32 pies contienen vocabulario
   de $n$/incertidumbre, y ninguno es una medida de dispersión. Enlaza con
   FASE 13: la incertidumbre no llega al lector.

2. **8 figuras nunca citadas por su número** —de 19 flotantes huérfanos totales
   (`mecanica/05-referencias-cruzadas.md`); descontados los ocultos por
   `\iffalse`, quedan 8 figuras + 7 tablas. Entre ellas
   `fig:coppelia-narrow-trajectories`, `fig:megajuego-routes`,
   `fig:megajuego-stopgo` y `fig:pre-results-provenance`. **VIU exige que toda
   figura numerada se cite por su número en el texto.**

3. **Escala de grises: falla para las series, pasa para la matriz de
   capacidades.** Hay que separar los dos casos.

   - **La matriz de capacidades está bien resuelta a propósito**: los glifos son
     **de forma**, no de color —`\capyes` disco relleno, `\cappart` media luna,
     `\capno` círculo vacío, `\capgoal` diana hueca— y el comentario del fichero
     registra que `\capgoal` se cambió deliberadamente para que no leyera como
     capacidad demostrada. Eso sobrevive al blanco y negro y al daltonismo.
   - **Las tintas de serie, no.** Las seis caen en una banda de nueve puntos de
     luminancia:

     | Color | Hex | Luminancia | % gris |
     |---|---|---:|---:|
     | SPBlue | `2369BD` | 93,6 | 37 % |
     | SPRed | `C63C32` | 100,1 | 39 % |
     | SPGreen | `2D8A57` | 104,4 | 41 % |
     | SPPurple | `7A58A6` | 107,1 | 42 % |
     | VIUGray | `6B7280` | 113,5 | 45 % |
     | VIUOrange | `E65113` | 118,5 | 46 % |

     Impresas en blanco y negro, **ninguna pareja se distingue**; y SPRed/SPGreen
     es además el par clásico de deuteranopia, a cuatro puntos de distancia. Sin
     simulación CVD ejecutada, los pares sin comprobar del mapa metodológico son
     `gamecol` (#2D6CC0) vs `foundcol` (#6F7C8E) y `searchcol` (#2E9B5F) vs
     `learncol` (#7B4DBA).

   Se arregla con marcadores, tramas o estilos de línea, no necesariamente
   cambiando la paleta — que es exactamente lo que la matriz de capacidades ya
   hace bien.

---

# FASE 17 — TABLAS — **FALLA**

42 tablas impresas (44 en fuente, 2 ocultas). Las de resultados distinguen
oráculo/proxy/ablación y, cuando hay $n$, lo declaran con honestidad (dos pies
dicen literalmente «$n=1$, sin réplicas»).

**El fallo es tipográfico y es el defecto más serio del documento a la vista.**

| Medida sobre el PDF | Valor |
|---|---:|
| Caracteres por debajo de **8 pt** | **31 949** |
| Caracteres por debajo de **7 pt** | **9 222** |
| Glifo más pequeño | **2,6 pt** |
| Llamadas explícitas `\fontsize{<8}` | **181**, en 22 ficheros |
| Tablas con `\resizebox{\textwidth}{!}{…}` | **12** (factor de reducción no acotado) |
| Tablas con `\scriptsize` / `\footnotesize` / `\small` | 8 / 3 / 3 |

Peores páginas: **p.44 (1 044 caracteres bajo 7 pt), p.54 (939), p.57 (884),
p.55 (875), p.49 (791), p.47 (639), p.110 (579)**. Los mayores generadores son
las figuras y tablas portadas de la revisión: `ind-fig-patents.tex` (27 llamadas,
hasta 4,0 pt), `lit-fig-stage-coverage.tex` (16, hasta 4,6 pt),
`05-theoretical-framework.tex` (14, hasta 4,2 pt), `ind-tab-matrix.tex` (10,
hasta 4,9 pt).

Con Arial 12 de base, `\scriptsize` son ≈8,2 pt; `\resizebox` va mucho más abajo.
**Afecta precisamente a las tablas que el tribunal más va a mirar**:
`tab:hypothesis-decision-rules`, `tab:conclusion-hypotheses`,
`tab:conclusion-hypothesis-h6`, `tab:results-compliance` y
`tab:results-model-map` están todas en `\scriptsize`.

Defectos adicionales:

- **7 tablas nunca citadas** por su número, incluidas
  `tab:conclusion-hypothesis-h6` (el estado final de H6),
  `tab:sp2-compact-cargo-results` y `tab:sp1-compact-e2-ablation`.
- **1 tabla sin `\caption` y sin fuente**: la clave de evidencia en
  `frontmatter-evidence-key.tex:10` — incumple «procedencia o fuente» por partida
  doble. Las otras 43 sí la llevan.
- **Sin unidades en ningún pie**; aparecen sólo en cabeceras de columna
  generadas y de forma inconsistente (`CPU [ms]` las tiene; `Terminación`,
  `Espera`, `Mensajes`, no).
- **Sin IC** (FASE 13).

---

# FASE 18 — ECUACIONES — **PASA**

Auditoría independiente sobre el cierre con las regiones `\iffalse` retiradas:

- **50 `\label{eq:…}`**, 0 duplicadas.
- **0 nunca referenciadas** — las 50 se citan por número. ✔
- **0 `\begin{equation}` sin `\label`** — ningún display numerado huérfano. ✔
- Las 50 etiquetas están dentro de entornos genuinamente numerados (ninguna
  perdida en `\[…\]`, que las desnumeraría).
- Censo: `equation` 46, `align` 2 (2 etiquetas cada uno), `align*` 1
  intencionalmente sin numerar.
- Notación consistente entre memoria y suplemento: comparten
  `config/math-commands.tex`, lo que lo hace estructural y no casual.
- Unidades declaradas: «Los costes estratégicos se expresan en escala
  normalizada; las variables físicas usan unidades SI».

Dos observaciones menores: **61 displays `\[ … \]` sin numerar**, alguno con
contenido citable —la clasificación de falsos positivos
$\mathrm{FP}_{gw}=\mathbf1\{A_{gw}=1, Y_{gw}=0\}$ de la p.52 es una definición
operativa que merecería número—; y **5 ecuaciones numeradas y nunca citadas en
`appendix-megajuego-detail.tex`** (el cuerpo está limpio).

Es la fase mejor resuelta del documento.

---

# FASE 19 — PSEUDOCÓDIGO — **PARCIAL**

**3 algoritmos** (`algorithmicx`; no hay `algorithm2e`, `lstlisting`, `verbatim`
ni `minted`). El PDF numera `Algoritmo 1`, `2` y `3`.

| # | Fichero | `\Require`/`\Ensure` | Complejidad | Citado |
|---|---|---|---|---|
| 1 | `sp2-compact.tex:176` | ✔ | ✘ | **0** |
| 2 | `cargo-e2e-v2.tex:36` | ✔ | ✔ $O(\|I^{\mathrm{vis}}\|\log\|I^{\mathrm{vis}}\|)$ + $O(\|E_C\|)$ | **0** |
| 3 | `sp3-e7-trimmed.tex:84` | ✔ | ✘ | 1 |

Calidad interna del Algoritmo 2, revisado línea a línea: sintaxis
`\While`/`\If`/`\Return` correcta, indentación coherente, sin `si no devolver`,
`\Ensure` que contempla los tres desenlaces («entrega en pose destino, **o
abstención, o fallo declarado con su causa**»), y —notablemente— **declara sus
propias dependencias globales en el `\Require`** («registro global de
atributos»), lo que lo hace coherente con FASE 11 en vez de contradecirla.

Tres defectos:

1. **Los Algoritmos 1 y 2 son casi duplicados**: el mismo demostrador Cargo,
   compactado en el cuerpo y completo en el anexo, con dos etiquetas y **dos
   números de algoritmo para un solo procedimiento**.
2. **Dos de los tres nunca se citan** por su número en el texto.
3. **Ninguno indica su correspondencia con código real.** No aparece nombre de
   guion, ruta, función ni módulo en el entorno ni junto a él. La procedencia
   que sí existe (`viu-run-sp2`,
   `experiments/configs/sp2_effective_capacity.yaml`) vive en
   `mecanica/01-gates.md`, **no en la memoria** — y el Anexo A, que debería
   recogerla, está vacío (FASE 23).

---

# FASE 20 — REDACCIÓN ACADÉMICA — **PARCIAL**

Voz única confirmada por medición: `lmscan` **1,8 % — «Human-written», confianza
alta**. Cero léxico de *hype* («novedoso», «innovador», «revolucionario»,
«significativamente»: 0 apariciones cada uno). Las 12 apariciones de «garantiza»
son todas técnicamente correctas y acotadas.

Tres defectos, uno visible a simple vista:

1. **Acentos ausentes en toda una subsección del anexo.**
   `appendix-megajuego-detail.tex:225-235` —Anexo **J.5**— está escrito sin un
   solo acento y sin eñe:

   > `\subsection{Extension no ensayada: actualizacion de informacion por diferencias}`
   > «La informacion … de la Ecuacion … la ultima version … No se implemento ni
   > se evaluo … menor trafico, decision mas temprana … perdida o retardo. Su
   > especificacion, la regla de admision y el **diseno** experimental …»

   Doce palabras mal escritas, una en un **encabezado que aparece en el índice**.
   Es la **única** región del documento afectada —el escaneo del cierre activo
   completo devuelve 12 aciertos, los 12 en este fichero—, así que es trivial de
   corregir y caro de dejar: VIU pide «ortografía y gramática impecables» y esto
   lo ve cualquiera que hojee el índice.

2. **Párrafos de menos de tres oraciones.** VIU lo prohíbe explícitamente.
   `mecanica/02-prosa.md` marca **174 párrafos con hallazgos**. La peor
   concentración está en `results-review.tex`, donde **cinco párrafos
   consecutivos de una sola oración** alternan con `\input` de figuras (líneas
   12–14, 18–20, 26–29, 33–35, 39–42).

3. **Ritmo plano.** Desviación típica de longitud de frase por debajo del mínimo
   de 8 en 13 ficheros, incluidos `01-introduction.tex` (7,0),
   `05-theoretical-framework.tex` (5,9), `thesis-results-v2.tex` (5,9) y
   `04-methodology.tex` (6,2). No es un fallo de norma; es lo que hace que un
   texto correcto se lea como generado.

Frases de más de 50 palabras: 15 reales en prosa.

---

# FASE 21 — AI-WRITING / «TALLER INTERNO» — **PARCIAL**

**Lo que la fase teme y aquí NO ocurre**, verificado sobre el texto extraído del
PDF y no sólo sobre el fuente: `PASS`, `FAIL`, `LIMITED`, `complete=true`,
`.yaml`, `.json`, `experiments/configs`, «humo acotado», `monograph`,
`commit` → **0 apariciones impresas cada uno**. Los 11 aciertos de cadenas
hexadecimales largas son DOI de la bibliografía. `pipeline` aparece 6 veces en
el fuente y **0 en el PDF**: son todas `\label{fig:…-pipeline}`, invisibles.

**Lo que sí llega al lector:**

| Término | En fuente | **Impreso** | Páginas |
|---|---:|---:|---|
| `claim` | 8 | **3** | p.52 (2), p.53 |
| `claim-ID` | 1 | **1** | p.52 |
| `gate` | 5 | **3** | p.17, 52, 53 |
| «formulación previa» | 1 | **1** | p.71 |
| rutas `.py` / `.csv` | 11 | 11 | pp. 55, 56, 74, 76 |
| `thesis/resources/…` | 1 | **1** | **p.75** |

**El peor sitio es la Tabla 6, p.52** (`results-interface.tex:75`), verbatim:

```
Elevar un claim | Solo un gate aprobado cambia 'PENDIENTE' o 'PARCIAL' a 'SOPORTADA'.
                | claim-ID, supuesto, prueba o artefacto y destino
```

Una sola tabla concentra `claim` ×2, `claim-ID`, `gate`, `artefacto` y tres
estados de CI. Es el único lugar donde el lector se encuentra el flujo de
trabajo de software sin disfraz. **Y arrastra un error tipográfico:** las
comillas simples de LaTeX salen como `‘PENDIENTE‘`, comilla de apertura a ambos
lados.

**Dos hallazgos más:**

1. **`Resultado y alcance:` aparece 16 veces en el PDF**, no una. Sólo una es
   cabecera literal de tabla; las otras 15 las emite el macro `\estadoaporte`
   (`viu-mrob-thesis.sty:348`) en diez ficheros. **Quince run-in en negrita con
   idéntica redacción es una firma de plantilla inconfundible**, y es exactamente
   lo que la fase señala como «repetir "Resultado y alcance" mecánicamente».
2. **`certific*` = 176 apariciones impresas**, ≈1,25 por página
   (`certificado` 80, `certifica` 51, `certificación` 16, `certificados` 15,
   **`certificate(s)` 11 — inglés sin traducir en una memoria en español**). El
   patrón fijo «certifica: … / no certifica: …» se repite ×20/×10 como nodo TikZ
   en las figuras de composición de SP1/SP2/SP3 (pp. 59, 64, 68, 71).

**Lo bueno:** los 21 `\estadoaporte` son prosa académica en su contenido
(«demostrado para $\Lambda_k$ cerrado, convexo y no vacío»), no etiquetas de
máquina; y «no certifica» 19 veces es repetitivo pero es el tipo de precisión que
esta memoria necesita. El preliminar «Guía de lectura y niveles de evidencia» es
defendible como convención académica, pero su columna «Soporte exigido» dice
«contraejemplo o **gate incumplido**», que conviene reescribir.

---

# FASE 22 — ORIGINALIDAD / TURNITIN — **FALLA**

**No existe informe Turnitin ni iThenticate en el repositorio.**
`pre-thesis/evidence/administrative-gates.md` lo registra como
`PENDIENTE_EXTERNO`.

Lo que sí existe:
`pre-thesis/evidence/integrity/originality/originality-report.md`, «PASS integral
con P3», 2026-09-09. Método serio: 279 párrafos de memoria, 90 muestreados
(32,3 %), diez estratos; dos consultas web por párrafo; 202 filas, todas
`ORIGINAL`, solapamiento abierto máximo de 4 palabras consecutivas. Comparación
contra el TFG Uniandes 2014 (texto completo, 188 ventanas) y contra el artículo
IECON 2015. **Su propia prioridad #1 es ejecutar Turnitin.**

**Pero el alcance es el mismo problema que en FASE 6:** los artefactos sellados
son `main.tex` → `build/main.pdf` (97 pp) y `monograph/main.tex` (110 pp).
**`main-v2.pdf` (146 pp) y `supplementary.pdf` (113 pp) no están cubiertos.** La
prosa exclusiva de la v2 —resumen, abstract, objetivos, hipótesis, conclusiones,
revisión compacta, juego de integración, CoppeliaSim y cinco anexos de detalle—
**nunca ha pasado ningún cribado**.

| Requisito del gate | Estado |
|---|---|
| 0 texto ajeno sin cita | no verificado para la v2 |
| 0 figuras adaptadas sin fuente | **FALLA** — 7 puntos de `fig:lit-methodological-map` dibujan trabajos sin `\cite` |
| 0 referencias falsas | PASA para `references.bib`; **no verificado** para `references-v2.bib` |
| 0 paráfrasis demasiado próximas | no verificado para la v2 |
| citas literales identificadas | PASA (`csquotes`) |
| **main/suplemento deduplicados** | **FALLA** |
| historial de autoría conservado | PASA |

**Duplicación main ↔ suplemento: 7 ficheros de prosa, ≈5 933 palabras idénticas
en los dos PDF.** El mayor es **el capítulo completo de Marco teórico**
(≈3 800 palabras), incluido por `main-v2.tex:106` y `supplementary/main.tex:87`.
Los otros seis: `06-sp4-proofs`, `method-comparison`, `08-sp7-proofs`,
`intro-contracts`, `aws-industrial2`, `04-sp2-proofs`.

Agravante: `supplementary/main.tex` **no declara que ese capítulo sea
reproducción**, y `main-v2.tex` **no cita el suplemento en ninguna parte** —no
hay entrada bibliográfica— pese a que la cabecera del suplemento afirma «Se cita
desde main-v2.tex como Anexo 2». **Si los dos PDF entran en la misma entrega
Turnitin, el marco teórico se auto-coincidirá.**

Dos condiciones abiertas que el propio informe deja sin resolver: (a)
confirmación escrita de que `paper/` y `work/` están inéditos —encontró 1
coincidencia exacta y 1 alta de `work/` hacia la monografía—; (b) decisión sobre
si el TFG Uniandes 2014 es antecedente conceptual que exija cita.

---

# FASE 23 — REPRODUCIBILIDAD — **FALLA**

**Lo que está bien, y está muy bien:** la cadena dato → macro → figura → frase.
17 familias de macros activas, 15 trazables a su generador, **0 sin registrar, 0
ausentes, 0 divergentes**. 22 puntos de entrada de consola en `pyproject.toml`.
51 configuraciones en `experiments/configs/`, **49 con semillas** (las dos sin
ellas son `sp3_wrench_evidence.yaml` y `sp5_safety_evidence.yaml`, y la primera
alimenta macros activas). `requirements.lock` con 6 pines exactos.

**El fallo es que nada de eso llega al PDF depositado.**

`pre-thesis/sections/source-snapshot/appendices/01-reproducibility.tex`
—que contiene la URL del repositorio, el commit base auditado
(`9278953cb6affeba…`), el entorno de referencia (Windows 11, Python 3.13.9,
NumPy 2.3.5, pandas 2.3.3, SciPy 1.16.3) y la tabla regenerable/reanálisis por
campaña— **está huérfano**: lo incluye únicamente `thesis/main.tex`, que es
**otro documento**. No está en los 89 ficheros del cierre activo.

Lo que compila como Anexo A es un párrafo de nueve líneas al principio de
`sections/thesis-appendices.tex`: **sin URL, sin commit, sin versiones de
entorno, sin política de semillas, sin tabla, sin nombrar un solo guion**. El
«A … 0 pág.» del informe de gates es un artefacto de medición (A y B empiezan en
la misma página), pero el fondo es real: **el anexo de reproducibilidad del
documento a depositar está prácticamente vacío, y la versión buena es código
muerto en disco.**

Otros defectos:

| Ítem | Estado |
|---|---|
| README | el de raíz manda a `thesis/main.tex`, **no** al candidato `pre-thesis/main-v2.tex`, e instruye `pip install -r requirements-reproducible.txt`, **fichero que no existe** |
| README-v2 | **desfasado en 32 páginas**: dice 114 pp / cuerpo 81 / anexos 8 / Resultados 53,1 %. El PDF real es 146 / 69 / 49 / 42 %. Declara un incumplimiento («cuerpo 81 > 80») que ya no existe y calla los dos que sí |
| versiones pinadas | `pyproject.toml` y `requirements.txt` usan **rangos**; sólo `requirements.lock` pina, y el README no lo usa |
| resultados brutos | `results/megajuego/` (95 ficheros) y `results/pre_thesis/` (35) **sin seguimiento git y sin estar ignorados**. `results/megajuego/SUMMARY.json`, citado por `pre-thesis/README.md` como respaldo de las figuras del MegaJuego, **no existiría en un clon** |
| versión de CoppeliaSim | **no documentada en ninguna parte**; sólo el cliente `coppeliasim-zmqremoteapi-client>=2.0`, sin pinar. Tampoco el motor de física ni el `\Delta t` |
| checksum interno | un único fichero de *hashes* en el árbol vivo |
| regenerar vs reanalizar | **bien distinguido** — pero vive en el anexo huérfano |

---

# FASE 24 — CÓDIGO Y REPOSITORIO — **PARCIAL**

| Ítem | Estado |
|---|---|
| Estructura clara | sí, 23 directorios con función declarada |
| `.gitignore` | presente; **sin regla `.env*` en la raíz** — la protección del único fichero de entorno real depende de un `.gitignore` anidado |
| Sin secretos | **PASA** — 2 322 ficheros seguidos revisados; todos los aciertos de `api_key`/`token` son nombres de variable o vocabulario de dominio; 0 aciertos de `password`, `BEGIN PRIVATE KEY`, `AKIA`, `ghp_`; ningún `.pem`/`.key`/`id_rsa` seguido |
| README | sí (raíz + dos en `pre-thesis/`) |
| Licencia | MIT, «Copyright (c) 2026 Jorge Luis Mayorga Taborda» |
| **Commit final** | **NO** — HEAD `fc7a655c6`, rama `sp1-final-refactor`, **554 entradas sucias** (225 modificadas seguidas + 330 sin seguir) |
| **Tag/release final** | **NO** — los 4 tags son de trabajo intermedio de SP1 |
| Scripts ejecutables | sí; 8 de 10 muestreados anclan con `Path(__file__).resolve().parents[1]` |
| Paths relativos | **una excepción seguida**: `final-hardening/verify_audit_claims.py:21` incrusta `ROOT = r"C:\Users\walla\…"`. Fallará en cualquier otra máquina |
| Código que genera tablas/figuras identificado | **sí**, es el punto fuerte |

**Corrección de un dato obsoleto del repositorio:** `pre-thesis/` **sí está
seguido** —382 ficheros, 0 sin seguir— contra lo que afirman
`pre-thesis/README.md` («El árbol `pre-thesis/` sigue sin seguimiento Git») y
`BASELINE_REPORT.md`. Esa afirmación induce a error y conviene retirarla.

Lo que sí sigue fuera: **`paper/` con 30 `.tex`, 0 seguidos**, y **los dos PDF
entregables están ignorados** (`.gitignore:25` `*.pdf` y `.gitignore:15`
`build/`). `pre-thesis/.gitignore` reexpone `build/main.pdf` y
`monograph/build/monograph.pdf` pero **no** `build-v2/` ni
`supplementary/build/`.

---

# FASE 25 — COPPELIASIM — **PARCIAL**

El claim está **exactamente** donde la fase lo permite, y ni un milímetro más
allá. `coppelia-compact.tex:10-15`:

> «Un mundo pareado análogo al de E4, **no las 108 instancias que la tabla
> resume**, se reproduce en CoppeliaSim … cuatro robots, **una sola semilla
> (886001)**. La reproducción comprueba geometría y reejecución de la
> trayectoria comandada, **no física independiente ni hardware**: el error
> máximo de reejecución fue $6{,}89\times10^{-9}$ m.»

Y el cierre de RQ6: «**Reproducir un resultado geométrico no es revalidar el
certificado que lo respalda**». `CLAIM_LEDGER.csv` CL-24 lo registra como
`LIMITED`, `n=1`, «NO es física independiente».

`final-hardening/COPPELIA_PREFLIGHT_AUDIT.md` dictamina
**`COPPELIA_GATE_BLOCKED`** para la campaña confirmatoria de 16 celdas: dos de
nueve *gates* físicos (`force_transmission_gate_pass`, `wheel_twist_gate_pass`)
están `not_executed` con centinela `1.0` —medidas **ausentes**, no fallidas— y
`dt_sensitivity` = `fail`, autodescrito
`single_dt_repeat_only_not_a_sensitivity_study`. Su §4.1 ordena: «El nivel de
evidencia de CoppeliaSim **no sube** … La memoria debe seguir diciendo lo que ya
dice». **La memoria obedece.**

**Lo que falta es la procedencia técnica, y es casi toda:**

| Ítem | Estrecho E4 | AWS Industrial 2 |
|---|---|---|
| Procedencia de escena | declarada | declarada (AWS RoboMaker, MIT-0) |
| **Versión de CoppeliaSim** | **ausente** | **ausente** |
| **Motor de física** | **ausente** | **ausente** |
| **ZMQ remote API** | **ausente** | **ausente** |
| **`dt`** | **ausente** | **ausente** |
| **Modelo de robot de la escena** | **ausente** | Pioneer P3-DX (12) |
| Actuación de rueda / transmisión de fuerza / contacto / fricción | excluidas explícitamente | excluidas explícitamente |
| Lazo cerrado vs *replay* | **declarado: replay** | **declarado: cinemático** |
| Multi-`dt` | ausente | ausente |
| Semillas | 886001, $n=1$ | 2 por escenario |
| Manifiesto confirmatorio | 6 comprobaciones de admisión | ausente |

El claim es correcto; **la reproducibilidad del claim no lo es**. Sin versión de
simulador, motor ni `dt`, nadie puede repetir la corrida — y el propio
`04-methodology.tex:120` promete que «Toda simulación digital declara su paso
$\Delta t$».

Matiz de redacción: «La reproducción **confirma**, en un motor distinto, la misma
conclusión» es un verbo fuerte para $n=1$. «Es compatible con» sería exacto y no
cuesta nada.

---

# FASE 26 — ANEXOS — **FALLA**

| Requisito | Estado |
|---|---|
| ≤20 páginas | **FALLA — 49 pp** |
| Sólo material necesario | no |
| Pruebas esenciales | sí (Anexos B–E) |
| Reproducibilidad mínima | **no** — el anexo está prácticamente vacío (FASE 23) |
| **No revisión histórica extensa** | **FALLA** — Anexo F, 8 pp: protocolo comparado, auditoría adversarial, panorama industrial y normativo, discusión ampliada. Es exactamente lo que la fase prohíbe y lo que la guía §3 [STRAT] manda mover al suplemento |
| **No atlas interno** | PASA en la memoria — el atlas PASS/FAIL está en el suplemento |
| **No resultados candidatos** | **FALLA** — Anexo **J.5**, «Extensión no ensayada». El texto lo admite: «**No se implementó ni se evaluó** … de modo que **no sostiene ninguna afirmación activa**». Ocupa página de un presupuesto ya desbordado en 29 pp, y es además la subsección sin acentos de FASE 20 |
| No teoría abandonada | PASA |

Los anexos además **duplican nueve enunciados del cuerpo** con otra etiqueta
(FASE 8): presupuesto de anexo gastado dos veces.

**Plan de recorte que cierra la fase y ayuda al 50 %:** sacar F (8 pp) y J.5, y
comprimir H (16 pp) a las demostraciones que el cuerpo cita. Eso deja los anexos
cerca de 20 pp sin tocar una sola prueba esencial.

---

# FASE 27 — SUPPLEMENTARY — **PARCIAL**

113 pp, compila limpio (0 avisos, 72 claves citadas). Contiene lo que la fase
pide: pruebas extendidas, datos adicionales, campañas históricas (E0–E1, E8) y
el protocolo de la capa epistemológica delta.

**Lo que la fase manda eliminar del PDF público, y sigue dentro:**

| Prohibido | Presencia |
|---|---|
| *ledger* PASS/FAIL en crudo | **SÍ** — `formal-candidate-atlas.tex`, `longtable` de 166 filas «ID \| Tipo \| Veredicto \| Destino \| Título» con PASS/FAIL/LIMITED/DUPLICATE/CONJECTURE y destinos `monograph-candidate`/`archive-only`. Cabecera: «Generated by `build_formal_candidate_atlas.py`. Do not edit by hand» |
| *hashes* | **SÍ** — SHA-256 `b6416d52c9ce4cade…` impreso |
| `semantic-all.csv` | **SÍ**, citado por nombre |
| *workflow* del agente | **no** |
| candidatos no ejecutados | **SÍ**, pero correctamente marcados: «Es un **protocolo, no un informe de resultados**» |
| **30 páginas copiadas del main** | **SÍ** — ≈5 933 palabras (FASE 22) |

El suplemento se defiende con una salvaguarda correcta («Su presencia en este
documento no eleva automáticamente el nivel de evidencia»), pero el *ledger*
crudo, los *hashes*, el CSV nombrado y la duplicación son cuatro de los seis
ítems de la lista de supresión.

---

# FASE 28 — AUDITORÍA VISUAL — **PARCIAL**

Extraído con PyMuPDF: mediana 2 077 caracteres/página. **0 páginas bajo 100
caracteres**, 2 bajo 200, 7 bajo 900.

## Páginas escasas y huérfanas

| Página | car. | Contenido | Veredicto |
|---|---:|---|---|
| **p.75** | **152** | `thesis/resources/MROB_MegaGame_E2E_bundle/.` | **La peor página del documento.** Una línea huérfana que es **una ruta de repositorio desnuda**, cerrando la sección del MegaJuego. Toca FASE 21 y FASE 28 a la vez |
| **p.4** | 159 | `formation, potential games, cooperative transport` | **La lista de palabras clave del Abstract cae sola a su página.** La frase empieza al pie de la p.3. FASE 28 lo prohíbe por nombre: «keywords no saltan a página vacía» |
| **p.86** | 228 | «…lo que basta para exigir una cota continua, no muestreada, antes de cualquier prueba con hardware.» | huérfano de dos líneas cerrando sección |
| **p.63** | 462 | `Tabla 11` + 3 filas + «Elaboración propia.» | **página de flotante aislado** — una tabla sola en una página |

**No hay páginas de sólo encabezado ni pies de figura separados** más allá de
la p.63.

## Las 8 invasiones de margen — qué hay en cada una

Requerido: izq/der 3,0 cm, sup/inf 2,5 cm.

| Página | Invasión (cm) | Contenido | Diagnóstico |
|---|---|---|---|
| **p.19** | sup **2,12** | `Figura 1`, escenario de almacén, 120 trazos | TikZ a ancho completo desborda por **arriba** |
| **p.44** | izq **2,26**, der **2,26** | `Figura 5`, dos paneles de revisión, 125 trazos, 1 044 car. bajo 7 pt | **el peor**: 0,74 cm dentro de cada margen lateral |
| **p.55** | der **2,87** | `Figuras 13–16` en una sola página, 108 trazos | cuatro flotantes apiñados |
| **p.64** | der **2,86** | §6.3 + `Figura 20` + Ec. (14) | figura de composición ancha |
| **p.73** | der **2,89** | prosa sobre el solver, «brecha 10⁻¹¹»; sólo 3 trazos | **no es una figura**: un `\texttt{}` o matemática inquebrable empuja al margen |
| **p.106** | izq **2,89**, der **2,89** | `Tablas 26 y 27`, 419 car. bajo 7 pt | **dos tablas con `\resizebox`** |
| **p.109** | izq **2,88**, der **2,88** | `Tabla 28` (antecedentes) + `Figura 8` | misma patología |
| **p.126** | inf **2,38** | «Juego de reparación», $\mathrm{NE}(G_6)=\{x:D_6(x)=0,\dots\}$ | desbordamiento **inferior** desde un bloque de demostración |

**Patrón:** 5 de 8 son las figuras y tablas portadas de la revisión —las mismas
que cargan el tipo de 4–5 pt de FASE 17—; 2 son prosa con material inquebrable;
1 es la figura protegida de la introducción.

## El resto

TOC compacto, abstract de una página, nomenclatura compacta: correctos. **Cero
encabezados consecutivos.** Ritmo visual denso: 69 flotantes para 69 páginas de
cuerpo, y 15 de ellos ni siquiera se citan.

---

# FASE 29 — BIBLIOGRAFÍA FINAL — **PARCIAL**

**El gate $C=R$ pasa numéricamente:**

| | |
|---|---:|
| Claves citadas (C) | **101** (`main-v2.blg`: «Found 101 citekeys») |
| Referencias impresas (R) | **101** (`main-v2.bbl`) |
| Citas sin entrada | **0** |
| Duplicados por título normalizado | **0** |
| Colisiones de clave entre los dos `.bib` | **0** |
| `main-v2.blg` | sin WARN ni ERROR |
| `build-v2/main-v2.log` | **0 apariciones de «Warning»**, 146 pp |

Contadores restantes:

| Exigencia | Estado |
|---|---|
| 0 DOI rotos | **PASA** para `references.bib` (116/116 contra Crossref, 112 HTTP 200, 2026-09-08). **NO VERIFICADO** para `references-v2.bib` |
| 0 metadata incorrecta | **FALLA** — 2 iniciales de autor erróneas, 1 título truncado, 5 `@article` incompletos, 1 norma mal descrita |
| 0 `et al.` indebidos | **FALLA** — 3 impresos |
| 0 duplicados | PASA |
| 0 preprints obsoletos | **FALLA** — 2 |
| 0 páginas corporativas como evidencia científica | PASA |
| ISO actualizado | **FALLA** — 1 norma con título, URL y estado equivocados |

**Y un incumplimiento estricto de $C=R$ que biber no ve:** 6 claves llegan a la
bibliografía sólo por `\nocite` (`05-theoretical-framework.tex:254` y `:364`):
`huang2022mlLns`, `paul2023collective`, `tang2025railgun`,
`yu2023graphTransformer`, `zhang2024coalition`, `zhou2026cttapf`. **Se imprimen
en la lista de referencias y no se citan en ninguna frase.** Bajo lectura APA,
seis referencias huérfanas impresas.

Densidad de cita: 105 instancias en 146 páginas ≈ 0,7 por página, frente a las
243 que contaba la v1. La compactación del capítulo 6 se llevó por delante buena
parte del aparato de cita.

---

# FASE 30 — CONCLUSIONES — **PASA**

Es uno de los capítulos más sólidos del documento.

| Requisito | Dónde |
|---|---|
| Respuesta a la pregunta central | §7 apertura: «La pregunta principal admite una respuesta **condicionada**» |
| RQ1–RQ6 | §7.3 + §7.7, las seis literalmente |
| OE1–OE6 | §7.2 + §7.7, con grado declarado |
| H1–H6 | `tab:conclusion-hypotheses` (9 filas) + `tab:conclusion-hypothesis-h6` |
| Contribución / resultado positivo | §7.1 |
| Resultado negativo principal | H3 «No sustentada»; §7.1 sobre Industrial 2 |
| Limitaciones | §7.5 |
| **Condiciones donde NO usar** | **§7.9 entera** — congestión alta, cargas no planares, contactos móviles, más de una carga, fuera del modelo Bernoulli, y «ningún resultado de esta memoria sostiene despliegue físico» |
| Trabajo futuro desde gaps reales | §7.6 y §7.8 |
| Ninguna teoría nueva, ningún claim nuevo | cumplido |

Además satisface el requisito VIU de **recomendaciones multidimensionales** que
casi todas las memorias incumplen: §7.8 desarrolla la teórica (Lyapunov común o
tiempo de permanencia), la económica (coste de cómputo por misión frente al
presupuesto de ejecución del `thm:megajuego-execution-budget`) y la social (la
abstención como propiedad con consecuencia sobre el operario).

Defecto de forma, no de fondo: §7.5 Limitaciones es **un solo párrafo de nueve
frases**. Su contenido es excelente; su presentación entierra ocho limitaciones
distintas en un bloque continuo, justo donde el tribunal más va a mirar.

---

# FASE 31 — «REVIEWER 1» — **PARCIAL**

| Pregunta | ¿Responde? |
|---|---|
| ¿Qué teorema es nuevo vs estándar? | **PARCIAL — el flanco.** Contestado para dos resultados y para la arquitectura entera («No se reclama originalidad de esos bloques»); **no contestado** para los cuatro teoremas de potencial exacto (E1, E6, E7, megajuego), que son aplicaciones de Monderer–Shapley y sólo el de E7 lo cita |
| ¿Dónde están los supuestos? | **sí**, en 18 de 20 enunciados más los `\estadoaporte`. Ausentes del enunciado (presentes en el anexo): `thm:sp2-compact-e6-exact-potential` y `thm:sp3-compact-e7-potential` |
| ¿Definición formal del juego? | **no**, 4 de 12 elementos (FASE 9). El documento no pretende lo contrario |
| ¿Nash implica optimalidad? | **contestado: no, con demostración.** `PoA`$_6=+\infty$. **Abierto para E1, E7 y el megajuego**, donde no hay PoA |
| ¿Converge el algoritmo implementado? | **contestado**: sólo terminación de camino de mejora finito, nunca convergencia de EDO |
| ¿Qué ocurre al discretizar? | **contestado, repetidamente**: «Una proyección o un redondeo **puede cambiar el potencial** de la relajación y **crear déficit**» |
| ¿La localidad es real? | **contestado: sólo E6 y E7** — pero el texto lo contradice en seis sitios (FASE 11) |
| ¿Qué prueba la factorización? | **contestado — sólo en el anexo**: «La factorización antes de eliminar estados no prueba localidad de la sensibilidad reducida». Ausente del cuerpo |
| ¿Cuál es el contraejemplo? | **cinco**: insuficiencia de la capacidad escalar; recíproco del *wrench* falso ($G=Q_W=W=1$, $\varepsilon=100$ → residual $100/101$); `PoA`$_6=M/2\to\infty$; umbral de servicio cumplido sin balance de torque; degeneración GNE con $z_1+z_2=1$ |

Nueve de diez contestables desde el documento. El flanco es el primero, y se
cierra con dos frases de atribución.

---

# FASE 32 — «REVIEWER 2» — **PARCIAL**

| Pregunta | ¿Responde? |
|---|---|
| ¿El modelo representa un AMR? | **PARCIAL** — uniciclo con no-holonomía, radio de rueda, vía, mapa twist→ruedas, par y constantes de motor sí. **Masa del robot, inercia y límites numéricos de actuación, no.** El P3-DX se nombra dos veces y **ningún resultado se deriva de sus parámetros** |
| ¿Cómo se transmite fuerza? | **contestado** en el modelo: $W_C=G_C(q)\boldsymbol\lambda_C$; **no medida**: `force_transmission_gate_pass` = `not_executed` |
| ¿Dónde está la fricción? | una instancia numérica ($|t_i|\le0{,}4 n_i$, Coulomb tangencial); **nunca nombrada $\mu$**; fuera de alcance en el resto |
| ¿Qué pasa con el *slip*? | **ABIERTO.** Dos menciones, ambas exclusiones. `results-interface.tex:86` define el éxito físico como incluir chequeo de deslizamiento, y **ninguna campaña lo mide** |
| ¿Qué es simulado / impuesto / medido? | **contestado con tabla dedicada.** Impuesto/exacto: pose de carga, atributos, déficit, líder. Estimado: agregado por consenso en anillo. Fuera: percepción real, contacto 3D, hardware |
| ¿Qué validó Coppelia? | **contestado y bien acotado**: geometría y *replay*, $n=1$. Motor, `dt` y modelo de robot **no declarados** |
| ¿Qué falta para hardware? | **contestado, con condición de parada**: «ningún resultado de esta memoria sostiene despliegue físico: el verificador registró dos violaciones de barrera …, lo que basta para exigir una **cota continua, no muestreada**» |
| ¿Los baselines son reales? | **contestado: no, y se declara como limitación**: «adaptaciones piloto, no implementaciones completas de CBBA, ORCA o DMPC» |

Los dos flancos serios: los parámetros mecánicos del vehículo y el
deslizamiento, que entra en la definición de éxito y no se mide.

---

# FASE 33 — JURADO VIU — **NO EVALUABLE DESDE LOS ARTEFACTOS**

La fase evalúa si **el autor** puede responder doce preguntas sin buscar. Eso no
se audita en un PDF.

Lo que sí puede afirmarse: **diez de las doce tienen respuesta escrita y
localizable**. **Dos son las débiles:**

- **«¿Por qué juegos?»** — §5.2 compara las cinco dinámicas y **no justifica la
  elección de Smith**.
- **«¿Qué pasa a 64 coaliciones?»** — la respuesta existe («tasa cero en
  $A=64$») pero **no está en el documento depositado**.

Ambas son preguntas que un tribunal hace, y ambas son baratas de cerrar.

---

# FASE 34 — DEFENSA — **FALLA**

**No existe ningún material de defensa en el repositorio.** Lo único presente es
la plantilla institucional en blanco, `resources/P11_06_F12 Plantilla PPT
Defensa_v01.pptx`.

| Requisito | Estado |
|---|---|
| versión 30 s / 2 min | no existen |
| presentación completa | **no existe** |
| backup PDF | no existe |
| vídeo | hay material fuente (el Anexo H.4 menciona vídeo y CSV de poses), sin montar |
| backup local / demo sin internet | n/a |
| 20–30 preguntas adversariales | **no existe** ningún documento de preparación |
| slides de backup | no existen |

Esto pesa más que cualquier otra fase de esta lista: **la defensa es el 70 % de
la nota** (guía §1, `viu-compliance` §1). Sobre la duración, la fase dice «no
imponer 10–15 min hasta verificar la convocatoria real»; `viu-compliance` §8
fija **15 minutos y 15–20 diapositivas**, con 6 de esos minutos para resultados y
validación. Ese dato procede de la tutoría colectiva final, cuyo PDF es de imagen
y no permite extracción de texto, así que **no pude confirmarlo
independientemente** — queda como [VERIFICAR].

---

# FASE 35 — CONGELACIÓN FINAL — **FALLA**

| Requisito | Estado |
|---|---|
| Commit final identificado | **NO** — 554 entradas sucias; HEAD es un commit de trabajo en `sp1-final-refactor` |
| Datos congelados | **NO** — `results/megajuego/` (95) y `results/pre_thesis/` (35) sin seguir ni ignorar |
| Figuras congeladas | parcial |
| Bibliografía congelada | **NO** — `references-v2.bib` es posterior al sello |
| PDF final desde fuente limpia | el PDF **es fresco** (ningún `.tex`/`.bib`/`.sty` bajo `pre-thesis/` es posterior a `main-v2.pdf`), pero la fuente no está limpia |
| Supplementary final | **NO** — `supplementary.pdf` es **anterior** a `references-v2.bib`, que `supplementary/main.tex:29` carga. Su bibliografía está obsoleta |
| Versión archivada / SHA interno | **NO para la v2** |
| README final | **NO** — README-v2 desfasado en 32 páginas |

**El sello está roto de tres maneras.** `pre-thesis/config/release-manifest.json`
(291 ficheros, `base_commit e2e67abe…`, **29 commits por detrás de HEAD**):

```
$ python scripts/verify_release_manifest.py --check
release manifest: FAIL: Release file set changed: missing=[],
  extra=['GUIDELINES.md','README-v2.md','bibliography/references-v2.bib',
         'build-supplementary.ps1','build-v2.ps1']
exit 1
```

Y al comparar los 291 *hashes*: **289 coinciden, 2 han cambiado** —
`sections/sp1-wrench-condensed.tex` (**está en el cierre activo**) y
`shared/generated-macros/sp7_numbers.tex` (una de las 15 familias trazables).

Peor: `build-v2.ps1` **salta deliberadamente la comprobación del manifiesto**,
con la justificación de que el sello describe la v1. La consecuencia es que **el
candidato a depósito no tiene mecanismo de congelación alguno**.

`pre-thesis/evidence/build-reproducibility.md` documenta compilaciones
byte-idénticas con SHA-256 — pero de la **memoria v1 de 97 pp** y de la
monografía de 110 pp. **No hay evidencia de reproducibilidad binaria del PDF que
se pretende depositar.**

El propio Anexo A huérfano lo dice: «La versión de depósito **deberá crear una
etiqueta inmutable y registrar su SHA** después de incorporar las correcciones
finales. Hasta entonces, la URL pública no equivale a un archivo permanente».
Sigue sin hacerse.

---

# FASE 36 — GATES AUTOMÁTICOS — **FALLA**

Ejecutados el 2026-09-19 (`mecanica/01-gates.md`, más mediciones propias):

```
LaTeX errors ............... 0      OK
Undefined references ....... 0      OK
Duplicate labels ........... 0      OK
Critical bib warnings ...... 0      OK
Broken DOI ................. 0      OK  (references.bib; v2 SIN VERIFICAR)
Citation without ref ....... 0      OK
Ref without citation ....... 54     FALLA  (+6 sólo-\nocite impresas)
Figure clipping ............ 0      OK  (8 overfull, máx 4,80 pt, ninguno en gráfico)
Known stale macros ......... 0      OK
P0 claims .................. 10     FALLA

Body pages ................. 69     OK   (50-80)
Annex pages ................ 49     FALLA (<=20)
Results fraction ........... 42,0 % FALLA (>=50 %)
Spanish abstract ........... 280    OK
English abstract ........... ~275   OK
Keywords ................... 5      OK
APA 7 ...................... FALLA  (gate DZ, 4/10 contadores)
```

**7 de 17 contadores fuera.** Cuatro bloquean: anexos, fracción de Resultados,
referencias huérfanas y APA 7.

---

# FASE 37 — GATES HUMANOS — **PARCIAL**

| Criterio | Valoración |
|---|---|
| Calidad matemática | **alta**. Las nueve confusiones no sólo se evitan: varias son resultados. El límite informacional, la `PoA` no acotada y el pasaje no-Zeno/*dwell time* son matemática seria |
| Novedad | **bien construida y bien acotada**. El claim es de composición, no de componente, y se dice así |
| Claridad | **media-baja**. La lastran los códigos E0–E8 y el tipo de 4–5 pt |
| Coherencia narrativa | **alta** en el eje contrato→certificado→ejecución; **rota** por §6.1 (bibliometría dentro de Resultados) y por las adendas OE6/H6/RQ6 |
| Calidad visual | **media**. Vectorial mayoritario, fuentes atribuidas al 100 %, glifos de forma en la matriz de capacidades; pero la paleta de series no sobrevive al gris y 15 flotantes no se citan |
| Plausibilidad física | **alta en contacto**, **débil en vehículo** (sin masa ni inercia) y **nula en deslizamiento**, que entra en la definición de éxito sin medirse |
| *AI-writing feel* | **bajo por léxico** (`lmscan` 1,8 %), **medio-alto por ritmo y plantilla**: sd bajo el umbral en 13 ficheros, 174 párrafos marcados, y 15 run-in idénticos «Resultado y alcance:» |
| Sobreclaims | **muy pocos**. Los que quedan: «confirma» para $n=1$; «Confirma pertinencia industrial» sobre patentes; dos resultados de libro de texto en caja de contribución; y seis «distribuido» sin matizar |

---

# FASE 38 — TEST DE LECTURA FINAL — **PARCIAL**

| Test | Resultado |
|---|---|
| **Heading-only** | **falla parcialmente.** Capítulos 1–5 y 7 se leen solos. El 6 exige el diccionario E0–E8 |
| **Figure-only** | **falla.** 8 figuras y 7 tablas no se citan, así que el hilo figura→argumento se rompe 15 veces. Los pies sí son autosuficientes y todos llevan fuente |
| **First-sentence** | **pasa.** Las frases temáticas van al principio y la cadena reconstruye el argumento |
| **Cold chapter** | **pasa.** Cada capítulo abre con párrafo introductorio y cierra con síntesis |
| **5-second figure** | mixto. Las figuras de arquitectura comunican de inmediato; las bibliométricas exigen leer el pie a 4–5 pt |
| **Read-aloud** | **falla en dos sitios**: los cinco párrafos de una frase de `results-review.tex` suenan a lista, y el párrafo único de Limitaciones (nueve frases) no se puede leer en voz alta sin perderse |
| **Tribunal («¿y por qué?» ×5)** | **pasa cuatro veces, falla la quinta en §5.2**: ¿por qué juegos? → porque la decisión es distribuida. ¿Por qué poblacionales? → porque hay muchos agentes intercambiables. ¿Por qué Smith? → **sin respuesta escrita** |

---

# FASE 39 — CHECKLIST DE ENTREGA — **PARCIAL**

| Ítem | Estado |
|---|---|
| PDF correcto | sí, abre, 146 pp, 2 903 786 bytes |
| **No draft** | **PASA, verificado** — 0 apariciones reales de `TODO`, `FIXME`, `XXX`, `TBD`, `borrador`, `draft`, `placeholder`, `por completar` en los 89 ficheros activos. Los 183 aciertos en bruto son falsos positivos del español (`todo`, `me**todo**logía`, `in**dependiente de**l`) |
| **Nombre correcto** | **NO** — `main-v2.pdf` y `supplementary.pdf` son nombres de artefacto de compilación |
| Suplemento correcto | **NO** — mismo `/Title` que la memoria; los dos entregables son indistinguibles por metadatos |
| Archivos abren | sí |
| Links | `hyperref` activo; no verifiqué resolución de URL externas |
| Página inicial correcta | sí: portada sin numerar con título, autor, tutor, fecha «Septiembre de 2026», máster y logo |
| **Director correcto** | sí — `config/metadata.tex:4`, «José Ignacio Iñíguez Amigot» |
| Fecha correcta | formato mes y año, como exige la norma |
| **Anexo III / Anexo IV** | **plantillas en blanco** en `resources/`, ninguna cumplimentada ni firmada |
| Expediente académico | **ausente** |
| Confirmar recepción | pendiente |

Metadatos por lo demás de calidad de depósito: `/Author`, `/Subject` y
`/Keywords` correctos y coincidentes con el Resumen, fecha de creación
determinista desde `config/build-epoch.txt`, sin `draft`.

**Y el dato de calendario que condiciona todo lo anterior.** `viu-compliance` §2
fija para la **1.ª convocatoria: depósito 08/09/2026**. Hoy es **19/09/2026**:
esa ventana **ya está cerrada**. Las siguientes son **2.ª — depósito 13/10/2026,
defensa 26–30/10** y **3.ª — depósito 10/11/2026, defensa 23–27/11**.
`pre-thesis/evidence/administrative-gates.md` ya trabaja contra la tercera, con
las fechas verificadas en la guía docente (SHA-256 `09b62592…`). **La
disponibilidad efectiva de la convocatoria para el expediente sigue
`PENDIENTE_AULA`.**

---

# FASE 40 — CRITERIO «10/10» — **NO ALCANZADO**

$$\text{10/10}=\text{pregunta clara}+\text{teoría correcta}+\text{evidencia sólida}+\text{claims exactos}+\text{narrativa excelente}+\text{presentación impecable}$$

| Término | Estado |
|---|---|
| Pregunta clara | **sí** |
| Teoría correcta | **sí** — con dos atribuciones que añadir y una contradicción de marcador que borrar |
| Evidencia sólida | **sí, dentro de su dominio**, y el dominio se declara en todas partes |
| Claims exactos | **sí en el cuerpo, no en el título** |
| Narrativa excelente | **no todavía** — códigos E0–E8, §6.1 fuera de sitio, ritmo plano, plantilla visible |
| Presentación impecable | **no** — dos fallos duros de extensión, márgenes, tipo de 2,6 pt, acentos, 15 flotantes sin citar, APA |

**Gate final absoluto** («para cada término del título … poder señalar qué
evidencia lo sostiene y en qué dominio es verdadero»): **falla en dos términos
del título** —«distribuida» y «en entornos industriales»— y en un tercero con
matiz, «cargas heterogéneas». Para todo lo demás —cada objetivo, cada hipótesis,
cada teorema, cada tabla, cada figura— el documento **sí** puede señalarlo, y esa
es una afirmación fuerte que pocos TFM soportan.

---
---

# Parte II — Guía estratégica VIU (`06-guia-estrategica-viu.md`)

## A. Ítems [P0] NO satisfechos

Ordenados por coste de cierre, de menor a mayor.

| # | [P0] | Sección | Estado | Cierre |
|---|---|---|---|---|
| **P0-1** | **Anexos ≤ 20 páginas** | §3 | **49 pp** | Sacar Anexo F (8 pp) y J.5 al suplemento; comprimir H (16 pp) |
| **P0-2** | **Resultados ≥ 50 % del cuerpo** | §3 | **42,0 %** | Recortar 11 pp de Marco teórico y Metodología → cuerpo 58 pp, 50,0 %. **No** por relleno: §3 lo prohíbe expresamente |
| **P0-3** | **Márgenes oficiales** | §2 | 8 páginas invaden | Reducir seis flotantes anchos y dos bloques de prosa inquebrable |
| **P0-4** | **Fonts legibles / cero texto microscópico** | §16 | **9 222 caracteres bajo 7 pt, hasta 2,6 pt**; 12 tablas con `\resizebox`; 181 llamadas `\fontsize{<8}` | Es el defecto más visible del documento. Requiere partir o girar las tablas portadas de la revisión, no encogerlas más |
| **P0-5** | **0 referencias huérfanas / APA 7 PASS** | §9, §24 | 54 huérfanas + 6 sólo-`\nocite`; 34 títulos en Title Case; 2 iniciales erróneas; 5 `@article` incompletos | Lista accionable línea a línea en `lectura/06-bibliografia.md` §9 |
| **P0-6** | **Bibliografía metodológica presente** | §9 | las 6 entradas metodológicas están huérfanas | Citar a Holm donde se aplica Holm. Media hora |
| **P0-7** | **0 figuras adaptadas sin fuente** | §10 | 7 puntos de `fig:lit-methodological-map` sin `\cite`; 1 tabla sin `\caption` ni fuente | Añadir citas y pie |
| **P0-8** | **Prueba antiplagio ejecutada** | §18 | **no existe informe Turnitin**; el cribado interno cubre la v1 de 97 pp, no la v2 de 146 ni el suplemento | Ejecutar el control institucional. Bloqueante formal |
| **P0-9** | **Main y suplemento deduplicados** | §17/§10 | ≈5 933 palabras idénticas, incluido el capítulo entero de Marco teórico | Decidir cuál lo imprime y que el otro lo referencie. Condiciona a P0-8 |
| **P0-10** | **Commit/hash interno congelado** | §18 | 554 entradas sucias, sin tag de depósito, manifiesto roto de tres maneras, `paper/` sin seguir, ambos PDF ignorados por git | Tag + SHA. Lo exige el propio Anexo A del TFM |

**Adicionales, fuera de la lista literal de [P0] pero igual de bloqueantes para
una versión final:**

- **Anexo de reproducibilidad vacío** — la versión buena
  (`01-reproducibility.tex`) sólo la compila `thesis/main.tex`. Añadirla a
  `thesis-appendices-v2.tex` cuesta **una línea** y cierra §24
  «Reproducibilidad».
- **Lenguaje de taller impreso** — 19 ocurrencias de `claim`/`gate`/`claim-ID`
  concentradas en 2 ficheros, «formulación previa» en el cuerpo, y **p.75, una
  página entera cuyo único contenido es una ruta de repositorio**.
- **Palabras clave del Abstract huérfanas en su propia página** (p.4), que FASE 28
  prohíbe por nombre.
- **Doce palabras sin acento** en el Anexo J.5, una en un encabezado del índice.
- **`tab:results-compliance` describe mal la corrección de Holm** y contradice a
  `tab:conclusion-hypotheses` del mismo documento.
- **`\estadoaporte` del presupuesto de ejecución contradice a su propio teorema**
  sobre la hipótesis no-Zeno.
- **Una demostración sin enunciado** en `appendix-megajuego-detail.tex:102`.
- **`supplementary.pdf` obsoleto** frente a `references-v2.bib`. Recompilar.
- **`final-hardening/census.json` desactualizado**, lo que hace que las
  herramientas escaneen el fichero de conclusiones antiguo.

## B. Ítems [VERIFICAR] — el estudiante debe comprobarlo en el Aula o con el tutor

| # | Qué verificar | Por qué no se resuelve desde el repositorio | Dónde |
|---|---|---|---|
| **V-1** | **¿Existe formulario de «Declaración de uso de IA generativa» en el Aula MROB 2025–26?** | Busqué en `resources/Instrucciones_TFM_MU Robotica F.pdf` y en la guía docente: **no lo mencionan**, y no hay plantilla en `resources/`. La guía §11 advierte de no asumir que el formulario de otro máster sea el de MROB | Aula, anuncios, tutoría final o el tutor |
| **V-2** | **Duración exacta de la exposición** | `viu-compliance` §8 afirma **15 min / 15–20 diapositivas**, procedente de la tutoría colectiva final; ese PDF es **de imagen** y no permite extracción de texto, así que no pude confirmarlo | Tutoría Final Colectiva, «Indicaciones Defensa TFM» |
| **V-3** | **Duración del turno de preguntas** | no documentada en ningún material del repositorio | ídem |
| **V-4** | **Plazo para enviar las diapositivas** | no documentado | ídem |
| **V-5** | **¿Está la convocatoria habilitada para este expediente?** | `administrative-gates.md` la marca `PENDIENTE_AULA` y registra que el 2026-09-09 no había sesión autenticada. **La 1.ª convocatoria (depósito 08/09/2026) ya venció**; hay que confirmar si se opta a la 2.ª (13/10) o a la 3.ª (10/11) | Tareas «Evidencia 5» y «Evidencia 6» del Aula |
| **V-6** | **¿Se acepta administrativamente una memoria generada en LaTeX?** | Las Instrucciones exigen la plantilla oficial y prohíben modificar sus estilos, pero **no prescriben la herramienta**. La conformidad técnica está demostrada; la aceptación administrativa no se infiere del silencio de la norma | Mensaje escrito del director o de soporte académico |
| **V-7** | **¿Autoriza el tutor el cambio de título?** | El Anexo I presentado fija el título actual. Cambiar la portada sin registro puede generar discrepancia entre expediente y memoria | Tutor |
| **V-8** | **¿Están `paper/` y `work/` inéditos?** | El informe de originalidad condiciona su PASS a esto; encontró 1 coincidencia exacta y 1 alta de `work/` hacia la monografía | Confirmación escrita, al expediente |
| **V-9** | **¿Es el TFG Uniandes 2014 antecedente conceptual citable?** | Decisión de criterio, no de dato | Tutor |
| **V-10** | **Comparación DOCX/PDF en el mismo equipo** | `viu-compliance` §6 y §11.7 lo dejan como **el único paso manual pendiente**: la automatización de Word no responde y no hay LibreOffice | Manual, una vez |
| **V-11** | **Anexo III firmado por el director; Anexo IV firmado; expediente académico** | Sólo existen las plantillas en blanco; el Anexo III lo emite el director | Depósito |

## C. Preparación para la defensa — secciones 19 a 24

### §19 Narrativa de defensa — **NO PREPARADA**

Los diez elementos de la *narrative checklist* —problema, brecha, objetivos,
arquitectura, método, resultados principales, resultado negativo, limitaciones,
conclusión, aporte— **existen todos en el documento y están bien escritos**. Lo
que no existe es la narrativa: **no hay presentación, ni guion de 30 s, ni de
2 min, ni PDF de respaldo**. Sólo la plantilla institucional vacía.

Es la brecha más cara del proyecto en relación coste/beneficio: la defensa pesa
el **70 %**, y hoy hay 0 % de ella hecho frente a un documento que está al 85 %.

### §20 Resiliencia técnica — **NO PREPARADA**

Ethernet, Wi-Fi de respaldo, *hotspot*, cargador, cámara y micrófono quedan fuera
del repositorio. Lo que sí es auditable y falta: **slides locales, backup PDF,
vídeo fuera de PowerPoint, demo pregrabada, copia en nube, copia USB** — ninguno
existe. Hay material fuente para el vídeo (el Anexo H.4 conserva vídeo y CSV de
poses), sin montar.

### §21 Dominio del contenido — **PARCIAL, con dos huecos conocidos**

De las doce cosas que hay que poder explicar sin notas, **diez tienen respuesta
escrita y localizable**. Las dos débiles:

- **«Por qué usaste juegos»** → el escalón que falta es **por qué Smith**. §5.2
  compara cinco dinámicas y no elige.
- **«Qué pasa a escala»** → la respuesta existe (tasa cero en $A=64$) pero vive
  en el suplemento; en el cuerpo H5b figura como «no adjudicada».

Tres están notablemente bien servidas: «qué validó Coppelia», «qué significa
distribuido» y «qué falta para hardware» tienen respuesta literal, acotada y
defendible. La tercera incluye una condición de parada explícita, que es
exactamente el tipo de respuesta que un tribunal técnico premia.

### §22 Preguntas de tribunal — **PARCIAL**

De las quince preguntas que la guía lista, **doce tienen respuesta directa**:

| Pregunta | Respuesta disponible |
|---|---|
| ¿Contribución central? | §7.1 y Resumen |
| ¿Qué tiene de nuevo? | claim de cuatro cláusulas, `review-compact.tex:31` |
| ¿Por qué teoría de juegos? | **parcial** — falta el porqué de Smith |
| ¿Qué es realmente distribuido? | `tab:results-model-map`: sólo E6 y E7 |
| ¿Diferencia con un centralizador? | los oráculos se presentan como techo, no como par |
| ¿Qué ocurre con $N$ grande? | **débil** — el dato está fuera del cuerpo |
| ¿Por qué falló H3? | IC incluye cero, $p_{\mathrm{Holm}}=0{,}068$ |
| ¿Qué demuestra H5b? | «no adjudicada» — hay que defender la decisión de alcance |
| ¿Por qué capacidad no implica *wrench*? | $\boldsymbol W_k^{\mathrm{req}}\in\mathcal W_{C_k}$ y la insuficiencia escalar, con contraejemplo |
| ¿Dónde está la fricción? | $|t_i|\le0{,}4 n_i$; fuera del alcance confirmatorio en el resto |
| ¿Qué validó Coppelia? | geometría y *replay*, $n=1$ |
| ¿Por qué no hardware? | §7.9 y las dos violaciones de barrera |
| ¿Qué teorema es realmente suyo? | **el flanco** — cuatro teoremas de potencial exacto sin atribuir a Monderer–Shapley, y dos resultados estándar en caja de contribución |
| ¿Cuál es el paper más parecido? | Shibata et al. 2023; en industria, Beacon Dual-AMR 2026 |
| ¿Dónde no usaría este método? | **§7.9 entera** — la mejor respuesta del documento |

**Tres flancos** («por qué Smith», «qué pasa a 64», «qué teorema es suyo»), los
tres cerrables con menos de una página de texto cada uno.

### §23 Matrícula de Honor — **CANDIDATURA VIABLE, NO ARMADA**

| Requisito | Estado |
|---|---|
| Contribución identificable en 30–60 s | **sí** en el papel; **no ensayada** |
| Al menos un resultado memorable | **sí** — «capacidad agregada no implica *wrench* realizable», con proposición de insuficiencia escalar, contraejemplo y medida de falsos positivos. Citable en una frase |
| Profundidad teórica | **sí** — límite informacional por indistinguibilidad, `PoA` no acotada, y la distinción no-Zeno / *dwell time* con contraejemplo $t_{k+1}-t_k=1/k$ |
| Validación experimental suficiente | **parcial** — sólida en E2/E3/E6/E7/Cargo; $n=1$ en Coppelia y en el e2e del juego; **sin IC en las tablas** |
| **Resultados negativos tratados científicamente** | **sí, y es el mayor activo del trabajo.** Ocho de nueve conservados y promovidos a fronteras del mecanismo |
| Literatura adversarial | **sí** — la auditoría cambió el claim: «el reemplazo durante el transporte ya existe» |
| Reproducibilidad | **parcial** — maquinaria excelente, anexo huérfano, sin tag |
| Figuras profesionales | **parcial** — fuente al 100 % y glifos de forma bien resueltos, pero paleta de series no separable en gris |
| **Documento sin errores visibles** | **NO** — anexos, %Resultados, márgenes, tipo de 2,6 pt, acentos, 15 flotantes sin citar |
| Defensa técnicamente sólida | **no preparada** |
| Responder preguntas difíciles | tres flancos abiertos |
| Claridad sobre límites | **sí, sobresaliente** |
| Distinción trabajo propio / literatura | **sí**, salvo los cuatro potenciales exactos y las dos cajas con resultados estándar |

**La pregunta de control** —«¿qué podría escribir el tribunal en un informe
motivado?»— sí tiene respuesta concreta:

> *Separa, con un predicado verificable y medido, la cobertura nominal de
> capacidad de la factibilidad mecánica de una coalición de transporte; demuestra
> que el peor equilibrio de su juego de reparación no admite cota uniforme;
> distingue con contraejemplo la ausencia de Zeno de un tiempo de permanencia
> positivo; y declara con precisión inusual el dominio de cada garantía,
> conservando los resultados negativos —incluida una hipótesis propia refutada—
> como fronteras del mecanismo.*

Eso es un informe motivado real. **Lo que hoy impide proponerlo son los errores
visibles del documento y la ausencia de defensa**, no la ciencia.

Nota reglamentaria: MH exige ≥9 y existe el límite del 5 % de matriculados, salvo
excepción para grupos de menos de 20. La decisión es de la Comisión de TFT, no
del tribunal.

### §24 Readiness final — marcador

```
VIU format ................ PARCIAL  (márgenes en 8 páginas; tipo hasta 2,6 pt)
Body pages 50-80 .......... PASS     (69)
Annexes <=20 .............. FAIL     (49)
Results >=50% ............. FAIL     (42,0 %)
Abstract 200-300 .......... PASS     (280)
Keywords 3-5 .............. PASS     (5)
APA 7 ..................... FAIL     (gate DZ, 4/10 contadores)

Scientific P0 ............. 1   (claim-source audit no cubre la v2)
Editorial P0 .............. 3   (anexos, %Resultados, lenguaje de taller)
Math P0 ................... 0   (2 atribuciones + 1 marcador contradictorio: P1)
Bibliographic P0 .......... 3   (huérfanas, metodológica ausente, APA)
Visual P0 ................. 3   (márgenes, tipo microscópico, prueba de gris)

Undefined refs ............ 0    PASS
Duplicate labels .......... 0    PASS
Broken DOI ................ 0    PASS en references.bib; v2 SIN VERIFICAR
Unverified central refs ... 26   FAIL
Stale numbers ............. 0    PASS  (0 macros divergentes)
```

Y los cinco gates humanos:

| Gate | Estado |
|---|---|
| **Director-ready** | **casi** — el trabajo es explicable en una frase, los objetivos están reconciliados con lo hecho, las hipótesis tienen estado final y los negativos están explicados. Falta enviar la versión completa con tabla comentario/corrección/página/estado (guía §6) |
| **Tribunal-ready** | **no** — tres flancos de pregunta abiertos y cero material de defensa |
| **Turnitin-ready** | **no** — sin informe institucional, y con ≈5 933 palabras duplicadas entre los dos entregables |
| **Defense-ready** | **no** — no existe presentación |
| **MH-candidate-ready** | **no hoy; sí alcanzable** — la ciencia da para el informe motivado; lo impiden los errores visibles y la defensa sin preparar |

---

## Camino más corto al depósito

Ordenado por coste, con el criterio de que cada paso cierre más de un gate.

1. **Mover Anexo F (8 pp) y J.5 al suplemento y comprimir H.** Cierra P0-1 y
   parte de FASE 26. De paso retira la subsección sin acentos y el resultado
   candidato.
2. **Recortar 11 pp de Marco teórico y Metodología al suplemento.** Cuerpo 58 pp,
   Resultados 50,0 %. Cierra P0-2 sin relleno. Combinado con el paso 1, los
   anexos quedan cerca de 20.
3. **Rehacer las tablas y figuras portadas de la revisión** —partir, girar o
   simplificar en vez de encoger. Cierra P0-4 y buena parte de P0-3, porque 5 de
   las 8 invasiones de margen vienen de esos mismos flotantes.
4. **Añadir `01-reproducibility.tex` a `thesis-appendices-v2.tex`** (una línea) y
   actualizar su commit y entorno. Cierra FASE 23 y el bloque §24 de la guía.
5. **Seis ediciones cortas:** acentos del Anexo J.5; la frase de Holm en
   `tab:results-compliance`; el `\estadoaporte` de no-Zeno; la definición de
   «local» en la Introducción; las dos atribuciones a Monderer–Shapley; la
   página 75 con la ruta desnuda. Cierran FASE 20, FASE 3, FASE 8, FASE 1 y
   FASE 21.
6. **Citar los 15 flotantes huérfanos o retirarlos**, y matizar los seis
   «distribuido» de FASE 11. Cierra un incumplimiento VIU explícito y la mayor
   contradicción interna del documento.
7. **Aplicar las correcciones de `lectura/06-bibliografia.md` §9** y citar la
   bibliografía metodológica. Cierra P0-5 y P0-6.
8. **Resolver la duplicación main↔suplemento** antes de Turnitin. P0-9 → P0-8.
9. **Ejecutar Turnitin.** P0-8.
10. **Congelar:** commit, tag, SHA, recompilar el suplemento, regenerar
    `census.json`, actualizar README-v2. P0-10.
11. **Construir la defensa.** Es el 70 % de la nota y hoy está a cero.

Los pasos 1–7 son entre dos y tres días de trabajo y convierten dos FALLA duros
en PASA. El paso 11 es el que decide la calificación.
