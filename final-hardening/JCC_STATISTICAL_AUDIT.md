# JCC_STATISTICAL_AUDIT — diseño inferencial de la campaña del juego de integración

Fecha: 2026-09-18. Responde A2 y A2.1.

**Parte I (diseño) se fijó antes de ejecutar** y está congelada en
`megajuego_regeneration_manifest.json`, commit `73b0b720d`.
**Parte II (resultados)** se rellena tras la ejecución, sin alterar la Parte I.

---

## Parte I — Diseño, congelado antes de ver ningún resultado

### 1. Unidad experimental

**Un mundo, identificado por su semilla.**

`make_scenario(seed)` es determinista con $N=8$, $K=2$, de modo que la misma
semilla produce el mismo mundo en toda celda y toda rejilla. Las celdas de una
rejilla están pareadas por mundo, y el pareado cruza rejillas.

No se cuentan como réplicas independientes: los 8 AMR de una corrida, las 2
cargas, los pasos temporales de una trayectoria, ni las rondas del mercado de
*wrench*.

Esto coincide con la política declarada del proyecto en
`docs/03_EXPERIMENT_PROTOCOL.md` §7: *«La unidad independiente es el mundo o
bloque escenario--semilla; robots, cargas y muestras temporales son
observaciones anidadas.»*

### 2. Endpoints y su tratamiento

| endpoint | tipo | pareado | tratamiento |
|---|---|---|---|
| `success` | binario | sí | **primario**. Diferencia pareada de proporciones con IC bootstrap percentil sobre mundos, más McNemar exacto para el contraste |
| `n_done` | recuento 0–2 | sí | descriptivo |
| `makespan` | continuo | sí | efecto pareado con IC bootstrap |
| `energy_Wh` | continuo | sí | efecto pareado con IC bootstrap |
| `msgs` | recuento | sí | efecto pareado con IC bootstrap |
| `min_sep_amr` | continuo | sí | efecto pareado con IC bootstrap |
| `revisions` | recuento | sí | efecto pareado con IC bootstrap |
| `wall_pen_max` | continuo | sí | efecto pareado con IC bootstrap |
| `false_cert` | recuento | sí | descriptivo; es un **resultado de seguridad**, se reporta siempre |
| `phi_oracle` | continuo | — | valor del oráculo, no un tratamiento |

### 3. La corrección que motiva este documento

El guion original (`run_factorial.py`) publica **un intervalo de Wilson por
celda** y lo presenta junto a un contraste. Eso es incorrecto en el punto exacto
que A2 señala:

> $\mathrm{IC}(A)$ y $\mathrm{IC}(B)$ separados **no** son el $\mathrm{IC}$ de $A-B$.

Dos intervalos que se solapan no implican ausencia de diferencia, y dos que no
se solapan sobreestiman la evidencia. Con diseño pareado, además, se desperdicia
la correlación entre celdas del mismo mundo.

**Regla adoptada:** Wilson se conserva **solo** para describir la tasa de una
celda aislada. Toda diferencia entre celdas lleva IC bootstrap percentil de la
diferencia pareada, remuestreando **mundos**, no corridas.

### 4. Parámetros del bootstrap

| parámetro | valor | origen |
|---|---|---|
| Remuestreos | 10 000 | manifiesto, antes de ejecutar |
| Nivel | 0,95 | manifiesto |
| Semilla de análisis | 20260918 | manifiesto; **distinta** de las semillas del simulador (0–29) |
| Unidad remuestreada | mundo | §1 |

La semilla de análisis separada cumple la exigencia de
`docs/03_EXPERIMENT_PROTOCOL.md`: *«Remuestrear mundos independientes en los
intervalos bootstrap y registrar una semilla de análisis distinta de las
semillas del simulador.»*

### 5. Contraste por rejilla: referencia interna, no global

El guion original compara **todo** contra `protocolos/smith`. Para
`seguridad=none` la pregunta natural no es «¿difiere de Smith?» sino «¿qué
pierde al retirar la barrera anidada?». Se corrige usando la referencia que cada
pregunta pide:

| rejilla | referencia | contraste |
|---|---|---|
| `protocolos` | `smith` | los otros cuatro protocolos |
| `aptitud` | `vector` | `scalar` — *margen de wrench frente a suma de capacidades* |
| `planificador` | `game` | `waypoint` |
| `pasillo` | `lease` | `price` |
| `seguridad` | `nested` | `coalition`, `none` |
| `reclutamiento` | `atomic` | `gne_pd` |
| `hiperjuego` | `belief_err=0,0` y `recertify=True` | efecto de cada factor |
| `hiperjuego2` | ídem, con `cap_scale=0,4` | efecto de cada factor |

### 6. Familias de multiplicidad

**No se aplica una única corrección de Holm sobre todas las tablas.** Cada
familia corresponde a una pregunta planificada, y Holm se aplica dentro de ella.

| familia | rejillas | contrastes | $k$ |
|---|---|---|---:|
| **F1 — protocolo de revisión** | `protocolos` | los cuatro no-referencia frente a `smith` | 4 |
| **F2 — ablación de seguridad** | `seguridad` | `coalition` y `none` frente a `nested` | 2 |
| **F3 — elecciones de mecanismo** | `aptitud`, `pasillo`, `reclutamiento`, `planificador` | un contraste pareado por rejilla | 4 |
| **F4 — creencia y recertificación** | `hiperjuego`, `hiperjuego2` | efecto de `belief_err` y de `recertify` en cada rejilla | 4 |

Esta enumeración cierra el hueco que la auditoría del corpus documental
identificó: la política del proyecto exige predeclarar familias pero **nunca las
enumera a nivel de repositorio**. Aquí quedan enumeradas para esta campaña.

### 7. Prohibiciones declaradas

- **Sin parada opcional.** La campaña se ejecuta una vez con el diseño
  congelado y se reporta completa, incluidas las celdas desfavorables.
- **Sin cambios post-hoc de rejilla.** Ninguna celda se añade, quita ni
  reordena después de abrir los resultados.
- **Sin elegir la versión favorable.** Si la regeneración diverge del archivo
  histórico, se investiga y se documenta; no se escoge la que convenga.
- **Sin reintento con otra semilla.** Una corrida fallida se registra con su
  traza; no se sustituye.
- **Sin $p$ sin hipótesis.** Los contrastes inferenciales son los de las cuatro
  familias; el resto es descriptivo y se etiqueta como tal.

### 8. Qué no puede concluirse de esta campaña, por diseño

Fijado antes de ejecutar, para que ningún resultado tiente a ampliarlo:

- nada sobre *caging* — con $K=2$ el modo no se ejercita;
- nada sobre el presupuesto de ejecución — no está instrumentado;
- nada sobre la separación de Bézier — la campaña usa continuaciones
  discretizadas, no esa familia analítica;
- nada sobre recuperación ante fallo de miembro — no es un factor;
- nada sobre la capa epistémica por diferencias — no está implementada;
- nada sobre validez industrial, hardware, tres cargas simultáneas ni escala
  mayor que $N=8$.

---

## Parte II — Resultados

*(pendiente de la ejecución; se rellena con `analyze_megajuego_regen.py`, que
implementa exactamente la Parte I y escribe `STATISTICS.csv` y
`STATISTICS.json` en `results/megajuego_regen_v1/`)*
