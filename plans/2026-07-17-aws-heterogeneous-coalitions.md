# Piloto AWS de cargas heterogéneas y coaliciones cooperativas

## Propósito y resultado observable

Extender el demostrador industrial con cuatro cargas de masa, tamaño y cardinalidad distintas. Cada carga solo podrá moverse cuando una coalición completa de AMR alcance sus poses de acoplamiento. Se comparará un MILP central de coaliciones con greedy, random y replicator con consenso local, conservando semillas pareadas, trazas, figuras y MP4.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md`: RQ1, formación de coaliciones heterogéneas.
- `docs/02_RESEARCH_MATRIX.md`: SP1 para cardinalidad y SP2 para capacidad efectiva.
- `docs/03_EXPERIMENT_PROTOCOL.md`: comparación pareada y fallos visibles.
- `src/viu_mrob_tfm/sp1/theory.py`: MILP-Q y cierre por cuórum existentes.
- `tmp/scripts/coppelia/build_aws_industrial_adversarial_scene.py`: cargas visuales de 5, 14, 28 y 18 kg.

## Alcance y no alcance

Incluye cuotas `n_k={1,2,3,2}`, masas y dimensiones diferentes, acoplamiento por cuórum, transporte cinemático de la carga, destinos variables, A* como baseline y una variante TFM con campo continuo, juego Replicator local y proyección CBF. No incluye reparto real de wrench, rigidez, contacto, torque, estabilidad del cuerpo compuesto ni una garantía de seguridad continua.

## Supuestos y preguntas resueltas

- La cuota se deriva de una capacidad cooperativa nominal conservadora de 10 kg por AMR: `ceil(m_k/10 kg)`, coincidente con las cuotas visuales existentes.
- Una carga se activa todo-o-nada; no se transporta con coalición parcial.
- Cada robot participa como máximo en una carga simultánea.
- El MILP, no Hungarian, es el oráculo apropiado para cuotas variables.
- El soporte físico se representa mediante offsets rígidos cinemáticos y se rotula como proxy visual.

## Diseño matemático/técnico

Variables binarias `x_ik` asignan robot `i` a carga `k` y `y_k` activa la carga. Se exige `sum_k x_ik <= 1` y `sum_i x_ik = n_k y_k`. El MILP maximiza cargas completas y minimiza coste de aproximación, transporte y batería. Replicator mantiene preferencias continuas robot--carga, estima ocupaciones mediante consenso vecinal y aplica un cierre local por cuórum.

## Plan experimental

- Cargas: 5 kg/R1, 14 kg/R2, 28 kg/R3 y 18 kg/R2.
- Políticas: MILP-Q, greedy-Q, random-Q y replicator-Q con consenso.
- Ocho semillas pareadas, horizonte de 100 s y decisión cada 0,5 s.
- Métricas: entregas, cargas completas, tiempo de formación, espera, distancia, energía, coste, déficit de cuota, mensajes y error de consenso.

## Hitos

- [x] Hito 1 — modelo y asignadores de coalición implementados.
- [x] Hito 2 — movimiento multi-AMR y trazas de carga/coalición implementados.
- [x] Hito 3 — figuras, MP4, pruebas y campaña verificadas.
- [x] Hito 4 — cada nueva misión recibe un destino aleatorio pareado que permanece fijo hasta la entrega.
- [x] Hito 5 — A* y reserva dinámica eliminan interpenetraciones con racks, barreras, robots y cargas en el modelo cinemático muestreado.
- [x] Hito 6 — radios diferenciados de sensado/comunicación, enlaces vecinales y conteos locales quedan visibles y trazados.
- [x] Hito 7 — variante independiente de centro abierto elimina puesto y barreras centrales, conserva racks y dibuja trayectorias realizadas.
- [x] Hito 8 — comparación pareada del centro abierto determina qué diferencias pueden atribuirse al asignador y cuáles a congestión.
- [x] Hito 9 — variante independiente con juego Replicator de primitivas, campo continuo y proyección CBF local reemplaza A* como método propuesto.
- [x] Hito 10 — trazas RAW--SAFE--EXEC, pruebas muestreadas y comparación pareada contra A* separan coordinación estratégica de navegación.

## Validación

- MILP produce solo coaliciones cero o exactamente `n_k`.
- Ningún robot pertenece a dos coaliciones.
- La carga no se mueve antes del cuórum y conserva su destino.
- Masa, tamaño y cuota quedan registrados en cada traza.
- MP4 validado con `ffprobe` y fotograma inspeccionado.
- Las 32 ejecuciones registran cero violaciones estáticas, cero dinámicas y cero fallos reales de A*.
- La campaña continua conserva 32 ejecuciones, simplex de preferencias, trazas RAW--SAFE--EXEC y el conteo explícito del guard muestreado.

## Riesgos y mitigaciones

- Confundir cuota con factibilidad mecánica: declarar explícitamente que no sustituye el certificado de wrench.
- Comparar Hungarian fuera de dominio: retirarlo de este piloto y conservarlo solo en SP0.
- Ocultar coaliciones parciales: registrar déficit y rechazar transporte hasta cierre completo.

## Registro de decisiones

- 2026-07-17: se crea un artefacto SP1/SP2 separado; no se sobrescribe la evidencia SP0.
- 2026-07-17: se reutiliza el MILP-Q canónico del repositorio como oráculo central.
- 2026-07-17: el destino se sortea de forma determinista por `semilla--carga--ciclo`; la aleatoriedad ocurre al crear la misión y no durante su ejecución.
- 2026-07-17: se planifica sobre racks y barreras inflados con A* de cuatro vecinos; la reserva local evita movimientos que solapen otra huella dinámica.
- 2026-07-17: el radio de sensado se mantiene en 1,8 m y el de comunicación en 3,2 m; sensado no implica comunicación y cada arista de comunicación existe solo mientras ambos AMR están dentro del alcance.
- 2026-07-17: se crea una variante `open_center`; no se sobrescribe la campaña con cuello porque ambas geometrías responden preguntas distintas.
- 2026-07-17: A* se conserva solo como baseline de movimiento. La variante TFM usa una ley matemática continua, ejecutada digitalmente por Euler con paso declarado, y no equipara el filtro CBF muestreado con una prueba de invariancia continua.

## Progreso

La reparación de rutas, la capa local y la variante abierta quedaron reproducidas en ocho semillas pareadas. En el layout con cuello, MILP-Q, greedy-Q, replicator-Q y random-Q entregaron 3,125, 3,25, 1,375 y 0,5 cargas; solo greedy-Q superó a random-Q tras Holm. En el centro abierto con A* entregaron 0,75, 1,25, 1,375 y 0,875. Con la ley continua muestreada entregaron 1,625, 2,0, 1,875 y 1,375, sin diferencias intravariante detectables tras Holm. Las 32 ejecuciones continuas tuvieron cero solapamientos muestreados y cero guardias finales, pero 26 muestras SAFE superaron el umbral `1e-6`, con máximo 0,0514; se conserva como evidencia de que la proyección local puede encontrar restricciones simultáneas incompatibles. El MP4 muestra trayectorias no ortogonales y la comparación cuantifica geometría observada, no optimalidad ni seguridad continua.
