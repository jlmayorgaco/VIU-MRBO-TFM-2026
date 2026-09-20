# Auditoría teórica de las familias SP1.N4

## Objeto común

Las cuatro familias estudian la misma decisión física de reclutamiento. Cada
robot indivisible termina inactivo o asignado a una carga. Para un perfil
atómico `a`, la prioridad es anular el déficit total `D_4(a)` y, entre perfiles
factibles, reducir el recorrido `J_4(a)`. El MILP de N2 es una referencia
central con información global; no representa la arquitectura propuesta.

## F-I — Juego potencial atómico

- **Variable:** `a_i ∈ {0,…,K}`.
- **Solución:** estabilidad local respecto de la vecindad `N_h` examinada.
- **Algoritmos:** BR, 2BR y C3 cambian el orden `h`; ASR y LLL cambian la regla
  de revisión; DMIS y TX resuelven concurrencia y consistencia.
- **Propiedad demostrada:** una desviación unilateral o coalicional puede
  evaluarse con los agregados de las cargas afectadas; todo commit estricto
  disminuye el criterio lexicográfico en la fase activa.
- **Límite:** la terminación finita y la estabilidad son locales. No implican
  optimalidad global, transporte seguro ni tolerancia a una red arbitraria.

## F-II — Juego poblacional

- **Variable:** `x_i ∈ Δ_i`; sus componentes son intenciones, no fracciones
  físicamente transportadas.
- **Potencial implementado:**
  `Φ(x)=-(α/2)||[1-Q(x)/m]_+||²-(β/N)Σ d̄_ik x_ik`.
- **Fitness común:** `F_ik=∂Φ/∂x_ik`. Replicator, Smith, BNN y Logit reciben
  exactamente este campo; solo cambia el protocolo de revisión.
- **Propiedades verificadas:** el campo mantiene el símplex bajo la integración
  implementada; Replicator conserva soporte; las dinámicas de correlación
  positiva se auditan contra el potencial exacto. Logit busca un punto
  perturbado y no se incluye en esa afirmación.
- **Capa distribuida:** cada robot estima la cobertura mediante DAC sobre el
  grafo estático y conectado heredado de N3.
- **Salida física:** `a=R(x)` mediante el cierre atómico común.
- **Límite:** el potencial es una penalización suave por tramos, no una
  codificación exacta del orden lexicográfico. La monotonía teórica corresponde
  al agregado exacto; el error transitorio de DAC se mide por separado.

## F-III — Primal–dual distribuido y vGNE

- **Variable:** `(x_i, λ_i)`.
- **Problema continuo:** coste espacial regularizado sujeto a
  `1-Q_k(x)/m_k≤0`. La regularización cuadrática `ε>0` hace estrictamente
  convexo el problema continuo y cambia de forma explícita su objetivo.
- **Referencia central:** SLSQP resuelve el problema continuo y una estimación
  dual permite auditar factibilidad primal, factibilidad dual,
  complementariedad y estacionariedad proyectada.
- **Algoritmo distribuido:** proyección primal, DAC del residual de cuota y
  consenso de las copias duales por aristas de N3.
- **Criterio de aceptación:** el indicador `converged` exige que el residual
  conjunto KKT y de consenso cruce el umbral preespecificado.
- **Salida física:** el mismo `R` de F-II.
- **Límite:** el código es una implementación empírica auditable. No se
  transfiere un teorema externo de convergencia porque todavía no se han
  demostrado, para esta discretización, todas las condiciones de ganancias y
  operador distribuido.

## F-IV — Reclutamiento repetido con eventos exógenos

- **Estado:** asignación vigente, trabajos activos, disponibilidad de robots y
  evento observado.
- **Eventos del piloto:** llegada, finalización y fallo.
- **Políticas:** reoptimización Geo-QPG desde cero y Geo-QPG activado por evento
  con warm start. Un programa dinámico central con conocimiento perfecto del
  futuro sirve de techo en instancias pequeñas.
- **Endpoint:** asignación atómica en cada instante; no participa en la tabla
  estática F-I–F-III.
- **Límite:** es un juego potencial repetido condicionado por una secuencia
  exógena. No se afirma que sea un juego potencial de Markov ni que el oráculo
  sea distribuido.

## Veredicto de madurez

F-I conserva las garantías formales más fuertes. F-II y F-III ya tienen una
cadena ejecutable completa —estado continuo, mecanismo distribuido, cierre
común y auditoría atómica—, pero sus resultados de convergencia permanecen
clasificados como numéricos. F-IV alcanza el nivel de piloto reproducible y
queda deliberadamente separada del benchmark estático. Esta asimetría es una
conclusión del trabajo, no una omisión editorial.
