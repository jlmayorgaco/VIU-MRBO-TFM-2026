# SP1.N3 — entrega tras implementar contrato, grafo, mensajes, mundos, E1 y pilotos

**Documento autocontenido.** No se ejecutó ninguna campaña confirmatoria, no se abrió
`base_seed` confirmatoria, no se escribió RAW y no se tocaron N1 ni N2.

- **Fecha:** 2026-08-08
- **Congelaciones de partida:** `SP1-N1-FROZEN` (13263e80), `SP1-N2-FROZEN` (42e05aad)
- **Semilla usada:** solo `PILOT_SEED_BASE = 4242000` (pilotos técnicos)
- **Semilla confirmatoria:** `CONFIRMATORY_SEED_BASE = None` (cerrada)

---

## Estado tras las correcciones

Los cuatro hallazgos de los pilotos están **corregidos y con test de regresión**. Se conservan
descritos abajo porque la evidencia del fallo es parte del resultado: explican por qué la
implementación es como es.

| # | fallo | antes | después |
|---|---|---|---|
| 0 | GRAPE diverge bajo pérdida y declara `CONVERGED` | 25/40 divergentes, todos `CONVERGED` | 0/40 a 15 % y 30 %; lo residual a 50–90 % sale como `DIVERGED`, **cero `CONVERGED` falsos** |
| 1 | Capacity-CBBA oscila | 0/27 terminan, 10 en `DEADLOCK` | **135/135 terminan**, 0 `DEADLOCK` |
| 3 | Tablas CBBA obsoletas tras una pérdida | 1,6 % de entradas obsoletas a 30 % | **0/1920 a 0 %, 15 % y 30 %** |
| — | punto fijo confundido con ciclo (introducido al corregir 1) | `DEADLOCK` espurio | quiescencia y ciclo se juzgan por la firma de decisión, no por el silencio |

Qué se cambió, en una línea cada uno:

- **GRAPE**: cada propuesta distinta se reintenta hasta 4 veces por vecino en lugar de enviarse
  una sola vez. Reenviar *cada* ronda también lo arreglaba, pero costaba ×34 en bytes; con
  reintentos acotados el coste es ×2,5.
- **Invariante de divergencia**: si al terminar los robots no sostienen el mismo perfil, el
  estado es `DIVERGED`, nunca `CONVERGED`. Hace falta igualmente, porque el acuerdo exacto
  sobre enlaces con pérdida es el problema del ataque coordinado y **no tiene solución**: los
  reintentos hacen improbable la divergencia, no imposible.
- **CBBA**: el bid se congela al comprometerse (dejar que flotara con el residual reordenaba el
  prefijo sin que nadie pujara) y cada robot guarda una **barrera** por carga: solo vuelve a una
  carga de la que fue desplazado con una puja estrictamente mejor. La barrera no decrece y el
  espacio de pujas es finito, luego el proceso termina.
- **CBBA**: retransmisión completa cada `N` rondas, y la ventana de quiescencia cubre un ciclo
  entero de refresco, para que "silencio" no se declare en el hueco entre heartbeats.

**Sigue abierto:** §16.2 (Pair-GRAPE escala ≈ N^4.9) y §16.3 (calidad de GRAPE invariante al
grafo conexo). Ninguno es un bug; son decisiones de alcance.

---

## Los cuatro hallazgos, con la evidencia original

### 0. CRÍTICO — bajo pérdida de paquetes, GRAPE **diverge y aun así declara `CONVERGED`**

Sondeo sobre 40 ejecuciones (N=16, regímenes `medium` y `threshold`, pérdida 15 % y 30 %),
contando cuántos perfiles distintos sostienen los 16 robots al terminar:

```
divergencia en 25/40 ejecuciones
peor caso: 13 perfiles distintos entre 16 robots
estado reportado en las 25: CONVERGED
```

La demostración de terminación de la opción A **presupone entrega fiable**, y esa hipótesis
resultó ser portante, no decorativa. Si la inundación no llega a todos dentro de la época,
cada robot cierra la época con un ganador distinto, aplica un movimiento distinto, y a partir
de ahí su `coverage` y su `actions` dejan de coincidir con los del resto. Peor: como cada uno
evalúa "sin movimiento" contra *su propio* perfil divergente, todos declaran terminación por
separado y el motor observa `terminated=True` en todos → **certificado falso de convergencia**.

Con entrega fiable (pérdida 0) la consistencia se mantiene en el 100 % de las ejecuciones, y
con pérdida 15 % sobre grafos densos suele sobrevivir por redundancia; pero eso es suerte
estructural, no una garantía.

**Consecuencia:** los tratamientos `loss-05` y `loss-15` de E4 producirían hoy resultados
silenciosamente incorrectos etiquetados como convergidos. E4 no puede ejecutarse hasta
resolverlo, y hace falta además un invariante del observador que detecte la divergencia en vez
de confiar en que no ocurra.

**Corregido.** Reintentos acotados + invariante `DIVERGED`. Ver «Estado tras las correcciones».

### 1. Capacity-CBBA con el bid acordado **no termina: oscila**

Sobre 27 ejecuciones piloto:

| método | CONVERGED | DEADLOCK | QUIESCENT_OBSERVED |
|---|---:|---:|---:|
| capacity_cbba | **0** | **10** | 17 |
| weighted_grape | 27 | 0 | 0 |
| weighted_pair_grape | 27 | 0 | 0 |

Y con presupuesto ampliado a 4 000 rondas el resultado **empeora** respecto al presupuesto
pequeño, porque el corte cae en otro punto del ciclo límite:

```
N=24 threshold rep2   budget=192    D = 7.963
N=24 threshold rep2   budget=4000   D = 27.407     <-- peor con más rondas
N=16 threshold rep1   budget=128    FEASIBLE
N=16 threshold rep1   budget=4000   D = 4.905      <-- peor con más rondas
```

**Consecuencia:** tal como está, el endpoint RAW de CBBA no es una aproximación a nada; es
una foto arbitraria de dónde estaba la oscilación cuando se agotó el reloj. Publicar
`P(raw_feasible)` de CBBA sobre esta base mediría el presupuesto, no el método.

**Causa.** El bid depende del residual estimado, que depende de quién está en la coalición,
que depende del bid. Un robot desplazado del prefijo libera, vuelve a pujar, desplaza a otro,
y el ciclo se cierra. No hay mecanismo monótono: nada impide que la puja de un robot sobre
la misma carga suba y baje indefinidamente. CBBA canónico evita esto con precios/pujas
monótonas; la adaptación multi-ganador con residual dinámico pierde esa propiedad.

Lo que sí hice: el observador ahora detecta el ciclo y lo reporta como `DEADLOCK` en vez de
`MAX_ROUNDS`, para que el estado no mienta. Es observación pura, nunca decide ni detiene.

**Corregido.** Bid congelado al comprometerse + barrera monótona por carga. Esto **redefine el
método**: `Capacity-CBBA` pasa a llevar una barrera de retorno, y así queda congelado.

### 2. Weighted-Pair-GRAPE escala ≈ N^4.9 en reloj

Mediana de tiempo de pared, grafo completo:

| método | N=16 | N=24 | N=32 |
|---|---:|---:|---:|
| capacity_cbba | 37 ms | 148 ms | 393 ms |
| weighted_grape | 139 ms | 472 ms | 1 048 ms |
| **weighted_pair_grape** | **902 ms** | **7 060 ms** | **26 245 ms** |

Exponente empírico ≈ 4,9. Extrapolado a N=64: **≈ 13 min por ejecución**. E4 propone
N=64 × 30 mundos × 7 tratamientos = 210 ejecuciones solo de pair-GRAPE en esa celda,
es decir **≈ 45 h**. E4 no es ejecutable tal como se propuso.

El coste viene de la enumeración conjunta: cada robot evalúa (K+1)² desviaciones por vecino
en cada arranque de época, y con grafo completo eso es O(N·K²) por robot, O(N²K²) por época,
O(N³K²) por ejecución.

**Decisión requerida (§16.2).**

### 3. La opción A hace que la *calidad* de GRAPE sea invariante al grafo conexo

Consecuencia directa de elegir selección serial distribuida: la época aplica el máximo global
sobre un perfil globalmente consistente, así que en cualquier grafo **conexo** la trayectoria
—y por tanto el resultado— es la misma. Solo cambia lo que cuesta comunicarla.

```
weighted_grape, mismo mundo:   complete / medium / threshold  ->  D = 1.011, J = 291.25 (idéntico)
bytes por robot:                  19 964  /  11 200  /   8 272
```

No es un error: es el precio del teorema. Pero significa que **el eje de calidad de E3 es
plano para GRAPE** y el "precio de la localidad" se reduce, para esta rama, a un precio
puramente comunicacional. CBBA sí varía con el grafo (J = 217,65 / 213,57 / 238,12).

Esto debe decirse en E3 explícitamente, o el lector concluirá que la localidad no cuesta calidad.

---

## 1. Pseudocódigo de los tres métodos

### Capacity-CBBA (adaptación)

```
estado_i = { tabla: {robot -> BidRecord}, acked: {vecino -> {robot -> versión}} }
BidRecord = (robot, target, capacidad, ΔD, -d, token, versión)

cada ronda t:
  1. para cada mensaje recibido, para cada registro r:
         si r.robot == i: descartar        # cada robot es autoridad sobre sí mismo
         si r.versión > tabla[r.robot].versión: tabla[r.robot] = r

  2. si mi target k >= 0:
         miembros = {r in tabla : r.target == k}
         si i no está en prefijo_voraz(miembros, m_k):  target = -1     # desplazado

  3. si target < 0:  target = argmax_k b_ik   sobre k con r_ik > 0
     recalcular ΔD, -d para el target

  4. si algo cambió: versión += 1

  5. para cada vecino v:
         enviar los registros cuya versión > acked[v][robot]
```

`prefijo_voraz(miembros, m_k)`: ordena por bid descendente y acumula capacidad hasta cubrir
`m_k`; todo lo que sobra es redundante y libera (con `d_ik > 0` salir siempre baja el objetivo).

### Weighted-GRAPE / Weighted-Pair-GRAPE (opción A)

```
estado_i = { coverage[K], actions[N], vecinos:{cap, token, distancias}, best, época, done }
H = max(N, 2)

ronda 0:           enviar (c_i, token_i, d_i[·]) a cada vecino          # handshake
ronda t >= 1, local = (t-1) mod H:
  merge(inbox)                                                          # siempre
  si local == 0:     best = mejor_desviación_propia();  reenviar
  si 1 <= local <= H-2:  reenviar best si cambió desde el último envío a ese vecino
  si local == H-1:
      si best es "sin movimiento":  done = True;  terminated = True      # certificado
      si no: aplicar(best); época += 1
```

`mejor_desviación_propia` recorre, para el unilateral, `a'_i ∈ {idle, 0..K-1}`; para pares,
`(a'_i, a'_j) ∈ {idle,0..K-1}²` con cada vecino `j`. Cubre idle→carga, carga→idle, uno se
mueve y el otro no, intercambio, y ambos a cargas distintas.

---

## 2. Semántica de rondas (congelada)

- Síncrona, `t = 0 … T_max−1`.
- En `t` un robot ve **solo** mensajes entregados hasta `t`.
- Todos los robots ejecutan `step` antes de que se encole ningún mensaje del turno, así que
  un mensaje emitido en `t` **no puede** influir en otra decisión dentro de `t`.
- Entrega en `t + 1 + delay`; pérdida y retardo se sortean por `(world_id, treatment, u, v, t)`,
  nunca por método, de modo que dos algoritmos ven el mismo estado de enlace en la misma arista
  y ronda aunque emitan tráfico distinto.
- El observador registra; **no decide, no detiene, no repara**.
- Enviar a un no-vecino lanza excepción.

Constantes públicas permitidas: `N`, `K`, `T_max`. **No** expuestos: adyacencia global,
diámetro, λ₂, rondas restantes, asignación global.

## 3. Terminación de GRAPE: lo que sí se prueba y lo que no

**Se prueba.** Al inicio de cada época el perfil es globalmente consistente. Se inunda `N−1`
rondas y el diámetro de cualquier grafo conexo de `N` nodos es ≤ `N−1`, luego todos terminan
la época con el mismo ganador y aplican la misma transición. Esa transición mejora
estrictamente `(D, J)` en orden lexicográfico. El espacio de perfiles es finito y no se puede
revisitar un perfil, luego el proceso termina. Cuando el ganador inundado es "sin movimiento",
todos lo saben simultáneamente: **certificado distribuido de terminación**, y es el único caso
del paquete autorizado a declarar `CONVERGED`.

Verificado en `test_grape_applies_one_strictly_improving_move_per_epoch`, que reconstruye la
trayectoria y comprueba `(D,J)` estrictamente decreciente época a época.

**No se prueba.** Nada sobre optimalidad. Un equilibrio unilateral o por pares no es óptimo
social; el piloto lo muestra: `weighted_grape` converge a `D = 1.011` (infactible) mientras
`weighted_pair_grape` alcanza `D = 0` en el mismo mundo. Tampoco se prueba nada sobre la
variante concurrente sin épocas (opción B), que no está implementada.

**Un detalle que costó un bug real.** Las ganancias viajan en float32. Sin canonicalizar, un
robot ordenaba su propia propuesta en float64 y las ajenas en float32, así que dos robots
podían ordenar el mismo par de candidatos al revés y el "max-consensus" dejaba de ser consenso:
un robot quedaba con un perfil distinto del resto. Ahora la propuesta se redondea al formato de
cable en el momento de crearse.

## 4. Bid de Capacity-CBBA (congelado, tal como se acordó)

```
r_ik  = [ m_k − Σ_{j ∈ Ĉ_ik, j≠i} c_j ]_+          estimación local de la membresía
ΔD_ik = min( c_i, r_ik )
b_ik  = ( ΔD_ik , −d_ik , −token_i )               comparación lexicográfica
```

`token_i = sha256(world_seed ‖ c_i ‖ p_i)`: viaja con el robot, **no** es el índice de fila.
La capacidad viaja en el registro porque sin ella no se puede estimar `r_ik`.

Con este bid el proceso oscila (§ resumen 1).

## 5. Esquemas de mensaje y bytes reales

Envelope común, 7 B: `<B H H H>` = tipo, emisor, ronda, longitud.

| tipo | payload | bytes payload | en cable |
|---|---|---:|---:|
| 1 `neighbour_profile` | `<f Q>` + K×f32 | 12 + 4K | 19 + 4K |
| 2 `cbba_table` | n × `<H h f f f Q H>` | 26 n | 7 + 26 n |
| 3 `grape_proposal` | `<B H f f Q H h f H h f>` | 35 | 42 |

K=5 → handshake 39 B en cable. Sin padding, sin constantes fijas: se cuenta la longitud real
serializada de cada transmisión unicast. Un método que necesita decir más, paga más.

## 6. E1 white-box — resultados

**46 pruebas, todas pasan** (`test_sp1_n3_contract.py`, `test_sp1_n3_invariants.py`).

Cubren: forma exacta de `RobotView` (y ausencia de campos globales); firma de `step`;
imposibilidad de reaccionar en la misma ronda; rechazo de envío a no-vecino; round-trip de los
tres esquemas; bytes reportados = suma de transmisiones; realización de canal pareada entre
métodos y distinta entre tratamientos; CBBA nunca declara `CONVERGED`; regresión de mundos
contra N2 (12 combinaciones CV × escenario, byte a byte); regla `K = round(0.3N)`;
certificado separando déficit de conflicto; exclusividad; reproducibilidad bit a bit;
invariancia a permutación; monotonía estricta de `(D,J)` por época; capacidad de los pares de
reclutar un robot ocioso; radio crítico como umbral de conectividad; orden de los regímenes;
grafo conexo mínimo; y control negativo de partición.

**Dos bugs reales encontrados por E1**, además del de float32:

- `certify` lanzaba excepción ante un índice de carga fuera de rango en vez de reportar
  `ROBOT_CONFLICT`. Un allocator con bug habría producido un traceback en mitad de la campaña
  en lugar de un certificado malo.
- El detector de quiescencia mataba las épocas de GRAPE a mitad de inundación: silencio
  intra-época no es quiescencia. La ventana ahora excede una época completa.

## 7. Sensibilidad a permutación de almacenamiento

`test_storage_permutation_does_not_change_the_solution`, los tres métodos: se permutan filas
de robots (posiciones, capacidades, distancias y adyacencia), y la decisión por robot físico y
el coste `J` se conservan exactamente. Es la prueba que un token derivado del índice habría
fallado silenciosamente mientras pasaba todas las demás.

En pares, el desempate local usa el token del compañero (aprendido en el handshake), no su
índice.

## 8. Piloto de radios — métricas de grafo únicamente

Mediana sobre 5 escenarios × 3 réplicas. Ningún resultado de método interviene en la elección.

| N | régimen | r_c [m] | grado medio | diámetro | λ₂ | componentes |
|---:|---|---:|---:|---:|---:|---:|
| 16 | complete | 30,07 | 15,000 | 1 | 16,000 | 1 |
| 16 | dense (2,0 r_c) | | 11,875 | 2 | 5,029 | 1 |
| 16 | medium (1,5 r_c) | | 8,375 | 3 | 1,531 | 1 |
| 16 | threshold (1,05 r_c) | | 5,375 | 5 | 0,276 | 1 |
| 16 | partitioned (0,95 r_c) | | 4,125 | — | 0,000 | 2 |
| 24 | complete | 26,04 | 23,000 | 1 | 24,000 | 1 |
| 24 | dense | | 11,833 | 3 | 3,001 | 1 |
| 24 | medium | | 8,417 | 4 | 0,904 | 1 |
| 24 | threshold | | 5,250 | 7 | 0,130 | 1 |
| 24 | partitioned | | 4,417 | — | 0,000 | 2 |
| 32 | complete | 21,80 | 31,000 | 1 | 32,000 | 1 |
| 32 | dense | | 13,875 | 4 | 2,458 | 1 |
| 32 | medium | | 9,188 | 5 | 0,615 | 1 |
| 32 | threshold | | 5,688 | 10 | 0,122 | 1 |
| 32 | partitioned | | 5,188 | — | 0,000 | 2 |

Los multiplicadores propuestos **{completo, 2,0, 1,5, 1,05, 0,95} r_c se validan**: λ₂ separa
en más de dos órdenes de magnitud y el régimen 0,95 r_c da entre 2 y 4 componentes siempre.
`r_c` se calcula como la arista mayor del árbol de expansión mínima euclídeo, que es
exactamente el umbral de conectividad del grafo R-disk.

## 9. Piloto de runtime

Bytes por robot (mediana, todos los regímenes):

| método | N=16 | N=24 | N=32 |
|---|---:|---:|---:|
| capacity_cbba | 21 008 | 90 727 | 98 667 |
| weighted_grape | 9 050 | 13 807 | 32 019 |
| weighted_pair_grape | 7 829 | 13 756 | 26 706 |

Tiempo de pared: ver § resumen 2. CBBA es barato en reloj pero caro en bytes (difunde tabla
completa y no converge, así que sigue difundiendo).

## 10-11. E2–E4 propuestos y conteo corregido

**E4 con siete tratamientos únicos** (ya no una unión que repetía el nominal):

| tratamiento | pérdida | retardo | tope rondas |
|---|---:|---:|---:|
| nominal | 0 | 0 | 100 |
| loss-05 | 0,05 | 0 | 100 |
| loss-15 | 0,15 | 0 | 100 |
| delay-2 | 0 | 2 | 100 |
| delay-U02 | 0 | U{0,1,2} | 100 |
| budget-25 | 0 | 0 | 25 |
| budget-50 | 0 | 0 | 50 |

Régimen nominal de grafo en E4: `medium` (1,5 r_c). `K = round(0.3N)` → {5, 7, 10, 14, 19}.

| Exp | rejilla | mundos únicos | ejec. método | oráculos nuevos |
|---|---|---:|---:|---:|
| E1 | ~40 a mano + property tests | 40 | 120 | 40 |
| E2 | N=16,K=5; CV{0; 0,35; 0,65; 1,0}; ρ{0,70; 0,85}; 5 escenarios; 30 semillas | 1 200 | 3 600 | 1 200 |
| E3 | subconjunto E2 (CV{0,35; 0,65}, ρ 0,85, 5 esc., 30 semillas) × 5 regímenes | 300 (⊂ E2) | 4 500 | **0** |
| E4 | N∈{16,24,32,48,64}; CV 0,65; ρ 0,85; 30 mundos/celda; 7 tratamientos | 150 | 3 150 | 150 |

**Totales corregidos: 1 690 mundos únicos, 11 370 ejecuciones método–mundo, 1 390 oráculos.**

El conteo anterior de 1 500 oráculos era erróneo por dos motivos: E3 no genera mundos nuevos
(es un subconjunto de E2 bajo otros grafos) y E4 tiene 150 mundos únicos, no uno por
tratamiento, porque los siete tratamientos no cambian el problema central.

**Advertencia de viabilidad:** con el runtime actual, la celda N=64 de E4 para
`weighted_pair_grape` cuesta ≈ 45 h. E4 no es ejecutable sin resolver §16.2.

## 12. Tests

```
tests/test_sp1_n3_contract.py     13 pruebas
tests/test_sp1_n3_invariants.py   37 pruebas  (4 nuevas de regresión)
tests/test_sp1_levels.py          16 pruebas  (N1/N2, sin cambios)
                                  ---------
                                  66 pasan
```

## 13. Archivos creados / modificados

**Creados**

```
src/viu_mrob_tfm/sp1_n3/{__init__,contract,graph,messages,certificate,worlds,
                          capacity_cbba,weighted_grape,runner}.py
scripts/sp1_n3_common.py
scripts/sp1_n3_pilot.py
tests/test_sp1_n3_contract.py
tests/test_sp1_n3_invariants.py
scripts/results/sp1_levels/n3_v1_pilot/{radius_pilot.csv,runtime_pilot.csv,pilot_manifest.json}
reports/2026-08-08-sp1-n3-fase1-entrega.md
```

**Modificados: ninguno.** En particular **no** se tocó `scripts/sp1_levels_common.py`; N3 tiene
su propio módulo común, como se pidió.

## 14. Integridad

```
git diff SP1-N2-FROZEN HEAD -- scripts/results/sp1_levels/n1_v2 \
    scripts/results/sp1_levels/n2_v1 scripts/results/sp1_levels/n3 \
    scripts/sp1_n1.py scripts/sp1_n2_confirmatory.py scripts/sp1_n2_oracle.py \
    scripts/sp1_n3.py scripts/sp1_levels_common.py thesis/sp1_levels_23p
  -> vacío
```

- N1 y N2: sin diff frente a sus tags, ni en RAW ni en sus dependencias de build.
- `scripts/sp1_n3.py` y `scripts/results/sp1_levels/n3/` (piloto histórico): intactos.
- `src/viu_mrob_tfm/sp1_geo/`: intacto.
- Ningún solver ejecutado. Ninguna semilla confirmatoria abierta. Ningún RAW escrito.
- Los mundos de N3 se demuestran byte a byte idénticos a los de N2 en 12 combinaciones
  CV × escenario.

---

## 16. Decisiones que necesito antes de E2

**16.1 · Capacity-CBBA no termina.** Opciones:

- **(a) Salvaguarda monótona de precios** (estilo subasta): cada robot mantiene el mejor bid
  visto por carga; solo puede tomar una carga si supera estrictamente el precio al que la
  perdió. Los precios no decrecen, luego el proceso termina. Cambia el método pero es el
  mecanismo estándar y sigue siendo local.
- **(b) Regla de no retorno**: un robot desplazado de `k` no vuelve a pujar por `k`. Termina en
  ≤ N·K pujas; más simple, más restrictivo.
- **(c) Dejarlo como está** y reportar el ciclo: `algorithm_status = DEADLOCK`, y declarar que
  la adaptación no termina. Científicamente honesto y es en sí un resultado, pero entonces
  `P(raw_feasible)` de CBBA no es interpretable y habría que decirlo.

Mi recomendación: **(a)**, y reportar además la frecuencia de ciclo del bid sin salvaguarda
como hallazgo, porque es exactamente la garantía que la adaptación multi-ganador pierde.

**16.2 · Pair-GRAPE escala ≈ N^4.9.** Opciones: limitar E4 a N ≤ 32 para esa rama;
restringir la enumeración de pares (por ejemplo solo a cargas en el radio del robot);
o aceptar el coste y recortar réplicas. Sin decisión, E4 no se puede ejecutar.

**16.3 · Calidad de GRAPE invariante al grafo conexo.** ¿Se acepta y se declara en E3, o se
prefiere la opción B (concurrente, sin teorema) como segunda rama para que E3 tenga un eje de
calidad no plano? Implementar B es viable, pero entonces hay dos GRAPE distintos que comparar.

**16.4 · GRAPE diverge bajo pérdida y miente al declarar `CONVERGED`.** Opciones:

- **(a) Inundación robusta**: reenviar el mejor conocido a cada vecino en *cada* ronda de la
  época en lugar de solo cuando cambia. Cuesta bytes (y hay que medirlo, no estimarlo), pero
  hace que la probabilidad de no entrega caiga geométricamente con las `N−1` rondas.
- **(b) Acuerdo en dos fases por época**: propuesta, y luego confirmación explícita del ganador;
  sin confirmación unánime la época se aborta y se repite. Es lo correcto en el sentido fuerte,
  y hace que la terminación deje de depender de una hipótesis oculta.
- **(c) Declarar E4 fuera de alcance para GRAPE-A** y evaluar pérdida/retardo solo con CBBA.

En cualquiera de los tres casos añadiría un **invariante del observador**: si al terminar los
robots no sostienen el mismo perfil, el estado no puede ser `CONVERGED` sino `DIVERGED`. Eso es
observación pura y debería existir aunque se elija (b), porque es lo que convierte un fallo
silencioso en un fallo visible.

Mi recomendación: **(b) + el invariante**, y reportar la tasa de divergencia de (a) como
evidencia de por qué la hipótesis de entrega fiable no era decorativa.

**No abro semillas confirmatorias hasta tener estas cuatro respuestas.**
