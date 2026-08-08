# SP1.N3 — auditoría de código y diseño propuesto

**Documento autocontenido para revisión externa.** Incluye los extractos de código
necesarios para verificar cada afirmación sin acceso al repositorio.

- **Fecha:** 2026-08-08
- **Estado:** solo diseño. Ninguna campaña ejecutada, ninguna semilla confirmatoria abierta, ningún RAW escrito.
- **Congelaciones de partida:** `SP1-N1-FROZEN` (13263e80), `SP1-N2-FROZEN` (42e05aad). Inmutables.

---

## 0. Contexto: qué está congelado

N2 dejó formalizado el problema heterogéneo y un oráculo central certificado en régimen
finito. N3 debe conservar **exactamente** ese problema y retirar únicamente el coordinador:

```
min  Σ_{i,k} d_ik · y_ik
s.a. Σ_k y_ik ≤ 1            para cada robot i
     Σ_i c_i · y_ik ≥ m_k    para cada carga k
     y ∈ {0,1}^{N×K}
```

Objetivo N2 congelado: distancia pura (`lambda_excess = lambda_robot = 0`).
Generador N2: capacidades lognormales renormalizadas a `Σc_i = N·q̄` fijo (para que CV sea lo
único que cambia entre niveles), demanda por Dirichlet `α=3.0` de `ρ·Σc_i`, workspace 100×100 m,
`q̄ = 5.0 kg`.

Pregunta de N3:

> ¿Qué factibilidad, calidad y coste de comunicación alcanzan baselines distribuidos enteros
> resolviendo el mismo problema heterogéneo de N2 sin optimizador ni registro global de robots?

---

## 1. Hallazgo principal

**Las implementaciones existentes en el repositorio (`src/viu_mrob_tfm/sp1_geo/allocators/`)
no son distribuidas y no resuelven el problema de N2.** No pueden reutilizarse.

Se auditaron línea por línea en lugar de confiar en sus nombres. Resumen:

| Componente | Veredicto |
|---|---|
| `allocators/cbba.py` (Capacity-CBBA) | No intercambia mensajes. Calcula el argmax global y **factura** rondas. |
| `allocators/grape.py` (Weighted-GRAPE) | Secuenciador de mejor-respuesta **centralizado**. |
| `allocators/grape.py` (`_best_pair_swap`) | Único fragmento genuinamente local, pero solo **intercambia puestos**. |
| `welfare.py` + `contributions.py` | Objetivo distinto: utilidad cóncava saturante + coste mezclado de 5 términos. |
| `scenario.py` (grafo) | kNN forzado conexo. **El control negativo de partición es inexpresable.** |
| `recovery.py` | Centralizado (certificado de mundo completo, conjunto global de robots). |
| `scripts/sp1_n3.py` | Reempaquetado del benchmark SP1-GEO. Piloto histórico. |

---

## 2. Capacity-CBBA: no ejecuta consenso

### 2.1 No existe paso de mensajes

Todo el "consenso" es este bloque (`allocators/cbba.py:99-109`):

```python
        # Simulate diameter rounds of max-consensus. The deterministic final
        # lexicographic maximum is the value every node obtains on a connected
        # graph; resource counts record the actual neighbor exchanges.
        winners: dict[int, tuple[float, int, int]] = {}
        for slot, bid, robot, action in proposals:
            candidate = (bid, -robot, action)
            if slot in winners:
                conflicts_removed += 1
            if slot not in winners or candidate > winners[slot]:
                winners[slot] = candidate
        consensus_rounds += diameter
```

Un único diccionario global sobre **todas** las propuestas de la flota, argmax lexicográfico en
una pasada, y después se suma `diameter` al contador de rondas *como si* el consenso hubiera
ocurrido. No hay aristas, ni buzones, ni vecinos.

**Consecuencia:** ninguna propiedad de convergencia de CBBA puede afirmarse desde este código,
porque no se ejecuta ningún consenso.

### 2.2 Usa el diámetro global del grafo como entrada

```python
    diameter = max(_graph_diameter(world.communication_adjacency), 1)   # cbba.py:47
```

El contrato N3 prohíbe explícitamente que el algoritmo use el diámetro real, el número global
de rondas restantes o una detección central de convergencia.

### 2.3 El control negativo de partición pasaría silenciosamente

```python
def _graph_diameter(adjacency: np.ndarray) -> int:          # cbba.py:14-30
    ...
        if np.any(distances < 0):
            return n            # grafo desconectado → devuelve n
```

En un grafo permanentemente desconectado, `_graph_diameter` devuelve `n`: la partición solo
encarece las rondas. **El ganador sigue siendo globalmente consistente.** Un experimento de
imposibilidad ejecutado contra este código reportaría éxito.

### 2.4 Los bids no son marginales sobre el déficit residual

```python
    zero = np.zeros(catalog.n_actions, dtype=float)
    base_bids = marginal_payoffs(world, catalog, zero, signal)   # cbba.py:45-46
```

`base_bids` se calcula **una sola vez en x = 0** y nunca se recalcula (se reutiliza en
`:76, :82, :94`). Por tanto una carga de 10 kg puntúa un robot de 1 kg y uno de 5 kg con un
número estático. No existe

```
r_k = m_k − Σ_{j∈C_k} c_j
```

en ninguna parte del bid. Es exactamente el defecto que la revisión anticipó.

### 2.5 Estado global mutable

`occupied` (`cbba.py:44, 116, 120`) es una única tabla de puestos compartida por todos los robots.

### 2.6 Mensajes y bytes son fórmulas, no medidas

```python
    messages = 2 * edges * consensus_rounds     # cbba.py:136
    bytes_sent = messages * 40                  # cbba.py:137
```

### 2.7 Lo único aprovechable

El desempate **sí** es determinista y merece conservarse:

```python
            candidate = (bid, -robot, action)   # cbba.py:104
```

(bid máximo → índice de robot menor → acción mayor).

---

## 3. Weighted-GRAPE: mejor-respuesta centralizada

### 3.1 El selector de movimiento es global

```python
def _best_unilateral(...):
    ...
    for robot in range(world.n_robots):          # grape.py:67
        ...
            if gain > best_gain + 1e-12:
                best_gain = float(gain)
                best = proposal
```

`_best_unilateral` recorre **todos** los robots y devuelve la única mejor desviación de toda la
flota; el bucle principal aplica ese movimiento (`grape.py:173, 185-196`). Un GRAPE distribuido
tiene a cada agente actuando sobre su propia vista.

`adjacency_restricted=True` solo limita **a qué cargas** puede unirse un robot (debe tener un
vecino ya en la coalición, `grape.py:77-87`); nunca limita **quién** puede moverse.

### 3.2 Potencial y unicidad evaluados globalmente

```python
    baseline = assignment_signal_potential(world, catalog, Assignment(profile), signal)  # :61
    value    = assignment_signal_potential(world, catalog, Assignment(proposal), signal) # :92
```

y `_valid_unique` (`grape.py:13-28`) comprueba unicidad de puestos sobre todos los robots.

### 3.3 Contadores

```python
    rounds = max(iterations, 1)        # grape.py:208 — movimientos aceptados, no rondas de comunicación
    messages = 2 * edges * rounds      # grape.py:209
    bytes_sent = messages * 48         # grape.py:226
```

### 3.4 Lo aprovechable

La separación de estado `local_stable` / `max_iterations` (`grape.py:221`) es correcta. Pero el
test de bloqueo mezcla un unilateral **restringido por adyacencia** con un pair **no restringido**
(`grape.py:199-206`), de modo que "estable" se mide contra dos vecindades distintas.

---

## 4. Weighted-Pair-GRAPE: solo intercambia puestos

```python
    for left in range(world.n_robots):
        for right in np.flatnonzero(world.communication_adjacency[left]):   # grape.py:116  ← local
            ...
            left_action, right_action = int(profile[left]), int(profile[right])
            if left_action < 0 or right_action < 0:                          # grape.py:121
                continue
            left_replacement  = catalog.action_for(left,  load[right_action], slot[right_action])
            right_replacement = catalog.action_for(right, load[left_action],  slot[left_action])
```

- La enumeración de pares **sí** está restringida a vecinos: es la única parte genuinamente local del módulo.
- Pero la selección vuelve a ser un **argmax global sobre todos los pares**.
- El movimiento **solo intercambia puestos**: dos robots permutan posiciones. Ninguno puede
  moverse a una carga que nadie ocupa.
- Ambos deben estar ya asignados, así que **ningún movimiento de pares puede reclutar un robot ocioso**.

Esto es estrictamente más débil que la desviación por pares que exige una afirmación de
estabilidad hedónica.

---

## 5. El objetivo no es el de N2

`welfare.py` maximiza una utilidad **cóncava saturante** de cobertura:

```python
def load_signal_value(service, demand, priority_value, *, curvature=1.0):
    ratio = np.maximum(np.asarray(service)[active], 0.0) / np.asarray(demand)[active]
    return float(priority_value * np.mean(1.0 - np.exp(-curvature * ratio)))
```

menos un **coste mezclado de cinco términos** (`contributions.py:14-20`):

```python
DEFAULT_COST_WEIGHTS = {
    "distance": 0.38,
    "energy": 0.24,
    "time": 0.18,
    "turn": 0.12,
    "reliability": 0.08,
}
```

Es decir:

- La capacidad es una **recompensa que satura**, no la restricción dura `Σ_i c_i y_ik ≥ m_k`.
  Cubrir el 90 % de una carga puntúa casi igual que cubrirla; en N2 lo primero es **infactible**.
- El objetivo no es `min Σ d_ik y_ik`: la distancia pesa 0,38 de un coste compuesto.

**El modelo tampoco es el de N2.** `sp1_geo` es un modelo físico de puestos de contacto —
`ContactSlot` con `offset_xy_m`, columnas de wrench, batería y márgenes de energía
(`models.py:90-144`, `contributions.py:48-58`). N2 no tiene puestos ni física.

---

## 6. El grafo de comunicación no admite el control negativo

```python
def _connected_knn_graph(positions, degree):        # scenario.py:83-108
    ...
    for robot in range(n):
        nearest = np.argsort(distances[robot])[: min(max(int(degree), 1), n - 1)]
        adjacency[robot, nearest] = True
    adjacency |= adjacency.T
    # A deterministic minimum spanning chain prevents accidental isolated
    # components while preserving sparse/local communication.
    visited = {0}
    while len(visited) < n:
        ...          # añade aristas hasta conectar todo
```

y el descarte de aristas **rechaza** cualquier eliminación que desconecte (`scenario.py:355-360`):

```python
                if adjacency[left, right] and rng.random() < loss_probability:
                    adjacency[left, right] = adjacency[right, left] = False
                    if _is_connected(adjacency):
                        ...
                    else:
                        adjacency[left, right] = adjacency[right, left] = True
```

Consecuencias:

- Es kNN, no R-disk: el parámetro es el **grado**, no el radio, y λ₂/diámetro no se barren de forma independiente.
- La conectividad está **garantizada por construcción**, de modo que el régimen de partición
  permanente es inalcanzable. El control negativo no puede ejecutarse.

---

## 7. La recuperación es centralizada

```python
    raw_certificate = certify_assignment(world, catalog, raw_assignment)   # recovery.py:245
    certificate     = certify_assignment(world, catalog, current)          # recovery.py:247, 332
```

certificado sobre el **mundo completo**, y el ranking de candidatos usa un conjunto global:

```python
def _rank_actions(world, catalog, load_index, available_robots: set[int]):   # recovery.py:33-40
    actions = np.flatnonzero(
        catalog.compatible
        & (catalog.load_index == int(load_index))
        & np.isin(catalog.robot_index, np.fromiter(available_robots, dtype=int))
    )
```

No puede servir como capa de recuperación de N3 sin reescribirse.

---

## 8. Riesgo de equidad ya activo para N4

```python
cbba.py:137   bytes_sent = messages * 40
grape.py:226  bytes_sent = messages * 48
qpg.py:283    bytes_sent = messages * (16 + 8 * world.n_loads * resource_dimension)
```

Tres constantes distintas cableadas, y **la de Geo-QPG es la única que escala con el número de
cargas**. Cualquier comparación de comunicación N3 vs N4 construida sobre esto mide las
constantes, no los algoritmos. Corregirlo es condición previa para N4, no un detalle.

---

## 9. Qué es realmente `scripts/results/sp1_levels/n3/`

`scripts/sp1_n3.py` reempaqueta el benchmark SP1-GEO (`GEO_SOURCE_ROOT`) y filtra solo la
etapa recuperada:

```python
    recovered = runs.loc[
        (runs["closure_stage"] == "RECOVERED")          # sp1_n3.py:39-42
        & runs["method"].isin(N3_METHODS)
    ].copy()
```

Reporta `served_load_rate` y `physical_welfare`, y calcula gaps contra el MILP de GEO: otro
objetivo, otro modelo, otra recuperación y otro contrato informativo. Además presenta
**únicamente** RECOVERED, que es precisamente lo que la revisión prohíbe.

**Tratamiento:** piloto histórico. Útil para elegir tamaños y detectar fallos; inutilizable como
resultado de N3. Se deja intacto en disco; la campaña nueva escribe en `n3_v1/`.

---

## 10. Contrato de información propuesto (N3.0)

A congelar antes de implementar y a heredar sin cambios por N4.

| Información | Acceso |
|---|---|
| Catálogo de cargas `(k, ℓ_k, m_k)` | Inmutable, anunciado a todos en t=0 |
| `(c_i, p_i)` propios | Privados del robot i |
| Capacidad, posición, bid, compromiso o coalición de otro robot | **Solo** por mensajes sobre `E` |
| Tabla global de robots | Prohibida |
| MILP en runtime | Prohibido |
| Reparación central | Prohibida en el resultado primario |
| Diámetro, λ₂, rondas restantes, flag global de convergencia | Prohibidos como entradas; solo los registra el observador |
| Observador global | Registra métricas; nunca influye en una decisión |

Nombre preciso: **decisión distribuida con tareas globalmente anunciadas y estado de robots
intercambiado únicamente entre vecinos.** No "percepción totalmente local": el catálogo de
cargas es un input común. Propagar también las tareas por el grafo es una **sensibilidad
posterior**, no la campaña primaria.

### Cumplimiento estructural, no por convención

Cada robot recibe un `RobotView` que expone únicamente su propio estado y su buzón. Todo lo
global queda **inalcanzable por construcción**, y un test verifica que la función de paso de
cada método no acepta ningún otro argumento.

> Una auditoría que dependa de leer el código es exactamente el modo de fallo que produjo los
> defectos §2.1–§2.6.

### Grafo

`G = (I, E)` estático, no dirigido, geométrico R-disk sobre las posiciones de N2.
Regímenes: completo / denso / medio / cerca del umbral / **partición permanente** (control negativo).
Se registra por mundo: `λ₂(L)`, grado medio, diámetro, componentes.

### Tres estados ortogonales, nunca colapsados

```
algorithm_status : CONVERGED | QUIESCENT | MAX_ROUNDS | TIME_LIMIT | DEADLOCK | ERROR
solution_status  : RAW_FEASIBLE | RECOVERED_FEASIBLE | CAPACITY_DEFICIT | ROBOT_CONFLICT
oracle_status    : OPTIMAL | FEASIBLE_TIME_LIMIT | INFEASIBLE | UNKNOWN
```

Un timeout no es una asignación infactible, y una asignación factible al llegar al tope de
rondas no prueba convergencia.

---

## 11. Teoría que N3 sí puede sostener

**T1 — Certificado distribuido de factibilidad.** La exclusividad `Σ_k y_ik ≤ 1` la certifica el
robot i por sí solo; la capacidad `Q_k(y) = Σ_i c_i y_ik ≥ m_k` la certifican los miembros de la
coalición k por sí solos. Por tanto *conflict-free*, *capacity-feasible* y *strictly feasible* son
predicados distintos y localmente verificables. **Estar libre de conflictos no es ser factible.**

**T2 — Imposibilidad bajo partición permanente.** En un grafo permanentemente desconectado,
ningún algoritmo que use solo información de su componente puede garantizar una asignación
globalmente factible para toda instancia en la que robots de componentes distintos compiten por
cargas comunes. Demostración por dos mundos globalmente distintos e indistinguibles para una
componente, que exigen compromisos diferentes.

Esto justifica que la conectividad sea un **supuesto**, no un detalle del simulador — y es
exactamente lo que el código actual (§2.3) no detectaría.

**T3 — Terminación por potencial para Weighted-GRAPE.** Con

```
Φ(y) = −Σ_{i,k} d_ik y_ik − λ_d Σ_k [m_k − Q_k(y)]₊ − λ_e Σ_k [Q_k(y) − m_k]₊
```

y aceptando **solo** mejoras estrictas: el espacio de perfiles es finito, Φ crece estrictamente,
luego la secuencia termina en un equilibrio unilateral (por pares, con movimientos de pares).

**Esto es terminación, no optimalidad**, y solo vale si la implementación acepta únicamente
mejoras estrictas — lo cual debe ser un test, no un supuesto.

**T4 — Invariantes de Capacity-CBBA.** Demostrables: como máximo un compromiso por robot;
ganadores identificables por versión/marca; desempate determinista; asignación final verificable
por T1.

### Teoremas que NO pueden heredarse

- Convergencia canónica de CBBA en `≤ N·D` rondas.
- La garantía DMG (*diminishing marginal gain*).
- La optimalidad de la resolución de conflictos de CBBA.

La adaptación multi-ganador con bids dependientes del déficit no cumple sus hipótesis. Si la
terminación se observa, se reportará como resultado **empírico** con el presupuesto de rondas
declarado.

---

## 12. Afirmaciones prohibidas en N3

1. Que un baseline "converge" sin una prueba válida para el scoring adaptado.
2. Que un equilibrio hedónico es óptimo — se compara con el MILP, nunca se llama óptimo.
3. Que CBBA o GRAPE es "mejor". N3 construye la frontera de referencia; no corona un ganador.
4. Que la salida RECOVERED es la salida nativa del método.
5. Que un timeout de rondas es infactibilidad.
6. Cualquier comparación de comunicación mientras §8 no esté corregido.

---

## 13. Campaña propuesta

| | Pregunta |
|---|---|
| **N3.E1** | White-box: ¿las implementaciones respetan sus invariantes, son deterministas y coinciden con una referencia del mismo protocolo en mundos pequeños? |
| **N3.E2** | Factibilidad y calidad frente al MILP de N2 en grafos conexos. |
| **N3.E3** | Precio de la localidad: calidad/factibilidad perdida por byte ahorrado. |
| **N3.E4** | Escala, pérdida de paquetes, retardo, presupuesto de rondas. |

**E1** — instancias construidas a mano + property tests: exclusividad, capacidad, desempates
deterministas, monotonía estricta de Φ, consistencia de winner lists, reejecución bit a bit,
invariancia a permutación de IDs, grafo completo, grafo conexo mínimo, y **grafo partido como
control negativo (debe fallar en garantizar factibilidad)**. Sin p-values: solo invariantes.

**E2** — mundos donde el oráculo de N2 es `OPTIMAL`; gap calculado solo ahí:

```
gap_w = (J_w^método − J_w^MILP) / J_w^MILP
```

**E3** — mismos mundos y métodos en los cinco regímenes de grafo. Figura principal: frente de
Pareto de factibilidad/calidad vs **bytes por agente**. La pregunta no es "¿es mejor el grafo
completo?" sino cuánto se pierde por byte ahorrado.

**E4** — factores variados de uno en uno: N; pérdida; retardo fijo/aleatorio; tope de rondas.

**RAW y RECOVERED se reportan siempre en paralelo:**

| Método | RAW factible | RECOVERED factible | gap RAW | gap RECOVERED | coste de recovery |

### Tamaños y número de ejecuciones

Reutilizando el generador de N2 (`q̄ = 5.0`, workspace 100×100 m, lognormal renormalizada,
Dirichlet `α = 3.0`), de modo que los mundos de N3 **son** mundos de N2.

| Exp | Rejilla | Mundos | × métodos | Runs |
|---|---|---|---|---|
| E1 | ~40 a mano + property tests | 40 | 3 | 120 |
| E2 | N=16, K=5; CV {0, 0.35, 0.65, 1.00}; ρ {0.70, 0.85}; 5 escenarios; 30 semillas | 1 200 | 3 | 3 600 |
| E3 | subconjunto de E2 (CV {0.35, 0.65}, ρ {0.85}, 5 escenarios, 30 semillas) × 5 regímenes de grafo | 300 × 5 | 3 | 4 500 |
| E4 | N ∈ {16,24,32,48,64}, K = 3N/10; CV 0.65; ρ 0.85; 15 semillas; {pérdida 0/0.05/0.15} ∪ {retardo 0/2} ∪ {tope 25/100} | 5 × 15 × 7 | 3 | 1 575 |

**Total ≈ 9 795 runs método–mundo + 1 500 resoluciones del oráculo** (rejilla E2, límite 30 s;
E3/E4 reutilizan el oráculo de E2 donde el mundo es idéntico). Reloj estimado: oráculo ~45 min,
baselines ~2–4 h monohilo. Las semillas derivan de un `base_seed` nuevo, abierto solo tras aprobación.

### Métricas por run

```
raw_feasible, recovered_feasible, robot_conflict, capacity_deficit,
distance_cost, optimality_gap, excess_capacity, coalition_size,
rounds, messages, bytes, runtime, recourse, censoring_status,
algorithm_status, solution_status, oracle_status,
lambda_2, mean_degree, diameter, components
```

---

## 14. Riesgos metodológicos

| Riesgo | Mitigación |
|---|---|
| Reutilizar los allocators de `sp1_geo` porque los nombres coinciden | Rechazado: §2–§7. Implementaciones nuevas. |
| Que reaparezca el atajo de consenso simulado (§2.1) | `RobotView` hace inalcanzable el estado global; el control de partición **debe** fallar. |
| Que las constantes de bytes decidan la comparación de N4 (§8) | Congelar un esquema de mensaje único; contar bytes serializados por tipo. |
| Reportar solo RECOVERED (como hace `sp1_n3.py`) | RAW y RECOVERED son endpoints separados y obligatorios. |
| Gap calculado donde el oráculo no está certificado | Gap solo donde `oracle_status == OPTIMAL`. |
| Las posiciones no están en el RAW de N2 | Ver abajo. |
| Heredar los teoremas de CBBA | §11 lista lo que no puede heredarse. |

### Reproducción de mundos

`make_world` devuelve `(capacities, masses, distance)` y **descarta las posiciones**
(`sp1_n2_confirmatory.py:105-153`), que N3 necesita para el grafo R-disk. Pero es determinista
en `seed`. N3 añadirá `make_world_with_positions` en un módulo **nuevo** que reproduce el mismo
flujo de RNG, con un test de regresión que verifica que sus `(capacities, masses, distance)` son
byte a byte idénticos a los de `make_world`. **N2 no se modifica.**

---

## 15. Archivos que se crearían / modificarían

**Creados**

```
experiments/configs/sp1_n3_confirmatory_v1.yaml
src/viu_mrob_tfm/sp1_n3/{__init__,contract,graph,messages,capacity_cbba,weighted_grape,recovery,certificate,worlds}.py
scripts/sp1_n3_confirmatory.py
scripts/sp1_n3_analysis.py
tests/test_sp1_n3_contract.py
tests/test_sp1_n3_invariants.py
scripts/results/sp1_levels/n3_v1/**
```

**Modificados**

```
scripts/sp1_levels_common.py   (etiquetas/colores de los tres métodos N3)
docs/04_CLAIMS_EVIDENCE.md     (filas de claims N3, tras la campaña)
```

**Intactos:** todo bajo `n1_v2/`, `n2_v1/`, `scripts/sp1_n1*.py`, `scripts/sp1_n2*.py`,
`thesis/sp1_levels_23p/main.tex`, `scripts/sp1_n3.py`, `scripts/results/sp1_levels/n3/`,
y todo el árbol `sp1_geo`.

---

## 16. Decisiones abiertas que requieren aprobación

1. **Reescribir vs adaptar.** Este plan asume implementaciones nuevas. Adaptar `sp1_geo` in situ
   cambiaría a la vez objetivo, modelo, grafo y recuperación.
2. **λ_d, λ_e en Φ.** GRAPE necesita penalizaciones para comparar perfiles infactibles, pero el
   objetivo de N2 tiene `λ_excess = λ_robot = 0`. Propuesta: las penalizaciones son un
   **dispositivo del solver**, se reportan como tal, y el objetivo puro de N2 se usa para toda
   métrica de calidad.
3. **Radios R-disk.** Requiere un piloto para elegir cinco regímenes de λ₂ bien separados.
4. **Capa de recuperación compartida.** La existente es centralizada (§7). ¿Rediseñarla como
   procedimiento aumentante local con radio declarado, o reportar solo RAW?

---

## 17. Confirmación de integridad

N1 y N2 no fueron tocados. Esta fase fue de solo lectura:

- `scripts/results/sp1_levels/n1_v2/` — sin diff frente a `SP1-N1-FROZEN`
- `scripts/results/sp1_levels/n2_v1/` — sin diff frente a `SP1-N2-FROZEN`
- `thesis/sp1_levels_23p/main.tex`, `scripts/sp1_n3.py`, `scripts/results/sp1_levels/n3/` y todo `sp1_geo` sin modificar
- Ningún solver ejecutado, ninguna semilla abierta, ningún RAW escrito, ninguna figura regenerada

**Pendiente de aprobación antes de los pilotos de la Fase 5.**
