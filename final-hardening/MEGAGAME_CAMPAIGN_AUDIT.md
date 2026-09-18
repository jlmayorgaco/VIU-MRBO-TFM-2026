# MEGAGAME_CAMPAIGN_AUDIT — auditoría forense de `results/megajuego/`

Fecha: 2026-09-18. Responde A0 y A0.1.
Nada de este documento es estimado: cada cifra procede de leer los artefactos o
de ejecutar el código.

---

## 1. Qué es esta campaña

Un banco factorial del **juego de integración** sobre un simulador propio, con
planta dinámica 2D. No es un guion suelto: son 1741 líneas de Python en
`src/viu_mrob_tfm/megajuego/`, de las cuales 830 son el mecanismo distribuido y
286 la planta.

### 1.1 Estructura del directorio

```
results/megajuego/
  protocolos.csv  aptitud.csv  planificador.csv  pasillo.csv
  seguridad.csv   reclutamiento.csv  hiperjuego.csv  hiperjuego2.csv
  SUMMARY.json
  factorial.log  factorial_h2.log  factorial_plan.log  factorial_plan_quick.log
  figs/   (trayectorias, líneas de tiempo, vídeos MP4 y .pkl por escenario)
  old/
```

**No hay `manifest.json`, ni `protocol/`, ni registro de semillas, ni lock de
entorno.** Todas las demás campañas confirmatorias del repositorio (SP6, SP7,
Cargo E2E) sí los tienen. Esta es la campaña peor gobernada del repositorio, y a
la vez la de mayor valor potencial.

### 1.2 La planta declarada

De la cabecera de `plant.py`, que documenta explícitamente lo que el mecanismo
puede y no puede suponer:

- **AMR diferencial** con chasis $(x,y,\theta,v,\omega)$ **y dos ruedas con
  inercia** $J_w$:
  $J_w\dot\omega_s=\tau_s-r_wF_s-b_w\omega_s$, con
  $F_s=\mathrm{clip}(c_g(r_w\omega_s-v_s),\ \text{disco de fricción compartido con la lateral})$.
- $m\dot v=F_L+F_R-b_vv+e^{\mathsf T}f_{\text{contacto}}$,
  $I\dot\omega=(F_R-F_L)b/2+\text{par de contacto}$.
- Restricción lateral **ideal salvo saturación**: si la fuerza lateral requerida
  excede el presupuesto del disco, se registra un **evento de deslizamiento** y
  la fuerza se satura.
- **Carga**: cuerpo rígido $(x,y,\theta,V,W)$ con huella rectangular.
- **Modo cargo**: pad en punto fijo; $f=k\varepsilon+d\,u$; límite $\mu_{\text{top}}N_i$
  con $N_i=mg/n$.
- **Modo caging**: parachoques circular contra el borde; $f_n=k_b[\delta]_+$,
  $|f_t|\le\mu_bf_n$; **sin tracción a distancia** (unilateral).
- **Paredes**: penetración registrada como violación.
- Unidades SI, integración semi-implícita, $dt=0{,}005$ s.

Esto es una planta dinámica con ruedas, contacto y fricción, no un modelo
cinemático.

### 1.3 El escenario

`bench.make_scenario`, con los valores que el banco usa realmente:

| Elemento | Valor |
|---|---|
| Planta | 22,0 × 14,0 m |
| Muro | $x=11{,}0$ |
| **Paso** | centro $y=7{,}0$, **anchura 3,3 m** |
| AMR | **N = 8** |
| Cargas | **K = 2** |
| Masa AMR | $\mathcal U(19,36)$ kg |
| Radio de rueda | $\mathcal U(0{,}085,\,0{,}11)$ m |
| Par máximo | $\mathcal U(4{,}2,\,7{,}0)$ N·m |
| Capacidad de contacto | $0{,}8\min(2\tau_{\max}/r_w,\ 0{,}7mg)$ |

Las cargas se colocan en lados opuestos del muro y **deben cruzar el paso**. Es,
por construcción, un escenario de paso estrecho con tráfico cruzado.

**Especificaciones de carga** (`specs[k % 3]`):

| # | masa | L×W | $r_{\text{req}}$ | modo | $\mu_f$ |
|---|---|---|---|---|---|
| 0 | 60,0 kg | 1,6 × 1,1 | 3 | cargo | 0,15 |
| 1 | 95,0 kg | 1,9 × 1,3 | 3 | cargo | 0,15 |
| 2 | 45,0 kg | 1,25 × 0,95 | 4 | **caging** | 0,10 |

La masa se perturba por semilla, $m\cdot\mathcal U(0{,}9,1{,}1)$, y la inercia se
deriva de la masa real, $I=m(L^2+W^2)/12$.

> **Consecuencia que condiciona todo lo demás: con $K=2$, el generador usa
> `specs[0]` y `specs[1]`, ambas en modo *cargo*. El modo caging nunca se
> ejercita en el factorial.** Las figuras `figs/caging_s0.*` proceden de
> ejecuciones sueltas fuera del banco, no de las ocho rejillas.

---

## 2. Las ocho rejillas

Medido con `final-hardening/audit_megajuego_campaign.py`. La octava familia
existe y se llama `hiperjuego2`: es `hiperjuego` con `cap_scale = 0,4` y
`a_ref = 1,0`, es decir, el mismo contraste de creencias bajo capacidad reducida.

| grid_id | pregunta científica | factores | niveles | celdas | semillas/celda | pareado | corridas |
|---|---|---|---|---|---:|---|---:|
| `protocolos` | ¿Qué protocolo de revisión sobre el potencial exacto entrega más? | `protocol` | best_response, smith, bnn, logit, replicator | 5 | **30** | sí | 150 |
| `aptitud` | ¿Basta la suma de capacidades o hace falta el margen de *wrench* por columnas? | `fitness` | vector, scalar | 2 | **30** | sí | 60 |
| `planificador` | ¿Waypoint o juego de continuaciones? | `planner` | waypoint, game | 2 | **30** | sí | 60 |
| `pasillo` | ¿Arrendamiento exclusivo o precio de congestión? | `corridor` | lease, price | 2 | **20** | sí | 40 |
| `seguridad` | ¿Qué aporta cada capa de barrera? | `safety` | nested, coalition, none | 3 | **20** | sí | 60 |
| `reclutamiento` | ¿Atómico o *shares* continuos con multiplicadores? | `recruit` | atomic, gne_pd | 2 | **20** | sí | 40 |
| `hiperjuego` | ¿Cuánto daña el error de creencia y cuánto lo repara recertificar? | `belief_err`, `recertify` | 0,0 / 0,35 × True / False | 4 | **20** | sí | 80 |
| `hiperjuego2` | Lo mismo con capacidad reducida (`cap_scale`=0,4) | `belief_err`, `recertify` | 0,0 / 0,35 × True / False | 4 | **20** | sí | 80 |
| | | | | **24** | | | **570** |

Campos comunes a todas: `plant_model` = planta dinámica 2D con ruedas y contacto,
$N=8$, $K=2$; `information_contract` = $n$-saltos con $R_{\text{com}}=9{,}0$ m,
`n_hops = 2`; `source_script` = `viu_mrob_tfm.megajuego.bench.factorial`;
`raw_data` = `results/megajuego/<grid>.csv`; `processed_data` =
`results/megajuego/SUMMARY.json`.

### 2.1 El N real

**«30 semillas» significa 30 mundos independientes como máximo, no 30 por
celda en todas las rejillas.**

- Espacio de semillas: `range(30)`, es decir 0–29.
- `protocolos`, `aptitud` y `planificador` usan las 30.
- Las otras cinco usan `seeds[:max(6, 30*2//3)]` = **las 20 primeras** (0–19).
- **Unión de semillas en toda la campaña: 30.**

Las celdas de una misma rejilla comparten exactamente el mismo conjunto de
semillas, y `make_scenario(seed)` es determinista con $N,K$ fijos, de modo que
**un mismo `seed` produce el mismo mundo en toda celda y toda rejilla**. El
pareado es genuino y además cruza rejillas.

**Unidad experimental = mundo (semilla).** Los 8 AMR, las 2 cargas y los pasos
temporales de una corrida no son réplicas independientes y no se cuentan como
tales.

### 2.2 Endpoints registrados

`success` (booleano, ambas cargas entregadas) como primario; y como secundarios
`n_done`, `makespan`, `energy_Wh`, `min_sep_amr`, `min_sep_load`, `msgs`,
**`false_cert`** (certificados que la física desmiente), `recert_reject`,
`revisions`, `wall_pen_max`, `slip`, `corridor_double`, `cpu_s` y `phi_oracle`
(valor del oráculo central con información verdadera, calculado por enumeración).

---

## 3. Procedencia — A0.1

### 3.1 Lo que no existe

- El módulo `src/viu_mrob_tfm/megajuego/` estaba **sin trackear**: `git log` del
  directorio no devolvía nada.
- `results/megajuego/` también **sin trackear**.
- Sin `manifest.json`, sin `seed_registry`, sin `environment.lock`, sin
  `config_sha256`, sin `git_sha_at_freeze`.

No hay, por tanto, ningún hash original de generación con el que contrastar. Los
hashes de este documento son **hashes de auditoría** tomados hoy.

### 3.2 Cronología, que es lo que decide

| Artefacto | Fecha y hora |
|---|---|
| `protocolos.csv` | 2026-09-08 **16:34** |
| `aptitud.csv` | 16:47 |
| `pasillo.csv` | 16:56 |
| `seguridad.csv` | 17:07 |
| `reclutamiento.csv` | 17:16 |
| `hiperjuego.csv` | 17:34 |
| `bench.py` (código) | **17:36** |
| `hiperjuego2.csv` | 17:56 |
| `trajgame.py` (código) | 18:51 |
| `run_factorial.py` (código) | 19:10 |
| **`mechanism.py` (código)** | **19:15** |
| `planificador.csv` | **19:29** |

**Siete de las ocho rejillas se escribieron antes de la última edición del
mecanismo. Solo `planificador` es posterior.**

### 3.3 La prueba de reproducción

Ejecuté la celda de referencia con el código actual, sin tocar nada.

`protocolos`, `protocol=smith`, `seed=0`:

| métrica | archivado (16:34) | reejecución (código actual) | |
|---|---|---|---|
| `success` | True | True | = |
| `n_done` | 2 | 2 | = |
| `revisions` | 6 | 6 | = |
| `false_cert` | 0 | 0 | = |
| **`phi_oracle`** | **159,08794149024982** | **159,08794149024982** | **= exacto** |
| `makespan` | 126,26 | **159,58** | **≠** |
| `min_sep_amr` | −0,0996 | **−0,3481** | **≠** |
| `msgs` | 763 208 | **846 713** | **≠** |
| `energy_Wh` | 8,5938 | 8,3977 | ≠ |
| `wall_pen_max` | 0,0721 | 0,1128 | ≠ |

`phi_oracle` coincide hasta el último dígito. Ese valor lo produce
`oracle_assignment` sobre `make_scenario(seed)`, de modo que **el generador de
mundos y las funciones de valor de coalición y coste de viaje están intactos: el
mundo es idéntico**. La divergencia está íntegramente en el mecanismo, editado a
las 19:15.

**Control.** `planificador`, `planner=game`, `seed=0`, generado a las 19:29, es
decir después de esa edición:

| métrica | archivado | reejecución |
|---|---|---|
| `makespan` | 159,57999999992737 | 159,57999999992737 |
| `min_sep_amr` | −0,3481327396089397 | −0,34813273960893976 |
| `msgs` | 846 713 | 846 713 |
| `energy_Wh` | 8,397650229007668 | 8,397650229007668 |
| `wall_pen_max` | 0,1128275045164173 | 0,11282750451641732 |

**Reproduce bit a bit.** El diagnóstico queda cerrado: el código cambió a media
campaña y las rejillas anteriores quedaron obsoletas.

Detalle que lo confirma por partida doble: mi reejecución de
`protocolos/smith/seed=0` devolvió **exactamente** los valores archivados de
`planificador/game/seed=0`. El planificador de juego es hoy el camino por
defecto, y el `protocolos` archivado corrió con el mecanismo anterior.

### 3.4 Veredicto de procedencia

| Rejilla | Procedencia | Uso permitido |
|---|---|---|
| `planificador` | **PROVENANCE_EXACT** | verificable; reproduce con el código auditado |
| `protocolos` | **PROVENANCE_UNKNOWN** | no citable como cifra |
| `aptitud` | PROVENANCE_UNKNOWN | no citable como cifra |
| `pasillo` | PROVENANCE_UNKNOWN | no citable como cifra |
| `seguridad` | PROVENANCE_UNKNOWN | no citable como cifra |
| `reclutamiento` | PROVENANCE_UNKNOWN | no citable como cifra |
| `hiperjuego` | PROVENANCE_UNKNOWN | no citable como cifra |
| `hiperjuego2` | PROVENANCE_UNKNOWN | no citable como cifra |

No se borra nada. El archivo histórico se conserva íntegro; lo que se restringe
es su uso.

### 3.5 Consecuencia operativa

La campaña archivada **no puede promoverse al TFM tal como está**. Pero el
diseño sí es válido y el código actual es determinista y reproducible, de modo
que la vía limpia es **regenerar la campaña completa con el código actual bajo
manifiesto congelado**, lo que convierte PROVENANCE_UNKNOWN en PROVENANCE_EXACT
para las ocho rejillas.

Coste medido, no estimado: 107 s por corrida (medido dos veces), 570 corridas,
22 CPU lógicas → **≈ 1 h con 16 procesos**.

Manifiesto congelado antes de ejecutar en
`final-hardening/megajuego_regeneration_manifest.json`, commit `73b0b720d`.
Salida en `results/megajuego_regen_v1/`; `results/megajuego/` queda intacto.

---

## 4. Defectos estadísticos del guion original

Detectados leyendo `run_factorial.py`, antes de ver ningún resultado nuevo.

1. **`wilson()` da el IC de una tasa, y se está usando como si describiera un
   contraste.** `SUMMARY.json` publica un Wilson por celda. Dos intervalos
   separados no son el intervalo de una diferencia.
2. **No hay ninguna corrección de multiplicidad.** `summarize()` calcula un
   `mcnemar_p` por celda frente a la referencia `protocolos/smith` —más de
   veinte comparaciones— y no aplica Holm en ningún punto.
3. **Los endpoints continuos se reportan como medianas por celda**, no como
   efecto pareado con incertidumbre, pese a que el diseño es pareado por mundo.
4. **La referencia es siempre `protocolos/smith`**, incluso para rejillas cuya
   pregunta natural es interna (por ejemplo `safety=none` frente a
   `safety=nested`). El contraste publicado no siempre es el contraste que la
   pregunta pide.
5. `summarize()` recorre **todo** `.csv` del directorio, de modo que cualquier
   fichero suelto entraría en el resumen.

La función `mcnemar_exact(b,c)` sí es correcta: calcula
$2\sum_{i=0}^{\min(b,c)}\binom{n}{i}/2^n$ con $n=b+c$, que es el $p$ exacto
bilateral.

Los cuatro primeros defectos se corrigen en la regeneración, con las familias de
Holm declaradas en el manifiesto **antes** de ejecutar.
