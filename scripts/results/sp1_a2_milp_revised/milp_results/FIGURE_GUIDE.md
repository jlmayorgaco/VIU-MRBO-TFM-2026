# Guía de lectura — figuras MILP heterogéneo

Cada figura responde una pregunta concreta. Las bandas P05–P95 describen dispersión empírica; los intervalos de Wilson describen incertidumbre de una proporción binaria.

## `milp_scaling_solver_time.png` / `milp_scaling_solver_time.pdf`

**Pregunta.** ¿Cómo crece el tiempo observado con el número de robots?

**Cómo leerla.** La línea azul es la mediana; la banda es P05–P95. La línea naranja resume una regresión log–log sobre medianas.

**Límite.** La pendiente no es una cota asintótica y depende del dominio, hardware, solver y timeout.

## `milp_scaling_memory.png` / `milp_scaling_memory.pdf`

**Pregunta.** ¿Cuánta memoria explícita requiere el modelo disperso?

**Cómo leerla.** Se muestra la matriz de distancia y la matriz CSR de restricciones, en MiB.

**Límite.** No incluye memoria interna del solver ni del proceso Python.

## `milp_balance_feasibility.png` / `milp_balance_feasibility.pdf`

**Pregunta.** ¿Cómo cambia la factibilidad con déficit o exceso nominal?

**Cómo leerla.** Cada punto es una tasa con IC Wilson 95 %. La zona roja corresponde a `N<M`.

**Límite.** La capacidad heterogénea puede hacer que `N/M` no determine por sí solo la factibilidad.

## `milp_optimality_by_size.png` / `milp_optimality_by_size.pdf`

**Pregunta.** ¿Con qué frecuencia el solver certifica optimalidad?

**Cómo leerla.** Una solución factible sin certificado se representa como no óptima.

**Límite.** La curva está condicionada por el límite de tiempo del perfil.

## `milp_geometry_distance_tail.png` / `milp_geometry_distance_tail.pdf`

**Pregunta.** ¿Qué geometrías producen colas de distancia más largas?

**Cómo leerla.** Se compara el P95 normalizado mediante cajas, medianas y puntos de ejecuciones.

**Límite.** Mide asignación estática, no navegación ni colisiones.

## `milp_capacity_effects.png` / `milp_capacity_effects.pdf`

**Pregunta.** ¿Cómo afecta la heterogeneidad a factibilidad y exceso?

**Cómo leerla.** El panel A muestra tasas; el B relaciona CV de capacidad con capacidad excedente reclutada.

**Límite.** La regresión es descriptiva y la capacidad es escalar.

## `milp_capacity_recruitment.png` / `milp_capacity_recruitment.pdf`

**Pregunta.** ¿Cuántos robots recluta el MILP respecto a slots homogéneos?

**Cómo leerla.** La línea 1 representa un robot por slot nominal; valores menores indican sustitución por robots de mayor capacidad.

**Límite.** Menos robots no implica menor energía ni mejor control.

## `milp_failure_resilience.png` / `milp_failure_resilience.pdf`

**Pregunta.** ¿Qué fallos preservan la misión y cuánto churn producen?

**Cómo leerla.** El panel A muestra recuperación completa; el B, cambios de carga entre robots supervivientes.

**Límite.** Es una reasignación estática posterior al fallo.

## `milp_fleet_utilization.png` / `milp_fleet_utilization.pdf`

**Pregunta.** ¿Qué fracción de la flota recluta cada geometría?

**Cómo leerla.** Las cajas muestran la distribución de robots asignados sobre robots disponibles.

**Límite.** Utilización alta no implica mejor energía, control o reparto de fuerza.
