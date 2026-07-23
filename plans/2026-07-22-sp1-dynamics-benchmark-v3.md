# SP1 Dynamics Benchmark V3

## Propósito y resultado observable

Implementar y ejecutar `SP1_DYNAMICS_BENCHMARK_v3` para separar el efecto de la dinámica primal, el consenso, la topología, `N` y `K` sobre la falta de convergencia observada en V2. El resultado observable son dos paquetes nuevos —preview y campaña completa— con datos crudos, trazas, estadística pareada, nueve figuras, mapa de regímenes, auditoría y hashes verificables. V1 y V2 son entradas inmutables.

## Contexto y archivos canónicos

- Contrato científico: `docs/00_TFM_CHARTER.md`, `docs/02_RESEARCH_MATRIX.md` y `docs/03_EXPERIMENT_PROTOCOL.md`.
- Trazabilidad y notación: `docs/04_CLAIMS_EVIDENCE.md`, `docs/05_NOTATION.md` y `docs/07_SP_SECTION_TEMPLATE.md`.
- Baseline congelado: `dynamics_v2.py`; Replicator conserva su paso mirror-prox y precondicionador sin alterarlos.
- Recuperación congelada: `rounding.py`, AugmentingRecovery-V2 con longitud 12, 50.000 nodos, 30 candidatos por carga, poda, intercambio y compresión activos.
- Configuración predeclarada: `experiments/configs/sp1_dynamics_benchmark_v3.yaml`.
- Rama y base: `codex/sp1-dynamics-v3`, derivada de `4c9ba49ddd486f923d622fdc6f21a127f154fd24`.

## Alcance y no alcance

Incluye Replicator-D, Smith-D, BNN-D, Logit-D annealed y BestResponse-D relajada bajo el mismo lazo dual/PI, más BestResponse-pure como familia entera secundaria. Incluye Auction-D y oráculos LP/MILP como referencias etiquetadas. Incluye E7.0–E7.5, calibración independiente, censura, contabilidad de cómputo/comunicación y recuperación entera condicionada a convergencia.

No incluye navegación, A*, uniciclo, obstáculos, contacto, transporte ni vídeos. No demuestra convergencia global, escalabilidad general ni optimalidad de la recuperación.

## Supuestos y preguntas resueltas

- La geometría primal es el único factor primario que cambia entre los cinco métodos; costes, máscara, estado inicial, grafo, duales, PI, tolerancias y presupuesto son compartidos por `world_id`.
- `logical_round` es una actualización simultánea primal–dual. Para mirror-prox hay dos intercambios por ronda; para las demás dinámicas, uno. Una transmisión de un vector dirigido sobre una arista es un paquete.
- El payload transmitido concatena dual y tracker PI, por lo que tiene dimensión `2*K*M` con `M=3`; `payload_bytes=8*scalar_transmissions`.
- E7.1 usa dual compartido y cero mensajes, y se etiqueta diagnóstico no distribuido. E7.2–E7.5 usan copias duales locales.
- La censura se decide por el primer presupuesto agotado entre rondas, tiempo o escalares; no dispara recuperación.
- Los límites son constantes entre tamaños y métodos: 3.000 rondas, 60 s y 5e9 escalares para evaluación. El preview usa 1.500 rondas y 30 s solo como validación, sin reducir la campaña final.
- La utilización E7.4 se construye en 75 % de los recursos disponibles mediante una partición testigo, y se certifica además con LP/MILP cuando aplica.

## Diseño matemático/técnico

Cada fila de `x_i` vive en el símplex enmascarado de `K+1` estrategias, incluida inactividad. El fitness compartido usa coste normalizado, el término regularizador objetivo declarado y `A^T lambda_i`. La revisión primal es:

- Replicator: implementación V2 mirror-prox, sin modificaciones.
- Smith: flujos pareados positivos, proyección explícita y `O(K^2)` comparaciones por agente/ronda.
- BNN: exceso positivo respecto al fitness medio.
- Logit: punto fijo softmax a temperatura `max(T_min,T_0*gamma^r)`.
- BestResponse relajada: combinación convexa con one-hot y desempate por menor índice.
- BestResponse-pure: activaciones asíncronas reproducibles; una época son `N` activaciones esperadas.

Invariantes: símplex, no negatividad, masa nula en estrategias enmascaradas, finitud, determinismo por semilla, mismo origen pareado, y recuperación únicamente tras el gate operacional. Cada residual conserva semántica propia en los datos.

## Plan experimental

La calibración usa semillas 70000–70019 en `(20,4)`, `(50,10)` y `(100,20)`, tres candidatos por método y el mismo presupuesto. La selección lexicográfica maximiza convergencia, minimiza residual y luego minimiza escalares y tiempo. Sus parámetros se congelan antes del preview/evaluación.

- E7.0: diez casos deterministas y tests de invariantes.
- E7.1: `(20,4)`, `(50,10)`, `(100,20)`, 30 semillas, dual compartido.
- E7.2: las mismas escalas, complete y r-disk conectado con grados objetivo 4/8/16, 20 semillas/celda.
- E7.3: `N={20,50,100,200,500}`, `K=ceil(N/5)`, semillas `{30,30,30,20,10}`, r-disk V2.
- E7.4: `N=100`, `K={2,5,10,20,40}`, 30 semillas, utilización construida 75 %.
- E7.5: `(50,10)`, `(100,20)`, `(200,40)`, 20 semillas por robot failure, new load, capacity drop y topology degradation, evento al 30 % y warm start.

La unidad independiente es `world_id`. Se calculan Wilson/McNemar para proporciones, bootstrap pareado/Wilcoxon/Holm/rank-biserial para continuas y RMST/Kaplan–Meier para endpoints censurados. El mapa de regímenes aplica literalmente el gate conjunto predeclarado de mejora frente a Replicator.

## Hitos

- [x] Hito 1 — rama limpia, commit inicial y protocolo congelado.
- [x] Hito 2 — motor y E7.0 con pruebas específicas aprobadas.
- [x] Hito 3 — calibración independiente completa y parámetros seleccionados.
- [ ] Hito 4 — preview completo con todos sus gates aprobados.
- [ ] Hito 5 — commit de implementación/configuración congelada y worktree limpio.
- [ ] Hito 6 — E7.1–E7.5 completos, reanudables y con conteos exactos.
- [ ] Hito 7 — estadística, F1–F9, reporte, auditoría y hashes aprobados.
- [ ] Hito 8 — trazabilidad actualizada y commit final limpio.

## Validación

- `python -m pytest tests/test_sp1_dynamics_v3.py tests/test_sp1_conference_v2.py tests/test_sp1_validation.py -q`
- `python -m viu_mrob_tfm.sp1_canonical.validation.dynamics_benchmark_v3 --config experiments/configs/sp1_dynamics_benchmark_v3.yaml --stage calibrate`
- mismo comando con `--stage preview`, `--stage full` y `--stage audit`.
- Verificar conteos, pares, hashes y `git status --short` al inicio y al final.

El preview solo aprueba si no hay violaciones/NaN, las cuentas se recomputan, todos los métodos producen filas, toda censura tiene causa y ninguna recuperación sigue a no convergencia.

## Riesgos y mitigaciones

- Coste de Replicator V2 en N=500: presupuesto de 60 s y checkpoints por run; la censura se conserva como resultado.
- Explosión de payload con `K`: límite común de escalares y RMST comunicativo; no se descartan censurados.
- Complete genera comunicación cuadrática: se reporta como diagnóstico y no como arquitectura escalable.
- Smith cuesta `O(K^2)`: se contabilizan comparaciones y se explicita en complejidad.
- Logit puede conservar sesgo/entropía: se reportan temperatura y gap, sin equipararlo a BestResponse.
- Eventos pueden volver inviable un mundo: el evento se construye factible cuando corresponde y cualquier inviabilidad residual se registra, no se re-muestrea por método.

## Registro de decisiones

- 2026-07-22 — Se deriva V3 del commit limpio V2 para mantener Replicator y recuperación congelados.
- 2026-07-22 — Se fija un único presupuesto de evaluación por run; no habrá tuning por N ni mundo.
- 2026-07-22 — Se separa BestResponse-pure en `result_family=integer_async`; no entra en gaps LP de las dinámicas fraccionarias.
- 2026-07-22 — Se usa 75 % como punto central del intervalo predeclarado 70–80 % para E7.4.
- 2026-07-22 — Ningún candidato convergió operacionalmente en 1.000 rondas r-disk; la selección aplicó honestamente el segundo criterio (residual terminal) y no amplió el espacio de tuning después de observar el resultado.

## Progreso

Rama V3 creada desde V2. El motor y 43 pruebas pasan. La calibración ejecutó 900/900 runs en 1.267,5 s con auditoría aprobada. Al no observar convergencia operacional en ningún candidato, se seleccionaron por residual y después escalares/tiempo: `rep_eta_012`, `smith_008`, `bnn_012`, `logit_slow` y `br_010`. El resultado negativo se conserva y los parámetros quedan congelados antes del preview.
