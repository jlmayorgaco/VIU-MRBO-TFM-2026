# Cobertura de la auditoría sobre los 60 frentes

La guía `01-auditoria-maestra.md` enumera **60 frentes de revisión**. Las demás
seis guías cubren algunos de ellos con mucho detalle y otros no los tocan. Esta
tabla dice cuál es cuál, para que la palabra «completa» signifique algo
verificable y no una impresión.

**Estado:** ✅ auditado con informe propio · 🟡 cubierto de pasada dentro de otro
informe · ⬜ sin auditar.

| # | Frente | Estado | Dónde |
|---:|---|:--:|---|
| 1 | Conformidad administrativa y normativa VIU | ✅ | `mecanica/01-gates.md`, `lectura/03-fases-y-deposito.md` |
| 2 | Coherencia entre título y tesis realizada | ✅ | `lectura/03`, `TITLE_DECISION.md` |
| 3 | Problema científico | 🟡 | `lectura/02-coherencia-y-flujo.md` |
| 4 | Motivación y relevancia | 🟡 | `lectura/02` |
| 5 | Preguntas de investigación — RQ | ✅ | `lectura/03` |
| 6 | Objetivo general | 🟡 | `lectura/03` |
| 7 | Objetivos específicos — OE | ✅ | `lectura/03` |
| 8 | Hipótesis | ✅ | `lectura/03`, `lectura/08` |
| 9 | Trazabilidad integral | ✅ | `mecanica/04`, `mecanica/05` |
| 10 | Contribuciones científicas | ✅ | `lectura/09-contribucion-novedad-industria.md` |
| 11 | Originalidad y novedad | ✅ | `lectura/09` |
| 12 | Estado del arte académico | ✅ | `lectura/06-bibliografia.md` |
| 13 | Bibliometría | 🟡 | `lectura/06`, `lectura/01-figuras.md` |
| 14 | Estado industrial | ✅ | `lectura/09` |
| 15 | Patentes | ✅ | `lectura/09` |
| 16 | Marco normativo | 🟡 | `lectura/06` (ISO 21423, ISO 3691-4, VDA 5050) |
| 17 | Arquitectura global de la tesis | ✅ | `lectura/02` |
| 18 | **SP1 — formación de coaliciones** | ✅ | `lectura/07-subsistemas-y-planta.md` |
| 19 | **SP2 — transporte** | ✅ | `lectura/07` |
| 20 | **SP3 — planificación y tráfico** | ✅ | `lectura/07` |
| 21 | Juego de integración / JCC | ✅ | `lectura/04-matematica.md`, `JCC_SEMANTIC_CROSSWALK.md` |
| 22 | Auditoría matemática general | ✅ | `lectura/04` |
| 23 | Teoremas, proposiciones y lemas | ✅ | `lectura/04` |
| 24 | **Notación matemática** | ✅ | `lectura/10-tablas-notacion-layout.md` |
| 25 | **Modelo físico y realismo robótico** | ✅ | `lectura/07` |
| 26 | Heterogeneidad | ✅ | `TITLE_DECISION.md`, `lectura/07` |
| 27 | Distributed/locality audit | ✅ | `TITLE_DECISION.md`, `lectura/02` |
| 28 | **Diseño experimental** | ✅ | `lectura/08-diseno-estadistica-comparadores.md` |
| 29 | **Estadística** | ✅ | `lectura/08`, `JCC_STATISTICAL_AUDIT.md` |
| 30 | **Baselines y comparadores** | ✅ | `lectura/08` |
| 31 | Reproducibilidad | ✅ | `lectura/03`, `mecanica/04` |
| 32 | CoppeliaSim | ✅ | `COPPELIA_PREFLIGHT_AUDIT.md` |
| 33 | Resultados negativos | 🟡 | `lectura/03`, `lectura/08` |
| 34 | Interpretación causal | ✅ | `lectura/08` (confusión de la ablación conjunta) |
| 35 | **Validez interna** | ✅ | `lectura/08` |
| 36 | **Validez externa** | ✅ | `lectura/08` |
| 37 | Conclusiones | 🟡 | `lectura/02`, `lectura/03` |
| 38 | **Trabajo futuro** | ✅ | `lectura/09` |
| 39 | Estructura narrativa | ✅ | `lectura/02` |
| 40 | Redacción académica | ✅ | `mecanica/02-prosa.md` |
| 41 | Patrones de escritura asistida | ✅ | `mecanica/02`, `mecanica/03` |
| 42 | Plagio y similitud | 🟡 | `lectura/05-suplementario.md` — **sin informe Turnitin** |
| 43 | Referencias | ✅ | `lectura/06` |
| 44 | Figuras | ✅ | `lectura/01` |
| 45 | **Tablas** | ✅ | `lectura/10` |
| 46 | Ecuaciones | ✅ | `mecanica/05` (50 etiquetadas, 0 sin citar) |
| 47 | Pseudocódigo | ✅ | corregido; 0 defectos en las 146 páginas |
| 48 | **Layout / composición visual** | ✅ | `lectura/10`, `mecanica/01` (márgenes) |
| 49 | **Front matter** | ✅ | `lectura/10` |
| 50 | Anexos de la memoria VIU | ✅ | `lectura/03` |
| 51 | Supplementary | ✅ | `lectura/05` |
| 52 | Consistencia main ↔ supplementary | ✅ | `lectura/05` (duplicación medida) |
| 53 | Revisión de todas las cifras | 🟡 | `mecanica/04` traza el origen, **no verifica valor a valor contra los datos crudos** |
| 54 | Auditoría de claims | 🟡 | `CLAIM_LEDGER.csv`, 40 filas — **no reauditado tras los cambios de esta sesión** |
| 55 | Defensa ante Reviewer 1 | ✅ | auditoría adversarial previa de la sesión |
| 56 | Defensa ante Reviewer 2 | ✅ | ídem |
| 57 | Defensa ante tribunal VIU | ✅ | `lectura/03` |
| 58 | Riesgos de rechazo | ✅ | `lectura/03` (10 FALLA, 10 `[P0]`) |
| 59 | Readiness final | ✅ | `lectura/03` |
| 60 | Pregunta final de control | 🟡 | se responde en el consolidado |

## Recuento

| Estado | n |
|---|---:|
| ✅ con informe propio | 48 |
| 🟡 de pasada | 11 |
| ⬜ sin auditar | 1 |

El único ⬜ es el **informe de Turnitin** (frente 42), y no depende de una
auditoría: hay que ejecutarlo. La detección de escritura asistida sí está
medida (`lmscan` 1,8 %, «Human-written»), y la duplicación interna
memoria ↔ suplemento también (28,6 % de frases largas), pero eso **no
sustituye** al informe de similitud institucional.

## Los tres 🟡 que conviene cerrar antes del depósito

**53 · Revisión de todas las cifras.** `mecanica/04` comprueba que cada cifra
viene de una macro y que las macros coinciden con el bundle de su campaña, lo
que garantiza la cadena. Lo que no hace es recomputar cada valor desde el
`runs.csv` crudo. Se hizo para SP3 —donde apareció la divergencia de 0,465
frente a 0,234— y para el juego de integración, pero no para las demás
familias.

**54 · Auditoría de claims.** El `CLAIM_LEDGER.csv` tiene 40 filas, pero se
escribió antes de las correcciones de esta sesión: el error de *caging*, la
adjudicación pendiente de H1b/H1c/H5b y el cambio del teorema del presupuesto
no están reflejados.

**42 · Plagio.** Sin informe institucional no hay conclusión posible. Lo que sí
se puede afirmar, y está medido, es que la duplicación interna es alta y que su
origen está identificado: el material duplicado es el desbordamiento de anexos
que se movió al suplemento sin retirarlo del principal.
