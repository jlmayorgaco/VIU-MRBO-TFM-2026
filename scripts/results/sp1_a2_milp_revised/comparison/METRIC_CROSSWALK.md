# Correspondencia de métricas Hungarian–MILP

| Eje Hungarian | Métrica MILP | Correspondencia | Razón |
|---|---|---|---|
| `N`, `K`, `M`, semilla, geometría, cuota | mismos campos | exacta | El mundo base es idéntico. |
| `mission_feasible` | `milp_feasible` | exacta en significado de misión completa | Todas las cargas son obligatorias. |
| `coverage` parcial de slots | `milp_complete_load_fraction` | no equivalente | El MILP no devuelve coaliciones parciales como solución. |
| `total_cost` de distancia | `milp_total_distance` | comparable con cautela | Cambia el conjunto factible cuando las capacidades son heterogéneas. |
| media por slot asignado | media por robot asignado y distancia por slot nominal | renombrada | Un robot heterogéneo no representa un slot. |
| P50/P95/máximo/CV/Gini/Jain | `milp_assignment_distance_*` | exacta sobre distancias seleccionadas | Misma unidad: metros. |
| utilización/robots libres | `milp_robot_utilization`, `milp_idle_fraction` | exacta | Cuenta robots, no capacidad. |
| cuota asimétrica | `quota_asymmetry_cv` | exacta | Las cuotas nominales son pareadas. |
| matriz de costes | matriz robot–carga | dimensionalmente distinta | Hungarian expande `M` slots; MILP conserva `K` cargas. |
| memoria | `milp_matrix_bytes` | específica | Incluye distancias y matriz dispersa de restricciones. |
| tiempos de solver/total | `milp_*_wall_ns` | exacta en reloj, no en complejidad | Se separan matriz, modelo, solver y postproceso. |
| ratio greedy/oráculo | no se replica | no aplicable | El propio MILP es el oráculo central. |
| mensajes/reintentos | `central_*` | modelo central explícito | No representa comunicación distribuida. |
| churn/coste tras fallo | `assignment_churn`, `relative_distance_increase` | exacta sobre robots supervivientes | Los IDs fallados son pareados entre modelos. |
| gap de optimalidad | `milp_mip_gap`, `milp_optimal` | adicional | Nunca se llama óptima a una incumbente sin certificado. |
| heterogeneidad | `capacity_*`, `capacity_cv` | adicional | Caracteriza las capacidades individuales en kg. |

La convención local solicitada por el autor denomina `q_i` a la capacidad. En la notación canónica de la memoria, `q_i` ya designa el estado del robot; por ello, esta campaña debe redactarse con `c_i^{pay}` para capacidad útil nominal.
